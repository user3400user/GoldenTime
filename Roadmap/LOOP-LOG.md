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

**Status: ✅ FREIGEGEBEN (Gründer 18.06.: G0 + 2. Snapshot + e.K.-Filter) → durchgeführt (s.u.).**

---

## Loop 0 · Durchführung + Closeout (18.06.2026) — ABGESCHLOSSEN

### Gebaut (autonomer Modus)
- **USP erzwungen:** `ledger.commit_delivery` (atomar, `BEGIN IMMEDIATE`) verdrahtet in `run_region` (Dry-Run-Vorschau, read-only) + CLI `--commit` (gate-demo/liefern). Dedupe (einheit×kaeufer×funktion) + Gebiets-Reservierung (funktion×gebiet×trigger).
- **e.K.-Hartfilter** (§0/I7) über gemeinsamen Choke-Point `hierarchy.partition_natuerliche` in **allen** Funneln (run_region, cmd_signals, cmd_diff) + Legacy cmd_leads; config_store-Schalter `natuerliche_personen_freigegeben` (Default aus).
- **LIVE-Guard** (I8): `config.LIVE_DELIVERY_ENABLED` (Default aus, CC setzt nie); `--commit` verweigert solange aus; Backup-vor-Commit (`state.backup_state_db`, Zwang 6); dl-de-Wortlaut (G24).

### Refute (§6.5.4 · 3-Winkel-Workflow, skeptiker-verifiziert) → 9 Funde, alle adressiert
- **[CRITICAL] Versprechen↔Schloss-Lücke:** Mail versprach Betriebs-Exklusivität, Schloss arbeitete auf Einheit×Gebiet×Trigger → derselbe Betrieb (ABR) in zwei Gebieten ginge an zwei „exklusive" Käufer. **Fix:** **Betriebs-Ebene-Exklusivität** (`betrieb_fremd_vergeben`, neue `delivery.betreiber_mastr_nr`-Spalte + Index) — ein Betrieb = ein Käufer je Funktion, gebiets- UND trigger-übergreifend; + Mail ehrlich gemacht.
- **[HIGH] cross-Trigger-Leck** → durch Betriebs-Ebene mitgeschlossen (trigger-agnostisch).
- **[HIGH] cmd_diff (FLUSS) ohne e.K.-Filter** → Choke-Point eingezogen.
- **[HIGH] `--commit` vor Versand** → Reihenfolge umgekehrt (CSV/Mail zuerst), klare „kein-SMTP/Versand-ist-manuell"-Warnung.
- **[MED] cmd_leads e.K. · save() verwarf policy-extras · funktion-Normalisierung · ROLLBACK maskiert Lock-Fehler** → alle gefixt. **[LOW] non-dict-policy-Crash** → defensiv.
- **[LOW, dokumentiert, nicht gefixt]** `cmd_ledger reserve/release` schreibt Live-Exklusivität ohne LIVE-Guard (pre-existing, manuelles Vertrags-Tool, kein Datenexport) → bewusst als manuelles Tool belassen, Kandidat für Funnel-Unifizierung (G28, M2).

### Verifikation (§6.5.5 · Echtdaten + Tests)
- **337 Tests grün** (313 + 24 G0). USP auf echten 41 Münsterland-Records bewiesen: 2. Commit = 0 (Dedupe), KäuferB = 0 (Exklusivität). Cross-Gebiet-Betriebs-Sperre per Unit-Test bewiesen; auf Demo-Daten 0 blockiert (lieferbare T2-Sets disjunkt — ehrlich). `--commit` bei LIVE=aus real verweigert, Live-Ledger leer. Migration der echten DB ok. Zahlen → `LOOP-METRICS.md`.

### Re-Score (§4a, mit Beleg — Delta zu Ist 17.06.)
| Dim | Ist 17.06. | Loop 0 | Beleg |
|---|:--:|:--:|---|
| 1 Funktionsumfang | 3 (eff. 2) | **3 (eff. 3)** | USP (Exklusivität/Dedupe) **funktioniert jetzt real** (`commit_delivery` verdrahtet, echtdaten-bewiesen) statt toter Ledger |
| 2 Korrektheit | 4 | **4** (gehärtet) | adversariale Verifikation + 1 CRITICAL + 3 HIGH Versprechen-/Funnel-Lecks geschlossen; +24 Tests |
| 6 Sicherheit Recht/Daten | 2 | **3** | §0 jetzt **im Code erzwungen** (e.K.-Hartfilter alle Funnel, LIVE-Guard, dl-de-Wortlaut) statt durch Abwesenheit |
| 7 Datenqualität/Integrität | 3 | **3** (gehärtet) | Backup-vor-Commit (nicht-regenerierbarer Ledger); Reconciliation um e.K.-Term erweitert, geht auf |

