# Lead-Qualitäts-Spezifikation (Punkt 1)
**Stand 13.06.2026 · Gehört in: 01_Strategie/ · Status: ENTSCHEIDUNG — Fundament für Pipeline-Bau & Kostproben-QA.**

> Dies ist die Spezifikation, gegen die Claude Code die Qualifizierungs-Pipeline baut und gegen die wir JEDE Kostprobe prüfen. Sie ist empirisch aus dem 208er-Inventar abgeleitet (Messungen unten), nicht aus dem Bauch. Bei Widerspruch in der Umsetzung gilt dieses Dokument.

---

## 0 · Die Leitfrage
Was macht einen Lead *gut*? Nicht „mehr Felder", sondern: **Kann der Käufer ihn sofort anrufen, mit echtem Kaufanlass, ohne selbst nachrecherchieren zu müssen, und ohne sich zu blamieren?** Jede Regel unten dient dieser einen Frage.

## 1 · Empirischer Befund (warum diese Spec nötig ist)
Messung am 208-Lead-Inventar (11.06.), erweiterte Klassifikation:
| Klasse | Anteil | Warum für Regional-Installateur wertlos |
|---|---|---|
| Saubere KMU | **75 %** | ← das echte Produkt |
| Öffentliche Hand | 9 % | Ausschreibungspflicht, kein Direktverkauf |
| Privatpersonen | 7 % | natürliche Person, DSGVO, kein Gewerbe-Case |
| Verein/Stiftung | 4 % | kein typischer Speicher-Investor |
| Konzern | 2 % | zentrale Beschaffung, Anruf verpufft |
| Immobilien-Ges. | 1 % | Betriebsaufspaltung — Verbraucher woanders |

**Kernerkenntnis:** Roh→lieferbar ≈ 75 %. Und selbst die erweiterte Namens-Heuristik lässt Reste durch (z.B. „Bremer Straßenbahn AG" = ÖPNV, „Suntec Energiesysteme" = PV-Firma). → **Eine reine Heuristik wird nie 100 % sauber. Die menschliche QA-Stufe ist daher kein Notbehelf, sondern bewusst designter Systembestandteil** (Detail → Punkt 3).

