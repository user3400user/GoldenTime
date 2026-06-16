"""
Tests für Komponente 3 — Cohort-Trigger T2 (Post-EEG + DV-Flag), stdlib & synthetisch.

Beweist gegen ein In-Memory-SQLite (solar_extended + solar_eeg + storage_extended), OHNE
~3-GB-Download und OHNE open-mastr:
  * nur EEG-Inbetriebnahmejahr 2006/2007 wird zum Signal,
  * der EEG-Join-Datum schlägt das Einheiten-Inbetriebnahmedatum (Präzision),
  * COLOCATED (Speicher am Standort / Lokations-Match) wird ausgeschlossen,
  * das kWp-Band (KWP_MIN..KWP_MAX) greift,
  * DV-Flag ab 100 kWp,
  * trigger_typ == 'T2', Datum = EEG-IBN, entity bleibt None (Qualifizierer macht den Namen),
  * operator_elsewhere -> Premium-Flag + volle Konfidenz.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_cohort
"""
from __future__ import annotations

import sqlite3
import unittest

from pipeline import config
from pipeline.speicher_check import OPERATOR_ELSEWHERE, build_storage_index
from pipeline.triggers import TRIGGER_KEY, cohort_signals, dv_flag_count

SOLAR_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer",
    "AnlagenbetreiberPersonenArt", "Postleitzahl", "Ort", "Bundesland",
    "Bruttoleistung", "Registrierungsdatum", "Inbetriebnahmedatum",
    "EegMaStRNummer", "Einspeisungsart", "EinheitBetriebsstatus",
    "SpeicherAmGleichenOrt",
]
# solar_eeg: 1:1 zu solar, Join über EegMaStRNummer, EegInbetriebnahmedatum 100 %.
EEG_COLS = ["EegMaStRNummer", "EegInbetriebnahmedatum"]
STORAGE_COLS = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer"]

