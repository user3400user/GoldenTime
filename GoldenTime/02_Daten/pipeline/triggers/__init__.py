"""
Komponente 3 — Trigger (Kaufsignal-Erkenner).

``cohort`` liefert den Stichtags-Trigger T2 (Post-EEG-Jahrgänge + DV-Flag, KEIN Diff). Die
Diff-basierten Trigger (T1/T4 scharf; T5/T6/PV_ERWEITERUNG default-aus) folgen separat in
``diff_based`` und teilen sich das ``base.Trigger``-Protokoll.
"""
from .base import Trigger
from .cohort import TRIGGER_KEY, cohort_signals, dv_flag_count

__all__ = [
    "Trigger",
    "cohort_signals",
    "dv_flag_count",
    "TRIGGER_KEY",
]
