"""Komponente 5 — Signal-Record-Schema: die zentrale Datenstruktur des Vollpakets."""
from .record import (
    SignalRecord,
    compute_konfidenz,
    is_dv_pflichtig,
    mastr_einheit_url,
)
from .from_lead import from_lead

__all__ = [
    "SignalRecord",
    "from_lead",
    "compute_konfidenz",
    "is_dv_pflichtig",
    "mastr_einheit_url",
]
