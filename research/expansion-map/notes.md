# Notes — expansion-map

_Run: 2026-06-14 · Mode: deep-research (Landkarte/Backlog) · Slug: expansion-map_

## Phase 1 — Scope & decomposition

**Restated question.** Baue eine **dauerhafte, referenzierbare Expansions-Landkarte** (Backlog) für das
Geschäft "GoldenTime" — die geordnete Optionsliste, in welche Richtungen sich das *bestehende* Modell
(register-abgeleitete, exklusiv-regionale, datierte B2B-Kaufsignal-Leads) künftig ausweiten lässt, **ohne
Pivot**. Bewusst **breit**, je Option **knapp aber belegt**; Detailtiefe bleibt späteren `/deepen`-Läufen
pro Achse. Kein einmaliger Faktencheck, sondern die Liste, auf die zurückgegriffen wird, sobald Prototyp/Gate
stehen.

**Gegeben (nicht neu herleiten — aus [mastr-pv-leads](../mastr-pv-leads/report.md) + Auftragsbrief):**
- Kernprodukt = frisch angemeldete **gewerbliche PV ohne gemeldeten Speicher** (Trigger T1), aus dem
  MaStR-Gesamtdatenexport, wöchentlich, **exklusiv pro Region an EINEN** Gewerbespeicher-Installateur
  (200–500 €/Gebiet/Monat oder 10–25 €/exkl. Lead). T2 = Post-EEG-Kohorte (2006→Ende 2026, 2007→Ende 2027).
- Asset/Moat = laufende Pull→Qualify→Enrich→Deliver-Pipeline auf dem **MaStR-Gesamtexport** (open-mastr →
  SQLite/Postgres; voller Betreibergraph via `AnlagenbetreiberMastrNummer`; historische `Inbetriebnahmedaten`;
  Woche-für-Woche diff-bar). **Grenzkosten/Zusatzgebiet ~0.** Verteidigung: Frische + Filterschärfe +
  Anreicherung + vertragliche Gebiets-Exklusivität.
- Constraints: **Solo-Gründer, ~4 h/Woche, BPV** (nur Dienste aus öffentlich zugänglichen Daten; keine
  Kunden aus dem Bundesumfeld).
- Gotchas (in jede Bewertung tragen): `Registrierungsdatum` ≠ neu gebaut → Frische am `Inbetriebnahmedatum`
  prüfen; "ohne Speicher" = "kein Speicher gemeldet"; vertrauliche Felder natürlicher Personen sind aus dem
  Export ausgeschlossen → Privathaushalte im Export nur eingeschränkt, B2B/juristische Personen greifbar.

**Decomposition — 6 Achsen / 9 Forschungs-Einheiten (parallel verarbeitet):**
- **A1** — weitere Erzeugungs-/Bestands-Trigger im MaStR (Leistungserhöhung, Speicher-Nachrüstung, neue
  Wind/Biogas/BHKW, Betreiberwechsel, Stilllegung): welches Feld, welcher Käufer, warum jetzt.
- **A2** — verbrauchsseitige & §14a-Trigger im MaStR (Wärmepumpe/Wallbox/steuerbare Verbrauchseinrichtungen,
  EinheitenStromVerbraucher) + Abgrenzung Ladesäulenregister; sind diese im *öffentlichen* Export?
- **B1** — neue Käufersegmente für das *Kernsignal* (O&M/Monitoring/Reinigung, Finanzierung/Leasing/PPA,
  Direktvermarkter, Messstellenbetreiber, konkurrierende EPC, Wallbox/WP-Cross-Sell, Energieberater,
  OT-Security) + Zahlungsbereitschaft + nicht-konkurrierende Mehrfachverwertung pro Gebiet.
- **C1** — wiederholbare Kanäle zur Käufer-Gewinnung (Hersteller-Co-Selling, Verbände, Fachmedien,
  Lead-Magnet, Affiliate, Messen, White-Label, LinkedIn). **R2-Scheibe, nur Option-Tiefe.**
- **D1** — nicht-DE öffentliche, maschinenlesbare Register (AT, CH, NL, FR, IT, ES, …). **R4-Scheibe.**
- **D2** — angrenzende DE-Register (Bauanträge, Förderzusagen, Vergabe/TED, Handelsregister, Gewerbe-
  anmeldungen, Ladesäulenregister) als register-abgeleitetes datiertes Kaufsignal.
- **E1** — Produktisierung/Geschäftsmodell (Alert-Abo, EaaS, Daten-API, White-Label, CRM-Integration,
  Gebiets-Auktion, gestufte Frische, Rev-Share, Daten-Kooperative) + Analoga (Dealfront/Implisense/…).
- **F1** — Blue-Ocean: echtes Job-to-be-done + völlig andere Branchen für dieselbe Engine (Wärmepumpen,
  EV-CPOs, Dachdecker, Agri/Biogas, Meta-Horizontale) — je 1 Kill-Frage.
- **X1** — Quer-Check Wettbewerb-als-Constraint / "gibt es schon" (MaStR-/register-abgeleitete Lead-Produkte,
  PV-Lead-Marktplätze, B2B-Trigger-Daten-Anbieter). **R1-Referenz, nicht duplizieren.**

**Abgrenzung zu bestehenden Aufträgen:** Dies ist die **strategische Superset-Landkarte**. R1 (Wettbewerb)
& R5 (Recht) nur als Constraint (X1 liefert nur den "gibt-es-schon"-Feed). R2 (Kanäle → C1) und R4 (AT → D1)
nur auf Option-Tiefe.

