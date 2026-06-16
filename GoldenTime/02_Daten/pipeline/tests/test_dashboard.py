"""
Tests für das Admin-Dashboard (K8) + §6-Metriken — stdlib, synthetisch, OHNE echten Socket/Server.

Geprüft wird die testbare Substanz:
  * views.render_dashboard — reine HTML-Erzeugung aus ConfigStore + Metrik-/Ledger-Zeilen
    (Default-Store + leere/synthetische Zeilen → String enthält die Trigger-Labels, escaped, sicher).
  * control/metrics.record + aggregate/latest_by_dimension — Roundtrip gegen state.connect(temp).
  * app.apply_toggle / set_* — Schalter-Mutation als reine Funktion (kein HTTP).

KEIN http.server-Bind, KEIN open-mastr, KEIN Export-Download (Briefing: Render- + Metrik-Funktionen).

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_dashboard
"""
from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from pipeline import ledger
from pipeline.control import config_store as cs
from pipeline.control import metrics
from pipeline.control import state
from pipeline.dashboard import app, views

DEFAULT_STORE = cs.load(Path("/nonexistent/config_store.json"))  # eingebaute Defaults


class TestRenderDashboard(unittest.TestCase):
    def test_leere_daten_liefert_html_mit_trigger_labels(self):
        html = views.render_dashboard(DEFAULT_STORE, [], [])
        self.assertTrue(html.startswith("<!doctype html>"))
        # alle Trigger-Schlüssel + ihre Default-Labels müssen auftauchen
        for key in cs.VALID_TRIGGERS:
            self.assertIn(key, html)
            label = DEFAULT_STORE.triggers[key]["label"]
            # Label kann '&'/'>' enthalten -> escaped vergleichen (z.B. '>=100')
            import html as _h
            self.assertIn(_h.escape(label), html)
        # Modul-Schalter + Gebiete sind sichtbar
        self.assertIn("anreicherung", html)
        self.assertIn("muensterland", html)
        # leere Tabellen tragen ihre Platzhalter
        self.assertIn("Noch keine Metriken erfasst.", html)
        self.assertIn("Keine aktiven Reservierungen.", html)

    def test_an_aus_zustand_wird_angezeigt(self):
        html = views.render_dashboard(DEFAULT_STORE, [], [])
        # T1 default an, T5 default aus -> beide Zustände im HTML
        self.assertIn("AN", html)
        self.assertIn("AUS", html)

    def test_synthetische_metrik_und_ledger_zeilen_im_html(self):
        metrics_rows = [
            {"woche": "2026-W25", "gebiet": "muensterland", "trigger": "T2",
             "metrik": "signale", "summe": 1614.0, "anzahl": 1,
             "letzte_erfassung": "2026-06-16T10:00:00+00:00"},
        ]
        ledger_rows = [
            {"funktion": "speicher_installateur", "gebiet": "muensterland",
             "trigger": "T2", "kaeufer": "KaeuferA", "status": "aktiv",
             "reserviert_am": "2026-06-16"},
        ]
        html = views.render_dashboard(DEFAULT_STORE, metrics_rows, ledger_rows)
        self.assertIn("2026-W25", html)
        self.assertIn("signale", html)
        self.assertIn("1614", html)            # Volumen je Gebiet×Trigger×Woche
        self.assertIn("speicher_installateur", html)
        self.assertIn("KaeuferA", html)

    def test_html_escaped_keine_injection(self):
        # bösartiger Gebietsname (Config ist menschlich editierbar) darf nicht roh durchschlagen
        gebiete = ({"id": "x", "name": "<script>alert(1)</script>", "enabled": True,
                    "plz_prefixes": ["99"], "trigger_overrides": {}},)
        store = cs.ConfigStore(DEFAULT_STORE.schema_version, DEFAULT_STORE.triggers,
                               DEFAULT_STORE.modules, gebiete)
        html = views.render_dashboard(store, [], [])
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_gebiet_override_nur_abschaltung_sichtbar(self):
        gebiete = ({"id": "m", "name": "M", "enabled": True, "plz_prefixes": ["48"],
                    "trigger_overrides": {"T2": False}},)
        store = cs.ConfigStore(DEFAULT_STORE.schema_version, DEFAULT_STORE.triggers,
                               DEFAULT_STORE.modules, gebiete)
        html = views.render_dashboard(store, [], [])
        self.assertIn("Trigger aus (Override)", html)


