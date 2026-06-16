"""
Tests für die Snapshot+Diff-Engine (Komponente 2, D2) — stdlib, synthetische SQLite.

Beweist OHNE open-mastr/3-GB-Download:
  * write_snapshot liest die 7 Diff-Schlüsselfelder schema-tolerant aus einer
    open-mastr-artigen Quell-DB in eine dated snap_<datum>.sqlite,
  * diff erkennt NEW_UNIT / REMOVED / FIELD_CHANGED (datum-/float-tolerant),
  * classify_diff klassifiziert nach Briefing §4: NEW_UNIT solar -> T1/PV_ERWEITERUNG,
    neuer Speicher -> T4, abr-Wechsel -> T5 (Konfidenz-Flag), Stilllegung leer->gesetzt -> T6,
  * list_snapshots/latest_two/prune über den Dateinamen.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_snapshot_diff
"""
from __future__ import annotations

import datetime as dt
import sqlite3
import tempfile
import unittest
from pathlib import Path

import pipeline.snapshot.diff as diffmod   # Submodul explizit (Paket-Attr 'diff' = re-exportierte Funktion)
from pipeline.snapshot import rules, store
from pipeline.snapshot.store import SNAPSHOT_FIELDS

# --- Schema einer open-mastr-artigen Quell-DB (vgl. test_speicher_abr) ---
SOLAR_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "EegMastrNummer",
    "Bruttoleistung", "Inbetriebnahmedatum", "DatumEndgueltigeStilllegung",
    "DatumBeginnVoruebergehendeStilllegung", "EinheitBetriebsstatus",
]
STORAGE_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "Bruttoleistung",
    "Inbetriebnahmedatum", "DatumEndgueltigeStilllegung",
    "DatumBeginnVoruebergehendeStilllegung", "EinheitBetriebsstatus",
]

#  Einheit, ABR, EEG, kWp, IBN, still_endg, still_vorueb, Status
SOLAR_ROWS = [
    ("SEE1", "ABR_A", "EEG1", "100.0", "2024-05-01", None, None, "In Betrieb"),
    ("SEE2", "ABR_B", "EEG2", "200.0", "2024-06-01", None, None, "In Betrieb"),
]
#  Speicher (storage): Einheit, ABR, kWp, IBN, still_endg, still_vorueb, Status
STORAGE_ROWS = [
    ("SSE1", "ABR_A", "50.0", "2024-04-01", None, None, "In Betrieb"),
]


def _build_source_db(path: Path) -> None:
    """Synthetische open-mastr-artige Quell-DB (solar_extended + storage_extended)."""
    con = sqlite3.connect(str(path))
    con.execute(f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})')
    con.execute(f'CREATE TABLE storage_extended ({", ".join(f"\"{c}\" TEXT" for c in STORAGE_COLS)})')
    con.executemany(
        f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})', SOLAR_ROWS
    )
    con.executemany(
        f'INSERT INTO storage_extended VALUES ({", ".join("?" for _ in STORAGE_COLS)})', STORAGE_ROWS
    )
    con.commit()
    con.close()


def _write_snap(path: Path, rows: list[tuple]) -> None:
    """Schreibe direkt eine snapshot-SQLite (für isolierte Diff-Tests, ohne Quell-DB)."""
    con = sqlite3.connect(str(path))
    con.execute(store._CREATE_SQL)
    placeholders = ", ".join("?" for _ in SNAPSHOT_FIELDS)
    con.executemany(
        f"INSERT INTO snapshot ({', '.join(SNAPSHOT_FIELDS)}) VALUES ({placeholders})", rows
    )
    con.commit()
    con.close()


# Hilfs-Zeilen für die snapshot-Tabelle (Feld-Reihenfolge = SNAPSHOT_FIELDS):
#  einheit_nr, traeger, abr, eeg_nr, brutto_kw, inbetriebnahme, still_endg, still_vorueb, status
def _row(einheit, traeger="solar", abr="ABR_A", eeg="EEG1", kw=100.0, ibn="2024-05-01",
         endg=None, vorueb=None, status="In Betrieb"):
    return (einheit, traeger, abr, eeg, kw, ibn, endg, vorueb, status)


