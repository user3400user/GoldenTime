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

import contextlib
import datetime as dt
import os
import shutil
import sqlite3
import tempfile
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
-- betreiber_mastr_nr = ABR -> Basis der Betriebs-Exklusivität (ein Betrieb = ein Käufer je Funktion).
CREATE TABLE IF NOT EXISTS delivery (
  einheit_mastr_nr   TEXT NOT NULL,
  kaeufer            TEXT NOT NULL,
  funktion           TEXT NOT NULL,
  gebiet             TEXT,
  trigger            TEXT,
  betreiber_mastr_nr TEXT,
  geliefert_am       TEXT,
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

-- Evidenz-URL-Cache: SEE-Nummer -> interne MaStR-Detail-ID (Resolver). Spart API-Calls; jede
-- Einheit wird nur einmal aufgelöst, Folgeläufe treffen den Cache.
CREATE TABLE IF NOT EXISTS mastr_url_cache (
  einheit_mastr_nr TEXT PRIMARY KEY,
  detail_id        INTEGER,
  resolved_at      TEXT
);

-- Kundenportal (Loop 3) — Auth + Mandanten. Ein Kunde ist genau EINEM Gebiet × Funktion zugeordnet
-- (Exklusivität); er sieht NUR die Leads seines Gebiets (Mandanten-Trennung). Passwort = scrypt-Hash
-- + per-User-Salt (nie Klartext). Sessions als sha256(Token) gespeichert (DB-Leck enthüllt keine
-- Live-Tokens). Bewusst getrennt vom Admin-Config (Kunde steuert NICHTS, liest nur seine Lieferung).
CREATE TABLE IF NOT EXISTS customer (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  login       TEXT NOT NULL UNIQUE,
  name        TEXT,
  pass_hash   TEXT NOT NULL,
  pass_salt   TEXT NOT NULL,
  gebiet      TEXT NOT NULL,
  funktion    TEXT NOT NULL DEFAULT 'speicher_installateur',
  aktiv       INTEGER NOT NULL DEFAULT 1,
  erstellt_am TEXT
);
CREATE TABLE IF NOT EXISTS portal_session (
  token_hash  TEXT PRIMARY KEY,         -- sha256(raw-token); der Roh-Token lebt nur im Cookie
  customer_id INTEGER NOT NULL,
  csrf        TEXT NOT NULL,            -- per-Session CSRF-Token für state-ändernde POSTs
  erstellt_am TEXT,
  laeuft_ab   TEXT NOT NULL            -- ISO-Zeitstempel; abgelaufene Sessions sind ungültig
);
CREATE INDEX IF NOT EXISTS ix_portal_session_cust ON portal_session (customer_id);
-- Pro Kunde sichtbare Liefer-Leads (Mandanten-Sicht). 'demo'=1 = Sample-/e.K.-gefiltert (kein echter
-- Personendaten-Pfad an einen zahlenden Kunden, §0/I8). Befüllt via CLI (portal seed-demo / publish).
CREATE TABLE IF NOT EXISTS portal_lead (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  gebiet      TEXT NOT NULL,
  see         TEXT NOT NULL,
  entity      TEXT,
  kwp         REAL,
  plz         TEXT,
  ort         TEXT,
  trigger     TEXT,
  datum       TEXT,
  evidenz_url TEXT,
  demo        INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_portal_lead_gebiet ON portal_lead (gebiet);
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
    # Idempotente Migration: betreiber_mastr_nr in delivery (Betriebs-Exklusivität, Loop 0). Für Alt-DBs,
    # deren delivery-Tabelle (CREATE IF NOT EXISTS = no-op) die Spalte noch nicht hat. ALTER schlägt auf
    # frischen DBs (Spalte schon da) mit OperationalError fehl → unterdrückt. DANACH der Betriebs-Index.
    with contextlib.suppress(sqlite3.OperationalError):
        con.execute("ALTER TABLE delivery ADD COLUMN betreiber_mastr_nr TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS ix_delivery_betrieb ON delivery (betreiber_mastr_nr, funktion)")
    con.commit()


def backup_state_db(db_path: Path | str | None = None,
                    backup_dir: Path | str | None = None) -> Path:
    """Konsistente, timestamped Sicherungskopie der NICHT-regenerierbaren pipeline_state.db.

    Aufruf VOR dem ersten echten ``--commit`` (Sprint-Zwang 6): die QA-Entscheide + das Exklusiv-/
    Liefer-Ledger sind nicht aus dem open-mastr-Export wiederherstellbar — ein Verlust zerstört das
    Exklusivitäts-Versprechen unwiederbringlich. Nutzt die sqlite ``.backup``-API (WAL-konsistent,
    auch während Leser offen sind). Gibt den Backup-Pfad zurück; legt ``backups/`` bei Bedarf an.
    """
    src_path = Path(db_path or config.PIPELINE_DB_PATH)
    bdir = Path(backup_dir) if backup_dir else src_path.parent / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    dest = bdir / f"pipeline_state_{stamp}.db"
    # Read-only-Quelle, falls vorhanden (sonst leere DB anlegen → leeres, valides Backup).
    if src_path.exists():
        src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    else:
        src = sqlite3.connect(str(src_path))
    dst = sqlite3.connect(str(dest))
    try:
        with dst:
            src.backup(dst)
    finally:
        src.close()
        dst.close()
    return dest


# Kern-Tabellen, deren Vorhandensein ein gültiges State-Backup ausmacht (Restore-Validierung).
_KERN_TABELLEN = ("qa_decision", "exclusivity", "delivery", "metrics_event")


def list_backups(backup_dir: Path | str | None = None) -> list[Path]:
    """Vorhandene State-Backups, **neueste zuerst** (Dateiname trägt den Timestamp → lexikografisch = chronologisch)."""
    bdir = Path(backup_dir) if backup_dir else Path(config.PIPELINE_DB_PATH).parent / "backups"
    if not bdir.exists():
        return []
    return sorted(bdir.glob("pipeline_state_*.db"), reverse=True)


def _validate_backup(path: Path) -> None:
    """Wirf, wenn das Backup keine lesbare SQLite mit den Kern-Tabellen ist (vor dem Überschreiben der Live-DB)."""
    if not path.exists():
        raise FileNotFoundError(f"Backup nicht gefunden: {path}")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        namen = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        con.close()
    fehlt = [t for t in _KERN_TABELLEN if t not in namen]
    if fehlt:
        raise ValueError(f"Backup {path} unvollständig — fehlende Kern-Tabellen: {fehlt}")


def restore_state_db(backup_path: Path | str,
                     db_path: Path | str | None = None) -> Path:
    """Stelle pipeline_state.db aus einem Backup wieder her — **atomar + validiert** (DoD §9.5).

    Schritte: (1) Backup validieren (lesbare SQLite mit den Kern-Tabellen — NIE eine kaputte Datei über
    die Live-DB legen). (2) Kopie per ``tempfile`` im Zielverzeichnis (gleiches FS) → ``os.replace``
    (atomar). (3) Stale WAL/SHM-Sidecars der ALTEN DB entfernen (sonst schattet ein alter WAL die
    restaurierte DB). Recovery-Operation — die DB darf dabei nicht aktiv beschrieben werden.
    """
    backup_path = Path(backup_path)
    _validate_backup(backup_path)
    dest = Path(db_path or config.PIPELINE_DB_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), prefix=".restore_", suffix=".db")
    os.close(fd)
    try:
        shutil.copyfile(backup_path, tmp)
        os.replace(tmp, dest)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise
    for sidecar in (dest.with_name(dest.name + "-wal"), dest.with_name(dest.name + "-shm")):
        with contextlib.suppress(FileNotFoundError):
            sidecar.unlink()
    return dest


def qa_pending(con: sqlite3.Connection, limit: int = 100) -> list:
    """Offene QA-Queue (pending-Grenzfälle) lesen — Control-Layer-Read fürs Dashboard.

    Bewusst hier (control), NICHT über qualify.qa_gate: das Dashboard importiert KEINE Pipeline-Logik
    (Briefing §6, einseitige Kopplung). Reine Lese-Operation auf der qa_decision-Tabelle.
    """
    return list(con.execute(
        "SELECT einheit_mastr_nr, betreiber_mastr_nr, flags_at_review, status, entschieden_am "
        "FROM qa_decision WHERE status = 'pending' ORDER BY einheit_mastr_nr LIMIT ?", (int(limit),)))


def connect_readonly(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Nur-Lese-Verbindung fürs Dashboard (URI ?mode=ro). Fällt auf normal zurück, wenn die DB fehlt."""
    path = Path(db_path or config.PIPELINE_DB_PATH)
    if not path.exists():
        return connect(path)  # legt sie an (leer) statt zu crashen
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=5000")
    return con
