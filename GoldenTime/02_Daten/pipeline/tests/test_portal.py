"""
Kundenportal (Loop 3, DoD §9.4) — Auth + MANDANTEN-TRENNUNG, voll getestet (stdlib, kein Netz extern).

Drei Ebenen:
  (1) Auth-Funktionen (pure): scrypt-Hash/Verify, authenticate (Erfolg/falsch/unbekannt), Session
      create/validate/EXPIRY/destroy/purge.
  (2) Mandanten-Trennung (pure): ein Kunde sieht NUR die Leads seines Gebiets (leads_for_customer /
      lead_belongs_to) — der §0-/Sicherheits-Kern (sonst „läuft" = „Datenleck").
  (3) Voller HTTP-Flow gegen einen in-process http.server: Login→Cookie→Leads, Auth-Pflicht,
      cross-Mandant-Zugriff = 404, CSRF-Logout.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_portal -v
"""
from __future__ import annotations

import http.client
import re
import tempfile
import threading
import unittest
import urllib.parse
from http.server import HTTPServer
from pathlib import Path
from unittest import mock

from pipeline import config as pconfig
from pipeline.control import state as statemod
from pipeline.portal import app as portalapp, auth as pauth, seed as pseed


def _seed(con):
    pauth.create_customer(con, login="a@x.de", password="GeheimA1", name="Kunde A", gebiet="muensterland")
    pauth.create_customer(con, login="b@x.de", password="GeheimB1", name="Kunde B", gebiet="osnabrueck")
    pseed.seed_demo_leads(con)


