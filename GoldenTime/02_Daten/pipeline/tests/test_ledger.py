"""
Tests für das Exklusivitäts-Ledger (ledger/ledger.py, K6/D6) — stdlib, gegen eine temporäre
pipeline_state.db (state.connect legt das Schema an). KEIN Export-Download, kein open-mastr.

Deckt ab: Reservierung (exklusiv + idempotent), owner/is_available, Lieferprotokoll-Dedupe,
filter_deliverable (Exklusivität + Dedupe), release und die Dashboard-overview.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_ledger
"""
from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from pipeline import ledger
from pipeline.control import state
from pipeline.signal import SignalRecord

FUNKTION = "speicher_installateur"
GEBIET = "muensterland"
TRIGGER = "T2"


def _rec(einheit: str) -> SignalRecord:
    """Minimaler SignalRecord (Pflichtfelder); nur die einheit_mastr_nr ist hier load-bearing."""
    return SignalRecord(
        einheit_mastr_nr=einheit,
        betreiber_mastr_nr="ABR_" + einheit,
        trigger_typ=TRIGGER,
        datum="2006-04-01",
        konfidenz=0.9,
        buy_relevanz="Post-EEG",
    )


class TestReservation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = state.connect(Path(self._tmp.name) / "pipeline_state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_reserve_neu_true_und_owner(self):
        self.assertTrue(ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA"))
        self.assertEqual(ledger.owner(self.con, FUNKTION, GEBIET, TRIGGER), "KaeuferA")

    def test_reserve_zweiter_kaeufer_gleicher_schluessel_false(self):
        self.assertTrue(ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA"))
        # gleicher Funktion×Gebiet×Trigger-Schlüssel, anderer Käufer -> blockiert
        self.assertFalse(ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferB"))
        # Halter unverändert
        self.assertEqual(ledger.owner(self.con, FUNKTION, GEBIET, TRIGGER), "KaeuferA")

    def test_reserve_gleicher_kaeufer_idempotent_true(self):
        self.assertTrue(ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA"))
        self.assertTrue(ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA"))
        # kein Doppel-Insert -> genau eine Zeile
        n = self.con.execute(
            "SELECT COUNT(*) FROM exclusivity WHERE funktion=? AND gebiet=? AND trigger=?",
            (FUNKTION, GEBIET, TRIGGER),
        ).fetchone()[0]
        self.assertEqual(n, 1)

    def test_anderer_trigger_frei(self):
        ledger.reserve(self.con, FUNKTION, GEBIET, "T2", "KaeuferA")
        # gleiches Gebiet/Funktion, ANDERER Trigger -> eigener Schlüssel, frei für KaeuferB
        self.assertTrue(ledger.reserve(self.con, FUNKTION, GEBIET, "T1", "KaeuferB"))
        self.assertEqual(ledger.owner(self.con, FUNKTION, GEBIET, "T1"), "KaeuferB")

    def test_is_available(self):
        self.assertTrue(ledger.is_available(self.con, FUNKTION, GEBIET, TRIGGER))
        ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA")
        # fremd belegt -> ohne Käufer-Angabe nicht verfügbar
        self.assertFalse(ledger.is_available(self.con, FUNKTION, GEBIET, TRIGGER))
        # ... aber für den Halter selbst weiterhin verfügbar
        self.assertTrue(ledger.is_available(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA"))
        self.assertFalse(ledger.is_available(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferB"))

    def test_release_gibt_frei(self):
        ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA")
        ledger.release(self.con, FUNKTION, GEBIET, TRIGGER)
        self.assertIsNone(ledger.owner(self.con, FUNKTION, GEBIET, TRIGGER))
        # nach Freigabe darf ein anderer Käufer reservieren
        self.assertTrue(ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferB"))


class TestDelivery(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = state.connect(Path(self._tmp.name) / "pipeline_state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_record_delivery_und_already_delivered(self):
        self.assertFalse(ledger.already_delivered(self.con, "SEE1", "KaeuferA", FUNKTION))
        ledger.record_delivery(self.con, "SEE1", "KaeuferA", FUNKTION, gebiet=GEBIET, trigger=TRIGGER)
        self.assertTrue(ledger.already_delivered(self.con, "SEE1", "KaeuferA", FUNKTION))
        # gleiche Einheit, ANDERER Käufer -> noch nicht geliefert
        self.assertFalse(ledger.already_delivered(self.con, "SEE1", "KaeuferB", FUNKTION))

    def test_record_delivery_idempotent_dedupe(self):
        ledger.record_delivery(self.con, "SEE1", "KaeuferA", FUNKTION)
        ledger.record_delivery(self.con, "SEE1", "KaeuferA", FUNKTION)  # zweiter Lauf -> kein Crash
        n = self.con.execute(
            "SELECT COUNT(*) FROM delivery WHERE einheit_mastr_nr=? AND kaeufer=? AND funktion=?",
            ("SEE1", "KaeuferA", FUNKTION),
        ).fetchone()[0]
        self.assertEqual(n, 1)


class TestFilterDeliverable(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = state.connect(Path(self._tmp.name) / "pipeline_state.db")
        self.records = [_rec("SEE1"), _rec("SEE2"), _rec("SEE3")]

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def _ids(self, recs):
        return [r.einheit_mastr_nr for r in recs]

    def test_freier_schluessel_alle_lieferbar(self):
        out = ledger.filter_deliverable(self.con, self.records, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(self._ids(out), ["SEE1", "SEE2", "SEE3"])

    def test_eigener_schluessel_lieferbar(self):
        ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA")
        out = ledger.filter_deliverable(self.con, self.records, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(self._ids(out), ["SEE1", "SEE2", "SEE3"])

    def test_fremder_schluessel_nichts_lieferbar(self):
        ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA")
        out = ledger.filter_deliverable(self.con, self.records, "KaeuferB", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(out, [])

    def test_bereits_geliefertes_faellt_raus(self):
        ledger.reserve(self.con, FUNKTION, GEBIET, TRIGGER, "KaeuferA")
        ledger.record_delivery(self.con, "SEE2", "KaeuferA", FUNKTION)
        out = ledger.filter_deliverable(self.con, self.records, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(self._ids(out), ["SEE1", "SEE3"])  # SEE2 dedupe-gefiltert

    def test_akzeptiert_lead_dicts(self):
        leads = [{"einheit_mastr_nr": "L1"}, {"einheit_mastr_nr": "L2"}]
        out = ledger.filter_deliverable(self.con, leads, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual([d["einheit_mastr_nr"] for d in out], ["L1", "L2"])


class TestOverview(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = state.connect(Path(self._tmp.name) / "pipeline_state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_overview_listet_reservierungen(self):
        ledger.reserve(self.con, FUNKTION, GEBIET, "T2", "KaeuferA")
        ledger.reserve(self.con, FUNKTION, "osnabrueck", "T1", "KaeuferB")
        ov = ledger.overview(self.con)
        self.assertEqual(len(ov), 2)
        # nach funktion/gebiet/trigger sortiert -> muensterland vor osnabrueck
        self.assertEqual(ov[0]["gebiet"], GEBIET)
        self.assertEqual(ov[0]["kaeufer"], "KaeuferA")
        self.assertEqual(ov[0]["trigger"], "T2")
        self.assertEqual(ov[1]["gebiet"], "osnabrueck")
        self.assertEqual(ov[1]["kaeufer"], "KaeuferB")
        # reserviert_am ist gesetzt (ISO-Tag von heute)
        self.assertEqual(ov[0]["reserviert_am"], dt.date.today().isoformat())

    def test_overview_leer_ohne_reservierung(self):
        self.assertEqual(ledger.overview(self.con), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
