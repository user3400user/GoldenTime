"""
Beweist die ABR-Speicher-Anywhere-Logik gegen ein synthetisches SQLite — OHNE den
~3-GB-Download und OHNE open-mastr. Deckt die drei Klassen (kein Speicher gemeldet /
Speicher beim Betreiber anderswo / Speicher am Standort), die Trigger-Ableitung
(T1/T2/T3) und die Frische-Validierung (R3 §7b) ab.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_speicher_abr
"""
from __future__ import annotations

import datetime as dt
import sqlite3
import unittest

from pipeline import normalize
from pipeline.speicher_check import (
    COLOCATED,
    NONE_REPORTED,
    OPERATOR_ELSEWHERE,
    build_storage_index,
)

HEUTE = dt.date.today()
FRISCH_REG = (HEUTE - dt.timedelta(days=5)).isoformat()    # innerhalb Frische-Fenster
FRISCH_IBN = (HEUTE - dt.timedelta(days=9)).isoformat()    # plausibel kurz vor Registrierung

SOLAR_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer",
    "AnlagenbetreiberName", "AnlagenbetreiberPersonenArt", "Postleitzahl", "Ort",
    "Bundesland", "Bruttoleistung", "Registrierungsdatum", "Inbetriebnahmedatum",
    "EegInbetriebnahmedatum", "Einspeisungsart", "EinheitBetriebsstatus",
    "SpeicherAmGleichenOrt",
]
STORAGE_COLS = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer"]

