# Marktstammdatenregister (MaStR) as a B2B buy-signal source — durable reference

_Distilled 2026-06-14 from [research/mastr-pv-leads/report.md](../research/mastr-pv-leads/report.md). All facts cited there._

The MaStR (Bundesnetzagentur) is the German register of every electricity/gas generation, storage and
consumption unit. It is a **first-rate buy-signal source**: new registrations = fresh PV/wind/storage
installations and the operators behind them; cohort filters surface trigger events (Post-EEG, retrofits).

## Measured snapshot (own live measurement off the MaStR web-JSON, 2026-06-14)
- Public electricity-generation units: **8,954,450** total · **solar 6,204,541** (6,058,494 operating) ·
  **storage 2,580,425** (2,544,621 operating). Storage ≈ **42 %** of solar — "without storage" filters against a huge class.
- **Post-EEG cohort by commissioning year (solar units):** 2006 = **63,807** (→ Förderende 2026, ~99 % still operating),
  2007 = **76,827** (→2027), then it climbs hard: 2009 = 182k, 2010 = 258k, 2011 = 260k, 2012 = 174k → the *ausgeförderte*
  market multiplies into the early 2030s. (Cohort keyed on unit `Inbetriebnahmedatum`; legal Förderende keys on `EegInbetriebnahmedatum` — near-identical, treat as proxy. "~66,000 plants in 2026" corroborated by Verbraucherzentrale.)
- **Web-JSON endpoint** `GetErweiterteOeffentlicheEinheitStromerzeugung` is open (no auth), returns `{Data, Total, …}`,
  has **no deep-paging cap in sampling** (pageSize ≥ 10k, full stock reachable, no throttle in 18+ reqs) and server-side
  filters: Energieträger (**Solar=2495, Speicher=2496**), Betriebs-Status (**In Betrieb=35**), date range on column
  **"Inbetriebnahmedatum der Einheit"** via `~gt~`/`~lt~` ISO dates. → Viable for **targeted filtered pulls**; bulk export
  still the better *backbone* (atomic versioned snapshot + storage-exclusion join + officially sanctioned channel). Weekly
  ~600-page full pulls via the frontend endpoint are untested/ToS-risky.
- **Number prefixes:** SEE Erzeugungseinheit · SEL Erzeugungslokation · SSE Speichereinheit · ABR Anlagenbetreiber ·
  SNB Netzbetreiber (struktur: 3 letters + version "9" + 10 digits + check digit). **§14 MaStRV:** a Stromerzeugungslokation
  groups "eine oder mehrere elektrisch verbundene Stromerzeugungseinheiten … über einen oder mehrere Netzanschlusspunkte".
- **Still unmeasured:** the exact PV+storage SEL co-location share — the community Datasette mirror (`ds.marktstammdatenregister.dev`)
  was down on 2026-06-14; the live endpoint can't filter "solar with co-located storage". Reproducible SQL is in the notes.

## Bezugsweg (how to get the full stock)
- **Gesamtdatenexport** = one ZIP of XML files (+ XSD + 142-pp data dictionary), `download.marktstammdatenregister.de`,
  **no login**, **~3 GB compressed** (2.96 GB on 2026-06-14, growing), **updated daily ~05:00** ("vom Vortag").
  Quarterly dated *Stichtag* exports (1.1/1.4/1.7/1.10) back to 01.04.2023. **New format since 01.10.2025** (schema 26.x).
  Confidential fields (natural-person names/addresses) are excluded from the public export.
- **No REST API delivers the whole stock.** SOAP API = single units + token; Web-JSON = paginated single queries.
- **For monitoring, use the bulk export**, not the Web-JSON, whenever you need operator-wide aggregation,
  both date fields jointly, or reproducible week-over-week diffs.

## Tooling (recency as of 2026-06-14)
- **open-mastr** (Python, OpenEnergyPlatform) — bulk download → SQLite/Postgres, `data=[...]` technology filter,
  `to_csv()`. **Actively maintained** (PyPI 0.17.1 2026-04-13; commit 2026-06-09). **Default choice.** No incremental
  update (whole daily dump per run; `download(method="API")` removed >v0.16.0).
