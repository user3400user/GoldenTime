"""
Tests der CLI-Schicht (``pipeline/cli.py``) — stdlib unittest, synthetische SQLite, KEIN Netz,
NICHT die 8,6-GB-Export-DB. Deckt PRAGMATISCH ab, was ohne den echten Gesamtexport geht:

(1) Reine Helfer: ``_slug`` (Umlaut-/Sonderzeichen-Normalisierung), ``_write_csv`` und
    ``_write_signals_csv`` (Header/Inhalt/Pfad gegen ein tmp-Dir).
(2) Der argparse-Aufbau: ``main`` baut den Parser, jedes Subcommand parst seine bekannten Argumente
    und trägt ``set_defaults(func=...)`` — der Dispatch (``args.func``) zeigt aufs richtige ``cmd_*``.
(3) Befehle gegen SYNTHETISCHE DBs (gemockte ``dbmod.connect`` / ``statemod.connect`` / ``cs.load``):
    ``cmd_qa list`` gegen eine temp state-DB, ``cmd_signals`` und ``cmd_mengen`` gegen eine kleine
    open-mastr-artige Quell-DB (wie test_snapshot_diff._build_source_db) + temp state-DB.

Befehle, die ZWINGEND den 8,6-GB-Export brauchen (``build-db``, ``inspect``, ``leads``, ``snapshot``,
``diff``, ``weekly``, ``gate-demo``, ``liefern``, ``evidenz-check`` mit Vollabdeckung) werden NICHT
erzwungen — siehe Caveats. ``cmd_signals``/``cmd_mengen`` laufen hier offline (``--offline`` bzw.
``resolve=False``), damit kein Netz angefasst wird.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_cli -v
"""
from __future__ import annotations

import contextlib
import csv
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import cli
from pipeline.control import state as statemod
from pipeline.control import config_store as cs
from pipeline.qualify import qa_gate
from pipeline.signal import SignalRecord


# --------------------------------------------------------------------------- #
# Synthetische open-mastr-artige Quell-DB (vgl. test_snapshot_diff / test_cohort).
# solar_extended + solar_eeg (T2-Kohorte, EEG-IBN-Jahr) + market_actors (Namens-Join)
# + storage_extended (Speicher-Index). Genau die Tabellen, die cohort/qualify/speicher_check lesen.
# --------------------------------------------------------------------------- #
SOLAR_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMastrNummer",
    "Postleitzahl", "Ort", "Bundesland", "Bruttoleistung", "Inbetriebnahmedatum",
    "Registrierungsdatum", "Einspeisungsart", "EinheitBetriebsstatus", "EegMastrNummer",
]
#  Einheit, ABR, Lokation, PLZ, Ort, Land, kWp, IBN, Reg, Einspeisung, Status, EEG-Nr
SOLAR_ROWS = [
    # Post-EEG-2006, 120 kWp (>=100 -> DV-Flag), Firma -> lieferbar
    ("SEE1", "ABR_FIRMA", "LOK1", "48143", "Münster", "Nordrhein-Westfalen",
     "120.0", "2006-05-01", "2006-05-10", "Volleinspeisung", "In Betrieb", "EEG1"),
    # Post-EEG-2007, 60 kWp, Klinikum -> QA-pending (OEFFENTLICH_PRUEFEN)
    ("SEE2", "ABR_KLINIK", "LOK2", "48155", "Münster", "Nordrhein-Westfalen",
     "60.0", "2007-03-01", "2007-03-05", "Teileinspeisung", "In Betrieb", "EEG2"),
    # Post-EEG-2006, 45 kWp, redacted nat. Person (Firmenname leer) -> namenlos-Bucket
    ("SEE3", "ABR_PRIV", "LOK3", "48159", "Münster", "Nordrhein-Westfalen",
     "45.0", "2006-09-01", "2006-09-09", "Volleinspeisung", "In Betrieb", "EEG3"),
    # 2015 -> NICHT Post-EEG -> fällt aus der Kohorte
    ("SEE4", "ABR_FIRMA", "LOK4", "48143", "Münster", "Nordrhein-Westfalen",
     "80.0", "2015-01-01", "2015-01-02", "Volleinspeisung", "In Betrieb", "EEG4"),
    # Andere Region (PLZ 70) -> vom PLZ-Filter 48/59 ausgeschlossen
    ("SEE5", "ABR_FIRMA", "LOK5", "70173", "Stuttgart", "Baden-Württemberg",
     "200.0", "2006-01-01", "2006-01-02", "Volleinspeisung", "In Betrieb", "EEG5"),
]
EEG_COLS = ["EegMastrNummer", "EegInbetriebnahmedatum"]
EEG_ROWS = [
    ("EEG1", "2006-05-01"), ("EEG2", "2007-03-01"), ("EEG3", "2006-09-01"),
    ("EEG4", "2015-01-01"), ("EEG5", "2006-01-01"),
]
MARKET_COLS = ["MastrNummer", "Firmenname", "Personenart", "Rechtsform"]
ORG = "Organisation (Unternehmen, ...)"
NAT = "Natürliche Person oder Organisation mit Personenbezug"
MARKET_ROWS = [
    ("ABR_FIRMA", "Wegener Stahlservice GmbH", ORG, "GmbH"),       # echtes Gewerbe -> lieferbar
    ("ABR_KLINIK", "Klinikum Münster", ORG, "GmbH"),                # öffentlich -> QA
    ("ABR_PRIV", None, NAT, None),                                  # redacted nat. Person -> namenlos
]
STORAGE_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMastrNummer",
    "GemeinsamRegistrierteSolareinheitMastrNummer", "EinheitBetriebsstatus",
]
STORAGE_ROWS: list[tuple] = []   # keine Speicher -> alle Solar-Einheiten bleiben none_reported


