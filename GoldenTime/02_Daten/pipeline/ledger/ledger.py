"""
Exklusivitäts-Ledger (K6, D6, Briefing §3) — Reservierung + Lieferprotokoll.

Schlüssel pro **Funktion × Gebiet × Trigger**: ein Käufer hält ein Gebiet×Trigger für eine
Funktion (z.B. 'speicher_installateur') exklusiv. Erzwungen wird die Exklusivität NICHT in
diesem Modul, sondern vom PRIMARY KEY ``(funktion, gebiet, trigger)`` der Tabelle ``exclusivity``
(control/state.py): der zweite Käufer mit gleichem Schlüssel löst eine IntegrityError aus, die
``reserve`` abfängt und als ``False`` zurückgibt. ``reserve`` ist gegenüber dem **gleichen** Käufer
idempotent (gleicher Schlüssel + gleicher Käufer → True, ohne Doppel-Insert).

Das Lieferprotokoll (Tabelle ``delivery``, PK ``(einheit_mastr_nr, kaeufer, funktion)``) entkoppelt
das Dedupe von der Exklusivität: dieselbe Einheit geht nicht zweimal an denselben Käufer/dieselbe
Funktion — unabhängig davon, über welchen Trigger/welches Gebiet sie kam.

Bewusst stdlib-only (sqlite3 + datetime). Kein eigenes Schema, keine Netzwerk-/pip-Abhängigkeit.
Alle Funktionen nehmen eine offene ``state.connect()``-Verbindung (sqlite3.Row) entgegen und
committen ihre Schreibvorgänge selbst.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Any

# Status-Werte der Reservierung (control/state.py: exclusivity.status DEFAULT 'aktiv').
STATUS_AKTIV = "aktiv"


def _heute() -> str:
    """Liefer-/Reservierungsdatum als ISO-Tag (testbar, ohne Zeitzone-Rauschen)."""
    return dt.date.today().isoformat()


def reserve(
    con: sqlite3.Connection,
    funktion: str,
    gebiet: str,
    trigger: str,
    kaeufer: str,
) -> bool:
    """Reserviere Funktion × Gebiet × Trigger exklusiv für ``kaeufer``.

    Rückgabe:
      * ``True``  — neu reserviert, ODER der Schlüssel gehört bereits demselben Käufer (idempotent).
      * ``False`` — der Schlüssel ist bereits an einen ANDEREN Käufer vergeben (IntegrityError
        durch den PRIMARY KEY, hier abgefangen).
    """
    aktueller = owner(con, funktion, gebiet, trigger)
    if aktueller is not None:
        # Schon vergeben: gleicher Käufer → idempotent True, anderer Käufer → blockiert.
        return aktueller == kaeufer
    try:
        con.execute(
            "INSERT INTO exclusivity(funktion, gebiet, trigger, kaeufer, status, reserviert_am) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (funktion, gebiet, trigger, kaeufer, STATUS_AKTIV, _heute()),
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        # Race: zwischen owner()-Check und INSERT hat ein Parallel-Schreiber denselben
        # Schlüssel belegt. PRIMARY KEY schützt — wir geben False statt zu crashen.
        con.rollback()
        return owner(con, funktion, gebiet, trigger) == kaeufer


def owner(
    con: sqlite3.Connection,
    funktion: str,
    gebiet: str,
    trigger: str,
) -> str | None:
    """Aktueller Halter des Schlüssels Funktion × Gebiet × Trigger, oder ``None`` wenn frei."""
    row = con.execute(
        "SELECT kaeufer FROM exclusivity "
        "WHERE funktion = ? AND gebiet = ? AND trigger = ? AND status = ?",
        (funktion, gebiet, trigger, STATUS_AKTIV),
    ).fetchone()
    return row["kaeufer"] if row else None


def is_available(
    con: sqlite3.Connection,
    funktion: str,
    gebiet: str,
    trigger: str,
    kaeufer: str | None = None,
) -> bool:
    """Ist der Schlüssel lieferbar?

    Frei (kein Halter) → ``True``. Ist ``kaeufer`` angegeben, gilt der Schlüssel auch dann als
    verfügbar, wenn er bereits DIESEM Käufer gehört (er darf weiter beliefert werden). Gehört er
    einem anderen Käufer → ``False``.
    """
    halter = owner(con, funktion, gebiet, trigger)
    if halter is None:
        return True
    return kaeufer is not None and halter == kaeufer


def release(
    con: sqlite3.Connection,
    funktion: str,
    gebiet: str,
    trigger: str,
) -> None:
    """Gib den Schlüssel frei (Reservierung löschen) — danach ist er wieder ``is_available``."""
    con.execute(
        "DELETE FROM exclusivity WHERE funktion = ? AND gebiet = ? AND trigger = ?",
        (funktion, gebiet, trigger),
    )
    con.commit()


def record_delivery(
    con: sqlite3.Connection,
    einheit: str,
    kaeufer: str,
    funktion: str,
    gebiet: str | None = None,
    trigger: str | None = None,
) -> None:
    """Protokolliere die Lieferung einer Einheit an einen Käufer für eine Funktion.

    Idempotent über den PRIMARY KEY ``(einheit_mastr_nr, kaeufer, funktion)``: dieselbe Einheit
    wird für denselben Käufer/dieselbe Funktion nur einmal geführt (``INSERT OR IGNORE``, damit
    ein erneuter Lauf nicht crasht). ``gebiet``/``trigger`` sind nur Audit-Kontext.
    """
    con.execute(
        "INSERT OR IGNORE INTO delivery"
        "(einheit_mastr_nr, kaeufer, funktion, gebiet, trigger, geliefert_am) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (einheit, kaeufer, funktion, gebiet, trigger, _heute()),
    )
    con.commit()


def already_delivered(
    con: sqlite3.Connection,
    einheit: str,
    kaeufer: str,
    funktion: str,
) -> bool:
    """Wurde diese Einheit bereits an diesen Käufer für diese Funktion geliefert (Dedupe)?"""
    row = con.execute(
        "SELECT 1 FROM delivery "
        "WHERE einheit_mastr_nr = ? AND kaeufer = ? AND funktion = ?",
        (einheit, kaeufer, funktion),
    ).fetchone()
    return row is not None


def _einheit_of(record: Any) -> str | None:
    """Hole die EinheitMastrNummer aus einem SignalRecord ODER einem Lead-Dict (quell-neutral)."""
    if isinstance(record, dict):
        return record.get("einheit_mastr_nr")
    return getattr(record, "einheit_mastr_nr", None)


def filter_deliverable(
    con: sqlite3.Connection,
    records: list,
    kaeufer: str,
    funktion: str,
    gebiet: str,
    trigger: str,
) -> list:
    """Filtere Records auf das, was diesem Käufer für Funktion × Gebiet × Trigger geliefert werden darf.

    Zwei Gates:
      1. **Exklusivität** — der Schlüssel (funktion × gebiet × trigger) muss frei sein ODER bereits
         diesem Käufer gehören (``is_available``). Gehört er einem anderen Käufer, ist NICHTS
         lieferbar → leere Liste.
      2. **Dedupe** — jede einzelne Einheit, die an diesen Käufer/diese Funktion schon geliefert
         wurde (``already_delivered``), fällt heraus.

    Akzeptiert SignalRecord-Objekte ODER normalize-Lead-Dicts (Zugriff via ``einheit_mastr_nr``).
    Reserviert NICHT selbst — das ist eine bewusste Entscheidung des Aufrufers (reserve()).
    """
    if not is_available(con, funktion, gebiet, trigger, kaeufer):
        return []
    lieferbar = []
    for rec in records:
        einheit = _einheit_of(rec)
        if not einheit:
            continue  # ohne stabilen Schlüssel nicht protokollierbar → nicht lieferbar
        if already_delivered(con, einheit, kaeufer, funktion):
            continue
        lieferbar.append(rec)
    return lieferbar


def overview(con: sqlite3.Connection) -> list[dict]:
    """Dashboard-Sicht: wer hält welches Gebiet × Trigger je Funktion (aktive Reservierungen).

    Sortiert nach Funktion/Gebiet/Trigger für stabile, lesbare Tabellen. Gibt flache Dicts zurück
    (nicht sqlite3.Row), damit das Dashboard sie direkt serialisieren kann.
    """
    rows = con.execute(
        "SELECT funktion, gebiet, trigger, kaeufer, status, reserviert_am "
        "FROM exclusivity WHERE status = ? "
        "ORDER BY funktion, gebiet, trigger",
        (STATUS_AKTIV,),
    ).fetchall()
    return [dict(r) for r in rows]
