# Expansions-Landkarte „GoldenTime" — dauerhafter Backlog (Engine: öffentliches Register → exklusiver regionaler datierter Kaufsignal-Lead)

_Distilled 2026-06-14 aus [expansion-map/report.md](../expansion-map/report.md). Alle Belege dort zitiert.
Baut auf [[mastr-buy-signals]] auf. Vertiefen Achse für Achse via `/deepen expansion-map <Achse>`._

**Kern-These (Job-to-be-done):** Der Kunde kauft nicht „Daten", sondern **„die richtige Vertriebspipeline
zur richtigen Zeit exklusiv gefüllt"**. Die Engine (öffentliches Pflichtregister → diff → qualifizieren →
anreichern → regional-exklusiv liefern) ist **vertikal-agnostisch**: jede neue Vertikale = ein neuer
Register-Filter, Grenzkosten/Zusatzgebiet ~0. Kernprodukt (T1: frische gewerbl. PV ohne gemeldeten Speicher,
exklusiv pro Region) ist **white-space** (kein gefundener Anbieter), ABER Engine (open-MaStR, AGPL) + Rohdaten
(gratis, Datenlizenz DE 2.0 = kommerziell) sind frei → **Moat = Frische + Filterschärfe + Anreicherung +
vertragliche Gebiets-Exklusivität + Tempo**, NICHT die Datenquelle. Das ist zugleich das schärfste R1-Risiko.

## Die 5 ersten Hebel (Solo · 4 h/Woche · BPV)
1. **B — Mehrfachverwertung pro Gebiet** (denselben frischen Lead an mehrere nicht-konkurrierende Käufer;
   Exklusivität *pro Funktion*). Erster Zweit-Käufer: **Direktvermarkter** (Pflicht-DV ≥100 kWp = strukturell
   garantiert; nur ein Leistungsfilter entfernt). Größter Umsatzmultiplikator bei ~0 Grenzkosten.
2. **E — „Kaufsignal-Radar"-Abo + gestufte Frische** (wiederkehrend/LTV/defensibel; Diff läuft ohnehin;
   Analog: Implisense „Signal Retainer ab 1.500 €/Monat").
3. **A — Speicher-Retrofit + Post-EEG-Erweiterung** (PV-T2 → Biogas) — neue Trigger auf demselben Pull.
4. **D/F — EV-Lade-CPO über das BNetzA-Ladesäulenregister** — billigster Beweis der horizontalen Engine
   (offenes Register, CC-BY 4.0, REST-API, tägl.; **BPV unkritisch**).
5. **C — Käufer-Akquise: Hersteller-Co-Selling (Tesvolt/Solarwatt/Fenecon) + BSW-Schnuppermitgliedschaft**
   (gratis, 6 Mon.); getaktet auf Intersolar/ees Europe (jährlich München, 2026: 23.–25.06.). Gate für alles.

## Achse A — neue Trigger aus demselben MaStR-Pull (Erzeugung/Bestand)
Wind/Biomasse/Speicher/Verbrennung/KWK liegen als eigene joinbare Tabellen vor (open-mastr `*_extended`).
- **Speicher-Retrofit** (neuer `EinheitenStromSpeicher` an ABR/Standort mit Bestands-PV) 🟢 — Signal lückenhaft
  (~40 % fristgerecht gemeldet). **Biogas/Wind Post-EEG** (EegInbetriebnahmedatum nahe 20-J.-Ende) 🟡.
- **Betreiberwechsel** (ABR-Diff bei gleicher Einheit — KEINE Neuregistrierung) 🟢; **Stilllegung**
  (`DatumEndgueltigeStilllegung`) 🟢; **PV-Erweiterung** = neue Zweit-Einheit 🟢. Alle WTP spekulativ.
- **Gotcha:** PV-Leistungserhöhung ist NICHT als Feldänderung erkennbar (nur Reduktion eintragbar; Zubau =
  neue Einheit). Bei Wind/Biomasse/Verbrennung sind Erhöhungen via Leistungshistorie diff-bar.

