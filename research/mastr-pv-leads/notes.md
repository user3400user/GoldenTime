# Notes — mastr-pv-leads

_Run: 2026-06-14 · Mode: deep-research · Slug: mastr-pv-leads_

## Phase 1 — Scope & decomposition

**Restated question.** A lead-gen product wants to identify, **weekly**, newly registered **commercial PV
installations without storage** in Germany, regionally filtered, from the Bundesnetzagentur's
Marktstammdatenregister (MaStR). Decide whether to build on the **Gesamtdatenexport** (full bulk export) or
on the **Web-JSON single query** (the public website's paginated JSON). Answer 5 sub-questions, then give a
clear recommendation with justification.

**Sub-questions (claims to support with sources):**
- **SQ1 — Bezugsweg & Format.** How to obtain the full export (not the web JSON). Format (XML/CSV/ZIP),
  scope (file size, unit count), update frequency. Is there an official download link / API for the full stock?
- **SQ2 — Tooling.** open-mastr (Python), marktstammdatenregister.dev, bundesAPI/deutschland: what they do,
  recency (last commit), which fits weekly filtered processing.
- **SQ3 — Historie & Post-EEG.** Does the export carry historical commissioning dates? Which field
  (Inbetriebnahmedatum)? Can the 2006/2007 commissioning cohort (end of 20-yr EEG support) be filtered?
- **SQ4 — Speicher-Verknüpfung (critical).** How is a separately registered battery storage linked to its
  operator / to the PV unit? Operator MaStR-Nr (Anlagenbetreiber) vs. Lokation-ID vs. not reliable? Goal:
  detect whether an operator has a storage *anywhere*, not only at the PV unit.
- **SQ5 — Registrierungsdatum-Stabilität.** Is a unit's Registrierungsdatum stable when the operator later
  corrects data, or can an old plant resurface as "new"? (Avoid selling old plants as fresh.) Related risk:
  late registration (Inbetriebnahme old, Registrierung recent).
- **SQ6 — Recommendation (synthesis, orchestrator).** Gesamtexport pipeline vs. Web-JSON for a weekly,
  regionally filtered lead product — justified from SQ1–SQ5.

**Already known (must still verify via sources):** MaStR run by BNetzA; full export is a large ZIP of XML;
open-mastr parses it; Lokation links co-located units; Registrierungsdatum ≠ Inbetriebnahmedatum; late
registration is a real confounder. All of this needs a real cited source before it enters the report.

**Success criteria:** each SQ has ≥2 independent sources OR is explicitly marked "not found"; field names for
commissioning date, registration date, operator number and location number are confirmed against a primary or
authoritative source; tool recency taken from the actual repo. **Stop condition:** all six met, fact-checker
issues resolved/downgraded.

## Phase 2 — Search strategy (tools per SQ)

- SQ1: Tavily/WebSearch for "Gesamtdatenexport marktstammdatenregister"; Firecrawl/WebFetch on the official
  download + help pages (marktstammdatenregister.de, hilfe.marktstammdatenregister.de).
- SQ2: GitHub repos (OpenEnergyPlatform/open-MaStR, bundesAPI/deutschland), ReadTheDocs, marktstammdatenregister.dev;
  WebFetch repo pages for last-commit dates.
- SQ3: open-mastr docs / official data-model docs for field `Inbetriebnahmedatum`, EEG tables; EEG 20-yr rule.
- SQ4: official MaStR help on "Lokation", open-mastr table schema (EinheitenStromSpeicher, LokationMastrNummer,
  AnlagenbetreiberMastrNummer); community write-ups on PV+storage linkage reliability.
- SQ5: official MaStR FAQ/help on Registrierungsdatum vs. Inbetriebnahmedatum vs. letzte Aktualisierung;
  reporting on late registration ("Nachregistrierung"/"verspätete Registrierung").

## Queries run (reproducibility log)
Orchestrator seeds handed to 5 parallel source-scouts (Phase 3, 2026-06-14); each scout logged its own
Tavily/WebSearch queries (see ledger). Representative seeds:
- SQ1: "Marktstammdatenregister Gesamtdatenexport download / XML ZIP Größe / Aktualisierung Häufigkeit"
- SQ2: "open-mastr github / readthedocs bulk", "marktstammdatenregister.dev github sqlite", "bundesAPI deutschland marktstammdaten"
- SQ3: "MaStR Inbetriebnahmedatum Gesamtdatenexport", "EegInbetriebnahmedatum AnlagenEegSolar", "ausgeförderte PV 20 Jahre 2006 2007"
- SQ4: "MaStR Lokation LokationMastrNummer Speicher PV", "EinheitenStromSpeicher", "Batteriespeicher PV Verknüpfung"
- SQ5: "Registrierungsdatum Inbetriebnahmedatum Unterschied", "MaStR Registrierungsdatum Korrektur", "verspätete Registrierung Frist Bestandsanlagen"
- Orchestrator Bash cross-check: GitHub API `/commits`,`/releases/latest` + PyPI JSON for open-mastr, marktstammdatenregister-dev/mastr, bundesAPI/deutschland, bundesAPI/marktstammdaten-api.

## Phase 5 deep-read outcome (10 readers)
Keystone PDF (Rev 26.1.2, 11.06.2026) read page-by-page → all field names confirmed first-hand. open-mastr
docs + GitHub/PyPI confirm capabilities + recency. RWTH (2203.06762) + data-quality (2304.10581) papers read
in full for reliability. 2019 newsletter recovered via Wayback (live 404). All digests returned with quotes.

## Phase 7 fact-check outcome (verdict: fix-then-ship)
- Field names: ZERO hallucinations — every name/type/prefix/definition matches the official PDF (top risk, clean).
- Tool recency, SQ1 facts, reliability numbers, EEG timing, late-reg deadline: all VERIFIED verbatim/in-context.
- Self-correction confirmed correct: rejected scout's "~15% PV mislocated" (real: 0.5–2% wrong present coords +
  ~95% missing coords; 21.3% = power-density plausibility, not location) [14].
