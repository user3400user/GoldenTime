# GoldenTime — KONZEPT-LANDKARTE (v1)
**Stand: 18.06.2026 · Lebendes Artefakt (§4b/§8 des Loop-Briefings) · erzeugt im Konzept-Vorlauf (Loop −1, §5).**
**Zweck:** das ZWEITE Ziel des Loops — nicht eine a-priori-Spec, sondern aus **erfolgreichen, ehrlichen Markt-Vorbildern** abgeleitete, wedge-gefilterte, belegte Anforderungen. Wird in jeder Recherche-Stufe geprüft/erweitert.

> **Provenienz:** strukturierte 4-Tier-Live-Web-Recherche (7-Agenten-Workflow, ~20 Anbieter, 124 Tool-Calls) → 3-Wege-Wedge-Filter-Synthese → **adversariale Skeptiker-Kritik**. Die Kritik hat **drei verifizierte Selbsttäuschungen** der Roh-Synthese gefunden; sie sind unten **eingearbeitet** (§3, §5), gegen den **echten Code** geprüft (nicht gegen STATE.md-Selbstreport). Recherche-Ehrlichkeit war hoch (dünne Trefferlagen als Befund gewertet, Negativ-Urteile load-bearing); die Synthese-Optimismen sind re-kalibriert.

---

## 0 · Verdikt in drei Sätzen
1. **Die Marktlücke ist real und scharf belegt:** Über ~20 Anbieter in 5 Tiers verkauft **kein einziger** die Kombination der vier Wedge-Säulen — sie existieren nur **einzeln** bei verschiedenen Playern (Solar-Lead-Marktplätze beherrschen *exklusiv+regional*, Sales-Intelligence beherrscht *register-getriggertes Kaufsignal*, Register-Datenprodukte beherrschen *Provenance*, aber niemand kombiniert sie vertikal+exklusiv+frisch+ehrlich).
2. **Der gefährlichste Befund ist intern, nicht extern:** Die am Markt am stärksten validierte, kategorieweit unbesetzte Säule — **regionale Abnehmer-Exklusivität** — ist in GoldenTimes eigenem Code **nicht erzwungen** (`record_delivery` 0 Produktions-Aufrufer). Marktlücke ≠ gebauter Burggraben.
3. **Die zwei Säulen mit dem meisten Aufholbedarf** sind genau die, die der Markt am stärksten honoriert und der Käufer am lautesten vermisst: **Exklusivität/Dedupe (im Code unverdrahtet)** und **sichtbare Frische (im Lieferpfad nicht gebaut)**.

---

## 1 · Der Wedge — die vier Säulen (Gründer bestätigt die Definition, §8)
> **Wedge = Kaufmoment-Timing + regionale Exklusivität + Frische + ehrliche Provenance.** Reihenfolge des Filters ist load-bearing (erst Wedge-Relevanz, dann Solo-machbar, dann automatisieren-oder-killen).

