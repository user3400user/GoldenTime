# GoldenTime — Zielbild / North Star (technisches Endbild)
**Stand: 18.06.2026 · Richtungs-/Referenzdatei (Pass A) · Read-only erzeugt, kein Code verändert.**

> **Was diese Datei ist:** das angehobene technische Endbild auf **Best-in-Class-/Referenz-Niveau im Segment**
> (Daten-Intelligence-/Lead-SaaS auf öffentlichen Registerdaten). Korridor **4,5–5,0** statt der früheren 4,2.
> **Was diese Datei NICHT ist:** ein Nah-Ziel. Das hier ist die **Destination (≈ M3 und darüber, unter Kundenlast)**.
> Der schlanke Nah-Teil (Sprint 0–3, siehe `GoldenTime-Sprint-Plan.md`) bleibt schlank — **Exzellenz wird NICHT in
> Sprint 0–3 vorgezogen** (das wäre Over-Engineering ohne Kunden).

## Kalibrierungs-Prinzip (warum nicht überall 5,0)
**5,0** dort, wo ein Versagen **existenziell/irreparabel** und **zentral für den Produktwert** ist — also wo der
Fehler das Vertrauen oder die Rechtsbasis dauerhaft zerstört. **4,5** dort, wo 5,0 für ein **B2B-Produkt mit
kleiner Kundenzahl** Over-Engineering wäre (Politur/Skalierungs-Paranoia ohne Gegenwert). Das hält die Leitlinie
des Assessments ein: **Qualität ≠ Größe.** Exzellenz wird je Dimension an **konkreten Merkmalen** beschrieben,
nicht an der Zahl.

---

## 1 · Korrektheit — **Ziel 5,0**
Das gesamte Wertversprechen ist „dieses Signal ist *wahr*" (dieser Betrieb hat *gerade* PV ohne Speicher
angemeldet). Korrektheit **ist** das Produkt — ein falsch verkauftes Exklusiv-Signal zerstört Vertrauen irreparabel.
**Exzellenz erkennbar an:**
- Jedes ausgelieferte Signal ist auf seine Quell-Evidenz rückführbar (Direktlink, kein toter Link).
- Property-based- + Golden-File-Tests auf dem Diff-/Klassifikations-Kern; Mutation-Testing auf dem Qualifizierer.
- Konfidenz ist **kalibriert** (gegen beobachtete Konversion), nicht nur ein ordinaler Indikator.
- Formale Invarianten auf Snapshot/Diff: kein Signal geht verloren oder wird doppelt erzeugt (Set-Diff-Vollständigkeit).
- 0 bekannte Defekte auf dem „ist-das-ein-echtes-Kaufsignal"-Pfad; Regressionen werden vom Gate gefangen, nicht vom Kunden.

## 2 · Datenqualität & -integrität — **Ziel 5,0**
Der Datenbestand (QA-Verdikte, Exklusiv-/Liefer-Ledger, Snapshots) **ist** das Asset. Eine stille Join-/Schema-
Korruption vergiftet das ganze Produkt. **Exzellenz erkennbar an:**
- Atomare, idempotente Wochenläufe (bereits vorhanden) + erzwungene Exklusivität+Dedupe end-to-end.
- **Datenkontrakte/Expectations auf jedem Ingest** — Schema-Drift wird gefangen und alarmiert, nie still absorbiert.
- Vollständige Feld-Provenance/Lineage je Signal; der „~9 % nicht gemeldete Speicher"-Caveat ist quantifiziert und ausgewiesen.
- Reconciliation, die immer aufgeht (lieferbar+pending+namenlos+rejected+geplant = roh); abweichende Summen blockieren.
- Backup/DR mit **getestetem Restore** der nicht-regenerierbaren `pipeline_state.db`.

## 3 · Observability / Tracking / Steuerbarkeit — **Ziel 5,0**
Bei einem wöchentlichen Change-Detection-Produkt ist das Diff-Volumen der **Herzschlag**; ein stiller Kollaps
liefert leere/falsche Listen an zahlende Exklusiv-Kunden — katastrophal und ohne Tracking **unsichtbar**.
**Exzellenz erkennbar an:**
- Jeder Wochenlauf voll beobachtbar: Run-History, Lineage, Trichter je Gebiet×Trigger, Frische = echter Datenstand.
- **Automatische Datenbruch-Erkennung** mit statistischer Woche-über-Woche-Baseline; Anomalie alarmiert **vor** Auslieferung.
- Vollständiges Audit „wer-hat-was-bekommen" (Exklusiv-Ledger abfragbar); Volumen/Kosten/Frische als Cockpit.
- Alerting, das den Gründer real erreicht (Push/Mail), nicht nur eine Dashboard-Farbe.

## 4 · Sicherheit — **Ziel 5,0 (Recht-/Daten-Achse) · 4,5 (Infra)**
Geteilt, weil die Bedrohungsmodelle verschieden sind.
- **Recht-/Datenschutz-Achse = 5,0 (existenziell):** dokumentierte Rechtsgrundlage, DPIA wo nötig, sauberes
  Handling von Betroffenenrechten, **lückenlose Provenance/Audit, welche personenbezogenen Daten wohin geflossen
  sind**, Lösch-/Retention-Disziplin. Für einen Daten-Broker ist das die tragende Wand — 5,0 gerechtfertigt.
