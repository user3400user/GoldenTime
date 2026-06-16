"""Komponente 7 — Anreicherungs-Modul (K7): gekapselt, DEFAULT AUS, ein Schalter.

Reichert SignalRecords um Entscheider/Direktkontakt an und vergibt eine Kontakt-Stufe A/B/C.
Scharf erst nach Modul-Schalter (D3 ``anreicherung``) — sonst striktes NO-OP. Phase 1: netzfreier
Stub (kein Scraping); echter Provider (nimble) folgt in P2 gegen dasselbe Protocol.
"""
from .enricher import (
    MODUL_NAME,
    STUFE_A,
    STUFE_B,
    STUFE_C,
    enrich,
)
from .providers import Provider, StubProvider

__all__ = [
    "enrich",
    "Provider",
    "StubProvider",
    "MODUL_NAME",
    "STUFE_A",
    "STUFE_B",
    "STUFE_C",
]
