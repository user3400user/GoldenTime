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

from . import config
from . import db as dbmod

log = logging.getLogger(__name__)

# Klassifikations-Codes
NONE_REPORTED = "none_reported"
OPERATOR_ELSEWHERE = "operator_elsewhere"
COLOCATED = "colocated"
GEPLANT = "geplant"            # Speicher am Standort IN PLANUNG -> eigener Bucket (nicht heiß, nicht Ausschluss)

# Belegbare Aussage je Code (R3: "gemeldet", nicht "vorhanden")
LABEL = {
    NONE_REPORTED: "kein Speicher gemeldet",
    OPERATOR_ELSEWHERE: "Speicher beim Betreiber (anderer Standort) gemeldet",
    COLOCATED: "Speicher am Standort gemeldet",
    GEPLANT: "Speicher am Standort in Planung gemeldet",
}


@dataclass(frozen=True)
class StorageIndex:
    """Vorberechnete Speicher-Indizes: einmal bauen, dann O(1) je Lead klassifizieren."""

    operators: frozenset[str]   # ABR mit >=1 gemeldetem (In-Betrieb-)Speicher (irgendwo)
    locations: frozenset[str]   # SEL-Lokationen mit >=1 gemeldetem Speicher
    colocated_solar: frozenset[str] = frozenset()   # Solar-EinheitMastrNr, auf die ein Speicher
    #   per GemeinsamRegistrierteSolareinheitMastrNummer direkt zeigt (Zweit-Review-Fix)
    geplant_locations: frozenset[str] = frozenset()  # Lokationen mit Speicher-Status 'In Planung'
    geplant_solar: frozenset[str] = frozenset()      # Solar-Einheiten mit co-reg. GEPLANTEM Speicher

    def classify(self, abr: str | None, lokation: str | None,
                 speicher_am_gleichen_ort: object = None, einheit_nr: str | None = None) -> str:
        """Klassifiziere eine PV-Einheit gegen den Speicher-Index.

        Co-lokal (= Speicher am Standort, Bedarf gedeckt -> Ausschluss), wenn EINES gilt:
        (a) PV-seitiges Flag ``SpeicherAmGleichenOrt`` truthy, (b) die PV-Lokation führt selbst
        einen Speicher, ODER (c) ein Speicher zeigt per ``GemeinsamRegistrierteSolareinheitMastr-
        Nummer`` direkt auf DIESE PV-Einheit (``einheit_nr``) — der direkte Back-Link fängt die
        ~15.492 co-registrierten Paare mit ABWEICHENDER Lokation, die (b) verfehlt.
        """
        colocated = (
            _truthy(speicher_am_gleichen_ort)
            or (bool(lokation) and lokation in self.locations)
            or (bool(einheit_nr) and einheit_nr in self.colocated_solar)
        )
        if colocated:
            return COLOCATED
        # In-Betrieb-Speicher hat Vorrang; sonst: ein GEPLANTER Speicher am Standort -> eigener Bucket
        # (kriegen ja gerade einen -> nicht heiß, aber kein 'hat schon Speicher'-Ausschluss).
        if (bool(lokation) and lokation in self.geplant_locations) or (
                bool(einheit_nr) and einheit_nr in self.geplant_solar):
            return GEPLANT
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
    status_col = dbmod.resolve_column(cols, "betriebsstatus")
    if not abr_col:
        raise LookupError(
            f"Speicher-Tabelle '{table}' ohne AnlagenbetreiberMastrNummer-Spalte. "
            f"Vorhandene Spalten: {cols}"
        )

    # Zweit-Review-Fix (16.06., D-Entscheid): NUR 'In Betrieb'-Speicher zählen für den
    # colocated/Anywhere-Ausschluss. Ein STILLGELEGTER/geplanter Speicher schloss sonst valide
    # PV-Leads fälschlich aus — toter Speicher = bester Nachrüst-Lead, kein Ausschluss-Grund.
    # (Belegt: SEE955882610581 wurde wegen einer 2023 endgültig stillgelegten Batterie verworfen.)
    # Direkter Back-Link Speicher -> co-registrierte Solar-Einheit (GemeinsamRegistrierteSolareinheit-
    # MastrNummer) fängt co-lokale Paare mit abweichender Lokation (Zweit-Review-Fix).
    gem_col = dbmod.resolve_column(cols, "gem_solar_nr")
    if not sel_col:
        log.warning("Speicher-Tabelle '%s' ohne Lokations-Spalte — "
                    "co-lokaler Check nur über SpeicherAmGleichenOrt.", table)
    if not status_col:
        log.warning("Speicher-Tabelle '%s' ohne Betriebsstatus-Spalte — "
                    "stillgelegte Speicher können nicht ausgefiltert werden.", table)

    operators: set[str] = set()
    locations: set[str] = set()
    colocated_solar: set[str] = set()        # In-Betrieb-Speicher (Ausschluss-Sets)
    geplant_locations: set[str] = set()
    geplant_solar: set[str] = set()          # 'In Planung'-Speicher (eigener Bucket, nicht heiß)
    in_betrieb = str(config.BETRIEBSSTATUS_IN_BETRIEB)
    geplant = str(config.STORAGE_GEPLANT_STATUS)

    # Opt-Hunt: EIN Voll-Scan über storage_extended (2,58 Mio) statt 5 separater DISTINCT-Scans
    # (~16 s -> ~3 s je Wochenlauf). Partitionierung In Betrieb / In Planung in Python; Sets dedupen.
    sel_expr = f'"{sel_col}"' if sel_col else "NULL"
    gem_expr = f'"{gem_col}"' if gem_col else "NULL"
    status_expr = f'"{status_col}"' if status_col else "NULL"
    for abr, sel, gem, status in con.execute(
            f'SELECT "{abr_col}", {sel_expr}, {gem_expr}, {status_expr} FROM "{table}"'):
        if status_col is None or status == in_betrieb:   # In Betrieb (bzw. alles, wenn kein Status)
            if abr:
                operators.add(abr)
            if sel:
                locations.add(sel)
            if gem:
                colocated_solar.add(gem)
        elif status == geplant:
            if sel:
                geplant_locations.add(sel)
            if gem:
                geplant_solar.add(gem)

    log.info("Speicher-Index aus '%s': %d Betreiber, %d Lok., %d co-reg. Solar (In Betrieb); "
             "%d Lok. + %d Solar geplant.", table, len(operators), len(locations),
             len(colocated_solar), len(geplant_locations), len(geplant_solar))
    return StorageIndex(frozenset(operators), frozenset(locations), frozenset(colocated_solar),
                        frozenset(geplant_locations), frozenset(geplant_solar))
