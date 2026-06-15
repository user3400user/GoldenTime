# Analyse: Expansions-Landkarte gegen den Vollpaket-Frame
**Erstellt 16.06.2026 · Gehört in: 01_Strategie/ · Zweck: Klares Urteil, welche Informationen aus `report.md` (Expansions-Landkarte) in den JETZT-Build einfließen, welche Backlog sind, welche Ablenkung. Antwort auf „welche Skalierungs-Infos sind schlau einzubinden".**

> Grundlage: vollständige Lektüre der Expansions-Landkarte (42 Vektoren, Achsen A–F). Frame: Wir bauen das technische Vollpaket, starten aber mit begrenzten Gebieten/Nischen. Heikle Module (Anreicherung) zuschaltbar, nicht weggelassen.

---

## 1 · Der zentrale Befund: „Vollpaket" = volle Architektur, nicht alle Trigger gleichzeitig
Die Landkarte zeigt: Fast jede Expansions-Option ist **kein neuer Technik-Stack**, sondern Konfiguration auf einer gemeinsamen Plattform — „nur ein Leistungsfilter entfernt" (Direktvermarkter), „ein Diff auf einer schon vorhandenen Tabelle" (Retrofit, Betreiberwechsel, Stilllegung), „dasselbe Muster auf einem Zwillingsregister" (EV-Lade). Daraus folgt die Bauphilosophie:

**Was wir bauen = die generische Plattform-Schicht (Vollpaket). Was wir zum Start anschalten = Konfiguration im Dashboard (schmal). Der Schalter zwischen beidem = das Admin-Dashboard.**

Das ist die Auflösung von „alles bauen, schmal starten": Die Fähigkeit ist vollständig vorhanden; das Dashboard entscheidet pro Gebiet/Trigger/Modul, was scharf ist — und schaltet ab, wo Leistung/Kosten es nicht tragen.

## 2 · Welche INFORMATION aus der Landkarte in den Build gehört (die Kernfrage)
Die Landkarte mischt zwei Sorten Information. Nur eine gehört in den Build:

**JA — technische/feldbezogene Befunde (build-relevant, in CC-Briefing einbauen):**
- **Joinbare Tabellen im Export:** `storage_extended`, `wind_extended`, `biomass_extended`, `combustion_extended`, `kwk` + `*_eeg` liegen alle im selben Gesamtexport [Landkarte A]. → Das Backbone muss generisch über diese Tabellen gebaut sein, nicht solar-only.
- **Feldnamen (Community-Spec + offizielle Doku):** `Bruttoleistung`, `Inbetriebnahmedatum`, beide Stilllegungsfelder (`DatumEndgueltigeStilllegung` vs. `DatumBeginnVoruebergehendeStilllegung`), `AnlagenbetreiberMastrNummer`, `EinheitMastrNummer`, `EegMaStRNummer`. → exakte Diff-Schlüssel.
- **Diff-Mechanik-Regeln (kritisch, sparen Fehlbau):**
  - PV-Leistungserhöhung ist NICHT als Feldänderung erkennbar — nur Reduzierungen; PV-Zubau = separate neue Einheit. Bei Wind/Biomasse/Verbrennung dagegen echte Leistungshistorie → Repowering-Diff möglich.
  - Betreiberwechsel erzeugt KEINE Neuregistrierung → einziges Signal = `AnlagenbetreiberMastrNummer`-Wechsel bei gleicher `EinheitMastrNummer`. False-Positive-Risiko: Umfirmierung.
  - Speicher-Retrofit = neuer `EinheitenStromSpeicher` an ABR/Standort mit bestehender Solar-Einheit.
- **Daten-Gotchas (müssen als Konfidenz/Caveat ins Signal):** Speicher-Nachrüstungen nur ~40 % fristgerecht gemeldet → Retrofit-Signal lückenhaft. „ohne Speicher" bleibt „nicht gemeldet", nicht „existiert nicht" (gilt analog für alle Negativ-Trigger). → Konfidenz-Score ist Pflichtfeld, kein Schmuck.
- **Freshness-Regel:** Inbetriebnahmedatum, nicht Registrierungsdatum (gegen Korrektur-Scheinfrische). [bereits in decisions.md]
- **EV-Zwilling als Architektur-Beweis:** BNetzA-Ladesäulenregister ist CC-BY 4.0, REST-API, täglich, Betreiber+Adresse — sauberer MaStR-Zwilling. → Das Backbone-Interface so abstrahieren, dass ein zweites Register später ein Adapter ist, kein Umbau. (NICHT jetzt bauen — aber die Architektur darauf vorbereiten.)

