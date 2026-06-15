# Stand & Abgleich — GoldenTime (Session 14.–15.06.2026)
**Stand 15.06.2026 · Typ: Momentaufnahme/Analyse für den Konzept-Review — KEIN Owner-Doc.**

> Diese Datei ist ein **datierter Snapshot** zum Abgleich „Ausgangspunkt → Jetzt", nicht der Live-Master.
> Bei Widerspruch gilt **STATE.md** (Owner für Geschäftsstand). Detail-Owner je Thema: `00_DOC-MAP.md`.
> Schwester-Datei: `Roadmap-Board_2026-06-15.md` (Gap-Analyse + sequenzierte Roadmap + offene Calls).

---

## 0 · TL;DR (in 6 Zeilen)
1. **Architektur entschieden** (R3 → Gesamtexport-Backbone, FINAL 14.06.), **Backbone gebaut + getestet** (PULL, 9/9 Tests), dann **Produkt-Reframe D1–D3** (15.06., andere Session).
2. **Genau EINE echte Richtungsänderung:** D3 verschiebt das kontaktzentrierte Lead-Modell (Stufe A/B/C, Anreicherung) auf **v2** — Liefereinheit v1 = **Signal-Record**. Alles andere ist **additiv** (Diff-Engine, generisches Backbone, Trigger-Portfolio, Exklusivität pro Funktion, Compliance-Stub).
3. **Produkt-These verschoben:** von „PV-**filtern**" zu „MaStR-**diffen**" (Change-Detection-Engine = das Eigen-IP).
4. **Code-Stand:** B-Backbone-PULL läuft (open-mastr→SQLite, ABR-Speicher-Anywhere, Trigger T1/T2/T3, Frische-Validierung) — solides Fundament, aber **hinter** dem Reframe-Ziel (generisch, Postgres, Snapshot+Diff, formales Signal-Record-Schema).
5. **Nächster früher Win:** Post-EEG-(T2)-Signal-Shipper — reine Kohorten-Query, **kein Diff-Engine nötig**, sofort nach Ingest lieferbar. Mein Backbone klassifiziert T2 bereits.
6. **Gate:** Berater-Essen ~27.06. · **Ein Vor-Launch-Blocker:** kommerzielle Weiterverbreitung MaStR-Daten (dl-de/by-2.0) prüfen.

---

## 1 · Ausgangspunkt — Richtung beim ersten Prompt dieser Session (Commit `9ef392b`, „Stand 13.06.")
So sah das Projekt zu Beginn dieser Session aus (vor dem R3-Changeset):

| Dimension | Ausgangspunkt |
|---|---|
| **Produkt** | „Kaufmoment" verkaufen: gewerbliche PV **ohne Speicher**, wöchentlich, qualifiziert, **exklusiv pro Region an EINEN Speicher-Anbieter**. |
| **Liefereinheit** | **Angereicherter Kontakt-Lead**: Entscheider + Direktkontakt, **Stufe A/B/C**. ANREICHERN (Domain→Impressum→GF/Tel + Mensch-QA) = **Kern-Pipeline-Schritt**. |
| **Leitfrage (Lead-Spec §0)** | „Kann der Käufer ihn **sofort anrufen**, ohne selbst nachzurecherchieren?" |
| **Datenquelle** | **OFFEN** — Web-JSON vs. MaStR-Gesamtexport. Architektur-Doc 13.06. = „ENTSCHEIDUNGS-RAHMEN, final nach R3". R3 „blockiert finalen Architektur-Entscheid" (so der **damalige** STATE §11 — in meinem R3-Changeset ersetzt). |
| **Exklusivität** | **pro Gebiet** (ein Käufer pro Region). |
| **Käuferzahl** | **1 Funktion** (Speicher-Installateur). |
| **Trigger** | T1/T2/T3 als „Multi-Trigger für denselben Käufer" (T1 Kern, T2 Q4-Upsell, T3 Prüfoption). |
| **Sprint** | 2 Wochen → Berater-Essen ~27.06.; Verkauf + Bau parallel. Funnel: 10 Kaltmails, 0 Antworten. |
| **Code** | `make_sample.py` (CSV-Demo, Speicher-Check per **PLZ+Namens-Fuzzy**) + 208er clean-v2-CSV. Keine versionierte Pipeline. |