- **One MAJOR over-reach FIXED:** claimed web-JSON has a "begrenzter Feldumfang" — but [9]'s OpenAPI `Entry`
  schema exposes AnlagenbetreiberMaStRNummer, AnlagenbetreiberPersonenArt, EinheitRegistrierungsdatum,
  InbetriebnahmeDatum, EegInbetriebnahmeDatum, DatumLetzteAktualisierung. Re-anchored the recommendation on
  operator-wide aggregation + reproducibility + stale tooling (still robust). Resolved the related open question.
- Minor: SQ5 EEG-Meldedatum-vs-Registrierungsdatum nuance already disclosed; tightened the field-table note.

## Dropped / weak sources
- Zenodo open-MaStR mirrors (14843222 / 8225106 / 10200980) — dated snapshots; superseded by live official pages.
- Fraunhofer ISE storage study, Clearingstelle/C.A.R.M.E.N./Nürnberg/photovoltaik-bw, de.wikipedia, photovoltaikforum,
  topagrar "~150k" figure — tertiary/forum or redundant; "~150.000 missed deadline" NOT used (unverified).
- "~15% PV mislocated" — rejected (see above).

## Phase N+1 (deepen, 2026-06-14) — gaps, methods, reproducible queries
Gaps: G1 Web-JSON caps · G2 Lokation/Nummernkonzept · G3 empirical co-location · G4 Post-EEG cohort · G5 counts+operator-type.
Wave: 2 scouts (Lokation/Nummernkonzept; cohort/totals) + 2 Bash agents (Datasette; live web-JSON). Datasette host DOWN
(L7 unresponsive from 6 vantage points incl. Firecrawl/Tavily) → G3 not measured. Live measurement done by orchestrator.

### Reproducible live queries — MaStR public JSON (gemessen 2026-06-14)
Endpoint: https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetErweiterteOeffentlicheEinheitStromerzeugung
Shape {Data, Total, AggregateResults, Errors}; read `Total` with pageSize=1. Filter DSL = Telerik/Kendo `Spalte~op~'Wert'`, join `~and~`.
Catalog: Energieträger Solar=2495, Speicher=2496; Betriebs-Status In Betrieb=35. Working date filter: column
"Inbetriebnahmedatum der Einheit", operators ~gt~ / ~lt~, ISO 'YYYY-MM-DD' (bounds one day outside the year);
~ge~/~gte~ and DE date were silently ignored (returned full count).
  curl -s -G "$BASE" --data-urlencode 'sort=' --data-urlencode 'page=1' --data-urlencode 'pageSize=1' --data-urlencode "filter=Energieträger~eq~'2495'"
