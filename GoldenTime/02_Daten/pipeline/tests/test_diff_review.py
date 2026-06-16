"""
Regression-Tests aus der Zweit-Review — Diff-Lieferpfad (Befunde 12-14 + T5-NULL-Schutz). stdlib.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_diff_review
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.control import config_store as cs
from pipeline.snapshot import rules as rulesmod
from pipeline.snapshot.diff import FIELD_CHANGED, DiffEvent
from pipeline.triggers import diff_based

_SNAP_DDL = ("CREATE TABLE snapshot (einheit_nr TEXT PRIMARY KEY, traeger TEXT, abr TEXT, "
             "eeg_nr TEXT, brutto_kw REAL, inbetriebnahme TEXT, datum_stilllegung_endg TEXT, "
             "datum_stilllegung_vorueb TEXT, betriebsstatus TEXT)")


def _snap(path: Path, rows: list[tuple]) -> None:
    con = sqlite3.connect(str(path))
    con.execute(_SNAP_DDL)
    con.executemany("INSERT INTO snapshot VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def _solar_con():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE solar_extended (EinheitMastrNummer TEXT, Postleitzahl TEXT, "
                "Ort TEXT, Bundesland TEXT)")
    con.executemany("INSERT INTO solar_extended VALUES (?,?,?,?)", [
        ("SEE_MS", "48143", "Münster", "Nordrhein-Westfalen"),
        ("SEE_BY", "80331", "München", "Bayern"),
    ])
    con.commit()
    return con


class TestT5NullGuard(unittest.TestCase):
    def test_abr_null_to_set_is_not_t5(self):
        # verspätete Erst-Registrierung des Betreibers (gleicher Eigentümer) -> KEIN Betreiberwechsel
        ev = DiffEvent("SEE1", "solar", "ABR_NEU", FIELD_CHANGED, field="abr", old="", new="ABR_NEU")
        self.assertIsNone(rulesmod.classify_diff(ev)[0])

    def test_real_abr_change_is_t5(self):
        ev = DiffEvent("SEE1", "solar", "ABR_B", FIELD_CHANGED, field="abr", old="ABR_A", new="ABR_B")
        self.assertEqual(rulesmod.classify_diff(ev)[0], rulesmod.T5)


class TestDiffRegionFilter(unittest.TestCase):
    def test_region_keeps_only_in_plz(self):
        with tempfile.TemporaryDirectory() as d:
            prev, curr = Path(d) / "prev.sqlite", Path(d) / "curr.sqlite"
            _snap(prev, [])  # leer -> alles in curr ist NEW_UNIT
            _snap(curr, [
                ("SEE_MS", "solar", "ABR1", "E1", "100", "2024-01-01", None, None, "In Betrieb"),
                ("SEE_BY", "solar", "ABR2", "E2", "100", "2024-01-01", None, None, "In Betrieb"),
            ])
            recs = list(diff_based.diff_based_signals(
                prev, curr, cs.defaults(), plz_prefixes=("48",), con=_solar_con()))
            # nur die Münster-Einheit bleibt; die Bayern-Einheit fällt aus dem Gebiet (Befund 14)
            self.assertEqual([r.einheit_mastr_nr for r in recs], ["SEE_MS"])
            self.assertEqual(recs[0].trigger_typ, "T1")
            self.assertEqual(recs[0].plz, "48143")

    def test_no_filter_keeps_all(self):
        with tempfile.TemporaryDirectory() as d:
            prev, curr = Path(d) / "prev.sqlite", Path(d) / "curr.sqlite"
            _snap(prev, [])
            _snap(curr, [
                ("SEE_MS", "solar", "ABR1", "E1", "100", "2024-01-01", None, None, "In Betrieb"),
                ("SEE_BY", "solar", "ABR2", "E2", "100", "2024-01-01", None, None, "In Betrieb"),
            ])
            recs = list(diff_based.diff_based_signals(prev, curr, cs.defaults(), con=_solar_con()))
            self.assertEqual(len(recs), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
