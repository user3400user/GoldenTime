"""
Mensch-QA-Gate (Komponente 4 / Entscheid D5, Briefing §7.5) — Grenzfälle vor die Auslieferung.

Nur **geflaggte** Grenzfälle (``record.flags`` ∩ ``QA_FLAGS``) landen in der Queue; alles andere ist
``auto_ok`` und liefert sofort (die Queue bremst die Demo nicht). Die Entscheidung des Gründers wird in
``qa_decision`` (pipeline_state.db, Key = stabiler EinheitMastrNummer) gespeichert und **hält über
Wochenläufe** — sie wird NUR neu fällig, wenn sich der **Fingerprint** ändert (D5: load-bearing Felder
entity · betreiber_mastr_nr · PersonenArt-Proxy · speicher_status · kWp-Band relativ KWP_MIN/MAX —
bewusst NICHT Frische/Datum, sonst würde jede Re-Registrierung die Entscheidung wegwerfen).

Schreib-Logik (apply_qa) — ein gespeicherter Entscheid hat IMMER Vorrang vor den aktuellen Flags:
  kein Eintrag, needs_qa False                -> 'auto_ok'  (nichts gespeichert)
  kein Eintrag, needs_qa True                 -> 'pending'  (Eintrag angelegt)
  Eintrag, fingerprint GLEICH                 -> gespeicherter status HÄLT ('approved'/'rejected'/'pending'),
                                                 auch wenn die Flags diesmal NICHT feuern (Bug-Hunt-Fix)
  Eintrag, fingerprint ANDERS (load-bearing)  -> invalidieren -> 'pending' (neuer Fingerprint)

Batch-CLI-Aktionen: approve / reject / approve_abr (Sammelaktion je Betreiber) / list_queue.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import sqlite3

from .. import config
from ..signal import SignalRecord
from . import hierarchy

# Welche Flags eine Mensch-QA auslösen. Genau die Grenzfälle der Ausschluss-Hierarchie (hierarchy.py)
# plus das e.K.-/Natürliche-Person-Caveat aus normalize. auto_ok = kein Schnitt mit dieser Menge.
QA_FLAGS = frozenset({
    "NATUERLICHE_PERSON_PRUEFEN",
    "OEFFENTLICH_PRUEFEN",
    "ENERGIE_FIRMA_PRUEFEN",
    "KETTE_PRUEFEN",
    "VEREIN_PRUEFEN",
    "IMMOBILIEN_PRUEFEN",
})

# QA-Status-Werte (Spiegel von SignalRecord.qa_status).
AUTO_OK = "auto_ok"
PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"

# --- Vorschlags-Schicht (read-only, für 'qa suggest') -------------------------------------------
# NUR ein Vorschlag für den Menschen — NICHTS hier entscheidet automatisch. apply_qa/approve/reject
# bleiben die einzigen Schreibpfade. Default-Empfehlung je Flag; bei Flag-Kombination gewinnt die
# RESTRIKTIVSTE (ein Reject-Flag darf NICHT von einem Premium-Approve überstimmt werden — sonst
# rutscht ein geflaggter e.V. mit Premium-Speicher durch).
REC_REJECT = "reject (prüfen)"
REC_PRUEFEN = "prüfen"
REC_APPROVE = "approve (Premium)"

FLAG_EMPFEHLUNG: dict[str, tuple[str, str]] = {
    "VEREIN_PRUEFEN": (REC_REJECT, "verein"),
    "OEFFENTLICH_PRUEFEN": (REC_REJECT, "oeffentlich"),
    "ENERGIE_FIRMA_PRUEFEN": (REC_REJECT, "energie_firma"),
    "IMMOBILIEN_PRUEFEN": (REC_REJECT, "immobilien"),
    "KETTE_PRUEFEN": (REC_REJECT, "kette"),
    "NATUERLICHE_PERSON_PRUEFEN": (REC_PRUEFEN, "natuerliche_person"),
    "PREMIUM_SPEICHER_ANDERER_STANDORT": (REC_APPROVE, "premium_speicher"),
}
_REC_RANG = {REC_REJECT: 0, REC_PRUEFEN: 1, REC_APPROVE: 2}


def parse_flags(flags_at_review: str | None) -> tuple[str, ...]:
    """'|'-jointe ``flags_at_review``-Spalte -> Flag-Tupel. Leer/None -> ()."""
    if not flags_at_review:
        return ()
    return tuple(f for f in flags_at_review.split("|") if f)


def suggest_for_flags(flags_at_review: str | None) -> tuple[str, str]:
    """Reiner Approve/Reject-VORSCHLAG für ein Flag-Muster -> (empfehlung, grund).

    Deterministisch, ohne DB/IO -> direkt testbar. Bei mehreren Flags gewinnt die restriktivste
    Empfehlung (Reject vor Prüfen vor Premium-Approve). Unbekannt/leer -> 'prüfen', NIE ein
    Auto-Approve. ``grund`` ist als CLI-Audit-Grund (``qa reject --grund``) verwendbar.
    """
    treffer = [FLAG_EMPFEHLUNG[f] for f in parse_flags(flags_at_review) if f in FLAG_EMPFEHLUNG]
    if not treffer:
        return (REC_PRUEFEN, "unklar")
    empf = min(treffer, key=lambda t: _REC_RANG[t[0]])[0]
    grund = "+".join(g for e, g in treffer if e == empf)
    return (empf, grund)


def _kwp_band(kwp: float | None) -> str:
    """kWp-Band relativ zur Produkt-Spanne: 'in' (KWP_MIN..KWP_MAX) sonst 'out'.

    Bewusst nur ein 2-Wege-Band (nicht der genaue Wert): kleine kWp-Korrekturen sollen die
    QA-Entscheidung NICHT invalidieren, ein Sprung über die Produktgrenze aber schon.
    """
    if kwp is None:
        return "out"
    return "in" if config.KWP_MIN <= kwp <= config.KWP_MAX else "out"


def fingerprint(record: SignalRecord) -> str:
    """sha1[:16] über die load-bearing Felder (D5) — Re-Review-Trigger bei Änderung.

    Load-bearing (ändert die QA-Bewertung): entity · betreiber_mastr_nr · PersonenArt-Proxy ·
    speicher_status · kWp-Band. NICHT enthalten: Frische/Datum/Konfidenz (volatil, nicht
    entscheidungsrelevant — sonst würde jede Nachregistrierung die Entscheidung wegwerfen).
    """
    teile = (
        (record.entity or "").strip().lower(),
        (record.betreiber_mastr_nr or "").strip(),
        hierarchy.personenart_of(record),         # 'juristisch' | 'natuerlich' | ''
        record.speicher_status or "",
        _kwp_band(record.kwp),
    )
    roh = "\x1f".join(teile)                       # Unit-Separator: kollisionssicher gegen '|' in Namen
    return hashlib.sha1(roh.encode("utf-8")).hexdigest()[:16]


def needs_qa(record: SignalRecord) -> bool:
    """True, wenn der Record mindestens ein QA-auslösendes Flag trägt."""
    return bool(set(record.flags) & QA_FLAGS)


def _heute() -> str:
    return dt.date.today().isoformat()


def apply_qa(record: SignalRecord, con: sqlite3.Connection) -> str:
    """Wende das QA-Gate auf einen Record an, persistiere/lies ``qa_decision`` und setze qa_status.

    Siehe Modul-Docstring für die Statuslogik. Gibt den gesetzten Status zurück (= record.qa_status).
    """
    row = con.execute(
        "SELECT status, fingerprint, flags_at_review FROM qa_decision WHERE einheit_mastr_nr = ?",
        (record.einheit_mastr_nr,),
    ).fetchone()

    if row is None:
        # KEIN gespeicherter Entscheid: nur geflaggte Grenzfälle in die Queue, der Rest ist auto_ok.
        if not needs_qa(record):
            record.qa_status = AUTO_OK
            return AUTO_OK
        fp = fingerprint(record)
        con.execute(
            "INSERT INTO qa_decision "
            "(einheit_mastr_nr, betreiber_mastr_nr, status, flags_at_review, fingerprint, "
            " entschieden_am) VALUES (?,?,?,?,?,?)",
            (record.einheit_mastr_nr, record.betreiber_mastr_nr, PENDING,
             "|".join(record.flags), fp, None),
        )
        con.commit()
        record.qa_status = PENDING
        return PENDING

    # Ein gespeicherter Entscheid HÄLT, bis sich der Fingerprint ändert (D5) — UNABHÄNGIG davon, ob die
    # Flags diesmal feuern (Bug-Hunt-Fix): sonst würde ein abgelehnter Lead wieder ausgeliefert, sobald
    # der market_actors-Namens-Join ausfällt oder ein Heuristik-Muster editiert/entfernt wird.
    fp = fingerprint(record)
    if row["fingerprint"] == fp:
        # G5 (asymmetrisch, KEIN Fingerprint-Eingriff): der Fingerprint deckt Flags bewusst NICHT (D5).
        # Ein zuvor APPROVED Lead, der seit dem Review einen NEUEN QA-Flag bekommen hat (echte Obermenge
        # der QA-Flags zur Review-Zeit — z.B. neu als Verein/öffentlich erkannt), muss zurück in die QA.
        # 'rejected' bleibt 'rejected' (kein Re-Review einer Ablehnung); Flags in fingerprint() zu nehmen
        # würde dagegen einen rejected wieder lieferbar machen (R6, qa_gate.py:159) — darum hier separat.
        if row["status"] == APPROVED:
            alt_qa = set(parse_flags(row["flags_at_review"])) & QA_FLAGS
            neu_qa = set(record.flags) & QA_FLAGS
            if neu_qa > alt_qa:                 # echte Obermenge -> neuer QA-Flag aufgetaucht
                con.execute(
                    "UPDATE qa_decision SET status = ?, flags_at_review = ?, grund = NULL, "
                    "entschieden_am = NULL WHERE einheit_mastr_nr = ?",
                    (PENDING, "|".join(record.flags), record.einheit_mastr_nr),
                )
                con.commit()
                record.qa_status = PENDING
                return PENDING
        record.qa_status = row["status"]
        return row["status"]

    # Load-bearing geändert -> Entscheidung invalidieren, zurück in die Queue (neuer Fingerprint).
    con.execute(
        "UPDATE qa_decision SET status = ?, flags_at_review = ?, fingerprint = ?, "
        "grund = NULL, entschieden_am = NULL WHERE einheit_mastr_nr = ?",
        (PENDING, "|".join(record.flags), fp, record.einheit_mastr_nr),
    )
    con.commit()
    record.qa_status = PENDING
    return PENDING


def _set_status(
    con: sqlite3.Connection, einheit: str, status: str,
    *, grund: str | None = None, notiz: str | None = None, reviewer: str = "gruender",
) -> int:
    """Setze den QA-Status einer bestehenden Queue-Zeile. Gibt die Zahl betroffener Zeilen zurück."""
    cur = con.execute(
        "UPDATE qa_decision SET status = ?, grund = ?, notiz = ?, reviewer = ?, "
        "entschieden_am = ? WHERE einheit_mastr_nr = ?",
        (status, grund, notiz, reviewer, _heute(), einheit),
    )
    con.commit()
    return cur.rowcount


def approve(con: sqlite3.Connection, einheit: str, grund: str | None = None,
            notiz: str | None = None, *, reviewer: str = "gruender") -> int:
    """Einen Grenzfall freigeben ('approved'). Hält fortan, bis sich der Fingerprint ändert."""
    return _set_status(con, einheit, APPROVED, grund=grund, notiz=notiz, reviewer=reviewer)


def reject(con: sqlite3.Connection, einheit: str, grund: str,
           *, notiz: str | None = None, reviewer: str = "gruender") -> int:
    """Einen Grenzfall ablehnen ('rejected'). ``grund`` ist Pflicht (Audit, z.B. 'energie_firma')."""
    if not grund:
        raise ValueError("reject() verlangt einen grund (Audit-Pflicht bei Ablehnung).")
    return _set_status(con, einheit, REJECTED, grund=grund, notiz=notiz, reviewer=reviewer)


def approve_abr(con: sqlite3.Connection, abr: str, grund: str | None = None,
                notiz: str | None = None, *, reviewer: str = "gruender") -> int:
    """Sammelaktion: alle offenen Einheiten EINES Betreibers (ABR) freigeben.

    Praktisch, wenn der Gründer einen Betreiber einmal als 'echtes Gewerbe' erkennt — alle seine
    Einheiten sind dann ok. Gibt die Zahl freigegebener Zeilen zurück.
    """
    cur = con.execute(
        "UPDATE qa_decision SET status = ?, grund = ?, notiz = ?, reviewer = ?, "
        "entschieden_am = ? WHERE betreiber_mastr_nr = ? AND status = ?",
        (APPROVED, grund, notiz, reviewer, _heute(), abr, PENDING),
    )
    con.commit()
    return cur.rowcount


def list_queue(con: sqlite3.Connection, *, status: str | None = PENDING,
               limit: int | None = None) -> list[sqlite3.Row]:
    """Die QA-Queue lesen (Default: offene 'pending'-Fälle), neueste zuerst.

    ``status=None`` liefert alle Stati. Reine Lese-Operation fürs Batch-CLI / Dashboard.
    """
    sql = "SELECT * FROM qa_decision"
    params: list[object] = []
    if status is not None:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY einheit_mastr_nr"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    return list(con.execute(sql, params))
