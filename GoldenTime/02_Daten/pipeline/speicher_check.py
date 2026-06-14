"""
ABR-Speicher-Anywhere-Query — Kern des B-Backbones (R3 §7a).

Ersetzt den PLZ+Namens-Fuzzy-Check aus make_sample.py durch einen ID-basierten,
betreiberweiten Check: Ein Betrieb "hat Speicher", wenn unter SEINER
``AnlagenbetreiberMastrNummer`` (ABR…) IRGENDWO ein Stromspeicher registriert ist — nicht
nur am PV-Standort. Grundlage: Solar UND Speicher tragen die ABR (~95–100 % befüllt,
Solar 100 %); Group-by ABR über die Speicher-Tabelle findet jeden Speicher eines
Betreibers (R3/SQ4).

Drei-Wege-Klassifikation (Lead-Spec §2 Regel 8):
  colocated          Speicher am selben Ort/Lokation  -> Bedarfslücke zu       -> Ausschluss
  operator_elsewhere Speicher beim Betreiber, anderswo -> kennt die Rechnung   -> PREMIUM, behalten
  none_reported      kein Speicher gemeldet            -> Standard-Lead

Wahrheits-Grenze (R3): "kein Speicher gemeldet" ist NICHT "kein Speicher" — ~9 % der
Speicher sind un-/spät registriert. Genau dieses Label gehört in Stempel + Liefer-Mail.

Implementierung: Wir bauen einmal je DB-Lauf zwei Mengen aus der Speicher-Tabelle
(ABR-Set + Lokations-Set) und klassifizieren dann jede Solar-Zeile in O(1). Bei ~2,58 Mio.
Speicher-Einheiten sind das handhabbare In-Memory-Sets; kein 6,2-Mio.×2,58-Mio.-Join nötig.
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

from . import db as dbmod

log = logging.getLogger(__name__)

# Klassifikations-Codes
NONE_REPORTED = "none_reported"
OPERATOR_ELSEWHERE = "operator_elsewhere"
COLOCATED = "colocated"

# Belegbare Aussage je Code (R3: "gemeldet", nicht "vorhanden")
LABEL = {
    NONE_REPORTED: "kein Speicher gemeldet",
    OPERATOR_ELSEWHERE: "Speicher beim Betreiber (anderer Standort) gemeldet",
    COLOCATED: "Speicher am Standort gemeldet",
}


@dataclass(frozen=True)
class StorageIndex:
    """Vorberechnete Speicher-Indizes: einmal bauen, dann O(1) je Lead klassifizieren."""

    operators: frozenset[str]   # ABR mit >=1 gemeldetem Speicher (irgendwo)
    locations: frozenset[str]   # SEL-Lokationen mit >=1 gemeldetem Speicher

    def classify(self, abr: str | None, lokation: str | None,
                 speicher_am_gleichen_ort: object = None) -> str:
        """Klassifiziere eine PV-Einheit gegen den Speicher-Index.

        ``speicher_am_gleichen_ort``: das PV-seitige Bool-Feld ``SpeicherAmGleichenOrt``
        (truthy / 1 / "1" / "true" zählt). Co-lokal = dieses Flag ODER die PV-Lokation
        führt selbst einen Speicher.
        """
        colocated = _truthy(speicher_am_gleichen_ort) or (
            bool(lokation) and lokation in self.locations
        )
        if colocated:
            return COLOCATED
        if abr and abr in self.operators:
            return OPERATOR_ELSEWHERE
        return NONE_REPORTED


def _truthy(v: object) -> bool:
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return v != 0
    return str(v).strip().lower() in {"1", "true", "ja", "wahr", "x", "y", "yes"}


def build_storage_index(
    con: sqlite3.Connection, storage_table: str | None = None
) -> StorageIndex:
    """Baue den Speicher-Index aus der Speicher-Tabelle (ABR-Set + Lokations-Set)."""
    table = storage_table or dbmod.resolve_table(con, "storage")
    cols = dbmod.table_columns(con, table)
    abr_col = dbmod.resolve_column(cols, "abr")
    sel_col = dbmod.resolve_column(cols, "lokation_nr")
    if not abr_col:
        raise LookupError(
            f"Speicher-Tabelle '{table}' ohne AnlagenbetreiberMastrNummer-Spalte. "
            f"Vorhandene Spalten: {cols}"
        )

    operators = {
        r[0]
        for r in con.execute(
            f'SELECT DISTINCT "{abr_col}" FROM "{table}" '
            f'WHERE "{abr_col}" IS NOT NULL AND "{abr_col}" <> \'\''
        )
    }
    locations: set[str] = set()
    if sel_col:
        locations = {
            r[0]
            for r in con.execute(
                f'SELECT DISTINCT "{sel_col}" FROM "{table}" '
                f'WHERE "{sel_col}" IS NOT NULL AND "{sel_col}" <> \'\''
            )
        }
    else:
        log.warning("Speicher-Tabelle '%s' ohne Lokations-Spalte — "
                    "co-lokaler Check nur über SpeicherAmGleichenOrt.", table)

    log.info("Speicher-Index aus '%s': %d Betreiber (ABR) mit Speicher, %d Lokationen.",
             table, len(operators), len(locations))
    return StorageIndex(frozenset(operators), frozenset(locations))