| # | Säule | Markt-Status laut Recherche |
|---|---|---|
| **1** | **Kaufmoment-Timing** (Betrieb hat *gerade* PV ohne Speicher angemeldet) | Validiert als großes Geschäftsmodell (Dealfront/6sense „Kaufmoment als Produkt"), aber **probabilistisch/Black-Box**. GoldenTimes **deterministisches, behördlich belegtes** Signal ist härter + ehrlicher. **Makro-Rückenwind:** PV-Neugeschäft −21 % (Heim) bis −33 % (Gewerbedach) Q1 2026, Speicher-Nachrüstung wächst (BSW-Solar). |
| **2** | **Regionale Abnehmer-Exklusivität** (1 Kunde pro Gebiet) | **Kategorieweit unbesetzt** in Sales-Intelligence (alle verkaufen dieselbe DB an alle; Exklusivität nur supply-side bei Bombora). Im Solar-Lead-Markt **etabliert + 3–5× bepreist** (geteilt 25–75 € → exklusiv 120–200 €). **ABER:** Exklusivität allein ist im Solar-Markt schon besetzt (Leadfluss) → nur die **Kombination** differenziert. |
| **3** | **Frische** (wöchentlich, Lead-Alter sichtbar) | Branchen-Best-Practice (Apollo predigt „field-level last-verified timestamps"); Käufer-Schmerz Nr. 1 ist „Leads Monate alt". **Im DE-Registermarkt** ist die Frische-Erwartung gesunken (Handelsregister seit Aug 2022 monatlich) — wöchentlich aus MaStR wäre überdurchschnittlich. *(⚠ Register-Vergleich nicht 1:1 — s. §5.)* |
| **4** | **Ehrliche Provenance** (Quelllink je Lead, dl-de-Lizenz, kalibrierte Konfidenz) | **Am breitesten validiertes Muster.** Dealfront (per-record Deep-Link), Bombora („Provenance verkauft"), OpenCorporates („Verified on [Date] via [Registry]"), OpenSanctions (Feld-Ebene: Quelle+Zeit+**Rohwert**). Alle SI-Majors zeigen Herkunft **nicht** je Datenpunkt → GoldenTimes Quelllink je Lead ist transparenter als der ganze Markt. |

---

## 2 · Markt-Landkarte — wo die Säulen einzeln leben (Beleg-Auszug)

| Tier | Vorbild (Beleg) | Übertragbares Muster | Trifft Säule |
|---|---|---|---|
| 1 direkt | **EliteLeadz** ([eliteleadz.de](https://eliteleadz.de/)) — „Batteriespeicher-Nachrüst-Leads für bestehende PV-Besitzer", exkl., 60–120 €/Lead | PV-ohne-Speicher-Segment IST verkaufbar — aber **demand-side**, Quelle verschleiert | 1+2 *(schwacher Beleg — s. §5)* |
| 1 direkt | **DAA/Aroundhome/WattFox** ([daa.net](https://www.daa.net/en/)) — Lead an **bis zu 5** Anbieter | Anti-Muster = Status quo, gegen den GoldenTime steht | (Negativ alle 4) |
| 1 direkt | **Dealfront** (Echobot) ([leadfeeder.com](https://www.leadfeeder.com/blog/intent-data/trigger-events-b2b-sales/)) — register-getriggertes Kaufsignal als Abo | Struktureller Hauptanalog; GoldenTime = vertikale+exklusive+frische Verengung | 1+3 |
| 1 direkt | **pvXchange/EUPD/BSW** ([pvxchange.com](https://www.pvxchange.com/Price-Index)) — MaStR-Neuanlagen nur **quartalsweise/anonym/Aggregat** | Granularitäts-/Frische-Lücke (wöchentlich, lead-level, exklusiv ist unbesetzt) | 3 (Negativ-Abgrenzung) |
| 2a SI-DACH | **Dealfront** ([dealfront.com/sources](https://www.dealfront.com/sources/)) — „we indicate next to each piece of information where data comes from" | **Per-record Quell-Backtrace mit Deep-Link** = Provenance sichtbar, nicht versteckt | 4 |
| 2a SI-DACH | **Implisense** ([implisense.com](https://implisense.com/en)) — personalisierte Signal-**Feeds** + „register-based"-Badge, Snapshot→Event→Alert, API ab 300 €/Mo | **DACH-Direktvorbild der Diff-Engine** (Monitoring→Push), Feed statt Self-Service-Suche | 1+3+Liefer-UX |
| 2a SI-DACH | **Cognism** ([cognism.com/compliance](https://www.cognism.com/compliance)) — **Art 6(1)(f) explizit** als Rechtsgrundlage + Benachrichtigung + DNC | Vorbild für die DSGVO-Anwalts-Mappe *(⚠ Reifegrad/Datentyp ≠ Solo-Gründer — s. §7)* | 4 + harte Grenze |
| 2a SI-DACH | **North Data** ([northdata.com](https://www.northdata.com/_premium)) — benennt Latenz-Ursache **ehrlich**, transparente öffentliche Preise (49 €/Mo) | Ehrlichkeit + Transparenz als Marke; Watchlist-Alert = Self-Service-Push | 3+4 |
| 2b SI-global | **Apollo** ([apollo.io/insights](https://www.apollo.io/insights/how-do-i-evaluate-a-sales-intelligence-platform-based-on-data-freshness-and-update-frequency)) — „freshness … the primary economic lever", verlangt field-level last-verified | Frische als **ökonomisches Verkaufsargument**, nicht Nice-to-have | 3 |
| 2b SI-global | **Bombora** ([bombora.com](https://bombora.com/our-data/)) — „not scraped … with consent, traceable" + 86 % exklusiver Daten-**Zugang** | Provenance VERKAUFT; Exklusivität ist **zahlungswirksam** — aber supply-side | 4 (+2 Kontrast) |
| 2b SI-global | **Lusha/Clay/6sense/ZoomInfo** — Konfidenz-Score sichtbar (Lusha), pay-per-match (Clay), Kaufmoment probabilistisch (6sense) | Konfidenz sichtbar (gut) / generierte Daten (schlecht) / „zahle nur für Treffer" / deterministisch schlägt Black-Box | 1+3+4 |
| 3 ehrlich | **OpenSanctions** ([opensanctions.org/docs](https://www.opensanctions.org/docs/data/)) — Quelle+Zeit+**Rohwert vor Normalisierung** je Feld | **Feld-Provenance** = Anti-Halluzinations-Invariante in Reinform | 4 |
| 3 ehrlich | **OpenCorporates** ([blog](https://blog.opencorporates.com/2025/11/18/data-provenance-explained/)) — „Verified on [Date] via [Registry]" | Fertiger UI-Baustein für den Provenance-Pitch | 4 |
| 3 ehrlich | **companyinfo.de** ([companyinfo.de](https://companyinfo.de/handelsregister-api-firmendaten-kyc-gwg/)) — Triade „Quelle/Datum/Ergebnis", „was nachweisbar ist statt was stimmt" | 1:1 das GoldenTime-Lead-Modell; ihr **DSGVO-Blindfleck** = unsere Warnung | 4 + harte Grenze |
| 4 Käufer | **Andreas May** ([andreas-may.com](https://andreas-may.com/photovoltaik-leads-kaufen/)) — Preistabelle: geteilt 25–75 € / exklusiv 120–200 € | **Pricing-Anker**: Exklusivität ist die Preisachse Nr. 1, 3–5× Aufschlag | 2 + Pricing |
| 4 Käufer | **P1 Commerce / Aroundhome-Erfahrung** ([p1commerce.de](https://p1commerce.de/aroundhome-erfahrungen/)) — ~9,5 % Abschluss, „halbes Geld floss in Leadkosten" | Käufer-Schmerz = **Streuverlust/tote Leads**, den der Kaufmoment-Vorfilter löst | 1 |
| 4 Käufer | **Anfragenfluss** ([anfragenfluss.de](https://anfragenfluss.de/)) — exkl. 1 Betrieb/Region, Wert **pro Termin**, Anti-Portal-Story | **Bestes ehrliches Vorbild** fürs Wert-Framing — kopierbar **ohne** deren Telefon-PII | 1+2+4 (Framing) |
| 4 Käufer | **BSW-Solar Q1 2026** ([solarwirtschaft.de](https://www.solarwirtschaft.de/2026/05/02/schwacher-photovoltaik-jahresauftakt/)) — PV-Neu −21 % bis −33 %, Speicher wächst | Makro-Rückenwind: Installateure brauchen Nachrüst-Pipeline dringender | 1 |

---

## 3 · Der 3-Wege-Wedge-Filter — Urteile (re-kalibriert)
> Entscheid in Reihenfolge: **① wedge-relevant?** (nein → verwerfen) **② solo von Hand machbar?** (ja → direkt bauen) **③ nicht solo machbar (Ressourcen-Vorteil)?** → automatisieren-wenn-auf-Echtdaten-beweisbar, **sonst killen** (kein Theater).
> **Status-Spalte ist gegen den echten Code geprüft** (die 3 Skeptiker-Pflicht-Korrekturen sind hier verbaut).

| Muster → GoldenTime-Anforderung | Säule | Entscheid | **Status (verifiziert)** |
|---|---|---|---|
| Per-record **Quelllink je Lead** sichtbar machen (MaStR-Direktlink) | 4 | **direkt** | **Teil-gebaut** (SEE→ID-Direktlinks existieren; einmal im Demo-Paket gemessen, *nicht* laufend verifiziert) |
| **Feld-Provenance**: Rohwert+Abrufzeit je Kern-Feld (Anmeldedatum/Standort/kein-Speicher) | 4 | **automatisierungs-play** | **zu bauen** — Engine-Arbeit; nur ehrlich, wenn Rohwert == unveränderter MaStR-Wert (stichprobenprüfen) |
| **Sichtbares Lead-Alter / „verifiziert am [Datum]"** + Frische-sortierte Lieferung | 3 | **direkt, NOCH ZU BAUEN** ⚠ | **NICHT gebaut im Lieferpfad**: `deliver.py:70` sortiert nach `(dv_flag, kwp)`, kein Frische-Feld/-Stempel. *(`reg_datum`+`frische_valide` existieren in normalize; `cmd_signals` sortiert frisch — aber der Kunden-Lieferpfad nicht.)* = Sprint S3/G2/G20 |
| **Regionale Abnehmer-Exklusivität + Dedupe** in EINEM Funnel erzwingen | 2 | **automatisierungs-play** | **NICHT verdrahtet** ⚠⚠ `record_delivery` 0 Produktions-Aufrufer; `run_region` berührt den Ledger nicht; `filter_deliverable` nur in `cmd_signals` (filtert leere Tabelle). = Sprint S1/S2 — **der USP ist heute unbelegt** |
| **Kaufmoment deterministisch** aus wöchentl. MaStR-Diff (T1 frische PV o. Speicher) | 1 | **automatisierungs-play** | **Kern-IP gebaut, aber auf Echtdaten UNBEWIESEN** ⚠ — Diff-Klassifikation korrekt + getestet, aber T1/T4 **lief nie** (nur 1 Baseline-Snapshot `snap_2026-06-15`) |
| **Feed/Push-Liefer-UX** (Snapshot→Neu-Anmeldung→Push an Gebietskunden) statt Self-Service | Liefer-UX | **automatisierungs-play** | **Architektur gebaut** (`weekly`-CLI/Snapshot/Diff) — Push-Versprechen hängt am bewiesenen Diff (s.o.) |
| **Konfidenz sichtbar + kalibriert**, nur beobachtete MaStR-Werte (nie generiert) | 4 | **direkt** | **Teil-gebaut** („nicht kalibriert"-Disclaimer real; kalibrierte Anzeige + A/B-QA-Siegel ausbauen) |
| **dl-de/by-2.0-Quellenvermerk + sichtbare Lizenz/Disclaimer** je Lieferung | 4 | **direkt** | **Teil-gebaut** (Attribution verdrahtet `deliver.py:26`; Lizenz-URL + „kein amtl. Datensatz"-Wortlaut = Sprint S0/G24) |
| **30-kWp-Floor / Gewerbe-Fokus** als harte Liefer-Invariante (regulatorischer Korridor) | 4+Grenze | **direkt** | **gebaut** (Filter 30–750 kWp); am Echtdatensatz prüfen, ab welcher Schwelle Firmenname öffentlich wird |
| **e.K./natürliche Person hart filtern** (qa-unabhängiges Liefer-Gate) | harte Grenze | **direkt** | **NICHT gebaut** — heute nur geflaggt→QA. = Sprint S0; Bisnode/LG-Kiel machen es zur Launch-Vorbedingung |
| **Mensch-QA-Stufe als sichtbares Qualitätssiegel** (auto_ok vs. geprüft, A/B/C) | 3+4 | **direkt** | **Infrastruktur gebaut** (`qa list/suggest/approve/reject`); als Siegel ausweisen |
| **Wert pro Konversionseinheit** framen + Anti-Portal-Erzählung + greifbares Datenpaket | 1+2+4 | **direkt** (Pitch) | Framing — kein Code; **ohne** Telefon-PII kopierbar |
| **Statisch-firmographische Qualifizierung** (Verbrauch/Dachfläche/Größe) als Kern | — | **verwerfen** | off-wedge Bloat (besetzt von LeadScraper) — NICHT bauen; nur als Pricing-Anker |
| **Telefon-Vorqualifizierung** als Differenzierer | — | **verwerfen** | besetzt + bis DSGVO-Freigabe gesperrt (PII) — NICHT bauen |

---

## 4 · Ressourcen-Vorteil — automatisieren ODER killen (v3-Kern, §4b/I10)
Die **automatisierungs-plays** sind GoldenTimes eigentlicher Solo-Edge: technische Lösungen auf Quantitäts-/Ressourcenprobleme, die ein Solo-Gründer **nicht von Hand** leisten kann (Mio. Anlagen wöchentlich vergleichen; betreiberweiter Speicher-Check; Exklusiv-Ledger über Wochenläufe).

**Harte I10-Bedingung — „funktioniert" = liefert den Wert auf Echtdaten, nicht „der Code läuft":**

| Play | Wird „adopted" nur wenn … | Sonst → |
|---|---|---|
| **Kaufmoment-Diff (T1)** | erster echter **Wochen-Diff aus 2 Snapshots** läuft UND die „kein-Speicher"-False-Positive-Rate am Echtdatensatz gemessen ist | killen / als unbewiesene Behauptung **nicht** verkaufen |
| **Exklusivität/Dedupe-Ledger** | `record_delivery`/`reserve` im Lieferpfad **verdrahtet** + 2. `--commit`-Lauf = 0 neue Einheiten + Gebiet A schließt B aus, alles auf Echtdaten | bis dahin ist Exklusivität **ein Versprechen, kein Feature** (Theater-Risiko für den Kern-Wedge) |
| **Feld-Provenance** | Diff-Engine schreibt Feld-Provenance je Lauf ohne Perf-Kollaps + Rohwert == MaStR-API-Wert stichprobenverifiziert | killen (sonst Provenance-Theater) |
| **Push-Feed-Liefer-UX** | hängt am bewiesenen Diff oben | aufschieben bis erster echter Diff |

**→ Alle vier Plays hängen direkt oder indirekt am ersten echten Wochen-Diff. Der ist die Wurzel-Bedingung des Kern-IP-Beweises.**

---

## 5 · Die zwei gefährlichen Selbsttäuschungen (Skeptiker-Befund — load-bearing)
Die Roh-Synthese feierte beides als „bereits gebaut". **Gegen den echten Code verifiziert falsch:**

**(a) Marktlücke ≠ gebauter Burggraben.** Regionale Abnehmer-Exklusivität ist der am stärksten validierte, kategorieweit unbesetzte Differenzierer — aber im eigenen Code **nicht erzwungen** (`record_delivery` 0 Produktions-Aufrufer, `run_region` ohne Ledger). *Ein Lead könnte heute an zwei Käufer gehen, ohne dass das Ledger es verhindert.* Den Markt-Raum als „Moat" zu feiern, während das Produkt die Exklusivität technisch nicht hält, ist die gefährlichste Wedge-Selbsttäuschung.

**(b) Die Frische-Säule ist Spec, nicht Implementierung.** `deliver.py:70` sortiert nach `kwp`, kein Frische-Feld/-Stempel im Lieferpfad. GoldenTime würde damit genau das Muster reproduzieren, das die Recherche an Apollo/Lusha/ZoomInfo kritisiert: **Frische predigen, nur versprechen.** *(Teilwahrheit: `reg_datum`/`frische_valide` existieren, `cmd_signals` sortiert frisch — aber der Kunden-Lieferpfad nicht.)*

**Kleinere Re-Kalibrierungen** (ehrlich notiert): „102+ Direktlinks" = einmaliger Demo-Selbstreport, kein laufender Beweis · Trustpilot-Schmerzzitat nur via Suchindex (403, confidence medium) · „wöchentlich ist überdurchschnittlich" mischt Handelsregister (North Data) mit MaStR (Äpfel/Birnen — Fazit mag zufällig stimmen) · EliteLeadz-Preis = Eigenwerbung, Quelle verschleiert (schwacher Anker) · Cognism-6(1)(f)-Vorbild überschätzt Übertragbarkeit auf einen Solo-Gründer (LG-Kiel/Bisnode wiegen schwerer — §7).

---

## 6 · Die FEHLENDE Achse (Skeptiker) — Dichte-vs-Exklusivität-Ökonomie ⚠ geschäftskritisch
Der gesamte Wedge hängt an regionaler Exklusivität (1 Kunde/Gebiet). Aber STATE.md §5 dokumentiert **brutal dünne Dichte**: Osnabrück ~3/Woche, Münsterland ~10, Stuttgart ~13. **Wenn nur 1 Kunde pro Gebiet zahlt UND das Gebiet nur 3–10 Leads/Woche liefert, ist der Umsatz pro Gebiet winzig — die Exklusivität, die als härtester Differenzierer gefeiert wird, ist zugleich der Umsatz-Deckel.** Dieser Trade-off ist nirgends recherchiert/gerechnet.

Eng verbunden: **Wiederhol-/Churn-Ökonomie.** Ein Installateur, der die frische PV ohne Speicher in seinem Exklusiv-Gebiet einmal abgegrast hat, hat den Bestand abgearbeitet — bleibt der dünne wöchentliche Fluss. **Ist das ein Retainer (wiederkehrend) oder ein One-Shot?** Das ist die wichtigste Geschäftsmodell-Frage und fehlt komplett. *(Das ist genau, warum der erste echte Wochen-Diff = FLUSS-Zahlen die Retainer-Pricing-Basis ist.)*

→ **Beide Fragen gehören aufs Berater-Essen (~27.06.)** und in die Liefermengen-Messung nach e.K.-Filter (Sprint S0 ⊕ Pass B.2).

---

## 7 · Negativ-Vorbilder & harte Grenze (validiert die §0-Grenze an deutschen Präzedenzfällen)
- **LG Kiel, 12 O 64/24 (27.09.2024, North Data):** Öffentliche Herkunft legitimiert **nicht** automatisch kommerziellen Resale von Personendaten — die **Zweckbindung des Folge-Verarbeiters** wird eigenständig geprüft; Löschung nach Art 17. **Frische/Disclaimer/Quelllink reichen NICHT** → eigene Interessenabwägung (LIA) + Lösch-/Widerspruchs-Mechanik nötig.
- **Bisnode/UODO Polen (~220k €, 2019):** Resale von Register-Daten über **Einzelgewerbetreibende (= e.K.!)** löst die **aktive Art-14-Informationspflicht** aus; Website-Disclaimer genügt nicht, Kosten sind kein Befreiungsgrund. **Präzisester Beleg für GoldenTimes konkreten Fall.**
- **§7 UWG / BVerwG (Telefonwerbung):** B2B-„mutmaßliche Einwilligung" verschärft — „allgemeiner Sachbezug reicht nicht", es braucht „konkrete tatsächliche Umstände". **Zweischneidig:** der Kaufmoment ist der *stärkste* konkrete Umstand **UND** der schärfste juristische Käufer-Einwand. **Zweite anwaltliche Frage neben DSGVO Art-6(1)(f).**
- **OffeneRegister.de (Zweck-Asymmetrie):** deren Personendaten trägt ein **Gemeinwohl**-Zweck (Korruptionsaufdeckung); GoldenTimes **kommerzieller** Zweck ist in der Abwägung schwächer → verstärkt das Argument, bis zur Freigabe bei **juristischen Personen / Anlagendaten** zu bleiben, e.K. hart zu filtern.

**Fazit harte Grenze:** Die §0-Invariante (keine echten Personendaten an zahlende Kunden bis Anwalts-Freigabe; `LIVE_DELIVERY_ENABLED` aus) ist durch **zwei deutsche/EU-Präzedenzfälle direkt bestätigt** — nicht Vorsicht, sondern belegter Launch-Blocker.

---

## 8 · Käufer-Frage-Batterie — Erweiterungen (§6.2, der Refuter MUSS bestehen)
Aus Tier-4-Funden — diese Fragen werden ein scharfer Speicher-Installateur stellen:
1. **Geschwindigkeit:** „Portale verteilen Leads im Minutentakt — reicht euer wöchentlicher Takt?" *(Antwort: kein Wettlauf, weil exklusiv = niemand sonst ruft denselben Lead an.)*
2. **Preis-Einordnung:** „Roh-Lead (25–75 €) oder exklusives Kaufmoment-Signal (120–200 €)?" — GoldenTime liefert **keine** Telefon-Vorqual. und (bis Freigabe) **keine** Echt-PII → in F1/F2/F3 mit echten Käufern validieren.
3. **Wert-Einheit:** „Zahle ich pro verifiziertem Lead (Stufe A/B, pay-per-match) oder pro Roh-Lead?" *(entwaffnet die Aroundhome-Schmerz-Skepsis „halbes Geld floss in tote Leads".)*
4. **§7 UWG:** „Reicht euch die frische PV-Anmeldung ohne Speicher als Rechtfertigung der Telefon-Erstansprache nach dem verschärften BVerwG-Maßstab?"
5. **Frische-Wahrnehmung:** „Ist wöchentliche Frische + sichtbares Lead-Alter ein echter Kauf-Vorteil — oder müsst ihr ihn uns erklären?" *(kein Anbieter bewirbt „wöchentlich" → Edukations-Aufwand?)*
6. **Personenbezug:** „Erwartet ihr Name/Telefon des Entscheiders — oder genügt das qualifizierte Firmen-/Anlagensignal mit MaStR-Beleg?" *(klärt Signal-vs-Kontakt-Wert + die DSGVO-/e.K.-Liefergrenze gegenüber dem Käufer.)*
7. *(bestehend, §6.2)* „Wie *garantiert* ihr Exklusivität?" · „Bekomme ich denselben Lead zweimal?" — **diese zwei brechen heute, weil G0 unverdrahtet ist.**

---

## 9 · Offene Markt-Fragen für den Gründer (markiert — fürs Essen ~27.06.)
1. **Dichte-vs-Exklusivität-Umsatzdeckel** (§6): 3–10 Leads/Woche × 1 Kunde/Gebiet — trägt das je Gebiet genug Umsatz? Wie lösen anfragenfluss/Leadfluss den Trade-off ihrer Regional-Modelle?
2. **Retainer oder One-Shot** (§6): nach dem Abgrasen des Bestands bleibt nur der Fluss — ist das ein wiederkehrendes Abo?
3. **WTP real:** alle Preisanker sind Drittanbieter-Listenpreise (0/10 Funnel-Antworten). Zahlt ein DE-Installateur für ein register-abgeleitetes Signal **ohne Kontakt**?
4. **§7-UWG-Kanal-Realität:** Akquirieren Installateure überhaupt per Telefon kalt (vs. Brief/Mail)? Wenn das Produkt (bis Freigabe) ein Signal **ohne** Telefonnummer ist, läuft das §7-Argument evtl. ins Leere.
5. **Stiller MaStR-Wettbewerber?** Recherche-Blindfleck: open-mastr-GitHub + Photovoltaikforum **nicht** geprüft. Die „unbesetzt"-These ruht auf einer Abwesenheit, die dort, wo sie am ehesten wäre (Entwickler-Communities), nicht gesucht wurde. **Vor Pricing-Zusagen prüfen.**
6. **DAA/Bosch intern?** Verkauft ein kapitalisierter Player MaStR-Neuanlagen-Auswertungen still an Hersteller?
7. **Aktive Art-14-Benachrichtigung** (Bisnode): wer benachrichtigt Betroffene — wir oder der Käufer? · **Lösch-/Widerspruchs-Mechanik** auch für reine Firmendaten (LG Kiel)? → PT1-Anwalts-Mappe.

---

## 10 · Übersetzung in GoldenTime-Anforderungen (priorisiert nach Hebel × Wedge-Treue)
1. **🔴 USP scharf machen — Exklusivität+Dedupe in EINEM Funnel erzwingen** (Säule 2; Sprint S1/S2). Größte Hebel-Lücke über beide Ziele. *(→ Ziel-Ableitung der 1. Bau-Schleife, `LOOP-LOG.md`.)*
2. **🟠 Erster echter Wochen-Diff** (Säule 1; Wurzel-Bedingung aller Plays) — kalender-/compute-gated → **parallel** anstoßen.
3. **🟡 Frische sichtbar im Lieferpfad** (Säule 3; Sprint S3/G2/G20) — Lead-Alter-Stempel + Frische-Sortierung + „verifiziert am [Datum]".
4. **🟡 Provenance vertiefen** (Säule 4) — Quelllink je Lead prominent + Feld-Provenance (Play) + dl-de-Wortlaut.
5. **🟢 Launch-Vorbedingungen** (Sprint S0) — e.K.-Hartfilter + Backup + Liefermengen-Messung nach Filter (löst §6-Frage 1 datenseitig).

> **Nächste Aktualisierung:** nach der 1. Bau-Schleife — prüfen, ob ein Markt-Fund (§9) die Priorisierung kippt; Käufer-Frage-Batterie um Essen-Funde erweitern.
