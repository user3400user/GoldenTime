"""
Direkt-Tests des Schema-Resolvers (pipeline/db.py).

Kern-Zweck von db.py: die Query-Logik gegen die exakte open-mastr-Schreibweise entkoppeln —
Tabellen/Spalten werden CASE-INSENSITIV (und für Tabellen zusätzlich per Teilstring) gegen die
tatsächliche DB aufgelöst. Diese Suite sichert genau diese Toleranz ab:
  - resolve_table: exakter (case-insensitiver) Treffer, Teilstring-Treffer, Vorrang exakt>Teilstring,
                   Mehrfach-Kandidaten, nicht gefunden -> LookupError (mit sprechender Meldung).
  - resolve_column / column_map: Casing, Teil-Verfügbarkeit, fehlende Spalte -> None/leerer Eintrag.
  - list_tables / table_columns: sqlite_master- bzw. PRAGMA-Parsing über synthetische Schemata.

stdlib 'unittest', KEIN Netz, KEINE 3rd-party-Libs, NICHT die 8,6-GB-Export-DB — alles über
synthetische in-memory sqlite mit Tabellen/Spalten in verschiedenen Schreibweisen.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_db -v
"""
from __future__ import annotations

import sqlite3
import unittest

from pipeline import db


def _con(*create_sql: str) -> sqlite3.Connection:
    """In-memory DB mit den gegebenen CREATE-Statements; Row-Factory wie in db.connect()."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    for sql in create_sql:
        con.execute(sql)
    con.commit()
    return con


class TestListTables(unittest.TestCase):
    def test_lists_only_tables_sorted(self):
        con = _con(
            'CREATE TABLE "Solar_Extended" (a TEXT)',
            'CREATE TABLE "market_actors" (b TEXT)',
            'CREATE TABLE "ZZZ" (c TEXT)',
        )
        # alphabetisch sortiert (ORDER BY name), exakte Schreibweise erhalten
        self.assertEqual(db.list_tables(con), ["Solar_Extended", "ZZZ", "market_actors"])

    def test_ignores_views_and_indexes(self):
        con = _con(
            "CREATE TABLE base (x INTEGER PRIMARY KEY, y TEXT)",
            "CREATE INDEX idx_base_y ON base (y)",
            "CREATE VIEW v_base AS SELECT x FROM base",
        )
        # nur echte Tabellen, KEIN View / KEIN Index (type='table' Filter)
        self.assertEqual(db.list_tables(con), ["base"])

    def test_empty_db(self):
        self.assertEqual(db.list_tables(_con()), [])


class TestTableColumns(unittest.TestCase):
    def test_pragma_parsing_preserves_casing_and_order(self):
        con = _con(
            'CREATE TABLE solar_extended '
            '("EinheitMastrNummer" TEXT, "AnlagenbetreiberMastrNummer" TEXT, "Bruttoleistung" REAL)'
        )
        self.assertEqual(
            db.table_columns(con, "solar_extended"),
            ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "Bruttoleistung"],
        )

    def test_quoted_table_name_with_mixed_case(self):
        # table_columns quotet den Namen -> MixedCase-Tabellen funktionieren
        con = _con('CREATE TABLE "MarketActors" ("Firmenname" TEXT, "MastrNummer" TEXT)')
        self.assertEqual(db.table_columns(con, "MarketActors"), ["Firmenname", "MastrNummer"])

    def test_unknown_table_returns_empty(self):
        # PRAGMA table_info auf nicht existierende Tabelle -> keine Zeilen -> leere Liste
        con = _con("CREATE TABLE present (a TEXT)")
        self.assertEqual(db.table_columns(con, "absent"), [])


class TestResolveTableExact(unittest.TestCase):
    def test_exact_lowercase_candidate(self):
        # Kandidat 'market_actors' liegt exakt vor
        con = _con("CREATE TABLE market_actors (a TEXT)")
        self.assertEqual(db.resolve_table(con, "market"), "market_actors")

    def test_case_insensitive_match_returns_real_casing(self):
        # reale Tabelle MixedCase, Kandidat lowercase -> case-insensitiver Treffer,
        # zurück kommt die REALE Schreibweise (für korrektes Quoting in Queries).
        con = _con('CREATE TABLE "Solar_Extended" (a TEXT)')
        self.assertEqual(db.resolve_table(con, "solar"), "Solar_Extended")

    def test_uppercase_db_lowercase_candidate(self):
        con = _con('CREATE TABLE "STORAGE_EXTENDED" (a TEXT)')
        self.assertEqual(db.resolve_table(con, "storage"), "STORAGE_EXTENDED")


class TestResolveTableCandidatePriority(unittest.TestCase):
    def test_first_candidate_wins_over_later(self):
        # Beide Kandidaten existieren; der ZUERST gelistete (solar_extended) gewinnt.
        con = _con(
            "CREATE TABLE solar_extended (a TEXT)",
            "CREATE TABLE einheitensolar (a TEXT)",
        )
        self.assertEqual(db.resolve_table(con, "solar"), "solar_extended")

    def test_falls_through_to_second_candidate(self):
        # Erster Kandidat fehlt -> zweiter (deutscher Legacy-Name) trägt.
        con = _con("CREATE TABLE einheitensolar (a TEXT)")
        self.assertEqual(db.resolve_table(con, "solar"), "einheitensolar")

    def test_exact_match_beats_substring_match(self):
        # Vorrang: der ERSTE exakte (case-insensitive) Kandidaten-Treffer schlägt jeden
        # Teilstring-Treffer — beide Schleifen sind getrennt (exakt zuerst, dann Teilstring).
        # Logischer Schlüssel ohne TABLE_CANDIDATES-Eintrag -> einziger Kandidat = 'lok',
        # der exakt UND als Teilstring (in 'lok_extended') vorkommt.
        con = _con(
            "CREATE TABLE lok_extended (a TEXT)",   # würde nur per Teilstring matchen
            "CREATE TABLE lok (a TEXT)",            # exakter Kandidaten-Treffer
        )
        self.assertEqual(db.resolve_table(con, "lok"), "lok")

    def test_candidate_order_decides_among_existing_exact_matches(self):
        # Reale TABLE_CANDIDATES['location'] = ('locations_extended', 'locations',
        # 'location', ...). Liegen MEHRERE Kandidaten exakt vor, gewinnt der zuerst
        # gelistete ('locations_extended'), NICHT der „kürzere" Name 'location'.
        con = _con(
            "CREATE TABLE locations_extended (a TEXT)",
            "CREATE TABLE location (a TEXT)",
        )
        self.assertEqual(db.resolve_table(con, "location"), "locations_extended")


class TestResolveTableSubstring(unittest.TestCase):
    def test_substring_fallback(self):
        # Kein exakter Kandidat, aber 'solar' steckt in 'solar_extended_v2' -> Teilstring-Treffer.
        con = _con("CREATE TABLE solar_extended_v2 (a TEXT)")
        self.assertEqual(db.resolve_table(con, "solar"), "solar_extended_v2")

    def test_substring_case_insensitive(self):
        con = _con('CREATE TABLE "MARKET_ACTORS_2025" (a TEXT)')
        # Kandidat 'market_actors' steckt (case-insensitiv) in 'MARKET_ACTORS_2025'
        self.assertEqual(db.resolve_table(con, "market"), "MARKET_ACTORS_2025")

    def test_default_candidate_uses_logical_key(self):
        # Logischer Schlüssel ohne Eintrag in TABLE_CANDIDATES -> Kandidat = (logical,).
        con = _con('CREATE TABLE "FooBar" (a TEXT)')
        self.assertEqual(db.resolve_table(con, "foobar"), "FooBar")


class TestResolveTableNotFound(unittest.TestCase):
    def test_raises_lookuperror(self):
        con = _con("CREATE TABLE irrelevant (a TEXT)")
        with self.assertRaises(LookupError):
            db.resolve_table(con, "solar")

    def test_lookuperror_message_lists_candidates_and_existing(self):
        con = _con("CREATE TABLE irrelevant (a TEXT)")
        with self.assertRaises(LookupError) as ctx:
            db.resolve_table(con, "storage")
        msg = str(ctx.exception)
        self.assertIn("storage", msg)               # logischer Schlüssel
        self.assertIn("storage_extended", msg)      # ein Kandidat
        self.assertIn("irrelevant", msg)            # vorhandene Tabelle gemeldet

    def test_unknown_logical_without_match_raises(self):
        con = _con("CREATE TABLE present (a TEXT)")
        with self.assertRaises(LookupError):
            db.resolve_table(con, "voellig_unbekannt")


class TestResolveColumn(unittest.TestCase):
    def test_exact_candidate(self):
        cols = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer"]
        self.assertEqual(db.resolve_column(cols, "einheit_nr"), "EinheitMastrNummer")

    def test_case_insensitive_returns_real_casing(self):
        # DB schreibt klein, Kandidat ist 'EinheitMastrNummer' -> trifft case-insensitiv,
        # zurück kommt die reale (kleingeschriebene) Spalte.
        cols = ["einheitmastrnummer", "anlagenbetreibermastrnummer"]
        self.assertEqual(db.resolve_column(cols, "einheit_nr"), "einheitmastrnummer")

    def test_lokation_two_candidates_resolves_either_casing(self):
        # 'lokation_nr' hat zwei Kandidaten (LokationMaStRNummer / LokationMastrNummer),
        # die sich NUR im Casing unterscheiden -> beide Schreibweisen lösen auf.
        self.assertEqual(
            db.resolve_column(["LokationMaStRNummer"], "lokation_nr"), "LokationMaStRNummer"
        )
        self.assertEqual(
            db.resolve_column(["LokationMastrNummer"], "lokation_nr"), "LokationMastrNummer"
        )

    def test_first_candidate_preferred_when_both_present(self):
        # eeg_nr-Kandidaten: ('EegMaStRNummer', 'EegMastrNummer') — beide da -> erster gewinnt.
        cols = ["EegMastrNummer", "EegMaStRNummer"]
        self.assertEqual(db.resolve_column(cols, "eeg_nr"), "EegMaStRNummer")

    def test_missing_column_returns_none(self):
        # Spalte fehlt komplett -> None (Aufrufer entscheidet, robust statt Crash).
        self.assertIsNone(db.resolve_column(["irgendwas"], "einheit_nr"))

    def test_empty_columns_returns_none(self):
        self.assertIsNone(db.resolve_column([], "abr"))

    def test_default_candidate_uses_logical_key(self):
        # Logischer Schlüssel ohne COL-Eintrag -> Kandidat = (logical,), case-insensitiv.
        self.assertEqual(db.resolve_column(["Sonderspalte"], "sonderspalte"), "Sonderspalte")
        self.assertIsNone(db.resolve_column(["andere"], "sonderspalte"))


class TestColumnMap(unittest.TestCase):
    def test_full_availability(self):
        cols = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "Bruttoleistung"]
        m = db.column_map(cols, "einheit_nr", "abr", "brutto_kw")
        self.assertEqual(
            m,
            {
                "einheit_nr": "EinheitMastrNummer",
                "abr": "AnlagenbetreiberMastrNummer",
                "brutto_kw": "Bruttoleistung",
            },
        )

    def test_partial_availability_missing_is_none(self):
        # Teil-Verfügbarkeit: vorhandene Spalten lösen auf, fehlende -> None (Schlüssel bleibt da).
        cols = ["einheitmastrnummer"]   # nur eine, dazu kleingeschrieben
        m = db.column_map(cols, "einheit_nr", "abr", "plz")
        self.assertEqual(m, {"einheit_nr": "einheitmastrnummer", "abr": None, "plz": None})

    def test_keys_are_logical_names_and_complete(self):
        # Jeder angefragte logische Name MUSS als Schlüssel erscheinen (auch wenn None).
        m = db.column_map([], "einheit_nr", "abr")
        self.assertEqual(set(m), {"einheit_nr", "abr"})
        self.assertTrue(all(v is None for v in m.values()))

    def test_no_logicals_returns_empty(self):
        self.assertEqual(db.column_map(["EinheitMastrNummer"]), {})

    def test_uses_table_columns_end_to_end(self):
        # Realistischer Fluss: Spalten aus PRAGMA -> column_map. MixedCase in der DB,
        # logische Felder lösen case-insensitiv auf.
        con = _con(
            'CREATE TABLE solar_extended '
            '("EinheitMastrNummer" TEXT, "Postleitzahl" TEXT, "Bruttoleistung" REAL)'
        )
        cols = db.table_columns(con, "solar_extended")
        m = db.column_map(cols, "einheit_nr", "plz", "netto_kw")
        self.assertEqual(
            m,
            {"einheit_nr": "EinheitMastrNummer", "plz": "Postleitzahl", "netto_kw": None},
        )


class TestResolverEndToEnd(unittest.TestCase):
    """resolve_table -> table_columns -> column_map als zusammenhängender Pfad (wie die Pipeline)."""

    def test_mixedcase_db_full_resolution(self):
        con = _con(
            'CREATE TABLE "Solar_Extended" '
            '("EinheitMastrNummer" TEXT, "AnlagenbetreiberMastrNummer" TEXT, '
            '"LokationMastrNummer" TEXT, "Postleitzahl" TEXT)'
        )
        table = db.resolve_table(con, "solar")
        self.assertEqual(table, "Solar_Extended")
        cols = db.table_columns(con, table)
        m = db.column_map(cols, "einheit_nr", "abr", "lokation_nr", "plz", "brutto_kw")
        self.assertEqual(m["einheit_nr"], "EinheitMastrNummer")
        self.assertEqual(m["abr"], "AnlagenbetreiberMastrNummer")
        self.assertEqual(m["lokation_nr"], "LokationMastrNummer")  # Casing-Variante 2 aufgelöst
        self.assertEqual(m["plz"], "Postleitzahl")
        self.assertIsNone(m["brutto_kw"])                          # Spalte fehlt -> None


if __name__ == "__main__":
    unittest.main(verbosity=2)
