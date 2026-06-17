"""
Snapshot-Speicher (D2) — schreibt je Lauf einen schlanken, dated SQLite-Auszug.

Aus der open-mastr-Arbeits-DB werden GENAU die 7 Diff-Schlüsselfelder je relevanter
Träger-Tabelle (solar, storage; generisch erweiterbar) in EINE Tabelle ``snapshot``
geschrieben — datiert als ``snap_<YYYY-MM-DD>.sqlite`` im ``config.SNAPSHOT_DIR``.

Warum schlank: open-mastr baut die ~8-GB-Export-DB je build-db KOMPLETT neu. Würden wir
die ganze DB versionieren, wären das pro Woche mehrere GB. Der Diff braucht aber nur die
Felder, an denen ein Buy-Signal hängt (Briefing §4): Existenz der Einheit (NEW_UNIT/REMOVED),
ABR (T5-Betreiberwechsel), Bruttoleistung (Reduzierung), Inbetriebnahme und die beiden
Stilllegungs-Daten (T6). Die ``einheit_nr`` ist PRIMARY KEY — der Diff ist ein Set-Diff.

stdlib-only (sqlite3). Schema-Auflösung über db.resolve_table/resolve_column, damit
unterschiedliche open-mastr-Schreibweisen (Casing) den Snapshot nicht brechen.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import re
import sqlite3
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .. import config
from .. import db as dbmod

log = logging.getLogger(__name__)

# Dateinamens-Muster: snap_<ISO-Datum>.sqlite. Datum steckt im Namen, damit list/latest
# allein über den Dateinamen sortieren können (keine DB je Snapshot öffnen müssen).
_SNAP_GLOB = "snap_*.sqlite"
_SNAP_NAME_RE = re.compile(r"^snap_(\d{4}-\d{2}-\d{2})\.sqlite$")

# Die 7 Diff-Schlüsselfelder (D2). Reihenfolge = Spaltenreihenfolge der snapshot-Tabelle.
# einheit_nr ist PRIMARY KEY; brutto_kw als REAL (Float-toleranter Vergleich im Diff).
SNAPSHOT_FIELDS: tuple[str, ...] = (
    "einheit_nr",
    "traeger",
    "abr",
    "eeg_nr",
    "brutto_kw",
    "inbetriebnahme",
    "datum_stilllegung_endg",
    "datum_stilllegung_vorueb",
    "betriebsstatus",
)

# Welche logische config.COL-Spalte je snapshot-Feld aus der Träger-Tabelle gelesen wird.
# 'traeger' ist kein DB-Feld, sondern die Herkunfts-Tabelle (solar|storage) — pro Zeile gesetzt.
_FIELD_TO_LOGICAL: dict[str, str] = {
    "einheit_nr": "einheit_nr",
    "abr": "abr",
    "eeg_nr": "eeg_nr",
    "brutto_kw": "brutto_kw",
    "inbetriebnahme": "inbetriebnahme",
    "datum_stilllegung_endg": "stilllegung_endg",
    "datum_stilllegung_vorueb": "stilllegung_vorueb",
    "betriebsstatus": "betriebsstatus",
}

# Generisch erweiterbar: weitere Träger (wind/biomass) hier ergänzen — der Rest ist
# schema-aufgelöst und bleibt unverändert. solar/storage decken den B-Backbone ab.
_TRAEGER: tuple[str, ...] = ("solar", "storage")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS snapshot (
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


@dataclass(frozen=True)
class SnapshotMeta:
    """Ein vorhandener Snapshot: Pfad + aus dem Dateinamen geparstes ISO-Datum."""

    path: Path
    datum: str          # 'YYYY-MM-DD'


def _to_float(v: object) -> float | None:
    """kWp tolerant nach float (deutsches Dezimalkomma erlaubt) — None bleibt None."""
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _resolve_stand_datum(con: sqlite3.Connection, datum: str | None) -> str:
    """Snapshot-Datum = explizit übergeben, sonst echter Export-Stand, sonst date.today().

    open-mastr legt keine Stand-/Meta-Tabelle ab — aber ``MAX(DatumLetzteAktualisierung)`` über die
    Träger-Tabellen ist der reale Datenstand (verlässlicher als der Wandkalender-Lauftag für die
    Retention/Wochen-Zuordnung des Diffs). date.today() nur, wenn auch das fehlt.
    """
    if datum:
        return str(datum)[:10]
    try:
        for traeger in _TRAEGER:
            table = dbmod.resolve_table(con, traeger)
            col = dbmod.resolve_column(dbmod.table_columns(con, table), "letzte_aktual")
            if col:
                row = con.execute(f'SELECT MAX("{col}") FROM "{table}"').fetchone()
                if row and row[0]:
                    return str(row[0])[:10]
    except Exception:   # robust: Stand-Ermittlung darf den Snapshot nie verhindern
        pass
    return dt.date.today().isoformat()


def _read_traeger_rows(con: sqlite3.Connection, traeger: str) -> Iterator[tuple]:
    """Lese die Diff-Schlüsselfelder einer Träger-Tabelle als (Feld-Reihenfolge)-Tupel.

    Schema-tolerant: fehlt eine optionale Spalte (z. B. eeg_nr auf storage), wird im
    SELECT ein NULL-Literal eingesetzt. einheit_nr ist Pflicht — fehlt sie, wird der
    Träger mit Warnung übersprungen (statt den ganzen Snapshot zu brechen).
    """
    table = dbmod.resolve_table(con, traeger)
    cols = dbmod.table_columns(con, table)

    select_parts: list[str] = []
    for fld in SNAPSHOT_FIELDS:
        if fld == "traeger":
            continue
        logical = _FIELD_TO_LOGICAL[fld]
        real = dbmod.resolve_column(cols, logical)
        if real:
            select_parts.append(f'"{real}" AS {fld}')
        else:
            select_parts.append(f"NULL AS {fld}")

    einheit_real = dbmod.resolve_column(cols, "einheit_nr")
    if not einheit_real:
        log.warning("Träger '%s' (Tabelle '%s') ohne EinheitMastrNummer — übersprungen.",
                    traeger, table)
        return

    sql = "SELECT " + ", ".join(select_parts) + f' FROM "{table}"'
    for row in con.execute(sql):
        d = dict(row)
        einheit = d.get("einheit_nr")
        if not einheit:                       # ohne PK keine Diff-Identität -> raus
            continue
        yield (
            einheit,
            traeger,                          # Herkunfts-Träger (kein DB-Feld)
            d.get("abr"),
            d.get("eeg_nr"),
            _to_float(d.get("brutto_kw")),
            d.get("inbetriebnahme"),
            d.get("datum_stilllegung_endg"),
            d.get("datum_stilllegung_vorueb"),
            d.get("betriebsstatus"),
        )


def write_snapshot(
    con: sqlite3.Connection,
    out_path: Path | str | None = None,
    datum: str | None = None,
    *,
    traeger: tuple[str, ...] = _TRAEGER,
) -> Path:
    """Schreibe einen schlanken, dated Snapshot der 7 Diff-Schlüsselfelder.

    ``con``: offene open-mastr-Arbeits-DB (Quelle). ``out_path``: Zielpfad; default
    ``config.SNAPSHOT_DIR/snap_<datum>.sqlite``. ``datum``: open-mastr-Stand (ISO);
    Fallback ``date.today()``. Gibt den geschriebenen Pfad zurück.

    Eine einzige ``einheit_nr`` ist PRIMARY KEY: kollidieren Träger auf derselben Nummer
    (in der Praxis nicht — solar/storage sind disjunkte EinheitMastrNummern), gewinnt der
    zuletzt geschriebene Träger (INSERT OR REPLACE), damit der Lauf nicht abbricht.
    """
    con.row_factory = sqlite3.Row     # defensiv: _read_traeger_rows nutzt dict(row) (auch bei Plain-Con)
    stand = _resolve_stand_datum(con, datum)
    if out_path is None:
        config.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        out = config.SNAPSHOT_DIR / f"snap_{stand}.sqlite"
    else:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

    # Atomar schreiben (Opt-Hunt/BUG): erst in eine Temp-Datei im selben Verzeichnis, dann os.replace.
    # Ein Teil-Abbruch (I/O-Fehler, OOM, Laptop-Sleep, Ctrl-C) lässt die alte Baseline UNANGETASTET,
    # statt sie via vorab-unlink + in-place-Schreiben zu zerstören (sonst: Diff gegen leeren Snapshot).
    placeholders = ", ".join("?" for _ in SNAPSHOT_FIELDS)
    insert_sql = (f"INSERT OR REPLACE INTO snapshot ({', '.join(SNAPSHOT_FIELDS)}) "
                  f"VALUES ({placeholders})")
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(out.parent), prefix=out.name + ".", suffix=".tmp")
    os.close(tmp_fd)
    tmp = Path(tmp_name)
    snap = sqlite3.connect(str(tmp))
    try:
        snap.execute(_CREATE_SQL)
        total = 0
        for t in traeger:
            n_before = snap.total_changes
            # _read_traeger_rows ist ein Generator -> executemany streamt (keine 6,2-Mio-Zeilen-Liste
            # mit ~2,5 GB Peak im RAM, Opt-Hunt). total_changes zählt die Inserts (Träger disjunkt).
            snap.executemany(insert_sql, _read_traeger_rows(con, t))
            total += snap.total_changes - n_before
        snap.commit()
    except BaseException:                      # auch KeyboardInterrupt -> Teil-Snapshot wegwerfen
        snap.close()
        tmp.unlink(missing_ok=True)
        raise
    snap.close()
    os.replace(str(tmp), str(out))             # atomar an die finale Stelle (alte Baseline ersetzt)
    log.info("Snapshot %s geschrieben: %d Einheiten (Träger=%s).",
             out.name, total, ",".join(traeger))
    return out


def list_snapshots(snapshot_dir: Path | str | None = None) -> list[SnapshotMeta]:
    """Alle vorhandenen Snapshots, aufsteigend nach ISO-Datum im Dateinamen sortiert."""
    base = Path(snapshot_dir or config.SNAPSHOT_DIR)
    if not base.exists():
        return []
    metas: list[SnapshotMeta] = []
    for p in base.glob(_SNAP_GLOB):
        m = _SNAP_NAME_RE.match(p.name)
        if m:
            metas.append(SnapshotMeta(path=p, datum=m.group(1)))
    metas.sort(key=lambda s: s.datum)
    return metas


def latest_two(snapshot_dir: Path | str | None = None) -> tuple[Path, Path] | None:
    """Die zwei jüngsten Snapshots (prev, curr) für den Wochen-Diff.

    Gibt ``(prev_path, curr_path)`` zurück oder ``None``, wenn weniger als zwei
    Snapshots existieren (Diff braucht >=2).
    """
    metas = list_snapshots(snapshot_dir)
    if len(metas) < 2:
        return None
    return metas[-2].path, metas[-1].path


def prune(
    retention_weeks: int = config.SNAPSHOT_RETENTION_WEEKS,
    snapshot_dir: Path | str | None = None,
    *,
    heute: dt.date | None = None,
) -> list[Path]:
    """Lösche Snapshots älter als ``retention_weeks`` Wochen. Gibt gelöschte Pfade zurück.

    Simpel und Anker-fähig gedacht: die jüngsten beiden Snapshots bleiben IMMER erhalten
    (der Diff braucht >=2), egal wie alt — sonst könnte ein langer Lauf-Aussetzer die
    Diff-Basis wegräumen. Monatliche Langzeit-Anker (config.SNAPSHOT_ANKER_MONATE) sind
    hier bewusst noch nicht implementiert (YAGNI bis T5/T6 scharf sind) — der Hook
    (Datum im Dateinamen) ist da.
    """
    heute = heute or dt.date.today()
    grenze = heute - dt.timedelta(weeks=retention_weeks)
    metas = list_snapshots(snapshot_dir)
    behalten_immer = {m.path for m in metas[-2:]}     # jüngste zwei nie löschen

    geloescht: list[Path] = []
    for m in metas:
        if m.path in behalten_immer:
            continue
        try:
            snap_datum = dt.date.fromisoformat(m.datum)
        except ValueError:
            continue
        if snap_datum < grenze:
            m.path.unlink()
            geloescht.append(m.path)
            log.info("Snapshot %s gelöscht (älter als %d Wochen).", m.path.name, retention_weeks)
    return geloescht