(Andere Dimensionen unverändert — bewusst nicht in dieser Schleife adressiert.)

### Offen (in nächste Schleife) / Vertagt
- **T1/T4-Fluss-Beweis** vertagt — MaStR-Download-Host blockt (extern, s. `LOOP-METRICS.md`).
- **Mensch-QA-Durchlauf** der ~134 Pending vor dem Essen (auto_ok ≠ mensch-geprüft).
- **Funnel-Unifizierung (G28):** cmd_signals/cmd_leads sind Export-/Analyst-Tools, kein committender Pfad — einziger committender Funnel ist run_region. Voll vereinheitlichen = M2.

**Status Loop 0: ✅ ABGESCHLOSSEN — committet `e380410`, gepusht.**

---

## ZIEL-ABLEITUNG · Bau-Schleife Loop 1 (18.06.2026)

### Ziel
**Korrektheits- & Sichtbarkeits-Leaks vor der ersten Lieferung schließen (Sprint S3, M1-Gate): G5 + G17.**
- **G5 (Korrektheit):** ein zuvor `APPROVED` Lead, der seit dem Review einen NEUEN QA-Flag bekommen hat (echte Obermenge von `flags_at_review`), muss zurück in die QA (`PENDING`). `rejected` bleibt `rejected`. Asymmetrisch in `apply_qa`, **kein** Fingerprint-Eingriff (würde R6-Design `qa_gate.py:159` brechen).
- **G17 (Observability/Datenbruch):** Anomalie-Erkennung — ein Lauf mit **0 lieferbaren** (oder Einbruch unter Trailing-Baseline) warnt **vor** der Auslieferung; eine leere/eingebrochene Liste an einen Exklusiv-Kunden ist ohne Tracking unsichtbar (Zielbild: „Diff-Volumen = Herzschlag").

### WARUM größte (baubare) Hebel-Lücke (über §4a + §4b)
1. **§4a:** Observability ist die **niedrigste In-Scope-Dimension (2)** und im Zielbild **existenziell (5,0)** — „stiller Kollaps liefert leere Listen an zahlende Exklusiv-Kunden, katastrophal und ohne Tracking unsichtbar". G5 trifft Korrektheit (Ziel 5,0). Beide sind **die letzten Code-Items des M1-Gate** (Sprint §2: (3) G5, (4) Datenbruch sichtbar) neben Anwalt (Mensch) — USP (2), Backup (5), Mengen-Messung (7) sind in Loop 0 erledigt.
2. **§4b/Refuter:** Käufer-Batterie „bekomme ich denselben Lead/eine leere Liste?" — G17 verhindert, dass ein gebrochener Wochenlauf still eine leere Liste an den Exklusiv-Kunden schickt (zerstört genau das Vertrauen, das das Produkt verkauft). G5 verhindert, dass ein nachträglich rot-geflaggter (z.B. als Verein erkannter) Betrieb ausgeliefert wird, den der Gründer früher freigegeben hatte.
3. **Baubar JETZT** (anders als Säule 1/T1/T4 + die volle Diff-Anomalie = extern blockiert/M2): G5 + G17-light brauchen keine 2. Snapshot-Daten; reg_datum/QA-Infrastruktur existiert.

### CHALLENGE (§1.4)
- **A) Säule 1 (T1/T4-Kaufmoment):** größter Markt-Hebel, aber **extern blockiert** (MaStR-Download) → nicht baubar.
- **B) Frische sichtbar (Säule 3, S3/G2):** markt-validiert, aber für das **T2-BESTAND**-Produkt (Kunde #1) **irrelevant** (Post-EEG-Leads von 2006/07 sind kein Frische-Signal; Sprint-Plan PT1-Branch sagt das explizit). Voller Wert erst mit T1-FLUSS → mit Säule 1 vertagt.
- **C) Volle Diff-Anomalie / Trailing-Baseline:** braucht ≥2–3 Wochen Metrik-Historie (haben wir nicht) → G17-light (0/Einbruch-Warnung) jetzt, volle Baseline wenn Historie da ist (M2).
- **Begründung:** G5+G17 sind die einzigen M1-Gate-Code-Items, die baubar UND nicht extern gated sind, und treffen die zwei existenziellsten Scorecard-Dimensionen.

