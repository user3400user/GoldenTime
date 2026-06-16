# CLAUDE.md — technisches Gedächtnis (Build)

Technik-Pendant zu `01_Strategie/STATE.md`. **Geschäftskontext, Funnel, Entscheidungen → STATE.md lesen.**
Diese Datei hält Tech-Stack, Pfade und Bau-Entscheide. Doc-Ownership: `00_DOC-MAP.md`.

## Was hier gebaut wird
Das **Vollpaket** (CC-Build-Briefing v2 §3): 8 generische Plattform-Komponenten, **schmal konfiguriert
gestartet, alles über ein Admin-Dashboard schaltbar.** Die frühere 6-Schritt-Pipeline (PULL → … →
FAKTURIEREN) ist darin aufgegangen. Quelle: Gewerbespeicher-Leads aus dem Marktstammdatenregister (MaStR).

## Architektur-Entscheid (FINAL 14.06., R3 eingearbeitet)
- **Datenquelle = MaStR-Gesamtdatenexport** (Backbone), via **open-mastr** → lokale **SQLite**.
  Web-JSON nur noch optionales Spot-Tool; CSV (`02_Daten/make_sample.py`) = Demo-Fallback.
  Begründung: nur der Export liefert den vollen Betreibergraph für den **betreiberweiten Speicher-Check**.
- **Adapter-Prinzip:** Quelle entkoppelt von Verarbeitung — die Verarbeitung kennt nur das
  normalisierte Objekt. Details: `01_Strategie/Architektur-Entscheidung-Datenquelle_2026-06-14.md`,
  R3-Report: `../research/mastr-pv-leads/report.md`, Distillat: `../research/knowledge/mastr-buy-signals.md`.

## Vollpaket-Architektur — 8 Komponenten + Struktur (Session 1, 16.06.)
Additiv auf bestehendem `pipeline/` — die **9 grünen Tests bleiben unangetastet** (Shims/neue Module).
Zentrale Datenstruktur: `signal/record.py` **SignalRecord (Konfidenz = Pflichtfeld)** — Trigger,
Qualifizierer, Ledger, Anreicherung hängen alle daran.
```
02_Daten/
├─ pipeline/
│  ├─ config.py·db.py·export_adapter.py·speicher_check.py·normalize.py·cli.py   [bleibt, Tests grün]
│  ├─ signal/      K5  SignalRecord · store · from_lead (mappt normalize-Lead-Dict → Record)
│  ├─ triggers/    K3  cohort.py (T2+DV, KEIN Diff) · diff_based.py (T1/T4 scharf; T5/T6/PV default-aus)
│  ├─ qualify/     K4  hierarchy.py + heuristics/*.txt (pflegbar) + qa_gate.py
│  ├─ snapshot/    K2  store·diff·rules  (+ snapshots/<datum>/)   ← Kern-IP
│  ├─ ledger/      K6  funktion × gebiet × trigger
│  ├─ enrich/      K7  gekapselt, DEFAULT AUS
│  ├─ control/     K8-Teil  config_store + metrics  (von Pipeline + Dashboard gelesen)
│  └─ register.py  K1  RegisterAdapter-Protocol + NormalizedUnit  (open-mastr = 1. Adapter)
├─ snapshots/        versionierte Wochen-Snapshots (dated, gitignored)
├─ pipeline_state.db QA + Ledger + Metriken (eigene leichte DB — NICHT die 3-GB-Export-DB)
├─ pipeline/config_store.json   D3-Config (git-versioniert)
└─ dashboard/        K8  schlanke stdlib-Web-App (liest Config+Metriken, schreibt nur Schalter)
```
**Bau-Sequenz:** Phase 0 (build-db+inspect) → **Phase 1** (signal → triggers/cohort T2+DV → qualify →
Signal-Liste; *demo-kritisch fürs Essen*) → Phase 2 (snapshot+diff, Kern-IP) → Phase 3 (dashboard+ledger).
Anreicherung parallel, default aus. **Leichter Start:** Phase 1 nutzt den bestehenden `normalize`-Fluss;
die generische `backbone/`-Umstrukturierung (wind/biomass) kommt erst in Phase 2.

## Die 5 §7-Architektur-Entscheide (16.06. mit Gründer bestätigt)
- **D1 · DB-Engine:** SQLite+WAL jetzt, **3 getrennte DBs** (Export wegwerfbar `~/.open-MaStR/…`; Snapshots
  dated; `pipeline_state.db` für QA/Ledger/Metriken), Postgres als ENV-Switch `MASTR_DB_ENGINE` erst bei
  Hosting/Mehrschreiber. Code ist schon engine-agnostisch — echte Kopplung = 2 db.py-Zeilen
  (`sqlite_master`/`PRAGMA`); list_tables/table_columns bekommen je einen Postgres-Branch (information_schema).
  WAL+busy_timeout+synchronous=NORMAL für nebenläufige Dashboard-Leser. `con.execute()`+`Row` bleibt überall.
