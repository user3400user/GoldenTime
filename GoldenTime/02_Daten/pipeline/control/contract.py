"""
Daten-Kontrakt / Schema-Drift-Gate (Loop 5, Zielbild Datenqualität 5,0) — Ingest-Expectations.

Der Datenbestand IST das Asset: eine stille Schema-/Katalog-Korruption (z.B. der open-mastr-Format-
Bruch vom 01.10.2025, oder ein Code-statt-Klartext-Drift bei ``EinheitBetriebsstatus``) würde sonst
**still** falsche oder leere Leads an zahlende Exklusiv-Kunden liefern. Dieses Modul fängt den Drift
**vor** der Lead-Produktion und **stoppt den Lauf laut** (statt ihn still zu absorbieren).

Reine Funktionen auf einer offenen open-mastr-Export-Verbindung; nutzt die case-insensitiven Resolver
aus ``db`` (gleiche Wahrheit wie ``cli inspect``). stdlib-only.
"""
from __future__ import annotations

import sqlite3

from .. import config
from .. import db as dbmod

# Pflicht-Spalten je logischer Tabelle — die load-bearing Felder, ohne die korrekte Leads unmöglich
# sind (Identität/Join/Filter/Trigger/Datum). Fehlt eines, ist der Export gedriftet → Lauf stoppen.
CONTRACT: dict[str, tuple[str, ...]] = {
    "solar": ("einheit_nr", "abr", "plz", "brutto_kw", "inbetriebnahme", "betriebsstatus",
              "einspeisung", "eeg_nr"),
    "market": ("markt_mastr_nr", "firmenname", "personenart"),
    "storage": ("einheit_nr", "abr"),
    "solar_eeg": ("eeg_nr", "eeg_inbetriebnahme"),
}


class ContractError(RuntimeError):
    """Daten-Kontrakt verletzt (Schema-/Katalog-Drift) — der Lauf wird gestoppt."""


def verify_contract(con: sqlite3.Connection) -> list[str]:
    """Prüfe Tabellen-/Spalten- und Katalog-Kontrakt. Gibt eine Liste von Verletzungen zurück (leer = OK)."""
    probleme: list[str] = []
    for logical, cols in CONTRACT.items():
        try:
            table = dbmod.resolve_table(con, logical)
        except LookupError:
            probleme.append(f"Tabelle '{logical}' fehlt (Kandidaten {config.TABLE_CANDIDATES.get(logical)}).")
            continue
        vorhanden = dbmod.table_columns(con, table)
        for c in cols:
            if dbmod.resolve_column(vorhanden, c) is None:
                probleme.append(f"Spalte '{logical}.{c}' fehlt in Tabelle '{table}' (Schema-Drift?).")

    # Katalog-Wert-Kontrakt: EinheitBetriebsstatus MUSS den Klartext 'In Betrieb' tragen (nicht Codes).
    # Genau der 01.10.2025-Format-/Code-Drift würde sonst still 0 lieferbare Leads erzeugen.
    try:
        table = dbmod.resolve_table(con, "solar")
        col = dbmod.resolve_column(dbmod.table_columns(con, table), "betriebsstatus")
        if col:
            row = con.execute(
                f'SELECT 1 FROM "{table}" WHERE "{col}" = ? LIMIT 1',
                (config.BETRIEBSSTATUS_IN_BETRIEB,),
            ).fetchone()
            if row is None:
                probleme.append(
                    f"Katalog-Drift: kein Datensatz mit {col}='{config.BETRIEBSSTATUS_IN_BETRIEB}' — "
                    "Betriebsstatus-Werte geändert (Code statt Klartext?)? Würde still leere Leads erzeugen."
                )
    except LookupError:
        pass  # fehlende solar-Tabelle ist oben bereits gemeldet

    return probleme


def assert_contract(con: sqlite3.Connection) -> None:
    """Wirf ``ContractError`` bei Kontrakt-Verletzung — der Lauf stoppt LAUT statt still falsch zu liefern."""
    probleme = verify_contract(con)
    if probleme:
        raise ContractError(
            "Daten-Kontrakt verletzt (Schema-/Katalog-Drift — Lauf gestoppt, statt still falsche/leere "
            "Leads zu liefern):\n  - " + "\n  - ".join(probleme)
            + "\n  → Diagnose: `python -m pipeline.cli inspect`; open-mastr-Exportformat prüfen."
        )
