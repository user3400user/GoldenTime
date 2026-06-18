# GoldenTime — LOOP-METRICS
**Lebendes Artefakt (§8 des Loop-Briefings) · Echtdaten-Zahlen je Loop. Quelle: echte 9,3-GB-MaStR-Export-DB (Stand 17.06.2026), nicht Schätzung.**

> Regel (§2.4): Jede pipeline-berührende Schleife beweist sich auf echten MaStR-Daten und schreibt Kennzahlen hierher.

---

## Loop 0 · G0 — USP scharf (Exklusivität + Dedupe erzwungen) · 18.06.2026

### Liefer-Dichte je Demo-Gebiet (T2-Bestand, nach e.K.-Hartfilter, Dry-Run)
Befehl: `gate-demo --gebiete muensterland,osnabrueck --offline` · Laufzeit **8 s** · Export-DB intakt.

| Gebiet | lieferbar | Betriebe (distinct ABR) | **e.K.-gesperrt** | QA-pending | namenlos | coloc-aus | roh | Reconciliation |
|---|--:|--:|--:|--:|--:|--:|--:|:--:|
| Münsterland | 41 | 35 | **0** | 68 | 203 | 10 | 312 | 41+0+68+203+0+0 = 312 ✓ |
| Raum Osnabrück | 48 | 41 | **0** | 66 | 189 | 5 | 303 | 48+0+66+189+0+0 = 303 ✓ |
| **Σ (distinct über Gebiete)** | **89** | **76** | 0 | — | — | — | — | — |

**Speicher-Index (Echtdaten):** 2.456.139 Betreiber · 2.528.210 Lokationen · 1.065.895 co-registrierte Solar (In Betrieb); 148 Lok. + 63 Solar „geplant" (strukturell dünn, bekannt).

### e.K.-Filter-Befund (ehrlich, für die Umsatzdeckel-Frage §6)
**e.K.-gesperrt = 0 in beiden Gebieten.** Der e.K.-Hartfilter entfernt **null** aus dem auto_ok-lieferbar-Bucket — weil benannte natürliche Personen ohnehin via `FLAG_NATUERLICHE_PERSON` → QA-pending laufen (nicht auto-lieferbar). Der Filter ist also **Defense-in-Depth** (fängt ein versehentliches `approve` einer e.K. + den Join-Ausfall-e.K. via Namensmuster), **senkt die lieferbare Dichte aber nicht.** → Die lieferbare Menge nach e.K.-Filter = 41 (Münsterland) / 48 (Osnabrück) Einheiten = 35 / 41 Betriebe. **Das ist T2-BESTAND (einmalig), kein Fluss** — der Retainer-Wert hängt am T1/T4-Wochen-Diff (noch ausstehend).

### USP-Beweis auf Echtdaten (Münsterland, gegen Temp-Ledger; Live-Ledger + I8 unberührt)
| Schritt | Ergebnis | Exit erfüllt |
|---|---|:--:|
| 1. `commit_delivery` KäuferA (41 echte Records) | 41 neu protokolliert | — |
| 2. `commit_delivery` KäuferA (Wiederholung) | **0 neu** | **S1 (Dedupe) ✓** |
| `commit_delivery` KäuferB (gleiches Gebiet×Trigger) | **0 neu** | **S2 (Exklusivität) ✓** |
| Gebiet-Halter | KäuferA | ✓ |
| Temp-Ledger | 41 Lieferzeilen, 1 Exklusiv-Reservierung | ✓ |

### Invarianten-Verifikation (Echtdaten + Tests)
- **I8/§0:** Live-Ledger nach Dry-Run-Demo **leer** (0 delivery, 0 exclusivity) → Demo füllt das Live-Ledger nie (Zwang 3). `--commit` bei `LIVE_DELIVERY_ENABLED=aus` **verweigert** (ABBRUCH, rc 2), Live-Ledger bleibt leer. `LIVE_DELIVERY_ENABLED` nie von CC gesetzt.
- **I5 Reconciliation:** geht in beiden Gebieten exakt auf (s. Tabelle).
- **I1 Tests:** **337 grün** (313 Bestand + 24 neue G0-Tests), 0,7 s.

### Refute-Härtung (nach adversarialer 3-Winkel-Review)
- **Betriebs-Ebene-Exklusivität** (CRITICAL-Fix): ein Betrieb (ABR) = ein Käufer je Funktion, **gebiets- UND trigger-übergreifend**. Echtdaten-Cross-Gebiet-Lauf (Münsterland an A → Osnabrück für B): **0 Betriebe blockiert** — die lieferbaren T2-Sets (35 vs 41 Betriebe) überlappen sich nicht (die „423 ABR in 48/59∩49" gelten über ALLE ABR, nicht die lieferbare T2-Teilmenge). Mechanismus per Unit-Test bewiesen; Leck geschlossen, falls es aufträte.
- **Migration:** `delivery.betreiber_mastr_nr` + Index idempotent ergänzt (echte DB, 0 Zeilen).

### Offen → nächste Schleife(n)
- **T1/T4-Fluss-Zahlen — VERTAGT (extern blockiert, nicht Code):** Parallel-Track (2. Snapshot via `weekly`) **2× fehlgeschlagen** am MaStR-Download-Host `download.marktstammdatenregister.de` (`RemoteDisconnected` / „Connection reset by peer", curl 56). Diagnose: allgemeine Connectivity ok (bundesnetzagentur.de → HTTP 302), **nur der Download-Host resettet aktiv** (temporäre Sperre/Rate-Limit/Egress-Restriktion). → Retainer-Pricing-Basis (T1/T4) steht erst nach erstem echten Wochen-Diff; **Aktion: `weekly` erneut ausführen, sobald der Host wieder erreichbar ist** (oder Export manuell laden). War Sprint-seitig ohnehin M2, nicht M1.
- **Mensch-QA-Durchlauf** der ~134 Pending (68+66) vor dem Essen (`qa suggest`) — die lieferbaren 41/48 sind auto_ok, NICHT mensch-geprüft.