---

## 2 · Was in dieser Session passiert ist (Chronologie, 4 Blöcke)

### Block A — R3 eingearbeitet → Architektur-Entscheid FINAL  *(committed `9f13a68`, 14.06.)*
- 8-Schritt-Changeset angewandt: STATE, Lead-Spec, CC-Build-Briefing, Geschäftsmodell-Canvas, make_sample.py-Hinweis.
- **Entscheid:** MaStR-**Gesamtdatenexport = Backbone** (open-mastr → SQLite), Web-JSON nur noch Spot-Tool, Adapter-Architektur bleibt. Alle 5 R3-Fakten zugunsten Export.
- **3 Produkt-Korrekturen:** Speicher-Label exakt „kein Speicher **GEMELDET**" via ABR (PLZ-Fuzzy ersetzt) · `Inbetriebnahmedatum` als Frische-Validierung · `PersonenArt` als Gewerblich-Filter (e.K.-Caveat).
- **`00_DOC-MAP.md`** neu (Single-Source-Ownership + Changeset-Ritual).

### Block B — B-Backbone PULL gebaut  *(committed `96def26`, 14.06.)*
- `02_Daten/pipeline/` als saubere Python-Pipeline: **Export-Adapter** (open-mastr→SQLite), **ABR-Speicher-Anywhere-Query** (3-Wege: kein Speicher gemeldet / Premium anderswo / colocated=Ausschluss), **Normalisierung** (Trigger T1/T2/T3 + Inbetriebnahme-Frische), **CLI** (`inspect`/`build-db`/`leads`), **9/9 Tests** (synthetisches SQLite, ohne 3-GB-Download).
- Technik-Gedächtnis `CLAUDE.md`. Beide Commits **gepusht** (`origin/main`).

### Block C — Produkt-Reframe D1–D3  *(andere Session, UNCOMMITTED, 15.06.)*
Decision Record `research/mastr-pv-leads/decisions.md`:
- **D1** — beide Wedges parallel (Neuinstallation **und** Post-EEG-Retrofit), eine Pipeline, zwei Signallinien.
- **D2** — Bulk-Backbone sofort, **generisch** gebaut (alle Energieträger, nicht solar-only), open-mastr→**Postgres**. Kern = **Change-Detection-Engine** (Snapshot+Diff = Eigen-IP).
- **D3** — Liefereinheit = **Signal-Record** (Käufer macht Outreach selbst) → Kontakt-Enrichment/Outreach/Consent **v2-deferred**.

### Block D — Expansionszulagen eingearbeitet  *(STATE §12, no-regret)*
Aus `knowledge/expansion-map.md` (Achsen A–F): Diff-Trigger-Portfolio **T1–T6 + ≥100-kWp/DV-Flag**, **Exklusivität pro Funktion**, **Compliance-Stub** (Redistributions-Lizenz), **3 strategische Essen-Fragen** (Fragenkatalog §F). Geparkt (post-Gate): Kanäle (R2), Geografien (R4: AT negativ; FR/IT/CH), EV-CPO-Adapter (Ladesäulenregister).

---

## 3 · Der Abgleich — die Richtungs-Deltas (Ausgangspunkt → Jetzt)