- **Infra-Achse = 4,5:** Auth, Secret-Management, Dependency-/Secret-Scanning, Least-Privilege, ggf. SOC2-lite
  wenn Enterprise-Kunden es verlangen. **Nicht** 5,0: das Bedrohungsmodell (B2B-Datenprodukt, keine Consumer-PII
  in Massen) rechtfertigt keine Nation-State-Paranoia.

## 5 · Deploy-/Betriebsreife — **Ziel 4,5 (allg.) · 5,0 (Datenverlust-Achse)**
- **Allgemein = 4,5:** CI/CD, IaC, automatisches Scheduling, Monitoring, Ein-Befehl-Deploy, Staging. **Nicht** 5,0:
  Multi-Region-Active-Active/Chaos-Engineering wäre Over-Investment für ein Single-Region-Wochenbatch-Produkt.
- **Datenverlust-Achse = 5,0:** Backup/DR mit **getestetem** Restore der QA-Entscheide + des Exklusiv-Ledgers —
  dieser Zustand ist nicht regenerierbar und trägt das Exklusivitäts-Versprechen. Hier ist 5,0 Pflicht.

## 6 · UX & visuelle Professionalität — **Ziel 4,5**
B2B, wenige regionale Abnehmer; der **Inhalt** des Deliverables (Signalqualität, Provenance, Frische) zählt mehr
als pixelgenaue Consumer-SaaS-Politur. **Exzellenz erkennbar an:** ein sauberes, vertrauenswürdiges Kundenportal
(oder erstklassig formatierte Lieferung), das Provenance/Evidenz **1-Klick-verifizierbar** macht und „seriöser
Datenpartner" signalisiert; ein wirklich nützliches internes Cockpit. **Nicht** 5,0 (Consumer-Design-System,
Motion-Design) — Over-Investment für ein Low-N-B2B-Publikum.

## 7 · Performance / Flüssigkeit — **Ziel 4,5**
Workload = Wochenbatch über Millionen Zeilen + niedrig frequentiertes Dashboard/Portal. **Exzellenz erkennbar an:**
der Wochen-Diff läuft komfortabel innerhalb Cloud-Limits (Streaming-SQL-Set-Diff, beschränkter RAM), Regional-
Queries indiziert, Portal/Cockpit responsiv; **10–100× Kopf-Reserve**. **Nicht** 5,0 (Sub-Sekunde bei
Massiv-Concurrency/Realtime) — das ist nicht der Job; 5,0 wäre Performance-Theater.

## 8 · Architektur / Wartbarkeit — **Ziel 4,5**
**Exzellenz erkennbar an:** ein einziger Liefer-Funnel (keine 4-fach-Reimplementierung), die Adapter-Abstraktion
**real nur falls** ein 2. Register existiert (sonst gelöscht — YAGNI), klare Modulgrenzen, **volle Typ-Abdeckung +
Gate**, hohe Testabdeckung inkl. Integration; „ein neuer Entwickler ist in einem Tag produktiv, Änderungen sind
lokal und sicher". **Nicht** 5,0 (formale Architektur, erschöpfende Abstraktionsschichten) — Over-Engineering für
ein fokussiertes ~10k-LOC-Produkt.

---

## Zusammenfassung des Korridors
| Dimension | Ziel | Begründung der Höhe |
|---|---|---|
| Korrektheit | **5,0** | Korrektheit IST das Produkt; falsches Signal = irreparabler Vertrauensverlust. |
| Datenqualität & -integrität | **5,0** | Der Datenbestand ist das Asset; stille Korruption vergiftet alles. |
| Observability/Tracking | **5,0** | Diff-Volumen = Herzschlag; stiller Bruch liefert falsch an Exklusiv-Kunden. |
| Sicherheit (Recht/Daten) | **5,0** | Tragende Wand eines Daten-Brokers; Fehler ist existenziell. |
| Sicherheit (Infra) | **4,5** | Bedrohungsmodell rechtfertigt keine 5,0-Paranoia. |
| Betriebsreife (Datenverlust) | **5,0** | Ledger/QA nicht regenerierbar; getesteter Restore Pflicht. |
| Betriebsreife (allgemein) | **4,5** | Multi-Region/Chaos = Over-Investment für Wochenbatch. |
| UX & visuelle Politur | **4,5** | Low-N-B2B; Inhalt schlägt Consumer-Politur. |
| Performance/Flüssigkeit | **4,5** | Wochenbatch + kleine Audienz; 5,0 wäre Performance-Theater. |
| Architektur/Wartbarkeit | **4,5** | Fokussiertes ~10k-LOC-Produkt; formale Über-Abstraktion unnötig. |

**Leitsatz:** Dieses Bild ist der Kompass für M2/M3 — **nicht** die Checkliste für Sprint 0–3. Jede Dimension wird
**erst dann** Richtung 4,5–5,0 gezogen, wenn ein zahlender Kunde sie real einfordert. Bis dahin gilt der schlanke
operative Plan.