class TestWriteSnapshot(unittest.TestCase):
    def test_skinny_extract_from_source_db(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            con = sqlite3.connect(str(src))
            con.row_factory = sqlite3.Row
            out = store.write_snapshot(con, out_path=Path(d) / "snap_2026-06-16.sqlite",
                                       datum="2026-06-16")
            con.close()

            self.assertTrue(out.exists())
            snap = sqlite3.connect(str(out))
            snap.row_factory = sqlite3.Row
            byid = {r["einheit_nr"]: dict(r) for r in snap.execute("SELECT * FROM snapshot")}
            snap.close()

            # 2 Solar + 1 Speicher, beide Träger getrennt markiert
            self.assertEqual(set(byid), {"SEE1", "SEE2", "SSE1"})
            self.assertEqual(byid["SEE1"]["traeger"], "solar")
            self.assertEqual(byid["SSE1"]["traeger"], "storage")
            # brutto_kw als echtes REAL gespeichert (float-toleranter Diff)
            self.assertIsInstance(byid["SEE1"]["brutto_kw"], float)
            self.assertEqual(byid["SEE1"]["brutto_kw"], 100.0)
            # storage hat kein eeg_nr -> NULL-Literal, kein Crash
            self.assertIsNone(byid["SSE1"]["eeg_nr"])

    def test_default_path_uses_snapshot_dir_and_datum(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "open-mastr.db"
            _build_source_db(src)
            con = sqlite3.connect(str(src))
            con.row_factory = sqlite3.Row
            # SNAPSHOT_DIR temporär umbiegen (read-only Contract config.py NICHT ändern)
            import pipeline.config as cfg
            orig = cfg.SNAPSHOT_DIR
            cfg.SNAPSHOT_DIR = Path(d) / "snaps"
            try:
                out = store.write_snapshot(con, datum="2026-01-02")
                self.assertEqual(out.name, "snap_2026-01-02.sqlite")
                self.assertEqual(out.parent, cfg.SNAPSHOT_DIR)
            finally:
                cfg.SNAPSHOT_DIR = orig
                con.close()


class TestDiff(unittest.TestCase):
    def _two_snaps(self, d, prev_rows, curr_rows):
        prev = Path(d) / "snap_2026-06-09.sqlite"
        curr = Path(d) / "snap_2026-06-16.sqlite"
        _write_snap(prev, prev_rows)
        _write_snap(curr, curr_rows)
        return prev, curr

    def test_new_unit_and_removed(self):
        with tempfile.TemporaryDirectory() as d:
            prev, curr = self._two_snaps(
                d,
                prev_rows=[_row("SEE1"), _row("SEE_GONE", abr="ABR_Z")],
                curr_rows=[_row("SEE1"), _row("SEE_NEW", abr="ABR_NEW")],
            )
            evs = list(diffmod.diff(prev, curr))
            by_type = {(e.einheit_nr, e.change_type) for e in evs}
            self.assertIn(("SEE_NEW", diffmod.NEW_UNIT), by_type)
            self.assertIn(("SEE_GONE", diffmod.REMOVED), by_type)
            # SEE1 unverändert -> kein Event
            self.assertNotIn("SEE1", {e.einheit_nr for e in evs})

    def test_abr_change_is_field_changed(self):
        with tempfile.TemporaryDirectory() as d:
            prev, curr = self._two_snaps(
                d,
                prev_rows=[_row("SEE1", abr="ABR_ALT")],
                curr_rows=[_row("SEE1", abr="ABR_NEU")],
            )
            evs = [e for e in diffmod.diff(prev, curr) if e.field == "abr"]
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0].change_type, diffmod.FIELD_CHANGED)
            self.assertEqual((evs[0].old, evs[0].new), ("ABR_ALT", "ABR_NEU"))

    def test_float_tolerant_kw_no_false_positive(self):
        with tempfile.TemporaryDirectory() as d:
            # "100.0" vs 100.00 vs "100,0" -> KEINE Änderung (Format-/Komma-Rauschen)
            prev, curr = self._two_snaps(
                d,
                prev_rows=[_row("SEE1", kw="100.0")],
                curr_rows=[_row("SEE1", kw="100,00")],
            )
            self.assertEqual(list(diffmod.diff(prev, curr)), [])

    def test_none_vs_empty_string_no_false_positive(self):
        with tempfile.TemporaryDirectory() as d:
            prev, curr = self._two_snaps(
                d,
                prev_rows=[_row("SEE1", endg=None)],
                curr_rows=[_row("SEE1", endg="")],
            )
            self.assertEqual(list(diffmod.diff(prev, curr)), [])