| # | Dimension | Ausgangspunkt (13./14.06.) | Jetzt (15.06., Reframe) | Bedeutung |
|---|---|---|---|---|
| 1 | **Architektur** | offen (Web-JSON vs. Export), R3 pending | **FINAL: Gesamtexport-Backbone** (open-mastr) | Teuerste Weiche geschlossen; Bau entblockt |
| 2 | **Kern-IP / Produkt-These** | „Daten **filtern**" (WHERE auf frischem Pull) | „Daten **diffen**" — **Change-Detection-Engine** über Wochen-Snapshots | Jedes Signal ist ein **Diff, kein WHERE**; Snapshot+Diff = das verteidigbare Eigen-IP |
| 3 | **Liefereinheit (D3)** ⚠ | angereicherter Kontakt-Lead (Stufe A/B/C) | **Signal-Record** (Entity·Trigger·Evidenz-URL·Region·Datum·Konfidenz·Buy-Relevanz); Käufer kontaktiert selbst | **Die eine echte Richtungsänderung.** Enrichment/A-B-C → **v2** (Reasoning erhalten, nur sequenziert). Senkt UWG §7/DSGVO-Haftung, beschleunigt Launch |
| 4 | **Backbone-Scope** | solar PV ohne Speicher | **generisch**: alle Energieträger + Lokationen + EEG + GelöschteUndDeaktivierte + Änderungen | Backbone = Plattform fürs ganze Trigger-Portfolio, kein PV-Feature |
| 5 | **Trigger** | T1/T2/T3 für denselben Käufer | **Portfolio T1–T6** + ≥100-kWp/DV-Flag (T4 Retrofit, T5 Betreiberwechsel, T6 Stilllegung) | Roadmap statt Einzelprodukt; T2 wird vom „Bonus" zum **frühesten Ship** |
| 6 | **Käuferzahl / Exklusivität** | 1 Funktion, Exklusivität **pro Gebiet** | ≥2 Funktionen, Exklusivität **pro Funktion × Gebiet** | Löst die **Dichte-Ökonomie**: dünnes Gebiet an mehrere nicht-konkurrierende Funktionen, Grenzkosten ~0 |
| 7 | **Stack** | (impliz. SQLite, Build ist SQLite) | **open-mastr → Postgres** (D2) | Stack-Detail; mein Code ist SQLite-first → Migrationspfad offen |
| 8 | **Compliance** | implizit (dl-de/by-2.0 im Mail-Fuß) | **benannter Vor-Launch-Blocker**: kommerzielle Weiterverbreitung (04_Compliance) | Überlebt D3; kein Code-Blocker, aber Launch-Blocker |
| 9 | **Build-Sequenz** | Pull → Qualifizieren → **Anreichern** | Pull → Qualifizieren → **Snapshot+Diff** (Post-EEG zuerst), Anreichern = v2 | Frühester Win = T2-Kohorte (kein Diff nötig) |

**Lesart:** 8 von 9 Deltas sind **additiv/schärfend** (Architektur bestätigt, Scope/Trigger/Käufer/Compliance erweitert). **Nur Delta 3 (D3) ist eine echte inhaltliche Korrektur** am Bestands-Konzept — und auch die löscht nichts, sondern sequenziert (A/B/C bleibt als v2-Design in Lead-Spec §4 erhalten).

---

## 4 · Ist-Stand konkret

### 4.1 · Dokumente (Konzept)
- **Committed (gepusht):** R3-Changeset + DOC-MAP (`9f13a68`), B-Backbone + CLAUDE.md (`96def26`).
- **Uncommitted (Reframe, im Working Tree):** 8 Docs geändert — STATE (§0/§1/§4/§6/§7/§8/§9 + neu **§12**), Architektur-Doc (neu **§10**), Lead-Spec (Reframe-Banner, §4→v2, §5 v1-Signal-Stempel, neu **§7d** Trigger-Portfolio, §7b Hebel 4), Sprint-Plan, Pricing (neu **§7**), Vertriebs-Mechanik (§2/§4/§5), Fragenkatalog (**§F**), DOC-MAP (Owner-Zeilen). + 2 neue Dateien: `04_Compliance/Datenlizenz-und-Provenance.md`, `research/mastr-pv-leads/decisions.md` (untracked).
- **Konsistenz:** Single-Source-Ownership gewahrt; STATE verweist auf Owner-Docs, dupliziert nicht. **Keine offene Drift** mehr zwischen STATE und decisions.md (Reframe in beide Richtungen eingearbeitet).