### Invarianten-Check / Exits
- **I1** Tests grün; **I4** Ehrlichkeit (Anomalie warnt, fälscht nichts; G5 macht die QA strenger, nicht lockerer).
- **Exits:** zuvor approved + NEU geflaggt (ohne load-bearing-Änderung) → `PENDING`; zuvor `rejected` bleibt `rejected`; Lauf mit 0 lieferbaren → `WARNING`; Einbruch < 50 % Trailing-Median (mit Historie) → `WARNING`. Echtdaten-Lauf zeigt keine Falsch-Anomalie auf den Demo-Gebieten.

### Durchführung + Closeout (18.06.2026) — ABGESCHLOSSEN
- **G5** (`qa_gate.apply_qa`): asymmetrisches Re-Review — `APPROVED` + echte QA-Flag-Obermenge → `PENDING`; `rejected` bleibt `rejected`; Teilmenge ändert nichts; **kein** Fingerprint-Eingriff (Bugfix: `SELECT` holt jetzt auch `flags_at_review`).
- **G17** (`metrics.anomaly_check` + `run_region`): 0 lieferbar → harte Warnung; Einbruch < 50 % Trailing-Median (≥2 Vorwochen) → Warnung; ohne Historie ehrlich None. Verdrahtet in `run_region` (loggt `log.warning` vor Auslieferung).
- **Refuter = adversariale Tests** (8 neue, Edge-Cases: rejected-bleibt-rejected · Flag-entfernt-bleibt-approved · keine-Historie-keine-Warnung). **345 Tests grün.**
- **Echtdaten:** gate-demo Münsterland/Osnabrück (41/48) → **keine** Falsch-Anomalie; leere Region (PLZ 99998, 0 lieferbar) → Warnung feuert korrekt.
- **Re-Score (Beleg):** Dim 5 **Observability 2→3** (Datenbruch warnt vor Auslieferung statt still leere Liste an Exklusiv-Kunden; Baseline-Infra gebaut, voll wirksam mit Wochen-Historie). Dim 2 **Korrektheit 4** (gehärtet: approved-dann-neu-geflaggt-Leck zu).
- **Vertagt:** Frische sichtbar (Säule 3) — T2-irrelevant, mit Säule 1/T1 vertagt. Volle Trailing-Baseline-Anomalie + per-Trigger-Diff-Metriken → M2 (brauchen FLUSS + Historie).

**Status Loop 1: ✅ ABGESCHLOSSEN.** Verbleibende M1-Gate-Code-Items: keine (USP ✓, Backup ✓, Mengen ✓, G5 ✓, G17 ✓); **kritischer M1-Pfad = nur noch Anwalt (PT1, Mensch) + Mensch-QA-Durchlauf**.

---