Measured Totals:
- all gen units (empty filter): 8,954,450
- solar 2495: 6,204,541 ; solar In Betrieb: 6,058,494
- storage 2496: 2,580,425 ; storage In Betrieb: 2,544,621
- solar by Inbetriebnahmejahr (filter Inbetriebnahmedatum der Einheit~gt~'(Y-1)-12-31'~and~..~lt~'(Y+1)-01-01'):
  2000=9,308·2001=21,940·2004=47,158·2005=67,185·2006=63,807(InB 63,095)·2007=76,827(InB 76,456)·2008=115,345·
  2009=182,219·2010=258,052·2011=260,128·2012=173,939
- cross-checks OK: solar→6,204,541; 2006→63,807.
Filter-metadata endpoint: .../GetFilterColumnsErweiterteOeffentlicheEinheitStromerzeugung (85 cols; date type "date";
Energieträger/Betriebs-Status "multidropdown"; "MaStR-Nr. der Lokation"/"…Speichereinheit" type "mastrnummer";
NO boolean "solar-has-colocated-storage" filter → G3 not expressible via this endpoint).

### Datasette co-location SQL (ready when ds.marktstammdatenregister.dev returns)
.../Marktstammdatenregister.json?_shape=array&_timelimit=20000&sql=
  SELECT COUNT(*) FROM EinheitStromSpeicher s WHERE s.LokationMastrNummer<>'' AND s.LokationMastrNummer IN (SELECT LokationMastrNummer FROM EinheitSolar)
  denom: SELECT COUNT(*) FROM EinheitStromSpeicher WHERE LokationMastrNummer<>''
  + SpeicherAmGleichenOrt rate; Personenart split via EinheitSolar⋈Marktakteur.

### G2 docs + fact-check
§14 MaStRV (gesetze-im-internet/buzer): Stromerzeugungslokation = "eine oder mehrere elektrisch verbundene
Stromerzeugungseinheiten … über einen oder mehrere Netzanschlusspunkte". Nummernkonzept: SEE/SEL/SSE/ABR/SNB +
structure (3 letters + version '9' + 10 digits + check digit). Fact-check N+1 verdict SHIP; fixes applied:
G4 cohort labelled unit-Inbetriebnahmedatum proxy vs EegInbetriebnahmedatum; TL;DR "in Stichprobe kein Cap";
§14 framing operational; "~66.000" corroborated by Verbraucherzentrale [19].

## C1 deep-reader run (2026-06-14) — Käufer-Gewinnungskanäle (R2-Scheibe, Option-Tiefe)
Tooling note: Firecrawl + Tavily keys waren UNAUTHORIZED (401/Invalid token) -> Fallback auf WebFetch + WebSearch (built-in). Reichweite daher leicht reduziert; einzelne PDFs (SWW-Mediadaten) nicht maschinenlesbar geparst.
Gelesene Primaerquellen (WebFetch):
- tesvolt.com/de/partner/partnerprogramm.html — Stufen + "Zugang zu Projektanfragen"
- solarwatt.de/fachpartner/solarwatt-partner — "Vorqualifizierte Leads"
- fenecon.de/fenecon-gewerbebetriebe — "ausschliesslich ueber Grosshandelspartner und Installateure" + Vermittlung
- solarwirtschaft.de/dabei-sein/schnuppermitgliedschaft — "sechs Monate kostenlos", ">1.000 ... Unternehmen"
- sungrowpower.com/de/de/partners — "Werden Sie ein Sungrow-Installateur" (kein Lead-Sharing belegt)
- intersolar.de/exhibition-quick-facts — "June 23-25, 2026", "100,000+ ... in total"
- daa.net/leads-kaufen -> taptaphome.com/de/ueber-uns/fachpartner — "Projektanfragen fuer Solartechnik (PV Leads)", "eine Marke der DAA GmbH"
- leospardo.de/.../photovoltaik-leads-kaufen — "maximal 3", "55 EUR pro Lead", Voll-Exklusivitaet gg. Aufpreis
- rct-power.com/de/vertriebspartner.html — RCT Power Akademie, "Fachpartner finden" (kein Lead-Sharing belegt)
Such-Queries (WebSearch built-in):
- "photovoltaik.eu Mediadaten Installateure IVW PageImpressions Reichweite" -> ">380.000 IVW-PI/Monat", Zielgruppe Installateure/Planer/Architekten
- "Solarwatt Fachpartner Netzwerk 8500 Handwerker groesstes Solateur-Netzwerk Europa" -> "8.500 craftspeople", "largest solar installer network in Europe"
Nicht erreicht: photovoltaik.eu Startseite (redirect loop), pv-magazine Mediadaten (Reichweite nur im downloadbaren Media Kit), SWW-PDF (binär, nicht geparst).
