# Architektur-Entscheidung: Datenquelle & Datenmodell (Punkt 2)
**Stand 14.06.2026 · Gehört in: 01_Strategie/ · Status: ENTSCHIEDEN (R3 eingearbeitet) — ersetzt die Rahmen-Version vom 13.06. (→ deprecated).**

> R3 (MaStR-Gesamtdatenexport, Report `research/mastr-pv-leads/report.md`, Run 14.06.) liegt vor. Die fünf offenen Fakten aus der 13.06.-Version §5 sind beantwortet; die teuerste Weiche des Projekts ist damit final entschieden. Bei Widerspruch zur 13.06.-Fassung gilt dieses Dokument.

---

## 1 · Der finale Entscheid in einem Satz
**Der MaStR-Gesamtdatenexport (Option B) wird das Backbone der Pipeline. Die Web-JSON-Einzelabfrage (Option A) wird vom Fundament zum optionalen Echtzeit-Spot-Tool degradiert. Die Adapter-Architektur (Quelle entkoppelt von Verarbeitung) bleibt — R3 bestätigt sie als die richtige Entkopplung.**

Damit ist die 13.06.-Hypothese („Prototyp auf A, B später ergänzen") **invertiert**: B ist nicht mehr „später ergänzbar", sondern primäres Fundament, und A ist nicht mehr Prototyp-Backbone, sondern Beiwerk. Begründung in §2 + §5.

## 2 · Warum B — nicht A (Begründung aus den R3-Fakten)
Vier der fünf Prüfpunkte fallen für B; der fünfte (Frische) war der Haupt-Hebel *für* A — und ist durch R3 **gegen** A aufgelöst:

1. **Frische ist KEIN Argument mehr für A.** Die 13.06.-Sorge war: „Wenn der Export seltener als wöchentlich aktualisiert, untergräbt das das ≤7-Tage-Versprechen → spricht für A." R3: Der Export wird **täglich ~05:00 Uhr** auf den Vortagesstand neu erzeugt. Für eine wöchentliche Kadenz mehr als ausreichend → der einzige Grund, bei A zu bleiben, ist weg.
2. **Der betreiberweite Speicher-Check (P0) verlangt den vollen Betreibergraph.** „Hat dieser Betrieb *irgendwo* einen Speicher?" ist eine globale Aggregation über alle Einheiten je `AnlagenbetreiberMastrNummer`. Der Export liefert diesen Graphen einmalig und lokal joinbar. A müsste den Gesamtbestand de facto rekonstruieren oder pro Lead × Betreiber × Einheitenart zahllose gefilterte Abfragen gegen ein Endpoint mit undokumentierten Limits fahren — **genau der Engpass, der bei 50 Gebieten kippt.** B ist hier nicht nur sauberer, sondern das einzige, das skaliert.
3. **Historie/Post-EEG (T2) ist nur über B erschließbar.** Inbetriebnahme- und EEG-Datum liegen im Export vollständig vor → die Kohorte 2006/2007 ist sauber filterbar. Über A gibt es keine garantierten historischen Stichtage.
4. **Tooling ist reif.** `open-mastr` (Python) lädt den Bulk-Export und schreibt ihn in SQLite/Postgres — aktiv gepflegt (PyPI 0.17.1 vom 13.04.2026, Commit 09.06.2026). Das 30-Tabellen-XML-Parsing übernimmt die Library; der Eigenaufwand ist *ein Library-Call + SQL*, kein Custom-Parser.
5. **Reproduzierbarkeit.** Tägliche/Stichtag-Exporte erlauben Woche-gegen-Woche-Diffs gegen einen lokalen Snapshot → sauber auditierbar und deduplizierbar. A ist eine live-bewegte Sicht ohne offizielle historische Stände.

**Ehrliche Gegenposition (aus dem Report):** Wer nur eine *sehr* schmale regionale Scheibe OHNE Anywhere-Speicher-Check braucht, fährt mit A leichter (serverseitiger Filter + Pagination, kein 3-GB-ZIP, kein 30-Tabellen-Parsing). Das trifft auf **Pilot #1** durchaus zu — siehe Sequenzierung §6. Sobald aber betreiberweiter Speicher-Check + beide Datumsfelder + Reproduzierbarkeit gefordert sind — also genau dieses Produkt in der Skalierung — kippt die Abwägung eindeutig zu B.

## 3 · Die fünf offenen Fakten — jetzt beantwortet (R3)
| # | Frage (13.06.) | Antwort (R3) | Konsequenz | Konfidenz |
|---|---|---|---|---|
| 1 | Frische des Exports? | Täglich ~05:00, Vortagesstand. ZIP ~2,96 GB komprimiert. | Deckt ≤7-Tage-Versprechen voll. **Kein Grund mehr für A.** | hoch |
| 2 | Inbetriebnahmedatum für Post-EEG? | `Inbetriebnahmedatum` (Einheit) **+** `EegInbetriebnahmedatum` (EEG-Anlage, maßgeblich fürs Förderende) vollständig vorhanden. 2006/07 filterbar. | **B ist der einzige Weg zu T2.** | hoch |
| 3 | Speicher-Verknüpfung — über welche ID? | **Betreiber-Weg:** `AnlagenbetreiberMastrNummer` (ABR…) auf PV *und* Speicher, ~95–100 % befüllt → der robuste „Anywhere"-Check. **Co-lokal:** `LokationMaStRNummer` (SEL…) + Direktfelder `GemeinsamRegistrierteSolareinheitMastrNummer` / `SpeicherAmGleichenOrt`. | Betreiberweiter Check (P0) erstmals **sauber, ID-basiert** möglich. ABER: „ohne Speicher" = nur „kein Speicher **gemeldet**" (~9 % Heimspeicher unregistriert; Gewerbe vermutlich besser). | hoch (Mechanik); med (Vollständigkeit co-lokal) |
| 4 | Tooling-Reife (open-mastr)? | `open-mastr` aktiv (0.17.1, Commit 09.06.2026); Bulk → SQLite/Postgres, selektive Tabellen via `data=`, `to_csv`. Kein inkrementelles Update (voller Tagesstand je Lauf). `marktstammdatenregister.dev` ruhend (2023), nur als Schema-Referenz. `bundesAPI/deutschland` hat **kein** MaStR-Modul. | B mit vertretbarem Aufwand betreibbar (1–2 CC-Sessions). | hoch |
| 5 | Registrierungsdatum stabil? | Soll-Konzept: `Registrierungsdatum` bleibt fix; `DatumLetzteAktualisierung` bewegt sich bei Korrekturen. Betreiberwechsel erzeugt KEINE Neuregistrierung. **ABER:** Nachregistrierungspflicht (Frist 31.01.2021) → viele Altanlagen tragen junges Registrierungsdatum. | **`reg_datum` allein ist KEIN Neubau-Beweis.** Immer mit `Inbetriebnahmedatum` kombinieren. (→ §7b) | hoch (Mechanismus); Skala der Nachzügler: not found |

## 4 · Datenmodell-Grundsätze (unverändert gültig — R3 verstärkt sie)
Die sechs Grundsätze der 13.06.-Version bleiben die nicht-verhandelbaren Leitplanken. R3 schärft zwei davon:
1. **Stabile Schlüssel als Primärschlüssel** (Betreiber-Nr. + Einheits-Nr.) — R3 hebt `AnlagenbetreiberMastrNummer` (ABR) zusätzlich zum **Join-Schlüssel für den Speicher-Anywhere-Check** und das Exklusivitäts-Ledger.
2. Quelle entkoppelt (Adapter). 3. Qualifizierungs-Status + Stufe + Stempel am Lead. 
4. **Provenance pro Feld** — R3 ergänzt: beide Datumsfelder (`Registrierungsdatum` + `Inbetriebnahmedatum`) gehören mit Provenance ins Modell, weil die Frische-Aussage sonst nicht belastbar ist.
5. Roh-Snapshot aufbewahren. 6. Lieferung als eigener Zustand.

## 5 · Der ehrliche Delta gegenüber der 13.06.-Hypothese
Die 13.06.-Version empfahl „Hybrid: A jetzt, B später" — **bewusst hedgend auf zwei Unbekannten**: (a) Export-Frische, (b) ob B überhaupt betreibbar ist. R3 hat **beide Unbekannten zugunsten B aufgelöst** (Frische täglich; open-mastr reif). Damit entfällt die Grundlage für „A zuerst". Was bleibt, ist die *Adapter*-Idee — die war nie der Hedge, sondern gute Architektur, und gilt weiter.

## 6 · Build-Sequenzierung — das 27.06.-Gate bleibt geschützt
Der Entscheid für B als Backbone heißt **nicht**, die Demo auf B zu wetten. Entkopplung von End-Zustand und Demo-Pfad:

- **Demo-Fallback (steht):** `clean-v2-CSV` + `make_sample.py` führen den End-to-End-Fluss (Region rein → qualifizierte, angereicherte, geflaggte Liste + Liefer-Mail) heute schon vor. Die Demo beweist das **Konzept**, der schriftliche Pilot beweist **Demand** — keines von beiden braucht B.
- **B-Backbone (Woche 1, via CC):** CC steht den B-Adapter via open-mastr auf (Download → SQLite) + die **ABR-Speicher-Anywhere-Query** als erstes Kern-Stück. Steht es bis 27.06., wird die Demo deutlich stärker (echter betreiberweiter Check, Inbetriebnahme-validierte Frische, T2-Scheibe verfügbar). Slippt es, fällt die Demo sauber auf den CSV-Pfad zurück.
- **Adapter dazwischen:** Verarbeitung/Anreicherung/Lieferung kennen nur das normalisierte Lead-Objekt → die zum 27.06. fertige Quelle (B oder CSV) steckt in denselben Slot.
- **A degradiert** zum *optionalen* Echtzeit-Spot-Tool (einzelner Lead-Status-Recheck am Liefertag). Für v1 nicht erforderlich — der tägliche Export ist für Wochenlieferung frisch genug.

**Guardrail:** B via open-mastr ist *ein Library-Call + SQL* — wenn es sich als mehr als ~2 CC-Sessions entpuppt (z. B. Format-Bruch 01.10.2025, 3-GB-Handling auf dem ZBook), Demo auf CSV fahren und B nach dem Gate fertigstellen. Kein Infra-Goldplating vor dem ersten zahlenden Kunden.

## 7 · Zwei Produkt-Korrekturen, die direkt aus R3 folgen (nicht optional)

### 7a · „ohne Speicher" → exakt „kein Speicher GEMELDET" + ABR-Check statt PLZ-Fuzzy
Der heutige `speicher_check` in make_sample.py ist ein Workaround mit zwei Fehlerquellen: (i) **PLZ-Grenze** — ein Speicher an einem *anderen* Standort desselben Betreibers wird übersehen → falsch-negativ; (ii) **Namens-Fuzzy-Match** (Wort-Set-Schnitt) — brittle bei Schreibvarianten/Rechtsform. Der **ABR-Join** im Export ersetzt beide: ein ID-basierter Group-by über `AnlagenbetreiberMastrNummer` liefert den echten betreiberweiten Check. Das ist exakt der als P0 markierte „betreiberweite Speicher-Check" — R3 macht ihn erstmals sauber möglich.
Gleichzeitig die **Wahrheits-Grenze sauber labeln:** Da ~9 % der (Heim-)Speicher gar nicht/verspätet registriert sind, ist die belegbare Aussage „kein Speicher **gemeldet** (betreiberweit, Stand X)", nicht „kein Speicher". Genau diese Formulierung gehört in Qualitäts-Stempel und Liefer-Mail — die Ehrlichkeit ist Teil der Differenzierung (vgl. Lead-Spec §5), nicht ihr Gegenteil.

### 7b · Inbetriebnahmedatum als Frische-VALIDIERUNG, nicht nur Kürfeld
Der Pitch ist „gerade angemeldet". R3 zeigt: `reg_datum` allein belegt **keine Neuinstallation** — wegen der Nachregistrierung (Frist 2021) können Altanlagen ein junges Registrierungsdatum tragen. Ein Käufer, der anruft und „PV haben wir seit 2015" hört, blamiert sich — das verletzt die Lead-Spec-Leitfrage direkt. **Konsequenz:** `Inbetriebnahmedatum` von Kür zu **Frische-Validierung** hochstufen — für T1 verlangen, dass die Inbetriebnahme nicht Jahre vor der Registrierung liegt; jeden Lead mit großer IBN↔Reg-Lücke flaggen.
*Maßhalten:* Die Nachregistrierungswelle (2019–2021) ist fünf Jahre her; ein Lead mit `reg_datum` 2026-06 ist heute mit hoher Wahrscheinlichkeit ein echter 2026-Neubau. Das Risiko ist real, aber **abnehmend** → behandeln als billige Versicherung (Feld mitführen + flaggen), nicht als Großalarm.

## 8 · Konsequenz für die erste CC-Session (aktualisiert)
- CC baut **zuerst** den B-Adapter via open-mastr (Bulk → SQLite) + die **ABR-Speicher-Anywhere-Query**; das normalisierte Lead-Objekt trägt `Inbetriebnahmedatum` und `EegInbetriebnahmedatum` als Pflichtfelder, `reg_datum` nur noch in Kombination als Frische-Signal.
- Der CSV-Pfad (make_sample.py) bleibt als **Fallback lauffähig** und als Referenz-Implementierung für die Verarbeitungs-Schicht.
- nimble bleibt P2 (Anreicherung), erst nach dem Kern — unverändert.
- Die §4-Grundsätze sind die Leitplanken; Sprache/Struktur (Module vs. CLI) entscheidet CC technisch mit dir.

## 9 · Quellen (R3-Report)
Vollständig in `research/mastr-pv-leads/report.md` (+ notes.md, sources.md). Kern-Belege: BNetzA Webhilfe Datenexport & Live-Download-Seite (täglich 05:00, ZIP-Größe); Dokumentation MaStR Gesamtdatenexport Rev. 26.1.2 (Felder, XSD, ABR/SEL/SEE-Verknüpfung); open-mastr Doku + Repo (Tooling-Recency); MaStR-Newsletter 2019 (Registrierungsdatum-Stabilität); green-energy-law (Nachmeldefrist 31.01.2021); Verbraucherzentrale Ü20 (Förderende = Inbetriebnahme + 20 J.).

## 10 · D2-Lock + Reframe: generisches Backbone + Change-Detection-Engine (Stand 15.06.)
Decision Record `research/mastr-pv-leads/decisions.md` (D2) + `knowledge/expansion-map.md` schärfen diesen Entscheid. Die Adapter-/Backbone-Wahl (B) bleibt; **neu ist die Ausrichtung des Backbones**:

- **Kern-Artefakt = Change-Detection-Engine über wöchentliche Snapshots:** ingest → **diff** vs. letzter Snapshot → klassifiziere Änderungen in Trigger-Typen. Das Produkt ist „Daten **diffen**", nicht „Daten filtern". Jedes Signal (Neuregistrierung · Speicher-Retrofit · Betreiberwechsel · Direktvermarktungs-Schwelle · Status/Stilllegung) ist ein **Diff, kein WHERE**.
- **Snapshot+Diff-Schicht = Eigenbau (= das meiste Eigen-IP):** `open-mastr` baut die Tabellen je Lauf **neu** (kein Inkrement/Diff) → wir wrappen es mit **eigener versionierter Snapshot-Ablage + Diff-Logik**. Stack: **open-mastr → Postgres**; Snapshot-Kadenz **wöchentlich, dated**; Retention dated (auditierbar/reproduzierbar). [Bestätigt §2.5 — Diff war dort schon „nice to have"; jetzt ist er das Produkt.]
- **Backbone GENERISCH bauen — NICHT solar-only:** alle Energieträger + `Lokationen` + EEG-Anlagen + die **GelöschteUndDeaktivierte**- und **Änderungen**-Objekte. Die Expansions-Trigger (expansion-map) hängen alle daran → das Backbone ist die Plattform für die ganze Roadmap, kein PV-Feature.
- **Build-Sequenz mit frühem Win:** **Post-EEG-Signale zuerst shippen** — reine Kohorten-Query (`EegInbetriebnahmedatum`-Jahr + „kein Speicher gemeldet" + Region), **kein Diff-Engine nötig**, direkt nach dem ersten Ingest lieferbar. Danach die Diff-Engine-Trigger (Neuinstallation/Retrofit/Betreiberwechsel). (Ersetzt die §6-Sequenz, wo „T2 verfügbar wenn B steht" stand — T2 ist jetzt der *früheste*, nicht ein Bonus.)
- **Unverändert tragend:** Operator-Graph (ABR) · Freshness-Regel (`Inbetriebnahmedatum`, nie `reg_datum` allein) · Speicher als **Score mit Konfidenz** (~9 % Dunkelziffer).
- **Liefereinheit (D3):** der Diff/Query produziert **Signal-Records** (CLAUDE.md-Signal-Schema), kein Kontakt-Enrichment in v1 (→ Lead-Spec §4 = v2). `make_sample.py`/CSV bleibt Demo-Fallback; die Demo zeigt jetzt Signal-Records (Post-EEG sofort vorführbar).
