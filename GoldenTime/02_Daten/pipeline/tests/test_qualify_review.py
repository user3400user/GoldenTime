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

    def test_fullwidth_ampersand_and_abbrev_und(self):
        # Zweit-Review 3: Voll-Breiten-'＆' (U+FF06) wird normalisiert, sonst rutschte die
        # Personengesellschaft 'Krühler ＆ Sander' ungeflaggt durch.
        self.assertTrue(H._looks_like_person("Krühler ＆ Sander"))
        # 'u.' als Wort-Trenner (das alte \bu\.\b matchte nie, weil auf '.' ein Leerzeichen folgt).
        self.assertTrue(H._looks_like_person("Linus u. Astrid Olbrich"))


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

    def test_r3_caritativ_und_hospital(self):
        # R3 (datengetrieben): Gemeinnützigkeit/Vereinsform steht oft nur in market_actors.Rechtsform,
        # der Name trägt bloß 'GmbH'. Namens-Token fangen den häufigsten Fall trotzdem -> QA-Flag.
        self.assertTrue(self.m("Seniorenhilfe St. Franziskus GmbH", "vereine_stiftungen.txt"))
        self.assertTrue(self.m("Seniorenzentrum am Park GmbH", "vereine_stiftungen.txt"))
        self.assertTrue(self.m("Altenheim St. Josef", "vereine_stiftungen.txt"))
        # 'Hospital' nur als Wort: Krankenhausträger ja, 'Hospitality'/Hotel-Catering NEIN (kein FP).
        self.assertTrue(self.m("St. Marien-Hospital Lüdinghausen", "oeffentliche_hand.txt"))
        self.assertTrue(self.m("Josephs-Hospital Warendorf", "oeffentliche_hand.txt"))
        self.assertFalse(self.m("Hospitality Group GmbH", "oeffentliche_hand.txt"))

    def test_zweit_review3_neue_muster(self):
        # KöR-Wortgrenze (öffentliche Hand) — 'kör' nur als Wort, nicht in 'Körting'/'Akörper'.
        self.assertTrue(self.m("Studierendenwerk KöR", "oeffentliche_hand.txt"))
        self.assertFalse(self.m("Körting Hannover GmbH", "oeffentliche_hand.txt"))
        # Filial-/Genossenschaftsbanken (Verein/zentrale Beschaffung)
        self.assertTrue(self.m("VR-Bank Mittelhaardt", "vereine_stiftungen.txt"))
        self.assertTrue(self.m("Kreissparkasse Köln", "vereine_stiftungen.txt"))
        # Religiöser Orden
        self.assertTrue(self.m("Schwestern vom Guten Hirten", "vereine_stiftungen.txt"))
        # Biogas/Biomasse (Energie-/Wettbewerber)
        self.assertTrue(self.m("Bioenergie Wadersloh Biogas GmbH", "energie_pv_firmen.txt"))
        # Holding/Beteiligung (Betriebsaufspaltung -> Immobilien-QA)
        self.assertTrue(self.m("Schmitz Holding GmbH", "immobilien.txt"))
        self.assertTrue(self.m("Müller Beteiligungsgesellschaft mbH", "immobilien.txt"))


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

    def _db_rf(self, actors):
        # market_actors MIT Rechtsform-Spalte (R3: Rechtsform-Join). Fehlt die Spalte (andere Tests),
        # bleibt rechtsform None -> kein Flag (rückwärtskompatibel).
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE market_actors "
                    "(MastrNummer TEXT, Firmenname TEXT, Personenart TEXT, Rechtsform TEXT)")
        con.executemany("INSERT INTO market_actors VALUES (?,?,?,?)", actors)
        con.commit()
        return con

    def test_rechtsform_join_flaggt_was_der_name_verbirgt(self):
        # R3: Verein/Gemeinnützigkeit/öffentl.-Recht aus market_actors.Rechtsform — auch wenn der
        # Firmenname die Form NICHT zeigt. Belege: 'gGmbH' (Name 'GmbH'), 'e.V.' (Name 'INI').
        org = "Organisation (Unternehmen, ...)"
        con = self._db_rf([
            ("ABR1", "Seniorenhilfe St. Franziskus GmbH", org, "gGmbH"),
            ("ABR2", "INI", org, "e.V."),
            ("ABR3", "Albatros", org, "Anstalt des öffentlichen Rechts"),
            ("ABR4", "Wegener Stahlservice GmbH", org, "GmbH"),
        ])
        recs = [_rec(f"SEE{i}", f"ABR{i}") for i in range(1, 5)]
        H.enrich_and_qualify(recs, con)
        f = {r.einheit_mastr_nr: set(r.flags) for r in recs}
        self.assertIn("VEREIN_PRUEFEN", f["SEE1"])         # gGmbH trotz 'GmbH'-Name
        self.assertIn("VEREIN_PRUEFEN", f["SEE2"])         # e.V. trotz nichtssagendem 'INI'
        self.assertNotIn("NATUERLICHE_PERSON_PRUEFEN", f["SEE2"])  # Rechtsform hat Vorrang
        self.assertIn("OEFFENTLICH_PRUEFEN", f["SEE3"])    # AöR rein aus Rechtsform (Name neutral)
        self.assertEqual(f["SEE4"], set())                 # normale GmbH -> kein Flag, bleibt lieferbar

    def test_rechtsform_flag_robust_whitespace_und_konzern(self):
        # R4: Katalog-Drift abfangen — der echte Wert hat ZWEI Leerzeichen; Voll-Breiten-&; Misch-/KGaA.
        self.assertEqual(H._rechtsform_flag("Stiftung  des öffentlichen Rechts"), "OEFFENTLICH_PRUEFEN")
        self.assertEqual(H._rechtsform_flag("Stiftung des Privatrechts"), "VEREIN_PRUEFEN")
        self.assertEqual(H._rechtsform_flag("gGmbH"), "VEREIN_PRUEFEN")
        self.assertEqual(H._rechtsform_flag("AG & Co. KGaA"), "KETTE_PRUEFEN")
        self.assertEqual(H._rechtsform_flag("SE ＆ Co. KG"), "KETTE_PRUEFEN")     # Voll-Breiten-&
        self.assertEqual(H._rechtsform_flag("GmbH & Co. KGaA"), "KETTE_PRUEFEN")
        self.assertIsNone(H._rechtsform_flag("GmbH & Co. KG"))                    # kein Konzernsignal
        self.assertIsNone(H._rechtsform_flag("GmbH"))
        self.assertIsNone(H._rechtsform_flag(None))


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

    def test_geplant_storage_is_own_bucket_not_exclusion(self):
        from pipeline.speicher_check import GEPLANT
        idx = build_storage_index(self._db())
        # 'In Planung'-Speicher (SSE3 an SEL_PLAN) -> Lokation im geplant-Index, NICHT im In-Betrieb-Set
        self.assertIn("SEL_PLAN", idx.geplant_locations)
        self.assertNotIn("SEL_PLAN", idx.locations)
        # eine PV an dieser Lokation -> GEPLANT (eigener Bucket), NICHT colocated und NICHT none_reported
        self.assertEqual(idx.classify("ABR_PV", "SEL_PLAN", None), GEPLANT)
        # In-Betrieb-Speicher hat Vorrang vor geplant
        self.assertEqual(idx.classify("ABR_PV", "SEL_LIVE", None), COLOCATED)


