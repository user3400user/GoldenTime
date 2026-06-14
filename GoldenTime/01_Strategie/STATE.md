# STATE.md — Gewerbespeicher-Leads · Single Source of Truth
**Stand: 13.06.2026 · Phase: Konzeption + Prototyp-Sprint (2 Wochen) · Nächster Meilenstein: Berater-Essen ~27.06.**

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
- **Zeigbar machen:** Prototyp end-to-end (Pull → Qualifizieren → Anreichern → fertige Kostprobe) + Vertriebs-Mechanik + präparierte offene Fragen fürs Netzwerk.
- **GO-Signal (parallel):** ≥1 schriftliche Zusage (Preis × Menge) → ITIL „Deliver", Markteintritt.
- **BPV-Trigger:** MRR ≥ 3'500 CHF vor 01.08. → sofort Gesuch + vorläufige Anpassungen. Sonst Gesuch erst nach August (Auskunft Vorgesetzter, §9).

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

## 4 · Nächste Aktionen (datiert) — Der 2-Wochen-Sprint
Siehe Detailplan `Sprint-Plan_2026-06-13.md`. Kurzfassung:
- **Sa/So:** Domain registrieren · Workspace-Mail · LinkedIn-Profil · Drive-Baum anlegen · Forum-Post.
- **Mo 15.06.:** Nachfass-Drafts + Welle-2-Drafts (Claude legt an) → senden.
- **Konzept (laeuft, Chat):** OK Punkt 1 Lead-Qualitaets-Spec · OK Punkt 2 Architektur-Entscheid (FINAL 14.06., R3 eingearbeitet -> Gesamtexport-Backbone) · OFFEN Punkt 3 Anreicherung/QA · Punkt 4 Exklusivitaets-Ledger.
- **Woche 1:** Prototyp-Bau (Claude Code): Pull-v2 + Qualifizieren + Anreicherung-Halbautomatik.
- **Woche 2:** Kostproben-Demo end-to-end · Vertriebs-Mechanik-Doc · Fragenkatalog fürs Essen.
- **~27.06.:** Berater-Essen — Prototyp zeigen, Kanal-/Kundengewinnungs-Input einholen.

## 5 · Daten-Inventar
- **Lieferbasis:** `mastr-leads-clean-v2-2026-06-11.csv` — 208 Leads, **mit stabilen Schlüsseln** (Betreiber-Nr. `abr`, Einheits-Nr.). Teileinspeisung, gehärtete SPV-Heuristik. NRW 38 · BY 40 · BW 36 · Nds 21 · SH+HH 14.
- **Segment-2-Saat:** 43 Volleinspeiser (Post-EEG-Bucket, T2 — haerterer Datums-Aufhaenger, aber duennes Gewerbevolumen + Frist bis 2032 -> Q4-Upsell, nicht Kern).
- **DICHTE-BEFUND (14.06.):** Problem ist Lead-Dichte pro Einzugsgebiet, nicht Masse bundesweit. Raum Osnabrueck ~3/Woche, Muensterland ~10, Stuttgart ~13 (12-Tage-Fenster). Groesster Hebel: Frische-Fenster 12->30 Tage verdreifacht Dichte. Details: Lead-Qualitaets-Spezifikation Paragraph 7b.
- **Deprecated:** clean-2026-06-11 (ohne IDs), fresh-2026-06-11 (mit Beifang). Nicht verwenden.

## 6 · Produkt-Spec (kondensiert)
**Lead-Anatomie:** Betrieb · Standort · kWp · Anmelde-/Inbetriebnahmedatum · Einspeise-Profil · Entscheider (Stufe A/B/C) · Gesprächsaufhänger · Qualitäts-Stempel + Datum · Feld-Provenance.
**Filter:** 30–750 kWp · Teileinspeisung · kein Speicher beim Betreiber · operativ · kein Filialist/Konzern (Ketten-Flag) · keine PV-/Energie-/Projektgesellschaften · öffentliche Hand markiert.
**Frische-Fenster (revidiert 14.06.):** Standard 30-45 Tage statt 12 (Dichte-Hebel), ABER Lead-Alter/Frische-Score pro Lead mitfuehren + nach Frische sortiert liefern (oberste = heisseste). Dichte UND Trigger-Schaerfe gleichzeitig. Frische-CLAIM zusaetzlich ueber `Inbetriebnahmedatum` validieren (reg_datum allein kein Neubau-Beweis wegen Nachregistrierung bis 2021, R3).
**Multi-Trigger fuer denselben Kaeufer:** T1 frische PV ohne Speicher [Kern] · T2 Post-EEG-Volleinspeiser [Q4-Upsell] · T3 aeltere Teileinspeiser ohne Speicher [Pruefoption Bestandsleads].
**Qualitätsstufen:** A = Name + Direktkontakt · B = Name + Zentrale · C = nur Firma. Nur A/B zählen für Mindermengen-Gutschrift.
**Lieferung:** wöchentlich, fixer Tag, Frische ≤7 Tage, Anreicherung ≤48h, Stufe C liefern statt zurückhalten. Exklusivität pro Gebiet, vertraglich; Ledger über stabile Schlüssel.
**Kostproben-Paket:** `make_sample.py` einsatzbereit — Regionalfilter + Speicher-Gegencheck (PLZ-Ebene als Demo-Fallback; v1 = betreiberweiter ABR-Check aus Gesamtexport) + Flags + Aufhänger + Liefer-Mail-Vorlage.

