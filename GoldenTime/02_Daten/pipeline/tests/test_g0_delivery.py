"""
G0 — der USP scharf: Exklusivität + Dedupe im Lieferpfad ERZWUNGEN, e.K.-Hartfilter (§0), LIVE-Guard.

Deckt die prüfbaren Exits der ersten Bau-Schleife (Loop 0) deterministisch ab (stdlib, KEIN Netz,
synthetische DBs):
  * ``commit_delivery`` atomar (BEGIN IMMEDIATE): 2. Lauf an denselben (kaeufer,funktion) = 0 neue (Dedupe).
  * Exklusivität: nach reserve(A) liefert/committet B nichts (filter_deliverable/commit_delivery -> []).
  * e.K./natürliche Person: ``ist_natuerliche_person`` (3 Wege) + ``run_region`` routet sie aus ``lieferbar``
    in ``nat_person_gesperrt`` (qa-unabhängig), schaltbar via ``nat_personen_frei``.
  * LIVE-Guard: ``_commit_guard`` sperrt ``--commit`` bei ``LIVE_DELIVERY_ENABLED`` aus; cmd_gate_demo bricht ab.
  * Dry-Run hinterlässt 0 Zeilen in delivery/exclusivity.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_g0_delivery -v
"""
from __future__ import annotations

import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import cli
from pipeline import deliver
from pipeline.control import config_store as cs
from pipeline.control import state as statemod
from pipeline.ledger import ledger as ledgermod
from pipeline.qualify import hierarchy
from pipeline.signal import SignalRecord

FUNKTION = "speicher_installateur"
GEBIET = "muensterland"
TRIGGER = "T2"


def _rec(see, abr="ABR1", entity="X GmbH"):
    """Minimaler lieferbarer Record (genug für Ledger-Dedupe/-Exklusivität)."""
    return SignalRecord(see, abr, "T2", "2006-01-01", 0.9, "Post-EEG", entity=entity, kwp=120.0)


