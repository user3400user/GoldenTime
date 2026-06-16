"""Steuer-Schicht: Config-Store (D3) + operativer State (pipeline_state.db, D1/D5/D6).

Von Pipeline UND Admin-Dashboard gelesen. Das Dashboard schreibt NUR in den Config-Store
(Schalter); die Pipeline schreibt Metriken/QA/Ledger in die pipeline_state.db. Kopplung
strikt einseitig (Briefing §6).
"""
from .config_store import ConfigStore, ConfigError, load, save, VALID_TRIGGERS, VALID_MODULES
from . import state

__all__ = [
    "ConfigStore", "ConfigError", "load", "save",
    "VALID_TRIGGERS", "VALID_MODULES", "state",
]
