"""
Tests für pipeline_state.db (control/state.py) — stdlib, gegen temporäre DB-Dateien.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_state
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.control import state


class TestStateDb(unittest.TestCase):
    def _con(self, d):
        return state.connect(Path(d) / "pipeline_state.db")

    def test_schema_tables_created(self):
        with tempfile.TemporaryDirectory() as d:
            con = self._con(d)
            names = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"qa_decision", "exclusivity", "delivery", "metrics_event"} <= names)
            con.close()

    def test_wal_enabled(self):
        with tempfile.TemporaryDirectory() as d:
            con = self._con(d)
            mode = con.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(mode.lower(), "wal")
            con.close()

    def test_qa_roundtrip_and_pk(self):
        with tempfile.TemporaryDirectory() as d:
            con = self._con(d)
            con.execute("INSERT INTO qa_decision(einheit_mastr_nr,status,fingerprint) VALUES(?,?,?)",
                        ("SEE1", "approved", "fp1"))
            con.commit()
            row = con.execute("SELECT status FROM qa_decision WHERE einheit_mastr_nr='SEE1'").fetchone()
            self.assertEqual(row["status"], "approved")
            # PRIMARY KEY auf einheit_mastr_nr -> Upsert/Replace-Semantik prüfbar
            con.execute("INSERT OR REPLACE INTO qa_decision(einheit_mastr_nr,status,fingerprint) "
                        "VALUES(?,?,?)", ("SEE1", "rejected", "fp2"))
            con.commit()
            self.assertEqual(con.execute(
                "SELECT status FROM qa_decision WHERE einheit_mastr_nr='SEE1'").fetchone()["status"],
                "rejected")
            con.close()

    def test_exclusivity_unique_per_funktion_gebiet_trigger(self):
        with tempfile.TemporaryDirectory() as d:
            con = self._con(d)
            con.execute("INSERT INTO exclusivity(funktion,gebiet,trigger,kaeufer) VALUES(?,?,?,?)",
                        ("speicher", "muensterland", "T2", "KaeuferA"))
            con.commit()
            import sqlite3
            with self.assertRaises(sqlite3.IntegrityError):   # gleicher Schlüssel -> Konflikt
                con.execute("INSERT INTO exclusivity(funktion,gebiet,trigger,kaeufer) VALUES(?,?,?,?)",
                            ("speicher", "muensterland", "T2", "KaeuferB"))
            con.close()

    def test_readonly_connection(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pipeline_state.db"
            state.connect(p).close()           # anlegen
            ro = state.connect_readonly(p)
            import sqlite3
            with self.assertRaises(sqlite3.OperationalError):
                ro.execute("INSERT INTO qa_decision(einheit_mastr_nr,status,fingerprint) "
                           "VALUES('X','pending','f')")
                ro.commit()
            ro.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