### 4.2 · Code (`02_Daten/pipeline/`, committed `96def26`)
| Baustein | Status | Reframe-Lücke |
|---|---|---|
| `export_adapter.py` (open-mastr→SQLite) | ✅ Code steht, **noch kein echter 3-GB-Lauf** | Postgres-Variante (D2); echter `build-db` + `inspect`-Verifikation auf ZBook |
| `speicher_check.py` (ABR-Anywhere, 3-Wege) | ✅ getestet | trägt unverändert (Reframe bestätigt ABR-Operator-Graph) |
| `normalize.py` (Trigger T1/T2/T3 + Frische) | ✅ getestet | nur T1–T3; **T4–T6** + ≥100-kWp/DV-Flag fehlen; **Output ist Lead-Dict, kein formales Signal-Record-Schema** (Evidenz-URL/Konfidenz/Buy-Relevanz fehlen) |
| `cli.py` (`inspect`/`build-db`/`leads`) | ✅ | `leads` = Filter/Klassifikation, **kein Diff-Modus** |
| `tests/` | ✅ 9/9 grün | nur Klassifikations-Logik |
| **Snapshot+Diff-Engine** | ❌ **nicht vorhanden** | das Kern-IP des Reframes (D2) — Eigenbau um open-mastr |
| **Generisches Multi-Carrier-Backbone** | ❌ solar+storage+location+market | alle Energieträger + GelöschteUndDeaktivierte + Änderungen |
| **Signal-Record-Output** | ⚠ teilweise (trigger_typ/speicher_status da) | Evidenz-URL (MaStR-Einheits-URL), Konfidenz-Score, Buy-Relevanz-Zeile |

**Fazit Code:** der PULL-Schritt + der betreiberweite Speicher-Check (das technisch Schwierigste) **steht und ist getestet**. Das Fundament trägt den Reframe — die Lücke ist additiv (Diff-Engine, Generik, Signal-Schema), kein Umbau.

### 4.3 · Research
R3-Report (`mastr-pv-leads/report.md` + notes/sources), Wissensbasis (`knowledge/mastr-buy-signals.md`, `knowledge/expansion-map.md`), Decision Record (`decisions.md`), Expansions-Report (`expansion-map/`). Alle committed außer `decisions.md` (untracked).

### 4.4 · Git
- `origin/main` = `96def26` (R3 + Build, gepusht).
- **Pending im Working Tree:** 8 Reframe-Docs + 2 neue Dateien — **noch nicht committet** (Konzept-Session folgt dem PUSH_ANLEITUNG-/Changeset-Ritual). Vorgeschlagene Commit-Message liegt vor.
- **Diese Analyse** (`Stand-und-Abgleich` + `Roadmap-Board`) ebenfalls neu/uncommitted.

---

## 5 · Gegencheck D3 — Enrichment + Stufe A/B/C wirklich nach v2? *(der Punkt, den du sehen wolltest)*

**Die Spannung:** Die ursprüngliche Leitfrage (Lead-Spec §0) war „Käufer kann **sofort anrufen, ohne nachzurecherchieren**" — getragen vom angereicherten, anrufbaren Lead. D3 liefert nur das **Signal** (ohne Kontaktdaten) → der Käufer recherchiert den Kontakt selbst. Auf den ersten Blick **schwächt** das die Kern-Value-Prop.

