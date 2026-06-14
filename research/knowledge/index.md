# Knowledge Index

Durable, cross-run insights distilled from investigations. The orchestrator writes one file per topic in
`knowledge/` and links it here. The SessionStart hook surfaces the top of this file each session, so keep
the most load-bearing facts near the top.

## How to use
- After a `/research` or `/deepen` run, distil anything reusable (a vetted source, an entity profile, a
  recurring buy-signal pattern, a quality caveat) into `knowledge/<topic>.md`.
- Add a one-line pointer below: `- [Title](file.md) — hook` (what it's good for).
- Keep entries factual and sourced; link back to the originating `research/<slug>/report.md`.

## Entries
- [Expansions-Landkarte „GoldenTime"](expansion-map.md) — dauerhafter, gescorter **Backlog** der Ausweitungs-Richtungen für das register-abgeleitete Lead-Geschäft: neue MaStR-Trigger (A), neue Käufersegmente (B), Kanäle (C/=R2), Geografien+angrenzende Register (D/=R4), Produktisierung (E), Blue-Ocean (F) + White-Space-/„gibt-es-schon"-Verdikt. Enthält die 5 ersten Hebel, die Revisit-Logik und die Kills (WP-aus-MaStR, AT E-Control, Gewerbeanmeldungen). Vertiefen via `/deepen expansion-map <Achse>`. _(expansion-map, 2026-06-14)_
- [MaStR as a B2B buy-signal source](mastr-buy-signals.md) — how to pull the Bundesnetzagentur Gesamtdatenexport, the key fields, tool landscape (open-mastr vs. dormant alternatives), and the registration-date / storage-completeness gotchas. _(mastr-pv-leads, 2026-06-14)_
- [HTTP/3 Adoption — state as of 2025](http3-adoption-2025.md) — traffic vs. site-level metrics; vetted web-protocol measurement sources. _(self-test, 2026-06-14)_

## Vetted sources & entities
- German energy assets / PV-storage installations & operators: **Marktstammdatenregister (MaStR)** Gesamtdatenexport + open-mastr; reliability caveats from arXiv:2203.06762 & arXiv:2304.10581 — see [mastr-buy-signals.md](mastr-buy-signals.md). _(verified 2026-06-14)_
- Web-protocol adoption: Cloudflare Radar, HTTP Archive/Web Almanac, W3Techs, IETF Datatracker — see [http3-adoption-2025.md](http3-adoption-2025.md). _(verified 2026-06-14)_
- Register-abgeleitete Kaufsignale über MaStR hinaus: **BNetzA-Ladesäulenregister** (CC-BY 4.0, REST-API, EV-CPO), **FR ODRÉ/RTE** (anlagengenau ≥36 kW, Speicher, bestes MaStR-Analog), IT GSE Conto-Energia, CH opendata.swiss EIV; B2B-Signal-Analoga: Implisense/Dealfront/Vainu (Handelsregister-/Web-Trigger, kein Energie-Register) — siehe [expansion-map.md](expansion-map.md). _(verified 2026-06-14)_

## Recurring buy-signal patterns
_(signal types that have proven predictive here, e.g. "new VP RevOps hire → tooling RFP within ~2 quarters")_
- **New MaStR registration** (gewerbliche PV, no recorded storage) → fresh install → storage-retrofit/O&M/monitoring lead. Gate "fresh" on `Inbetriebnahmedatum`, not just `Registrierungsdatum`. _(mastr-pv-leads, 2026-06-14)_
- **Post-EEG cohort** (`EegInbetriebnahmedatum` year + 20 → end of 21st operating year; 2006→end-2026, 2007→end-2027) → loss of guaranteed tariff = decision trigger. _(mastr-pv-leads, 2026-06-14)_
- **Speicher-Retrofit** (neuer `EinheitenStromSpeicher` an ABR/Standort mit Bestands-PV) → Nachrüst-Lead; Signal lückenhaft (~40 % fristgerecht). _(expansion-map, 2026-06-14)_
- **Betreiberwechsel** (ABR-Diff bei gleicher `EinheitMastrNummer`, KEINE Neuregistrierung) → O&M/Asset-Mgmt/Versicherer-Lead (False-Positive bei Umfirmierung). _(expansion-map, 2026-06-14)_
- **Neuer öffentlicher Ladepunkt** (BNetzA-Ladesäulenregister, CC-BY 4.0, REST-API) → EV-Lade-CPO-Lead; kein IBN-Datum → Frische per Diff. _(expansion-map, 2026-06-14)_
- **Pflicht-Direktvermarktung** (frische PV ≥100 kWp, IBN nach 1.1.2016) → strukturell garantierter Direktvermarkter-Lead (nicht-konkurrierend zum Speicher-Lead). _(expansion-map, 2026-06-14)_
- **Anti-Pattern (Kill):** Wärmepumpen/Wallboxen sind NICHT aus dem MaStR triggerbar (NS-Verbraucher nicht meldepflichtig; §14a → Netzbetreiber). _(expansion-map, 2026-06-14)_
