# STATE.md — Gewerbespeicher-Leads · Single Source of Truth
**Stand: 16.06.2026 · Phase: Vollpaket GEBAUT + Zweit-Review-gehärtet, Demo-fertig (Claude Code, `main`) · Nächster Meilenstein: Berater-Essen ~27.06.**

> Session-Ritual: Jeder Arbeitsblock beginnt mit „Lies STATE.md" und endet mit „Update STATE.md".
> Diese Datei ersetzt alle früheren Planungs-Docs. Bei Widerspruch gilt STATE.md.

---

## 0 · MINDSET (revidiert 13.06. nach Berater-Gespräch)
Frühere These: „erst Demand verifizieren, dann bauen". Korrektur des Beraters (zu Recht): Das Warten kann zur Endlosschleife werden. **Neuer Frame: Verkauf und Bau laufen parallel.** Das Gate verschiebt sich vom Beweis *vor* dem Bau zum Beweis *durch das Zeigen* eines funktionierenden Prototyps.
ABER (Synthese, nicht Kompromiss): Begeisterung eines Beraters ≠ zahlender Kunde. Deshalb wird bewusst **das Produkt vorgebaut, die Skalierungs-/Kanal-Architektur aber offen gehalten** — denn „wie kommen wir wiederholbar an Kunden" beantwortet das Berater-Netzwerk erst beim Essen. Kein Vollgas in eine ungeprüfte Kanal-Richtung.
Leitsatz: **In 2 Wochen ein zeigbares Halb-Business — danach fehlt nur noch ITIL-Schritt „Deliver" an den Markt.**

## 1 · Idee in einem Satz
Wir verkaufen den Kaufmoment: Gewerbebetriebe, die gerade eine PV-Anlage ohne Speicher angemeldet haben — wöchentlich, qualifiziert, exklusiv pro Region an einen einzigen Speicher-Anbieter. (Pitch: `Gewerbespeicher-Leads_Onepager.pdf`.)

## 2 · Sprint-Ziel & Gate (Essen ~27.06.)
- **FRAME REVIDIERT 16.06.: Vollpaket statt v1/v2-Gates.** Wir bauen die volle technische Plattform; begrenzte Gebiete/Nischen zum Start = Dashboard-Konfiguration, kein Architektur-Verzicht. Heikle Teile (Anreicherung) gebaut-aber-zuschaltbar (scharf erst nach Kundencall + Lizenz).
- **Demo-kritisch fürs Essen:** echter Daten-Lauf (Phase 0) + Post-EEG-Signal-Liste (Phase 1) im Signal-Record-Format. Trägt das Gate allein; Diff-Engine + Dashboard dürfen darüber hinausreichen.
- **GO-Signal (parallel):** ≥1 schriftliche Zusage (Preis × Menge), die Signal-only akzeptiert → Markteintritt.
- **BPV-Trigger:** MRR ≥ 3'500 CHF vor 01.08. → sofort Gesuch + vorläufige Anpassungen. Sonst nach August (§9).

## 3 · Funnel (10 Erstkontakte, Mail 11.06.)
| # | Firma | Region | Mail | Korrektur | Antwort | F1 Preis | F2 Spec/Menge | F3 WTP/exkl. |
|---|-------|--------|------|-----------|---------|----------|----------------|---------------|
| 1 | AceFlex (Robbers) | Nds | ✅ | ✅ | — | | | |
| 2 | UKB Energie (Linneweber) | Münsterland | ✅ | ✅ | — | | | |
| 3 | ENPLA (Joos) | BW | ✅ | ✅ | — | | | |
| 4 | Energietechnik West | Dortmund | ✅ | ✅ | — | | | |
| 5 | Sunaro (Arens) | NRW/OWL | ✅ | ✅ | — | | | |
| 6 | aurivolt (Baumann) | OWL | ✅ | ✅ | — | | | |
| 7 | Greenflash (Böker) | Nds | ✅ | ✅ | — | | | |
| 8 | solareins SGI | Bayern | ✅ | ✅ | — | | | |
| 9 | SAPOtech (Halaburda) | SH/HH | ✅ | ✅ | — | | | |
| 10 | revotec (Paschen) | Stuttgart | ✅ | ✅ | — | | | |