#  Einheit, ABR, Lokation, PersonenArt, PLZ, Ort, BL, kWp, reg, ibn, eeg_nr, Einsp, Status, SpeicherAmOrt
SOLAR_ROWS = [
    # P1 — EEG-IBN 2006, kein Speicher, 120 kWp -> T2, DV-Flag, none_reported
    ("SEE1", "ABR_A", "SEL_A1", "Organisation (Unternehmen)", "80331", "München", "Bayern",
     "120", "2007-01-10", "2006-04-01", "EEG1", "Volleinspeisung", "In Betrieb", "0"),
    # P2 — EEG-IBN 2007, kein Speicher, 60 kWp -> T2, KEIN DV-Flag (<100)
    ("SEE2", "ABR_B", "SEL_B2", "Organisation (Unternehmen)", "80333", "München", "Bayern",
     "60", "2008-02-01", "2007-07-20", "EEG2", "Teileinspeisung", "In Betrieb", "0"),
    # P3 — Einheiten-IBN 2006, ABER EEG-IBN 2010 -> EEG-Join schlägt IBN -> KEIN T2 (raus)
    ("SEE3", "ABR_C", "SEL_C3", "Organisation (Unternehmen)", "80335", "München", "Bayern",
     "200", "2006-03-01", "2006-03-01", "EEG3", "Volleinspeisung", "In Betrieb", "0"),
    # P4 — EEG-IBN 2006, aber SpeicherAmGleichenOrt=1 -> COLOCATED -> ausgeschlossen
    ("SEE4", "ABR_D", "SEL_D4", "Organisation (Unternehmen)", "80337", "München", "Bayern",
     "150", "2007-01-01", "2006-05-01", "EEG4", "Volleinspeisung", "In Betrieb", "1"),
    # P5 — EEG-IBN 2007, aber kWp 800 (> KWP_MAX) -> herausgefiltert
    ("SEE5", "ABR_E", "SEL_E5", "Organisation (Unternehmen)", "80339", "München", "Bayern",
     "800", "2008-01-01", "2007-02-02", "EEG5", "Volleinspeisung", "In Betrieb", "0"),
    # P6 — EEG-IBN 2007, aber kWp 20 (< KWP_MIN) -> herausgefiltert
    ("SEE6", "ABR_F", "SEL_F6", "Organisation (Unternehmen)", "80331", "München", "Bayern",
     "20", "2008-01-01", "2007-03-03", "EEG6", "Volleinspeisung", "In Betrieb", "0"),
    # P7 — EEG-IBN 2005 (kein Post-EEG-Jahrgang) -> kein Signal
    ("SEE7", "ABR_G", "SEL_G7", "Organisation (Unternehmen)", "80331", "München", "Bayern",
     "300", "2006-01-01", "2005-12-01", "EEG7", "Volleinspeisung", "In Betrieb", "0"),
    # P8 — EEG-IBN 2006, Betreiber hat Speicher an ANDERER Lokation -> operator_elsewhere -> Premium
    ("SEE8", "ABR_H", "SEL_H8", "Organisation (Unternehmen)", "80331", "München", "Bayern",
     "250", "2007-01-01", "2006-09-09", "EEG8", "Volleinspeisung", "In Betrieb", "0"),
    # P9 — EEG-IBN 2006, aber stillgelegt -> herausgefiltert (nur in Betrieb)
    ("SEE9", "ABR_I", "SEL_I9", "Organisation (Unternehmen)", "80331", "München", "Bayern",
     "180", "2007-01-01", "2006-06-06", "EEG9", "Volleinspeisung", "Endgültig stillgelegt", "0"),
    # P10 — kein EEG-Datensatz (Join->NULL), Einheiten-IBN 2006 -> Fallback greift -> T2
    ("SEE10", "ABR_J", "SEL_J10", "Organisation (Unternehmen)", "80331", "München", "Bayern",
     "110", "2007-01-01", "2006-08-08", "EEG_FEHLT", "Volleinspeisung", "In Betrieb", "0"),
    # P11 — EEG-IBN 2006, aber andere Region (PLZ 48...) -> PLZ-Filter raus
    ("SEE11", "ABR_K", "SEL_K11", "Organisation (Unternehmen)", "48143", "Münster", "NRW",
     "140", "2007-01-01", "2006-10-10", "EEG11", "Volleinspeisung", "In Betrieb", "0"),
]
EEG_ROWS = [
    ("EEG1", "2006-04-01"),
    ("EEG2", "2007-07-20"),
    ("EEG3", "2010-03-01"),   # EEG-IBN 2010 schlägt Einheiten-IBN 2006 -> P3 raus
    ("EEG4", "2006-05-01"),
    ("EEG5", "2007-02-02"),
    ("EEG6", "2007-03-03"),
    ("EEG7", "2005-12-01"),
    ("EEG8", "2006-09-09"),
    ("EEG9", "2006-06-06"),
    # EEG_FEHLT bewusst NICHT eingetragen -> LEFT JOIN liefert NULL -> Fallback auf Einheiten-IBN
    ("EEG11", "2006-10-10"),
]
STORAGE_ROWS = [
    ("SSE_H", "ABR_H", "SEL_H99"),   # Speicher von ABR_H an anderer Lokation -> P8 operator_elsewhere
    ("SSE_X", "", ""),                # leere ABR -> aus dem Index gefiltert
]


def _build_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})')
    con.execute(f'CREATE TABLE solar_eeg ({", ".join(f"\"{c}\" TEXT" for c in EEG_COLS)})')
    con.execute(f'CREATE TABLE storage_extended ({", ".join(f"\"{c}\" TEXT" for c in STORAGE_COLS)})')
    con.executemany(
        f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})', SOLAR_ROWS
    )
    con.executemany(
        f'INSERT INTO solar_eeg VALUES ({", ".join("?" for _ in EEG_COLS)})', EEG_ROWS
    )
    con.executemany(
        f'INSERT INTO storage_extended VALUES ({", ".join("?" for _ in STORAGE_COLS)})', STORAGE_ROWS
    )
    con.commit()
    return con