## 2 · Die Ausschluss-Hierarchie (harte Filter, in dieser Reihenfolge)
Ein Lead fliegt raus, sobald EINE Regel greift. Reihenfolge = Prüfreihenfolge in der Pipeline:
1. **Keine natürliche Person** (PersonenArt ≠ Organisation, oder Name matcht „Vorname Nachname" ohne Rechtsform). → DSGVO + kein Gewerbe. (R3-bestaetigt:) `AnlagenbetreiberPersonenArt` ist im Gesamtexport ein STRUKTURIERTER Diskriminator (juristisch vs. natuerlich) statt reiner Namens-Heuristik. CAVEAT: Einzelkaufleute (e.K./e.U., z.B. „Thomas Gerdes Reisen e. K.") sind juristisch natuerliche Personen, aber echtes Gewerbe -> PersonenArt mit Rechtsform-Suffix kombinieren, nicht blind ausschliessen; Mensch-QA fuer Grenzfaelle.
2. **Keine öffentliche Hand** (Zweckverband, Stadtwerke, Klinikum, Amt, Landkreis, Freistaat, Bundeswehr, ÖPNV/Verkehrsbetriebe …). → Ausschreibung.
3. **Kein Verein/Stiftung/gGmbH** (e.V., Stiftung, gemeinnützig). → kein Investitionsprofil.
4. **Kein Konzern/Filialist** (Liste großer Namen + Rechtsform SE/AG als Warnsignal, manuell bestätigen). → zentrale Beschaffung.
5. **Keine PV-/Energie-/Projektgesellschaft** (Name enthält solar, energie, PV, photovoltaik, „Erneuerbare", Projektgesellschaft). → Selbstversorger/Wettbewerber.
6. **Keine reine Immobiliengesellschaft** (Name enthält Immobilien/Grundbesitz). → Betriebsaufspaltung, Pain-Owner woanders → bei Anreicherung Standort-Firma suchen.
7. **Volleinspeisung** → kein Eigenverbrauch → (heute) kein Speicher-Case. (Bucket für Segment 2.)
8. **Speicher beim Betreiber vorhanden** → Bedarfslücke geschlossen. ABER: Speicher an *anderem* Standort = Premium-Flag, nicht Ausschluss (kennt die Rechnung). (R3:) Betreiberweiter Check jetzt sauber ueber `AnlagenbetreiberMastrNummer` (ABR, ~95-100% befuellt) statt PLZ+Namens-Fuzzy. „ohne Speicher" = belegbar nur „kein Speicher GEMELDET" (~9% unregistriert).

## 3 · Pflicht- vs. Kürfelder (Lead-Anatomie)
**PFLICHT (ohne diese kein lieferbarer Lead):**
- Betreiber (juristische Person) · Standort (PLZ + Ort) · kWp · Anmeldedatum · Einspeise-Profil · stabile Schlüssel (Betreiber-Nr. + Einheits-Nr.) · Speicher-Check-Ergebnis + Prüfdatum · Klassen-Flag (sauber/Premium/…).
- *Messung: alle aus dem Pull zu 100 % verfügbar. Diese Basis ist solide.*

**KÜR (steigert Stufe, aber Lieferung nie blockierend):**
- Straße/Hausnummer · Inbetriebnahmedatum · Entscheider-Name · Direktkontakt (Tel/Mail) · Gesprächsaufhänger · Branche.
- *Messung: GF-Name 3/5, Tel 3/5 automatisch — daher Stufensystem statt Alles-oder-nichts.*

**(R3-Korrektur:)** `Inbetriebnahmedatum` ist NICHT mehr nur Kuer — es VALIDIERT den Frische-CLAIM (T1). `reg_datum` allein belegt keine Neuinstallation (Nachregistrierung bis 2021). Fuer T1 mitfuehren + bei grosser IBN<->Reg-Luecke flaggen. Maßhalten: Welle ist ~5 J. her -> billige Versicherung, kein Großalarm.

## 4 · Die Qualitätsstufen A/B/C (operational definiert)
| Stufe | Definition | Zählt für Mindermengen-Gutschrift? |
|---|---|---|
| **A** | Betrieb sauber + **namentlicher Entscheider + Direktkontakt** (durchwahl/personenbezogene Mail), Mensch-verifiziert | ✅ |
| **B** | Betrieb sauber + Entscheider-Name ODER zentrale Kontaktmöglichkeit, plausibilisiert | ✅ |
| **C** | Betrieb sauber, nur Firmen-Identität (kein verifizierter Kontakt) | ❌ (wird geliefert, aber gutgeschrieben) |
**Regel:** Lieber Stufe C *liefern* als zurückhalten (Frische schlägt Vollständigkeit). Nur A/B zählen gegen die zugesagte Wochenmenge.

## 5 · Der Qualitäts-Stempel (Vertrauen als Verkaufsargument)
Jeder gelieferte Lead trägt sichtbar:
- **Geprüft am [Datum]** · **Speicher-Check: „kein Speicher gemeldet" (betreiberweit via ABR, Stand [Datum])** · **Inbetriebnahme [Jahr] (Frische-Validierung)** · **Provenance je Kürfeld** (z.B. „GF: Impressum, 13.06.") · **Stufe A/B/C** · **Flags** (Premium / Kette / öffentlich, falls grenzwertig geliefert).
Kein Portal zeigt das. Die Transparenz IST die Differenzierung gegen mehrfachverkaufte Black-Box-Leads.

