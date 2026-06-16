"""
Trigger-Protokoll (Komponente 3) — gemeinsames Interface für alle Kaufsignal-Trigger.

Hält den Vertrag minimal: ein Trigger trägt einen ``key`` (T1/T2/… aus dem Config-Store)
und eine ``evaluate``-Methode, die je Treffer einen ``SignalRecord`` ausgibt. Bewusst
``@runtime_checkable``, damit der Orchestrator (CLI/Pipeline) per ``isinstance`` prüfen kann,
ohne von einer Basisklasse zu erben — die Trigger sind freie Funktionen mit dünnem Adapter.

Diese Datei ist der Platzhalter für die spätere ``diff_based``-Familie (T1/T4 scharf;
T5/T6/PV_ERWEITERUNG default-aus, Briefing K3): die kennen zusätzlich einen Snapshot-Diff.
Der Cohort-Trigger (T2 Post-EEG) braucht KEINEN Diff (reine Stichtags-Kohorte über das
EEG-Inbetriebnahmejahr) und wird darum als freie Funktion in ``cohort.py`` ausgeliefert.
"""
from __future__ import annotations

import sqlite3
from typing import Iterator, Protocol, runtime_checkable

from ..signal import SignalRecord
from ..speicher_check import StorageIndex


@runtime_checkable
class Trigger(Protocol):
    """Vertrag eines Kaufsignal-Triggers (Briefing K3).

    Implementierungen sind quell-neutral: sie kennen nur die (bereits aufgelöste) DB-Verbindung
    und den vorberechneten Speicher-Index, NICHT die open-mastr-Schreibweise (das löst ``db``).
    """

    #: Trigger-Schlüssel aus dem Config-Store (z. B. ``"T2"``); steuert is_trigger_enabled.
    key: str

    def evaluate(
        self,
        con: sqlite3.Connection,
        index: StorageIndex,
        **kwargs: object,
    ) -> Iterator[SignalRecord]:
        """Liefere die Kaufsignale dieses Triggers als ``SignalRecord``-Strom.

        ``kwargs`` sind trigger-spezifisch (Cohort: plz_prefixes/kwp_min/kwp_max/jahrgaenge/
        region; diff_based später zusätzlich: ``snapshot_diff``). Implementierungen MÜSSEN
        co-lokal belegte Einheiten (Speicher am Standort) ausschließen — der Bedarf ist dort
        bereits gedeckt (Lead-Spec §2 Regel 8).
        """
        ...