def _build_source_db(path: Path) -> None:
    """Synthetische open-mastr-artige Quell-DB: solar_extended/solar_eeg/market_actors/storage_extended."""
    con = sqlite3.connect(str(path))
    con.execute(f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})')
    con.execute(f'CREATE TABLE solar_eeg ({", ".join(f"\"{c}\" TEXT" for c in EEG_COLS)})')
    con.execute(f'CREATE TABLE market_actors ({", ".join(f"\"{c}\" TEXT" for c in MARKET_COLS)})')
    con.execute(f'CREATE TABLE storage_extended ({", ".join(f"\"{c}\" TEXT" for c in STORAGE_COLS)})')
    con.executemany(f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})', SOLAR_ROWS)
    con.executemany(f'INSERT INTO solar_eeg VALUES ({", ".join("?" for _ in EEG_COLS)})', EEG_ROWS)
    con.executemany(f'INSERT INTO market_actors VALUES ({", ".join("?" for _ in MARKET_COLS)})', MARKET_ROWS)
    if STORAGE_ROWS:
        con.executemany(f'INSERT INTO storage_extended VALUES ({", ".join("?" for _ in STORAGE_COLS)})',
                        STORAGE_ROWS)
    con.commit()
    con.close()


def _source_con(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def _store(plz_prefixes=("48", "59"), gebiet_id="muensterland", name="Münsterland",
           enabled=True, t2_enabled=True) -> cs.ConfigStore:
    """Minimaler Config-Store mit genau einem Gebiet (kein Zugriff auf die echte config_store.json)."""
    triggers = {"T2": {"enabled": t2_enabled, "label": "Post-EEG"}}
    gebiete = ({"id": gebiet_id, "name": name, "enabled": enabled,
                "plz_prefixes": list(plz_prefixes), "trigger_overrides": {}},)
    return cs.ConfigStore(schema_version=cs.SCHEMA_VERSION, triggers=triggers,
                          modules={}, gebiete=gebiete)


# --------------------------------------------------------------------------- #
# (1) Reine Helfer
# --------------------------------------------------------------------------- #
class TestSlug(unittest.TestCase):
    def test_umlaute_und_eszett(self):
        self.assertEqual(cli._slug("Münsterland"), "muensterland")
        self.assertEqual(cli._slug("Raum Osnabrück"), "raum-osnabrueck")
        self.assertEqual(cli._slug("Größe"), "groesse")
        self.assertEqual(cli._slug("Öko Ärzte"), "oeko-aerzte")

    def test_sonderzeichen_kollabieren_und_trimmen(self):
        self.assertEqual(cli._slug("PLZ 48/59"), "plz-48-59")
        self.assertEqual(cli._slug("  --A--B--  "), "a-b")

    def test_leer_faellt_auf_region_zurueck(self):
        self.assertEqual(cli._slug(""), "region")
        self.assertEqual(cli._slug("///"), "region")
        self.assertEqual(cli._slug(None), "region")   # _slug toleriert None


class TestWriteCsv(unittest.TestCase):
    def test_header_inhalt_und_flags_am_ende(self):
        leads = [
            {"betreiber": "Wegener GmbH", "kwp": 120.0, "plz": "48143",
             "flags": ["A", "B"]},
            {"betreiber": "Müller KG", "kwp": 60.0, "plz": "48155",
             "flags": []},
        ]
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "leads.csv"
            cli._write_csv(out, leads)
            self.assertTrue(out.exists())
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
                f.seek(0)
                header = f.readline().strip().split(",")
        # 'flags' steht garantiert als LETZTE Spalte (Helfer-Vertrag)
        self.assertEqual(header[-1], "flags")
        self.assertEqual(set(header), {"betreiber", "kwp", "plz", "flags"})
        self.assertEqual(rows[0]["flags"], "A|B")     # '|'-join
        self.assertEqual(rows[1]["flags"], "")        # leere Flags -> leerer String
        self.assertEqual(rows[0]["betreiber"], "Wegener GmbH")


class TestWriteSignalsCsv(unittest.TestCase):
    def _rec(self, see="SEE1", entity="Wegener GmbH", kwp=120.0) -> SignalRecord:
        return SignalRecord(see, "ABR1", "T2", "2006-05-01", 0.9,
                            "Post-EEG", entity=entity, kwp=kwp, plz="48143",
                            speicher_label="kein Speicher gemeldet", flags=("X",))

    def test_header_ist_csv_fields_schema(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "signals.csv"
            cli._write_signals_csv(out, [self._rec()])
            self.assertTrue(out.exists())
            with open(out, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                header = reader.fieldnames
        # Header == das Liefer-Schema (record.CSV_FIELDS), exakte Reihenfolge
        self.assertEqual(tuple(header), SignalRecord.CSV_FIELDS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entity"], "Wegener GmbH")
        self.assertEqual(rows[0]["trigger_typ"], "T2")
        self.assertEqual(rows[0]["einheit_mastr_nr"], "SEE1")
        # to_row()-Mapping: detail_id=None -> robuster Such-Link (kein toter SEE-Direktlink)
        self.assertIn("marktstammdatenregister.de", rows[0]["evidenz_url"])

    def test_mehrere_records_und_to_row_konvertierung(self):
        recs = [self._rec("SEE1", "Firma A", 120.0), self._rec("SEE2", "Firma B", 60.0)]
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "s.csv"
            cli._write_signals_csv(out, recs)
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual([r["entity"] for r in rows], ["Firma A", "Firma B"])
        self.assertEqual(rows[0]["dv_flag"], "")       # dv_flag=False -> '' (to_row-Vertrag)
        self.assertEqual(rows[0]["flags"], "X")


# --------------------------------------------------------------------------- #
# (2) argparse-Aufbau, set_defaults(func=...) je Subcommand, Dispatch
# --------------------------------------------------------------------------- #
class TestArgparse(unittest.TestCase):
    # main() parst die argv und ruft dann args.func(args). Wir patchen JEDES cmd_* auf eine Sonde,
    # die nur Funcname + Namespace festhält — so beweist ein einziger main()-Lauf Parse UND Dispatch,
    # ohne die echte Befehls-Logik (DB-Zugriff) anzustoßen.
    def _dispatch(self, argv):
        """main(argv) ausführen, aber alle cmd_* auf eine Sonde umbiegen. Gibt (funcname, args) zurück."""
        seen = {}
        cmd_names = [n for n in dir(cli) if n.startswith("cmd_")]
        patchers = []
        for n in cmd_names:
            def make(name):
                def probe(args):
                    seen["func"] = name
                    seen["args"] = args
                    return 0
                return probe
            p = mock.patch.object(cli, n, make(n))
            p.start()
            patchers.append(p)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = cli.main(argv)
        finally:
            for p in patchers:
                p.stop()
        return seen.get("func"), seen.get("args"), rc

    def test_each_subcommand_dispatches_to_its_cmd(self):
        # (Subcommand-argv, erwarteter cmd_*-Name). Pflichtargumente je Subcommand mitgeben.
        cases = [
            (["inspect"], "cmd_inspect"),
            (["build-db"], "cmd_build_db"),
            (["leads", "--plz", "48,59"], "cmd_leads"),
            (["signals", "--gebiet", "muensterland"], "cmd_signals"),
            (["evidenz-check", "--plz", "48"], "cmd_evidenz_check"),
            (["liefern", "--gebiet", "muensterland"], "cmd_liefern"),
            (["mengen"], "cmd_mengen"),
            (["weekly"], "cmd_weekly"),
            (["gate-demo"], "cmd_gate_demo"),
            (["qa", "list"], "cmd_qa"),
            (["snapshot"], "cmd_snapshot"),
            (["diff"], "cmd_diff"),
            (["ledger", "overview"], "cmd_ledger"),
            (["dashboard"], "cmd_dashboard"),
        ]
        for argv, expected in cases:
            with self.subTest(argv=argv):
                func, args, rc = self._dispatch(argv)
                self.assertEqual(func, expected)
                self.assertEqual(rc, 0)
                self.assertTrue(hasattr(args, "func"))   # set_defaults(func=...) sitzt

    def test_known_args_are_parsed_per_subcommand(self):
        # leads-Argumente landen typrichtig im Namespace.
        func, args, _ = self._dispatch(
            ["leads", "--plz", "48,59", "--bundesland", "Bayern", "--limit", "50",
             "--region-name", "Test", "--out", "x.csv"])
        self.assertEqual(func, "cmd_leads")
        self.assertEqual(args.plz, "48,59")
        self.assertEqual(args.bundesland, "Bayern")
        self.assertEqual(args.limit, 50)                  # type=int greift
        self.assertEqual(args.region_name, "Test")        # --region-name -> region_name

    def test_signals_offline_flag_and_defaults(self):
        func, args, _ = self._dispatch(["signals", "--gebiet", "muensterland", "--offline"])
        self.assertEqual(func, "cmd_signals")
        self.assertTrue(args.offline)                     # store_true
        self.assertEqual(args.gebiet, "muensterland")
        self.assertEqual(args.plz, "")                    # Default
        # ohne --offline ist es False
        _, args2, _ = self._dispatch(["signals", "--plz", "48"])
        self.assertFalse(args2.offline)

    def test_qa_positional_action_choices(self):
        func, args, _ = self._dispatch(["qa", "approve", "SEE1", "--grund", "ok"])
        self.assertEqual(func, "cmd_qa")
        self.assertEqual(args.action, "approve")
        self.assertEqual(args.einheit, "SEE1")
        self.assertEqual(args.grund, "ok")

    def test_db_global_option_before_subcommand(self):
        func, args, _ = self._dispatch(["--db", "/tmp/x.db", "qa", "list"])
        self.assertEqual(func, "cmd_qa")
        self.assertEqual(args.db, "/tmp/x.db")

    def test_dashboard_port_type_int(self):
        _, args, _ = self._dispatch(["dashboard", "--port", "9000"])
        self.assertEqual(args.port, 9000)

    def test_missing_subcommand_is_error(self):
        # subparsers required=True -> SystemExit (argparse) bei fehlendem Befehl.
        buf = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(buf):
            cli.main([])

    def test_unknown_subcommand_is_error(self):
        buf = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(buf):
            cli.main(["gibtsnicht"])

    def test_ledger_action_choices_reject_invalid(self):
        buf = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(buf):
            cli.main(["ledger", "loeschen"])   # nicht in choices=[overview,reserve,release]


# --------------------------------------------------------------------------- #
# (3a) cmd_qa 'list' gegen eine synthetische temp state-DB
# --------------------------------------------------------------------------- #
class TestCmdQaList(unittest.TestCase):
    def _args(self, **kw):
        base = dict(action="list", einheit="", grund="", notiz="",
                    status="pending", limit=None, online=False, db=None)
        base.update(kw)
        return _NS(**base)

    def test_list_zeigt_pending_eintraege(self):
        with tempfile.TemporaryDirectory() as d:
            state_con = statemod.connect(Path(d) / "state.db")
            # Zwei pending-Grenzfälle in die Queue legen (geflaggt -> apply_qa schreibt pending).
            for see, abr, ent in (("SEE_A", "ABR_A", "Klinikum X"), ("SEE_B", "ABR_B", "Stadt Y")):
                r = SignalRecord(see, abr, "T2", "2006-01-01", 0.9, "x",
                                 entity=ent, flags=("OEFFENTLICH_PRUEFEN",))
                self.assertEqual(qa_gate.apply_qa(r, state_con), "pending")
            state_con.close()

            con2 = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.statemod, "connect", return_value=con2), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_qa(self._args(status="pending"))
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("QA-Queue (pending): 2 Einträge", out)
        self.assertIn("SEE_A", out)
        self.assertIn("SEE_B", out)
        # Cache-Miss (kein --online, leerer mastr_url_cache) -> robuster Such-Link, kein toter SEE-Link
        self.assertIn("marktstammdatenregister.de", out)
        self.assertNotIn("IndexOeffentlich/SEE", out)

    def test_list_alle_status_filter(self):
        with tempfile.TemporaryDirectory() as d:
            con = statemod.connect(Path(d) / "state.db")
            r = SignalRecord("SEE_A", "ABR_A", "T2", "2006-01-01", 0.9, "x",
                             entity="Klinikum X", flags=("OEFFENTLICH_PRUEFEN",))
            qa_gate.apply_qa(r, con)
            qa_gate.reject(con, "SEE_A", "oeffentlich")   # -> rejected
            con.close()

            con2 = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.statemod, "connect", return_value=con2), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_qa(self._args(status="alle"))
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        # status='alle' -> Filter None -> der rejected-Eintrag erscheint
        self.assertIn("QA-Queue (alle): 1 Einträge", out)
        self.assertIn("rejected", out)

    def test_list_leere_queue(self):
        with tempfile.TemporaryDirectory() as d:
            con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.statemod, "connect", return_value=con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_qa(self._args())
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("QA-Queue (pending): 0 Einträge", out)

    def test_qa_approve_setzt_status(self):
        with tempfile.TemporaryDirectory() as d:
            con = statemod.connect(Path(d) / "state.db")
            r = SignalRecord("SEE_A", "ABR_A", "T2", "2006-01-01", 0.9, "x",
                             entity="Klinikum X", flags=("OEFFENTLICH_PRUEFEN",))
            qa_gate.apply_qa(r, con)
            con.close()
            con2 = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.statemod, "connect", return_value=con2), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_qa(self._args(action="approve", einheit="SEE_A", grund="echtes gewerbe"))
            out = buf.getvalue()
            # Verify gegen eine frische Verbindung
            con3 = statemod.connect(Path(d) / "state.db")
            row = con3.execute("SELECT status FROM qa_decision WHERE einheit_mastr_nr='SEE_A'").fetchone()
            con3.close()
        self.assertEqual(rc, 0)
        self.assertIn("approved: 1", out)
        self.assertEqual(row["status"], "approved")


# --------------------------------------------------------------------------- #
# (3b) cmd_signals / cmd_mengen gegen die synthetische open-mastr-artige DB
# --------------------------------------------------------------------------- #
class TestCmdSignals(unittest.TestCase):
    def _args(self, **kw):
        base = dict(db=None, gebiet="muensterland", plz="", region_name="",
                    kaeufer="", funktion="", offline=True, out="")
        base.update(kw)
        return _NS(**base)

    def test_signals_schreibt_lieferbar_csv_und_buckets(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            out = Path(d) / "signals.csv"
            src_con = _source_con(src)
            state_con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.cs, "load", return_value=_store()), \
                    mock.patch.object(cli.dbmod, "connect", return_value=src_con), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_signals(self._args(out=str(out)))
            output = buf.getvalue()
            self.assertTrue(out.exists(), output)
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual(rc, 0)
        # Genau die Firma (SEE1) ist lieferbar; Klinikum -> QA-pending, Privat -> namenlos.
        entities = {r["entity"] for r in rows}
        self.assertIn("Wegener Stahlservice GmbH", entities)
        self.assertNotIn("Klinikum Münster", entities)   # öffentlich -> nicht in der Lieferliste
        # Report-Zeile: 1 lieferbar, 1 QA-pending, 1 namenlos (SEE4 ist 2015, SEE5 andere PLZ)
        self.assertIn("1 lieferbar", output)
        self.assertIn("1 QA-pending", output)
        self.assertIn("1 namenlos", output)
        self.assertIn("Σ lieferbar (alle Gebiete): 1", output)
        # offline -> KEINE Evidenz-Direktlink-Zeile (kein Netz angefasst)
        self.assertNotIn("Evidenz-Direktlinks:", output)

    def test_signals_dv_flag_fuer_120_kwp(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            out = Path(d) / "signals.csv"
            src_con = _source_con(src)
            state_con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.cs, "load", return_value=_store()), \
                    mock.patch.object(cli.dbmod, "connect", return_value=src_con), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                cli.cmd_signals(self._args(out=str(out)))
            with open(out, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        # SEE1 hat 120 kWp >= 100 -> DV-Flag 'ja'
        see1 = next(r for r in rows if r["einheit_mastr_nr"] == "SEE1")
        self.assertEqual(see1["dv_flag"], "ja")

    def test_signals_inaktiver_trigger_uebersprungen(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            src_con = _source_con(src)
            state_con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.cs, "load", return_value=_store(t2_enabled=False)), \
                    mock.patch.object(cli.dbmod, "connect", return_value=src_con), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_signals(self._args())
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("Trigger T2 inaktiv", out)
        self.assertIn("Σ lieferbar (alle Gebiete): 0", out)

    def test_signals_adhoc_plz_ueberschreibt_gebiet(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            src_con = _source_con(src)
            state_con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            # --plz 70 (Stuttgart): SEE5 ist zwar Post-EEG, aber Firma -> lieferbar in 70.
            with mock.patch.object(cli.cs, "load", return_value=_store()), \
                    mock.patch.object(cli.dbmod, "connect", return_value=src_con), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_signals(self._args(plz="70", gebiet="", out=str(Path(d) / "s.csv")))
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        # ad-hoc-Label aus den PLZ-Präfixen
        self.assertIn("PLZ 70", out)
        self.assertIn("1 lieferbar", out)


class TestCmdMengen(unittest.TestCase):
    def _args(self, **kw):
        base = dict(db=None, gebiet="muensterland")
        base.update(kw)
        return _NS(**base)

    def test_mengen_report_struktur_und_zahlen(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            src_con = _source_con(src)
            state_con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.cs, "load", return_value=_store()), \
                    mock.patch.object(cli.dbmod, "connect", return_value=src_con), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_mengen(self._args())
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("EHRLICHER MENGEN-/DICHTE-REPORT", out)
        self.assertIn("Münsterland", out)
        # Reconciliation-Lesart steht im Report (Q4-Ehrlichkeit) — inkl. e.K.-gesperrt-Term (S0).
        self.assertIn("lieferbar + eK-gesperrt + QA-pend + namenlos + rejected + geplant = roh", out)

    def test_mengen_unbekanntes_gebiet_wird_uebersprungen(self):
        # store.gebiet('xx') -> None -> targets=[None] -> Schleife überspringt; Report bleibt leer (0 Zeilen).
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            src_con = _source_con(src)
            state_con = statemod.connect(Path(d) / "state.db")
            buf = io.StringIO()
            with mock.patch.object(cli.cs, "load", return_value=_store()), \
                    mock.patch.object(cli.dbmod, "connect", return_value=src_con), \
                    mock.patch.object(cli.statemod, "connect", return_value=state_con), \
                    contextlib.redirect_stdout(buf):
                rc = cli.cmd_mengen(self._args(gebiet="gibtsnicht"))
            out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("EHRLICHER MENGEN-/DICHTE-REPORT", out)   # Report kommt, nur ohne Gebiets-Zeile


class _NS:
    """Leichter argparse.Namespace-Ersatz (Attribut-Zugriff), damit cmd_*(args) direkt testbar ist."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