Stand 13.06.: 0 Antworten (normal nach 2 Tagen). Nachfass Mo 15.06. + Welle 2.
Verarbeitung: Antwort → Claude → Spalten füllen → bei PLZ Kostprobe (make_sample.py) <24h → Follow-up Tag 3 Geld-Fragen → schriftliche Zusage einholen.

## 4 · Nächste Aktionen — Vollpaket-Build (in Claude Code)
Bau-Anweisung: `CC-Build-Briefing-v2_2026-06-16.md` · Skalierungs-Logik: `Analyse-Expansionslandkarte-vs-Vollpaket_2026-06-16.md`.
- **JETZT (P0) Phase 0:** `build-db` echter Lauf auf ZBook (~3 GB) + `inspect` → reale open-mastr-Spalten gegen config.py verifizieren. Entkoppelt alles vom Namens-Risiko.
- **Phase 1 (demo-kritisch):** Post-EEG-Signal-Shipper (T2-Kohorte + DV-Flag + Qualifizierer) → Signal-Liste. Kein Diff nötig. Trägt das Essen.
- **Phase 2:** Snapshot+Diff-Engine (Kern-IP) → T1/T4 scharf, T5/T6/PV-Erweiterung gebaut-aber-aus.
- **Phase 3:** Admin-Dashboard (Gebiete/Trigger/Module schaltbar, Volumen/Kosten-Monitoring) + Exklusivitäts-Ledger (pro Funktion × Gebiet × Trigger).
- **Parallel (separate Sessions, kein Bau-Blocker):** Kundencall = Strang 2 (`KONTEXT_Kundencall-Session_2026-06-16.md`) — klärt Wert-Frage Signal-vs-Kontakt → entscheidet, ob Anreicherungs-Modul scharf wird. Redistributions-Lizenz (dl-de/by-2.0) vor Launch.
- **~27.06.:** Berater-Essen — Signal-Demo zeigen, Kanal-Input einholen.

**Konzeptphase abgeschlossen (16.06.):** Lead-Spec (inkl. 7b Dichte, 7c Trigger-Klassifizierung) · Architektur-Entscheid · Pricing · Expansions-Analyse · Build-Briefing v2 · Kundencall-Übergabe. Alles im Repo. Die 6-Schritt-Pipeline wird ab jetzt in Claude Code gebaut, nicht mehr im Chat konzipiert.

## 5 · Daten-Inventar
- **Lieferbasis:** `mastr-leads-clean-v2-2026-06-11.csv` — 208 Leads, **mit stabilen Schlüsseln** (Betreiber-Nr. `abr`, Einheits-Nr.). Teileinspeisung, gehärtete SPV-Heuristik. NRW 38 · BY 40 · BW 36 · Nds 21 · SH+HH 14.
- **Segment-2-Saat:** 43 Volleinspeiser (Post-EEG-Bucket, T2 — haerterer Datums-Aufhaenger, aber duennes Gewerbevolumen + Frist bis 2032 -> Q4-Upsell, nicht Kern).
- **DICHTE-BEFUND (14.06.):** Problem ist Lead-Dichte pro Einzugsgebiet, nicht Masse bundesweit. Raum Osnabrueck ~3/Woche, Muensterland ~10, Stuttgart ~13 (12-Tage-Fenster). Groesster Hebel: Frische-Fenster 12->30 Tage verdreifacht Dichte. Details: Lead-Qualitaets-Spezifikation Paragraph 7b.
- **Deprecated:** clean-2026-06-11 (ohne IDs), fresh-2026-06-11 (mit Beifang). Nicht verwenden.

