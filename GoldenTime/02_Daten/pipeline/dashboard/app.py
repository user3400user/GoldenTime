"""
Admin-Dashboard-Server (K8, Briefing §6) — schlanker stdlib ``http.server``, KEIN Framework.

GET  /        → render_dashboard (liest Config-Store + Metriken read-only + Ledger-Overview).
POST /toggle  → setzt EINEN Schalter (Trigger/Modul/Gebiet) im Config-Store, schreibt ihn
                (cs.save(updated_by='dashboard')) und leitet auf / zurück (Post-Redirect-Get).

Kopplung strikt einseitig (Briefing §6): das Dashboard ist der EINZIGE Writer des Config-Stores,
liest die pipeline_state.db NUR über ``state.connect_readonly()`` und importiert KEINE Pipeline-Logik
(triggers/qualify/cohort) — nur ``control`` + ``ledger``. Die Schalter-Mutation (set_trigger/…)
liegt hier als reine Funktion (ohne Server testbar); der Handler ist nur die HTTP-Hülle.
"""
from __future__ import annotations

import dataclasses
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .. import ledger
from ..control import config_store as cs
from ..control import metrics, state
from . import views

log = logging.getLogger(__name__)

VALID_KINDS = ("trigger", "module", "gebiet")


# --- Schalter-Mutation (reine Funktionen, ohne Server testbar) -------------------------------

def set_trigger(store: cs.ConfigStore, key: str, enabled: bool) -> cs.ConfigStore:
    """Neuer Store mit gesetztem Trigger-Schalter (frozen → Kopie, kein In-Place-Mutate)."""
    if key not in cs.VALID_TRIGGERS:
        raise ValueError(f"unbekannter Trigger '{key}'")
    triggers = {k: dict(v) for k, v in store.triggers.items()}
    triggers.setdefault(key, {})["enabled"] = enabled
    return dataclasses.replace(store, triggers=triggers)   # erhält extras (_comment etc.)


def set_module(store: cs.ConfigStore, key: str, enabled: bool) -> cs.ConfigStore:
    """Neuer Store mit gesetztem Modul-Schalter (z.B. Anreicherung)."""
    if key not in cs.VALID_MODULES:
        raise ValueError(f"unbekanntes Modul '{key}'")
    modules = {k: dict(v) for k, v in store.modules.items()}
    modules.setdefault(key, {})["enabled"] = enabled
    return dataclasses.replace(store, modules=modules)


def set_gebiet(store: cs.ConfigStore, key: str, enabled: bool) -> cs.ConfigStore:
    """Neuer Store mit ge-/entschaltetem Gebiet (key = gebiet.id)."""
    if store.gebiet(key) is None:
        raise ValueError(f"unbekanntes Gebiet '{key}'")
    gebiete = tuple({**g, "enabled": enabled} if g.get("id") == key else dict(g)
                    for g in store.gebiete)
    return dataclasses.replace(store, gebiete=gebiete)


_SETTER = {"trigger": set_trigger, "module": set_module, "gebiet": set_gebiet}


def apply_toggle(store: cs.ConfigStore, kind: str, key: str, enabled: bool) -> cs.ConfigStore:
    """Dispatch auf den passenden Setter; ValueError bei unbekanntem ``kind`` (Handler → 400)."""
    setter = _SETTER.get(kind)
    if setter is None:
        raise ValueError(f"unbekannter kind '{kind}' (erlaubt: {VALID_KINDS})")
    return setter(store, key, enabled)


def _truthy(value: str) -> bool:
    """Form-Wert → bool ('1'/'true'/'on'/'ja' = an, sonst aus)."""
    return value.strip().lower() in {"1", "true", "on", "ja", "yes"}


# --- Daten-Sammlung fürs Rendering (read-only) ----------------------------------------------

def gather_view_data() -> tuple[cs.ConfigStore, list[dict], list[dict], list, list]:
    """Lädt alles, was render_dashboard braucht: Config + aggregierte Metriken + Ledger-Overview.

    Metriken/Ledger über ``state.connect_readonly()`` (nebenläufig zur schreibenden Pipeline,
    WAL). Schlägt der State-Zugriff fehl (DB fehlt o.Ä.), bleibt das Dashboard bedienbar und zeigt
    leere Tabellen statt zu crashen.
    """
    try:
        store = cs.load()
    except cs.ConfigError as e:   # korrupter Store darf das Dashboard nicht mit 500 abschießen
        log.warning("Dashboard: Config-Store ungültig (%s) — Defaults geladen.", e)
        store = cs.defaults()
    metrics_rows: list[dict] = []
    ledger_rows: list[dict] = []
    qa_rows: list = []
    latest_rows: list = []
    try:
        con = state.connect_readonly()
        try:
            metrics_rows = metrics.aggregate(con)
            latest_rows = metrics.latest_by_dimension(con)
            ledger_rows = ledger.overview(con)
            qa_rows = state.qa_pending(con)
        finally:
            con.close()
    except Exception as e:  # noqa: BLE001 — Dashboard darf nie wegen State-IO crashen
        log.warning("Dashboard: State-Lesen fehlgeschlagen (%s) — zeige leere Tabellen.", e)
    return store, metrics_rows, ledger_rows, qa_rows, latest_rows


# --- HTTP-Hülle ------------------------------------------------------------------------------

class DashboardHandler(BaseHTTPRequestHandler):
    """Minimaler Handler: GET / rendert, POST /toggle schaltet. Sonst 404."""

    server_version = "GoldenTimeDashboard/1.0"

    def _send_html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str = "/") -> None:
        self.send_response(303)  # See Other → Post-Redirect-Get (kein Doppel-Submit beim Reload)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 — http.server-Namenskonvention
        if self.path not in ("/", "/index.html"):
            self._send_html("<h1>404</h1>", status=404)
            return
        store, metrics_rows, ledger_rows, qa_rows, latest_rows = gather_view_data()
        self._send_html(views.render_dashboard(store, metrics_rows, ledger_rows, qa_rows, latest_rows))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/toggle":
            self._send_html("<h1>404</h1>", status=404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        form = parse_qs(raw)
        kind = (form.get("kind") or [""])[0]
        key = (form.get("key") or [""])[0]
        enabled = _truthy((form.get("enabled") or [""])[0])
        try:
            updated = apply_toggle(cs.load(), kind, key, enabled)
            cs.save(updated, updated_by="dashboard")
        except (ValueError, cs.ConfigError) as e:
            log.warning("Dashboard-Toggle abgelehnt: %s", e)
            self._send_html(f"<h1>400</h1><p>{e}</p>", status=400)
            return
        self._redirect("/")

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        """http.server-Logs in unseren Logger umlenken (kein stderr-Rauschen)."""
        log.info("dashboard %s", fmt % args)


def serve(port: int = 8765, host: str = "127.0.0.1") -> None:
    """Startet das Dashboard (blockierend). Default localhost-gebunden — interne Steuer-Schicht."""
    httpd = HTTPServer((host, port), DashboardHandler)
    log.info("Admin-Dashboard läuft auf http://%s:%d/", host, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Admin-Dashboard beendet.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
