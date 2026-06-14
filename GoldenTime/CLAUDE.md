# CLAUDE.md — technisches Gedächtnis (Build)

Technik-Pendant zu `01_Strategie/STATE.md`. **Geschäftskontext, Funnel, Entscheidungen → STATE.md lesen.**
Diese Datei hält Tech-Stack, Pfade und Bau-Entscheide. Doc-Ownership: `00_DOC-MAP.md`.

## Was hier gebaut wird
Die 6-Schritt-Pipeline (PULL → QUALIFIZIEREN → ANREICHERN → PAKETIEREN → LIEFERN → FAKTURIEREN) für
Gewerbespeicher-Leads aus dem Marktstammdatenregister (MaStR).

## Architektur-Entscheid (FINAL 14.06., R3 eingearbeitet)
- **Datenquelle = MaStR-Gesamtdatenexport** (Backbone), via **open-mastr** → lokale **SQLite**.
  Web-JSON nur noch optionales Spot-Tool; CSV (`02_Daten/make_sample.py`) = Demo-Fallback.
  Begründung: nur der Export liefert den vollen Betreibergraph für den **betreiberweiten Speicher-Check**.
- **Adapter-Prinzip:** Quelle entkoppelt von Verarbeitung — die Verarbeitung kennt nur das
  normalisierte Lead-Objekt. Details: `01_Strategie/Architektur-Entscheidung-Datenquelle_2026-06-14.md`,
  R3-Report: `../research/mastr-pv-leads/report.md`, Distillat: `../research/knowledge/mastr-buy-signals.md`.

## Code-Stand
- `02_Daten/pipeline/` — **B-Backbone** (Export-Adapter + ABR-Speicher-Anywhere-Query + Normalisierung +
  CLI + Tests). Eigene `pipeline/README.md`. Schritt **PULL** steht; QUALIFIZIEREN/ANREICHERN folgen.
- `02_Daten/make_sample.py` — CSV-Demo-Pfad (LEGACY-Speicher-Check), bleibt als Fallback lauffähig.

## Tech-Stack & Konventionen
- **Python 3.12**, stdlib-first. Einzige externe Abhängigkeit: **open-mastr** (nur für den echten Export;
  Query-/Normalisierungs-Logik + Tests laufen ohne). `02_Daten/pipeline/requirements.txt`.
- DB-Default: `~/.open-MaStR/data/sqlite/open-mastr.db` (per ENV `MASTR_DB_PATH` überschreibbar).
- MaStR-Feld-/Tabellennamen: zentral in `pipeline/config.py` (Kandidatenlisten), case-insensitiv via
  `db.resolve_*`. **Nach erstem `build-db`: `python -m pipeline.cli inspect` und `config.py` verifizieren.**
- Stabile Schlüssel (`EinheitMastrNummer`, `AnlagenbetreiberMastrNummer`) sind Primärschlüssel + Join-/
  Ledger-Basis. Beide Datumsfelder (`Registrierungsdatum` + `Inbetriebnahmedatum`) immer mitführen
  (Frische nur kombiniert belastbar, R3 §7b).

## Befehle
```bash
cd 02_Daten
python -m unittest pipeline.tests.test_speicher_abr   # Logik-Tests (sofort, ohne Daten)
python -m pipeline.cli build-db                        # Export laden (~3 GB, gehört aufs ZBook)
python -m pipeline.cli inspect                         # Schema gegen config.py prüfen
python -m pipeline.cli leads --plz 48,59               # Region -> klassifizierte Leads (CSV)
```

## Nicht vergessen
- „kein Speicher **gemeldet**" ≠ „kein Speicher" (~9 % unregistriert) — Label genau so führen.
- `AnlagenbetreiberPersonenArt` = strukturierter Gewerblich-Filter, ABER e.K.-Caveat (Einzelkaufleute
  sind juristisch natürliche Personen, echtes Gewerbe) → flaggen + Mensch-QA, nicht blind ausschließen.
- Guardrail: open-mastr-Lauf > ~2 Sessions (Format-Bruch 01.10.2025, 3-GB-Handling) → Demo auf CSV, B nach Gate.