## 6 · Produkt-Spec (kondensiert)
**Lead-Anatomie:** Betrieb · Standort · kWp · Anmelde-/Inbetriebnahmedatum · Einspeise-Profil · Entscheider (Stufe A/B/C) · Gesprächsaufhänger · Qualitäts-Stempel + Datum · Feld-Provenance.
**Filter:** 30–750 kWp · Teileinspeisung · kein Speicher beim Betreiber · operativ · kein Filialist/Konzern (Ketten-Flag) · keine PV-/Energie-/Projektgesellschaften · öffentliche Hand markiert.
**Frische-Fenster (revidiert 14.06.):** Standard 30-45 Tage statt 12 (Dichte-Hebel), ABER Lead-Alter/Frische-Score pro Lead mitfuehren + nach Frische sortiert liefern (oberste = heisseste). Dichte UND Trigger-Schaerfe gleichzeitig.
**Multi-Trigger fuer denselben Kaeufer:** T1 frische PV ohne Speicher [Kern] · T2 Post-EEG-Volleinspeiser [Q4-Upsell] · T3 aeltere Teileinspeiser ohne Speicher [Pruefoption Bestandsleads].
**Qualitätsstufen:** A = Name + Direktkontakt · B = Name + Zentrale · C = nur Firma. Nur A/B zählen für Mindermengen-Gutschrift.
**Lieferung:** wöchentlich, fixer Tag, Frische ≤7 Tage, Anreicherung ≤48h, Stufe C liefern statt zurückhalten. Exklusivität pro Gebiet, vertraglich; Ledger über stabile Schlüssel.
**Kostproben-Paket:** `make_sample.py` einsatzbereit — Regionalfilter + Speicher-Gegencheck (PLZ-Ebene, betreiberweit ab v1) + Flags + Aufhänger + Liefer-Mail-Vorlage.

