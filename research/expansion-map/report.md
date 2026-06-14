# Expansions-Landkarte „GoldenTime" — Backlog der Ausweitungs-Richtungen
_Run: 2026-06-14 · Mode: deep-research (Landkarte/Backlog) · Slug: expansion-map_

> Dauerhafte, referenzierbare Optionsliste, auf die wir zurückgreifen, sobald Prototyp/Gate stehen und
> skaliert wird. **Kein Pivot** — eine geordnete Erweiterung des bestehenden Modells (öffentliches Register
> → exklusiver regionaler datierter Kaufsignal-Lead). Strategische **Superset-Landkarte**: R1 (Wettbewerb)
> & R5 (Recht) nur als Constraint; R2 (Kanäle, = Achse C) und R4 (Österreich, = Teil Achse D1) nur auf
> Option-Tiefe. Vertieft wird Achse für Achse via `/deepen expansion-map`.

## TL;DR
Das bestehende Asset — die **MaStR-Gesamtexport-Pipeline** (Pull→Qualify→Enrich→Deliver, Grenzkosten/
Zusatzgebiet ~0) — trägt deutlich mehr als T1 (frische gewerbliche PV ohne Speicher) und T2 (Post-EEG).
Vier Hebel stechen heraus: **(B) derselbe frische Lead an mehrere nicht-konkurrierende Käufer pro Gebiet**
(Direktvermarkter ab 100 kWp ist strukturell *Pflicht*-getrieben [18]; dazu Finanzierung/PPA, O&M,
wMSB) — der größte Umsatzmultiplikator bei ~0 Grenzkosten; **(E) Verstetigung** als Monitoring-/Alert-Abo
(„Kaufsignal-Radar") — direkt validiert durch Implisenses „Signal Retainer ab 1.500 €/Monat" [61] — plus
gestufte Frische [64]; **(A) neue Trigger aus demselben Pull** (Speicher-Retrofit, PV/Biogas-Post-EEG —
Wind/Biogas/Speicher liegen als eigene joinbare Tabellen vor [4][7]); und **(D/F) der billigste Beweis,
dass die Engine horizontal ist**: das **BNetzA-Ladesäulenregister** ist ein sauberer MaStR-Zwilling (tägl.,
CC-BY 4.0, REST-API, Betreiber+Adresse) → EV-Lade-CPO-Vertikale [49][50]. Das **Kernprodukt ist
white-space** — kein *gefundener* Anbieter verkauft „frische gewerbliche PV ohne Speicher, MaStR-abgeleitet, exklusiv pro
Region, wöchentlich" [71][73][74]; **aber** Engine (open-MaStR) und Rohdaten sind frei und kommerziell
nutzbar [71][72] → der Moat liegt in Frische+Filterschärfe+Anreicherung+Exklusivität+Ausführung, nicht in
den Daten. Wichtige **Kills** (sparen Zeit): Wärmepumpen/Wallboxen sind **nicht** aus dem MaStR triggerbar
(NS-Verbraucher nicht meldepflichtig; §14a-Meldung geht an den Netzbetreiber) [15][16][7]; das **AT
E-Control-Register** trägt das Exklusiv-Lead-Versprechen nicht (nur HKN-Daten, kein Betreibergraph) [46];
Gewerbeanmeldungen sind nur aggregiert öffentlich [56].

## Wie diese Landkarte zu lesen ist
- **Status** je Option: 🟢 white-space · 🟡 exists-partial (existiert angrenzend/teilweise) · 🔴 exists-crowded
  (Anbieter/Quelle existiert, Markt besetzt) · ⚫ killed/ausgeschlossen · ⏸ parken.
- **Fit** = Passung zum vorhandenen Asset (gleicher Pull/Engine, ~0 Grenzkosten, Solo/4h/BPV-tauglich).
- **Aufwand** = bis zur ersten verkaufbaren Version für einen Solo-Gründer mit 4 h/Woche.
- **Revisit-Trigger** = woran wir erkennen, dass die Option *jetzt* dran ist.
- BPV-Constraint (nur öffentliche Daten; **keine Kunden aus dem Bundesumfeld**) ist in jede Bewertung eingearbeitet.

---

## Key findings — je Achse

### Achse A — neue Kaufsignale aus demselben MaStR-Pull
- **A liefert ≥6 zusätzliche Trigger, alle bei Grenzkosten ~0**, weil Wind/Biomasse/Verbrennung/KWK/Speicher
  als eigene, joinbare Tabellen im selben Export liegen (`storage_extended`, `wind_extended`,
  `biomass_extended`, `combustion_extended`, `kwk` + `*_eeg`) [7], Feldnamen primär aus der Community-Spec
  bestätigt (Bruttoleistung, Inbetriebnahmedatum, beide Stilllegungsfelder, `AnlagenbetreiberMastrNummer`,
  `EegMaStRNummer`) [4]. (beantwortet Achse A)
- **Speicher-Retrofit ist erkennbar** (Spiegelbild zu T1): „sowohl die Solaranlage als auch den
  Batteriespeicher einzeln … eintragen" [5] → ein neuer `EinheitenStromSpeicher` an einem ABR/Standort mit
  bestehender Solar-Einheit = Nachrüst-Signal. **Gotcha:** „nur 40 % der nachgerüsteten Speicher fristgerecht
  gemeldet" [6] → Signal lückenhaft/verzögert. Markt: Gewerbespeicher „+58 Prozent … gegenüber dem
  Vorjahresquartal", aber kleine Basis 163 MWh [8]. (confidence: high für Mechanik, med für Volumen)
- **PV-Leistungserhöhung ist NICHT als Feldänderung erkennbar:** „Bei Solaranlagen können über diesen Weg
  nur Leistungsreduzierungen registriert werden" [1]; PV-Zubau = **separate** neue Einheit [1] (→ als
  Erweiterungs-Signal nutzbar). Bei **Wind/Biomasse/Verbrennung** sind Erhöhungen eintragbar und werden als
  „Leistungshistorie" gespeichert [1] → echter Repowering-Diff möglich. (confidence: high)
- **Betreiberwechsel erzeugt KEINE Neuregistrierung:** „Die Einheit darf nicht neu … registriert werden …
  Datenverantwortung … übertragen" [2] → einziges Signal = `AnlagenbetreiberMastrNummer`-Wechsel bei gleicher
  `EinheitMastrNummer` (Diff). White-Space, aber False-Positive-Risiko (Umfirmierung). (confidence: high für
  Mechanik, med für Verkaufbarkeit)
