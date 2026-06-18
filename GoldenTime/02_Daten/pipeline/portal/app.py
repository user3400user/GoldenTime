"""
Kundenportal-Server (Loop 3, DoD §9.4) — stdlib ``http.server``, KEIN Framework (architektur-konsistent
zum Admin-Dashboard; bewusste Abweichung vom FastAPI-Backlog-Vorschlag §6.3: stdlib-first, voll
in-process testbar, kein Playwright-Browser-Download nötig).

Routen:
  GET  /login   → Login-Formular
  POST /login   → authentifizieren → Session-Cookie setzen → /
  GET  /        → die Kaufsignale DES KUNDEN (hart auf sein Gebiet gefiltert) · Auth-Pflicht
  GET  /lead/<MaStR-Nr> → Lead-Detail (nur wenn er zum Gebiet des Kunden gehört) · Auth-Pflicht
  POST /logout  → Session beenden (CSRF-geschützt)

Sicherheit: Session-Cookie HttpOnly + SameSite=Strict; Session-Token nur als sha256 in der DB;
scrypt-Passwörter; Mandanten-Trennung serverseitig (Gebiet kommt aus der customer-Zeile, nie aus der
Anfrage). ``LIVE_DELIVERY_ENABLED`` aus → Demo-Banner; das Portal zeigt nur ``portal_lead`` (Sample/
e.K.-gefiltert) — kein echter Personendaten-Pfad an einen zahlenden Kunden (§0/I8).
"""
from __future__ import annotations

import hmac
import http.cookies
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote

from .. import config
from ..control import state
from . import auth, views

log = logging.getLogger("pipeline.portal")

COOKIE = "gt_session"
MAX_BODY = 64 * 1024           # Formular-Body-Limit (Security-Review M2: gegen OOM-DoS)


def _demo() -> bool:
    """Demo-Modus, solange die Live-Lieferung gesperrt ist (§0)."""
    return not config.LIVE_DELIVERY_ENABLED


def _cookie(token: str, max_age: int) -> str:
    """Session-Cookie-Header. ``Secure`` per ENV ``PORTAL_COOKIE_SECURE=1`` (Pflicht hinter TLS/Prod;
    für die localhost-http-Demo aus, sonst sendet der Browser das Cookie nicht). M1 der Security-Review."""
    attrs = f"{COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={max_age}"
    if os.environ.get("PORTAL_COOKIE_SECURE", "") == "1":
        attrs += "; Secure"
    return attrs


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "Portal"          # L4: kein Versions-/Tech-Leak im Server-Banner
    sys_version = ""

    # --- HTTP-Helfer ----------------------------------------------------------------------------
    def _send_html(self, body: str, status: int = 200, *, set_cookie: str | None = None,
                   clear_cookie: bool = False) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        if set_cookie is not None:
            self.send_header("Set-Cookie", _cookie(set_cookie, 43200))
        if clear_cookie:
            self.send_header("Set-Cookie", _cookie("", 0))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str, *, set_cookie: str | None = None, clear_cookie: bool = False) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        if set_cookie is not None:
            self.send_header("Set-Cookie", _cookie(set_cookie, 43200))
        if clear_cookie:
            self.send_header("Set-Cookie", _cookie("", 0))
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _cookie_token(self) -> str | None:
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        try:
            jar = http.cookies.SimpleCookie(raw)
        except http.cookies.CookieError:
            return None
        morsel = jar.get(COOKIE)
        return morsel.value if morsel else None

    def _read_form(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        return parse_qs(raw)

    # --- Routing --------------------------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        con = state.connect()
        try:
            if self.path in ("/login", "/login/"):
                self._send_html(views.render_login())
                return
            kunde = auth.session_customer(con, self._cookie_token())
            if kunde is None:
                self._redirect("/login")
                return
            csrf = auth.session_csrf(con, self._cookie_token()) or ""
            if self.path in ("/", "/index.html"):
                leads = auth.leads_for_customer(con, kunde, nur_demo=_demo())
                self._send_html(views.render_leads(kunde, leads, csrf=csrf, demo=_demo()))
            elif self.path.startswith("/lead/"):
                see = unquote(self.path[len("/lead/"):]).strip("/")
                r = auth.lead_belongs_to(con, kunde, see, nur_demo=_demo())
                if r is None:                      # nicht vorhanden ODER fremdes Gebiet → 404 (kein Leak)
                    self._send_html("<h1>404</h1>", status=404)
                else:
                    self._send_html(views.render_lead(kunde, r, csrf=csrf, demo=_demo()))
            else:
                self._send_html("<h1>404</h1>", status=404)
        finally:
            con.close()

    def do_POST(self) -> None:  # noqa: N802
        if int(self.headers.get("Content-Length") or 0) > MAX_BODY:
            self._send_html("<h1>413</h1><p>Anfrage zu groß.</p>", status=413)
            return
        con = state.connect()
        try:
            form = self._read_form()
            if self.path in ("/login", "/login/"):
                self._handle_login(con, form)
            elif self.path == "/logout":
                self._handle_logout(con, form)
            else:
                self._send_html("<h1>404</h1>", status=404)
        finally:
            con.close()

    def _handle_login(self, con, form: dict) -> None:
        login = (form.get("login") or [""])[0]
        password = (form.get("password") or [""])[0]
        kunde = auth.authenticate(con, login, password)
        if kunde is None:
            # Generische Meldung — verrät NICHT, ob Login existiert oder Passwort falsch ist.
            self._send_html(views.render_login(fehler="Login oder Passwort ist falsch."), status=401)
            return
        # H1: abgelaufene Sessions aufräumen + bestehende Sessions DIESES Kunden invalidieren
        # (Single-Active-Session — ein einmal abgegriffenes Token überlebt den Re-Login nicht).
        auth.purge_expired(con)
        auth.invalidate_customer_sessions(con, kunde["id"])
        token, _csrf = auth.create_session(con, kunde["id"])
        self._redirect("/", set_cookie=token)

    def _handle_logout(self, con, form: dict) -> None:
        token = self._cookie_token()
        # CSRF: das mitgesendete Token muss dem Session-CSRF entsprechen (state-ändernder POST).
        erwartet = auth.session_csrf(con, token)
        gesendet = (form.get("csrf") or [""])[0]
        if erwartet and gesendet and hmac.compare_digest(erwartet, gesendet):
            auth.destroy_session(con, token)
        self._redirect("/login", clear_cookie=True)

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        log.info("portal %s", fmt % args)


def serve(port: int = 8770, host: str = "127.0.0.1") -> None:
    httpd = HTTPServer((host, port), PortalHandler)
    log.info("Kundenportal läuft auf http://%s:%d/  (Strg+C zum Beenden)", host, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Kundenportal beendet.")
    finally:
        httpd.server_close()