## 7 · Befunde-Log
**Punkt 1 — PULL:** Speicher-Check P0 (Betreiber-weit); Bug behoben (Volleinspeiser/SPV → 208 clean); Trigger-Semantik (In-Planung eigenes Segment, Inbetriebnahme-Feld, Korrektur-Stabilität prüfen); 750er-Deckel → Lage-Filter P1; v1 = MaStR-Gesamtexport (Post-EEG trivial).
**Punkt 3 — ANREICHERN (live 5 Leads):** Pain-Owner ≠ Betreiber (standort-zentriert); Domain 5/5·Impressum 5/5·GF 3/5·Tel 3/5, Extraktion rauscht → Halbautomatik+QA P0, nimble P2; Lidl-Fund → Ketten-Flag P0; Stufen A/B/C; DSGVO-Provenance als Verkaufsargument; Frische schlägt Vollständigkeit (48h-SLA).
**Punkt 2 — QUALIFIZIEREN:** OEFFENTLICH-Flag. Datenanalyse 208er-Inventar (13.06.): roh->lieferbar nur ~75% (9% oeffentl., 7% Privatpers., 4% Verein/Stiftung, 2% Konzern, 1% Immo). Heuristik laesst Reste durch (OEPNV-AGs, Energie-Firmen) -> Mensch-QA ist Pflicht-Systemteil, kein Notbehelf. kWp stark KMU-lastig (Median 86, p90 264) -> 750er-Deckel kostet beste Industrie-Daecher -> Lage-Filter P1.
**Architektur-Weiche (13.06.):** Web-JSON (heute) vs. MaStR-Gesamtexport. Entscheid: Adapter-Architektur (Quelle von Verarbeitung entkoppeln) — Prototyp auf Web-JSON, Export ergaenzbar fuer Post-EEG + betreiberweiten Speicher-Check. Final nach R3.
**VOLLPAKET-ENTSCHEID (16.06.):** Expansions-Landkarte analysiert (`Analyse-Expansionslandkarte-vs-Vollpaket`). Kern-Einsicht: "Vollpaket" = volle generische Plattform (Backbone + Diff-Engine + Ledger + Dashboard), Trigger/Gebiete/Vertikalen = Konfiguration. Trigger-Portfolio: T1/T2/T4/DV-Flag scharf, T5/T6/PV-Erweiterung gebaut-aber-default-aus. Mehrfachverwertung pro Gebiet (Achse B) = Ledger pro Funktion×Gebiet×Trigger. Aus Landkarte nur TECHNISCHE Befunde in den Build (Tabellen/Felder/Diff-Regeln/Gotchas); Markt-/WTP-/Kanal-Befunde → Call+Pricing. Backlog: EV-CPO-Vertikale, Auslands-Register, andere Energieträger, Integrationen. Kills: WP/Wallbox aus MaStR, AT-Register, Gewerbeanmeldungen, HR-Live, Vergabe-Auftraggeber.
**Admin-Dashboard (16.06.):** als gleichwertige Komponente entschieden — interne Steuer-Schicht, Gebiete/Trigger/Module einzeln schaltbar, Volumen-/Kosten-Monitoring (Gebiete abschalten wo unrentabel). Spec in CC-Build-Briefing-v2 §6.
**VOLLPAKET GEBAUT + ZWEIT-REVIEW-gehärtet (16.06., Claude Code, auf `main`):** Alle 8 Komponenten + Steuer-Spine end-to-end auf der echten 8,6-GB-MaStR-DB, **173 Tests grün**. Phase 0: echter Ingest + Schema verifiziert (reale `*_extended`-Namen, Betreibername/PersonenArt nur via `market_actors`-Join). Phase 1 Post-EEG-Signal-Shipper LIVE: **Münsterland 312→47 lieferbar gewerblich (41 Betriebe)**, 62 QA-pending, 203 Privatpersonen (namenlos), 10 colocated; Osnabrück 55 lieferbar (48 Betriebe). **Unabhängige Zweit-Review**: Datenpipeline + Diff-Engine + Integrität korrekt, ABER Qualifizierer unvollständig (~18 % Durchrutscher) + Evidenz-URLs kaputt (SEE→HTTP 400) — beides behoben (§2-Hierarchie vollständig als QA-Flags: Namensmuster/Klinik/Energie-Synonyme/Immobilien/Konzern; Evidenz-DIREKTlink via MaStR-API SEE→ID, live HTTP 200). Entscheide: 5 Architektur (D1-D5) + 5 Review (Q1-Q4 + geplante-Speicher-Bucket) mit Gründer bestätigt.
**DEMO-FERTIG fürs Essen:** `python -m pipeline.cli gate-demo --gebiete muensterland,osnabrueck --kaeufer "<Name>"` → Liefer-Pakete (Buckets getrennt + Liefer-Mail mit klickbaren Evidenz-Links) + ehrlicher Mengen-Report (Betriebe UND Einheiten, T2 als BESTAND ausgewiesen). 102 Direktlinks verifiziert.
**WOCHEN-TAKT GESTARTET:** Baseline-Snapshot `snap_2026-06-15` fest (Uhr läuft); `python -m pipeline.cli weekly` wöchentlich (build-db→Snapshot→prune) → in ~7 Tagen erster echter Wochen-Diff = **FLUSS-Zahlen (T1/T4) = Retainer-Pricing-Basis**. Takt-Entscheid offen: manuell-wöchentlich (Laptop-Realität, empfohlen) vs. lokaler Timer.
**ZWEIT-REVIEW RUNDE 3 (16.06., `main`, Commit `2ba8bfd`, 177 Tests grün):** Personensplitter härtet (Voll-Breiten-`＆` U+FF06 = 22× häufiger als ASCII → normalisiert; `u.`-Trenner korrekt) → Personengesellschaften ohne Rechtsform rutschen nicht mehr durch. Heuristik erweitert (KöR, VR-/Kreissparkasse + religiöse Orden, Biogas/Biomasse, Holding/Beteiligung). Diff-Peak-RAM ~12→~4 GB (Tupel-Load). **Daten-Ehrlichkeit:** geplant-Bucket strukturell dünn (nur 0,65 % der 'In Planung'-Speicher tragen Lokation — real geprüft). **Post-Runde-3-Echtzahlen Münsterland: 312 T2 → 43 lieferbar / 66 QA-pending / 203 namenlos, 43/43 Evidenz-Direktlinks, Zählung konsistent.** Stichprobe der lieferbaren „Personennamen" (Schulze-Icking/Rahmann) adversarial geprüft → alle echte **GbR/GmbH (juristisch)**, kein Durchrutscher.
**OFFENER CAVEAT (Mensch-QA):** Die 43 „lieferbar" sind `auto_ok` (= kein QA-Flag), NICHT mensch-geprüft. QA-Queue kumuliert 125 pending (75 Energie-Firma, 18 öffentlich, 14 Immo, 13 nat. Person, 9 Premium-Speicher, 9 Kette, 8 Verein). **Vor dem Essen 1× `qa list/approve/reject` für das Gebiet laufen lassen — sonst Paket NICHT als „makellos" präsentieren.**
**AUTONOMER R0–R3-LOOP (16.06., `main`, 183 Tests grün, Multi-Agent-Review + Direkt-Fixes):** Adversariale Ganz-System-Review (Workflow) → Funde behoben. **DEMO-KRITISCH gefixt:** `qa list` zeigte tote SEE-Evidenz-Links (HTTP 400) — genau der QA-Pfad vor dem Essen; jetzt klickbare Direkt-/Such-Links (live verifiziert: Demo-Paket 141 Direktlinks, 0 tote). **Ehrlichkeit:** Liefer-Mail-Konfidenz mit „nicht kalibriert"-Disclaimer; Mengen-Report Σ-Betriebe DISTINCT (vorher Doppelzählung über Gebiete) + rejected-Spalte + Reconciliation. **Resolver gehärtet** (Cache-Fehler bricht Lauf nicht mehr ab). **[BUSINESS-SHIFTING, VETOBAR, Commit `3ec1db3`]** Rechtsform-Join: caritative/Vereins-Träger, deren Form nur in `market_actors.Rechtsform` steht (gGmbH/e.V./KöR), werden jetzt geflaggt → **Münsterland lieferbar 43→41, QA-pending 66→68** (die 2 sind 'Seniorenhilfe St. Franziskus' gGmbH + 'INI' e.V. — gehören in die Mensch-QA). Revert = 1 Commit. Demo-Artefakt R2 reproduziert + verifiziert. **PARKED:** Dashboard-Politur (6 Vorschläge analysiert+ready), dedizierte finale Review (R4) — beide nicht demo-kritisch, für Kapazitäts-Fenster nach Session-Limit-Reset (heute 19:00).
**R3c + R4 (16.06., `main`, 188 Tests grün):** Dashboard-Politur umgesetzt (Monitoring = Trichter je Gebiet×Trigger + Ausbeute% + Frische, effektive Trigger je Gebiet). **Finale adversariale Review (Workflow, 5 Dim. × Skeptiker)** fand 7 Rest-Defekte → behoben (Commit `eb316b7`): Rechtsform-Katalog-Drift (echter Wert 'Stiftung␣␣des öffentlichen Rechts' mit DOPPEL-Leerzeichen → matchte nie; jetzt whitespace-/＆-robust + AG/SE/KGaA tokenbasiert) — **Münsterland-Impact 0**, reine Abwehr-Härtung; **[demo-kritisch] `--offline` verwarf gecachte Evidenz-Direktlinks** → behoben (cache_only); Monitoring-Speisung aus allen Pfaden (run_region). **TOP POST-ESSEN-ITEM (deferred, business-shifting):** `record_delivery`/`reserve` werden im CLI-Pfad NIE aufgerufen → Dashboard-Exklusivität + Dedupe-/Exklusiv-Versprechen sind aktuell unbelegt; Verdrahtung braucht Demo-vs-Real-Design (Demo darf das echte Liefer-Ledger nicht füllen).
**R6 Bug+Optimierungs-Jagd (16.06., Workflow, 191 Tests grün, Commit `28a9fcd`):** 6 Bugs + 5 Opt gefunden, die wirkungsvollen behoben. **2 ernste, die 4 Review-Runden übersehen hatten:** (1) `write_snapshot` war nicht atomar → ein Teil-Abbruch hätte die Diff-Baseline zerstört (Fix: temp+os.replace, streamt jetzt); (2) QA-Gate lieferte einen ABGELEHNTEN Lead wieder aus, sobald sein Flag im Folgelauf nicht feuerte → gespeicherter Entscheid hat jetzt Vorrang (D5 robust). **Optimierung real verifiziert:** Speicher-Index 5 Scans→1, **16 s→3 s je Lauf, Counts identisch.** Beide HIGH-Bugs hätten erst beim 2. Wochenlauf zugeschlagen — jetzt vor dem Live-Takt zu.
**R7 Sprint A/B/C (17.06., Workflow + Direkt, 313 Tests grün, Commit `16ce7f2`, gepusht):** **A `qa suggest`** = Vor-dem-Essen-Helfer (gruppiert die ~125 Pending nach Flag, je Fall Empfehlung + Direkt-Link + Copy-Paste-`qa reject`-Kommando, restriktivste Empfehlung gewinnt, NIE Auto-Entscheid) → der Mensch-QA-Durchlauf wird zum schnellen Batch. **B** Test-Coverage +116 (normalize/db/cli, 191→313). **C2** `latest_by_dimension` ins Dashboard verdrahtet. **C3** PLZ-Filter ehrlich ziffern-gegated statt LIKE-Escape. **C1 (cohort-Single-Scan) bewusst vertagt** — der Entwurf hätte die ehrliche coloc-aus-Mengen-Spalte still auf 0 regressiert.
**Offen:** **record_delivery/reserve verdrahten (Exklusivität belegen)**; FAKTURIEREN; FLUSS-Zahlen nach 2. Snapshot; Mensch-QA-Durchlauf vor dem Essen (jetzt mit `qa suggest` schnell); Park: Konfidenz-Kalibrierung, cohort-Single-Scan (korrekt+nicht-regressiv). Tech-Gedächtnis: `CLAUDE.md`.