**Success criteria:** jede Achse mit ≥1 belegter Option im Backlog; jede Option mit fit/aufwand/nachfrage-
beleg/revisit-trigger/konfidenz + white-space-/exists-Markierung; Top-3–5 nach Hebel sortiert (Solo/4h/BPV
+ Berater-Essen ~27.06). **Stop condition:** alle 9 Einheiten ausgewertet, Fact-Checker-Issues behoben/
abgewertet, Landkarte als `knowledge/expansion-map.md` destilliert + im Index verlinkt.

## Phase 2 — Search strategy
Pro Einheit ein **source-scout** (Tavily/WebSearch, breit; offizielle Register/Doku direkt) → **deep-reader**
(`deep-research`-Agent, Firecrawl/Tavily-extract/WebFetch auf 4–7 Top-Kandidaten + 1–2 Bestätigungs-Suchen).
Primär > sekundär. Bekannte Primärquellen wiederverwendet: offizielle MaStR-Doku-PDF + MaStR-Hilfe (A1/A2),
BNetzA-Ladesäulenregister & TED/Handelsregister (D2). Orchestrator synthetisiert (Phase 6), Fact-Checker
red-teamt (Phase 7) — beides nicht im Scout/Read-Workflow.

## Queries / Dispatch (Reproduzierbarkeit)
Phase 3–5 als Hintergrund-Workflow `expansion-map-research` (9 Einheiten, Scout→Read-Pipeline, Run
`wf_857118bc-760`). Jeder Scout/Reader logt seine eigenen Tavily/Firecrawl/WebFetch-Queries automatisch in
`_sources/ledger.log`. Orchestrator-Seeds = die 9 Einheiten-Briefs oben (A1–F1 + X1).

## Phase 3–5 Rücklauf (Workflow `wf_857118bc-760`)
18 Subagents, 9/9 Digests, 61 vorgeschlagene Backlog-Optionen, ~103 Quellen (94 unique). Ein F1-Scout
stallte einmal (227 s) → automatisch retry, ok. Digests strukturiert (findings+Zitate+Status+Backlog-Zeilen).

## Phase 6 — Synthese (Orchestrator)
61 Roh-Optionen → **42 distinkte Vektoren** konsolidiert (Cross-Achsen-Dubletten gemerged: EV-CPO D2+F;
Biogas A+F; WP-Kill A2+F; Meta-Horizontale F+X1; Permit/Dachdecker D2+F). Eine gescorte Backlog-Tabelle
nach Hebel sortiert; **Top-5 erste Welle**: B-Mehrfachverwertung(+DV) · E-Kaufsignal-Radar · A-Speicher-
Retrofit/Post-EEG · D/F-EV-CPO(Ladesäulenregister) · C-Hersteller-Co-Selling+BSW (getaktet auf Intersolar
23.–25.06., 2 Tage vor Berater-Essen ~27.06.). White-Space-Verdikt (X1) als Querschnitt; 3 explizite Kills
(WP-aus-MaStR, AT E-Control, Gewerbeanmeldungen). R1/R5 nur als Constraint, R2=C/R4=D1 nur Option-Tiefe.

## Phase 7 — Fact-Check (4 parallele fact-checker, je Achsen-Slice)
Gesamt-Verdikt **fix-then-ship**: KEINE critical; alle load-bearing Zitate real & scope-treu; alle 3 Kills
sauber belegt (z. T. durch unabhängige Gegen-Recherche gehärtet). Behobene Issues:
- MAJOR: „~8.500 Handwerker" stand NICHT auf der zitierten Solarwatt-Seite [31] → ersetzt durch belegtes
  „größtes Solateur-Netzwerk Europas" (gestreckte Zahl entfernt — CLAUDE.md-Regel 1).
- MAJOR: e2m [19] „100 kW" = Redispatch 2.0, NICHT DV-Pflicht → Doppel-Attribution korrigiert; DV-Pflicht
  ≥100 kWp trägt jetzt allein [18], e2m nur als „adressiert Segment aktiv".
- MAJOR: OffeneRegister [53] „veraltet" durch Quelle selbst widersprochen + „SQL-API/SQLite" nicht
  verifizierbar → umformuliert zu „Bulk-JSONL, via Gazette gepflegt, Aktualität unklar" (report + sources.md).
- MINOR: White-Space-Verdikt entschärft („kein *gefundener* Anbieter", Negativbeleg); ecomento 196.353 =
  Stand 1.2.2026 (nicht 3/2026); CH-Feld „Inbetriebnahme/Anlagengenauigkeit" als unverifiziert markiert;
  Leospardo Voll-Exklusiv = Aufpreis; §14a-TL;DR um „Speicher dagegen im MaStR" ergänzt; #29 Aufstockung als
  Inferenz markiert; open-MaStR AGPL-3.0 + DV-Schwellen-Stabilität (Revisit/Uncertainty) ergänzt.

## Dropped / schwach
- Enrichment-Pro-Record-Preise, Belkins Pay-per-Appointment, sales-mind.ai White-Label, LSE-Coop-Kritik (E1)
  — nur Scout-Annotation, nicht deep-gelesen → als „spekulativ" geführt, nicht tragend zitiert.
- NL/ES/BE/PL/IE-Register (D1) — Scout-Annotationen, kein Deep-Read → „parken".
- §14a-WP/Wallbox-, AT-E-Control-, Gewerbeanmeldungs-Trigger → als ⚫ Kill dokumentiert (Negativbefund ist Ergebnis).

## Stop-Bedingung erfüllt
Alle 9 Einheiten ausgewertet; jede Achse mit belegten Backlog-Optionen; Fact-Checker-Issues behoben/abgewertet;
Landkarte als `knowledge/expansion-map.md` destilliert + in `knowledge/index.md` verlinkt; `## Quellen` vorhanden.
