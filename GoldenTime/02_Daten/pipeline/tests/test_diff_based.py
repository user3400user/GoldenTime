"""
Beweist die diff-basierten Trigger (3b) gegen zwei synthetische Snapshot-SQLite — OHNE den
~3-GB-Download, OHNE open-mastr, OHNE Netz. Deckt:

  * T1  (Neuregistrierung solar an NEUER ABR)      — default AN  -> emittiert
  * T4  (Speicher-Retrofit an Solar-Betreiber)     — default AN  -> emittiert, Retrofit-Lücke
  * PV_ERWEITERUNG (Zweit-solar an Bestands-ABR)   — default AUS -> NICHT emittiert
  * T5  (Betreiberwechsel, abr-Wechsel)            — default AUS -> NICHT emittiert; AN -> emittiert
  * T6  (Stilllegung leer->gesetzt)                — default AUS -> NICHT emittiert; AN -> emittiert
  * Config-Gate über store.effective_trigger / is_trigger_enabled
  * Konfidenz-Gründe (T4 Retrofit-Lücke, T5 Umfirmierungs-Vorbehalt)

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_diff_based
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.control import config_store as cs
from pipeline.snapshot.store import SNAPSHOT_FIELDS
from pipeline.triggers import diff_based

# snapshot-Schema 1:1 wie snapshot.store._CREATE_SQL (PK = einheit_nr).
_CREATE_SQL = """
CREATE TABLE snapshot (
    einheit_nr               TEXT PRIMARY KEY,
    traeger                  TEXT NOT NULL,
    abr                      TEXT,
    eeg_nr                   TEXT,
    brutto_kw                REAL,
    inbetriebnahme           TEXT,
    datum_stilllegung_endg   TEXT,
    datum_stilllegung_vorueb TEXT,
    betriebsstatus           TEXT
)
"""


def _row(einheit, traeger, abr, brutto_kw, inbetriebnahme,
         stilllegung_endg=None, stilllegung_vorueb=None, betriebsstatus="In Betrieb",
         eeg_nr=None):
    """Snapshot-Zeile in SNAPSHOT_FIELDS-Reihenfolge (kompakt für die Fixtures)."""
    return (einheit, traeger, abr, eeg_nr, brutto_kw, inbetriebnahme,
            stilllegung_endg, stilllegung_vorueb, betriebsstatus)


def _write_snapshot(path: Path, rows: list[tuple]) -> None:
    con = sqlite3.connect(str(path))
    try:
        con.execute(_CREATE_SQL)
        ph = ", ".join("?" for _ in SNAPSHOT_FIELDS)
        con.executemany(
            f"INSERT INTO snapshot ({', '.join(SNAPSHOT_FIELDS)}) VALUES ({ph})", rows
        )
        con.commit()
    finally:
        con.close()


# --- Fixtures: prev hält Bestand (ABR_BESTAND führt Solar); curr bringt die Diffs ---
PREV_ROWS = [
    # Bestands-Solar an ABR_BESTAND -> macht ABR_BESTAND zum Solar-Betreiber (T4-/PV-Bezug).
    _row("SEE_BESTAND", "solar", "ABR_BESTAND", 120.0, "2015-03-01"),
    # Einheit, deren ABR in curr wechselt -> T5.
    _row("SEE_WECHSEL", "solar", "ABR_ALT", 200.0, "2016-06-01"),
    # Einheit, die in curr stillgelegt wird -> T6.
    _row("SEE_STILL", "solar", "ABR_STILL", 300.0, "2017-09-01"),
]

CURR_ROWS = [
    # Bestand unverändert mitführen (sonst sähe der Diff sie als REMOVED).
    _row("SEE_BESTAND", "solar", "ABR_BESTAND", 120.0, "2015-03-01"),
    # T1: neue Solar-Einheit an NEUER ABR (kein Bestands-Solar) -> Erst-Anmeldung.
    _row("SEE_NEU_T1", "solar", "ABR_NEU", 150.0, "2026-06-10"),
    # PV_ERWEITERUNG: neue Solar-Einheit an BESTANDS-ABR -> Zweit-Einheit (default AUS).
    _row("SEE_NEU_PV", "solar", "ABR_BESTAND", 80.0, "2026-06-11"),
    # T4: neuer Speicher an ABR_BESTAND (führt Bestands-Solar) -> Retrofit (SCHARF).
    _row("SSE_NEU_T4", "storage", "ABR_BESTAND", 90.0, "2026-06-12"),
    # T5: ABR-Wechsel an Bestands-Einheit (ABR_ALT -> ABR_NEU2).
    _row("SEE_WECHSEL", "solar", "ABR_NEU2", 200.0, "2016-06-01"),
    # T6: Stilllegungsdatum leer -> gesetzt.
    _row("SEE_STILL", "solar", "ABR_STILL", 300.0, "2017-09-01",
         stilllegung_endg="2026-05-01", betriebsstatus="Endgültig stillgelegt"),
]


def _store(**trigger_overrides_enabled) -> cs.ConfigStore:
    """Baue einen ConfigStore mit Default-Triggern; ``T5=True`` o. ä. überschreibt enabled."""
    triggers = {t: {"enabled": en, "label": t}
                for t, en in {
                    "T1": True, "T2": True, "T3": True, "T4": True,
                    "T5": False, "T6": False, "DV_FLAG": True, "PV_ERWEITERUNG": False,
                }.items()}
    for key, enabled in trigger_overrides_enabled.items():
        triggers[key] = {"enabled": enabled, "label": key}
    return cs.ConfigStore(
        schema_version=cs.SCHEMA_VERSION,
        triggers=triggers,
        modules={"anreicherung": {"enabled": False, "label": "x"}},
        gebiete=(),
    )


class DiffBasedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.prev = base / "snap_2026-06-01.sqlite"
        self.curr = base / "snap_2026-06-15.sqlite"
        _write_snapshot(self.prev, PREV_ROWS)
        _write_snapshot(self.curr, CURR_ROWS)

    def tearDown(self):
        self.tmp.cleanup()

    def _signals(self, store, **kw):
        return {s.einheit_mastr_nr: s
                for s in diff_based.diff_based_signals(self.prev, self.curr, store, **kw)}

    # --- Default-Config: T1/T4 emittiert; T5/T6/PV_ERWEITERUNG NICHT ---
    def test_default_emits_t1_and_t4_only(self):
        sigs = self._signals(_store())
        self.assertIn("SEE_NEU_T1", sigs)          # T1 default AN
        self.assertIn("SSE_NEU_T4", sigs)          # T4 default AN
        self.assertNotIn("SEE_NEU_PV", sigs)       # PV_ERWEITERUNG default AUS
        self.assertNotIn("SEE_WECHSEL", sigs)      # T5 default AUS
        self.assertNotIn("SEE_STILL", sigs)        # T6 default AUS

    def test_t1_record_shape(self):
        t1 = self._signals(_store())["SEE_NEU_T1"]
        self.assertEqual(t1.trigger_typ, "T1")
        self.assertEqual(t1.betreiber_mastr_nr, "ABR_NEU")
        self.assertEqual(t1.kwp, 150.0)
        self.assertEqual(t1.datum, "2026-06-10")
        self.assertTrue(t1.dv_flag)                # 150 kWp >= 100
        self.assertIn("DIFF_NEW_UNIT", t1.flags)
        # T1 ohne gemeldeten Speicher -> „kein Speicher gemeldet"-Abschlag im Konfidenz-Grund.
        self.assertTrue(any("kein Speicher" in g for g in t1.konfidenz_gruende))
        self.assertTrue(0.0 <= t1.konfidenz <= 1.0)

    def test_t4_carries_retrofit_konfidenz(self):
        t4 = self._signals(_store())["SSE_NEU_T4"]
        self.assertEqual(t4.trigger_typ, "T4")
        self.assertIn("RETROFIT_GEMELDET", t4.flags)
        # §4-Falle 3: Retrofit-Meldung lückenhaft -> benannter Konfidenz-Grund.
        self.assertTrue(any("Retrofit" in g or "lückenhaft" in g for g in t4.konfidenz_gruende))
        # T4 trägt den Retrofit-Abschlag -> Konfidenz unter dem T1-Wert.
        t1 = self._signals(_store())["SEE_NEU_T1"]
        self.assertLess(t4.konfidenz, t1.konfidenz)

    # --- Scharfschalten via Config-Store: T5/T6/PV_ERWEITERUNG werden dann emittiert ---
    def test_t5_emitted_when_enabled(self):
        sigs = self._signals(_store(T5=True))
        self.assertIn("SEE_WECHSEL", sigs)
        t5 = sigs["SEE_WECHSEL"]
        self.assertEqual(t5.trigger_typ, "T5")
        self.assertEqual(t5.betreiber_mastr_nr, "ABR_NEU2")   # neue ABR aus curr
        self.assertIn("DIFF_FIELD_CHANGED", t5.flags)
        self.assertIn("UMFIRMIERUNG_PRUEFEN", t5.flags)
        # §4-Falle 2: Umfirmierungs-Vorbehalt als Konfidenz-Grund.
        self.assertTrue(any("Umfirmierung" in g for g in t5.konfidenz_gruende))

    def test_t6_emitted_when_enabled(self):
        sigs = self._signals(_store(T6=True))
        self.assertIn("SEE_STILL", sigs)
        self.assertEqual(sigs["SEE_STILL"].trigger_typ, "T6")
        self.assertIn("DIFF_FIELD_CHANGED", sigs["SEE_STILL"].flags)

    def test_pv_erweiterung_emitted_when_enabled(self):
        sigs = self._signals(_store(PV_ERWEITERUNG=True))
        self.assertIn("SEE_NEU_PV", sigs)
        self.assertEqual(sigs["SEE_NEU_PV"].trigger_typ, "PV_ERW")

    # --- Gebiets-Override: kann scharfgeschaltetes ABschalten (D3-Semantik) ---
    def test_gebiet_override_can_disable(self):
        store = cs.ConfigStore(
            schema_version=cs.SCHEMA_VERSION,
            triggers=_store().triggers,                  # T1 global AN
            modules={"anreicherung": {"enabled": False, "label": "x"}},
            gebiete=({"id": "g1", "name": "G1", "enabled": True,
                      "plz_prefixes": ["48"], "trigger_overrides": {"T1": False}},),
        )
        sigs = self._signals(store, gebiet_id="g1")
        self.assertNotIn("SEE_NEU_T1", sigs)             # T1 fürs Gebiet abgeschaltet

    def test_enrichment_optional_without_con(self):
        # Ohne con bleibt Region/Name None (Snapshot trägt keine PLZ) — Signal ist trotzdem valide.
        t1 = self._signals(_store())["SEE_NEU_T1"]
        self.assertIsNone(t1.plz)
        self.assertIsNone(t1.entity)

    def test_enrichment_with_con_fills_region(self):
        # Mit con (synthetische solar_extended) wird PLZ/Ort/Bundesland angereichert.
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute(
            'CREATE TABLE solar_extended ("EinheitMastrNummer" TEXT, "Postleitzahl" TEXT, '
            '"Ort" TEXT, "Bundesland" TEXT)'
        )
        con.execute(
            'INSERT INTO solar_extended VALUES (?,?,?,?)',
            ("SEE_NEU_T1", "48143", "Münster", "Nordrhein-Westfalen"),
        )
        con.commit()
        try:
            t1 = self._signals(_store(), con=con)["SEE_NEU_T1"]
        finally:
            con.close()
        self.assertEqual(t1.plz, "48143")
        self.assertEqual(t1.ort, "Münster")
        self.assertEqual(t1.bundesland, "Nordrhein-Westfalen")


if __name__ == "__main__":
    unittest.main(verbosity=2)
