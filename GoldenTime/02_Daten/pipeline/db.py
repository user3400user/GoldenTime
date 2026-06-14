"""SQLite-Verbindung + tolerante Schema-Auflösung (Tabellen/Spalten case-insensitiv).

Entkoppelt die Query-Logik von der exakten open-mastr-Schreibweise: Tabellen werden über
Kandidatenlisten (config.TABLE_CANDIDATES), Spalten über config.COL aufgelöst. So bricht
die Pipeline nicht, wenn open-mastr eine Spalte anders schreibt — sie meldet stattdessen
klar, was fehlt.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path or config.DEFAULT_DB_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"MaStR-SQLite nicht gefunden: {path}\n"
            f"  -> Export laden:  python -m pipeline.cli build-db\n"
            f"  -> oder MASTR_DB_PATH auf eine vorhandene open-mastr.db setzen.\n"
            f"  -> Demo ohne DB:  python make_sample.py --plz 48,59  (CSV-Fallback)."
        )
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con


def list_tables(con: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]


def table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]


def resolve_table(con: sqlite3.Connection, logical: str) -> str:
    """Realen Tabellennamen zu einem logischen Schlüssel finden (config.TABLE_CANDIDATES)."""
    candidates = config.TABLE_CANDIDATES.get(logical, (logical,))
    existing = {t.lower(): t for t in list_tables(con)}
    for cand in candidates:                      # exakter (case-insensitiver) Treffer zuerst
        if cand.lower() in existing:
            return existing[cand.lower()]
    for cand in candidates:                      # dann Teilstring (z. B. 'solar' in 'solar_extended')
        for low, real in existing.items():
            if cand.lower() in low:
                return real
    raise LookupError(
        f"Keine Tabelle für '{logical}' gefunden (Kandidaten={candidates}). "
        f"Vorhanden: {sorted(existing.values())}. Prüfe `cli.py inspect`."
    )


def resolve_column(columns: list[str], logical: str) -> str | None:
    """Reale Spalte zu einem logischen Feld finden (config.COL), case-insensitiv."""
    candidates = config.COL.get(logical, (logical,))
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def column_map(columns: list[str], *logicals: str) -> dict[str, str | None]:
    """{logischer Name: realer Spaltenname oder None} für mehrere Felder auf einmal."""
    return {lg: resolve_column(columns, lg) for lg in logicals}