class TestMetricsRoundtrip(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = state.connect(Path(self._tmp.name) / "pipeline_state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_iso_woche_format(self):
        # 2026-06-16 ist ISO-Woche 25
        self.assertEqual(metrics.iso_woche(dt.date(2026, 6, 16)), "2026-W25")

    def test_record_default_woche_ist_aktuelle(self):
        metrics.record(self.con, metrik="signale", wert=42)
        row = self.con.execute("SELECT woche, metrik, wert FROM metrics_event").fetchone()
        self.assertEqual(row["woche"], metrics.iso_woche())
        self.assertEqual(row["metrik"], "signale")
        self.assertEqual(row["wert"], 42.0)

    def test_record_leere_metrik_raises(self):
        with self.assertRaises(ValueError):
            metrics.record(self.con, metrik="", wert=1)

    def test_aggregate_idempotent_je_dimension(self):
        # Fix 16.06.: record() ist idempotent je (woche, gebiet, trigger, metrik) — ein erneuter Lauf
        # DERSELBEN Woche ersetzt den Wert, statt ihn zu addieren (kein 2x-Count-Doubling).
        metrics.record(self.con, metrik="signale", wert=10, woche="2026-W25",
                       gebiet="muensterland", trigger="T2")
        metrics.record(self.con, metrik="signale", wert=5, woche="2026-W25",
                       gebiet="muensterland", trigger="T2")
        metrics.record(self.con, metrik="signale", wert=7, woche="2026-W25",
                       gebiet="osnabrueck", trigger="T1")
        rows = metrics.aggregate(self.con)
        # zwei Dimensionen (muensterland/T2, osnabrueck/T1)
        self.assertEqual(len(rows), 2)
        by_geb = {r["gebiet"]: r for r in rows}
        self.assertEqual(by_geb["muensterland"]["summe"], 5.0)    # ersetzt (Letztwert), NICHT 15
        self.assertEqual(by_geb["muensterland"]["anzahl"], 1)     # nur eine Zeile je Dimension
        self.assertEqual(by_geb["osnabrueck"]["summe"], 7.0)

    def test_aggregate_filter_gebiet(self):
        metrics.record(self.con, metrik="signale", wert=10, gebiet="muensterland", trigger="T2")
        metrics.record(self.con, metrik="signale", wert=7, gebiet="osnabrueck", trigger="T1")
        rows = metrics.aggregate(self.con, gebiet="osnabrueck")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["gebiet"], "osnabrueck")

    def test_aggregate_leer(self):
        self.assertEqual(metrics.aggregate(self.con), [])

    def test_latest_by_dimension_nimmt_juengste_woche(self):
        metrics.record(self.con, metrik="signale", wert=100, woche="2026-W24",
                       gebiet="muensterland", trigger="T2")
        metrics.record(self.con, metrik="signale", wert=160, woche="2026-W25",
                       gebiet="muensterland", trigger="T2")
        rows = metrics.latest_by_dimension(self.con)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["woche"], "2026-W25")     # jüngste Woche gewinnt
        self.assertEqual(rows[0]["summe"], 160.0)

    def test_render_konsumiert_echte_aggregat_zeilen(self):
        # End-to-End der Lese-Seite: record -> aggregate -> render (ohne Server)
        metrics.record(self.con, metrik="lieferbar", wert=12488, woche="2026-W25",
                       gebiet="muensterland", trigger="T2")
        ledger.reserve(self.con, "speicher_installateur", "muensterland", "T2", "KaeuferA")
        html = views.render_dashboard(DEFAULT_STORE,
                                      metrics.aggregate(self.con),
                                      ledger.overview(self.con))
        self.assertIn("lieferbar", html)
        self.assertIn("12488", html)
        self.assertIn("KaeuferA", html)


class TestApplyToggle(unittest.TestCase):
    def test_set_trigger_kippt_zustand(self):
        # T5 default aus -> einschalten
        updated = app.set_trigger(DEFAULT_STORE, "T5", True)
        self.assertTrue(updated.is_trigger_enabled("T5"))
        # Original (frozen) unverändert
        self.assertFalse(DEFAULT_STORE.is_trigger_enabled("T5"))

    def test_set_module(self):
        updated = app.set_module(DEFAULT_STORE, "anreicherung", True)
        self.assertTrue(updated.is_module_enabled("anreicherung"))
        self.assertFalse(DEFAULT_STORE.is_module_enabled("anreicherung"))

    def test_set_gebiet(self):
        # stuttgart default aus -> einschalten
        updated = app.set_gebiet(DEFAULT_STORE, "stuttgart", True)
        self.assertTrue(updated.gebiet("stuttgart")["enabled"])
        self.assertFalse(DEFAULT_STORE.gebiet("stuttgart")["enabled"])

    def test_apply_toggle_dispatch(self):
        updated = app.apply_toggle(DEFAULT_STORE, "trigger", "T1", False)
        self.assertFalse(updated.is_trigger_enabled("T1"))

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            app.apply_toggle(DEFAULT_STORE, "boese", "T1", True)

    def test_unknown_key_raises(self):
        with self.assertRaises(ValueError):
            app.set_trigger(DEFAULT_STORE, "T99", True)
        with self.assertRaises(ValueError):
            app.set_gebiet(DEFAULT_STORE, "atlantis", True)

    def test_apply_toggle_persistiert_ueber_save(self):
        # Toggle -> save -> reload: der geschaltete Zustand hält, updated_by='dashboard'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config_store.json"
            cs.save(DEFAULT_STORE, path=p)                 # Ausgangs-Store
            updated = app.apply_toggle(cs.load(p), "trigger", "T5", True)
            cs.save(updated, updated_by="dashboard", path=p)
            reloaded = cs.load(p)
            self.assertTrue(reloaded.is_trigger_enabled("T5"))
            self.assertEqual(reloaded.updated_by, "dashboard")


if __name__ == "__main__":
    unittest.main(verbosity=2)
