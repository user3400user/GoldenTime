"""
Beweist das Register-Adapter-Interface (Komponente 1 / D4) gegen ein synthetisches SQLite —
OHNE open-mastr und OHNE den ~3-GB-Download (wie tests/test_speicher_abr.py).

Geprüft:
  * runtime_checkable-Konformität: MastrAdapter erfüllt das RegisterAdapter-Protocol.
  * iter_units gegen synthetisches solar_extended liefert NormalizedUnit mit korrekten
    stabilen Schlüsseln (einheit_id/betreiber_id/lokation_id), Standort, datum (= IBN),
    energietraeger_typ und kWp; Region-Filter (plz_prefixes) greift in SQL.
  * resolve_schema findet Tabelle + Spalten (und meldet Fehlendes tolerant).
  * Schnitt D4: KEINE Speicher-/Trigger-/Frische-Logik im Adapter — reg_datum bleibt in raw.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_register
"""
from __future__ import annotations

import sqlite3
import unittest

from pipeline.register import (
    ET_SOLAR,
    ET_SPEICHER,
    NormalizedUnit,
    RegisterAdapter,
    REGISTERS,
    SchemaMap,
    Standort,
)
from pipeline.adapters.mastr import MastrAdapter

# Synthetisches Schema wie in test_speicher_abr.py (reale *_extended-Spaltennamen).
SOLAR_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer",
    "AnlagenbetreiberName", "AnlagenbetreiberPersonenArt", "Postleitzahl", "Ort",
    "Bundesland", "Bruttoleistung", "Registrierungsdatum", "Inbetriebnahmedatum",
    "EegInbetriebnahmedatum", "Einspeisungsart", "EinheitBetriebsstatus",
    "SpeicherAmGleichenOrt",
]
STORAGE_COLS = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer"]

#  Einheit, ABR,    Lokation, Name, PersonenArt, PLZ, Ort, BL, kWp, reg, ibn, eeg, Einsp, Status, SpeicherAmOrt
SOLAR_ROWS = [
    ("SEE1", "ABR_A", "SEL_A1", "Müller GmbH", "Juristische Person", "48143", "Münster", "NRW",
     "100", "2025-01-10", "2025-01-05", None, "Teileinspeisung", "In Betrieb", "0"),
    ("SEE3", "ABR_C", "SEL_C3", "Schmidt AG", "Juristische Person", "59065", "Hamm", "NRW",
     "150,5", "2024-06-01", "2024-05-20", None, "Teileinspeisung", "In Betrieb", "0"),
    ("SEE5", "ABR_E", "SEL_E5", "Fischer GmbH", "Juristische Person", "80331", "München", "BY",
     "90", "2006-04-01", "2006-04-01", "2006-04-01", "Volleinspeisung", "In Betrieb", "0"),
]
STORAGE_ROWS = [
    ("SSE_C", "ABR_C", "SEL_C9"),
    ("SSE_D", "ABR_D", "SEL_D4"),
]


def _build_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})')
    con.execute(f'CREATE TABLE storage_extended ({", ".join(f"\"{c}\" TEXT" for c in STORAGE_COLS)})')
    con.executemany(
        f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})', SOLAR_ROWS
    )
    con.executemany(
        f'INSERT INTO storage_extended VALUES ({", ".join("?" for _ in STORAGE_COLS)})', STORAGE_ROWS
    )
    con.commit()
    return con


class TestProtocolConformance(unittest.TestCase):
    def test_mastr_adapter_is_register_adapter(self):
        # runtime_checkable: strukturelle Konformität (key/label + Methoden vorhanden).
        self.assertIsInstance(MastrAdapter(), RegisterAdapter)

    def test_registry_holds_mastr(self):
        self.assertIn("mastr", REGISTERS)
        self.assertIsInstance(REGISTERS["mastr"], RegisterAdapter)
        self.assertEqual(REGISTERS["mastr"].key, "mastr")
        self.assertEqual(REGISTERS["mastr"].label, "MaStR Gesamtdatenexport")


