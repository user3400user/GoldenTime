# Compliance: Datenlizenz, Redistribution & Provenance
**Stand 15.06.2026 · Gehört in: 04_Compliance/ · Status: STUB (Expansionszulage) — sammelt die belegten Compliance-Fakten + das eine Vor-Launch-Rechts-Item. Owner laut 00_DOC-MAP.**

> Single Source für: Datenlizenz der Rohdaten, kommerzielle Weiterverbreitung, Provenance-Modell, BPV-Bezug. Vollanalyse = Research-Auftrag **R5** (separat). Hier nur, was bereits belegt/entschieden ist.

---

## 1 · Datenlizenz der Quelle (belegt, R3/expansion-map)
- Der **MaStR-Gesamtdatenexport** steht unter **„Datenlizenz Deutschland – Namensnennung – Version 2.0" (dl-de/by-2.0)** → kommerzielle Nutzung ist erlaubt, **aber mit Pflicht zur Quellennennung (Namensnennung)**. Quelle: MaStR-Datendownload-Seite (s. `research/mastr-pv-leads/`, expansion-map [72]).
- **Konsequenz fürs Produkt:** Die **Namensnennung** muss in der Lieferung sichtbar sein (Liefer-Mail-Fuß / Signal-Stempel: „Datenquelle: Marktstammdatenregister der Bundesnetzagentur, dl-de/by-2.0"). Das ist eine echte Auflage, kein Nice-to-have — in den Stempel (Lead-Spec §5 v1) aufnehmen.
- Nur **öffentlich zugängliche** Felder: vertrauliche Daten natürlicher Personen sind aus dem Export **ausgeschlossen** → stützt die BPV-Formulierung „öffentlich zugänglicher Registerdaten" (STATE §9).

## 2 · Das offene Vor-Launch-Rechts-Item (überlebt D3!)
**Auch Signal-Leads = kommerzielle WEITERVERBREITUNG MaStR-abgeleiteter Daten.** D3 (Signal-Record statt Outreach) entfernt die *Outreach*-Haftung (UWG §7 / DSGVO-Erstkontakt liegt beim Käufer) — **nicht** die *Redistributions*-Lizenzfrage. Noch NICHT abschließend geprüft:
- Erlaubt dl-de/by-2.0 die kommerzielle Weiterverbreitung der aufbereiteten Datensätze in dieser Form? (sehr wahrscheinlich ja bei korrekter Namensnennung — **bestätigen**.)
- Sonderfall **personenbezogene Daten natürlicher Personen** (z.B. Einzelkaufleute e.K. als Betreiber): trotz Org-Filter mögliche Restfälle → Behandlung definieren.
- Korrekte **Attributions-Formel** + ggf. Hinweis „kein amtlicher Datensatz / keine Gewähr".
→ **Vor Launch klären** via `/deepen mastr-pv-leads` bzw. R5: „MaStR-Nutzungsbedingungen kommerzielle Weiterverbreitung". **Blocker-Status: kein Launch ohne dieses OK.**

## 3 · Provenance-Modell (v1)
- **v1 (Signal-Record):** Provenance = **Evidenz-URL** zur öffentlichen MaStR-Seite je Signal + Speicher-Check-Konfidenz + Prüfdatum. Keine Kontaktdaten → keine Kontaktdaten-Provenance nötig.
- **v2 (Enrichment-Upsell, D3-deferred):** Feld-Provenance je Kürfeld (GF: Impressum/Datum …) + DSGVO-Grundlage (berechtigtes Interesse, Funktionsdaten) — erst wenn Enrichment gebaut wird (Lead-Spec §4 v2).

## 4 · BPV-Bezug (Verweis, Owner = STATE §9)
D3 senkt die Haftungsfläche (kein Outreach/Consent bei uns). BPV-Trigger + Gesuchstext bleiben in STATE §9. Kernlinie: nur öffentlich zugängliche Daten, keine Kunden aus dem Bundesumfeld, keine dienstlichen Ressourcen.

## 5 · Offen (→ R5 / Jurist vor Launch)
- [ ] dl-de/by-2.0 Weiterverbreitung kommerziell — finale Bestätigung + Attributions-Wortlaut.
- [ ] e.K./natürliche-Person-Restfälle im Org-Filter — Ausschluss- oder Anonymisierungsregel.
- [ ] B2B-Erstkontakt-Rahmen (UWG §7, BVerwG 6 C 3.23) — relevant für den KÄUFER; als Argument/Hinweis dokumentieren, nicht unsere Haftung.