- **Stilllegung:** „Endgültige Stilllegungen können … nicht rückgängig gemacht werden" [3] (`DatumEndgueltige-
  Stilllegung` vs. `DatumBeginnVoruebergehendeStilllegung`) → Rückbau-/Repowering-/Flächen-Signal. (high
  Mechanik, Zahlungsbereitschaft spekulativ)

### Achse A2 — verbrauchsseitige & §14a-Trigger: weitgehend ein KILL
- **Kein verbrauchsseitiger §14a-Massentrigger im MaStR.** Stromverbrauchsanlagen sind nur bei Anschluss an
  Hoch-/Höchstspannung meldepflichtig: „Damit sind auch keine Wärmepumpen in Wohnhäusern zu registrieren"
  [15]; `electricity_consumer` = „Only large consumers" [7]; das Verbraucherobjekt trägt **kein Leistungs-/
  Spannungsfeld** [12]. Die §14a-Meldung „müssen Sie … Ihrem Netzbetreiber … melden" [16] — nicht ins MaStR.
  **Im 142-seitigen Schema kein Lade-/Wallbox-Objekt** [12]. ⇒ Wärmepumpen-/Wallbox-Leads aus MaStR sind
  **nicht** baubar (Ladeinfrastruktur separat über das Ladesäulenregister, s. D2/F). **Stromspeicher** dagegen sind — obwohl §14a-Gerät — sehr wohl im MaStR und bleiben die Basis von
  Vektor #4. Käufermarkt existiert
  (WP +55 %, 299.000 [14]) — aber die *Trigger-Quelle* fehlt. (confidence: high — Kill belegt)

### Achse B — neue Käufersegmente für dasselbe Kernsignal
- **Direktvermarkter sind der härteste, strukturell garantierte Zweit-Käufer:** „verpflichtende
  Direktvermarktung … nach dem 1.1.2016 … über 100 kWp" [18]; e2m [19] belegt die 100-kW-Schwelle nur für Redispatch 2.0, zeigt aber, dass DV-Anbieter ≥100-kWp-PV
  aktiv adressieren. Frische ≥100-kWp-PV ist
  für *mehrere* DV gleichzeitig heiß → nicht-konkurrierend zum Speicher-Lead. (confidence: high)
- **Weitere zahlungsbereite Segmente:** PV-Leasing/Finanzierung (grenke [20]), OnSite-PPA (Mainova, ab
  ~150.000 kWh/600 m² [21]), O&M/Monitoring (meteocontrol [22]; aber ~31 Anbieter [23] → crowded), wMSB/
  Smart-Meter (iMSys ab 7 kWp; freie wMSB-Wahl [24] → white-space, WTP dünn), OT/IT-Security/NIS2 (DNV:
  Wechselrichter als „kritische Produkte" [25] → entstehend, high effort), Energieberater (BAFA [26]).
- **Der eigentliche Hebel = nicht-konkurrierende Mehrfachverwertung pro Gebiet.** Preis-Headroom belegt:
  gewerbl. PV-Leads „zwischen 20 und 120 Euro" [27] bzw. „35 € und 125 €" exklusiv [28]; B2B-CPL via Outbound
  „250 bis 550 €" [29] → die Summe mehrerer Segmente pro Gebiet ist realistisch, Exklusivität bleibt **pro
  Käuferfunktion** erhalten. (confidence: med-high)

### Achse C — wiederholbare Kanäle zur Käufer-Gewinnung (R2-Scheibe)
- **Hersteller haben bereits einen Lead-Verteil-Reflex** — der stärkste Andockpunkt: Tesvolt „Zugang zu
  Projektanfragen" / „priorisierten Zugang zu ausgesuchten Projektanfragen" [30]; Solarwatt „Vorqualifizierte
  Leads" im „größten Solateur-Netzwerk Europas" [31]; Fenecon „ausschließlich über Großhandelspartner und Installateure" +
  „vermitteln wir Ihnen gerne einen qualifizierten Betrieb" [32]. (Sungrow/RCT: Partnerstrukturen, aber
  Lead-Weitergabe nicht belegt [33][34].) (confidence: high)
- **Exklusivität ist am Markt bereits bepreist:** Leospardo „55 € pro Lead", „Klassische Leadportale … an
  10+ Betriebe … Bei Leospardo maximal 3" (Voll-Exklusivität gegen Aufpreis) [37]; DAA/TapTapHome „Projektanfragen für Solartechnik (PV Leads)"
  [36] → GoldenTimes Kern-USP wird vom Markt validiert. (confidence: high)
- **Solo/4h-taugliche Türöffner:** BSW-Solar „sechs Monate kostenlos" / „>1.000 Solar- und
  Speicherunternehmen" [35]; Fachmedien (photovoltaik.eu „>380.000 page impressions monthly" [38];
  pv magazine „Sponsored Content" [39]); **Intersolar/ees Europe „June 23–25, 2026" München, „100,000+"**
  [40] — Networking-Fenster **direkt vor dem Berater-Essen ~27.06.** (confidence: high)

### Achse D1 — neue Geografien (R4-Scheibe)
- **FR ist das beste MaStR-Analog:** „Registre national des installations de production et de stockage
  d'électricité" (RTE/ODRÉ), anlagengenau ≥36 kW, mit Speicherdimension, CSV/API, monatlich (m+2) [41] →
  T1-Klon inkl. Speicher-Lücken-Prüfung baubar (kein Wochen-, aber Monats-Diff). (confidence: high für
  Eignung, Zahlungsbereitschaft spekulativ)
- **CH:** opendata.swiss EIV/Pronovo „published as open data … regularly updated" [42], mit Leistung/
  Kategorie (Inbetriebnahme-Feld + Anlagengenauigkeit noch zu verifizieren) — **aber** Granularität teils pro Kanton/Jahr aggregiert [43] → Anlagengenauigkeit
  prüfen. **IT:** GSE Conto-Energia-Begünstigte mit Name+Steuerdaten+Leistung, „IODL … v2.0 … CSV … and JSON"
  [44] → reichste Betreiber-Identität, klare 20-Jahres-Auslaufkohorte. (confidence: med)
- **AT (R4-Fokus) = geprüft-negativ:** E-Control-Register „beruhen ausschließlich auf … Herkunftsnachweis-
  datenbank … § 81 … EAG" [46] → kein Betreibergraph/Adresse; Post-Förder-Kohorte liegt bei OeMAG, nicht offen
  [47]. **Kein GoldenTime-Produkt direkt darauf.** (confidence: high) — NL/ES/BE/PL/IE: Register fragmentiert
  oder hinter Login → parken; DK (Energinet [48]) = Deep-Read-Kandidat.

### Achse D2 — angrenzende öffentliche DE-Register
- **Ladesäulenregister = sauberster MaStR-Zwilling:** „Liste der Ladesäulen (CSV) (csv / 46 MB) … Creative
  Commons Namensnennung 4.0 … Betreiber … Adresse … technische Ausstattung" [49] + „öffentliche Schnittstelle
  … einmal täglich aktualisiert" (JSON/XML) [50]. **BPV unkritisch** (kein Bundes-Auftraggeber). Gotcha: kein
  Inbetriebnahmedatum pro Ladepunkt → Frische per Diffing rekonstruieren. (confidence: high)
- **Vergabe/TED:** anonyme Search-API + eForms-XML [51] — öffentlich/datiert/maschinenlesbar, **aber
  Auftraggeber = öffentliche Hand** → als *Zielkunde* BPV-kritisch; nutzbar nur als **Bieter-Intelligence**
  für private EPC. (confidence: high, Status exists-crowded)
- **Handelsregister:** seit DiRUG 1.8.2022 gratis [52], aber **kein offizielles Bulk**; OffeneRegister.de
  bietet Bulk-JSONL (>5 Mio Firmen), laufend via Gazette-Notices gepflegt (Vollständigkeit/Aktualität pro
  Datensatz unklar) [53]; bundesAPI „60 Abrufe pro Stunde" + „§§303a,
  b StGB" [54] → R5-Rechtsrisiko, nur als punktuelle Anreicherung. **Gewerbeanmeldungen** nur aggregiert [56]
  → **ausgeschlossen**; **Baugenehmigungen** zentral nur Aggregat [57] → fragmentiert/high effort.

### Achse E — Produktisierung & Geschäftsmodell
- **Monitoring-/Alert-Abo („Kaufsignal-Radar") ist die direkteste Verstetigung** — direkt validiert:
  Implisense „Signal Retainer … from €1,500/month" auf 2,5 Mio dt. Firmen + API/Real-Time [61]. Der
  wöchentliche Diff läuft ohnehin → Abo bei ~0 Zusatzaufwand. (confidence: high)
- **Gestufte Frische & Exklusivitäts-Auktion:** SolarReviews „exclusive … as much as $300 per lead" +
  Stufenmodell „Exclusive / Duo / Trio / Quad" [64]; Vainu zeigt API/Feed als Premium-Tier („Vainu for Data …
  Customized pricing", Webhook/SFTP [59]) und ~80 Signaltypen als Produkt [60]. (confidence: med-high)
- **Distribution über CRM-Marktplätze** ist real, aber auflagenbehaftet: Pipedrive „visible to over 100,000
  companies" [62]; HubSpot „at least 3 active installs" [63] → erst nach Erst-Traktion. **Daten-Kooperative**
  (Bombora „86% … exclusively shared" [65]) und **Rev-Share** = Spätstadium, da Zusatz-Datenfluss/Attribution
  nötig (widerspricht Solo/4h). (confidence: med für die starken, low für Spät-Modelle)

### Achse F — disruptive / Blue-Ocean-Schwünge
- **JTBD:** der Kunde kauft nicht „Daten", sondern **„die richtige Vertriebspipeline zur richtigen Zeit
  exklusiv gefüllt"** — pro neuer Trigger-Vertikale. Die Engine ist **vertikal-agnostisch**: der Export deckt
  „electricity and gas production units … consumers, storages, grids, and energy market participants" [67] →
  jede neue Vertikale = ein neuer Register-Filter (Grenzkosten ~0). (confidence: high für die Engine-Logik)
- **Bestätigte Schwünge:** EV-Lade-CPO (Ladesäulenregister, CC-BY 4.0, diff-bar [49]; ~196.353 öffentl.
  Ladepunkte, Stand 1.2.2026 [70]); Biogas-Post-EEG (Biomethan im MaStR [15]; „Ausschreibungsmengen … 2026 auf 1.126
  MW angehoben" [10]). **Kills:** Wärmepumpen (kein öffentl. Trigger [15][16]; BAFA-WEP ist Geräte-Katalog,
  kein Installationsregister [Quelle F1]); Dachdecker/Permit (US-Modell BuildZoom „350M+ building permits …
  windows and doors to pools, HVAC, and roofing" [68] **bewiesen**, aber DE-Bauanträge fragmentiert → erst
  Kill-Frage klären). **Meta-Konkurrenz:** PredictLeads-artige Trigger-Engines existieren, aber
  digital-/firmen-event-basiert, **nicht aus öffentlichen Pflichtregistern und ohne Regional-Exklusivität**
  [69]. (confidence: med)

### Quer (X1) — Wettbewerb als Constraint (R1 besitzt die volle Analyse)
- **White-Space-Verdikt Kernprodukt bestätigt:** Kein *gefundener* Anbieter verkauft die exakte Kombination (Negativbeleg nach
  Recherche, kein systematischer Vollbeweis) „frische
  gewerbliche PV ohne Speicher, MaStR-abgeleitet, exklusiv pro Region, wöchentlich" [71]. Jede Einzelzutat
  existiert getrennt: Engine commodity/Open-Source (open-MaStR, AGPL-3.0, „parsing the XML files to a relational
  database" [71]), Rohdaten frei + „Datenlizenz Deutschland – Namensnennung – Version 2.0" (kommerziell) [72];
  MaStR-Aufbereitung nur als **Aggregat** (solarzubau.de „Gemeinden mit mindestens 50 PV-Anlagen" [73], keine
  Einzel-Leads); PV-Leads existieren als **Hausbesitzer-Anfrage** (DAA „3 bis 5 regionale Fachbetriebe" [75];
  „Exklusive Leads ab 60€" [74]); Trigger-Daten-Anbieter (Dealfront „national trade registers" [77];
  Implisense [76]; databyte [78]) liefern Handelsregister-/Web-Signale, **kein** Energie-Register-Timing.
- **Folge für den Moat:** Weil Pull+Daten gratis/offen sind, ist die **Eintrittsbarriere niedrig** → der Moat
  ist *nicht* die Datenquelle, sondern **Frische + Filterschärfe + Anreicherung + vertragliche Gebiets-
  Exklusivität + Ausführungstempo**. Das ist auch das schärfste strategische Risiko (s. Gegenposition).
  (confidence: high)

---

## Backlog-Tabelle „Expansions-Vektoren" (gescort, nach Hebel sortiert)

> Sortierung absteigend nach Hebel (Fit × Nachfrage-Beleg × Umkehr-Aufwand × Defensibilität, unter Solo/4h/
> BPV). Zeilen 1–6 = **erste Welle**. Killed/parken-Zeilen am Ende dokumentieren bewusst, was *nicht* zu
> verfolgen ist.

| # | Vektor · Achse | Was → Käufer · Trigger | Fit (warum) | Aufw. | Status | Nachfrage-Beleg (Quelle · Konf) | Revisit-Trigger | Konf |
|--:|:--|:--|:--|:--|:--|:--|:--|:--|
| 1 | **Nicht-konkurrierende Mehrfachverwertung** · B | Denselben frischen Gewerbe-PV-Lead pro Gebiet an mehrere Käufer (Speicher + DV + Finanzierung + O&M + Versicherung), Exklusivität *pro Funktion* → jede neue Gewerbe-PV-Einheit | **high** — exakt der Asset-Hebel: 1 Pull, viele Abnehmer, ~0 Grenzkosten | med | 🟢 | PV-Leads 20–125 €/exkl. [27][28]; B2B-CPL bis 550 € [29] (med-high) | Zweites Käufersegment in derselben Region zahlt | high |
| 2 | **Direktvermarkter-Leads ≥100 kWp** · B | Frische PV ≥100 kWp (IBN nach 2016) exklusiv an DV/VPP (Next Kraftwerke, e2m) → Pflicht-Direktvermarktung = sofortiger Bedarf | **high** — reiner Leistungsfilter auf vorhandenem Feld, nicht-konkurrierend zum Speicher-Lead | low | 🔴 | Pflicht-DV ab 100 kWp [18] (e2m [19] = Redispatch-2.0-Schwelle) (high; Pro-Lead-Preis n/a → med) | DV signalisiert Interesse; >5 frische ≥100-kWp/Woche/Region; ODER DV-Schwelle gesenkt (Mengen-Upside) | high |
| 3 | **„Kaufsignal-Radar" Monitoring-/Alert-Abo** · E | Wiederkehrendes Abo: gespeicherte Filterprofile (T1/T2) laufen gegen den Diff, neue Treffer als Alert → Gewerbespeicher-Installateur | **high** — Diff läuft ohnehin, keine neue Datenbasis, ~0 Grenzkosten | low | 🟡 | Implisense „Signal Retainer … €1,500/month" [61] (high) | Kunde fragt „laufend statt einmalig" ODER Churn nach Erstlieferung | high |
| 4 | **Speicher-Retrofit-Leads** · A | Diff: neuer `EinheitenStromSpeicher` an ABR/Standort mit bestehender PV = Nachrüstung → Speicher-/EMS-/O&M-Anbieter | **high** — `storage_extended` joinbar via ABR, gleiche Diff-Logik wie T1 | low | 🟢 | Gewerbespeicher +58 % YoY (kleine Basis 163 MWh) [8]; Retrofit-Meldung nur ~40 % [6] (med) | T1-Kunde fragt nach Retrofit-Bestand ODER Zubau >500 MWh/Q | high |
| 5 | **EV-Lade-CPO-Leads (Ladesäulenregister)** · D2/F | Tägl./wöchentl. Diff neuer öffentl. Ladepunkte (Betreiber+Adresse+Technik) exklusiv an Lade-O&M/Backend/Netzanschluss-Dienstleister | **high** — identische Engine, freie REST-API+CSV, CC-BY 4.0, **BPV unkritisch** | low | 🟢 | Register diff-bar [49][50]; ~196.353 Ladepunkte (Stand 1.2.2026) [70] (Käufer-WTP spekulativ → med) | >5 neue Ladepunkte/Region/Woche ODER CPO-Zulieferer fragt an | high |
| 6 | **Hersteller-Co-Selling + BSW-Andockung** · C | GoldenTime als Lead-Vorlieferant in bestehende Hersteller-Verteilkanäle (Tesvolt/Solarwatt/Fenecon); BSW-Schnuppermitgliedschaft als Reichweiten-Türöffner | **high** — Hersteller haben Verteilkanal schon; BSW gratis, BPV-konform | med | 🟡 | Tesvolt „Zugang zu Projektanfragen" [30]; Solarwatt „Vorqualifizierte Leads" [31]; BSW 6 Mon. gratis [35] (high) | Erster Installateur-Pilot ist Hersteller-Fachpartner → warmer Intro; **Intersolar 23.–25.06.** | high |
| 7 | Gestufte Frische (Premium tagesfrisch) · E | Preisstaffel nach Lieferfrequenz: wöchentl. Batch vs. tagesfrischer Alert nach täglichem Export-Diff | high — reine Job-Frequenz, gleiche Engine | low | 🟢 | SolarReviews „as much as $300 per lead" exkl. [64]; Vainu Premium-Tier [59] (med) | Zwei Installateure wollen dasselbe Gebiet ODER Kunde will schnellere Lieferung | med |
| 8 | Lead-Magnet: Regional-Kostprobe · C | Kostenloser Mini-Report „X frische gewerbl. PV ohne Speicher in Ihrem PLZ-Gebiet" als Conversion-Türöffner über alle Kanäle | high — direkt aus dem Engine, ~0 Grenzkosten, multipliziert jeden Kanal | low | 🟢 | indirekt über belegte Lead-Zahlungsbereitschaft [36][37] (Mechanik spekulativ → low) | Erster Kanal-Test (BSW/LinkedIn) braucht ein konkretes Angebot | low |
| 9 | Biogas/Biomasse-Post-EEG (T2-Analog) · A/F | `EinheitenBiomasse` nahe 20-J.-EEG-Ende (join `biomass_eeg`/`Kwk`) → BHKW-/Flex-/Direktvermarktungs-Anbieter | high — eigene Tabellen im selben Pull, identische T2-Logik | low | 🟡 | Ausschreibung 2026 „1.126 MW" [10]; Biomethan im MaStR [15] (med) | PV-T2 steht als Produkt → Biogas-Filter dazuschalten; Gebotstermine | med |
| 10 | Direkt-Marktplatz mit Exklusivitäts-USP · C | Eigenständiger Lead-Verkauf positioniert „exklusiv pro Region an EINEN" — direkt gegen Massenportale | high — Exklusivität ist der Kern-Moat, am Markt bepreist | low | 🔴 | Leospardo „55 €/Lead", Standard max. 3, Voll-Exklusiv gegen Aufpreis [37]; DAA [36] (high) | CPL steigt >~50 € ODER Installateure beschweren sich über Lead-Recycling | high |
| 11 | PV-Finanzierung/Leasing-Leads · B | Frische Gewerbe-PV-Betreiber als (Re-)Finanzierungs-Leads → grenke u.a. | high — gleicher Pull, B2B via ABR gut greifbar | low | 🟡 | grenke verkauft PV-Leasing aktiv [20] (high; Pro-Lead-WTP spekulativ → med) | Erster Cross-Sell-Bündel-Pilot ODER Finanzierer fragt an | med |
| 12 | O&M/Monitoring/Reinigung-Onboarding · B | Frische Anlagen als Service-/Vertragskandidaten → meteocontrol/Solar-Log/Reinigung | high — nicht-konkurrierend, Gebiet mehrfach verwertbar | low | 🔴 | meteocontrol O&M+Monitoring [22]; ~31 Anbieter [23] (med; Lead-Kauf nicht belegt) | O&M-Anbieter fragt nach Frisch-Feed ODER freie Vertriebskapazität | med |
| 13 | Wind-Repowering / Post-EEG-Wind · A | `wind_extended` (frisch ODER IBN-Jahr nahe Förderende) + Anreicherung Nabenhöhe/Hersteller → Projektierer/Repowering/O&M | high — eigene Tabelle, Repowering-Felder vorhanden | med | 🟡 | „~16.000 MW … aus der Förderung" bis Ende 2025 [9] (med; Daten breit verfügbar) | Wind-Service/Projektierer als zahlender Kunde ODER EEG-Nachfolge ab 2027 | med |
| 14 | Enrichment-as-a-Service · E | Anreicherungs-Layer (Betreibergraph via ABR, Firmenstatus, Kontakt-Hinweise) separat bepreist | high — Betreibergraph schon im Export, gleiche Engine | med | 🔴 | Vainu CRM-Tier 4.200 €/J [59] (med; Pro-Record-Preise nur spekulativ) | Kunden reichern den Roh-Lead selbst an / fragen nach Kontext | med |
| 15 | Meta-Horizontale: Register-as-a-Filter-Engine · F | Dieselbe Engine über beliebige öffentl. Pflichtregister; jede Vertikale = neuer Filter → „Vertikale-Playbook" | high — kein neuer Tech-Stack, Export deckt viele Sparten ab [67] | low | 🟢 | Horizontale Trigger-Lead-Anbieter existieren, aber nicht register-/exklusiv-basiert [69] (med) | Zweite Vertikale (z. B. EV-CPO) verkauft eigenständig profitabel | med |
| 16 | Exklusivitäts-Marktplatz / Gebiets-Auktion · E | Knappe Gebiete per Auktion/Wartelistenpreis; gestaffelte Exklusivität (Premium/Duo/Trio) | med — Auktions-Tooling = Zusatzkomplexität für Solo | med | 🟡 | SolarReviews Stufenmodell + „$300/lead" [64] (med) | ≥1 Gebiet hat >1 zahlungsbereiten Interessenten | med |
| 17 | FR-Klon (ODRÉ ≥36 kW) · D1 | GoldenTime-Pipeline auf das franz. nationale Register: Monats-Diff ≥36-kW-PV, Speicher-Flag → FR-Installateure | high — gleiches Muster, anlagengenau ≥36 kW, Speicher im selben Register | med | 🟡 | ODRÉ anlagengenau ≥36 kW + Speicher [41] (Eignung high; WTP spekulativ) | DE-Modell hält Retainer UND FR-Pilotinstallateur signalisiert Interesse | high |
| 18 | Register-Trigger als Add-on für Signal-Anbieter (B2B2B) · X1/E | MaStR-PV-Frische als Daten-Feed an Implisense/Dealfront/databyte (kein Endkunden-Vertrieb) | high — gleicher Pull, anderer Abnehmer, passt zu 4 h/Woche | med | 🟢 | Anbieter integrieren „publicly available sources" [76][77] (kein Energie-Trigger belegt → low) | Ein Signal-Anbieter kündigt „Energie-/Nachhaltigkeits-Trigger" an | low |
| 19 | wMSB / Smart-Meter-Leads · B | Frische PV ≥7 kWp (iMSys-pflichtig) → wettbewerbliche Messstellenbetreiber | high — niedrige kW-Schwelle = großes Mengenpotenzial | med | 🟢 | iMSys ab 7 kWp + freie wMSB-Wahl [24] (med; wMSB-Lead-Kauf spekulativ) | Rollout-Pflicht verschärft sich ODER wMSB testet Lead-Zukauf | low |
| 20 | IT Conto-Energia-Kohorte (GSE) · D1 | GSE-Open-Data (Name+Steuerdaten+Leistung) → Post-Förder-Kohorten als Retrofit-Leadliste | high — reichste Betreiber-Identität, klare Förderkohorte | med | 🟡 | „IODL v2.0 … CSV … JSON" [44] (Datenbasis high; WTP spekulativ) | Atlaimpianti wieder anlagengenau live UND IT-Kanal vorhanden | med |
| 21 | OnSite-PPA-Leads (große Dächer) · B | Betriebe mit großen Dächern/Verbrauch → PPA-Anbieter (Mainova-Modell) | med — „große Dachfläche" nur indirekt aus Leistung → Anreicherung nötig | med | 🟡 | Mainova OnSite-PPA ab ~150.000 kWh/600 m² [21] (high; Lead-WTP spekulativ) | Dachflächen-/Verbrauchsproxy steht ODER PPA-Anbieter fragt an | med |
| 22 | Daten-Feed / API (Premium-Stufe) · E | Strukturierter Feed/Webhook/SFTP an größere Abnehmer statt Einzel-Leads | med — API/SLA-Engineering jenseits 4 h/Woche | high | 🟡 | Vainu „for Data" + Implisense API [59][61] (high für Modell; MaStR-PV white-space) | Abnehmer kauft Bulk/regionsübergreifend / will maschinelle Anbindung | high |
| 23 | CH EIV-Kohorte (Pronovo/BFE) · D1 | opendata.swiss-EIV: CH-Gewerbe-PV + KEV/EIV-Post-Förder-Listen → CH-Installateure | med — Granularität teils pro Kanton/Jahr aggregiert | med | 🟡 | „open data … regularly updated" [42] (Anlagengenauigkeit offen → med) | Geprüft: Datensatz pro Anlage (nicht pro Kanton/Jahr) mit Standort | med |
| 24 | Betreiberwechsel-Signal (ABR-Diff) · A | Diff: ABR-Wechsel bei gleicher Einheit = Eigentümer-/Betreiberwechsel → O&M/Asset-Mgmt/Versicherer/M&A | high — rein aus vorhandener Diff-Logik | med | 🟢 | Mechanik belegt [2] (WTP spekulativ; False-Positive bei Umfirmierung → med) | O&M/Asset-Kunde äußert Bedarf ODER Pilot trennt Wechsel sauber von Umfirmierung | med |
| 25 | Wind/Verbrennung-Repowering via Leistungshistorie · A | Diff auf Bruttoleistung/Nettonennleistung (Nicht-PV) → Wind-/BHKW-Service & Komponenten | high — Felder+Historie vorhanden, reiner Feld-Diff | med | 🟢 | Leistungshistorie+Erhöhung belegt [1] (WTP spekulativ) | Wind-/Biomasse-Vektor hat Kunden → Leistungs-Diff als Premium-Filter | med |
| 26 | CRM-Integration (Pipedrive/HubSpot) · E | Connector-App, die Leads ins CRM des Installateurs pusht; Marktplatz = Distribution | low — App-Bau/Review/Pflege jenseits 4 h/Woche | high | 🔴 | Pipedrive 100.000+ Firmen [62]; HubSpot „3 active installs" [63] (high) | Mehrere Kunden nennen dasselbe CRM UND ≥3 zahlende Kunden | high |
| 27 | White-Label-Lieferung (Hersteller/Installateur) · C/E | Lead-/Alert-Lieferung unter fremder Marke/Domain; ggf. weiterverkaufbar | med — Mehr-Mandanten-Verwaltung kostet Solo-Zeit | med | 🟡 | Hersteller-Programme versprechen Partnern Leads [31] (med; reiner WL-Markt spekulativ) | Abnehmer fragt nach eigener Marke/Weiterverkauf | low |
| 28 | Stilllegungs-Signal · A | Diff auf Stilllegungs-Datumsfelder → Rückbau/Recycling/Repowering/Projektentwickler | high — Felder in allen Tabellen, reiner Diff | med | 🟢 | Semantik belegt [3] (WTP spekulativ; oft verzögert gemeldet) | Rückbau-/Projektentwickler fragt nach freiwerdenden Standorten | med |
| 29 | PV-Erweiterung als Zweit-Einheit · A | Zweite Solar-Einheit (frische IBN) an ABR/Standort mit älterer PV = Aufstockung → PV-/Speicher-Anbieter | high — gleicher Pull/Join wie T1 | low | 🟢 | Zubau=neue Einheit belegt [1] (Aufstockung vs. unabhängige Neuanlage = Inferenz; WTP spekulativ) | T1-Kunde fragt nach „Bestandskunden, die erweitern" | med |
| 30 | Vergabe-Bieter-Intelligence · D2 | Datierte Alerts zu neuen öffentl. Solar-/Speicher-Ausschreibungen (TED/eForms) → **private** Bieter (EPC) | med — **BPV: nur Bieter-Seite**, nicht Auftraggeber; Markt besetzt | med | 🔴 | TED Search-API/eForms [51]; kommerzielle Vergabe-Monitore existieren (R1) (med) | Bestandskunde fragt „wer schreibt PV aus" ODER PV-CPV-Dichte hoch | med |
| 31 | Handelsregister-Trigger (Anreicherung) · D2 | Firmen-Trigger (Neugründung/GF-Wechsel/Kapital) via OffeneRegister als Anreicherung/Signal | med — Bulk vorhanden, aber veraltet; offizieller Live-Zugang fehlt | med | 🟡 | OffeneRegister >5 Mio Firmen, Bulk-JSONL, via Gazette gepflegt (Aktualität unklar) [53]; **R5-Risiko** bundesAPI §303a/b [54] (med) | Offizieller maschinenlesbarer HR-Zugang entsteht (Open-Data-Ausbau) | med |
| 32 | HV/EHV-Industrieverbraucher-Trigger · A2 | Frische HV/EHV-Verbrauchseinheiten (`electricity_consumer`) → EVU/Industrie-Flex-Vermarkter | high (Daten) — aber Nische winzig (nur HV/EHV) | low | 🟢 | Verbraucherobjekt existiert [7][12] (Käufer-WTP spekulativ → low) | EVU/Flex-Vermarkter fragt nach Industrie-Lastdaten | low |
| 33 | Dachdecker/Permit-Leads · F/D2 | Bauantrags-/Permit-Diff (neue Dächer/PV-Dach) → Dachdecker/Bedachungs-Großhandel (US-Modell) | med — Engine identisch, **aber** DE-Bauanträge fragmentiert/nicht zentral offen | high | 🔴 | BuildZoom „350M+ permits", Käufer „roofing/HVAC" [68] (US bewiesen; DE-Datenlage offen) | DE-Region bietet Einzel-Bauvorhaben als Open Data (z. B. „Digitale Baugenehmigung") | med |
| 34 | OT/IT-Security / NIS2-Leads · B | Frische Gewerbe-PV als Compliance-/Security-Lead → OT-Security/NIS2-Berater | med — NIS2-Zuordnung braucht Anreicherung (Größe/Sektor) | high | 🟢 | DNV „Wechselrichter … kritische Produkte" [25] (Segment entstehend → low) | Verbindliche NIS2-/Wechselrichter-Pflicht in Kraft | low |
| 35 | Energieberater/Effizienz-Leads · B | Frische PV-Betreiber als Folge-/Effizienz-Lead → **private** Energieberater (BPV: keine Behörden) | med — gleicher Pull; BPV beachten | low | 🟡 | BAFA fördert Audits f. Unternehmen [26] (Pro-Lead-WTP inferiert → low) | Berater-Netzwerk fragt nach Frisch-Leads | low |
| 36 | Erfolgs-/Rev-Share (Outcome-Pricing) · E | Bezahlung pro Termin/abgeschlossener Installation statt Retainer | low — Attribution/Streit, braucht Einblick in Kunden-Vertrieb | high | 🟡 | Outcome-Pricing-Analoga (nur Scout, spekulativ) | Kunde lehnt Retainer ab, glaubt aber an Conversion; Closed-Loop-Feedback da | low |
| 37 | Daten-Kooperative · E | Installateure speisen Conversion-Feedback zurück → besseres Scoring + Lock-in | low — Zusatz-Datenfluss/Governance, widerspricht „ohne Datenbasis-Wechsel" | high | 🟡 | Bombora Co-op real [65] (Modell tragfähig; Revenue-Allocation kritisch → low) | Viele Kunden je Region mit verlässlichem Conversion-Feedback (Spätstadium) | low |
| 38 | Handelsregister-Live via bundesAPI · D2 | Punktuelle Echtzeit-Firmenanreicherung einzelner Leads | low — „60 Abrufe/h" + StGB-Risiko → nicht skalierbar | low | ⚫ | Limit/Risiko belegt [54] (R5) | Offizieller maschinenlesbarer Zugang entsteht → Risiko entfällt | high |
| 39 | EU-Beihilfe-Empfänger-Trigger · D2 | „Förderzusage X" für Großempfänger oberhalb EU-Transparenzschwelle | low — Schwelle schneidet KMU/typische Gewerbe-PV weg | med | ⏸ | Felder belegt [55]; Schwelle nicht verifiziert (low) | Schwelle gesenkt ODER GoldenTime ins Utility-Segment | low |
| 40 | §14a-WP/Wallbox-Leads aus MaStR · A2/F | (gewünscht) WP/Wallbox-Neuinstallationen aus MaStR | — **KILL**: NS-Verbraucher nicht meldepflichtig; §14a → Netzbetreiber; kein Lade-Objekt | high | ⚫ | Käufermarkt groß (WP +55 % [14]) **aber Trigger fehlt** [15][16][7] (Kill high) | Nur falls ein öffentliches bundesweites WP-/§14a-Register mit Bulk-Export entsteht | high |
| 41 | AT E-Control-Register · D1 | (R4) GoldenTime-Produkt auf AT-Register | — **KILL**: nur HKN-Daten, kein Betreibergraph/Adresse; OeMAG-Kohorte nicht offen | high | ⚫ | Negativbefund belegt [46][47] (high) | AT führt MaStR-artiges offenes Betreiber-Register ein | high |
| 42 | Gewerbeanmeldungen-Trigger · D2 | Einzelne Gewerbean-/abmeldungen als Neugründungs-Signal | — **KILL**: nur aggregiert öffentlich (Destatis) | high | ⚫ | Negativbefund [56] (high) | Gesetzliche Öffnung einzelbetrieblicher Gewerbedaten (unwahrscheinlich) | high |

---

## Top 3–5 zuerst (Solo · 4 h/Woche · BPV · Berater-Essen ~27.06.)
Reihenfolge = Hebel ÷ Aufwand, mit Blick auf das Gespräch am ~27.06. (zwei Tage nach Intersolar/ees Europe):

1. **B — Mehrfachverwertung pro Gebiet, beginnend mit Direktvermarktern ≥100 kWp** (#1+#2). Der größte
   Umsatzmultiplikator ohne neue Datenarbeit: derselbe Pull, derselbe frische Lead, mehrere
   nicht-konkurrierende Abnehmer pro Gebiet bei ~0 Grenzkosten. Direktvermarkter haben *strukturell
   garantierten* Bedarf (Pflicht-DV ab 100 kWp [18][19]) und sind nur ein Leistungsfilter entfernt.
   *Kill-/Validierungsfrage fürs Essen:* „Würde ein regionaler Direktvermarkter den frischen ≥100-kWp-Lead
   exklusiv kaufen, den mein Speicher-Installateur ohnehin bekommt?"
2. **E — „Kaufsignal-Radar"-Abo + gestufte Frische** (#3+#7). Verwandelt Einmal-Leads in wiederkehrenden,
   verteidigbaren Umsatz (LTV) — der Diff läuft ohnehin. Analog hart belegt (Implisense 1.500 €/Monat [61]).
   *Validierung:* „Zahlt der erste Pilotkunde lieber monatlich für laufende Frische als pro Lead?"
3. **A — Speicher-Retrofit + Post-EEG-Erweiterung (PV-T2 → Biogas)** (#4+#9). Neue Produktlinien auf
   *demselben* Pull; Speicher-Retrofit bedient sogar den *bestehenden* Käufertyp. Niedriger Aufwand.
   *Validierung:* „Will mein Speicher-Installateur auch Bestands-PV, die *gerade jetzt* einen Speicher
   nachrüstet?"
4. **D/F — EV-Lade-CPO über das Ladesäulenregister** (#5). Der billigste Beweis, dass die Engine horizontal
   ist: ein zweites, sauberes, offenes Register (CC-BY 4.0, REST-API, tägl. [49][50]), **BPV unkritisch**,
   identische Diff-Mechanik. *Kill-Frage:* „Entstehen pro Zielregion genug *neue* öffentliche Ladepunkte/
   Woche, damit ein CPO-Zulieferer dafür zahlt?"
5. **C — Käufer-Akquise: Hersteller-Co-Selling + BSW-Schnuppermitgliedschaft, getaktet auf Intersolar/ees
   Europe (23.–25.06.)** (#6). Ohne wiederholbaren Kanal zu den Käufern skaliert keine der obigen Optionen.
   Hersteller verteilen bereits Leads [30][31][32]; die BSW-Mitgliedschaft ist 6 Monate gratis [35]. Das
   Messe-Fenster liegt *unmittelbar* vor dem Berater-Essen — als Networking/Lead-Probe nutzbar (kein Stand).

**Querschnitt fürs Essen (kein eigener Vektor):** Das Kernprodukt ist *white-space* [71][73], **aber** der
Moat ist nicht die Datenquelle (Open-Source-Engine + gratis Daten [71][72]), sondern Frische + Exklusivität +
Anreicherung + Tempo. Die obigen 5 Hebel *vertiefen genau diesen Moat* (mehr Käufer/Gebiet, Verstetigung,
mehr Trigger, zweite Vertikale, Kanal) — statt ihn auf wackeligen Boden (eigene neue Datenquelle) zu stellen.

## Uncertainties & contradictions
- **Zahlungsbereitschaft pro Segment ist überwiegend abgeleitet, nicht direkt belegt.** Hart belegt sind
  PV-Lead-Preise (20–125 €/exkl.) und Hersteller-Lead-Verteilung; die Pro-Lead-WTP von Direktvermarktern,
  O&M, wMSB, CPOs etc. ist **spekulativ** und muss je Vektor pilotiert werden. Das ist die größte Lücke.
- **Regulatorische Stabilität (B/#2):** Die 100-kWp-DV-Pflichtschwelle gilt 2025/26 unverändert; eine
  Absenkung (Richtung 25 kWp ~2027) war im Gespräch, ist final aber **nicht** beschlossen [18]. Eine Senkung
  vergrößert das Mengenpotenzial (Chance), erhöht aber die Planungsunsicherheit → als Revisit-Trigger geführt.
- **Stärkste Gegenposition (R1-Risiko):** Weil open-MaStR Open-Source und der Gesamtexport gratis +
  kommerziell lizenziert ist [71][72], ist die technische Eintrittsbarriere niedrig. Ein finanzstärkerer
  Wettbewerber (oder solarzubau.de, das heute nur Aggregate zeigt [73]) könnte das Einzelanlagen-Lead-Produkt
  kopieren. Der Schutz ist *nicht* technisch, sondern **vertragliche Gebiets-Exklusivität + Frische-Vorsprung
  + Kundenbindung (Abo)**. → Vektoren #1/#3/#6 sind damit auch *defensiv* die richtigen ersten Schritte.
- **Datenlücken in den Triggern selbst:** Speicher-Retrofit nur ~40 % fristgerecht gemeldet [6]; Ladepunkte
  ohne Inbetriebnahmedatum (Frische nur per Diff) [49]; „ohne Speicher"/„kein Ladepunkt" bleiben „nicht
  gemeldet", nicht „existiert nicht" (MaStR-Gotcha gilt analog).
- **R5-Rechtsflags (nicht hier gelöst — R5 besitzt es):** Handelsregister-Scraping via bundesAPI berührt
  §§303a/b StGB + 60/h-Limit [54]; Vergabe-Auftraggeber sind öffentliche Stellen → BPV verbietet sie als
  *Kunden* [51]; Ladesäulen-CC-BY 4.0 [49] und MaStR-Datenlizenz DE 2.0 [72] sind dagegen unkritisch.
- **D1-Geografie widerspricht der R4-Engführung:** Der R4-Fokus *Österreich* trägt **nicht** (E-Control
  HKN-only [46]); **FR/CH/IT** sind die tragfähigeren Auslands-Kandidaten. R4 sollte das aufnehmen.

## Open questions / next steps (für `/deepen expansion-map <Achse>`)
- **B (zuerst):** Pro-Lead-/Retainer-WTP von Direktvermarktern, MSB, PPA-Anbietern *empirisch* erheben
  (3–5 Discovery-Gespräche je Segment); Bündel-/Multi-Tenant-Pricing-Modell rechnen.
- **A:** Auf einem Stichtag-Export quantifizieren, wie viele Speicher-Retrofit-/Betreiberwechsel-/Biogas-
  Post-EEG-Events pro Woche/Region real anfallen (Mengen-Gate vor Vermarktung).
- **D2/F (EV):** Ladesäulen-Diff bauen (Frische-Rekonstruktion); wöchentl. Neu-Ladepunkt-Volumen je Zielregion
  messen; einen CPO-Zulieferer als Pilotkäufer ansprechen.
- **C (= R2):** Konkreten Andock-Pfad zu *einem* Hersteller-Partnerprogramm (Tesvolt/Fenecon) ausarbeiten;
  BSW-Schnuppermitgliedschaft jetzt starten; Lead-Magnet-Kostprobe als Conversion-Asset bauen.
- **D1 (= R4, aber umlenken):** ODRÉ-Schema (FR) tief lesen (Felder, Speicher-Flag, Kadenz) als bestes
  Auslands-Analog; CH-EIV-Anlagengenauigkeit prüfen; AT als negativ dokumentieren.
- **E:** „Kaufsignal-Radar"-Abo als Pricing-/Lieferformat spezifizieren (wöchentl. vs. tagesfrisch-Premium).
- **R1/R5:** volle Wettbewerbs- bzw. Rechtsanalyse (eigene Aufträge) — diese Landkarte liefert nur die Flags.

## Quellen
Abgerufen **2026-06-14**; Publikationsdaten in Klammern. Primär > sekundär > tertiär. (Volle, nach Achse
gruppierte Liste inkl. Glaubwürdigkeitsnotizen in `sources.md`; URL-/Query-Log in `_sources/ledger.log`.)

1. MaStR-Hilfe – Datenänderung einer Einheit (Leistungshistorie; PV-Sonderregel) — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitDatenaenderung.html — primär (offiziell), hoch.
2. MaStR-Hilfe – Betreiberwechsel — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitBetreiberwechsel.html — primär, hoch.
3. MaStR-Hilfe – Stilllegung einer Einheit — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitstilllegungEinheit.html — primär, hoch.
4. marktstammdatenregister-dev/mastr – Gesamtexport-Spezifikation (YAML je Einheit) — https://github.com/marktstammdatenregister-dev/mastr — primär (Spec am Exportformat), hoch.
5. Verbraucherzentrale – MaStR bei Solaranlage & Co. — https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/marktstammdatenregister-das-muessen-sie-bei-solaranlage-und-co-wissen-33124 — sekundär, hoch.
6. photovoltaik.info – Speicher-Nachrüstung im MaStR melden — https://www.photovoltaik.info/stromspeicher-nachruesten-mastr-meldung/ — sekundär (Fachportal), mittel.
7. open-mastr Dataset-Doku (Tabellen; „electricity_consumer = Only large consumers") — https://open-mastr.readthedocs.io/en/latest/dataset/ — primär (Engine-Doku), hoch.
8. pv magazine – Batterie-Rekordzubau Q1/2026 (2026-05-08) — https://www.pv-magazine.de/2026/05/08/starkes-wachstum-im-grossspeichermarkt-fuehrt-zu-batterie-rekordzubau-von-ueber-2-gigawattstunden-im-1-quartal-2026/ — sekundär, hoch.
9. windindustrie-in-deutschland.de – Repowering von Altanlagen — https://www.windindustrie-in-deutschland.de/fachartikel/repowering-von-altanlagen-was-bieten-die-neuregelungen-und-wo-finden-sie-ihre-grenzen — sekundär, mittel.
10. next-kraftwerke.de – Anschlussförderung Biogas — https://www.next-kraftwerke.de/wissen/anschlussfoederung-biogas — sekundär, mittel.
11. MaStR-Hilfe – FAQ (HV/EHV-Verbraucher) — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/faq.html — primär, hoch.
12. Dokumentation MaStR Gesamtdatenexport, PDF Rev. 26.1.2 (2026-06-11) — https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf — primär (Datenwörterbuch), höchste.
13. MaStR-Hilfe – Schutz/Freigabe (natürliche Personen / ≤30 kWp) — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/schutzFreigabe.html — primär, hoch.
14. BWP – Wärmepumpen-Absatz 2025 (+55 %) (2026-01-27) — https://www.waermepumpe.de/presse/pressemitteilungen/details/ueber-50-prozent-im-plus-waermepumpen-absatz-steigt-2025-deutlich/ — sekundär (Verband), hoch.
15. MaStR-Hilfe – Registrierungspflichtige Anlagen (keine WP in Wohnhäusern; Biomethan) — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/registrierungVerpflichtendAnlagen.html — primär, hoch.
16. BNetzA – Steuerbare Verbrauchseinrichtungen §14a EnWG — https://www.bundesnetzagentur.de/DE/Vportal/Energie/SteuerbareVBE/start.html — primär, hoch.
17. MaStR-Hilfe – Gesamtdatenexport (vertrauliche Felder ausgeschlossen) — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/datenexport.html — primär, hoch.
18. Next Kraftwerke – PV-Direktvermarktung (ab 100 kWp) — https://www.next-kraftwerke.de/virtuelles-kraftwerk/solar — primär (Anbieter), hoch.
19. e2m (Energy2market) – Photovoltaik — https://www.e2m.energy/de/photovoltaik.html — primär (Anbieter), hoch.
20. grenke – Photovoltaik-Leasing — https://www.grenke.de/loesungen/photovoltaik-leasing/ — primär (Anbieter), hoch.
21. Mainova – PV OnSite PPA für Unternehmen — https://www.mainova.de/de/fuer-unternehmen/loesungen/energie-selbst-erzeugen/onsite-ppa — primär (Anbieter), hoch.
22. meteocontrol – VCOM CMMS (Monitoring + O&M) — https://www.meteocontrol.com/unternehmen/news/detail/meteocontrol-erweitert-pv-monitoringportal-um-vcom-cmms/ — primär (Anbieter), mittel.
23. pv magazine – Monitoring-Anbietervergleich (~31 Anbieter) — https://www.pv-magazine.de/unternehmensmeldungen/monitoring-software-solar-log-meteocontrol-solytic-7-weitere-anbieter-im-vergleich/ — sekundär, mittel.
24. eha – Smart-Meter-Pflicht (iMSys ab 7 kWp; wMSB) — https://www.eha.net/blog/details/smart-meter-pflicht.html — sekundär (Anbieter-Blog), mittel.
25. pv magazine – DNV-Bericht Cybersecurity PV (2025-04-29) — https://www.pv-magazine.de/2025/04/29/cybersecurity-dnv-bericht-fordert-neue-standards-fuer-photovoltaik/ — sekundär, mittel.
26. BAFA – Energieberatung/Energieaudit für Unternehmen — https://www.bafa.de/DE/Energie/Energieberatung/energieberatung_node.html — primär (Behörde), hoch.
27. leadscraper.de – Gewerbliche PV-Leads kaufen — https://www.leadscraper.de/blog/gewerbliche-pv-leads-kaufen — sekundär (Anbieter, werblich), mittel.
28. SMART11 – Photovoltaik-Leads (Preise) — https://www.smart11.de/photovoltaik-leads — sekundär (Anbieter, werblich), mittel.
29. lead-gene.com – B2B Cost-per-Lead Benchmark 2026 — https://lead-gene.com/de/blog/cout-par-lead-b2b-2026-benchmark — sekundär (Agentur), mittel.
30. TESVOLT – Partnerprogramm — https://www.tesvolt.com/de/partner/partnerprogramm.html — primär (Hersteller), hoch.
31. Solarwatt – Fachpartnerprogramm — https://www.solarwatt.de/fachpartner/solarwatt-partner — primär (Hersteller), hoch.
32. FENECON – für Gewerbebetriebe — https://www.fenecon.de/fenecon-gewerbebetriebe — primär (Hersteller), hoch.
33. Sungrow – Partner — https://www.sungrowpower.com/de/de/partners — primär (Hersteller), mittel.
34. RCT Power – Vertriebspartner — https://www.rct-power.com/de/vertriebspartner.html — primär (Hersteller), mittel.
35. BSW-Solar – Schnuppermitgliedschaft — https://www.solarwirtschaft.de/dabei-sein/schnuppermitgliedschaft/ — primär (Verband), hoch.
36. TapTapHome / DAA GmbH – Fachpartner — https://www.taptaphome.com/de/ueber-uns/fachpartner — sekundär (Marktreferenz), hoch.
37. Leospardo – Photovoltaik-Leads kaufen — https://leospardo.de/fachpartner/photovoltaik-leads-kaufen/ — sekundär (Marktreferenz), hoch.
38. photovoltaik.eu (Reichweite/Mediadaten) — https://www.photovoltaik.eu/ — sekundär (Fachmedium), mittel.
39. pv magazine Deutschland – Mediainformation — https://www.pv-magazine.de/mediainformation/ — primär (Verlag), mittel.
40. Intersolar Europe / ees Europe – Quick Facts (23.–25.06.2026) — https://www.intersolar.de/exhibition-quick-facts — primär (Messe), hoch.
41. ODRÉ/RTE – Registre national des installations de production et de stockage d'électricité (FR) — https://odre.opendatasoft.com/explore/dataset/registre-national-installation-production-stockage-electricite-agrege/information/?flg=fr-fr — primär (OpenData), hoch.
42. opendata.swiss – Einmalvergütung für PV (CH, BFE/Pronovo) — https://opendata.swiss/de/dataset/einmalvergutung-fur-photovoltaikanlagen — primär (Bund-Portal), mittel.
43. data.sz.ch – Einmalvergütung PV (CH, Kantons-Mirror) — https://data.sz.ch/explore/dataset/einmalverguetung_fuer_photovoltaikanlagen/ — primär, mittel.
44. opendata GSE – Beneficiari incentivi Conto Energia (IT) — http://opendata.gse.it/dataset?res_format=JSON — primär (Anbieter), mittel.
45. GSE – Atlaimpianti (IT) — https://www.gse.it/dati-e-scenari/atlaimpianti — primär, mittel.
46. E-Control – Anlagenregister (AT; HKN-only) — https://anlagenregister.at/ — primär (Register), hoch.
47. BMLUK – Marktprämie PV (AT) — https://www.bmluk.gv.at/themen/klima-und-umwelt/klima/energiewende/erneuerbare-energie/foerderungen-pv/marktpraemie2.html — primär, mittel.
48. Energinet – Energidataservice (DK) — https://en.energinet.dk/energy-data/ — tertiär (Scout-Annotation), niedrig.
49. BNetzA – Ladesäulenkarte/-register (CSV/XLSX, CC BY 4.0) — https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenkarte/start.html — primär, hoch.
50. BNetzA – E-Mobilität Schnittstellen (REST JSON/XML, täglich) — https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Schnittstellen/artikel.html — primär, hoch.
51. TED – Developers' corner for reusers (Search-API, eForms, LOD) — https://ted.europa.eu/de/simap/developers-corner-for-reusers — primär (EU), hoch.
52. WBS Legal – Handelsregister seit 1.8.2022 gratis (DiRUG) — https://www.wbs.legal/handelsrecht-gesellschaftsrecht/seit-dem-1-8-2022-das-handelsregister-ist-in-deutschland-jetzt-gratis-61548/ — tertiär (Kanzlei-Blog), mittel.
53. OffeneRegister.de – Daten (Bulk-JSONL, >5 Mio Firmen; laufend via Gazette-Notices gepflegt, Aktualität/Vollständigkeit pro Datensatz unklar; SQLite/SQL-API auf der aktuellen Seite nicht verifiziert) — https://offeneregister.de/daten/ — sekundär (Open-Data-Repo), mittel.
54. bundesAPI/handelsregister (GitHub; 60/h, §§303a/b StGB) — https://github.com/bundesAPI/handelsregister — primär (Repo), hoch.
55. EU State Aid Transparency Public Search — https://webgate.ec.europa.eu/competition/transparency/public?lang=en — primär (EU), hoch.
56. Destatis – Erläuterungen Gewerbeanzeigen (nur aggregiert) — https://www.destatis.de/DE/Themen/Branchen-Unternehmen/Unternehmen/Gewerbemeldungen-Insolvenzen/Methoden/Erlaeuterungen/erlaeuterungen-gewerbeanzeigen.html — primär, hoch.
57. Destatis – Baugenehmigungen (nur Aggregat) — https://www.destatis.de/DE/Themen/Branchen-Unternehmen/Bauen/Tabellen/baugenehmigungen.html — primär, hoch.
58. Nationaler Bekanntmachungsservice / Open-Data-Richtlinie (oeffentlichevergabe.de) — https://oeffentlichevergabe.de/ui/de/Open-Data-Richtlinie — primär, niedrig (JS-gerendert, nicht direkt verifiziert).
59. Vainu – Pricing („Vainu for Data": Webhook/SFTP/API) — https://www.vainu.com/pricing — primär (Anbieter), hoch.
60. Vainu Developers – Signal and Event Data (~80 Typen) — https://developers.vainu.com/docs/signal-and-event-data — primär, hoch.
61. Implisense – Services („Signal Retainer … €1,500/month"; 2,5 Mio Firmen; API) — https://implisense.com/en/services/ — primär (Anbieter, DACH), hoch.
62. Pipedrive Developers – About the Marketplace — https://pipedrive.readme.io/docs/about-the-marketplace — primär, hoch.
63. HubSpot – App-Marketplace listing requirements (min. 3 Installs) — https://developers.hubspot.com/docs/guides/apps/marketplace/app-marketplace-listing-requirements — sekundär (offizielle Doku), mittel.
64. SolarReviews – Solar Leads (Exclusive bis $300; Duo/Trio/Quad) — https://www.solarreviews.com/solar-leads — sekundär (US-Branchenseite), mittel.
65. Bombora – Data Co-op (200+ Publisher; 86 % exklusiv) — https://bombora.com/co-op — primär (Betreiber, werblich), mittel.
66. Dealfront/Echobot – Monitoring Suchprofil-Typen (Help Center) — https://help.leadfeeder.com/en/articles/13922294-echobot-monitoring-suchprofil-typen-und-ergebnisliste — primär (Produktdoku), mittel.
67. open-mastr – Dokumentation (Export deckt Erzeugung/Speicher/Verbraucher/Gas ab) — https://open-mastr.readthedocs.io/en/latest/ — primär, hoch.
68. BuildZoom – How real-time permit data is reshaping construction sales (2025-05-06) — https://www.buildzoom.com/blog/how-real-time-permit-data-is-reshaping-construction-sales-for-manufacturers-and-distributors — sekundär (US), mittel.
69. PredictLeads – Sales trigger data for B2B outreach (2026-05-20) — https://blog.predictleads.com/2026/05/20/sales-trigger-data-b2b-outreach-workflows — sekundär, mittel.
70. ecomento – 196.353 öffentliche Ladepunkte (2026-03-11) — https://ecomento.de/2026/03/11/bundesnetzagentur-jetzt-196353-oeffentliche-ladepunkte-in-deutschland/ — sekundär, mittel.
71. open-MaStR (OpenEnergyPlatform) – GitHub (Engine commodity/Open-Source) — https://github.com/OpenEnergyPlatform/open-MaStR — primär, hoch.
72. MaStR Datendownload (Datenlizenz Deutschland 2.0 – kommerziell) — https://www.marktstammdatenregister.de/MaStR/Datendownload — primär, hoch.
73. solarzubau.de – Daten (MaStR nur als Aggregat, CC-BY) — https://solarzubau.de/daten/ — primär, hoch.
74. online-adressen-kaufen.de – Photovoltaik-Leads („Exklusive Leads ab 60€") — https://online-adressen-kaufen.de/photovoltaik-leads/ — primär (Anbieter), mittel.
75. echtsolar.de – DAA GmbH PV-Vermittler-Portrait — https://echtsolar.de/daa-gmbh-pv-vermittler/ — sekundär, mittel.
76. Implisense – Homepage (EN) — https://implisense.com/en/ — primär, hoch.
77. Dealfront (Echobot + Leadfeeder) — https://www.leadfeeder.com/dealfront/ — primär, hoch.
78. digital-affin.de – B2B-Datenbank-Vergleich (databyte) — https://www.digital-affin.de/blog/b2b-datenbank/ — sekundär, mittel.
79. Enpal – PM enpal.pro B2B-Plattform — https://www.corporate.enpal.com/pressemitteilungen/enpal-erweitert-geschaftsmodell-um-b2b-plattform-enpal-pro — primär, mittel.

_Cross-Run-Basis (nicht neu erhoben): T1/T2, Pipeline & Gotchas aus `research/mastr-pv-leads/report.md` und `knowledge/mastr-buy-signals.md`._