#  Einheit, ABR,    Lokation, Name, PersonenArt, PLZ, Ort, BL, kWp, reg, ibn, eeg, Einsp, Status, SpeicherAmOrt
SOLAR_ROWS = [
    # S1 — Betreiber ohne Speicher -> none_reported, frisch -> T1
    ("SEE1", "ABR_A", "SEL_A1", "Müller GmbH", "Juristische Person", "48143", "Münster", "NRW",
     "100", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung", "In Betrieb", "0"),
    # S2 — SpeicherAmGleichenOrt=1 -> colocated -> Ausschluss
    ("SEE2", "ABR_B", "SEL_B2", "Bäcker KG", "Juristische Person", "48155", "Münster", "NRW",
     "200", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung", "In Betrieb", "1"),
    # S3 — Betreiber hat Speicher an ANDERER Lokation -> operator_elsewhere -> Premium
    ("SEE3", "ABR_C", "SEL_C3", "Schmidt AG", "Juristische Person", "59065", "Hamm", "NRW",
     "150", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung", "In Betrieb", "0"),
    # S4 — PV-Lokation führt selbst einen Speicher (Lokations-Match) -> colocated
    ("SEE4", "ABR_D", "SEL_D4", "Weber e.K.", "Natürliche Person", "70173", "Stuttgart", "BW",
     "300", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung", "In Betrieb", "0"),
    # S5 — Post-EEG-Jahrgang 2006 -> T2
    ("SEE5", "ABR_E", "SEL_E5", "Fischer GmbH", "Juristische Person", "80331", "München", "BY",
     "90", FRISCH_REG, "2006-04-01", "2006-04-01", "Volleinspeisung", "In Betrieb", "0"),
    # S6 — frisches reg_datum, aber Inbetriebnahme 2014 -> Nachregistrierungs-Verdacht (FRISCHE_WARNUNG)
    ("SEE6", "ABR_F", "SEL_F6", "Klein OHG", "Juristische Person", "49074", "Osnabrück", "NDS",
     "500", FRISCH_REG, "2014-05-01", None, "Teileinspeisung", "In Betrieb", "0"),
    # S7 — kWp 5 (< 30) -> herausgefiltert (taucht nie als Lead auf)
    ("SEE7", "ABR_G", "SEL_G7", "Mini UG", "Juristische Person", "48999", "Münster", "NRW",
     "5", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung", "In Betrieb", "0"),
    # S8 — stillgelegt -> herausgefiltert (nur_in_betrieb)
    ("SEE8", "ABR_H", "SEL_H8", "Alt GmbH", "Juristische Person", "48888", "Münster", "NRW",
     "120", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung", "Endgültig stillgelegt", "0"),
]
STORAGE_ROWS = [
    ("SSE_C", "ABR_C", "SEL_C9"),   # Speicher von ABR_C an anderer Lokation -> S3 = operator_elsewhere
    ("SSE_D", "ABR_D", "SEL_D4"),   # Speicher an SEL_D4 -> S4 colocated via Lokation
    ("SSE_X", "", ""),               # leere ABR -> muss aus dem Index gefiltert werden
]


def _build_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})')
    con.execute(f'CREATE TABLE storage_extended ({", ".join(f"\"{c}\" TEXT" for c in STORAGE_COLS)})')
    con.executemany(
        f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})', SOLAR_ROWS
    )
    con.executemany(
        f'INSERT INTO storage_extended VALUES ({", ".join("?" for _ in STORAGE_COLS)})', STORAGE_ROWS
    )
    con.commit()
    return con


class TestStorageIndex(unittest.TestCase):
    def setUp(self):
        self.con = _build_db()
        self.index = build_storage_index(self.con)

    def tearDown(self):
        self.con.close()

    def test_index_filters_empty_abr(self):
        self.assertEqual(self.index.operators, frozenset({"ABR_C", "ABR_D"}))
        self.assertEqual(self.index.locations, frozenset({"SEL_C9", "SEL_D4"}))

    def test_classify_three_ways(self):
        c = self.index.classify
        self.assertEqual(c("ABR_A", "SEL_A1", "0"), NONE_REPORTED)          # kein Speicher
        self.assertEqual(c("ABR_B", "SEL_B2", "1"), COLOCATED)             # Flag am Ort
        self.assertEqual(c("ABR_C", "SEL_C3", "0"), OPERATOR_ELSEWHERE)    # anderswo
        self.assertEqual(c("ABR_D", "SEL_D4", "0"), COLOCATED)            # Lokations-Match
        self.assertEqual(c("ABR_E", "SEL_E5", "0"), NONE_REPORTED)

    def test_truthy_variants(self):
        self.assertEqual(self.index.classify("ABR_A", "SEL_A1", "true"), COLOCATED)
        self.assertEqual(self.index.classify("ABR_A", "SEL_A1", 1), COLOCATED)
        self.assertEqual(self.index.classify("ABR_A", "SEL_A1", None), NONE_REPORTED)


class TestIterLeads(unittest.TestCase):
    def setUp(self):
        self.con = _build_db()
        self.index = build_storage_index(self.con)

    def tearDown(self):
        self.con.close()

    def _leads_by_id(self, **kw):
        return {l["einheit_mastr_nr"]: l for l in normalize.iter_leads(self.con, self.index, **kw)}

    def test_region_filter_and_exclusions(self):
        leads = self._leads_by_id(plz_prefixes=("48",))
        # 48er: S1 (lieferbar), S2 (colocated), S7 (zu klein -> raus), S8 (stillgelegt -> raus)
        self.assertIn("SEE1", leads)
        self.assertIn("SEE2", leads)
        self.assertNotIn("SEE7", leads)   # kWp < 30
        self.assertNotIn("SEE8", leads)   # nicht in Betrieb
        self.assertIsNone(leads["SEE1"]["ausschluss_grund"])
        self.assertEqual(leads["SEE2"]["ausschluss_grund"], "speicher_colocated")

    def test_labels_and_premium_flag(self):
        s3 = self._leads_by_id(plz_prefixes=("59",))["SEE3"]
        self.assertEqual(s3["speicher_status"], OPERATOR_ELSEWHERE)
        self.assertIn("PREMIUM_SPEICHER_ANDERER_STANDORT", s3["flags"])
        s1 = self._leads_by_id(plz_prefixes=("48",))["SEE1"]
        self.assertEqual(s1["speicher_label"], "kein Speicher gemeldet")

    def test_trigger_classification(self):
        self.assertEqual(self._leads_by_id(plz_prefixes=("48",))["SEE1"]["trigger_typ"], "T1")
        self.assertEqual(self._leads_by_id(plz_prefixes=("80",))["SEE5"]["trigger_typ"], "T2")

    def test_freshness_validation(self):
        s6 = self._leads_by_id(plz_prefixes=("49",))["SEE6"]
        self.assertFalse(s6["frische_valide"])
        self.assertIn("FRISCHE_WARNUNG", s6["flags"])
        self.assertIn("Nachregistrierung", s6["frische_warnung"])

    def test_ek_caveat_flag_not_hard_exclude(self):
        # Weber e.K. ist "Natürliche Person" -> markiert (QA), aber NICHT automatisch verworfen.
        s4 = self._leads_by_id(plz_prefixes=("70",))["SEE4"]
        self.assertIn("NATUERLICHE_PERSON_PRUEFEN", s4["flags"])

    def test_no_region_requires_limit(self):
        with self.assertRaises(ValueError):
            list(normalize.iter_leads(self.con, self.index))


if __name__ == "__main__":
    unittest.main(verbosity=2)
