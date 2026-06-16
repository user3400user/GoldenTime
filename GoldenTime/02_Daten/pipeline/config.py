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

# --- Eigener operativer State (D1: 3-DB-Trennung) --------------------------
# pipeline_state.db hält QA + Exklusivitäts-Ledger + Metriken; GETRENNT von der
# Export-DB, die open-mastr je build-db KOMPLETT neu baut (sonst wäre der State weg).
PIPELINE_DB_PATH = Path(
    os.environ.get("PIPELINE_DB_PATH", str(Path(__file__).resolve().parent.parent / "pipeline_state.db"))
)
# Versionierte Wochen-Snapshots (D2): dated, schlank, eigener Ordner.
SNAPSHOT_DIR = Path(
    os.environ.get("MASTR_SNAPSHOT_DIR", str(Path(__file__).resolve().parent.parent / "snapshots"))
)
SNAPSHOT_RETENTION_WEEKS = 8     # rollende Wochen (Diff braucht >=2)
SNAPSHOT_ANKER_MONATE = 13       # zusätzlich monatliche Anker für T5/T6-Langhistorie
# Config-Store (D3): versionierte JSON, von Pipeline + Dashboard gelesen.
CONFIG_STORE_PATH = Path(
    os.environ.get("CONFIG_STORE_PATH", str(Path(__file__).resolve().parent / "config_store.json"))
)
# DB-Engine (D1): 'sqlite' jetzt; Postgres als ENV-Switch erst bei Hosting/Mehrschreiber.
DB_ENGINE = os.environ.get("MASTR_DB_ENGINE", "sqlite")

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
    "betreiber_name": ("AnlagenbetreiberName", "Anlagenbetreiber"),  # Phase 0: NICHT im Export auf der Einheit -> via firmenname (market_actors)
    "personenart": ("Personenart", "AnlagenbetreiberPersonenArt"),   # Phase 0: nur auf market_actors
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
    "eeg_inbetriebnahme": ("EegInbetriebnahmedatum",),   # auf solar_eeg (Join via eeg_nr), Phase 0: 100% Coverage
    # --- T6 Stilllegung (Phase 0: auf solar_extended + storage_extended belegt) ----
    "stilllegung_endg": ("DatumEndgueltigeStilllegung",),
    "stilllegung_vorueb": ("DatumBeginnVoruebergehendeStilllegung",),
    "wiederaufnahme": ("DatumWiederaufnahmeBetrieb",),
    # --- Marktakteure-Join: Betreibername/PersonenArt liegen NICHT auf der Einheit
    #     (Phase 0 verifiziert), sondern auf market_actors. Join: Einheit.abr -> market_actors.MastrNummer.
    "firmenname": ("Firmenname",),
    "markt_mastr_nr": ("MastrNummer",),
    # Rechtsform = Wahrheit zu Gemeinnützigkeit/Verein/öffentl./Konzern, die der Name oft NICHT trägt
    # ('Seniorenhilfe St. Franziskus GmbH' = gGmbH; 'INI' = e.V.). Katalog-Klartext (empirisch verifiziert).
    "rechtsform": ("Rechtsform",),
}

# --- Katalog-Werte (Phase 0, 16.06. verifiziert) ---------------------------
# Die open-mastr *_extended-Tabellen lösen Katalog-Codes bereits zu deutschem
# KLARTEXT auf: Bundesland='Bayern', Einspeisungsart='Volleinspeisung',
# EinheitBetriebsstatus='In Betrieb'. -> Region über PLZ filtern (nicht Bundesland-Code).
BETRIEBSSTATUS_IN_BETRIEB = "In Betrieb"   # Klartext im Export (Web-JSON war Code 35)
STORAGE_GEPLANT_STATUS = "In Planung"      # Speicher in Planung -> eigener 'geplant'-Bucket (Gründer-
#   Entscheid 16.06.): NICHT in die heiße Lieferliste (sonst Fehlalarm 'hat schon Speicher'), aber
#   mitführen für die Re-Opportunity (falls die geplante Anlage doch nicht kommt).
# Reine Web-JSON-Codes (NICHT für Export-Queries; *_extended ist Klartext):
ENERGIETRAEGER_SOLAR = 2495
ENERGIETRAEGER_SPEICHER = 2496

# --- Produkt-Konstanten (Lead-Spec / STATE §6) -----------------------------
KWP_MIN = 30.0
KWP_MAX = 750.0              # grober Solarpark-Schutz; P1: Lage-Filter, dann anheben
DV_FLAG_MIN_KWP = 100.0     # Direktvermarktungs-Pflicht ab 100 kWp (DV-Flag, Multiplikator)
FRISCHE_FENSTER_TAGE = 45    # Standard 30–45 (Dichte-Hebel)
# R3 §7b: reg_datum allein ist kein Neubau-Beweis. Liegt die Inbetriebnahme deutlich
# vor der Registrierung -> Nachregistrierungs-Verdacht (Frist bis 2021) -> flaggen.
IBN_REG_LUECKE_WARN_TAGE = 365
POST_EEG_JAHRGAENGE = (2006, 2007)   # T2: EEG-Förderende 2026/2027
