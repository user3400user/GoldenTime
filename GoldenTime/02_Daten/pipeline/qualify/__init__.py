"""
Komponente 4 — Qualifizierer + Mensch-QA-Gate (Briefing §3/§7.5).

Zwei Stufen auf den SignalRecords aus normalize/from_lead:
  - ``hierarchy.enrich_and_qualify`` — market_actors-Join (Name/PersonenArt liegen NICHT auf der
    Einheit) + pflegbare Ausschluss-Hierarchie (``heuristics/*.txt``) -> additive ``*_PRUEFEN``-Flags.
  - ``qa_gate`` (D5) — nur geflaggte Grenzfälle in die ``qa_decision``-Queue; Entscheidung hält über
    Wochenläufe, Re-Review nur bei Fingerprint-Änderung (load-bearing Felder, NICHT Frische).
"""
from .hierarchy import enrich_and_qualify, personenart_of
from .qa_gate import (
    QA_FLAGS,
    apply_qa,
    approve,
    approve_abr,
    fingerprint,
    list_queue,
    needs_qa,
    reject,
)

__all__ = [
    "enrich_and_qualify",
    "personenart_of",
    "QA_FLAGS",
    "apply_qa",
    "approve",
    "approve_abr",
    "fingerprint",
    "list_queue",
    "needs_qa",
    "reject",
]
