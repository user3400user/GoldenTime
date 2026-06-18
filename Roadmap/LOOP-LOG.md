# GoldenTime — LOOP-LOG
**Lebendes Artefakt (§1.1/§8 des Loop-Briefings) · die Quelle, aus der jede Iteration ihr nächstes Ziel ableitet.**
**Regel (§1):** Jede Iteration beginnt mit einer schriftlichen Ziel-Ableitung — *welches* Ziel und *warum es die größte Hebel-Lücke ist*, belegt aus den lebenden Artefakten (§4a Scorecard, §4b Landkarte, letztes Log). **Kein Bau ohne diese Begründung.** Backlog (§7) ist Hypothese, keine Reihenfolge.

---

## Loop −1 · Konzept-Vorlauf (18.06.2026) — ABGESCHLOSSEN
**Getan:** Snapshot-Commit + Push (`9665385`), Branch `loop-engineering`. Alle lebenden Artefakte gelesen (STATE.md, Zielbild, Sprint-Plan, Roadmap-Fern, CLAUDE.md, Recht-/Standort-Memories). Strukturierte 4-Tier-Live-Web-Recherche (7-Agenten-Workflow, ~20 Anbieter) → **`KONZEPT-LANDKARTE.md` v1** mit 3-Wege-Wedge-Filter erzeugt.

**Schlüssel-Lehre des Vorlaufs (Skeptiker-verifiziert):** Die Roh-Synthese hatte zwei Säulen als „bereits gebaut" gefeiert, die **gegen den echten Code verifiziert NICHT existieren** — Exklusivität (unverdrahtet) und Frische (im Lieferpfad nicht gebaut). **Konsequenz für den Loop:** Markt-Funde und STATE.md-Selbstreport werden ab jetzt **gegen den realen Code geprüft**, bevor sie ein Urteil tragen (I4-Ehrlichkeit, I10-Anti-Theater).

**Eigene Code-Verifikation (Belege für die Ableitung unten):**
- `record_delivery` (`ledger/ledger.py:115`) hat **0 Produktions-Aufrufer** (nur `__init__`-Re-Export + Tests).
- `deliver.run_region` (`deliver.py:48`) berührt den **Ledger nicht** (keine `ledger`/`reserve`/`record_delivery`-Referenz); sortiert nach `(dv_flag, kwp)` (`deliver.py:70`) — **nicht** nach Frische.
- `filter_deliverable` läuft **nur** in `cmd_signals` (`cli.py:192`) → filtert gegen eine **nie befüllte** Tabelle (wirkungslos). `reserve` nur im manuellen `ledger`-CLI (`cli.py:373`).
- **1 Snapshot** (`snap_2026-06-15.sqlite`) → T1/T4-Diff lief nie.
- `LIVE_DELIVERY_ENABLED` **existiert nicht im Code** → die harte Grenze (§0) wird heute durch *Abwesenheit jeder Liefer-Verdrahtung* gehalten, nicht durch einen Guard.

**Re-Score-Note (§4a, kein Bau → kein echtes Delta):** Die Scorecard-Werte (17.06.) bleiben gültig; die Landkarte schärft das *zweite* Ziel. Schwächste In-Scope-Dimensionen bleiben Funktionsumfang (eff. 2), UX (2), Observability (2), Recht/Daten (2), Deploy (2).

---

## ZIEL-ABLEITUNG · Erste Bau-Schleife (Loop 0) — WARTET AUF GRÜNDER-FREIGABE (Checkpoint §5)

### Ziel
**Den USP scharf machen: regionale Exklusivität + Dedupe in EINEM Liefer-Funnel erzwingen — auf echten MaStR-Daten bewiesen.**
Konkret: `filter_deliverable` (Dedupe) + `is_available`/`reserve` (Exklusivität) + `record_delivery` (nach bestätigtem Versand) in `run_region` verdrahten, mit `--commit`/`--dry-run` + `BEGIN IMMEDIATE`-Transaktion; den `cmd_signals`-Lückenfunnel (`cli.py:188-192`) schließen. (= Sprint S1 + S2, mit den invarianten-erzwungenen S0-Vorbedingungen davor.)