class TestQaGateStoredDecision(unittest.TestCase):
    """Bug-Hunt: ein gespeicherter QA-Entscheid hält, auch wenn die Flags im Folgelauf nicht feuern."""

    def _rec(self, see, abr, entity, flags=()):
        r = SignalRecord(see, abr, "T2", "2006-01-01", 0.9, "x", entity=entity, kwp=100.0)
        r.flags = tuple(flags)
        return r

    def test_gespeicherter_reject_haelt_auch_ohne_flag(self):
        import pathlib
        import tempfile

        from pipeline.control import state
        with tempfile.TemporaryDirectory() as d:
            con = state.connect(pathlib.Path(d) / "s.db")
            # Woche 1: geflaggt -> pending -> vom Menschen abgelehnt.
            r1 = self._rec("SEE1", "ABR1", "Stadtwerke X", flags=("OEFFENTLICH_PRUEFEN",))
            self.assertEqual(qa_gate.apply_qa(r1, con), "pending")
            qa_gate.reject(con, "SEE1", "oeffentlich")
            # Woche 2: SELBER Lead, aber Flag feuert nicht mehr (Heuristik editiert / Join-Ausfall).
            # Frueher Bug: -> auto_ok -> wieder ausgeliefert. Jetzt: gespeicherter 'rejected' haelt.
            r2 = self._rec("SEE1", "ABR1", "Stadtwerke X", flags=())
            self.assertEqual(qa_gate.apply_qa(r2, con), "rejected")
            self.assertEqual(r2.qa_status, "rejected")
            con.close()

    def test_kein_eintrag_ohne_flag_bleibt_auto_ok(self):
        import pathlib
        import tempfile

        from pipeline.control import state
        with tempfile.TemporaryDirectory() as d:
            con = state.connect(pathlib.Path(d) / "s.db")
            r = self._rec("SEE9", "ABR9", "Müller GmbH", flags=())
            self.assertEqual(qa_gate.apply_qa(r, con), "auto_ok")    # Normalfall unverändert
            con.close()


class TestQaSuggest(unittest.TestCase):
    """A: reine 'qa suggest'-Vorschlagslogik — deterministisch, NIE ein Auto-Approve."""

    def test_reject_flags(self):
        for flag in ("VEREIN_PRUEFEN", "OEFFENTLICH_PRUEFEN", "ENERGIE_FIRMA_PRUEFEN",
                     "IMMOBILIEN_PRUEFEN", "KETTE_PRUEFEN"):
            empf, grund = qa_gate.suggest_for_flags(flag)
            self.assertEqual(empf, qa_gate.REC_REJECT, flag)
            self.assertTrue(grund)

    def test_person_pruefen_und_premium_approve(self):
        self.assertEqual(qa_gate.suggest_for_flags("NATUERLICHE_PERSON_PRUEFEN")[0], qa_gate.REC_PRUEFEN)
        self.assertEqual(qa_gate.suggest_for_flags("PREMIUM_SPEICHER_ANDERER_STANDORT")[0], qa_gate.REC_APPROVE)

    def test_reject_ueberstimmt_premium_in_kombi(self):
        # e.V. + Premium-Speicher -> der Reject-Flag MUSS gewinnen (kein Durchrutschen).
        empf, grund = qa_gate.suggest_for_flags("VEREIN_PRUEFEN|PREMIUM_SPEICHER_ANDERER_STANDORT")
        self.assertEqual(empf, qa_gate.REC_REJECT)
        self.assertIn("verein", grund)

    def test_leer_oder_unbekannt_ist_pruefen_nie_approve(self):
        self.assertEqual(qa_gate.suggest_for_flags(None)[0], qa_gate.REC_PRUEFEN)
        self.assertEqual(qa_gate.suggest_for_flags("")[0], qa_gate.REC_PRUEFEN)
        self.assertEqual(qa_gate.suggest_for_flags("WAS_UNBEKANNTES")[0], qa_gate.REC_PRUEFEN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
