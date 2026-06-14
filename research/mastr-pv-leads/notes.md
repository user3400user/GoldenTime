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
(scouts log their own; orchestrator-chosen seeds below — appended as the run proceeds)
- [Phase 3 scouts dispatched 2026-06-14 — see source-scout returns]

## Dropped / weak sources
(filled during triage)