- **D2 · Snapshot:** wöchentl. **„Skinny"-Snapshot** (nur die 7 Diff-Schlüsselfelder: EinheitMastrNummer,
  AnlagenbetreiberMastrNummer, Bruttoleistung, Inbetriebnahmedatum, 2× Stilllegung, EegMastrNummer) als
  komprimierte dated SQLite je Lauf (`snapshots/snap_<YYYY-MM-DD>.sqlite`, Datum = open-mastr-Stand).
  Retention **8 Wochen + monatl. Anker ~13 Mt** (T5/T6-Historie). Diff = Set-Diff über EinheitMastrNummer +
  Feldvergleich; stdlib (sqlite3+gzip), <5 GB gesamt. PV-Zubau nur als NEW_UNIT (nicht Leistungs-Diff, §4).
- **D3 · Config-Store:** versionierte **`pipeline/config_store.json`** (git-Diff/blame/revert; überlebt den
  build-db-Neuaufbau; stdlib read+write), gekapselt hinter `control/config_store.py`; Dashboard = einziger
  Writer (atomic `os.replace`), Pipeline liest read-only, 1 Snapshot je Lauf. `trigger_overrides` pro Gebiet
  kann nur AB-, nicht zuschalten (verhindert versehentl. Scharfschalten von default-aus-Triggern).
- **D4 · Register-Adapter:** `pipeline/register.py` — **`typing.Protocol RegisterAdapter`** + `NormalizedUnit`-
  Dataclass (stabile Schlüssel einheit_id / betreiber_id[=ABR-Äquiv.] / lokation_id / standort / datum[=IBN] /
  energietraeger_typ / leistung_kw; quell-spez. Rest in `raw`). open-mastr = erster `MastrAdapter` (umhüllt
  export_adapter/db/normalize). **NUR Interface, kein zweites Register** (YAGNI). Schnitt: Ingest+Normalisierung
  = Adapter (quell-spezifisch); Qualifizierung/Trigger = downstream (quell-neutral, kennt nur NormalizedUnit).
- **D5 · QA-Gate:** Tabelle **`qa_decision`** in `pipeline_state.db`, Key = **EinheitMastrNummer**; nur
  *geflaggte* Grenzfälle in der Queue (`QA_FLAGS`); Entscheidung *hält über Wochenläufe*; **Re-Review nur bei
  Fingerprint-Änderung** (load-bearing: betreiber, abr, personenart, speicher_status, kWp-Band — NICHT Frische).
  Batch-CLI `qa list/approve/reject/approve-abr` jetzt, Dashboard-Tab Phase 3. `auto_ok` (kein QA-Flag) liefert
  sofort → Queue bremst die Demo nicht.

## Phase-0-Schema-Befund (open-mastr 0.17.1 Bulk-SQLite — EMPIRISCH per `inspect`+Inventar 16.06.)
**Reale Tabellennamen = die englischen `*_extended`-Namen** (open-mastrs gejointe Ausgabetabellen; die zuvor
aus dem Quellcode vermuteten deutschen XSD-Namen waren over-thought — `inspect` ist die Wahrheit):
`solar_extended`, `storage_extended`, `solar_eeg`, `storage_eeg`, `locations_extended` (dünn, 8 Spalten),
`market_actors`. **config.py-Tabellen-Kandidaten stimmen → keine Tabellen-Änderung nötig.**
- **Spalten:** deutsche MaStR-Felder, Casing „Mastr" (`LokationMastrNummer`, `EegMastrNummer`) — alle auflösbar.
- **Katalog-Felder sind KLARTEXT, nicht Integer-Codes:** `EinheitBetriebsstatus='In Betrieb'` (6,06 Mio),
  `Bundesland='Bayern'`/`'Nordrhein-Westfalen'`, `Einspeisungsart='Volleinspeisung'`/`'Teileinspeisung (…)'`.
  → `config.BETRIEBSSTATUS_IN_BETRIEB` = Klartext „In Betrieb" gesetzt (Code 35 war Web-JSON). Region via PLZ.
