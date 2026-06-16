"""
Regression-Tests aus der unabhängigen Zweit-Review (16.06.) — Qualifizierer §2 + Speicher-Index.

Sichert die belegten Befunde ab: §2.1-Personennamen, Klinikum/öffentliche Hand, Energie-/PV-Synonyme
(fotovoltaik/windkraft/pv), Konzern (ALBA + SE/AG), Immobilien (§2.6), und der Speicher-Index-Fix
(stillgelegte Speicher schließen keine Leads mehr aus). stdlib, synthetisch.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_qualify_review
"""
from __future__ import annotations

import sqlite3
import unittest

from pipeline.qualify import hierarchy as H
from pipeline.qualify import qa_gate
from pipeline.signal import SignalRecord
from pipeline.speicher_check import COLOCATED, NONE_REPORTED, build_storage_index


def _rec(einheit: str, abr: str, entity: str | None = None) -> SignalRecord:
    return SignalRecord(einheit, abr, "T2", "2006-01-01", 0.9, "x", entity=entity)


class TestPersonNamePattern(unittest.TestCase):
    def test_bare_person_names_flagged(self):
        for n in ["Oliver Topmöller", "Jan Ritschny", "Christian Gölz", "Reinhard Benneker", "Hans Müller"]:
            self.assertTrue(H._looks_like_person(n), n)

    def test_multi_person(self):
        self.assertTrue(H._looks_like_person("Hildegard Schulze-Icking und Gerd Müller"))
        self.assertTrue(H._looks_like_person("Anna Meier/Bernd Schulz"))

    def test_firms_not_person(self):
        for n in ["Wegener Stahlservice GmbH", "Brockmann GmbH", "Christina Rahmann/Astrid Schröter GbR",
                  "Resy Energy GmbH & Co. KG", "Müller Bau", "Sonnenkraft Robert KG"]:
            self.assertFalse(H._looks_like_person(n), n)

    def test_digit_not_person(self):
        self.assertFalse(H._looks_like_person("Solarpark 7 Betreiber"))


class TestMatcherRegex(unittest.TestCase):
    def setUp(self):
        self.listen = H._load_alle_listen()

    def m(self, name, datei):
        return H._matcht(name, self.listen[datei])

    def test_oeffentlich_klinik_stadt(self):
        self.assertTrue(self.m("Klinikum Stuttgart", "oeffentliche_hand.txt"))
        self.assertTrue(self.m("Stadt Beilstein", "oeffentliche_hand.txt"))
        # 'stadt' nur mit Wortgrenze -> 'Neustadt' NICHT öffentlich
        self.assertFalse(self.m("Neustadt Maschinenbau GmbH", "oeffentliche_hand.txt"))

    def test_energie_synonyme(self):
        self.assertTrue(self.m("Peters Fotovoltaik", "energie_pv_firmen.txt"))
        self.assertTrue(self.m("Windkraft Benkamp GmbH", "energie_pv_firmen.txt"))
        self.assertTrue(self.m("Teuto Sonne GmbH", "energie_pv_firmen.txt"))
        self.assertTrue(self.m("PV Anlagenverwaltung GmbH", "energie_pv_firmen.txt"))
        # 'pv' nur als Wort -> 'Improvement' nicht
        self.assertFalse(self.m("Improvement Service GmbH", "energie_pv_firmen.txt"))

    def test_kette_konzern(self):
        self.assertTrue(self.m("Alba Städte- und Industriereinigung Baving GmbH", "ketten_filialisten.txt"))

    def test_verein_eG_gGmbH(self):
        self.assertTrue(self.m("Raiffeisenbank Müllheim eG", "vereine_stiftungen.txt"))
        self.assertTrue(self.m("Kliniken Ludwigsburg gGmbH", "vereine_stiftungen.txt"))

    def test_immobilien(self):
        self.assertTrue(self.m("Keller Grundstücksverwaltungsgesellschaft GmbH", "immobilien.txt"))