## Achse A2/F — KILL: Wärmepumpen/Wallboxen NICHT aus MaStR triggerbar
NS-Verbraucher (WP/Wallbox in Wohnhäusern) sind **nicht registrierungspflichtig**; `electricity_consumer` =
„only large consumers" (nur HV/EHV); §14a-Meldung geht an den **Netzbetreiber**, nicht ins MaStR; kein
Lade-Objekt im Export. Käufermarkt riesig (WP +55 %), aber **Trigger-Quelle fehlt**. ⚫ Nur revisiten, falls
ein öffentliches bundesweites WP-/§14a-Register mit Bulk-Export entsteht. (Speicher dagegen = §14a-Gerät,
aber sehr wohl im MaStR → Basis von Vektor #4.)

## Achse B — neue Käufersegmente fürs Kernsignal
**Direktvermarkter ≥100 kWp** (Pflicht, strukturell) · PV-Finanzierung/Leasing (grenke) · OnSite-PPA
(Mainova, große Dächer) · O&M/Monitoring (meteocontrol, 🔴 crowded) · **wMSB/Smart-Meter** (iMSys ab 7 kWp,
🟢 dünn) · OT/IT-Security/NIS2 (entstehend) · Energieberater (BPV: nur private, keine Behörden).
WTP-Anker: gewerbl. PV-Leads 20–125 €/exkl.; B2B-Outbound-CPL 250–550 €. Pro-Lead-WTP je Segment = empirisch
zu erheben (größte offene Lücke).

## Achse C — Kanäle zur Käufer-Gewinnung (= R2)
Hersteller haben Lead-Verteil-Reflex (Tesvolt „Zugang zu Projektanfragen"; Solarwatt „Vorqualifizierte
Leads"; Fenecon rein indirekt + Vermittlung) → andocken/white-label. Markt bepreist Exklusivität bereits
(Leospardo 55 €/Lead, Voll-Exklusiv = Aufpreis). Türöffner: BSW-Schnuppermitgliedschaft (gratis 6 Mon.),
Lead-Magnet (Regional-Kostprobe), Fachmedien (photovoltaik.eu), Intersolar/ees (jährl. München).

## Achse D — Geografien & angrenzende Register
- **Geografie (R4):** **FR** (ODRÉ/RTE, anlagengenau ≥36 kW, Speicher, m+2) = bestes MaStR-Analog; **IT**
  (GSE Conto-Energia, Name+Steuerdaten+Leistung) reichste Identität; **CH** (opendata.swiss EIV, Granularität
  prüfen). ⚫ **AT** (E-Control = nur HKN, kein Betreibergraph; OeMAG-Kohorte nicht offen) — trägt das
  Exklusiv-Lead-Versprechen NICHT. NL/ES/BE/PL/IE = fragmentiert/parken; DK = Deep-Read-Kandidat.
- **Angrenzende DE-Register:** **Ladesäulenregister** 🟢 (sauberster Zwilling, CC-BY 4.0, REST-API, BPV
  unkritisch; Gotcha: kein Inbetriebnahmedatum → Frische per Diff). Vergabe/TED 🔴 (Auftraggeber = öffentl.
  Hand → BPV-kritisch, nur Bieter-Intelligence für private EPC). Handelsregister 🟡 (kein offizielles Bulk;
  OffeneRegister veraltet/JSONL; bundesAPI = §303a/b-Risiko → R5). ⚫ Gewerbeanmeldungen + Baugenehmigungen =
  zentral nur Aggregat.

## Achse E — Produktisierung (ohne Datenbasis-Wechsel)
**Kaufsignal-Radar-Abo** (Implisense-Analog) · **gestufte Frische** (SolarReviews $300/exkl.; Vainu-Tier) ·
Enrichment-as-a-Service (Betreibergraph schon im Export) · Daten-Feed/API (Vainu „for Data") · Gebiets-
Auktion (Exclusive/Duo/Trio/Quad) · CRM-Integration (Pipedrive/HubSpot, erst nach Traktion) · White-Label ·
Rev-Share + Daten-Kooperative (Bombora-Analog) = Spätstadium.

## Achse F — Blue-Ocean
**Meta-Horizontale „Register-as-a-Filter"** 🟢 (Vertikale-Playbook). Bestätigte Schwünge: EV-CPO, Biogas.
Kills/Kill-Fragen: WP (kein Trigger), Dachdecker/Permit (US-Modell BuildZoom bewiesen, DE-Bauanträge
fragmentiert → erst Open-Data-Verfügbarkeit klären).

## Revisit-Logik (woran erkennen wir, dass eine Option dran ist)
Zweiter zahlender Käufer im Gebiet → Bündel-Pricing (B). Kunde will „laufend statt einmalig" → Abo (E).
Zwei Interessenten fürs gleiche Gebiet → gestufte Frische/Auktion (E). >5 frische Einheiten/Region/Woche in
einer neuen Sparte → Vertikale pilotieren (A/F). DE-Modell hält Retainer + Auslands-Pilotinstallateur → FR
(D1). Wettbewerber bewirbt MaStR-EINZELanlagen-Leads (statt Aggregat wie solarzubau.de) → Moat schärfen (R1).

## Abgrenzung
R1 (Wettbewerb) & R5 (Recht) = nur Constraints (Flags hier vermerkt). R2 = Achse C (vertiefen). R4 = Achse D1
(vertiefen — und auf FR/CH/IT umlenken, AT ist negativ).