class TestCohortT2(unittest.TestCase):
    def setUp(self):
        self.con = _build_db()
        self.index = build_storage_index(self.con)

    def tearDown(self):
        self.con.close()

    def _by_id(self, **kw):
        return {
            s.einheit_mastr_nr: s
            for s in cohort_signals(self.con, self.index, plz_prefixes=("80",), **kw)
        }

    def test_only_post_eeg_years_emit(self):
        sigs = self._by_id()
        # T2-Treffer im 80er-Gebiet: P1, P2, P8, P10 (Fallback). NICHT: P3 (EEG 2010),
        # P4 (colocated), P5 (zu groß), P6 (zu klein), P7 (EEG 2005), P9 (stillgelegt).
        self.assertEqual(set(sigs), {"SEE1", "SEE2", "SEE8", "SEE10"})

    def test_trigger_typ_is_t2(self):
        for s in self._by_id().values():
            self.assertEqual(s.trigger_typ, "T2")
            self.assertEqual(s.trigger_typ, TRIGGER_KEY)

    def test_eeg_join_beats_unit_ibn(self):
        # P3: Einheiten-IBN 2006, EEG-IBN 2010 -> nicht in der Kohorte.
        self.assertNotIn("SEE3", self._by_id())
        # P1: maßgebliches Datum ist die EEG-Inbetriebnahme, nicht die Einheiten-IBN (2007-01-10).
        self.assertEqual(self._by_id()["SEE1"].datum, "2006-04-01")

    def test_eeg_missing_falls_back_to_unit_ibn(self):
        # P10: kein EEG-Datensatz -> Fallback auf Einheiten-IBN 2006 -> Signal, Datum = IBN.
        s = self._by_id()["SEE10"]
        self.assertEqual(s.datum, "2006-08-08")

    def test_colocated_excluded(self):
        self.assertNotIn("SEE4", self._by_id())

    def test_kwp_band(self):
        sigs = self._by_id()
        self.assertNotIn("SEE5", sigs)   # 800 > KWP_MAX
        self.assertNotIn("SEE6", sigs)   # 20 < KWP_MIN
        # Bandgrenze über Parameter steuerbar:
        only_big = self._by_id(kwp_min=200.0)
        self.assertNotIn("SEE1", only_big)   # 120 < 200
        self.assertIn("SEE8", only_big)      # 250

    def test_dv_flag_threshold(self):
        sigs = self._by_id()
        self.assertTrue(sigs["SEE1"].dv_flag)    # 120 kWp >= 100
        self.assertFalse(sigs["SEE2"].dv_flag)   # 60 kWp < 100
        self.assertEqual(config.DV_FLAG_MIN_KWP, 100.0)

    def test_dv_flag_count_helper(self):
        sigs = list(cohort_signals(self.con, self.index, plz_prefixes=("80",)))
        # P1(120), P8(250), P10(110) sind >=100; P2(60) nicht.
        self.assertEqual(dv_flag_count(sigs), 3)

    def test_operator_elsewhere_premium(self):
        s = self._by_id()["SEE8"]
        self.assertEqual(s.speicher_status, OPERATOR_ELSEWHERE)
        self.assertIn("PREMIUM_SPEICHER_ANDERER_STANDORT", s.flags)
        self.assertEqual(s.konfidenz, 1.0)        # operator_elsewhere: kein Abschlag
        self.assertIn("Premium", s.buy_relevanz)

    def test_none_reported_konfidenz_abschlag(self):
        # P1: none_reported -> Konfidenz-Abschlag (~9 % unregistriert).
        s = self._by_id()["SEE1"]
        self.assertEqual(s.speicher_status, "none_reported")
        self.assertEqual(s.konfidenz, 0.90)
        self.assertIn("Post-EEG", s.buy_relevanz)

    def test_entity_none_region_set(self):
        s = next(iter(cohort_signals(
            self.con, self.index, plz_prefixes=("80",), region="München-Süd"
        )))
        self.assertIsNone(s.entity)               # Name macht der Qualifizierer
        self.assertEqual(s.region, "München-Süd")

    def test_region_filter(self):
        # PLZ-Filter '80' lässt das Münsteraner P11 (48143) draußen.
        self.assertNotIn("SEE11", self._by_id())
        muenster = {
            s.einheit_mastr_nr
            for s in cohort_signals(self.con, self.index, plz_prefixes=("48",))
        }
        self.assertEqual(muenster, {"SEE11"})

    def test_custom_jahrgaenge(self):
        # Auf 2007 eingeschränkt: nur P2 bleibt (P1/P8/P10 sind 2006).
        sigs = {
            s.einheit_mastr_nr
            for s in cohort_signals(self.con, self.index, plz_prefixes=("80",), jahrgaenge=(2007,))
        }
        self.assertEqual(sigs, {"SEE2"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