class TestEnrichPrecedence(unittest.TestCase):
    def _db(self, actors):
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE market_actors (MastrNummer TEXT, Firmenname TEXT, Personenart TEXT)")
        con.executemany("INSERT INTO market_actors VALUES (?,?,?)", actors)
        con.commit()
        return con

    def test_flag_assignment_and_precedence(self):
        org = "Organisation (Unternehmen, ...)"
        con = self._db([
            ("ABR1", "Oliver Topmöller", org),
            ("ABR2", "Klinikum Stuttgart", org),
            ("ABR3", "Alba Reinigung GmbH", org),
            ("ABR4", "Peters Fotovoltaik", org),
            ("ABR5", "Keller Grundstücksverwaltung GmbH", org),
            ("ABR6", "Müller Solar SE", org),
            ("ABR7", None, "Natürliche Person oder Organisation mit Personenbezug"),
        ])
        recs = [_rec(f"SEE{i}", f"ABR{i}") for i in range(1, 8)]
        H.enrich_and_qualify(recs, con)
        f = {r.einheit_mastr_nr: set(r.flags) for r in recs}
        self.assertIn("NATUERLICHE_PERSON_PRUEFEN", f["SEE1"])        # §2.1 bloßer Name
        self.assertIn("OEFFENTLICH_PRUEFEN", f["SEE2"])
        self.assertNotIn("NATUERLICHE_PERSON_PRUEFEN", f["SEE2"])     # Vorrang: Klinikum != Person
        self.assertIn("KETTE_PRUEFEN", f["SEE3"])
        self.assertIn("ENERGIE_FIRMA_PRUEFEN", f["SEE4"])
        self.assertIn("IMMOBILIEN_PRUEFEN", f["SEE5"])
        self.assertIn("KETTE_PRUEFEN", f["SEE6"])                     # SE-Rechtsform-Warnung
        self.assertIn("PRIVATPERSON_REDACTED", f["SEE7"])            # redacted nat. Person -> namenlos

    def test_immobilien_in_qa_flags(self):
        self.assertIn("IMMOBILIEN_PRUEFEN", qa_gate.QA_FLAGS)


class TestStorageBetriebsstatus(unittest.TestCase):
    def _db(self):
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE storage_extended (EinheitMastrNummer TEXT, "
                    "AnlagenbetreiberMastrNummer TEXT, LokationMastrNummer TEXT, "
                    "GemeinsamRegistrierteSolareinheitMastrNummer TEXT, EinheitBetriebsstatus TEXT)")
        con.executemany("INSERT INTO storage_extended VALUES (?,?,?,?,?)", [
            ("SSE1", "ABR_LIVE", "SEL_LIVE", None, "In Betrieb"),
            ("SSE2", "ABR_DEAD", "SEL_DEAD", None, "Endgültig stillgelegt"),
            ("SSE3", "ABR_PLAN", "SEL_PLAN", None, "In Planung"),
            # In-Betrieb-Speicher zeigt per Back-Link direkt auf eine Solar-Einheit an ANDERER Lokation
            ("SSE4", "ABR_X", "SEL_STORAGE", "SEE_PV_OTHERLOC", "In Betrieb"),
        ])
        con.commit()
        return con

    def test_only_in_betrieb_indexed(self):
        idx = build_storage_index(self._db())
        self.assertIn("ABR_LIVE", idx.operators)
        self.assertNotIn("ABR_DEAD", idx.operators)    # stillgelegt: nicht mehr Ausschluss
        self.assertNotIn("ABR_PLAN", idx.operators)
        self.assertNotIn("SEL_DEAD", idx.locations)
        # PV-Betreiber mit nur TOTEM Speicher -> none_reported (lieferbar), NICHT colocated
        self.assertEqual(idx.classify("ABR_DEAD", "SEL_DEAD", None), NONE_REPORTED)

    def test_colocated_via_gemeinsam_backlink(self):
        idx = build_storage_index(self._db())
        self.assertIn("SEE_PV_OTHERLOC", idx.colocated_solar)
        # die PV-Einheit liegt an einer ANDEREN Lokation (SEL_PV != SEL_STORAGE), trotzdem co-lokal
        self.assertEqual(idx.classify("ABR_PV", "SEL_PV", None, einheit_nr="SEE_PV_OTHERLOC"), COLOCATED)
        # eine PV ohne Back-Link bleibt none_reported
        self.assertEqual(idx.classify("ABR_PV", "SEL_PV", None, einheit_nr="SEE_OTHER"), NONE_REPORTED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
