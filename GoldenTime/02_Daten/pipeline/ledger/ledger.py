"""
Exklusivitäts-Ledger (K6, D6, Briefing §3) — Reservierung + Lieferprotokoll + Betriebs-Exklusivität.

**Drei Schutz-Ebenen** (Loop 0 „G0", refute-gehärtet):
1. **Gebiets-Reservierung** (``exclusivity``, PK ``funktion × gebiet × trigger``): ein Käufer hält ein
   Gebiet×Trigger für eine Funktion exklusiv. Der zweite Käufer mit gleichem Schlüssel löst eine
   IntegrityError aus, die ``reserve`` als ``False`` zurückgibt.
2. **Einheiten-Dedupe** (``delivery``, PK ``einheit × kaeufer × funktion``): dieselbe Einheit geht nicht
   zweimal an denselben Käufer/dieselbe Funktion.
3. **Betriebs-Exklusivität** (``betrieb_fremd_vergeben``): ein BETRIEB (Anlagenbetreiber/ABR = der
   angerufene Entscheider) gehört für eine Funktion **genau EINEM** Käufer — **gebiets- UND
   trigger-übergreifend**. Schliesst das Versprechen-vs-Schloss-Leck (Refute, CRITICAL+HIGH): derselbe
   Betrieb mit Anlagen in zwei Gebieten (real 423 ABR in PLZ 48/59 ∩ 49) ginge sonst an zwei „exklusive"
   Käufer; und derselbe Lead könnte über einen anderen TRIGGER an einen zweiten Käufer (Dedupe ist
   trigger-agnostisch, Reservierung trigger-spezifisch). Beides fängt die Betriebs-Ebene.

**Schlüssel-Normalisierung:** ``funktion`` wird kanonisiert (casefold + snake_case), damit
'Speicher-Installateur' / 'speicher_installateur' DENSELBEN Ledger-Schlüssel ergeben (sonst dedupt das
Ledger byte-genau und derselbe Lead ginge doppelt raus — Refute MEDIUM). ``kaeufer`` wird getrimmt.

Bewusst stdlib-only (sqlite3 + datetime + re). Alle Funktionen nehmen eine offene ``state.connect()``-
Verbindung (sqlite3.Row) entgegen und committen ihre Schreibvorgänge selbst.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import re
import sqlite3
from typing import Any

# Status-Werte der Reservierung (control/state.py: exclusivity.status DEFAULT 'aktiv').
STATUS_AKTIV = "aktiv"


def _heute() -> str:
    """Liefer-/Reservierungsdatum als ISO-Tag (testbar, ohne Zeitzone-Rauschen)."""
    return dt.date.today().isoformat()


def _nf(funktion: str) -> str:
    """Kanonische Funktions-Form (casefold + Whitespace/Bindestrich → Unterstrich), damit der
    Ledger-Schlüssel nicht an der Schreibweise eines getippten Strings hängt."""
    return re.sub(r"[\s\-]+", "_", (funktion or "").strip().casefold())


def _ck(kaeufer: str) -> str:
    """Käufer-Schlüssel normalisieren (trimmen; Anzeige-Casing bleibt erhalten)."""
    return (kaeufer or "").strip()


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
    funktion, kaeufer = _nf(funktion), _ck(kaeufer)
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
        (_nf(funktion), gebiet, trigger, STATUS_AKTIV),
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
    return kaeufer is not None and halter == _ck(kaeufer)


def release(
    con: sqlite3.Connection,
    funktion: str,
    gebiet: str,
    trigger: str,
) -> None:
    """Gib den Schlüssel frei (Reservierung löschen) — danach ist er wieder ``is_available``."""
    con.execute(
        "DELETE FROM exclusivity WHERE funktion = ? AND gebiet = ? AND trigger = ?",
        (_nf(funktion), gebiet, trigger),
    )
    con.commit()


def record_delivery(
    con: sqlite3.Connection,
    einheit: str,
    kaeufer: str,
    funktion: str,
    gebiet: str | None = None,
    trigger: str | None = None,
    betreiber: str | None = None,
) -> None:
    """Protokolliere die Lieferung einer Einheit an einen Käufer für eine Funktion.

    Idempotent über den PRIMARY KEY ``(einheit_mastr_nr, kaeufer, funktion)`` (``INSERT OR IGNORE``).
    ``betreiber`` (ABR) wird mitgeschrieben — Basis der Betriebs-Exklusivität; ``gebiet``/``trigger``
    sind Audit-Kontext.
    """
    con.execute(
        "INSERT OR IGNORE INTO delivery"
        "(einheit_mastr_nr, kaeufer, funktion, gebiet, trigger, betreiber_mastr_nr, geliefert_am) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        (einheit, _ck(kaeufer), _nf(funktion), gebiet, trigger, betreiber, _heute()),
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
        (einheit, _ck(kaeufer), _nf(funktion)),
    ).fetchone()
    return row is not None


def betrieb_fremd_vergeben(
    con: sqlite3.Connection,
    betreiber: str | None,
    funktion: str,
    kaeufer: str,
) -> bool:
    """Gehört der BETRIEB (ABR) bereits einem ANDEREN Käufer für diese Funktion?

    Gebiets- UND trigger-übergreifend: sobald ein Betrieb an Käufer A geliefert wurde, ist er für
    jeden anderen Käufer derselben Funktion gesperrt — egal über welches Gebiet/welchen Trigger.
    Ohne ``betreiber`` (kein stabiler ABR) → ``False`` (nicht entscheidbar, nicht sperren).
    """
    if not betreiber:
        return False
    row = con.execute(
        "SELECT 1 FROM delivery WHERE betreiber_mastr_nr = ? AND funktion = ? AND kaeufer <> ? LIMIT 1",
        (betreiber, _nf(funktion), _ck(kaeufer)),
    ).fetchone()
    return row is not None


def _einheit_of(record: Any) -> str | None:
    """Hole die EinheitMastrNummer aus einem SignalRecord ODER einem Lead-Dict (quell-neutral)."""
    if isinstance(record, dict):
        return record.get("einheit_mastr_nr")
    return getattr(record, "einheit_mastr_nr", None)


def _betreiber_of(record: Any) -> str | None:
    """Hole die AnlagenbetreiberMastrNummer (ABR) aus einem SignalRecord ODER Lead-Dict."""
    if isinstance(record, dict):
        return record.get("betreiber_mastr_nr")
    return getattr(record, "betreiber_mastr_nr", None)


def filter_deliverable(
    con: sqlite3.Connection,
    records: list,
    kaeufer: str,
    funktion: str,
    gebiet: str,
    trigger: str,
) -> list:
    """Filtere Records auf das, was diesem Käufer geliefert werden darf (READ-ONLY Vorschau).

    Drei Gates (in dieser Reihenfolge):
      1. **Gebiets-Exklusivität** — gehört ``funktion × gebiet × trigger`` einem anderen Käufer
         (``is_available`` False), ist NICHTS lieferbar → ``[]``.
      2. **Einheiten-Dedupe** — schon an diesen Käufer/diese Funktion gelieferte Einheiten raus.
      3. **Betriebs-Exklusivität** — Einheiten, deren Betrieb (ABR) bereits einem ANDEREN Käufer
         derselben Funktion gehört (gebiets-/trigger-übergreifend), fallen raus.

    Akzeptiert SignalRecord-Objekte ODER normalize-Lead-Dicts. Reserviert NICHT selbst.
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
        if betrieb_fremd_vergeben(con, _betreiber_of(rec), funktion, kaeufer):
            continue  # Betrieb gehört schon einem anderen Käufer (Betriebs-Exklusivität)
        lieferbar.append(rec)
    return lieferbar