- **Kern-IP trägt (Echtdaten):** ABR auf solar 99,3 % befüllt; Speicher-Index = 2,48 Mio Betreiber + 2,53 Mio
  Lokationen. Co-Lokalität kommt aus dem **Lokations-Set** (Solar+Speicher tragen `LokationMastrNummer`).
  ⚠ `SpeicherAmGleichenOrt` ist im Bulk-Export NICHT brauchbar (nur Werte NULL/'andere Gase' — verschobener
  Katalogwert); `_truthy` verwirft sie korrekt, also kein Schaden, aber NICHT als Co-Lokal-Flag verwenden.
  Realer `leads`-Lauf Münsterland (PLZ 48/59): 13.454 klassifiziert → 12.488 lieferbar, 966 colocated, 1.614 Premium.
- **Marktakteure-Join verdrahtet:** Betreibername/PersonenArt NICHT auf der Einheit → `market_actors`
  (`Firmenname`, `Personenart`, `MastrNummer`); Join `solar_extended.AnlagenbetreiberMastrNummer →
  market_actors.MastrNummer`. config.COL um `firmenname`/`markt_mastr_nr` ergänzt. Personenart = 2 Klartext-
  Klassen ('Organisation…' = juristisch · 'Natürliche Person oder Organisation mit Personenbezug…' = nat./e.K.).
- **T2-Präzision:** `solar_eeg` 1:1 zu solar (6,2 Mio), `EegInbetriebnahmedatum` ~99 % (64.697 leer) → exakter
  LEFT JOIN via `EegMastrNummer`; Fallback auf Einheiten-IBN-Jahr ist real nötig (nicht nur Zierde).
- **T6-Felder in config.COL ergänzt:** `DatumEndgueltigeStilllegung` / `…VoruebergehendeStilllegung` /
  `DatumWiederaufnahmeBetrieb` (auf der Einheit belegt).

## Code-Stand
- `02_Daten/pipeline/` — **PULL steht** (Export-Adapter + ABR-Speicher-Anywhere + Normalisierung + CLI).
  **Neu (Session 1):** `signal/` (K5 SignalRecord + from_lead, Konfidenz=Pflicht) · `control/` (D3 config_store
  + D1/D5/D6 `pipeline_state.db`, WAL) · `config_store.json` (versioniert). **36 Tests grün** (stdlib).
  **Gebaut + integriert (CLI), 151 Tests grün, end-to-end auf Echtdaten validiert:** register(D4) ·
  snapshot+diff(K2) · triggers cohort/diff_based(K3) · qualify+QA(K4/D5) · ledger(K6) · enrich(K7, aus) ·
  dashboard(K8)+metrics. CLI: `signals`/`qa`/`snapshot`/`diff`/`ledger`/`dashboard`. Eigene `pipeline/README.md`.
- `02_Daten/.venv/` — lokales venv (gitignored), **open-mastr 0.17.1** + Deps installiert
  (System-`python3` hat kein pip → via `get-pip.py` gebootstrappt, kein sudo).
- **Phase 0 ABGESCHLOSSEN (16.06.):** `build-db` echter Lauf ✅ (Export-DB 8,6 GB, Download 1575 s), `inspect` ✅,
  `config.py` empirisch verifiziert+korrigiert ✅, 9/9 Tests grün, realer `leads`-Lauf validiert die Pipeline.
- `02_Daten/make_sample.py` — CSV-Demo-Pfad (LEGACY-Speicher-Check), bleibt als Fallback lauffähig.

## Tech-Stack & Konventionen
- **Python 3.12**, stdlib-first. Einzige schwere Dep: **open-mastr** (nur für den echten Export;
  Query-/Normalisierungs-/Snapshot-/Diff-/QA-/Config-Logik + Tests laufen ohne). Aufruf via `.venv/bin/python`.
- DB-Default (Export): `~/.open-MaStR/data/sqlite/open-mastr.db` (per ENV `MASTR_DB_PATH` überschreibbar).
  Operativer State getrennt: `02_Daten/pipeline_state.db` (QA/Ledger/Metriken), Config: `pipeline/config_store.json`.
- MaStR-Feld-/Tabellennamen zentral in `pipeline/config.py` (Kandidatenlisten), case-insensitiv via
  `db.resolve_*`. **Nach `build-db`: `inspect` und `config.py` verifizieren** (deutsche Bulk-Namen, s.o.).
- Stabile Schlüssel (`EinheitMastrNummer`, `AnlagenbetreiberMastrNummer`) = Primärschlüssel + Join-/Ledger-/
  QA-Basis. Beide Datumsfelder (`Registrierungsdatum` + `Inbetriebnahmedatum`) immer mitführen (R3 §7b).