class TestResolveSchema(unittest.TestCase):
    def setUp(self):
        self.con = _build_db()
        self.adapter = MastrAdapter()

    def tearDown(self):
        self.con.close()

    def test_resolve_solar_table_and_columns(self):
        schema = self.adapter.resolve_schema(self.con, ET_SOLAR)
        self.assertIsInstance(schema, SchemaMap)
        self.assertEqual(schema.table, "solar_extended")
        # Logische -> reale Spaltennamen aufgelöst (case-insensitiv via db.column_map).
        self.assertEqual(schema.columns["einheit_nr"], "EinheitMastrNummer")
        self.assertEqual(schema.columns["abr"], "AnlagenbetreiberMastrNummer")
        self.assertEqual(schema.columns["lokation_nr"], "LokationMaStRNummer")
        self.assertEqual(schema.columns["inbetriebnahme"], "Inbetriebnahmedatum")
        self.assertEqual(schema.missing, ())  # alle _SELECT-Felder vorhanden

    def test_resolve_storage_table(self):
        schema = self.adapter.resolve_schema(self.con, ET_SPEICHER)
        self.assertEqual(schema.table, "storage_extended")
        self.assertEqual(schema.columns["einheit_nr"], "EinheitMastrNummer")
        # Storage-Stub hat keine PLZ/kWp-Spalten -> als fehlend gemeldet, nicht geworfen.
        self.assertIn("plz", schema.missing)

    def test_unknown_energietraeger_raises(self):
        with self.assertRaises(ValueError):
            self.adapter.resolve_schema(self.con, "kernfusion")


class TestIterUnits(unittest.TestCase):
    def setUp(self):
        self.con = _build_db()
        self.adapter = MastrAdapter()

    def tearDown(self):
        self.con.close()

    def _by_id(self, **kw) -> dict:
        return {u.einheit_id: u for u in self.adapter.iter_units(self.con, **kw)}

    def test_region_filter_in_sql(self):
        units = self._by_id(plz_prefixes=("48",))
        self.assertEqual(set(units), {"SEE1"})   # nur 48er Münster
        units59 = self._by_id(plz_prefixes=("59",))
        self.assertEqual(set(units59), {"SEE3"})

    def test_normalized_unit_stable_keys(self):
        u = self._by_id(plz_prefixes=("48",))["SEE1"]
        self.assertIsInstance(u, NormalizedUnit)
        self.assertEqual(u.einheit_id, "SEE1")
        self.assertEqual(u.betreiber_id, "ABR_A")
        self.assertEqual(u.lokation_id, "SEL_A1")
        self.assertEqual(u.energietraeger_typ, ET_SOLAR)
        self.assertEqual(u.quelle, "mastr")

    def test_standort_and_datum_is_ibn(self):
        u = self._by_id(plz_prefixes=("48",))["SEE1"]
        self.assertIsInstance(u.standort, Standort)
        self.assertEqual(u.standort.plz, "48143")
        self.assertEqual(u.standort.ort, "Münster")
        self.assertEqual(u.standort.bundesland, "NRW")
        # datum = Inbetriebnahmedatum (R3 §7b), NICHT Registrierungsdatum.
        self.assertEqual(u.datum, "2025-01-05")
        # reg_datum bleibt quell-spezifisch in raw (Schnitt D4: keine Frische-Logik hier).
        self.assertEqual(u.raw["reg_datum"], "2025-01-10")

    def test_leistung_parsed_to_float(self):
        u = self._by_id(plz_prefixes=("59",))["SEE3"]
        self.assertEqual(u.leistung_kw, 150.5)   # "150,5" tolerant geparst

    def test_no_region_requires_limit(self):
        with self.assertRaises(ValueError):
            list(self.adapter.iter_units(self.con))

    def test_limit_without_region(self):
        units = list(self.adapter.iter_units(self.con, limit=2))
        self.assertEqual(len(units), 2)

    def test_multiple_energietraeger(self):
        # Beide Träger in einem Lauf -> Solar + Storage gemischt (limit je Träger).
        units = list(
            self.adapter.iter_units(
                self.con, energietraeger=(ET_SOLAR, ET_SPEICHER), limit=2
            )
        )
        traeger = {u.energietraeger_typ for u in units}
        self.assertEqual(traeger, {ET_SOLAR, ET_SPEICHER})


if __name__ == "__main__":
    unittest.main(verbosity=2)