class TestPortalAuth(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = statemod.connect(Path(self._tmp.name) / "s.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_password_hash_roundtrip(self):
        h, salt = pauth.hash_password("Geheim123")
        self.assertNotIn("Geheim123", h)                       # nie Klartext
        self.assertTrue(pauth.verify_password("Geheim123", h, salt))
        self.assertFalse(pauth.verify_password("falsch", h, salt))

    def test_authenticate_erfolg_falsch_unbekannt(self):
        pauth.create_customer(self.con, login="A@X.de", password="GeheimA1", name="A", gebiet="muensterland")
        self.assertIsNotNone(pauth.authenticate(self.con, "a@x.de", "GeheimA1"))   # login case-insensitiv
        self.assertIsNone(pauth.authenticate(self.con, "a@x.de", "falsch"))
        self.assertIsNone(pauth.authenticate(self.con, "gibtsnicht@x.de", "egal"))  # kein Crash, generisch

    def test_session_lifecycle_und_expiry(self):
        cid = pauth.create_customer(self.con, login="a@x.de", password="GeheimA1", name="A", gebiet="muensterland")
        token, csrf = pauth.create_session(self.con, cid)
        self.assertIsNotNone(pauth.session_customer(self.con, token))
        self.assertEqual(pauth.session_csrf(self.con, token), csrf)
        # In der DB liegt NICHT der Roh-Token (nur sein Hash).
        roh_treffer = self.con.execute("SELECT count(*) FROM portal_session WHERE token_hash = ?",
                                       (token,)).fetchone()[0]
        self.assertEqual(roh_treffer, 0)
        # Ablauf erzwingen → ungültig.
        self.con.execute("UPDATE portal_session SET laeuft_ab = '2000-01-01T00:00:00+00:00'")
        self.con.commit()
        self.assertIsNone(pauth.session_customer(self.con, token))
        self.assertEqual(pauth.purge_expired(self.con), 1)

    def test_logout_invalidiert(self):
        cid = pauth.create_customer(self.con, login="a@x.de", password="GeheimA1", name="A", gebiet="muensterland")
        token, _ = pauth.create_session(self.con, cid)
        pauth.destroy_session(self.con, token)
        self.assertIsNone(pauth.session_customer(self.con, token))


class TestMandantenTrennung(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = statemod.connect(Path(self._tmp.name) / "s.db")
        _seed(self.con)
        self.a = self.con.execute("SELECT * FROM customer WHERE login='a@x.de'").fetchone()
        self.b = self.con.execute("SELECT * FROM customer WHERE login='b@x.de'").fetchone()

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_leads_nur_eigenes_gebiet(self):
        a_leads = {r["gebiet"] for r in pauth.leads_for_customer(self.con, self.a)}
        b_leads = {r["gebiet"] for r in pauth.leads_for_customer(self.con, self.b)}
        self.assertEqual(a_leads, {"muensterland"})
        self.assertEqual(b_leads, {"osnabrueck"})

    def test_lead_detail_fremdes_gebiet_gesperrt(self):
        # A (muensterland) darf einen Osnabrück-Lead NICHT per Detail-Zugriff sehen.
        self.assertIsNotNone(pauth.lead_belongs_to(self.con, self.a, "SEE-DEMO-MS-01"))
        self.assertIsNone(pauth.lead_belongs_to(self.con, self.a, "SEE-DEMO-OS-01"))

    def test_demo_filter_verriegelt_echtdaten(self):
        # §0-Härtung: ein (hypothetischer) Echtdaten-Lead (demo=0) wird im Demo-Modus NIE gezeigt.
        self.con.execute("INSERT INTO portal_lead(gebiet, see, entity, demo) VALUES('muensterland','REAL1','Echt GmbH',0)")
        self.con.commit()
        sees_demo = {r["see"] for r in pauth.leads_for_customer(self.con, self.a, nur_demo=True)}
        sees_live = {r["see"] for r in pauth.leads_for_customer(self.con, self.a, nur_demo=False)}
        self.assertNotIn("REAL1", sees_demo)                  # Demo-Modus verbirgt Echtdaten
        self.assertIn("REAL1", sees_live)                     # nur mit LIVE sichtbar
        self.assertIsNone(pauth.lead_belongs_to(self.con, self.a, "REAL1", nur_demo=True))

    def test_invalidate_customer_sessions(self):
        cid = self.a["id"]
        pauth.create_session(self.con, cid)
        t2, _ = pauth.create_session(self.con, cid)
        self.assertEqual(pauth.invalidate_customer_sessions(self.con, cid), 2)
        self.assertIsNone(pauth.session_customer(self.con, t2))


class TestPortalHTTP(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self._tmp.name) / "s.db"
        self._patch = mock.patch.object(pconfig, "PIPELINE_DB_PATH", self.dbpath)
        self._patch.start()
        con = statemod.connect(self.dbpath)
        _seed(con)
        con.close()
        self.httpd = HTTPServer(("127.0.0.1", 0), portalapp.PortalHandler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self._patch.stop()
        self._tmp.cleanup()

    def _req(self, method, path, *, cookie=None, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        if cookie:
            headers["Cookie"] = cookie
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        c.request(method, path, body=body, headers=headers)
        resp = c.getresponse()
        data = resp.read().decode("utf-8")
        sc = resp.getheader("Set-Cookie")
        c.close()
        return resp.status, data, sc

    def _login(self, login, password):
        body = urllib.parse.urlencode({"login": login, "password": password})
        status, _data, sc = self._req("POST", "/login", body=body)
        self.assertEqual(status, 303, "Login sollte per Redirect bestätigen")
        m = re.search(r"gt_session=([^;]+)", sc or "")
        self.assertIsNotNone(m, "Set-Cookie mit gt_session erwartet")
        self.assertIn("HttpOnly", sc)
        self.assertIn("SameSite=Strict", sc)
        return f"gt_session={m.group(1)}"

    def test_login_seite_oeffentlich(self):
        status, data, _ = self._req("GET", "/login")
        self.assertEqual(status, 200)
        self.assertIn("Anmeldung", data)

    def test_unauth_redirect_zu_login(self):
        status, _data, _ = self._req("GET", "/")
        self.assertEqual(status, 303)

    def test_falscher_login_401_generisch(self):
        body = urllib.parse.urlencode({"login": "a@x.de", "password": "FALSCH"})
        status, data, _ = self._req("POST", "/login", body=body)
        self.assertEqual(status, 401)
        self.assertIn("falsch", data.lower())

    def test_login_dann_eigene_leads(self):
        cookie = self._login("a@x.de", "GeheimA1")
        status, data, _ = self._req("GET", "/", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertIn("Wiesmann Metallbau GmbH", data)     # muensterland-Lead sichtbar
        self.assertNotIn("Hasetal", data)                  # osnabrueck-Lead NICHT sichtbar

    def test_cross_mandant_detail_404(self):
        cookie = self._login("a@x.de", "GeheimA1")
        # eigener Lead → 200
        s1, _d1, _ = self._req("GET", "/lead/SEE-DEMO-MS-01", cookie=cookie)
        self.assertEqual(s1, 200)
        # fremder (Osnabrück) Lead → 404 (Mandanten-Trennung, kein Existenz-Leak)
        s2, _d2, _ = self._req("GET", "/lead/SEE-DEMO-OS-01", cookie=cookie)
        self.assertEqual(s2, 404)

    def test_kunde_b_sieht_nur_b(self):
        cookie = self._login("b@x.de", "GeheimB1")
        status, data, _ = self._req("GET", "/", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertIn("Hasetal", data)
        self.assertNotIn("Wiesmann", data)

    def test_logout_mit_csrf_invalidiert_session(self):
        cookie = self._login("a@x.de", "GeheimA1")
        _s, page, _ = self._req("GET", "/", cookie=cookie)
        m = re.search(r'name=csrf value="([^"]+)"', page)
        self.assertIsNotNone(m, "CSRF-Token im Logout-Formular erwartet")
        body = urllib.parse.urlencode({"csrf": m.group(1)})
        status, _d, sc = self._req("POST", "/logout", cookie=cookie, body=body)
        self.assertEqual(status, 303)
        self.assertIn("Max-Age=0", sc or "")               # Cookie gelöscht
        # alte Session ist tot → / leitet wieder auf Login
        s2, _d2, _ = self._req("GET", "/", cookie=cookie)
        self.assertEqual(s2, 303)

    def test_relogin_invalidiert_alte_session(self):
        # H1: zweiter Login macht das erste Token sofort ungültig (Single-Active-Session).
        cookie1 = self._login("a@x.de", "GeheimA1")
        s1, _d, _ = self._req("GET", "/", cookie=cookie1)
        self.assertEqual(s1, 200)
        cookie2 = self._login("a@x.de", "GeheimA1")
        self.assertNotEqual(cookie1, cookie2)
        s_alt, _d2, _ = self._req("GET", "/", cookie=cookie1)
        self.assertEqual(s_alt, 303)                          # altes Token tot
        s_neu, _d3, _ = self._req("GET", "/", cookie=cookie2)
        self.assertEqual(s_neu, 200)                          # neues Token lebt

    def test_oversized_body_413(self):
        # M2: überlanger POST-Body → 413 (kein OOM-Read).
        gross = "x=" + ("a" * (70 * 1024))
        status, _d, _ = self._req("POST", "/login", body=gross)
        self.assertEqual(status, 413)


if __name__ == "__main__":
    unittest.main(verbosity=2)