## Befehle
```bash
cd 02_Daten
.venv/bin/python -m unittest pipeline.tests.test_speicher_abr   # Logik-Tests (sofort, ohne Daten)
.venv/bin/python -m pipeline.cli build-db                       # Export laden (~3 GB; läuft auf ZBook)
.venv/bin/python -m pipeline.cli inspect                        # Schema gegen config.py prüfen
.venv/bin/python -m pipeline.cli leads --plz 48,59              # Region → klassifizierte Leads (CSV)
.venv/bin/python -m unittest discover -s pipeline/tests -p "test_*.py"   # volle Suite (151 Tests)
.venv/bin/python -m pipeline.cli signals --gebiet muensterland # T2-Signal-Shipper (cohort+qualify+QA → SignalRecord-CSV)
.venv/bin/python -m pipeline.cli qa list                       # QA-Queue ansehen (approve/reject/approve-abr)
.venv/bin/python -m pipeline.cli snapshot                      # schlanker Wochen-Snapshot (D2)
.venv/bin/python -m pipeline.cli diff                          # Wochen-Diff der 2 jüngsten Snapshots → T1/T4-Signale
.venv/bin/python -m pipeline.cli dashboard                     # Admin-Dashboard (http://127.0.0.1:8765)
```

## Nicht vergessen
- „kein Speicher **gemeldet**" ≠ „kein Speicher" (~9 % unregistriert) — Label genau so führen; gehört als
  Konfidenz-Abschlag in den SignalRecord (Konfidenz = Pflichtfeld).
- **Betreibername/PersonenArt nur via `Marktakteure`-Join** (nicht auf der Einheit, s. Schema-Befund). e.K.-Caveat
  (Einzelkaufleute = juristisch natürliche Personen, echtes Gewerbe) → flaggen + Mensch-QA, nicht blind ausschließen.
- **Region über PLZ filtern** (`Postleitzahl` = Klartext); `Bundesland` ist zwar Klartext, aber grob (exakte Strings wie 'Bayern').
- Guardrail: open-mastr-Lauf > ~2 Sessions (Format-Bruch 01.10.2025, 3-GB-Handling) → Demo auf CSV, B nach Gate.

## Build-Fortschritt (für STATE §7-Übernahme)
**Session 1 (16.06., Claude Code):**
- **Phase 0 ABGESCHLOSSEN:** venv + open-mastr 0.17.1; `build-db` echter Lauf (Export-DB 8,6 GB); `inspect` +
  config.py empirisch verifiziert/korrigiert; 9/9 Tests grün; realer `leads`-Lauf bestätigt die Pipeline auf Echtdaten.
- **Inventar (16.06.):** solar 6.206.994 · storage 2.581.999 · market_actors 5.415.063 · solar_eeg 1:1 (100 %).
  **Post-EEG-Kohorte: 2006=63.806, 2007=76.827 (Σ 140.633);** davon kWp 30–750 + In Betrieb bundesweit ≈ **10.043**
  (T2-Universum vor Speicher-Ausschluss/Qualifizierung). Münsterland 48/59: 12.488 lieferbar, 1.614 Premium.
- Struktur der 8 Komponenten festgelegt; **5 §7-Entscheide bestätigt** (D1 SQLite+WAL/3-DBs · D2 Skinny-Snapshot
  8 Wo.+Anker · D3 JSON-Config · D4 Protocol-Adapter · D5 qa_decision+Fingerprint).
- **Schlüssel-Befund:** Betreibername/PersonenArt nur via `market_actors`-Join (Pflicht im Phase-1-Qualifizierer).
- **Session 1: VOLLES System gebaut + integriert + end-to-end auf Echtdaten validiert.** Alle 8 Komponenten +
  Steuer-Spine, **151 Tests grün**, CLI verdrahtet. Echter `signals`-Lauf Münsterland: **311 T2-Post-EEG-Signale →
  72 lieferbar** (echte Firmennamen via market_actors-Join), 6 DV-Flag; Snapshot (50 s) + Dashboard laufen.
  **Adversariale Review (16.06.):** 17 Befunde verifiziert + behoben — u.a. Over-Flagging (94,6 % der MaStR-
  Akteure sind natürliche Personen mit redacted Namen → nameless Privatpersonen jetzt eigener Bucket, nicht
  QA), T4-Selbstwiderspruch, Zirkel-Import, --out-Kollision, Doppel-T6, Metrik-Doubling. Diff braucht 2. Snapshot.
- **Auftrag (Gründer 16.06.):** das VOLLE generische System bauen inkl. Dashboard, NICHT regionsfixiert — Gebiete = Config.
- **Demo-Ziel:** echte Post-EEG-Signal-Liste + Dashboard fürs Berater-Essen ~27.06.