## 6 · kWp-Strategie (empirisch nachjustiert)
Messung: Median 86 kWp, p90 264, nur 9 Anlagen > 400. Das Inventar ist **stark KMU-lastig** — das ist gut (KMU = erreichbarer Entscheider), aber:
- **Untergrenze 30 kWp** bleibt (darunter Privat-Charakter).
- **Obergrenze 750 kWp** ist aktuell ein grober Solarpark-Schutz — kostet aber große Dach-Industrieanlagen (die besten Cases). → **P1: durch Lage-Filter (Dach vs. Freifläche) ersetzen, dann Deckel anheben** (Abhängigkeit: Lage-Feld im Datenexport, → R3).
- **Größenklassen als Pricing-Hebel prüfen:** 30–100 (Masse, Eigenverbrauchs-Argument) vs. 200+ (Peak-Shaving/Netzentgelte, höherer Auftragswert) — könnte unterschiedliche Preise/Zielkäufer rechtfertigen (→ Pricing-Doku).

## 7 · Konsequenzen für den Pipeline-Bau (Übergabe an CC)
1. Qualifizierung ist **mehrstufig**: harte Ausschluss-Filter (§2) → automatische Klassifikation → **Mensch-QA-Gate** für Grenzfälle (§1).
2. Klassifikation muss **erklärbar** sein: pro Ausschluss wird der Grund geloggt (welche Regel griff) — für Nachvollziehbarkeit + Heuristik-Verbesserung.
3. Heuristik-Listen (öffentliche-Hand-Begriffe, Konzernnamen, Energie-Begriffe) als **pflegbare Datei**, nicht hartcodiert — wächst mit jedem gefundenen Durchrutscher.
4. Stufen-Logik + Stempel-Felder gehören ins Datenmodell von Anfang an (→ Punkt 2).

## 7b · Lead-Dichte & Multi-Trigger-Strategie (Analyse 14.06.)
**Ausloeser:** Wissensbasis-Report + Frage "wie generieren wir mehr Leads?". Empirische Pruefung ergab eine Praezisierung der Frage.

**Kernbefund — das Problem ist DICHTE pro Gebiet, nicht Masse bundesweit:**
Ein realer Installateur deckt ein Einzugsgebiet ab (Radius/PLZ-Cluster), kein Bundesland. Gemessen am 12-Tage-Fenster: Raum Osnabrueck (PLZ 49) = nur ~3 Leads/Woche, Muensterland (48+59) = ~10, Grossraum Stuttgart (70-73) = ~13. Bundesweite Masse (208/Woche) ist genug — aber pro Gebiet ist es DUENN. Das ist der echte Engpass fuer Kundenzufriedenheit.

**Die drei Hebel fuer Dichte, nach Wirkung/Aufwand bewertet:**
1. **Frische-Fenster aufweiten (groesster Hebel, sofort).** 12->30 Tage verdreifacht die Dichte (Osnabrueck 3->8, Muensterland 10->25, Stuttgart 13->32). Linear weiter bei 60/90 Tagen. KOSTEN: aeltere Anmeldung = schwaecherer "gerade jetzt"-Trigger. AUFLOESUNG: Lead-Alter als Feld mitfuehren + Leads nach Frische sortiert liefern (oberste = heisseste). So bekommt der Kaeufer Dichte UND behaelt die Trigger-Schaerfe sichtbar. Empfehlung: Standardfenster auf 30-45 Tage, "Frische-Score" pro Lead.
2. **Multi-Trigger: mehrere Kaufanlaesse fuer denselben Kaeufer buendeln (mittel, Q4-relevant).** Der Speicher-Nachruester interessiert sich fuer JEDEN Betrieb mit Eigenverbrauch+Speicherluecke, nicht nur frische Anmeldungen. Drei Trigger speisen denselben Feed:
   - T1 frische Gewerbe-PV ohne Speicher [Kern, laeuft]
   - T2 Post-EEG / Ue20-Volleinspeiser 2006/07 [Segment 2, haerterer Datums-Aufhaenger, ABER duennes Gewerbevolumen + Uebergangsfrist bis 2032 nimmt Druck -> Q4-Upsell, nicht Kern]
   - T3 (Pruefoption) aeltere Teileinspeiser ohne Speicher, die NICHT mehr "frisch" sind, aber weiterhin Speicherluecke haben -> reaktivierbare Bestandsleads