**NEIN — Markt-/Zahlungsbereitschafts-Befunde (NICHT in den Build, gehören in Call + Pricing):**
- WTP pro Segment (Direktvermarkter, O&M, wMSB, CPO …) ist laut Landkarte selbst „überwiegend abgeleitet, nicht direkt belegt" → das ist genau die Frage für die Kundencall-Session, nicht für CC.
- Wettbewerbspreise (20–125 €/exkl. Lead, Implisense 1.500 €/Mt) → Pricing-Dokument, nicht Build.
- Hersteller-Co-Selling-Kanäle (Tesvolt/Fenecon/Solarwatt), BSW-Mitgliedschaft, Intersolar-Timing → Vertriebs-/Kanal-Strategie, nicht Build.

**Merksatz:** Feldnamen, Tabellen, Diff-Regeln, Gotchas → in den Build. Preise, WTP, Kanäle → in Call/Pricing/Vertrieb. Die Landkarte ist zu 30 % Build-Input und zu 70 % Markt-Input; nur die 30 % gehören CC.

## 3 · Das Trigger-Portfolio: was im Vollpaket scharf gebaut wird
Die Architektur trägt alle Trigger. Welche wir tatsächlich verdrahten (im Dashboard an/abschaltbar):

| Trigger | Mechanik | Bau-Aufwand (gegeben Engine) | Käufer belegt? | Verdikt |
|---|---|---|---|---|
| **T1 Neuregistrierung PV o. Speicher** | Diff: neue Einheit | gering (Engine) | ja (Kern) | **Vollpaket scharf** |
| **T2 Post-EEG 2006/07** | Kohorten-Query, KEIN Diff | trivial | ja (wachsend) | **Vollpaket scharf — früher Win** |
| **T4 Speicher-Retrofit** | neuer Speicher an Bestands-PV | gering (Engine) | ja (bestehender Käufertyp!) | **Vollpaket scharf** |
| **DV-Flag ≥100 kWp** | Leistungsfilter | trivial | ja (Pflicht-DV [18]) | **Vollpaket scharf — Multiplikator** |
| **T5 Betreiberwechsel** | ABR-Diff bei gleicher Einheit | gering (Engine) | spekulativ | **bauen, aber DEFAULT AUS** (Dashboard) |
| **T6 Stilllegung** | Diff auf Stilllegungsfelder | gering (Engine) | spekulativ | **bauen, aber DEFAULT AUS** |
| **PV-Erweiterung (Zweit-Einheit)** | neue Einheit an Bestands-ABR | gering (gleicher Join wie T1) | inferiert | **bauen, DEFAULT AUS** |

**Logik:** Was die Engine ohnehin fast gratis erzeugt, wird gebaut (Grenzkosten ~0 ist das ganze Geschäftsmodell). Was Käufer-seitig unbelegt ist, startet im Dashboard **ausgeschaltet** — gebaut, aber nicht scharf, bis der Call/Markt es bestätigt. Das ist exakt dein „zuschaltbar statt weggelassen", angewandt auf Trigger.

## 4 · Mehrfachverwertung pro Gebiet (Achse B) — der Umsatzhebel ins Datenmodell
Der größte Hebel der Landkarte: derselbe Lead an mehrere nicht-konkurrierende Käufer-**Funktionen** pro Gebiet, Exklusivität bleibt pro Funktion erhalten. Das ist primär eine **Datenmodell-Entscheidung**, kein Feature: Das Exklusivitäts-Ledger muss von Anfang an **pro Funktion × Gebiet × Trigger** schlüsseln (nicht nur pro Gebiet). Dann ist „ein Gebiet, zwei zahlende Funktionen (Speicher-Installateur + Direktvermarkter)" eine Konfiguration, kein Umbau. → Gehört ins Vollpaket-Datenmodell (CC-Briefing).