## Loop 2 · Getesteter Restore (DoD §9.5, Zielbild Datenverlust-Achse 5,0) — ABGESCHLOSSEN (18.06.)
**Ziel-Ableitung:** M1-Code ist fertig → der Loop zielt auf die DoD §9. §9.5 verlangt **„getesteter Restore"**; das Zielbild rät die Datenverlust-Achse auf **5,0** (existenziell — QA-/Exklusiv-/Liefer-Ledger nicht regenerierbar, Verlust zerstört das Exklusivitäts-Versprechen). Trifft die niedrigste Deploy-Dimension (2). **Challenge:** Portal/Auth = größerer Asset-Hebel (DoD §9.4), aber Multi-Session-Frontend → besser frisch; CI = M2; T1/T4 extern blockiert → Restore ist der bounded, completable, existenzielle Hebel jetzt.
- **Gebaut:** `state.restore_state_db` (validiert Backup = lesbare SQLite mit Kern-Tabellen VOR dem Überschreiben → nie kaputte Datei über Live-DB; atomar via `tempfile`+`os.replace`; stale WAL/SHM bereinigt) + `state.list_backups` + CLI `backup`/`restore` (Default neuestes).
- **Getesteter Restore (Exit):** voller **Backup → Datenverlust → Restore**-Zyklus, Daten intakt (Unit-Test + End-to-End-CLI: delivery 2 / exclusivity 1 nach Löschung + Restore wiederhergestellt). Kaputtes Backup wird abgelehnt, Live-DB bleibt unangetastet. **349 Tests grün (+4).**
- **Re-Score (Beleg):** Dim 9 **Betriebsreife/Datenverlust 2→3** (Backup + getesteter Restore des nicht-regenerierbaren Ledgers; Zielbild-Kern „getesteter Restore" erfüllt). Cron-Tagesbackup (G32-Ops) + voller CI/IaC bleiben M2.

**Status Loop 2: ✅ ABGESCHLOSSEN.**

---

## Loop 3 · Kundenportal mit Login/Auth (DoD §9.4) — ABGESCHLOSSEN (18.06.)
**Ziel-Ableitung (§1.1):** Gründer-Direktive: Meilenstein erst „fertig", wenn alles davor top-tier ist (DoD §9, nicht Loop-Bookkeeping). Größter verbleibender §9-Hebel = **„Portal (mit Auth) läuft demonstrierbar auf Sample-Daten" (§9.4)** — das „verkaufbare Asset" + die niedrigste In-Scope-Dimension **UX (2)** (Zielbild 4,5: „sauberes, vertrauenswürdiges Kundenportal, Provenance 1-Klick"). Käufer-Frage „Was sehe ich als Kunde?" wird erst hier beantwortet. Baubar JETZT (Sample-Daten, LIVE aus) — nicht extern/human-gated.
- **Abweichung (§6.3, begründet):** **stdlib `http.server`** statt FastAPI+HTMX+Tailwind+Playwright (Backlog-Vorschlag). Gründe: architektur-konsistent („stdlib-first", wie das Admin-Dashboard); **voll in-process testbar** (Playwright-Browser-Download blockt hier wie der MaStR-Download → nicht verifizierbar = nicht „abgeschlossen aus meiner Sicht"); Zielbild UX 4,5 (nicht Consumer-Design-System). Invarianten unberührt.
- **Gebaut:** `pipeline/portal/` — `auth.py` (scrypt-Passwörter + Salt, Sessions als sha256(Token) in DB, Mandanten-Filter), `views.py` (sauberes HTML, alles escaped, Provenance 1-Klick + dl-de-Footer + Demo-Banner), `app.py` (HTTP-Hülle, HttpOnly+SameSite=Strict-Cookies, CSRF-Logout), `seed.py` (synthetische Demo-Leads, §0-bulletproof). Schema: `customer`/`portal_session`/`portal_lead`. CLI: `portal serve/seed-demo/add-customer`.
- **Refute = Security-Engineer-Review** (adversarial): **kein CRITICAL** (kein SQLi/IDOR/XSS/§0-Leck; Mandanten-Trennung serverseitig, cross-Mandant = 404). 1 HIGH (Session-Fixation-Restrisiko) + MEDIUMs **gefixt**: H1 Single-Active-Session (Re-Login invalidiert alte Tokens) · M1 `Secure`-Cookie (ENV-gated) · M2 Body-Limit (413) · **§0-Härtung: `nur_demo`-Filter serverseitig** (Demo-Modus zeigt NIE `demo=0`-Echtdaten — §0 im Lese-Pfad verriegelt, nicht nur per Schreib-Disziplin). M3 (Rate-Limit) als pre-Internet-Item dokumentiert vertagt.
- **Verifikation:** **366 Tests grün (+17 Portal: Auth, Mandanten-Trennung, voller HTTP-Flow inkl. cross-Mandant-404, CSRF-Logout, Session-Expiry, §0-Filter, Body-413).** End-to-End-Live-Server-Smoke (CLI seed/add-customer + curl Login→Cookie→eigene Leads→Demo-Banner→Auth-Pflicht).
- **Re-Score (Beleg):** **UX 2→4** (sauberes, sicheres Kundenportal mit Login + Mandanten-Trennung + Provenance 1-Klick + Demo-Banner — trifft die Zielbild-Merkmale; nur der volle Cockpit-Ausbau fehlt zu 4,5). Funktionsumfang eff.3→3,5 (verkaufbares Asset DoD §9.4). Infra-Sicherheit gehärtet (Auth/Session, security-reviewed). **DoD §9.4 erfüllt.**

**Status Loop 3: ✅ ABGESCHLOSSEN.**