# --------------------------------------------------------------------------- #
# (1) Ledger: atomarer Commit, Dedupe, Exklusivität (ohne Quell-DB)
# --------------------------------------------------------------------------- #
class TestCommitDelivery(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = statemod.connect(Path(self._tmp.name) / "state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_commit_records_and_reserves(self):
        recs = [_rec("S1"), _rec("S2")]
        neu = ledgermod.commit_delivery(self.con, recs, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(len(neu), 2)
        # Lieferprotokoll hat beide; Exklusivität ist für A reserviert.
        self.assertTrue(ledgermod.already_delivered(self.con, "S1", "KaeuferA", FUNKTION))
        self.assertEqual(ledgermod.owner(self.con, FUNKTION, GEBIET, TRIGGER), "KaeuferA")

    def test_second_commit_is_zero_new(self):
        # S1-Exit: zwei aufeinanderfolgende --commit an dieselbe (kaeufer,funktion) -> 2. Lauf 0 neue.
        recs = [_rec("S1"), _rec("S2")]
        ledgermod.commit_delivery(self.con, recs, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        neu2 = ledgermod.commit_delivery(self.con, recs, "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(neu2, [])
        # genau 2 Lieferzeilen (kein Doppel-Insert).
        n = self.con.execute("SELECT count(*) FROM delivery").fetchone()[0]
        self.assertEqual(n, 2)

    def test_exclusivity_blocks_other_buyer(self):
        # S2-Exit: nach reserve(A) bekommt B in derselben Kombination nichts (Exklusivität).
        ledgermod.commit_delivery(self.con, [_rec("S1")], "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        leer = ledgermod.filter_deliverable(self.con, [_rec("S9")], "KaeuferB", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(leer, [])
        neu_b = ledgermod.commit_delivery(self.con, [_rec("S9")], "KaeuferB", FUNKTION, GEBIET, TRIGGER)
        self.assertEqual(neu_b, [])
        # B hat NICHTS protokolliert und hält den Schlüssel NICHT.
        self.assertEqual(ledgermod.owner(self.con, FUNKTION, GEBIET, TRIGGER), "KaeuferA")
        self.assertFalse(ledgermod.already_delivered(self.con, "S9", "KaeuferB", FUNKTION))

    def test_same_buyer_idempotent_reserve(self):
        # idempotent: zweiter Commit an A reserviert nicht doppelt (genau eine Exklusiv-Zeile).
        ledgermod.commit_delivery(self.con, [_rec("S1")], "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        ledgermod.commit_delivery(self.con, [_rec("S2")], "KaeuferA", FUNKTION, GEBIET, TRIGGER)
        n = self.con.execute("SELECT count(*) FROM exclusivity").fetchone()[0]
        self.assertEqual(n, 1)


# --------------------------------------------------------------------------- #
# (2) e.K./natürliche Person — ist_natuerliche_person (3 Wege)
# --------------------------------------------------------------------------- #
class TestIstNatuerlichePerson(unittest.TestCase):
    def test_personenart_proxy(self):
        r = _rec("S1", entity="Wegener GmbH")
        r.provenance = "personenart=natuerlich"
        self.assertTrue(hierarchy.ist_natuerliche_person(r))

    def test_flag(self):
        r = _rec("S1", entity="Irgendwas")
        r.flags = (hierarchy.FLAG_NATUERLICHE_PERSON,)
        self.assertTrue(hierarchy.ist_natuerliche_person(r))

    def test_ek_name_ohne_personenart(self):
        # Path 3 (Join-Ausfall-Resilienz): e.K. im Namen, PersonenArt juristisch/leer.
        r = _rec("S1", entity="Maier Handel e.K.")
        r.provenance = "personenart=juristisch"
        self.assertTrue(hierarchy.ist_natuerliche_person(r))

    def test_gmbh_ist_keine(self):
        r = _rec("S1", entity="Wegener Stahlservice GmbH")
        r.provenance = "personenart=juristisch"
        self.assertFalse(hierarchy.ist_natuerliche_person(r))


# --------------------------------------------------------------------------- #
# (3) _commit_guard — LIVE_DELIVERY_ENABLED-Schalter (§0/I8)
# --------------------------------------------------------------------------- #
class TestCommitGuard(unittest.TestCase):
    def test_blockt_wenn_live_aus(self):
        with mock.patch.object(cli.config, "LIVE_DELIVERY_ENABLED", False):
            msg = cli._commit_guard("A", FUNKTION)
        self.assertIsNotNone(msg)
        self.assertIn("LIVE_DELIVERY_ENABLED ist aus", msg)

    def test_blockt_ohne_kaeufer(self):
        with mock.patch.object(cli.config, "LIVE_DELIVERY_ENABLED", True):
            self.assertIsNotNone(cli._commit_guard("", FUNKTION))

    def test_erlaubt_wenn_live_an_und_kaeufer(self):
        with mock.patch.object(cli.config, "LIVE_DELIVERY_ENABLED", True):
            self.assertIsNone(cli._commit_guard("A", FUNKTION))


# --------------------------------------------------------------------------- #
# (4) End-to-end gegen synthetische Quell-DB: e.K.-Routing + Dry-Run-0-Zeilen + --commit-Sperre
# --------------------------------------------------------------------------- #
SOLAR_COLS = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMastrNummer",
              "Postleitzahl", "Ort", "Bundesland", "Bruttoleistung", "Inbetriebnahmedatum",
              "Registrierungsdatum", "Einspeisungsart", "EinheitBetriebsstatus", "EegMastrNummer"]
SOLAR_ROWS = [
    ("SEE1", "ABR_FIRMA", "LOK1", "48143", "Münster", "NRW", "120.0", "2006-05-01", "2006-05-10",
     "Volleinspeisung", "In Betrieb", "EEG1"),
    # e.K. im Namen, PersonenArt = Organisation (juristisch) -> nur der e.K.-Namensfilter greift (Path 3).
    ("SEE_EK", "ABR_EK", "LOK2", "48155", "Münster", "NRW", "90.0", "2006-06-01", "2006-06-10",
     "Volleinspeisung", "In Betrieb", "EEG2"),
]
EEG_ROWS = [("EEG1", "2006-05-01"), ("EEG2", "2006-06-01")]
MARKET_ROWS = [
    ("ABR_FIRMA", "Wegener Stahlservice GmbH", "Organisation (Unternehmen, ...)", "GmbH"),
    ("ABR_EK", "Maier Handel e.K.", "Organisation (Unternehmen, ...)", "Einzelunternehmen"),
]


def _build_source(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute(f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})')
    con.execute('CREATE TABLE solar_eeg ("EegMastrNummer" TEXT, "EegInbetriebnahmedatum" TEXT)')
    con.execute('CREATE TABLE market_actors ("MastrNummer" TEXT, "Firmenname" TEXT, '
                '"Personenart" TEXT, "Rechtsform" TEXT)')
    con.execute('CREATE TABLE storage_extended ("EinheitMastrNummer" TEXT, '
                '"AnlagenbetreiberMastrNummer" TEXT, "LokationMastrNummer" TEXT, '
                '"GemeinsamRegistrierteSolareinheitMastrNummer" TEXT, "EinheitBetriebsstatus" TEXT)')
    con.executemany(f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})', SOLAR_ROWS)
    con.executemany('INSERT INTO solar_eeg VALUES (?, ?)', EEG_ROWS)
    con.executemany('INSERT INTO market_actors VALUES (?, ?, ?, ?)', MARKET_ROWS)
    con.commit()
    con.close()


def _src_con(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def _store():
    triggers = {"T2": {"enabled": True, "label": "Post-EEG"}}
    gebiete = ({"id": GEBIET, "name": "Münsterland", "enabled": True,
                "plz_prefixes": ["48", "59"], "trigger_overrides": {}},)
    return cs.ConfigStore(schema_version=cs.SCHEMA_VERSION, triggers=triggers, modules={}, gebiete=gebiete)


class _NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TestRunRegionEkFilter(unittest.TestCase):
    def test_ek_aus_lieferbar_in_gesperrt(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src.db"
            _build_source(src)
            con = _src_con(src)
            qa_con = statemod.connect(Path(d) / "state.db")
            try:
                b = deliver.run_region(con, qa_con, plz_prefixes=("48", "59"), region="M",
                                       gebiet_id=GEBIET, resolve=False)
            finally:
                con.close()
                qa_con.close()
        lief = {r.entity for r in b.lieferbar}
        gesp = {r.entity for r in b.nat_person_gesperrt}
        self.assertIn("Wegener Stahlservice GmbH", lief)   # GmbH bleibt lieferbar
        self.assertIn("Maier Handel e.K.", gesp)            # e.K. hart aus lieferbar
        self.assertNotIn("Maier Handel e.K.", lief)
        # Reconciliation: lieferbar + nat_gesperrt + pending + namenlos + rejected + geplant = roh
        summe = (len(b.lieferbar) + len(b.nat_person_gesperrt) + len(b.pending)
                 + len(b.namenlos) + len(b.rejected) + len(b.speicher_geplant))
        self.assertEqual(summe, b.roh)

    def test_freigegeben_laesst_ek_durch(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src.db"
            _build_source(src)
            con = _src_con(src)
            qa_con = statemod.connect(Path(d) / "state.db")
            try:
                b = deliver.run_region(con, qa_con, plz_prefixes=("48", "59"), region="M",
                                       gebiet_id=GEBIET, resolve=False, nat_personen_frei=True)
            finally:
                con.close()
                qa_con.close()
        self.assertIn("Maier Handel e.K.", {r.entity for r in b.lieferbar})
        self.assertEqual(b.nat_person_gesperrt, [])

    def test_dry_run_schreibt_keine_ledger_zeilen(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src.db"
            _build_source(src)
            con = _src_con(src)
            qa_con = statemod.connect(Path(d) / "state.db")
            try:
                deliver.run_region(con, qa_con, plz_prefixes=("48", "59"), region="M",
                                   gebiet_id=GEBIET, resolve=False, kaeufer="A", funktion=FUNKTION)
                n_del = qa_con.execute("SELECT count(*) FROM delivery").fetchone()[0]
                n_exc = qa_con.execute("SELECT count(*) FROM exclusivity").fetchone()[0]
            finally:
                con.close()
                qa_con.close()
        self.assertEqual((n_del, n_exc), (0, 0))   # Vorschau ist read-only


class TestGateDemoCommitRefused(unittest.TestCase):
    def test_commit_refused_when_live_off(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src.db"
            _build_source(src)
            state_con = statemod.connect(Path(d) / "state.db")
            args = _NS(db=None, gebiete=GEBIET, kaeufer="A", funktion=FUNKTION,
                       out_dir=str(Path(d) / "out"), offline=True, commit=True)
            buf = io.StringIO()
            with mock.patch.object(cli.config, "LIVE_DELIVERY_ENABLED", False), \
                    mock.patch.object(cli.cs, "load", return_value=_store()), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_gate_demo(args)
            out = buf.getvalue()
            n_del = state_con.execute("SELECT count(*) FROM delivery").fetchone()[0]
            state_con.close()
        self.assertEqual(rc, 2)
        self.assertIn("ABBRUCH", out)
        self.assertIn("LIVE_DELIVERY_ENABLED ist aus", out)
        self.assertEqual(n_del, 0)   # nichts protokolliert


# --------------------------------------------------------------------------- #
# (5) Betriebs-Exklusivität (Refute CRITICAL+HIGH: cross-Gebiet & cross-Trigger) + Normalisierung
# --------------------------------------------------------------------------- #
class TestBetriebExklusivitaet(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.con = statemod.connect(Path(self._tmp.name) / "state.db")

    def tearDown(self):
        self.con.close()
        self._tmp.cleanup()

    def test_cross_gebiet_betrieb_geht_nicht_an_zwei_kaeufer(self):
        # CRITICAL: derselbe Betrieb (ABRX) mit Anlagen in zwei Gebieten darf NICHT an zwei Käufer.
        ledgermod.commit_delivery(self.con, [_rec("S1", abr="ABRX")], "A", FUNKTION, "gebiet1", "T2")
        neu_b = ledgermod.commit_delivery(self.con, [_rec("S2", abr="ABRX")], "B", FUNKTION, "gebiet2", "T2")
        self.assertEqual(neu_b, [])   # Betrieb gehört A -> B bekommt ihn nicht (gebiets-übergreifend)
        self.assertTrue(ledgermod.betrieb_fremd_vergeben(self.con, "ABRX", FUNKTION, "B"))
        self.assertFalse(ledgermod.betrieb_fremd_vergeben(self.con, "ABRX", FUNKTION, "A"))  # A selbst: ok

    def test_cross_trigger_betrieb_geht_nicht_an_zwei_kaeufer(self):
        # HIGH: A hält gebiet1×T2, B will gebiet1×T1 (anderer Trigger, freier Reservierungs-Schlüssel) —
        # der Betrieb ist trotzdem gesperrt (Dedupe ist trigger-agnostisch über die Betriebs-Ebene).
        ledgermod.commit_delivery(self.con, [_rec("S1", abr="ABRX")], "A", FUNKTION, "gebiet1", "T2")
        neu_b = ledgermod.commit_delivery(self.con, [_rec("S2", abr="ABRX")], "B", FUNKTION, "gebiet1", "T1")
        self.assertEqual(neu_b, [])

    def test_gleicher_kaeufer_behaelt_betrieb_ueber_gebiete(self):
        ledgermod.commit_delivery(self.con, [_rec("S1", abr="ABRX")], "A", FUNKTION, "gebiet1", "T2")
        neu = ledgermod.commit_delivery(self.con, [_rec("S2", abr="ABRX")], "A", FUNKTION, "gebiet2", "T2")
        self.assertEqual(len(neu), 1)   # derselbe Käufer darf seinen Betrieb auch im 2. Gebiet

    def test_funktion_normalisierung_dedupt(self):
        ledgermod.commit_delivery(self.con, [_rec("S1")], "A", "Speicher-Installateur", GEBIET, "T2")
        neu = ledgermod.commit_delivery(self.con, [_rec("S1")], "A", "speicher_installateur", GEBIET, "T2")
        self.assertEqual(neu, [])   # 'Speicher-Installateur' == 'speicher_installateur' (gleicher Schlüssel)
        self.assertTrue(ledgermod.already_delivered(self.con, "S1", "A", "SPEICHER-INSTALLATEUR"))


class TestPartitionNatuerliche(unittest.TestCase):
    def test_partition_trennt_ek(self):
        gmbh = _rec("S1", entity="X GmbH")
        gmbh.provenance = "personenart=juristisch"
        ek = _rec("S2", entity="Y e.K.")
        ek.provenance = "personenart=juristisch"
        behalten, gesperrt = hierarchy.partition_natuerliche([gmbh, ek], nat_frei=False)
        self.assertEqual([r.einheit_mastr_nr for r in behalten], ["S1"])
        self.assertEqual([r.einheit_mastr_nr for r in gesperrt], ["S2"])

    def test_partition_freigegeben_behaelt_alle(self):
        ek = _rec("S2", entity="Y e.K.")
        behalten, gesperrt = hierarchy.partition_natuerliche([ek], nat_frei=True)
        self.assertEqual(len(behalten), 1)
        self.assertEqual(gesperrt, [])


# --------------------------------------------------------------------------- #
# (6) Config-Store Policy-Schalter (Refute MEDIUM: save() verwarf extras; LOW: non-dict policy)
# --------------------------------------------------------------------------- #
class TestConfigStorePolicy(unittest.TestCase):
    def test_save_erhaelt_policy_block(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "cs.json"
            cs.save(cs.defaults(), path=p)
            reloaded = cs.load(p)
            self.assertIn("policy", reloaded.extras)
            cs.save(reloaded, path=p)                       # zweiter Toggle-Roundtrip
            self.assertIn("policy", cs.load(p).extras)

    def test_freigabe_kippt_nicht_still_zurueck(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "cs.json"
            raw = cs._default_raw()
            raw["policy"]["natuerliche_personen_freigegeben"] = True
            cs.save(cs._from_raw(raw), path=p)
            self.assertTrue(cs.load(p).natuerliche_personen_freigegeben())

    def test_non_dict_policy_kein_crash(self):
        store = cs.ConfigStore(cs.SCHEMA_VERSION, {}, {}, (), extras={"policy": "garbage"})
        self.assertFalse(store.natuerliche_personen_freigegeben())


if __name__ == "__main__":
    unittest.main(verbosity=2)
