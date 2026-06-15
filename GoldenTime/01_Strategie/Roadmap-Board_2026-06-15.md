# Roadmap-Board — GoldenTime (Stand 15.06.2026)
**Typ: Momentaufnahme/Arbeitsboard — KEIN Owner-Doc.** Live-Master = `STATE.md`. Kontext: `Stand-und-Abgleich_2026-06-15.md`.

> Zweck: **wo stehen wir, was fehlt noch.** Workstream × Ist × Ziel × Gap × Prio, dann sequenzierte Roadmap,
> dann die Entscheidungen, die bei dir liegen. Prio: **P0** = blockiert den nächsten Schritt · **P1** = vor Gate/Launch · **P2** = post-Gate.

---

## A · Gap-Analyse (Ist → Reframe-Ziel)

| # | Workstream | Ist (heute) | Ziel (Reframe) | Gap (was fehlt) | Prio |
|---|---|---|---|---|---|
| 1 | **Ingestion-Lauf** | Adapter-Code steht, **kein echter Download** | open-mastr-Lauf auf realen Daten | `build-db` auf ZBook (~3 GB) + `inspect` → reale Tabellen/Spalten gegen `config.py` verifizieren | **P0** |
| 2 | **Signal-Record-Schema** | Lead-Dict (trigger_typ, speicher_status, kWp, Datum) | formales Signal-Record (Entity·Trigger·**Evidenz-URL**·Region·Datum·**Konfidenz**·**Buy-Relevanz**) | Evidenz-URL (öffentl. MaStR-Einheits-Link), Konfidenz-Score, Buy-Relevanz-Zeile, Output-Shape | **P0** (definiert die v1-Liefereinheit) |
| 3 | **Post-EEG-(T2)-Shipper** | `normalize` klassifiziert T2 | T2-**Kohorten-Query als Produkt** (EEG-Jahr 2006/07 + kein Speicher gemeldet + Region → Signal-Liste) | dünner Wrapper um das Vorhandene; **kein Diff nötig** → frühester Win | **P0** |
| 4 | **Qualifizieren (§2)** | nur PersonenArt-Flag | volle Ausschluss-Hierarchie (öffentl./Konzern/Verein/PV-Firma/Immo) + **Mensch-QA-Gate** | Qualifier-Schritt bauen (Heuristik-Listen als pflegbare Datei) | **P1** |
| 5 | **Snapshot+Diff-Engine** | — (Point-in-time-Klassifikation) | **Kern-IP**: versionierte Wochen-Snapshots + Diff → Trigger-Klassifikation | Snapshot-Ablage (dated) + Diff-Logik um open-mastr (das baut je Lauf neu) | **P1** (Produkt-These; für T1/T4/T5/T6 nötig) |
| 6 | **Trigger-Portfolio T4–T6 + DV-Flag** | T1/T2/T3 | T4 Retrofit · T5 Betreiberwechsel · T6 Stilllegung · **≥100-kWp/DV-Flag** | T4–T6 = Diffs (hängen an #5); **DV-Flag = trivial** (Ableitung auf kWp) | DV-Flag **P1**, T4–T6 **P2** |
| 7 | **Generisches Backbone** | solar+storage+location+market | alle Energieträger + EEG + GelöschteUndDeaktivierte + Änderungen | `OPENMASTR_DATA` erweitern + generische Tabellen-Behandlung | **P2** (außer was T1/T2 braucht) |
| 8 | **Stack: Postgres (D2)** | SQLite (`db.py` = sqlite3) | open-mastr → Postgres | Postgres-Pfad in `db.py`/`export_adapter`; **prüfen, ob für v1 nötig** (SQLite trägt das Volumen) | **P1/P2** (Entscheidung, s. D-2) |
| 9 | **Exklusivitäts-Ledger** | — | Ledger **pro Funktion × Gebiet × Trigger** (ABR-Schlüssel) | Datenmodell + Mechanik; **Wording vor erster LOI** (Vertriebs-Mechanik §4 steht schon) | Ledger **P1**, Wording **P0-vor-LOI** |
| 10 | **Demo (27.06.-Gate)** | `make_sample.py` (Legacy-PLZ-Check) | **Signal-Record-Demo** (Region → Signal-Liste + Liefer-Mail) | make_sample auf Signal-Output heben **oder** `pipeline leads`+T2 nutzen; Post-EEG zeigt den Fluss ohne fertige Diff-Engine | **P1** |
| 11 | **Compliance / Redistribution** | Stub-Doc (`04_Compliance`) | finale Klärung dl-de/by-2.0 kommerzielle Weiterverbreitung (R5) | `/deepen mastr-pv-leads` bzw. Jurist; **kein Code** | **P0-vor-Launch** (nicht vor Bau) |
| 12 | **Enrichment + A/B/C** | — (D3-deferred) | v2-Upsell (GF/Tel + Stufen) | nichts jetzt (bewusst v2) | **v2** |

---

## B · Sequenzierte Roadmap

### Phase 0 — Aufräumen & Festzurren *(jetzt, Tage)*
- **Reframe committen** (Changeset-Ritual; Message liegt vor) + diese 2 Analyse-Docs.
- **`build-db` auf ZBook** + `inspect` → `config.py` gegen reale open-mastr-Namen verifizieren (entkoppelt alle Folgeschritte vom Namens-Risiko).
- **Exklusivität-pro-Funktion-Wording** final in Pricing §7 / Vertriebs-Mechanik §4 / Ledger-Skizze — **vor der ersten LOI** (einziger Punkt mit Verfallsdatum).

### Phase 1 — Früher Win: Post-EEG-Signal-Shipper *(Woche 1)*
- **T2-Kohorten-Query** (EEG-Jahr 2006/07 + „kein Speicher gemeldet" via ABR + Region) → **Signal-Record-Output** (#2): Evidenz-URL, Konfidenz, Buy-Relevanz. **Kein Diff-Engine nötig — sofort nach erstem Ingest lieferbar.**
- **≥100-kWp/DV-Flag** (trivial) → zweite Käufer-Funktion (Direktvermarkter) adressierbar.
- **Qualifizieren §2** (harte Filter + QA-Gate) auf den Signal-Fluss.

### Phase 2 — Das Eigen-IP: Snapshot+Diff-Engine *(Woche 1–2)*
- **Versionierte Wochen-Snapshots** (dated) + **Diff-Logik** um open-mastr.
- Damit **T1** (Neuregistrierung), **T4** (Retrofit), **T5** (Betreiberwechsel), **T6** (Stilllegung) als Diffs.
- **Generik** so weit, wie die aktiven Trigger es brauchen; **Postgres** nur, falls SQLite-Volumen/Diff es erzwingt (s. Call D-2).

### Phase 3 — Demo & Gate *(Woche 2 → ~27.06.)*
- **End-to-end Signal-Demo** (Region → qualifizierte Signal-Liste + Liefer-Mail; Post-EEG trägt die Demo).
- Vertriebs-Mechanik + **Fragenkatalog §F** (Multi-Buyer / Moat / Horizontal) fürs Essen.
- **Berater-Essen ~27.06.** = Gate (Kanal-Input + Signal-only-Akzeptanz testen).

### Parallel / Vor Launch (kein Bau-Blocker)
- **Redistributions-Lizenz** (R5 / Jurist) — **kein Launch ohne OK** (04_Compliance §2/§5).

### v2 (nach Traktion / erster LOI)
- **Enrichment** (GF/Tel, Halbautomatik + nimble) + **Stufe A/B/C** als Upsell (Lead-Spec §4 = fertiges Design).

---

## C · Was bis zum 27.06.-Gate konkret reicht (minimal viable Demo)
Du **musst** bis zum Essen NICHT die Diff-Engine fertig haben. Es reicht:
1. **Post-EEG-Signal-Liste** für 1–2 reale Gebiete (T2, ohne Diff) im Signal-Record-Format + Liefer-Mail.
2. **DV-Flag** sichtbar (zeigt die 2. Käufer-Funktion = die Mehrfachverwertungs-Story).
3. **Onepager + 1 gedruckte Kostprobe + Fragenkatalog §F.**
Die Diff-Engine + breiteres Portfolio sind die **Roadmap-Erzählung** (Defensibilität), nicht die Demo.

---

## D · Offene Entscheidungen (dein Call) — mit Empfehlung

| # | Entscheidung | Empfehlung | Dringlichkeit |
|---|---|---|---|
| **D-1** | **D3 bestätigen?** (Signal-Record v1, Enrichment/A-B-C → v2) | **Bestätigen** — aber Signal-only-Akzeptanz + WTP am Essen/erster LOI testen (s. Abgleich §5). Rückdrehen nur, falls du anrufbare Leads als v1-Kern willst (Kosten: Tempo + Haftung). | vor v1-Scope-Fix |
| **D-2** | **Postgres jetzt (D2) oder SQLite-first?** | **SQLite-first für v1/Demo**, Postgres wenn Diff-Engine/Volumen es erzwingt. SQLite trägt 6,2 Mio.+2,58 Mio. Zeilen für Wochenbatch problemlos; `engine`-Param ist swappbar. Spart jetzt Zeit. | vor Phase 2 |
| **D-3** | **Exklusivität pro Funktion vertraglich festzurren** | **Ja, vor der ersten LOI** — der einzige Punkt mit Verfallsdatum (sonst Mehrfachverwertung verbaut). Wording steht (Vertriebs-Mechanik §4). | **vor erster LOI** |
| **D-4** | **Redistributions-Lizenz wann prüfen** | `/deepen mastr-pv-leads` **vor erster bezahlter Lieferung** — nicht vor dem Bau. Bauen + Demo brauchen es nicht. | vor Launch |
| **D-5** | **Reframe + diese Docs committen?** | **Ja** — ich kann den vorgeschlagenen Changeset committen (8 Docs + 2 neue Dateien + decisions.md + diese 2 Analyse-Docs) und pushen. Oder du willst es selbst per PUSH_ANLEITUNG. | jederzeit |
| **D-6** | **Generisch jetzt oder solar-first?** | **Solar-first bis Phase 1**, generisch ab Diff-Engine (Phase 2). Post-EEG/T2 ist ohnehin solar; Generik zahlt erst mit den A-Triggern. | vor Phase 2 |

---

## E · Risiken & Blocker (kurz)
- **Validierungs-Risiko (offen seit Start):** 0/10 Funnel-Antworten; Signal-only ändert das Bewertete → am Essen testen. *(größtes Risiko, nicht-technisch)*
- **Vor-Launch-Blocker:** kommerzielle Weiterverbreitung MaStR-Daten (dl-de/by-2.0) — `04_Compliance`.
- **Namens-Risiko Code:** open-mastr-Tabellen/Spalten ggf. anders geschrieben → durch `inspect` früh prüfen (P0).
- **Format-Bruch MaStR 01.10.2025:** beim ersten echten `build-db` auf Parsing achten (Guardrail Architektur §6).
- **Moat-Risiko (R1):** Rohdaten + open-mastr gratis → Verteidigung = Diff-Engine + Snapshot-Historie + Exklusivität + Tempo. Am Essen gegenchecken (Fragenkatalog §F-16).