def commit_delivery(
    con: sqlite3.Connection,
    records: list,
    kaeufer: str,
    funktion: str,
    gebiet: str,
    trigger: str,
) -> list:
    """ATOMAR (``BEGIN IMMEDIATE``): Exklusivität reservieren + Dedupe + Lieferung protokollieren.

    Der EINZIGE schreibende Liefer-Pfad (G0 verdrahtet). In EINER Transaktion: Gebiets-Exklusivität
    prüfen → reservieren (idempotent) → je Einheit Dedupe + Betriebs-Exklusivität → ``delivery``-Insert.
    Rückgabe: die Liste der in DIESEM Lauf NEU protokollierten Records. Zweiter Lauf an denselben
    (kaeufer, funktion) → ``[]`` (Dedupe). Ein Betrieb, der schon einem anderen Käufer gehört, fällt raus.

    ``BEGIN IMMEDIATE`` nimmt sofort die Write-Lock → zwei quasi-gleichzeitige ``--commit`` können nicht
    zwei Reservierungen erzeugen. Scheitert die Lock-Akquise (``database is locked`` nach busy_timeout),
    propagiert die ECHTE Fehlermeldung (kein maskierendes ROLLBACK auf eine nie geöffnete Transaktion).
    Aufrufer MUSS vorher sichergestellt haben, dass eine ECHTE Lieferung erlaubt ist
    (``config.LIVE_DELIVERY_ENABLED`` — Demo/Dry-Run kommt hier NIE an).
    """
    fn, kf = _nf(funktion), _ck(kaeufer)
    con.commit()                          # evtl. offene implizite Transaktion schließen (BEGIN-sicher)
    prev_iso = con.isolation_level
    con.isolation_level = None            # manuelle Transaktionskontrolle (BEGIN/COMMIT explizit)
    in_txn = False
    try:
        con.execute("BEGIN IMMEDIATE")    # ab hier ist eine Transaktion offen
        in_txn = True
        if not is_available(con, fn, gebiet, trigger, kf):
            con.execute("ROLLBACK")
            in_txn = False
            return []
        if owner(con, fn, gebiet, trigger) is None:
            con.execute(
                "INSERT INTO exclusivity(funktion, gebiet, trigger, kaeufer, status, reserviert_am) "
                "VALUES(?, ?, ?, ?, ?, ?)",
                (fn, gebiet, trigger, kf, STATUS_AKTIV, _heute()),
            )
        neu = []
        for rec in records:
            einheit = _einheit_of(rec)
            if not einheit:
                continue                  # ohne stabilen Schlüssel nicht protokollierbar
            if already_delivered(con, einheit, kf, fn):
                continue                  # Dedupe: schon an diesen Käufer/diese Funktion geliefert
            betreiber = _betreiber_of(rec)
            if betrieb_fremd_vergeben(con, betreiber, fn, kf):
                continue                  # Betriebs-Exklusivität: Betrieb gehört anderem Käufer
            con.execute(
                "INSERT OR IGNORE INTO delivery"
                "(einheit_mastr_nr, kaeufer, funktion, gebiet, trigger, betreiber_mastr_nr, geliefert_am) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (einheit, kf, fn, gebiet, trigger, betreiber, _heute()),
            )
            neu.append(rec)
        con.execute("COMMIT")
        in_txn = False
        return neu
    except BaseException:
        # ROLLBACK nur, wenn wirklich eine Transaktion offen ist — sonst würde 'cannot rollback - no
        # transaction is active' die echte Ursache (z.B. 'database is locked') maskieren (Refute MEDIUM).
        if in_txn:
            with contextlib.suppress(sqlite3.OperationalError):
                con.execute("ROLLBACK")
        raise
    finally:
        con.isolation_level = prev_iso


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
