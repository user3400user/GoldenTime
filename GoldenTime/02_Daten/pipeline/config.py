"""
Zentrale Konfiguration der MaStR-Pipeline — eine Quelle für Namen/Codes/Konstanten.

Warum hier gebündelt: MaStR/open-mastr variieren die Schreibweise je Schema-/Tool-Version
leicht (z. B. ``LokationMaStRNummer`` vs. ``LokationMastrNummer``; neues Exportformat seit
01.10.2025). Darum stehen je Feld/Tabelle mehrere Kandidaten; ``db.resolve_*`` löst den
realen Namen case-insensitiv gegen die tatsächliche DB auf. Feldnamen sind gegen das
offizielle Datenwörterbuch (Gesamtdatenexport-Doku Rev. 26.1.2) belegt — R3-Report
``research/mastr-pv-leads/report.md`` (Schnellreferenz dort).
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Pfade -----------------------------------------------------------------
# open-mastr schreibt standardmäßig nach ~/.open-MaStR/data/sqlite/open-mastr.db .
# Per ENV MASTR_DB_PATH überschreibbar (z. B. externer Datenträger fürs ~3-GB-ZIP).
DEFAULT_DB_PATH = Path(
    os.environ.get(
        "MASTR_DB_PATH",
        str(Path.home() / ".open-MaStR" / "data" / "sqlite" / "open-mastr.db"),
    )
)

# --- open-mastr Technologie-/Objekt-Auswahl (download(data=...)) -----------
# Nur diese Datensätze laden statt aller ~30 Objekte: solar + storage genügen für den
# ABR-Anywhere-Check; location (co-lokal) + market (gewerblich/PersonenArt) ergänzen.
# Das sind open-mastr-`data=`-Schlüssel, NICHT die SQLite-Tabellennamen.
OPENMASTR_DATA: tuple[str, ...] = ("solar", "storage", "location", "market")

# --- Erwartete SQLite-Tabellennamen (Defaults; gegen reale DB verifizieren) -
# `cli.py inspect` zeigt die echten Namen; resolve_table matcht case-insensitiv und
# per Teilstring, daher sind das nur Start-Kandidaten.
TABLE_CANDIDATES: dict[str, tuple[str, ...]] = {
    "solar": ("solar_extended", "solar", "einheitensolar", "einheitsolar"),
    "storage": ("storage_extended", "storage", "einheitenstromspeicher",
                "einheitstromspeicher"),
    "solar_eeg": ("solar_eeg", "anlageneegsolar", "eeg_solar"),
    "location": ("locations_extended", "locations", "location", "lokationen"),
    "market": ("market_actors", "marktakteure", "market"),
}

# --- Spaltennamen (MaStR-Felder) -> Kandidaten -----------------------------
COL: dict[str, tuple[str, ...]] = {
    "einheit_nr": ("EinheitMastrNummer",),
    "abr": ("AnlagenbetreiberMastrNummer",),
    "lokation_nr": ("LokationMaStRNummer", "LokationMastrNummer"),
    "betreiber_name": ("AnlagenbetreiberName", "Anlagenbetreiber"),
    "personenart": ("AnlagenbetreiberPersonenArt", "Personenart"),
    "plz": ("Postleitzahl",),
    "ort": ("Ort",),
    "bundesland": ("Bundesland",),
    "brutto_kw": ("Bruttoleistung",),
    "netto_kw": ("Nettonennleistung",),
    "reg_datum": ("Registrierungsdatum",),
    "inbetriebnahme": ("Inbetriebnahmedatum",),
    "letzte_aktual": ("DatumLetzteAktualisierung",),
    "einspeisung": ("Einspeisungsart",),
    "betriebsstatus": ("EinheitBetriebsstatus", "Betriebsstatus"),
    "speicher_gleicher_ort": ("SpeicherAmGleichenOrt",),
    "gem_solar_nr": ("GemeinsamRegistrierteSolareinheitMastrNummer",),
    "eeg_nr": ("EegMaStRNummer", "EegMastrNummer"),
    "eeg_inbetriebnahme": ("EegInbetriebnahmedatum",),
}

# --- Katalog-Codes (MaStR; gemessen R3 N+1) --------------------------------
ENERGIETRAEGER_SOLAR = 2495
ENERGIETRAEGER_SPEICHER = 2496
BETRIEBSSTATUS_IN_BETRIEB = 35  # "In Betrieb"

# --- Produkt-Konstanten (Lead-Spec / STATE §6) -----------------------------
KWP_MIN = 30.0
KWP_MAX = 750.0              # grober Solarpark-Schutz; P1: Lage-Filter, dann anheben
FRISCHE_FENSTER_TAGE = 45    # Standard 30–45 (Dichte-Hebel)
# R3 §7b: reg_datum allein ist kein Neubau-Beweis. Liegt die Inbetriebnahme deutlich
# vor der Registrierung -> Nachregistrierungs-Verdacht (Frist bis 2021) -> flaggen.
IBN_REG_LUECKE_WARN_TAGE = 365
POST_EEG_JAHRGAENGE = (2006, 2007)   # T2: EEG-Förderende 2026/2027