## 5 · Backlog (echt wertvoll, aber NICHT jetzt — post-Gate/post-Traktion)
Diese Optionen sind real, aber sie jetzt zu bauen würde den Fokus splitten, bevor ein zahlender Kunde existiert. Die Architektur soll sie *ermöglichen* (Adapter/Konfiguration), aber nicht *enthalten*:
- **EV-Lade-CPO-Vertikale** (#5, Ladesäulenregister) — der stärkste Backlog-Punkt (zweite Vertikale = Beweis der Horizontalität). Architektur darauf vorbereiten (Register-Adapter-Interface), aber als zweite Vertikale erst nach Gate bauen.
- **Auslands-Register** FR/ODRÉ (#17), CH-EIV (#23), IT-GSE (#20) — Backlog. AT ist KILL (s.u.).
- **Andere Energieträger** Wind-/Biogas-Repowering (#13, #25) — Backlog (andere Käufer, andere Tabellen — aber Backbone ist generisch, also später Konfiguration).
- **„Kaufsignal-Radar"-Abo** (Achse E) — das ist ein **Pricing-/Packaging-Format**, kein Build. Der Diff läuft ohnehin; ob wir ihn als Abo verkaufen, ist Pricing-Entscheidung. Wandert ins Pricing-Doku, nicht in den Build.
- **Integrationen:** CRM-Connector (#26), API/Feed-Premium (#22), White-Label (#27), B2B2B-Feed an Implisense/Dealfront (#18) — alle „jenseits 4 h/Woche", post-Traktion.
- **Exklusivitäts-Auktion/Marktplatz** (#16) — Backlog.

## 6 · Kill (NICHT bauen — Landkarte belegt als Sackgasse)
Diese sind dokumentiert tot; jede Stunde hier ist verschwendet:
- **Wärmepumpen/Wallbox aus MaStR** (#40) — NS-Verbraucher nicht meldepflichtig, §14a geht an Netzbetreiber, kein Lade-Objekt im Schema. Trigger-Quelle existiert schlicht nicht.
- **AT E-Control-Register** (#41) — nur HKN-Daten, kein Betreibergraph/Adresse. Trägt das Exklusiv-Lead-Versprechen nicht.
- **Gewerbeanmeldungen** (#42) — nur aggregiert öffentlich (Destatis).
- **Handelsregister-Live via bundesAPI** (#38) — 60 Abrufe/h + §§303a/b-StGB-Risiko → nicht skalierbar, rechtlich heikel.
- **Vergabe-Auftraggeber** (#30) — öffentliche Stellen als Kunden = BPV-Verbot. Nur Bieter-Seite, und die ist crowded.
- **HV/EHV-Industrieverbraucher** (#32) — Nische winzig, WTP spekulativ.

## 7 · Was das konkret für den JETZT-Build heißt (Übergabe an CC)
**Bauen (Vollpaket-Architektur):**
1. Generisches Backbone (open-mastr → Postgres, alle relevanten Tabellen joinbar).
2. Snapshot+Diff-Engine (versionierte Wochen-Snapshots + Diff-Logik) — das Kern-IP.
3. Trigger-Klassifikator T1/T2/T4/DV scharf + T5/T6/PV-Erweiterung gebaut-aber-aus.
4. Qualifizierer (Ausschluss-Hierarchie + Mensch-QA-Gate).
5. Signal-Record-Schema (inkl. Konfidenz-Score als Pflichtfeld wegen der Melde-Gotchas).
6. Exklusivitäts-Ledger **pro Funktion × Gebiet × Trigger**.
7. **Admin-Dashboard** als Steuer-Schicht: Gebiete/Trigger/Module einzeln an/aus, Volumen-/Kosten-Monitoring.
8. Anreicherungs-Modul **gebaut, aber DEFAULT AUS** (scharf erst nach Call + Lizenzklärung).

**Architektur darauf vorbereiten, aber NICHT bauen:** Register-Adapter-Interface (für EV-/Auslands-Register als spätere zweite Quelle).

**Nicht anfassen:** alle Kills aus §6.

**Aus der Landkarte in den Build übernehmen:** nur die technischen Befunde aus §2 (Tabellen, Feldnamen, Diff-Regeln, Gotchas). Die Markt-/WTP-/Kanal-Befunde bleiben draußen — sie sind Input für Kundencall + Pricing.
