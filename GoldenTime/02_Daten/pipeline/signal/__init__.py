"""Komponente 5 — Signal-Record-Schema: die zentrale Datenstruktur des Vollpakets."""
from .from_lead import from_lead
from .record import (
    SignalRecord,
    compute_konfidenz,
    is_dv_pflichtig,
    mastr_detail_url,
    mastr_einheit_url,
    mastr_suchlink,
)

__all__ = [
    "SignalRecord",
    "from_lead",
    "compute_konfidenz",
    "is_dv_pflichtig",
    "mastr_detail_url",
    "mastr_suchlink",
    "mastr_einheit_url",
]