## 7 · Befunde-Log
**Punkt 1 — PULL:** Speicher-Check P0 (Betreiber-weit); Bug behoben (Volleinspeiser/SPV → 208 clean); Trigger-Semantik (In-Planung eigenes Segment, Inbetriebnahme-Feld, Korrektur-Stabilität prüfen); 750er-Deckel → Lage-Filter P1; v1 = MaStR-Gesamtexport (Post-EEG trivial).
**Punkt 3 — ANREICHERN (live 5 Leads):** Pain-Owner ≠ Betreiber (standort-zentriert); Domain 5/5·Impressum 5/5·GF 3/5·Tel 3/5, Extraktion rauscht → Halbautomatik+QA P0, nimble P2; Lidl-Fund → Ketten-Flag P0; Stufen A/B/C; DSGVO-Provenance als Verkaufsargument; Frische schlägt Vollständigkeit (48h-SLA).
**Punkt 2 — QUALIFIZIEREN:** OEFFENTLICH-Flag. Datenanalyse 208er-Inventar (13.06.): roh->lieferbar nur ~75% (9% oeffentl., 7% Privatpers., 4% Verein/Stiftung, 2% Konzern, 1% Immo). Heuristik laesst Reste durch (OEPNV-AGs, Energie-Firmen) -> Mensch-QA ist Pflicht-Systemteil, kein Notbehelf. kWp stark KMU-lastig (Median 86, p90 264) -> 750er-Deckel kostet beste Industrie-Daecher -> Lage-Filter P1.
**Architektur-Entscheid FINAL (14.06., R3 eingearbeitet):** Gesamtdatenexport = Backbone (open-mastr -> SQLite, betreiberweiter Speicher-Check via `AnlagenbetreiberMastrNummer`/ABR); Web-JSON nur noch optionales Echtzeit-Spot-Tool; Adapter-Architektur bleibt. Alle 5 R3-Fakten zugunsten Export: Frische taeglich ~05:00 (<=7-Tage gedeckt), IBN-/EEG-Datum vollstaendig (T2 erschliessbar), ABR ~95-100% befuellt = echter Anywhere-Check, open-mastr aktiv gepflegt, reg_datum stabil aber nur mit `Inbetriebnahmedatum` frische-valide. Plus `AnlagenbetreiberPersonenArt` als strukturierter Gewerblich-Filter (e.K.-Caveat). Details: Architektur-Entscheidung-Datenquelle_2026-06-14.md · R3-Report: research/mastr-pv-leads/report.md.
**Offen:** Punkt 3 ANREICHERN/QA-Mechanismus · Punkt 4 Exklusivitaets-Ledger · 5 LIEFERN · 6 FAKTURIEREN.