## 8 · Entscheidungs-Log
- 11.06.: Discovery-Mails (Experten-Frame, 3 Fragen, Sample als Dank); Pitch-Mappe (Produkt+Pain, Demand „in Validierung"). Anti-Lowball: Ist-Preis-Anker + Exklusivität als Gebot.
- 11.06.: Build-Ladder demand-gated. Anonymisierungs-Standard außen: Branche+PLZ+kWp+Datum.
- 11.06.: Volleinspeiser → Segment-2-Bucket. Clean-v2 mit stabilen Schlüsseln.
- 13.06.: **Mindset revidiert** (§0) — Parallel-Frame statt Validierung-zuerst, nach Berater-Input.
- 13.06.: **BPV** — kein Gesuch nötig bis Einkommen/August (Auskunft Vorgesetzter); Trigger 3.5k MRR. Bestätigung per Mail einholen.
- 14.06.: **Trigger-Klassifizierung** — jeder Lead traegt sichtbares Feld `trigger_typ` (T1 Neuanmeldung / T2 Post-EEG / T3 Bestand) auf Website + in Liefer-Liste. Uebersicht + differenzierte Ansprache + Pricing-Hebel. Pflichtfeld im Datenmodell. Details: Lead-Spec Paragraph 7c.
- 14.06.: **Dichte-Strategie** — Engpass ist Leads/Gebiet, nicht Masse. Hebel: Frische-Fenster auf 30-45 Tage (3x Dichte) + Frische-Score + Multi-Trigger-Buendelung (T1/T2/T3) + ggf. groessere Exklusivgebiete. "Mehr Leads = zufriedener Kunde" gilt NUR mit hartem Qualitaetsfilter — Dichte ohne Qualitaet = Schrott.
- 13.06.: **Brand** — Domain-Entscheid offen (Empfehlung kaufmoment.de; alle 7 Kandidaten frei 13.06.); LinkedIn über neue Workspace-Arbeitsmail; CI/Website/Rechtsform bewusst NACH Gate.

## 9 · BPV-Status
Auskunft Vorgesetzter (12.06., mündlich → **per Mail bestätigen lassen**): Solange kein relevantes monatliches Einkommen, kein Gesuch nötig; ohnehin erst nach August einreichen. **Trigger für sofortiges Gesuch: MRR ≥ 3'500 CHF vor 01.08.** Versandfertiger Text:
> Gesuch um Bewilligung einer Nebenbeschäftigung (Art. 91 BPV): nebenberufliche selbständige KI-/Software-Automatisierungs- sowie Datenanalyse-/Informationsdienstleistungen (Aufbereitung öffentlich zugänglicher Registerdaten) für privatwirtschaftliche Unternehmen außerhalb der Bundesverwaltung, ca. 4 Std./Woche. Keine Kunden aus dem Bundesumfeld, keine dienstlichen Ressourcen/Daten/Tools, keine Überschneidung mit der BIT-Tätigkeit.

## 10 · Netzwerk (Berater-Kontakt)
- Berater: überzeugt, „schnell an den Markt", Kontakte zugesagt (Energieberater AT, Technik-/Startup-Profi DE), Folge-Essen ~27.06. mit erweitertem Netzwerk.
- Offene Fragen fürs Essen → siehe `Fragenkatalog-Netzwerk_2026-06-13.md` (Kanal/Kundengewinnung, Pricing-Realität, Technik-Sparring).

## 11 · Arbeits-Setup
- Claude-Projekt = Heimat (STATE.md als Master-Kopie). **GitHub-Repo = Versionierung/Archiv: github.com/user3400user/GoldenTime** (Struktur 01_Strategie/02_Daten/03_Vertrieb/04_Compliance/05_Brand). Pro Arbeitsblock frischer Chat.
- Clients: Desktop = Bau/Doku/Auswertung · Mobile = Antwort-Triage. Gmail-Connector läuft · GitHub-Sync im Chat einbinden für Konzept-Docs · Kalender empfohlen · Claude Code + nimble = jetzt relevant (Prototyp-Bau Woche 1).
- Memory: STATE.md ist das Gedächtnis; Dauerfakten zusätzlich per „merke dir …".
- **Konzept-Docs (GitHub-Repo, Stand 16.06.):** 01_Strategie/: **CC-Build-Briefing-v2** (Bau-Anweisung, ersetzt v1) · **Analyse-Expansionslandkarte-vs-Vollpaket** · Lead-Qualitaets-Spezifikation · Architektur-Entscheidung-Datenquelle · Geschaeftsmodell-Canvas · Session-Memory-Management · Research-Auftraege · Onepager · **KONTEXT_Kundencall-Session** (für Strang 2). 02_Daten/: clean-v2-CSV · make_sample.py · pipeline/ (CC-Code). 03_Vertrieb/: Vertriebs-Mechanik · Pricing-Modell · Fragenkatalog-Netzwerk. Bei Detailfragen dort nachlesen, nicht neu herleiten.
- **R3 (MaStR-Export-Mechanik) ausgelagert an Research-Setup — blockiert finalen Architektur-Entscheid.**
