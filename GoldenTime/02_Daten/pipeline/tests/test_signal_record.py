"""
Tests für Komponente 5 (SignalRecord + from_lead) — stdlib, synthetisch, ohne Daten.

Deckt: Konfidenz-Pflichtfeld + Wertebereich, Evidenz-URL, Konfidenz-Abschläge aus den Gotchas,
DV-Flag-Schwelle, und das Mapping normalize-Lead-Dict → SignalRecord.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_signal_record
"""
from __future__ import annotations

import datetime as dt
import unittest

from pipeline import config
from pipeline.signal import SignalRecord, compute_konfidenz, from_lead, mastr_einheit_url
from pipeline.signal.record import KONF_MIN


def _lead(**over):
    base = {
        "einheit_mastr_nr": "SEE900000001",
        "betreiber_mastr_nr": "ABR900000001",
        "betreiber": None,                 # noch kein market_actors-Join
        "plz": "48143", "ort": "Münster", "bundesland": "Nordrhein-Westfalen",
        "kwp": 120.0, "einspeisung": "Teileinspeisung (einschließlich Eigenverbrauch)",
        "reg_datum": "2026-06-01", "inbetriebnahme": "2026-05-20",
        "speicher_status": "none_reported", "speicher_label": "kein Speicher gemeldet",
        "trigger_typ": "T1", "frische_valide": True,
        "flags": ["NATUERLICHE_PERSON_PRUEFEN"],
        "geprueft_am": "2026-06-16", "provenance": "MaStR Gesamtdatenexport",
    }
    base.update(over)
    return base


class TestKonfidenzPflicht(unittest.TestCase):
    def test_konfidenz_required(self):
        with self.assertRaises(ValueError):
            SignalRecord("SEE1", "ABR1", "T2", "2006-01-01", None, "x")

    def test_konfidenz_range(self):
        with self.assertRaises(ValueError):
            SignalRecord("SEE1", "ABR1", "T2", "2006-01-01", 1.5, "x")
        with self.assertRaises(ValueError):
            SignalRecord("SEE1", "ABR1", "T2", "2006-01-01", -0.1, "x")

    def test_einheit_required(self):
        with self.assertRaises(ValueError):
            SignalRecord("", "ABR1", "T2", "2006-01-01", 0.9, "x")


class TestEvidenzUrl(unittest.TestCase):
    def test_url_built_from_einheit(self):
        r = SignalRecord("SEE900000123", "ABR1", "T2", "2006-01-01", 0.9, "x")
        self.assertIn("SEE900000123", r.evidenz_url)
        self.assertTrue(r.evidenz_url.startswith("https://www.marktstammdatenregister.de/"))
        self.assertEqual(mastr_einheit_url("SEE900000123"), r.evidenz_url)


class TestKonfidenzModell(unittest.TestCase):
    def test_none_reported_abschlag(self):
        k, gruende = compute_konfidenz("T1", "none_reported", True)
        self.assertEqual(k, 0.90)
        self.assertTrue(any("kein Speicher" in g for g in gruende))

    def test_operator_elsewhere_voll(self):
        k, gruende = compute_konfidenz("T1", "operator_elsewhere", True)
        self.assertEqual(k, 1.0)
        self.assertEqual(gruende, ())

    def test_frische_warnung_abschlag(self):
        k, gruende = compute_konfidenz("T1", "none_reported", False)
        self.assertAlmostEqual(k, 0.65, places=2)   # 1.0 - 0.10 - 0.25
        self.assertTrue(any("Frische" in g for g in gruende))

    def test_t4_retrofit_luecke(self):
        k, gruende = compute_konfidenz("T4", "operator_elsewhere", True)
        self.assertAlmostEqual(k, 0.85, places=2)
        self.assertTrue(any("Retrofit" in g for g in gruende))

    def test_floor(self):
        # alle Abschläge gleichzeitig bleibt >= KONF_MIN
        k, _ = compute_konfidenz("T4", "none_reported", False)
        self.assertGreaterEqual(k, KONF_MIN)


class TestFromLead(unittest.TestCase):
    def test_maps_core_fields(self):
        r = from_lead(_lead(), region="Münsterland")
        self.assertEqual(r.einheit_mastr_nr, "SEE900000001")
        self.assertEqual(r.trigger_typ, "T1")
        self.assertEqual(r.datum, "2026-05-20")           # IBN bevorzugt
        self.assertEqual(r.region, "Münsterland")
        self.assertEqual(r.konfidenz, 0.90)               # none_reported
        self.assertIn("NATUERLICHE_PERSON_PRUEFEN", r.flags)
        self.assertIsNone(r.entity)                       # kein Join → None

    def test_dv_flag_threshold(self):
        self.assertTrue(from_lead(_lead(kwp=100.0)).dv_flag)
        self.assertTrue(from_lead(_lead(kwp=260.0)).dv_flag)
        self.assertFalse(from_lead(_lead(kwp=99.0)).dv_flag)
        self.assertIn("Direktvermarktung", from_lead(_lead(kwp=120.0)).buy_relevanz)

    def test_post_eeg_buy_relevanz(self):
        r = from_lead(_lead(trigger_typ="T2", inbetriebnahme="2006-04-01", kwp=80.0))
        self.assertIn("Post-EEG", r.buy_relevanz)
        self.assertFalse(r.dv_flag)

    def test_premium_note(self):
        r = from_lead(_lead(speicher_status="operator_elsewhere",
                            speicher_label="Speicher beim Betreiber (anderer Standort) gemeldet"))
        self.assertIn("Premium", r.buy_relevanz)
        self.assertEqual(r.konfidenz, 1.0)

    def test_to_row_csv_shape(self):
        row = from_lead(_lead()).to_row()
        self.assertEqual(set(row.keys()), set(SignalRecord.CSV_FIELDS))
        self.assertIn("marktstammdatenregister.de", row["evidenz_url"])
        self.assertEqual(row["flags"], "NATUERLICHE_PERSON_PRUEFEN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