3. **Geografische Buendelung anbieten (klein, vertrieblich).** Wo ein einzelnes Gebiet zu duenn ist (laendlich), groesseren Radius als ein Exklusivgebiet schneiden. Loest Duenne ohne Datenaenderung.

**Konsequenz fuer Pricing/Vertrieb:** Dichte pro Gebiet bestimmt, ob Retainer (200-500/Mt) gerechtfertigt ist. Bei <5 Leads/Woche ist Retainer schwer verkaufbar -> entweder Fenster weiten (Hebel 1) oder Gebiet groesser schneiden (Hebel 3) oder Pro-Lead statt Retainer. Das ist die Bruecke zwischen Datenlage und Preismodell.

**Was NICHT stimmt an "mehr Leads = zufriedener Kunde":** Bei 30-150k EUR/Abschluss und oft 1 Abschluss/Quartal will der Kaeufer TREFFER, nicht Masse. Mehr Leads bei sinkender Trefferquote senkt die wahrgenommene Qualitaet. Dichte erhoehen JA — aber Qualitaetsfilter (Paragraph 2) bleibt hart. Dichte ohne Qualitaet ist Schrott-Volumen.

## 7c · Trigger-Klassifizierung als sichtbares Lead-Attribut (Entscheid 14.06.)
**Idee:** Jeder Lead traegt sichtbar seinen Trigger-Typ — auf der Website UND in der gelieferten Liste. Der Kaeufer sieht auf einen Blick, WARUM dieser Betrieb gerade jetzt ein Kaufanlass ist. Aus "hier sind Leads" wird "hier sind Leads + Grund pro Lead".

**Die Trigger-Typen (Pflichtfeld `trigger_typ` am Lead):**
| Code | Bezeichnung | Aufhaenger fuer den Kaeufer | Datenquelle |
|---|---|---|---|
| **T1** | Neuanmeldung PV ohne Speicher | "gerade angemeldet, Eigenverbrauch, Speicher fehlt noch" | Web-JSON (frisch) |
| **T2** | Post-EEG / Ue20-Volleinspeiser | "Foerderung endet, ab dann ~3 ct/kWh — Umstieg auf Eigenverbrauch+Speicher" | MaStR-Gesamtexport (Historie) |
| **T3** | Bestandslead Teileinspeiser o. Speicher | "aelter, aber Speicherluecke besteht weiter" | Web-JSON/Export, aelteres Fenster |

**Warum das wertvoll ist:**
1. **Uebersicht & Vertrauen:** Kaeufer versteht die Heterogenitaet statt sie als Inkonsistenz zu erleben.
2. **Differenzierte Ansprache:** Jeder Trigger hat ein eigenes Gespraechsskript (T2 mit Datums-Dringlichkeit, T1 mit Frische).
3. **Pricing-Hebel:** Trigger-Typen koennen unterschiedlich bepreist/gebuendelt werden (T1 Premium-frisch, T3 guenstiger Bestand).
4. **Frische-Score ergaenzt:** zusaetzlich zum Trigger-Typ das Lead-Alter in Tagen + Sortierung (heisseste oben, vgl. 7b).

**Konsequenz fuer Bau (CC):** `trigger_typ` ist Pflichtfeld im Datenmodell von Anfang an. Website-Darstellung + Liefer-CSV zeigen es als Spalte/Badge. Stempel (Paragraph 5) wird um Trigger-Typ erweitert.

## 8 · Offene Punkte (abhängig von Research/Build)
- Lage-Filter (Dach/Freifläche): Feld im Datenexport vorhanden? → R3.
- Betreiberweiter Speicher-Check: **BEANTWORTET (R3)** = `AnlagenbetreiberMastrNummer` (ABR), ~95-100% befuellt.
- Gewerblich-Erkennung: `AnlagenbetreiberPersonenArt` (R3) als strukturiertes Signal verfuegbar (e.K.-Caveat, s. §2).
- Branchen-Erkennung: aus Name heuristisch (heute) vs. aus Handelsregister/WZ-Code (später)?
- Größenklassen-Pricing: bestätigt sich der höhere Wert großer Anlagen im Markt? → R1 + Netzwerk.
