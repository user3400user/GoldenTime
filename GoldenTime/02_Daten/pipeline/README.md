# pipeline — MaStR-Lead-Backbone (B)

Der **Gesamtdatenexport-Backbone** aus dem Architektur-Entscheid FINAL (14.06., R3 eingearbeitet).
Quelle entkoppelt von Verarbeitung (Adapter): open-mastr lädt den Export als SQLite, die
Verarbeitung kennt nur das normalisierte Lead-Objekt. Geschäftskontext: `../../01_Strategie/STATE.md`.

## Module
| Datei | Rolle |
|---|---|
| `config.py` | Tabellen-/Spaltennamen (Kandidaten), Katalog-Codes, Produkt-Konstanten — **eine Quelle** |
| `db.py` | SQLite-Verbindung + tolerante Schema-Auflösung (case-insensitiv, Kandidatenliste) |
| `export_adapter.py` | **Export-Adapter:** open-mastr Bulk-Export → SQLite |
| `speicher_check.py` | **ABR-Speicher-Anywhere-Query** (Kern, R3 §7a) — Drei-Wege-Klassifikation |
| `normalize.py` | Roh-Solar-Zeile → Lead-Objekt (Trigger T1/T2/T3, Frische-Validierung R3 §7b) |
| `cli.py` | `inspect` · `build-db` · `leads` |
| `tests/` | Synthetisches SQLite beweist die ABR-Logik **ohne** 3-GB-Download / open-mastr |

## Schnellstart
```bash
cd 02_Daten
python -m unittest pipeline.tests.test_speicher_abr     # Logik verifizieren (stdlib, sofort)

pip install -r pipeline/requirements.txt                # nur für den echten Export nötig
python -m pipeline.cli build-db                         # ~3-GB-ZIP -> ~/.open-MaStR/.../open-mastr.db
python -m pipeline.cli inspect                          # echte Tabellen/Spalten gegen config.py prüfen
python -m pipeline.cli leads --plz 48,59 --region-name Muensterland
```
`--db <pfad>` überall, falls die SQLite woanders liegt (oder `MASTR_DB_PATH` setzen).

## Der ABR-Speicher-Anywhere-Check (Kern)
Solar **und** Speicher tragen die `AnlagenbetreiberMastrNummer` (ABR…, ~95–100 % befüllt).
`build_storage_index` sammelt einmal je Lauf alle ABR **mit** Speicher + alle Speicher-Lokationen;
danach klassifiziert jeder Lead in O(1):

- **`none_reported`** → „kein Speicher gemeldet" → Standard-Lead.
- **`operator_elsewhere`** → Betreiber hat Speicher anderswo → **Premium-Flag**, behalten (Lead-Spec §2 Regel 8).
- **`colocated`** → Speicher am selben Ort/Lokation → Bedarfslücke zu → **Ausschluss** (markiert, nicht still verworfen).

**Wahrheits-Grenze (R3):** „kein Speicher **gemeldet**" ≠ „kein Speicher" — ~9 % der Speicher sind
un-/spät registriert. Genau dieses Label steht im Lead.

## Frische-Validierung (R3 §7b)
`reg_datum` allein belegt **keine** Neuinstallation (Nachregistrierung bis 2021). `freshness_check`
flaggt Leads, deren `Inbetriebnahmedatum` deutlich vor der Registrierung liegt (`FRISCHE_WARNUNG`).

## Caveats / bewusste Grenzen
- **Tabellen-/Spaltennamen** sind gegen das offizielle Datenwörterbuch belegt, aber open-mastr kann sie
  je Version anders schreiben (z. B. `LokationMaStRNummer` vs. `LokationMastrNummer`). `db.resolve_*`
  fängt das case-insensitiv ab; **nach dem ersten echten `build-db` mit `inspect` verifizieren** und
  `config.py` ggf. nachziehen.
- **`EegInbetriebnahmedatum`** liegt eigentlich auf `AnlagenEegSolar` (Join via `EegMaStRNummer`); wird
  hier nur gelesen, wenn in der Solar-Tabelle vorhanden, sonst fällt T2 auf das Einheiten-IBN-Jahr zurück.
- **Kein inkrementelles Update** (open-mastr): pro Lauf voller Tagesstand.

## Nächste Schritte (nicht in diesem Stück)
- **QUALIFIZIEREN** — volle Ausschluss-Hierarchie (Lead-Spec §2: öffentliche Hand, Konzern/Filialist,
  Energie-/Projektgesellschaften …) + Mensch-QA-Gate. Hier wird PersonenArt nur **geflaggt**.
- **ANREICHERN** — Entscheider/Kontakt (Halbautomatik + QA, nimble P2).
- **Liefer-Ledger** (Exklusivität über stabile Schlüssel).
- **CSV-Demo-Pfad** `../make_sample.py` bleibt als Fallback fürs 27.06.-Gate (Architektur-Doku §6).
