"""
pipeline_state.db (D1 3-DB-Trennung · D5 QA · D6 Ledger · §6 Metriken) — der operative Schreib-State.

GETRENNT von der open-mastr-Export-DB, die je ``build-db`` KOMPLETT neu entsteht (export_adapter.py):
ein QA-/Ledger-/Metrik-Zustand DARIN wäre nach jedem Lauf weg. Hier lebt der dauerhafte State.
WAL-Mode + busy_timeout, damit das Admin-Dashboard nebenläufig LESEN kann, während die Pipeline schreibt
(genau der „1 Schreiber + N Leser"-Fall aus D1 — der eigentliche WAL-Hebel).

Diese Datei besitzt nur Verbindung + Schema. Die Fach-Logik (QA-Fingerprint, Ledger-Reservierung,
Metrik-Aggregation) lebt in qualify/qa_gate.py, ledger/ledger.py bzw. control/metrics.py und nutzt
``state.connect()``.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .. import config

SCHEMA = """
-- D5: Mensch-QA-Gate. Schlüssel = stabiler EinheitMastrNummer -> Entscheidung HÄLT über Wochenläufe.
CREATE TABLE IF NOT EXISTS qa_decision (
  einheit_mastr_nr   TEXT PRIMARY KEY,
  betreiber_mastr_nr TEXT,
  status             TEXT NOT NULL,          -- pending | approved | rejected
  grund              TEXT,                   -- Pflicht bei rejected (z.B. oepnv_ag, energie_firma)
  flags_at_review    TEXT,                   -- '|'-join der Flags zur Review-Zeit (Audit)
  fingerprint        TEXT NOT NULL,          -- Hash der load-bearing Felder -> Re-Review-Trigger
  reviewer           TEXT DEFAULT 'gruender',
  entschieden_am     TEXT,
  notiz              TEXT
);

-- D6: Exklusivitäts-Ledger, Schlüssel pro Funktion × Gebiet × Trigger (Mehrfachverwertung = Konfig).
CREATE TABLE IF NOT EXISTS exclusivity (
  funktion      TEXT NOT NULL,               -- z.B. 'speicher_installateur', 'direktvermarkter'
  gebiet        TEXT NOT NULL,               -- gebiet.id aus dem Config-Store
  trigger       TEXT NOT NULL,               -- T1..T6 / DV_FLAG / PV_ERWEITERUNG
  kaeufer       TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'aktiv',
  reserviert_am TEXT,
  PRIMARY KEY (funktion, gebiet, trigger)    -- 1 Käufer-Funktion hält ein Gebiet×Trigger exklusiv
);

-- Lieferprotokoll (Dedupe: dieselbe Einheit nicht zweimal an denselben Käufer/dieselbe Funktion).
CREATE TABLE IF NOT EXISTS delivery (
  einheit_mastr_nr TEXT NOT NULL,
  kaeufer          TEXT NOT NULL,
  funktion         TEXT NOT NULL,
  gebiet           TEXT,
  trigger          TEXT,
  geliefert_am     TEXT,
  PRIMARY KEY (einheit_mastr_nr, kaeufer, funktion)
);

-- §6 Monitoring: append-only Ereignisse, vom Dashboard aggregiert (Volumen/Frische/Kosten je Dimension).
CREATE TABLE IF NOT EXISTS metrics_event (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  woche       TEXT,                          -- ISO-Woche des Laufs
  gebiet      TEXT,
  trigger     TEXT,
  metrik      TEXT NOT NULL,                 -- z.B. 'signale', 'lieferbar', 'pending_qa', 'frische_median'
  wert        REAL,
  erfasst_am  TEXT
);
CREATE INDEX IF NOT EXISTS ix_metrics_dim ON metrics_event (gebiet, trigger, metrik, woche);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Öffne pipeline_state.db (WAL), lege das Schema bei Bedarf an, gib eine Row-Verbindung zurück."""
    path = Path(db_path or config.PIPELINE_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")      # 1 Schreiber + N Leser (Dashboard) konfliktfrei
    con.execute("PRAGMA busy_timeout=5000")     # Leser wartet statt 'database is locked'
    con.execute("PRAGMA synchronous=NORMAL")    # WAL-sicher, schnellerer Bulk-Insert
    con.execute("PRAGMA foreign_keys=ON")
    init_schema(con)
    return con


def init_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.commit()


def connect_readonly(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Nur-Lese-Verbindung fürs Dashboard (URI ?mode=ro). Fällt auf normal zurück, wenn die DB fehlt."""
    path = Path(db_path or config.PIPELINE_DB_PATH)
    if not path.exists():
        return connect(path)  # legt sie an (leer) statt zu crashen
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=5000")
    return con