**Wofür D3 trotzdem spricht (überzeugend):**
1. **Haftung** — der mit Abstand stärkste Grund unter deinen BPV-Bedingungen (§9): Signal-only verlagert UWG §7 (B2B-Erstkontakt) + DSGVO-Outreach auf den **Käufer** (eigene Rechtsbasis/Kundenbeziehung). Für einen Solo-Nebenerwerb ist „keine Outreach-Haftung bei uns" Gold wert.
2. **Tempo/Schlankheit** — Enrichment (Impressum→GF/Tel, Mensch-QA) war der **rauschende, langsame** Teil (gemessen GF 3/5, Tel 3/5). Weglassen = schnellster Launch, v.a. die **Post-EEG-Kohorte ist ohne Enrichment sofort lieferbar**.
3. **Der Moat ist NICHT die Kontaktinfo** — Impressum kann jeder scrapen. Verteidigbar sind **Frische + Diff-Engine + Filterschärfe + Exklusivität pro Funktion + Tempo**. D3 lässt den Moat unangetastet.
4. **B2B-Käufer haben eigenen Vertrieb** — ein präzises, frisches, exklusives, qualifiziertes Signal (Firma X hat gerade Y kWp PV ohne Speicher in deinem Gebiet gemeldet, Evidenz-URL) ist hochgradig handlungsfähig; den Kontakt findet der Außendienst in Minuten.

**Risiken (ehrlich):**
- **R1 — wahrgenommener Wert / Preis:** Signal-only kann Richtung „Daten-Feed" rutschen und weniger Preis tragen als ein anruffertiger Lead. Gegenmittel (Pricing §7): „wir verkaufen **Timing + Exklusivität**, nicht Daten" + Exklusivität pro Funktion + Frische-Framing. **Aber: unbewiesen.**
- **R2 — Funnel-Wechsel:** Die 10 Discovery-Mails warben sinngemäß mit „Kostprobe" (eher kontaktnah). v1 = Signal-only ändert, was die Prospects bewerten. Muss am Essen/erster LOI getestet werden.
- **R3 — „ohne Nachrecherche" minimal angekratzt:** abfedern, indem das v1-Signal **maximal handlungsfähig** ist (eindeutige Entity-Identifikation + Evidenz-URL + 1 Zeile Buy-Relevanz).
- **R4 — e.K./natürliche Personen** bleiben auch im Signal ein Compliance-Sonderfall (Redistribution).

**Verdikt:** **D3 ist eine tragfähige Sequenzierung, kein strategischer Rückzug** — vorausgesetzt zwei Annahmen werden **am 27.06.-Essen / an der ersten LOI validiert**: (a) die frühen Käufer-Funktionen (Speicher-Installateur, Direktvermarkter) **akzeptieren Signal-only** und zahlen Retainer-Niveau; (b) das Signal ist für sie **ohne unsere Kontaktdaten handlungsfähig**. Nichts wird verworfen (A/B/C bleibt v2-Design), die Haftung sinkt materiell, der Moat ist enrichment-unabhängig.

**Empfehlung:** **D3 für v1 bestätigen** — aber „Signal-only-Akzeptanz + WTP" zur **expliziten Test-Frage** am Essen machen und den v1-Scope an **mindestens eine LOI knüpfen, die Signal-only akzeptiert**. Falls du anrufbare Leads als v1-Kern willst: sag es, dann wird D3 zurückgedreht (Enrichment zurück in v1) — Kosten: langsamerer Launch + Outreach-Haftung wieder bei uns.

---

## 6 · Was das Konzept voranbringt (Synthese)
Aus **„PV-Filter-Produkt mit Kontakt-Anreicherung"** wird ein belegtes, sequenziertes **Plattform-Konzept**:
generische **Diff-Engine** (das IP) → **Post-EEG als Tag-1-Ship** → **Trigger-Portfolio** als Roadmap → **zwei exklusive Käufer-Funktionen pro Gebiet** (löst die Dichte-Ökonomie) → schlankerer, **haftungsärmerer Launch** (D3) → **ein einziger benannter Vor-Launch-Blocker** (Redistributions-Lizenz). Der Code-Stand (PULL + ABR-Check getestet) trägt dieses Konzept ohne Umbau.

➡ **Konkrete Lücken, Sequenz und deine offenen Calls: siehe `Roadmap-Board_2026-06-15.md`.**
