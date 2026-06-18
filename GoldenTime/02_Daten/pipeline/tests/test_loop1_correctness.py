"""
Loop 1 — Korrektheits-/Sichtbarkeits-Leaks (Sprint S3, M1-Gate): G5 (QA asymmetrisch) + G17 (Anomalie).

  * G5: ein zuvor APPROVED Lead, der einen NEUEN QA-Flag bekommt (echte Obermenge), geht zurück nach
    PENDING; rejected bleibt rejected; eine Teilmenge (Flag entfernt) ändert nichts. KEIN Fingerprint-Eingriff.
  * G17: anomaly_check warnt bei 0 lieferbaren und bei Einbruch unter die Trailing-Baseline (≥2 Vorwochen).

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_loop1_correctness -v
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.control import metrics, state as statemod
from pipeline.qualify import qa_gate
from pipeline.signal import SignalRecord


def _rec(see, flags=(), entity="X GmbH", speicher="none_reported", kwp=120.0):
    """SignalRecord mit setzbaren Flags; load-bearing Felder konstant → stabiler Fingerprint."""
    r = SignalRecord(see, "ABR_" + see, "T2", "2006-01-01", 0.9, "Post-EEG",
                     entity=entity, kwp=kwp, speicher_status=speicher)
    r.flags = tuple(flags)
    return r


class TestG5AsymmetrischesReReview(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = statemod.connect(Path(self._tmp.name) / "state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_approved_plus_neuer_flag_zurueck_pending(self):
        self.assertEqual(qa_gate.apply_qa(_rec("S1", ["NATUERLICHE_PERSON_PRUEFEN"]), self.con), qa_gate.PENDING)
        qa_gate.approve(self.con, "S1")
        # gleicher Lead (gleicher Fingerprint), aber NEUER QA-Flag (Verein) dazu → zurück in die QA.
        nach = qa_gate.apply_qa(_rec("S1", ["NATUERLICHE_PERSON_PRUEFEN", "VEREIN_PRUEFEN"]), self.con)
        self.assertEqual(nach, qa_gate.PENDING)

    def test_approved_gleiche_flags_bleibt_approved(self):
        qa_gate.apply_qa(_rec("S1", ["NATUERLICHE_PERSON_PRUEFEN"]), self.con)
        qa_gate.approve(self.con, "S1")
        self.assertEqual(qa_gate.apply_qa(_rec("S1", ["NATUERLICHE_PERSON_PRUEFEN"]), self.con), qa_gate.APPROVED)

    def test_rejected_plus_neuer_flag_bleibt_rejected(self):
        qa_gate.apply_qa(_rec("S1", ["ENERGIE_FIRMA_PRUEFEN"]), self.con)
        qa_gate.reject(self.con, "S1", grund="energie")
        nach = qa_gate.apply_qa(_rec("S1", ["ENERGIE_FIRMA_PRUEFEN", "VEREIN_PRUEFEN"]), self.con)
        self.assertEqual(nach, qa_gate.REJECTED)   # Ablehnung wird NICHT re-reviewt

    def test_approved_flag_entfernt_bleibt_approved(self):
        qa_gate.apply_qa(_rec("S1", ["NATUERLICHE_PERSON_PRUEFEN", "VEREIN_PRUEFEN"]), self.con)
        qa_gate.approve(self.con, "S1")
        # ein Flag WENIGER (Teilmenge, keine Obermenge) → kein Re-Review.
        self.assertEqual(qa_gate.apply_qa(_rec("S1", ["NATUERLICHE_PERSON_PRUEFEN"]), self.con), qa_gate.APPROVED)


class TestG17Anomaly(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = statemod.connect(Path(self._tmp.name) / "state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_null_lieferbar_warnt_immer(self):
        msg = metrics.anomaly_check(self.con, gebiet="g", trigger="T2", wert=0)
        self.assertIsNotNone(msg)
        self.assertIn("0", msg)

    def test_keine_historie_keine_baseline_warnung(self):
        self.assertIsNone(metrics.anomaly_check(self.con, gebiet="g", trigger="T2", wert=5))

    def test_einbruch_unter_trailing_median_warnt(self):
        metrics.record(self.con, metrik="lieferbar", wert=40, woche="2026-W20", gebiet="g", trigger="T2")
        metrics.record(self.con, metrik="lieferbar", wert=42, woche="2026-W21", gebiet="g", trigger="T2")
        msg = metrics.anomaly_check(self.con, gebiet="g", trigger="T2", wert=5)
        self.assertIsNotNone(msg)
        self.assertIn("Median", msg)

    def test_normaler_wert_keine_warnung(self):
        metrics.record(self.con, metrik="lieferbar", wert=40, woche="2026-W20", gebiet="g", trigger="T2")
        metrics.record(self.con, metrik="lieferbar", wert=42, woche="2026-W21", gebiet="g", trigger="T2")
        self.assertIsNone(metrics.anomaly_check(self.con, gebiet="g", trigger="T2", wert=38))


if __name__ == "__main__":
    unittest.main(verbosity=2)