### WARUM das die größte Hebel-Lücke ist (über §4a + §4b + Code-Evidenz)
1. **§4b-Markt-Konvergenz (dreifach):** Die Landkarte zeigt regionale Abnehmer-Exklusivität als (a) **kategorieweit unbesetzt** (kein einziger der ~20 Anbieter verkauft 1-Kunde/Gebiet — SI nur supply-side, Bombora), (b) **am höchsten bepreist** (3–5× Aufschlag, 120–200 €), (c) den **lautesten Käufer-Schmerz** (Mehrfachverkauf „Kunde wird zum Auktionator", Leads an 3–8 Betriebe). Es ist die load-bearing Wedge-Säule 2.
2. **§4a-/Code-Lücke:** Genau diese Säule ist im Code **nicht erzwungen** (verifiziert: `record_delivery` 0 Aufrufer, `run_region` ohne Ledger). Die Standortbestimmung führt G0 als **kritisch/hoch in 6/9 Dimensionen** — der einzige strukturelle Hebel, der so breit streut.
3. **Refuter-Test bricht heute:** Die zwei härtesten Käufer-Fragen (§6.2) — „Wie *garantiert* ihr Exklusivität?" / „Bekomme ich denselben Lead zweimal?" — sind aktuell **unbeantwortbar**. Ein USP, der dem ersten skeptischen Installateur nicht standhält, ist demo-tödlich.
4. **Hebel ÷ Aufwand maximal:** `ledger.py` ist **voll gebaut + getestet** → es ist **Verdrahtung, kein Neubau** (Effort M). Höchster Wert je Zeile.
5. **Nicht gated:** anders als der Kaufmoment-Beweis (Säule 1) hängt G0 **nicht** am Kalender (2. Snapshot) oder am Anwalt (es ist Bau, nicht Lieferung) — sofort baubar, sofort auf Echtdaten beweisbar (Münsterland/Osnabrück).
6. **Anti-Theater-Pflicht (I10):** Die Landkarte (§4, §5a) markiert Exklusivität als „Versprechen, kein Feature" — ein **automatisierungs-play, das erst „adopted" wird, wenn es auf Echtdaten funktioniert.** Es zu verdrahten ist genau die geforderte „echte, funktionierende Fähigkeit".

### CHALLENGE (§1.4 — Pflicht: besserer Weg ODER Begründung, warum dieser der beste ist)
Geprüfte Alternativen für die erste Bau-Schleife:
- **A · Kaufmoment-Beweis (T1/T4-Diff, Säule 1, Backlog Loop 0):** der andere Top-Hebel. **Verworfen als erste Schleife, weil** kalender-/compute-gated (Baseline erst 15.06.; braucht frischen `build-db` ~26 Min + open-mastr-Format-Bruch-Guardrail + sinnvolle Register-Bewegung). Sprint-Plan + Standortbestimmung depriorisieren T1/T4 **explizit auf M2** (T2-Bestand trägt Kunde #1). → **Als Parallel-Track empfohlen** (unten), nicht als erste Schleife.
- **B · Frische sichtbar (Säule 3, S3):** zweitstärkste Säule, verifiziert nicht gebaut. **Verworfen als erste Schleife, weil** geringerer Einsatz (Sortier-/Anzeige-Feature, Rohdatum existiert), Sprint-downstream von S1/S2, und es bricht die Käufer-Batterie **nicht** so hart wie Exklusivität.
- **C · Dichte-vs-Exklusivität-Ökonomie (Skeptiker-Lücke §6):** geschäftskritisch — aber primär **Messung + Gründer-Entscheid**, kein Bau. **Als Beifang in die Verify-Stufe gefaltet** (s.u.), nicht als eigene Schleife.

**Begründung, warum G0 der beste erste Schritt ist:** Es ist der einzige Kandidat, der gleichzeitig die größte Markt-validierte Säule, die breiteste Code-Lücke, den härtesten Refuter-Test und das beste Hebel/Aufwand-Verhältnis trifft — **und** nicht extern gated ist, **und** auf Echtdaten beweisbar ist (erfüllt die Echtdaten-Gating-Norm §2.4, obwohl der Konzept-Vorlauf selbst nicht mit einem Echtdaten-Lauf endete).

### Invarianten-Check (§3 — bei jedem Schritt)
- **I8 (load-bearing):** `record_delivery` schreibt in die **nicht-regenerierbare** `pipeline_state.db`. Darum **erzwungene Vorbedingungen in dieser Schleife**: (1) `pipeline_state.db`-Backup **vor** dem ersten `--commit` (Sprint-Zwang 6); (2) `--commit`/`--dry-run`-Guard existiert **bevor** je ein Live-`record_delivery` läuft (Zwang 3) — `LIVE_DELIVERY_ENABLED` Default **aus**, **CC schaltet ihn nie**; Demo/`--dry-run` füllt das Live-Ledger **nie** (Versand ist manuell, kein SMTP → `--commit` = bewusste Post-Versand-Bestätigung des Gründers).
- **I6:** Exklusivität/Dedupe in **einem** Funnel, kein Umgehungspfad → `cmd_signals`-Lücke schließen ist Teil des Ziels.
- **I1/I2/I3:** Tests bleiben grün (313), neue Oberflächen bringen Tests mit; Snapshot-Atomarität + Diff-Klassifikation unangetastet.
- **§0 harte Grenze:** Schleife läuft auf Demo-/Sample-Gebieten; **kein** echter Personendaten-Pfad an einen zahlenden Kunden. e.K.-Hartfilter (S0) als **empfohlener Graft** (s.u.), damit der gezeigte lieferbar-Bucket sauber ist.

### Prüfbare Exits (§6.5)
- Integrationstest: 2 aufeinanderfolgende `--commit`-Läufe an dieselbe `(kaeufer, funktion)` → **2. Lauf = 0 neue Einheiten** (Dedupe greift).
- Integrationstest: `reserve(Käufer A)` → `filter_deliverable` für Käufer B in derselben Kombination gibt **[]** (Exklusivität greift); Race-Test: zwei quasi-gleichzeitige `--commit` → **nicht** zwei Reservierungen.
- `--dry-run`-Demo-Lauf hinterlässt **0 Zeilen** in `delivery`/`exclusivity` (Live-Ledger bleibt unberührt).
- Echtdaten-Lauf Münsterland/Osnabrück grün; **Reconciliation geht auf** (I5).
- **Beifang (Skeptiker-Lücke §6):** lieferbare **Dichte je Gebiet** nach e.K.-Filter gemessen + in `LOOP-METRICS.md` notiert → datenseitige Vorbereitung der Umsatzdeckel-Frage fürs Essen.

### Empfehlungen an den Gründer (Checkpoint)
- **Parallel-Track (Freigabe nötig, kalender-gated):** zweiten MaStR-`build-db`+Snapshot anstoßen, damit der T1/T4-Fluss-Beweis (Säule 1) tickt, während G0 gebaut wird. *(Heavy-Op + Format-Bruch-Guardrail → bewusst nicht autonom gestartet.)*
- **Graft-Entscheid:** e.K.-Hartfilter (S0) in diese Schleife ziehen (ja/nein) — billig, macht den Demo-Bucket DSGVO-sauber und liefert die Dichte-Messung.

**Status: ⏸ CHECKPOINT — wartet auf Freigabe, bevor die erste Bau-Schleife startet.**
