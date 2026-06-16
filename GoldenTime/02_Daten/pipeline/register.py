"""
Register-Adapter-Interface (Komponente 1 / D4, Briefing §7.4).

Entkoppelt die Datenquelle von der Verarbeitung: Trigger, Qualifizierer und Ledger kennen
nur das quell-neutrale ``NormalizedUnit`` — nicht open-mastr, nicht die MaStR-Schreibweise.
Eine neue Quelle (anderes Register) ist damit „nur" ein weiterer Adapter, der dasselbe
``RegisterAdapter``-Protocol erfüllt; die Downstream-Logik bleibt unangetastet.

Schnitt (D4): Ingest + Normalisierung = Adapter (quell-spezifisch). Speicher-/Trigger-/
Frische-Logik = downstream (quell-neutral). Dieser Modul-Header definiert NUR das Interface
und ``NormalizedUnit``; der erste (und vorerst einzige) Adapter ist ``MastrAdapter`` —
KEIN zweites Register (YAGNI).

Stabile Schlüssel (wie im Bestand): ``einheit_id`` (EinheitMastrNummer-Äquiv.),
``betreiber_id`` (AnlagenbetreiberMastrNummer-Äquiv.), ``lokation_id``. ``datum`` ist das
maßgebliche Datum = Inbetriebnahmedatum (R3 §7b: reg_datum allein ist kein Neubau-Beweis,
darum führt der Adapter beides in ``raw`` mit, gibt aber IBN als ``datum`` aus).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Protocol, runtime_checkable

# --- Energieträger-Typen (quell-neutral; Adapter mappt sein Schema hierauf) ----------
# Bewusst Strings (nicht die MaStR-Web-JSON-Codes 2495/2496 aus config.py): das Interface
# soll register-unabhängig sein. Der MastrAdapter übersetzt diese Typen auf seine Tabellen.
ET_SOLAR = "solar"
ET_SPEICHER = "speicher"
ET_WIND = "wind"
ET_EV_LADEPUNKT = "ev_ladepunkt"


@dataclass(frozen=True)
class Standort:
    """Geografische Verortung einer Einheit (quell-neutral). Region-Filter läuft über PLZ."""

    plz: str | None
    ort: str | None
    bundesland: str | None
    strasse: str | None = None


@dataclass(frozen=True)
class NormalizedUnit:
    """Die quell-neutrale Einheit — das einzige, was die Verarbeitung downstream kennt.

    Quell-spezifische Roh-Felder (Status, Einspeisung, EEG-Nummer, beide Datumsfelder …)
    bleiben in ``raw`` erhalten, damit die downstream-Logik (Speicher-Check, Trigger,
    Frische) daraus weiterarbeiten kann, ohne dass das Interface jedes Feld kennen muss.
    """

    einheit_id: str                  # stabiler Einheiten-Schlüssel (EinheitMastrNummer-Äquiv.)
    betreiber_id: str | None         # Betreiber-Schlüssel (AnlagenbetreiberMastrNummer-Äquiv.)
    lokation_id: str | None          # Lokations-Schlüssel (co-lokaler Speicher-Check)
    standort: Standort
    datum: str | None                # maßgebliches Datum = Inbetriebnahmedatum (ISO-Text)
    energietraeger_typ: str          # ET_SOLAR | ET_SPEICHER | ET_WIND | ET_EV_LADEPUNKT
    leistung_kw: float | None        # kWp = Bruttoleistung
    raw: dict = field(default_factory=dict)   # quell-spezifischer Rest (Status, beide Daten, …)
    quelle: str = ""                 # Adapter-key, der diese Einheit erzeugt hat (Provenance)


@dataclass(frozen=True)
class SchemaMap:
    """Auflösung logischer Felder auf die realen Tabellen-/Spaltennamen einer Quelle.

    ``columns``: {logischer Name -> realer Spaltenname}. ``missing``: logische Felder, für
    die in der Quelle keine Spalte gefunden wurde (Diagnose, nicht hart fehlschlagen lassen).
    """

    table: str
    columns: dict
    missing: tuple = ()


@runtime_checkable
class RegisterAdapter(Protocol):
    """Vertrag jeder Datenquelle (D4). open-mastr = erster Adapter (``MastrAdapter``).

    Bewusst schmal (YAGNI): genug, um Einheiten zu beschaffen (``build_db``), zu öffnen
    (``connect``), das Schema aufzulösen (``resolve_schema``) und quell-neutral zu iterieren
    (``iter_units``). Speicher-/Trigger-/Frische-Logik bleibt downstream.
    """

    key: str
    label: str

    def build_db(self, *, data: object = None, engine: str = "sqlite") -> Path:
        """Beschafft/baut die lokale Quell-DB und gibt deren Pfad zurück."""
        ...

    def connect(self, db_path: Path | str | None = None) -> sqlite3.Connection:
        """Öffnet die Quell-DB (``sqlite3.Row`` als row_factory)."""
        ...

    def resolve_schema(self, con: sqlite3.Connection, energietraeger: str) -> SchemaMap:
        """Löst Tabelle + logische Spalten für einen Energieträger auf (tolerant)."""
        ...

    def iter_units(
        self,
        con: sqlite3.Connection,
        *,
        energietraeger: tuple = (ET_SOLAR,),
        plz_prefixes: tuple = (),
        bundesland: str = "",
        limit: int | None = None,
    ) -> Iterator[NormalizedUnit]:
        """Iteriert quell-neutrale ``NormalizedUnit`` für die gewählten Energieträger/Region."""
        ...


# --- Adapter-Registry ----------------------------------------------------------------
# WICHTIG: register.py importiert adapters.mastr NICHT auf Modulebene — adapters.mastr
# importiert seinerseits aus register (NormalizedUnit etc.). Ein Top-Level-Import hier
# erzeugte einen Zirkel, der crasht, sobald jemand `pipeline.adapters` ZUERST importiert.
# Darum lazy: der Adapter wird erst bei Zugriff auf REGISTERS / get_registers() geladen,
# wenn register vollständig initialisiert ist (PEP 562).
_REGISTERS_CACHE: dict | None = None


def get_registers() -> dict:
    """Adapter-Registry (lazy + gecacht). open-mastr = erster Adapter; zweites Register = neuer Eintrag."""
    global _REGISTERS_CACHE
    if _REGISTERS_CACHE is None:
        from .adapters.mastr import MastrAdapter
        _REGISTERS_CACHE = {"mastr": MastrAdapter()}
    return _REGISTERS_CACHE


def __getattr__(name: str):
    # `from pipeline.register import REGISTERS` löst hier lazy auf — kein Import-Zyklus.
    if name == "REGISTERS":
        return get_registers()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