class TestRules(unittest.TestCase):
    def _two_snaps(self, d, prev_rows, curr_rows):
        prev = Path(d) / "snap_2026-06-09.sqlite"
        curr = Path(d) / "snap_2026-06-16.sqlite"
        _write_snap(prev, prev_rows)
        _write_snap(curr, curr_rows)
        return prev, curr

    def test_new_solar_unknown_abr_is_t1(self):
        ev = diffmod.DiffEvent("SEE_NEW", "solar", "ABR_FRESH", diffmod.NEW_UNIT)
        idx = rules.PrevIndex(frozenset({"ABR_BESTAND"}))
        self.assertEqual(rules.classify_diff(ev, idx), (rules.T1, False))

    def test_new_solar_known_abr_is_pv_erweiterung(self):
        # §4-Falle 1: Zweit-Einheit an Bestands-ABR ist Ausbau, nicht frische Erst-Anmeldung.
        ev = diffmod.DiffEvent("SEE_NEW", "solar", "ABR_BESTAND", diffmod.NEW_UNIT)
        idx = rules.PrevIndex(frozenset({"ABR_BESTAND"}))
        self.assertEqual(rules.classify_diff(ev, idx), (rules.PV_ERWEITERUNG, False))

    def test_new_storage_at_solar_operator_is_t4_with_flag(self):
        # §4-Falle 3: Retrofit-Meldung lückenhaft -> T4 mit Konfidenz-Flag.
        ev = diffmod.DiffEvent("SSE_NEW", "storage", "ABR_BESTAND", diffmod.NEW_UNIT)
        idx = rules.PrevIndex(frozenset({"ABR_BESTAND"}))
        self.assertEqual(rules.classify_diff(ev, idx), (rules.T4, True))

    def test_new_storage_without_solar_bezug_no_trigger(self):
        ev = diffmod.DiffEvent("SSE_NEW", "storage", "ABR_NURSPEICHER", diffmod.NEW_UNIT)
        idx = rules.PrevIndex(frozenset({"ABR_BESTAND"}))
        self.assertEqual(rules.classify_diff(ev, idx), (None, False))

    def test_abr_change_is_t5_with_konfidenz_flag(self):
        # §4-Falle 2: Betreiberwechsel vs. Umfirmierung nicht trennbar -> T5 + Flag.
        ev = diffmod.DiffEvent("SEE1", "solar", "ABR_NEU", diffmod.FIELD_CHANGED,
                               field="abr", old="ABR_ALT", new="ABR_NEU")
        self.assertEqual(rules.classify_diff(ev), (rules.T5, True))

    def test_stilllegung_leer_to_gesetzt_is_t6(self):
        # §4-Falle 4: nur leer -> gesetzt ist das Repowering-Signal.
        ev = diffmod.DiffEvent("SEE1", "solar", "ABR_A", diffmod.FIELD_CHANGED,
                               field="datum_stilllegung_endg", old=None, new="2026-06-10")
        self.assertEqual(rules.classify_diff(ev), (rules.T6, False))

    def test_stilllegung_gesetzt_to_leer_is_no_t6(self):
        # Wiederaufnahme (gesetzt -> leer) ist KEIN T6.
        ev = diffmod.DiffEvent("SEE1", "solar", "ABR_A", diffmod.FIELD_CHANGED,
                               field="datum_stilllegung_endg", old="2026-01-01", new=None)
        self.assertEqual(rules.classify_diff(ev), (None, False))

    def test_kw_erhoehung_no_trigger_reduzierung_flag(self):
        # §4-Falle 1: Erhöhung = Korrektur (kein Trigger); Reduzierung = Rückbau-Flag.
        up = diffmod.DiffEvent("SEE1", "solar", "ABR_A", diffmod.FIELD_CHANGED,
                               field="brutto_kw", old="100.0", new="150.0")
        self.assertEqual(rules.classify_diff(up), (None, False))
        down = diffmod.DiffEvent("SEE1", "solar", "ABR_A", diffmod.FIELD_CHANGED,
                                 field="brutto_kw", old="150.0", new="100.0")
        self.assertEqual(rules.classify_diff(down), (None, True))

    def test_removed_no_trigger(self):
        ev = diffmod.DiffEvent("SEE_GONE", "solar", "ABR_Z", diffmod.REMOVED)
        self.assertEqual(rules.classify_diff(ev), (None, False))

    def test_end_to_end_diff_plus_rules(self):
        # Voller Pfad: 2 Snapshots -> diff -> classify_diff -> erwartete Trigger.
        with tempfile.TemporaryDirectory() as d:
            prev, curr = self._two_snaps(
                d,
                prev_rows=[
                    _row("SEE1", abr="ABR_ALT"),                       # bekommt abr-Wechsel
                    _row("SEE2", abr="ABR_A", endg=None),              # bekommt Stilllegung
                ],
                curr_rows=[
                    _row("SEE1", abr="ABR_NEU"),                       # T5
                    _row("SEE2", abr="ABR_A", endg="2026-06-12"),      # T6
                    _row("SEE_NEW", traeger="solar", abr="ABR_FRESH"), # T1 (neue ABR)
                    _row("SSE_NEW", traeger="storage", abr="ABR_A"),   # T4 (ABR_A führt Solar)
                ],
            )
            idx = rules.PrevIndex.from_snapshot(prev)
            triggers = {}
            for ev in diffmod.diff(prev, curr):
                trig, flag = rules.classify_diff(ev, idx)
                if trig:
                    triggers[ev.einheit_nr] = (trig, flag)
            self.assertEqual(triggers["SEE1"], (rules.T5, True))
            self.assertEqual(triggers["SEE2"], (rules.T6, False))
            self.assertEqual(triggers["SEE_NEW"], (rules.T1, False))
            self.assertEqual(triggers["SSE_NEW"], (rules.T4, True))


