# 00_DOC-MAP — Doc-Ownership & Changeset-Ritual
**Stand 14.06.2026 · Zweck: jede Tatsache hat EIN Heimat-Doc. Andere verweisen, statt zu wiederholen — killt Drift an der Wurzel, ohne Tooling.**

## Prinzip
- **Single-Source-Ownership:** Eine Tatsache wird genau einmal definiert (Owner-Doc). Andere Docs verlinken/verweisen, statt zu kopieren.
- **STATE.md = Live-Master** (Geschaeftsstand, Funnel, Entscheidungs-Log, naechste Aktionen) — die einzige Datei, die jeden Arbeitsblock beruehrt wird.
- Detailfragen -> Owner-Doc lesen, nicht neu herleiten.

## Owner-Map
| Fakten-Cluster | Owner-Doc |
|---|---|
| Geschaeftsstand, Funnel, Entscheidungs-Log, naechste Aktionen | 01_Strategie/STATE.md |
| Lead-Qualitaet: Filter, Ausschluss-Hierarchie, Stufen A/B/C, Stempel, Dichte/Trigger | 01_Strategie/Lead-Qualitaets-Spezifikation |
| Datenquelle, Datenmodell-Grundsaetze, Speicher-Check-Methode, Frische-Logik | 01_Strategie/Architektur-Entscheidung-Datenquelle |
| Pipeline-Schritt ANREICHERN + QA | 03_Vertrieb/ (folgt, SCHRITT 3) |
| Pricing, Preismodell, Anti-Lowball | 03_Vertrieb/Pricing-Modell |
| Vertriebs-Mechanik, Konversions-Kette, LOI | 03_Vertrieb/Vertriebs-Mechanik |
| Geschaeftsmodell (Canvas) | 01_Strategie/Geschaeftsmodell-Canvas |
| Netzwerk-Fragen | 03_Vertrieb/Fragenkatalog-Netzwerk |
| CC-Setup / Build-Kontext | 01_Strategie/CC-Build-Briefing |
| Session-/Memory-Disziplin | 01_Strategie/Session-Memory-Management |
| Research-Auftraege + Reports | 01_Strategie/Research-Auftraege + research/<slug>/ |

## Changeset-Ritual (Chat <-> CC)
1. **Chat (Konzept)** entscheidet eine Aenderung -> gibt einen CHANGESET aus: betroffene Docs + exakte Edits + Commit-Message.
2. **CC (Build)** liest STATE.md + betroffene Docs, wendet die Edits an, committet.
3. Querschnittliche Aenderung -> immer Owner-Doc + STATE §7/§8 aktualisieren; andere Docs nur verweisen.

## Datei-Konvention (Empfehlung)
Mit git ist Versionierung durch git-Historie abgedeckt -> **datierte Dateinamen sind redundant.**
Empfehlung: kuenftig stabile Namen (STATE.md, Lead-Qualitaets-Spezifikation.md, ...), „Stand"-Datum nur im Doc-Header.
Migration der Bestands-Files als separater Cleanup (nicht im selben Changeset wie inhaltliche Aenderungen).
