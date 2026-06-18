"""
Loop 2 — Backup/Restore mit GETESTETEM Restore (DoD §9.5; Zielbild Datenverlust-Achse 5,0).

Die pipeline_state.db (QA-Entscheide + Exklusiv-/Liefer-Ledger + Metriken) ist NICHT regenerierbar —
ihr Verlust zerstört das Exklusivitäts-Versprechen. Deckt ab: voller Backup→Datenverlust→Restore-Zyklus
mit Daten-Integrität, Ablehnung eines kaputten Backups (Live-DB bleibt unangetastet), Backup-Sortierung.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_backup_restore -v
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from pipeline.control import state as statemod
from pipeline.ledger import ledger as ledgermod


class TestBackupRestore(unittest.TestCase):
    def test_backup_restore_cycle_haelt_daten(self):
        with tempfile.TemporaryDirectory() as d:
            dbp = Path(d) / "state.db"
            con = statemod.connect(dbp)
            ledgermod.commit_delivery(
                con, [{"einheit_mastr_nr": "S1", "betreiber_mastr_nr": "ABR1"}],
                "KaeuferA", "speicher_installateur", "muensterland", "T2")
            con.execute("INSERT INTO qa_decision(einheit_mastr_nr, status, fingerprint) "
                        "VALUES('Q1','approved','fp1')")
            con.commit()
            con.close()
            bp = statemod.backup_state_db(db_path=dbp, backup_dir=Path(d) / "bk")

            # Datenverlust simulieren: Live-DB + WAL/SHM löschen.
            for sc in (dbp, dbp.with_name(dbp.name + "-wal"), dbp.with_name(dbp.name + "-shm")):
                if sc.exists():
                    sc.unlink()
            self.assertFalse(dbp.exists())

            statemod.restore_state_db(bp, db_path=dbp)
            con2 = statemod.connect(dbp)
            try:
                self.assertEqual(con2.execute("SELECT count(*) FROM delivery").fetchone()[0], 1)
                self.assertEqual(
                    con2.execute("SELECT status FROM qa_decision WHERE einheit_mastr_nr='Q1'").fetchone()[0],
                    "approved")
                self.assertEqual(con2.execute("SELECT kaeufer FROM exclusivity").fetchone()[0], "KaeuferA")
            finally:
                con2.close()

    def test_restore_lehnt_kaputtes_backup_ab_und_schont_live(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.db"
            bad.write_text("kein valides SQLite")
            live = Path(d) / "live.db"
            live.write_text("ORIGINAL")
            with self.assertRaises(Exception):
                statemod.restore_state_db(bad, db_path=live)
            # Validierung läuft VOR dem Überschreiben -> Live-DB unverändert.
            self.assertEqual(live.read_text(), "ORIGINAL")

    def test_restore_fehlt_backup(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(FileNotFoundError):
            statemod.restore_state_db(Path(d) / "gibtsnicht.db", db_path=Path(d) / "x.db")

    def test_list_backups_neueste_zuerst(self):
        with tempfile.TemporaryDirectory() as d:
            dbp = Path(d) / "state.db"
            statemod.connect(dbp).close()
            bdir = Path(d) / "bk"
            b1 = statemod.backup_state_db(db_path=dbp, backup_dir=bdir)
            b2 = bdir / "pipeline_state_20991231T235959.db"   # späterer Timestamp im Namen
            shutil.copyfile(b1, b2)
            lst = statemod.list_backups(bdir)
            self.assertEqual(lst[0].name, b2.name)            # neuestes zuerst (Timestamp im Namen)
            self.assertEqual(len(lst), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