class TestStoreHousekeeping(unittest.TestCase):
    def test_list_and_latest_two_sorted_by_iso_date(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            for datum in ("2026-06-02", "2026-05-26", "2026-06-09"):
                _write_snap(base / f"snap_{datum}.sqlite", [_row("SEE1")])
            (base / "ignored.sqlite").write_text("x")  # Nicht-Snapshot -> ignoriert
            metas = store.list_snapshots(base)
            self.assertEqual([m.datum for m in metas],
                             ["2026-05-26", "2026-06-02", "2026-06-09"])
            prev, curr = store.latest_two(base)
            self.assertEqual(prev.name, "snap_2026-06-02.sqlite")
            self.assertEqual(curr.name, "snap_2026-06-09.sqlite")

    def test_latest_two_needs_at_least_two(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            _write_snap(base / "snap_2026-06-09.sqlite", [_row("SEE1")])
            self.assertIsNone(store.latest_two(base))

    def test_prune_keeps_recent_and_latest_two(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            heute = dt.date(2026, 6, 16)
            data = {
                "2026-01-01": "alt",       # weit außerhalb 8 Wochen -> löschen
                "2026-02-01": "alt",       # außerhalb -> löschen (aber s. latest-two-Schutz)
                "2026-06-01": "frisch",    # innerhalb 8 Wochen -> behalten
                "2026-06-16": "frisch",    # jüngster -> behalten
            }
            for datum in data:
                _write_snap(base / f"snap_{datum}.sqlite", [_row("SEE1")])
            geloescht = store.prune(retention_weeks=8, snapshot_dir=base, heute=heute)
            namen = {p.name for p in geloescht}
            # 2026-01-01 ist alt UND nicht unter den jüngsten zwei -> gelöscht
            self.assertIn("snap_2026-01-01.sqlite", namen)
            uebrig = {m.datum for m in store.list_snapshots(base)}
            self.assertIn("2026-06-01", uebrig)
            self.assertIn("2026-06-16", uebrig)

    def test_prune_never_deletes_latest_two_even_if_old(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            heute = dt.date(2026, 6, 16)
            for datum in ("2026-01-01", "2026-01-08"):   # beide alt, aber die einzigen zwei
                _write_snap(base / f"snap_{datum}.sqlite", [_row("SEE1")])
            geloescht = store.prune(retention_weeks=8, snapshot_dir=base, heute=heute)
            self.assertEqual(geloescht, [])               # latest-two-Schutz greift
            self.assertEqual(len(store.list_snapshots(base)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