## 8 · Entscheidungs-Log
- 11.06.: Discovery-Mails (Experten-Frame, 3 Fragen, Sample als Dank); Pitch-Mappe (Produkt+Pain, Demand „in Validierung"). Anti-Lowball: Ist-Preis-Anker + Exklusivität als Gebot.
- 11.06.: Build-Ladder demand-gated. Anonymisierungs-Standard außen: Branche+PLZ+kWp+Datum.
- 11.06.: Volleinspeiser → Segment-2-Bucket. Clean-v2 mit stabilen Schlüsseln.
- 13.06.: **Mindset revidiert** (§0) — Parallel-Frame statt Validierung-zuerst, nach Berater-Input.
- 13.06.: **BPV** — kein Gesuch nötig bis Einkommen/August (Auskunft Vorgesetzter); Trigger 3.5k MRR. Bestätigung per Mail einholen.
- 14.06.: **Trigger-Klassifizierung** — jeder Lead traegt sichtbares Feld `trigger_typ` (T1 Neuanmeldung / T2 Post-EEG / T3 Bestand) auf Website + in Liefer-Liste. Uebersicht + differenzierte Ansprache + Pricing-Hebel. Pflichtfeld im Datenmodell. Details: Lead-Spec Paragraph 7c.
- 14.06.: **Dichte-Strategie** — Engpass ist Leads/Gebiet, nicht Masse. Hebel: Frische-Fenster auf 30-45 Tage (3x Dichte) + Frische-Score + Multi-Trigger-Buendelung (T1/T2/T3) + ggf. groessere Exklusivgebiete. "Mehr Leads = zufriedener Kunde" gilt NUR mit hartem Qualitaetsfilter — Dichte ohne Qualitaet = Schrott.
- 14.06.: **Architektur FINAL (R3 eingearbeitet)** — Gesamtdatenexport als Backbone (open-mastr -> SQLite, ABR-weiter Speicher-Check); Web-JSON nur noch Spot-Tool; Adapter bleibt. + drei Produkt-Korrekturen: Speicher-Label exakt „kein Speicher GEMELDET" via ABR (PLZ-Fuzzy ersetzt), `Inbetriebnahmedatum` als Frische-Validierung, `PersonenArt` als Gewerblich-Filter. R3 nicht mehr blockierend. Details: Architektur-Entscheidung-Datenquelle_2026-06-14.md.
- 13.06.: **Brand** — Domain-Entscheid offen (Empfehlung kaufmoment.de; alle 7 Kandidaten frei 13.06.); LinkedIn über neue Workspace-Arbeitsmail; CI/Website/Rechtsform bewusst NACH Gate.

## 9 · BPV-Status
Auskunft Vorgesetzter (12.06., mündlich → **per Mail bestätigen lassen**): Solange kein relevantes monatliches Einkommen, kein Gesuch nötig; ohnehin erst nach August einreichen. **Trigger für sofortiges Gesuch: MRR ≥ 3'500 CHF vor 01.08.** Versandfertiger Text:
> Gesuch um Bewilligung einer Nebenbeschäftigung (Art. 91 BPV): nebenberufliche selbständige KI-/Software-Automatisierungs- sowie Datenanalyse-/Informationsdienstleistungen (Aufbereitung öffentlich zugänglicher Registerdaten) für privatwirtschaftliche Unternehmen außerhalb der Bundesverwaltung, ca. 4 Std./Woche. Keine Kunden aus dem Bundesumfeld, keine dienstlichen Ressourcen/Daten/Tools, keine Überschneidung mit der BIT-Tätigkeit.

## 10 · Netzwerk (Berater-Kontakt)
- Berater: überzeugt, „schnell an den Markt", Kontakte zugesagt (Energieberater AT, Technik-/Startup-Profi DE), Folge-Essen ~27.06. mit erweitertem Netzwerk.
- Offene Fragen fürs Essen → siehe `Fragenkatalog-Netzwerk_2026-06-13.md` (Kanal/Kundengewinnung, Pricing-Realität, Technik-Sparring).

## 11 · Arbeits-Setup
- Claude-Projekt = Heimat; Drive = Archiv (Struktur in 00_README). Pro Arbeitsblock frischer Chat.
- Clients: Desktop = Bau/Doku/Auswertung · Mobile = Antwort-Triage. Gmail-Connector läuft · Drive-Connector liest+lädt (keine Ordner) · Kalender empfohlen · Claude Code + nimble = jetzt relevant (Prototyp-Bau Woche 1).
- Memory: STATE.md ist das Gedächtnis; Dauerfakten zusätzlich per „merke dir …".
- Doc-Aenderungen via CC-Changeset (Chat entscheidet -> CC wendet an + committet)
- **Konzept-Docs (Drive 01_Strategie/, Stand 13.06.):** 00_DOC-MAP · Lead-Qualitaets-Spezifikation · Architektur-Entscheidung-Datenquelle · CC-Build-Briefing · Session-Memory-Management · Pricing-Modell · Research-Auftraege · Geschaeftsmodell-Canvas · Vertriebs-Mechanik (03_Vertrieb) · Fragenkatalog-Netzwerk. Bei Detailfragen dort nachlesen, nicht neu herleiten. research/mastr-pv-leads/ enthaelt den R3-Report (report.md, notes.md, sources.md) + knowledge/mastr-buy-signals.md.
- **R3 (MaStR-Export-Mechanik) eingearbeitet 14.06. — Architektur entschieden (Gesamtexport-Backbone). Report: research/mastr-pv-leads/report.md.**
