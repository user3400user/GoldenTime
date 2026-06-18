"""
Snapshot+Diff-Engine (Komponente 2, D2 — Kern-IP, Briefing §3/§4).

Versionierte „Skinny"-Snapshots der MaStR-Arbeits-DB + Set-/Feld-Diff zwischen zwei
Läufen. Der Diff ist die einzige Quelle der zeitlichen Trigger (T1/T4/T5/T6/PV_ERWEITERUNG):
open-mastr baut die Export-DB je Lauf KOMPLETT neu — ohne eigenen, dated Snapshot ginge
jede „was ist seit letzter Woche neu/anders?"-Information verloren.

Bewusst stdlib-only (sqlite3 + gzip-fähig über kleine Dateien): je Lauf wird NUR ein
schlanker Auszug der 7 Diff-Schlüsselfelder als ``snap_<datum>.sqlite`` abgelegt, nicht die
8-GB-Export-DB. Der Diff arbeitet über ``einheit_nr`` (PRIMARY KEY) als Set-Diff plus
Feldvergleich; ``rules`` klassifiziert die Diff-Events nach Briefing §4 in Trigger.

Module:
  store   — write_snapshot / list_snapshots / latest_two / prune (dated SQLite-Auszug)
  diff    — DiffEvent + diff(prev, curr): NEW_UNIT / REMOVED / FIELD_CHANGED
  rules   — classify_diff(ev, prev_index): Diff-Event -> (Trigger | None, Konfidenz-Flag)

Geschäftskontext: 01_Strategie/STATE.md. Technik: ../../CLAUDE.md.
"""
from __future__ import annotations

# Submodule (diff/rules/store) bewusst NICHT als bare Namen re-exportieren — sonst würde
# das Paket-Attribut ``snapshot.diff`` von der gleichnamigen Funktion ``diff.diff``
# überschattet (``from pipeline.snapshot import diff`` läge dann auf der Funktion, nicht
# dem Modul). Die Submodule sind regulär importierbar:
#   from pipeline.snapshot import store, diff, rules
#   from pipeline.snapshot.diff import DiffEvent, diff
#   from pipeline.snapshot.rules import classify_diff, PrevIndex
from . import diff, rules, store  # noqa: F401  (Submodule verfügbar machen)
from .diff import DiffEvent
from .rules import PrevIndex, classify_diff
from .store import (
    SNAPSHOT_FIELDS,
    latest_two,
    list_snapshots,
    prune,
    write_snapshot,
)

__all__ = [
    "store",
    "diff",
    "rules",
    "DiffEvent",
    "PrevIndex",
    "classify_diff",
    "SNAPSHOT_FIELDS",
    "latest_two",
    "list_snapshots",
    "prune",
    "write_snapshot",
]
