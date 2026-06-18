# GoldenTime — Management-Report
## Was sich seit Beginn der Loop-Phase verändert hat (Vorher → Nachher)

**Stand: 18.06.2026 · Zeitraum: Loop-Engineering-Run · Branch `loop-engineering` (von `main`)**

---

## Bottom Line
Vor der Loop-Phase war das System **demo-fertig, aber mit einem Loch im Herzen**: der USP — regionale
Exklusivität, „kein Lead zweimal" — war **im Code nicht erzwungen** (reines Versprechen). Heute ist der USP
**real und auf echten Daten bewiesen**, dazu sind ein **verkaufbares Kundenportal**, ein **Qualitäts-/CI-Gate**,
ein **getesteter Restore** und ein **Schema-Drift-Schutz** dazugekommen.

**Der Engpass hat sich verschoben:** vorher fehlte *Bau*; jetzt ist der **M1-Code-Pfad komplett** und der
kritische Pfad zum ersten zahlenden Kunden ist **rein menschlich/extern** (Anwalt · Mensch-QA · MaStR-Download).

**Gesamt-Reifegrad: ≈ 2,6 / 5 → ≈ 3,6 / 5.**

---

## Die wichtigsten Veränderungen

| Bereich | Vorher (Beginn Loop-Phase) | Nachher (jetzt) |
|---|---|---|
| **USP (Exklusivität + Dedupe)** | im Code **NICHT erzwungen** — `record_delivery` 0 Aufrufer, Versprechen unbelegt | **erzwungen** auf Betriebs-Ebene (ein Betrieb = ein Käufer, gebiets-/trigger-übergreifend), echtdaten-bewiesen |
| **Kundenportal** | nicht vorhanden | **Login/Auth + Mandanten-Trennung** (Kunde sieht nur sein Gebiet), Provenance-1-Klick, security-reviewed |
| **Rechts-Schutz (e.K./DSGVO)** | e.K./natürl. Personen nur *geflaggt* | **hart gefiltert** in allen Liefer-Pfaden + `LIVE_DELIVERY`-Schalter (Default aus) |
| **Datensicherung** | Backup vorhanden, aber **Restore ungetestet** | **getesteter** Backup→Datenverlust→Restore-Zyklus |
| **Datenqualität** | Schema-/Format-Drift würde **still** falsche Leads liefern | **Drift-Gate** stoppt den Lauf laut (fängt open-mastr-Format-Bruch) |
| **Code-Qualität / CI** | kein Lint/Typ-/Test-Gate, kein Lockfile | **ruff + mypy + Coverage + Lockfile + GitHub-Actions — grün** |
| **Mengen-Integrität (I5)** | Reconciliation nur *angezeigt* | **erzwungen** (Lauf blockiert bei Mengen-Leck) |
| **Markt-/Strategie-Grundlage** | nur interne Annahmen | **markt-geerdete Konzept-Landkarte** (3 strategische Entscheidungen markiert) |
| **Tests** | 313 grün | **373 grün** (ruff + mypy clean) |
| **Status zu Kunde #1 (M1)** | mehrere **Code-Lücken** offen | **Code fertig** — nur noch Anwalt + Mensch-QA |

---

## Reifegrad je Dimension (Vorher → Nachher, Ziel)

| Dimension | Vorher | Nachher | Ziel |
|---|:--:|:--:|:--:|
| Funktionsumfang | 2,0 | **3,5** | 4,5 |
| Korrektheit | 4,0 | 4,0 *(gehärtet)* | 5,0 |
| UX & Professionalität | 2,0 | **4,0** | 4,5 |
| Performance | 3,0 | 3,0 | 4,5 |
| Observability / Tracking | 2,0 | **3,0** | 5,0 |
| Sicherheit (Recht/Daten) | 2,0 | **3,0** | 5,0 |
| Sicherheit (Infrastruktur) | 2,0 | **3,0** | 4,5 |
| Datenqualität & -integrität | 3,0 | **4,0** | 5,0 |
| Wartbarkeit / Codequalität | 3,0 | **4,0** | 4,5 |
| Deploy-/Betriebsreife | 2,0 | **3,5** | 4,5 |

*Die letzte Stufe Richtung 4,5–5,0 ist bewusst auf reale Kundenlast vertagt (kein Over-Engineering vor dem ersten Kunden).*

---

## Was sich NICHT verändert hat (und warum)
Diese Punkte konnten **nicht durch Engineering** gelöst werden — sie sind der eigentliche Engpass:

- **Anwalts-Freigabe** (DSGVO Art-6(1)(f) **+ neu erkannt: §7 UWG**) — Kalender-Langpol, Mensch.
- **Mensch-QA-Durchlauf** der ~134 Grenzfälle — vor dem Berater-Essen ~27.06.
- **T1/T4-Kaufmoment-Beweis** (wiederkehrende FLUSS-Zahlen) — der MaStR-Download-Server blockt aktuell aktiv (extern, nicht Code); nachzuholen, sobald erreichbar.

---

## Neu erkannte Strategie-Punkte für den Gründer
Aus der Markt-Recherche dieser Phase (Details in `KONZEPT-LANDKARTE.md`):

1. **Umsatzdeckel-Risiko:** 1 Kunde/Gebiet × nur 3–10 Leads/Woche — trägt das je Gebiet genug Umsatz?
2. **§7 UWG** als **zweiter** Rechts-Blocker neben DSGVO (verschärfte B2B-Kaltakquise-Rechtsprechung).
3. **Wettbewerber-Blindfleck:** niemand hat geprüft, ob jemand still dasselbe MaStR-Verfahren nutzt — vor Pricing-Zusagen klären.

---

## Empfohlene nächste Schritte (Reihenfolge)
1. **Anwalts-Mandat starten** (längste Vorlaufzeit — blockiert die Lieferung, nicht den Bau).
2. **Mensch-QA** für die Demo-Gebiete durchlaufen (`qa suggest`) vor dem Essen.
3. **`weekly` erneut laufen**, sobald der MaStR-Download wieder geht → dann liegen die FLUSS-/Retainer-Zahlen vor.
4. **Strategie-Punkte** beim Berater-Essen klären (Umsatzdeckel, Pricing, Kanal).
