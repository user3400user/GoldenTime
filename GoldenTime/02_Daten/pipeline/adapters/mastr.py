"""
MaStR-Adapter (open-mastr-Gesamtdatenexport) — erster RegisterAdapter (D4).

Umhüllt den Bestand: ``build_db`` → ``export_adapter.build_db``, ``connect`` → ``db.connect``,
``resolve_schema`` → ``db.resolve_table``/``column_map``. ``iter_units`` nutzt dieselbe
SELECT/WHERE-Mechanik wie ``normalize.iter_leads`` (Region in SQL, Rest in Python), baut aber
die quell-neutrale ``NormalizedUnit`` statt des Lead-Dicts.

WICHTIG (Schnitt D4): Hier KEINE Speicher-/Trigger-/Frische-Logik. Der Adapter liefert nur
roh-normalisierte Einheiten; Klassifikation (speicher_check), Trigger und Frische bleiben
downstream (sie konsumieren ``NormalizedUnit.raw`` weiter). So bleibt das Interface quell-neutral.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from .. import config, export_adapter
from .. import db as dbmod
from ..register import (
    ET_SOLAR,
    ET_SPEICHER,
    NormalizedUnit,
    SchemaMap,
    Standort,
)

# Energieträger-Typ (Interface) -> logischer Tabellen-Schlüssel (db.resolve_table/config).
# YAGNI: nur die im Vollpaket benötigten Träger. Der EV-Ladepunkt-Fall ist nur als Mapping-
# Kommentar belegt (das Interface PASST: sobald open-mastr eine Ladepunkt-Tabelle exportiert,
# genügt hier eine Zeile, z. B. ``ET_EV_LADEPUNKT: "ladepunkt"`` + ein TABLE_CANDIDATES-Eintrag —
# kein Eingriff in die Downstream-Logik). Wind analog (``ET_WIND: "wind"``).
_ET_TO_TABLE: dict = {
    ET_SOLAR: "solar",
    ET_SPEICHER: "storage",
    # ET_WIND: "wind",            # sobald gebraucht: TABLE_CANDIDATES['wind'] ergänzen
    # ET_EV_LADEPUNKT: "ladepunkt",
}

# Logische Felder, die wir je Einheit lesen (wie normalize._SELECT, ohne die reinen
# Qualifizierer-Felder). Beide Datumsfelder werden mitgeführt (R3 §7b), ``datum`` = IBN.
_SELECT = (
    "einheit_nr", "abr", "lokation_nr", "plz", "ort", "bundesland",
    "brutto_kw", "reg_datum", "inbetriebnahme", "eeg_inbetriebnahme",
    "einspeisung", "betriebsstatus", "personenart", "betreiber_name",
    "speicher_gleicher_ort",
)


def _to_float(v: object) -> float | None:
    """kWp tolerant parsen (Komma/Whitespace) — wie normalize._to_float."""
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


class MastrAdapter:
    """open-mastr-Gesamtdatenexport als ``register.RegisterAdapter`` (Protocol-konform)."""

    key = "mastr"
    label = "MaStR Gesamtdatenexport"

    def build_db(self, *, data: tuple[str, ...] | None = None, engine: str = "sqlite") -> Path:
        """Lädt den Export via open-mastr (delegiert an export_adapter.build_db)."""
        objekte = tuple(data) if data is not None else config.OPENMASTR_DATA
        return export_adapter.build_db(data=objekte, engine=engine)

    def connect(self, db_path: Path | str | None = None) -> sqlite3.Connection:
        """Öffnet die Export-SQLite (db.connect setzt sqlite3.Row)."""
        return dbmod.connect(db_path)

    def resolve_schema(self, con: sqlite3.Connection, energietraeger: str) -> SchemaMap:
        """Reale Tabelle + Spaltenauflösung für einen Energieträger (tolerant)."""
        logical_table = self._logical_table(energietraeger)
        table = dbmod.resolve_table(con, logical_table)
        cols = dbmod.table_columns(con, table)
        cmap = dbmod.column_map(cols, *_SELECT)
        columns = {lg: real for lg, real in cmap.items() if real}
        missing = tuple(lg for lg, real in cmap.items() if not real)
        return SchemaMap(table=table, columns=columns, missing=missing)

    def iter_units(
        self,
        con: sqlite3.Connection,
        *,
        energietraeger: tuple = (ET_SOLAR,),
        plz_prefixes: tuple = (),
        bundesland: str = "",
        limit: int | None = None,
    ) -> Iterator[NormalizedUnit]:
        """Iteriert quell-neutrale ``NormalizedUnit`` je gewähltem Energieträger.

        Region (plz_prefixes/bundesland) wird in SQL gefiltert (wie normalize.iter_leads);
        ohne Region MUSS ein ``limit`` gesetzt sein (Solar hat ~6,2 Mio. Zeilen).
        """
        if not plz_prefixes and not bundesland and limit is None:
            raise ValueError(
                "Ohne Region (plz_prefixes/bundesland) bitte ein limit setzen — "
                "die MaStR-Tabellen haben Millionen Zeilen."
            )
        for et in energietraeger:
            yield from self._iter_one(
                con, et, plz_prefixes=plz_prefixes, bundesland=bundesland, limit=limit
            )

    # --- intern ----------------------------------------------------------------------

    def _logical_table(self, energietraeger: str) -> str:
        logical = _ET_TO_TABLE.get(energietraeger)
        if not logical:
            raise ValueError(
                f"MastrAdapter kennt den Energieträger '{energietraeger}' (noch) nicht. "
                f"Bekannt: {sorted(_ET_TO_TABLE)}."
            )
        return logical

    def _iter_one(
        self,
        con: sqlite3.Connection,
        energietraeger: str,
        *,
        plz_prefixes: tuple,
        bundesland: str,
        limit: int | None,
    ) -> Iterator[NormalizedUnit]:
        schema = self.resolve_schema(con, energietraeger)
        cmap = schema.columns
        if "einheit_nr" not in cmap:
            raise LookupError(
                f"Tabelle '{schema.table}' ohne Pflichtspalte 'einheit_nr' "
                f"(EinheitMastrNummer). Fehlend: {schema.missing}"
            )

        # SELECT exakt nach normalize-Vorbild: nur vorhandene Spalten, AS logischer Name.
        sql = (
            "SELECT "
            + ", ".join(f'"{real}" AS {lg}' for lg, real in cmap.items())
            + f' FROM "{schema.table}"'
        )

        where: list = []
        params: list = []
        if plz_prefixes:
            if "plz" not in cmap:
                raise LookupError(
                    f"PLZ-Filter verlangt, aber Tabelle '{schema.table}' ohne Postleitzahl-Spalte."
                )
            where.append("(" + " OR ".join(f'"{cmap["plz"]}" LIKE ?' for _ in plz_prefixes) + ")")
            params.extend(f"{p}%" for p in plz_prefixes)
        if bundesland and "bundesland" in cmap:
            where.append(f'"{cmap["bundesland"]}" = ?')
            params.append(bundesland)
        if where:
            sql += " WHERE " + " AND ".join(where)
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))

        for row in con.execute(sql, params):
            r = dict(row)
            yield NormalizedUnit(
                einheit_id=r.get("einheit_nr") or "",
                betreiber_id=r.get("abr"),
                lokation_id=r.get("lokation_nr"),
                standort=Standort(
                    plz=r.get("plz"),
                    ort=r.get("ort"),
                    bundesland=r.get("bundesland"),
                ),
                # datum = Inbetriebnahmedatum (maßgeblich, R3 §7b); reg_datum bleibt in raw.
                datum=r.get("inbetriebnahme"),
                energietraeger_typ=energietraeger,
                leistung_kw=_to_float(r.get("brutto_kw")),
                raw=r,  # quell-spezifischer Rest für Speicher-/Trigger-/Frische-Logik downstream
                quelle=self.key,
            )
