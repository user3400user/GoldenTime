"""
Tests für den Qualifizierer + das Mensch-QA-Gate (Komponente 4 / D5).

Synthetisches solar_extended + market_actors (:memory:) für den Name/PersonenArt-Join und eine
temporäre pipeline_state.db (``state.connect``) für das QA-Gate — KEIN open-mastr, KEIN Download.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_qualify
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.control import state
from pipeline.qualify import hierarchy, qa_gate
from pipeline.signal import SignalRecord

# --- Synthetische market_actors: Firmenname + Personenart je Betreiber (ABR) -----------------
MARKET_COLS = ["MastrNummer", "Firmenname", "Personenart"]
PA_JUR = "Organisation (Unternehmen, juristische Person des privaten/öffentlichen Rechts ...)"
PA_NAT = "Natürliche Person oder Organisation mit Personenbezug (...)"
MARKET_ROWS = [
    ("ABR_A", "Müller Maschinenbau GmbH", PA_JUR),     # sauberes Gewerbe -> kein Flag, auto_ok
    ("ABR_B", "Weber Solar GmbH", PA_JUR),             # 'solar' -> ENERGIE_FIRMA_PRUEFEN
    ("ABR_C", "Hans Schmidt e.K.", PA_NAT),            # natürliche Person -> NATUERLICHE_PERSON_PRUEFEN
    ("ABR_D", "Stadtwerke Münster GmbH", PA_JUR),      # 'stadtwerke' -> OEFFENTLICH_PRUEFEN
    ("ABR_E", "Lidl Vertriebs GmbH", PA_JUR),          # 'lidl' -> KETTE_PRUEFEN
    ("ABR_F", "SV Blau-Weiß e.V.", PA_NAT),            # 'e.v.' -> VEREIN_PRUEFEN (+natürlich)
]


def _market_con() -> sqlite3.Connection:
    """In-memory DB mit market_actors (für den Anreicherungs-Join)."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(f'CREATE TABLE market_actors ({", ".join(f"\"{c}\" TEXT" for c in MARKET_COLS)})')
    con.executemany(
        f'INSERT INTO market_actors VALUES ({", ".join("?" for _ in MARKET_COLS)})', MARKET_ROWS
    )
    con.commit()
    return con


def _record(einheit: str, abr: str | None, *, kwp: float | None = 100.0,
            entity: str | None = None, flags: tuple[str, ...] = ()) -> SignalRecord:
    """Minimaler gültiger SignalRecord (Konfidenz ist Pflicht)."""
    return SignalRecord(
        einheit_mastr_nr=einheit,
        betreiber_mastr_nr=abr,
        trigger_typ="T2",
        datum="2007-04-01",
        konfidenz=0.9,
        buy_relevanz="Test",
        entity=entity,
        kwp=kwp,
        speicher_status="none_reported",
        flags=flags,
    )