- **marktstammdatenregister.dev** (`marktstammdatenregister-dev/mastr`, Go CLI → SQLite + Datasette/Zenodo) —
  good **schema/SQL reference**, but **dormant since 2023-11-23**, spec stuck at export v23.1 → likely needs spec
  updates for the post-2025 format. Hosted instance = 2023 snapshot.
- **bundesAPI/deutschland** — **NO MaStR module.** The org's `bundesAPI/marktstammdaten-api` is an OpenAPI spec of
  the **Web-JSON** endpoint `GetErweiterteOeffentlicheEinheitStromerzeugung` (paginated, `filter=` predicates),
  **frozen since 2022-07-17**. Its `Entry` schema is NOT field-poor — it exposes `AnlagenbetreiberMaStRNummer`,
  `AnlagenbetreiberPersonenArt`, `EinheitRegistrierungsdatum`, `InbetriebnahmeDatum`, `EegInbetriebnahmeDatum`,
  `DatumLetzteAktualisierung` (useful for lightweight live lookups/enrichment).

## Key export fields (official XML object → field; from the data dictionary)
- Dates: `Registrierungsdatum` (first registration; stable by design), `Inbetriebnahmedatum` (commissioning;
  historical, back to 1990s), `EegInbetriebnahmedatum` (on `AnlagenEegSolar`; governs the EEG clock),
  `DatumLetzteAktualisierung` (changes on every correction).
- Linkage: `AnlagenbetreiberMastrNummer` (`ABR…`, ~95–100 % populated, **solar 100 %** → robust operator roll-up),
  `LokationMaStRNummer` (`SEL…`, groups co-located units behind one grid connection point),
  `GemeinsamRegistrierteSolareinheitMastrNummer` (`SEE…`, storage→PV) + `SpeicherAmGleichenOrt` (Bool, PV side).
- Storage is a **separate Einheit** (`EinheitenStromSpeicher`), usually co-registered with its generator.

## ⚠️ Gotchas (cost you credibility if ignored)
1. **`Registrierungsdatum` ≠ "newly built."** Bestandsanlagen had to back-register by **31.01.2021**, so old
   plants carry young registration dates. **Always gate freshness on `Inbetriebnahmedatum` too.**
2. **"Without storage" = "no storage recorded," not reality.** ~9 % of home storage is un-/late-registered;
   manual lay entries cause confusions/errors. Never assert absence with certainty.
3. **PV↔storage record-level linkage is imperfect.** The literature matches storage to PV *statistically*
   (PV-side flag), not by a clean key. Operator-number roll-up is the most reliable linkage; SEL/co-location
   fields are available but not exhaustively complete.
4. **PV geolocation is weak:** ~95 % of PV units have no coordinate; 0.5–2 % of present ones are wrong.
   (The "21.3 %" data-quality figure is power-density plausibility, NOT a mislocation rate.)
5. **Schema changed 01.10.2025** — older tools/specs (e.g. the Go converter's v23.1) may not parse current exports.

## Recurring buy-signal patterns seeded here
- **New registration (gewerblich PV, no recorded storage)** → fresh installation → storage-retrofit / O&M / monitoring lead.
- **Post-EEG cohort** = `EegInbetriebnahmedatum` year + 20 calendar years → end of 21st operating year. 2006→end-2026,
  2007→end-2027. Loss of guaranteed tariff is a trigger event (Eigenverbrauch/Direktvermarktung/repowering decision).

## Vetted sources
- Primary: `marktstammdatenregister.de` Webhilfe/Datendownload + the **Gesamtdatenexport documentation PDF** (the
  authoritative data dictionary); MaStR-Gesamtkonzept & Registrierungshilfe PDFs; MaStR help subpages; 2019 newsletter (Wayback).
- Reliability caveats: Figgener et al. arXiv:2203.06762 (storage market/matching); arXiv:2304.10581 (MaStR data quality).
- EEG 20-yr rule: Verbraucherzentrale Ü20 page (clean, neutral).
