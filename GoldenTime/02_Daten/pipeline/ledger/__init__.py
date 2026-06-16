"""Komponente 6 — Exklusivitäts-Ledger (K6, D6).

Reserviert je **Funktion × Gebiet × Trigger** exklusiv für genau einen Käufer (Mehrfach-
verwertung = Konfiguration, nicht Default) und führt das Lieferprotokoll (Dedupe: dieselbe
Einheit nicht zweimal an denselben Käufer/dieselbe Funktion). Nutzt ausschliesslich die Tabellen
``exclusivity`` + ``delivery`` aus ``control/state.py`` — KEIN eigenes Schema.
"""
from .ledger import (
    already_delivered,
    filter_deliverable,
    is_available,
    overview,
    owner,
    record_delivery,
    release,
    reserve,
)

__all__ = [
    "reserve",
    "owner",
    "is_available",
    "release",
    "record_delivery",
    "already_delivered",
    "filter_deliverable",
    "overview",
]