class TestEnrichAndQualify(unittest.TestCase):
    def setUp(self):
        self.con = _market_con()

    def tearDown(self):
        self.con.close()

    def test_name_join_setzt_entity(self):
        recs = [_record("SEE_A", "ABR_A")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertEqual(recs[0].entity, "Müller Maschinenbau GmbH")

    def test_sauberes_gewerbe_ohne_flag(self):
        recs = [_record("SEE_A", "ABR_A")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertFalse(set(recs[0].flags) & qa_gate.QA_FLAGS)
        self.assertFalse(qa_gate.needs_qa(recs[0]))

    def test_natuerliche_person_flag(self):
        recs = [_record("SEE_C", "ABR_C")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertIn("NATUERLICHE_PERSON_PRUEFEN", recs[0].flags)
        # PersonenArt-Proxy landet in provenance -> Fingerprint kann ihn lesen.
        self.assertEqual(hierarchy.personenart_of(recs[0]), "natuerlich")

    def test_energie_firma_muster_flag(self):
        recs = [_record("SEE_B", "ABR_B")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertIn("ENERGIE_FIRMA_PRUEFEN", recs[0].flags)

    def test_oeffentliche_hand_und_kette(self):
        recs = [_record("SEE_D", "ABR_D"), _record("SEE_E", "ABR_E")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertIn("OEFFENTLICH_PRUEFEN", recs[0].flags)
        self.assertIn("KETTE_PRUEFEN", recs[1].flags)

    def test_verein_und_natuerlich_additiv(self):
        recs = [_record("SEE_F", "ABR_F")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertIn("VEREIN_PRUEFEN", recs[0].flags)
        self.assertIn("NATUERLICHE_PERSON_PRUEFEN", recs[0].flags)  # additiv, nicht überschrieben

    def test_flags_additiv_bestehende_bleiben(self):
        recs = [_record("SEE_B", "ABR_B", flags=("PREMIUM_SPEICHER_ANDERER_STANDORT",))]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertIn("PREMIUM_SPEICHER_ANDERER_STANDORT", recs[0].flags)
        self.assertIn("ENERGIE_FIRMA_PRUEFEN", recs[0].flags)

    def test_unbekannte_abr_keine_streichung(self):
        # ABR ohne market-Eintrag: kein Join, kein Crash, entity bleibt wie übergeben.
        recs = [_record("SEE_X", "ABR_UNBEKANNT", entity="Bestehend GmbH")]
        hierarchy.enrich_and_qualify(recs, self.con)
        self.assertEqual(recs[0].entity, "Bestehend GmbH")


class TestQaGate(unittest.TestCase):
    def setUp(self):
        self.market = _market_con()
        self._tmp = tempfile.TemporaryDirectory()
        self.state = state.connect(Path(self._tmp.name) / "pipeline_state.db")

    def tearDown(self):
        self.market.close()
        self.state.close()
        self._tmp.cleanup()

    def _qualified(self, einheit: str, abr: str, **kw) -> SignalRecord:
        rec = _record(einheit, abr, **kw)
        hierarchy.enrich_and_qualify([rec], self.market)
        return rec

    def test_auto_ok_ohne_flag(self):
        rec = self._qualified("SEE_A", "ABR_A")          # sauberes Gewerbe
        self.assertEqual(qa_gate.apply_qa(rec, self.state), "auto_ok")
        self.assertEqual(rec.qa_status, "auto_ok")
        # auto_ok schreibt NICHTS in die Queue.
        self.assertEqual(qa_gate.list_queue(self.state), [])

    def test_pending_bei_flag(self):
        rec = self._qualified("SEE_B", "ABR_B")          # Energie-Firma -> Flag
        self.assertEqual(qa_gate.apply_qa(rec, self.state), "pending")
        queue = qa_gate.list_queue(self.state)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["einheit_mastr_nr"], "SEE_B")
        self.assertEqual(queue[0]["status"], "pending")

    def test_approved_haelt_ueber_zweiten_lauf(self):
        rec = self._qualified("SEE_B", "ABR_B")
        qa_gate.apply_qa(rec, self.state)                # -> pending
        qa_gate.approve(self.state, "SEE_B", grund="echtes_dachhandwerk")
        # Zweiter Lauf, identischer Record/Fingerprint -> approved HÄLT (kein Re-Pending).
        rec2 = self._qualified("SEE_B", "ABR_B")
        self.assertEqual(qa_gate.apply_qa(rec2, self.state), "approved")
        self.assertEqual(rec2.qa_status, "approved")

    def test_kwp_band_wechsel_re_review(self):
        rec = self._qualified("SEE_B", "ABR_B", kwp=100.0)   # im Band
        qa_gate.apply_qa(rec, self.state)
        qa_gate.approve(self.state, "SEE_B", grund="ok")
        # kWp springt über die Produktgrenze (KWP_MAX=750) -> Fingerprint ändert sich -> Re-Review.
        rec2 = self._qualified("SEE_B", "ABR_B", kwp=900.0)  # out of band
        self.assertEqual(qa_gate.apply_qa(rec2, self.state), "pending")

    def test_kwp_kleine_aenderung_kein_re_review(self):
        rec = self._qualified("SEE_B", "ABR_B", kwp=100.0)
        qa_gate.apply_qa(rec, self.state)
        qa_gate.approve(self.state, "SEE_B", grund="ok")
        # kWp ändert sich, bleibt aber IM Band -> selbes Band -> Entscheidung hält.
        rec2 = self._qualified("SEE_B", "ABR_B", kwp=120.0)
        self.assertEqual(qa_gate.apply_qa(rec2, self.state), "approved")

    def test_rejected_haelt_und_grund_pflicht(self):
        rec = self._qualified("SEE_E", "ABR_E")          # Kette
        qa_gate.apply_qa(rec, self.state)
        with self.assertRaises(ValueError):
            qa_gate.reject(self.state, "SEE_E", grund="")
        qa_gate.reject(self.state, "SEE_E", grund="filialist_zentraleinkauf")
        rec2 = self._qualified("SEE_E", "ABR_E")
        self.assertEqual(qa_gate.apply_qa(rec2, self.state), "rejected")

    def test_approve_abr_setzt_mehrere(self):
        # Zwei Einheiten DESSELBEN Betreibers (ABR_B) -> beide pending -> approve_abr gibt beide frei.
        r1 = self._qualified("SEE_B1", "ABR_B")
        r2 = self._qualified("SEE_B2", "ABR_B")
        qa_gate.apply_qa(r1, self.state)
        qa_gate.apply_qa(r2, self.state)
        n = qa_gate.approve_abr(self.state, "ABR_B", grund="betreiber_ist_endkunde")
        self.assertEqual(n, 2)
        again1 = self._qualified("SEE_B1", "ABR_B")
        again2 = self._qualified("SEE_B2", "ABR_B")
        self.assertEqual(qa_gate.apply_qa(again1, self.state), "approved")
        self.assertEqual(qa_gate.apply_qa(again2, self.state), "approved")

    def test_fingerprint_stabil_und_unabhaengig_von_frische(self):
        # Frische/Datum/Konfidenz sind NICHT load-bearing -> Fingerprint bleibt gleich.
        rec_a = self._qualified("SEE_B", "ABR_B")
        fp_a = qa_gate.fingerprint(rec_a)
        rec_b = self._qualified("SEE_B", "ABR_B")
        rec_b.datum = "1999-01-01"
        rec_b.konfidenz = 0.31
        self.assertEqual(qa_gate.fingerprint(rec_b), fp_a)


if __name__ == "__main__":
    unittest.main(verbosity=2)
