# Architektur-Entscheidung: Datenquelle & Datenmodell (Punkt 2)
**Stand 13.06.2026 · Gehört in: 01_Strategie/ · Status: ENTSCHEIDUNGS-RAHMEN — finaler Entscheid nach R3.**

> Dies ist die teuerste Weiche des Projekts. Sie bestimmt, ob Post-EEG, betreiberweiter Speicher-Check und Historie möglich sind — oder ob in 6 Wochen alles neu gebaut wird. Diese Entscheidung gehört VOR den CC-Build und wird NICHT von CC getroffen. Das Dokument arbeitet die Abwägung so weit aus, wie ohne R3-Fakten seriös möglich; die offenen Fakten sind in §5 markiert.

---

## 1 · Die Entscheidung in einem Satz
**Web-JSON-Einzelabfrage (heutiger Prototyp) ODER MaStR-Gesamtdatenexport (Vollbestand) als Fundament der Pipeline?**

## 2 · Die zwei Optionen im Profil

### Option A — Web-JSON-Abfrage (Status quo, läuft)
Der heutige Pull (make_sample.py / repull) fragt den öffentlichen Web-Endpoint paginiert ab.
- **Pro:** Läuft bereits. Kein großer Download. Immer live-aktuell. Geringe Komplexität. Reicht für wöchentlichen Frische-Pull der letzten N Tage.
- **Contra:** Kein garantierter Zugriff auf **Historie** (Inbetriebnahme-Jahre → Post-EEG nicht abfragbar). Rate-Limit-Risiko bei Volumen. Speicher-Verknüpfung nur über Einzelabfragen pro Betreiber (langsam, das ist der heutige PLZ-Workaround). Inoffizielle Schnittstelle → kann sich ändern.

### Option B — MaStR-Gesamtdatenexport (Vollbestand)
Offizieller Gesamtdatenexport der Bundesnetzagentur, lokal verarbeitet (ggf. via open-mastr o.ä.).
- **Pro:** **Vollständige Historie** → Post-EEG-Kohorten (Inbetriebnahme 2006/07) trivial = Segment 2 wird erschließbar. Betreiberweiter Speicher-Check lokal möglich (kein Rate-Limit). Offizielle, stabile Quelle. Beliebige Filter ohne API-Limits. Einmal lokal = jede Auswertung billig.
- **Contra:** Großer Download, anspruchsvolleres Setup (Parsing, Speicher, Aktualisierung). Update-Frequenz der Quelle bestimmt Frische (täglich? wöchentlich? → R3). Mehr Build-Aufwand vorab.

## 3 · Das eigentliche Entscheidungskriterium
Die Frage ist NICHT „welche ist technisch schöner", sondern: **Brauchen wir Historie und betreiberweiten Speicher-Check für das Produkt, das wir bauen wollen?**
- Für **Segment 1 heute** (frische Anmeldungen, Speicher-Check auf PLZ-Ebene): Option A **reicht**.
- Für **die Vision** (Post-EEG-Segment 2, sauberer betreiberweiter Speicher-Check, Skalierung auf viele Gebiete ohne Rate-Limit): Option B ist **notwendig**.
- **Vorläufige These (zu bestätigen):** Der Prototyp fürs Berater-Essen kann auf A laufen, ABER das Datenmodell wird so gebaut, dass der Wechsel auf B keine Neuentwicklung ist. **Wir entkoppeln Datenquelle von Verarbeitung** (Adapter-Prinzip): Pull-Schicht austauschbar, Qualifizierung/Anreicherung/Lieferung quellenunabhängig.

## 4 · Datenmodell-Grundsätze (gelten für BEIDE Optionen)
Unabhängig vom Quellen-Entscheid baut CC das Modell nach diesen Grundsätzen:
1. **Stabile Schlüssel als Primärschlüssel:** Betreiber-MaStR-Nr. + Einheits-MaStR-Nr. — die Basis für Dedup, Exklusivitäts-Ledger und „nie zweimal verkauft" (→ Punkt 4).
2. **Quelle entkoppelt:** Eine Pull-Schnittstelle, dahinter A oder B. Verarbeitung kennt nur das normalisierte Lead-Objekt.
3. **Qualifizierungs-Status + Stufe + Stempel** sind Felder am Lead von Anfang an (→ Punkt 1 §7).
4. **Provenance pro Feld** mitführen (Wert + Quelle + Datum) — für Compliance + Qualitäts-Stempel.
5. **Roh-Snapshot aufbewahren:** Was wann gezogen wurde, unverändert speichern (Audit, Reproduzierbarkeit, Korrektur-Erkennung).
6. **Lieferung als eigener Zustand:** Lead → qualifiziert → angereichert → geliefert (an wen, wann, welches Gebiet). Trennung von „existiert" und „verkauft".

## 5 · Was R3 liefern muss, damit der Entscheid fällt (die offenen Fakten)
1. **Frische des Exports:** Aktualisiert die Bundesnetzagentur den Gesamtexport täglich oder seltener? → Wenn seltener als wöchentlich, untergräbt das unser ≤7-Tage-Frische-Versprechen → spricht für A (oder Hybrid).
2. **Historie/Inbetriebnahme:** Enthält der Export das Inbetriebnahmedatum für Post-EEG-Filterung? → Wenn ja, ist B der einzige Weg zu Segment 2.
3. **Speicher-Verknüpfung:** Über welche ID ist ein separater Speicher dem Betreiber zuzuordnen? → Entscheidet, ob betreiberweiter Check überhaupt sauber geht (in A wie B).
4. **Tooling-Reife:** Ist open-mastr o.ä. aktuell genug, um B mit vertretbarem Aufwand zu betreiben?
5. **Korrektur-Stabilität:** Bleibt das Registrierungsdatum bei Datenkorrekturen stabil? → Risiko „alte Anlage erscheint als frisch".

## 6 · Wahrscheinliche Empfehlung (Hypothese, vor R3)
**Hybrid mit Adapter-Architektur:** Prototyp und wöchentlicher Frische-Pull über A (läuft, reicht für Segment 1, schützt Frische). Datenmodell + Verarbeitung quellenunabhängig. Sobald R3 die Export-Mechanik klärt, B als zweite Pull-Schicht ergänzen — primär für Historie/Post-EEG (Segment 2) und betreiberweiten Speicher-Check. **So zahlt der Prototyp nicht den vollen B-Aufwand, verbaut sich aber nichts.** Finaler Entscheid: nach R3.

## 7 · Konsequenz für die erste CC-Session
CC baut das **normalisierte Lead-Objekt + die Pull-Schnittstelle (Adapter)** zuerst — mit A als erstem Adapter. Damit ist die teure Weiche offen gehalten, ohne den Sprint zu blockieren. Die §4-Grundsätze sind die nicht-verhandelbaren Leitplanken; alles andere entscheidet CC mit dir technisch.
