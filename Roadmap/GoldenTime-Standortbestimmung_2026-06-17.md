# GoldenTime — Unabhängige technische Standortbestimmung
**Stand: 17.06.2026 · Read-only Gap-Analyse · Rolle: unabhängiger, adversarialer Principal Engineer**
**Methode: 9-Dimensionen-Multi-Agent-Review (je adversarial skeptiker-verifiziert) + eigene Code-Verifikation des Orchestrators + Diagnostik-Battery (Tests/Coverage/ruff/mypy/radon/vulture/pip-audit). Kein Code/Config verändert.**

> Lesehinweis: Jeder Befund trägt Beleg (`Datei:Zeile` bzw. Befehl+Ausgabe). Selbsteinschätzungen aus
> `CLAUDE.md`/`STATE.md` wurden **nicht** übernommen, sondern am Code geprüft. Wo das Repo ehrlich ist,
> steht das ausdrücklich dabei — diese Ehrlichkeit ist ein echter Aktivposten.

---

## 0 · Annahmen & Ziel-Latte (explizit)

**Produkt / Job-to-be-done (aus den Docs abgeleitet, am Code bestätigt):**
GoldenTime verkauft den *Kaufmoment* — deutsche Gewerbebetriebe, die gerade eine PV-Anlage **ohne Speicher**
angemeldet haben — **wöchentlich, qualifiziert, exklusiv pro Region** an je *einen* Speicher-Anbieter.
Kern-IP = Erkennung dieser Kaufsignale aus dem **MaStR-Gesamtdatenexport** über eine **Snapshot+Diff-
Change-Detection** (wöchentlich).

**Geschäftsstand (Kalibrierung — entscheidend für die Latte):**
PRE-REVENUE, **0 Kunden** (10 Kaltmails, 0 Antworten, `STATE.md:23-37`). **Ein** Gründer, Nebengig (BPV).
Läuft **lokal auf dem Laptop**, manuell wöchentlich. Nächstes Ziel = **Demo fürs Berater-Essen ~27.06.**
„Millionen-Business" ist die *Ambition*, nicht der Ist-Zustand.

**Ziel-Latte (technische/ingenieurmäßige Qualität auf dem Niveau eines ernsthaften, gut finanzierten SaaS —
für GENAU dieses Produkt):** Korrektheit, Robustheit, Testabdeckung, Typsicherheit, Sicherheit, Observability,
Performance, Datenintegrität, saubere Architektur, Fehlerbehandlung, Deploy-/CI-Reife, visuelle & UX-Politur.
**QUALITÄT ≠ GRÖSSE** — keine Abwertung für fehlende Konzern-Strukturen/Microservices, sofern sachlich nicht
nötig. Bewertet wird, was *vorhanden* ist, **und** was ein skaliertes Mehrkunden-SaaS *braucht* (klar getrennt).

**Wichtigste Rahmen-Erkenntnis (vorab, ehrlich):**
Die **Ingenieursqualität des Vorhandenen ist für dieses Stadium überdurchschnittlich** — verifiziert: atomarer
Snapshot-Write, korrekte Diff-Klassifikation, 313 grüne Tests, disziplinierte Fehlerbehandlung, *ehrliche*
Daten-Caveats. Der Abstand zum „Millionen-Business-SaaS" ist daher **zu ~70-80 % „Not-Yet-Built"**
(Hosting, Kunden-UI, Automatisierung, Mandantenfähigkeit, Billing, CI) **und zu ~20-30 % echte Defekte im
Vorhandenen** (Exklusivität inert, keine Quality-Gates, ~13 GB Diff-RAM, hohle Tracking-Hälfte, Typ-Lockerheit).
Zwei Dinge sind zugleich *gebaut* **und** *als Versprechen gebrochen* — und beide sind zentral:
(1) **Exklusivität/Dedupe ist nicht erzwungen**, (2) der **„Kaufmoment"-Diff lief nie** (nur 1 Snapshot).
Dazu **ein existenzieller Nicht-Engineering-Blocker**: die ungeklärte dl-de/by-2.0-Weiterverbreitungs- und
DSGVO-Frage.

---

## 1 · Inventur & Diagnostik (Belege)

### 1.1 Struktur & Größe
- Repo: `/home/puser/bigbag` → `GoldenTime/` (Produkt) + `research/` (Research-Workspace).
- Code (Python 3.12, stdlib-first; einzige schwere Dep `open-mastr`, nur für `build-db`):
  `GoldenTime/02_Daten/pipeline/` — **5.389 LOC Quellcode**, **4.123 LOC Tests** (`wc -l`).
- 26 Quell-Module + 18 Test-Module. Saubere Paketierung: `signal/ triggers/ qualify/ snapshot/ ledger/
  enrich/ control/ dashboard/ adapters/`.
- Datenmengen real: solar 6,21 Mio · storage 2,58 Mio · market_actors 5,42 Mio · 1 Snapshot
  `snap_2026-06-15.sqlite` = **1,07 GB / 8,79 Mio Zeilen**.

### 1.2 Diagnostik-Battery (read-only, Tools in `/tmp/gt-lib` außerhalb des Projekts installiert)
| Diagnose | Ergebnis | Bewertung |
|---|---|---|
| **Tests** | `313 Tests OK in 0,635 s` (stdlib unittest) | Claim „313 grün" **verifiziert ✅** |
| **Coverage** | 89 % **inkl. Testdateien** (die zählen ~99 % mit). Reale *Quell*-Coverage ~70-80 %, schwach an I/O-Rändern: `dashboard/app.py` **41 %**, `enrich/mastr_resolve.py` **43 %**, `export_adapter.py` **46 %** | Logik top, I/O-Ränder ungetestet |
| **ruff (default)** | nur **10** Issues (5 unused imports, 5 ambiguous names) | sehr sauber |
| **ruff (erweitert)** | 1222 line-too-long · 26 S608 (f-string-SQL) · 1 S324 (sha1) · 1 S110 · 2 S108 | Großteil kosmetisch; SQL/Hash geprüft (s.u.) |
| **mypy** (`--ignore-missing-imports`) | **14 Fehler in 5 Dateien**, KEINE mypy-Config | s. Korrektheit — alle 14 = False Positives |
| **vulture** | nur **2** Dead-Code-Items | minimaler Ballast |
| **radon CC** | Hotspots: `cmd_signals` **E(37)** · `iter_leads` E(31) · `cohort_signals` D(30) · `cmd_qa` D(30) · `liefer_mail` D(24) | CLI = God-Modul |
| **radon MI** | nur `cli.py` unter A (**B, 10.12**) | sonst durchweg A |
| **pip-audit** | **keine bekannten Vulnerabilities** | kleine Dep-Fläche |
| **Typ-Hints** | nur **165/580** Quell-Funktionen (~28 %) mit Return-Annotation | schwach, kein Gate |
| **CI / Tooling** | **kein** `.github`, **kein** `pyproject.toml/pytest.ini/pre-commit/conftest`, mypy/ruff/coverage **nicht** im Projekt installiert | Fundament-Defizit |
| **Secrets** | keine hartcodierten Secrets; `.env` gitignored, `${VAR}`-Expansion in `.mcp.json` | gute Hygiene ✅ |

### 1.3 Eigene Code-Verifikation des Orchestrators (unabhängig, vor/parallel zum Agenten-Review)
- **Snapshot-Atomarität (Kern-Integritätsanspruch): WAHR ✅** — `snapshot/store.py:203-222` schreibt in
  `tempfile.mkstemp` (gleiches Verzeichnis) → `commit` → `os.replace`; auf jede `BaseException` (inkl.
  `KeyboardInterrupt`) wird die Temp-Datei `unlink`t und re-raised. Streamt via Generator+`executemany`.
- **Diff-Klassifikation korrekt ✅** — `snapshot/diff.py`/`rules.py`: NEW_UNIT storage an Solar-ABR → `(T4,True)`;
  NEW_UNIT solar an neuer ABR → `(T1,False)`; an Bestands-ABR → `(PV_ERWEITERUNG,False)` (synthetisch
  end-to-end verifiziert, auch von Agenten).
- **Die zwei „Headline"-mypy-Bugs sind FALSE POSITIVES** (selbst nachvollzogen): `diff_based.py:175`
  `gruende = list(gruende)` bindet **vor** `.append` (Z.179) neu → kein `tuple.append`-Crash; `mastr_resolve.py:150-154`
  = heterogenes Dict als `dict[str,object]` fehlinferiert, zur Laufzeit harmlos. → Kein Crash, aber Beleg, dass
  **kein mypy-Gate läuft**.
- **Neu gefunden (real):** `diff_based.py:92 _load_snapshot_rows` lädt den **gesamten** curr-Snapshot als
  Dict-of-Dicts in RAM, um nur die wenigen Diff-Treffer nachzuschlagen → vermeidbarer Multi-GB-Peak (s. Performance).
  `HEUTE = date.today()` auf Modulebene (`normalize.py:25`, `cohort.py:36`, `diff_based.py:49`) → veraltet in
  langlebigen Prozessen.
- **Exklusivitäts-Ledger inert (selbst bestätigt):** `record_delivery` hat **0 Aufrufer** außerhalb Tests;
  `reserve` nur im manuellen `ledger`-Subcommand (`cli.py:373`); `filter_deliverable` *ist* in `cmd_signals`
  verdrahtet (`cli.py:192`), aber da nie `record_delivery` läuft, ist `already_delivered` **immer False** → der
  Dedupe-Filter ist **verdrahtet, aber wirkungslos**.
- **„Kaufmoment" lief nie:** `ls snapshots/` = **genau 1** Snapshot → `cli diff` gibt „<2 Snapshots" zurück →
  T1/T4 (das *differenzierte* Produkt) haben **auf Echtdaten noch kein einziges Signal** erzeugt.
- **Compliance (eigener Read `04_Compliance/Datenlizenz-und-Provenance.md`):** dl-de/by-2.0-**Weiterverbreitung
  kommerziell** = ausdrücklich „NICHT abschließend geprüft", „**Blocker-Status: kein Launch ohne dieses OK**".
  Attribution *ist* verdrahtet (`diff_based.py:192`, `deliver.py:26`), das *Recht* zur Resale aber unbestätigt.

---

## 2 · Scorecard — Ist-Level vs. Ziel-Level je Dimension
Skala 1 (weit weg) … 5 (Top-Tier). „Ist" beleggestützt, „Ziel" = Top-Tier *für dieses Produkt*.

| # | Dimension | Ist | Ziel | Δ | Ein-Satz-Abstand |
|---|---|:--:|:--:|:--:|---|
| 1 | **Funktionsumfang/Vollständigkeit** | 3* | 4 | 1 | T2-Kohorte komplett & sauber; das *literale* Kernversprechen (T1/T4-Change-Detection) ist gebaut, aber **nicht funktionsfähig** (1 Snapshot), Exklusivität/Dedupe & FAKTURIEREN unverdrahtet. *(\*großzügig; für das differenzierte Produkt effektiv 2)* |
| 2 | **Korrektheit** | 4 | 5 | 1 | Kern-IP korrekt & gut getestet; alle 14 mypy-Fehler = False Positives; Restkanten in QA-Fingerprint & cohort-Statusfilter. |
| 3 | **UX & visuelle Professionalität** | 2 | 4 | 2 | **Kein** kundenseitiges Produkt (Lieferung = CSV+E-Mail); internes Dashboard funktional, aber spartanisch (stdlib-HTML, 0 JS, keine Charts). |
| 4 | **Performance/Flüssigkeit** | 3 | 4 | 1 | Bei 1× korrekt & schnell, eine echte Opt (Streaming-Write); aber Wochen-Diff **~13 GB RAM** (nicht „~4 GB") → OOM-Risiko auf 16-GB-Laptop. |
| 5 | **Observability/Tracking/Steuerbarkeit** | 2 | 4 | 2 | Steuer-Hälfte real & sauber; **Tracking-Hälfte hohl**: Diff-Engine ohne Metriken, Lieferprotokoll leer, „Frische" = Schreibzeit, kein Alerting. |
| 6 | **Sicherheit** | 2 | 4 | 2 | Code-Hygiene überdurchschnittlich (kein erreichbares SQLi, escaped, keine Secrets) — aber **existenzielle Rechts-/DSGVO-Lücke** + null Security-Tooling. |
| 7 | **Datenqualität & -integrität** | 3 | 5 | 2 | Lokale Snapshot/Diff-Engine robust & korrekt; **USP-Versprechen Exklusivität+Dedupe in jedem realen Pfad unerzwungen**. |
| 8 | **Wartbarkeit/Codequalität** | 3 | 4 | 1 | Sauberer Domänenkern; untergraben von God-CLI (Funnel 4× reimplementiert), **dekorativem** Adapter-Protocol & fehlendem Typ-Gate. |
| 9 | **Deploy-/Betriebsreife** | 2 | 4 | 2 | Diszipliniertes Laptop-Tool; **kein** CI/Lockfile/Scheduling/Backup/Hosting — Weg zu hosted/mandantenfähig komplett „Not-Yet-Built". |
| — | *(Querschnitt: Tests)* | 3 | 4 | 1 | Starke behaviorale Unit-Tests am Logikkern; **0 % Coverage** auf jedem Orchestrierungs-Command (`weekly/gate-demo/liefern/diff`) + HTTP-Layer; **keine CI**. |

**Gesamt-Fazit:** Ein **technisch sauber gebauter, ehrlicher Prototyp/MVP** mit einem *korrekten und nicht-trivialen
Kern-IP* — aber gemessen an „Millionen-Business-SaaS" fehlen (a) die **End-to-End-Erzwingung des eigenen
USP** (Exklusivität/Dedupe), (b) der **Beweis des Kern-IP auf Flussdaten** (2. Snapshot), (c) die gesamte
**Betriebs-/Hosting-/Kunden-UI-/Automatisierungs-Schicht**, (d) **Quality-/Type-/CI-Gates**, und es steht (e) ein
**rechtlicher Launch-Blocker** im Raum, der kein Engineering-Problem ist. Durchschnitt Ist ≈ **2,6 / 5**, Ziel 4,2 —
der Abstand ist groß, aber das *Fundament trägt*.

---

## 3 · Gap-Liste (fehlt / muss dazu / muss raus)
Abstand-Einstufung: **Fundament-Defizit** (verfehlt Standard grundlegend) · **Substanz-Lücke** · **Feinschliff** ·
**Not-Yet-Built** (existiert noch nicht, vom skalierten SaaS gebraucht). Aufwand S/M/L/XL.

### 3.0 — DER zentrale Querschnitts-Befund (in 6 von 9 Dimensionen kritisch/hoch)
**G0 · Exklusivität + Dedupe (der USP) ist im Code nicht erzwungen.** [Substanz-Lücke → faktisch Fundament für das Geschäftsmodell] [Aufwand M]
- **Beleg:** `record_delivery` 0 Aufrufer außerhalb Tests; `reserve` nur manuell (`cli.py:373`);
  `filter_deliverable` (`cli.py:192`) nur bei `--kaeufer`+`--funktion` und schreibt nie `record_delivery` →
  `already_delivered` immer False; `deliver.run_region` (der echte Lieferpfad für `liefern`/`gate-demo`) berührt
  den Ledger gar nicht; Dashboard-Exklusivitäts-Panel rendert daher permanent „Keine aktiven Reservierungen"
  (`views.py:197`). Von 6 Dimensionen unabhängig bestätigt; Skeptiker-Verdikt: **confirmed/critical**.
- **Wirkung:** Das *einzige*, was GoldenTime verkauft — „exklusiv pro Region, nie derselbe Lead zweimal" — ist im
  laufenden System weder nachweisbar noch verhindert. Zwei Anbieter könnten dieselbe Region/Leads bekommen; ein
  zweiter Wochenlauf liefert dieselben Einheiten erneut.
- **Best-in-Class-Fix:** `deliver.run_region` zur *einzigen* Lieferstelle machen; vor Lieferung
  `ledger.is_available(...)` als Gate, `filter_deliverable` zum Dedupe, nach echtem Versand `reserve(...)` +
  `record_delivery(...)` **in einer expliziten Transaktion** (`BEGIN IMMEDIATE … COMMIT`), hinter einem
  klaren `--commit`/`--dry-run`-Schalter (Demo darf das Live-Ledger nicht füllen). Integrationstest: 2. Lauf
  liefert 0 neue Einheiten für denselben Käufer; Region an A schließt B aus.

### 3.1 — Funktionsumfang
- **G1 · T1/T4 „Kaufmoment" nicht funktionsfähig** [Substanz-Lücke; **Zeit/Daten-, kein Code-Defekt**] [M] —
  nur 1 Snapshot ⇒ `cli diff` = „<2 Snapshots". Die *gebaute & verifizierte* Diff-Engine hat auf Flussdaten noch
  nichts produziert. **Fix:** 2. Wochen-Snapshot ziehen (bzw. aus zurückgehaltenem Export-Slice synthetisieren),
  um den Pfad VOR dem Essen end-to-end auf Echtdaten zu beweisen; T1/T4 bis dahin nicht als „live" zeigen.
- **G2 · Frische-Score fehlt, Lieferung nicht nach Frische sortiert** [Substanz-Lücke] [S] — Spec §6/§7b verlangt
  „nach Frische sortiert, heißeste oben" + Frische-Score pro Lead; `SignalRecord` (`record.py:91-122`) hat kein
  solches Feld, Sortierung = `(dv_flag, kwp)` (`deliver.py:70`). **Fix:** `frische_score`/`lead_alter_tage` als
  Felder, in CSV/Mail führen, Sort-Key voranstellen.
- **G3 · FAKTURIEREN fehlt vollständig** [Not-Yet-Built] [L] — kein invoice/Mindermengen-Gutschrift/A-B-Quota
  (Spec §4). **Korrekt für jetzt deferred** (pre-revenue); für 1. Kunde dünner Billing-Layer über dem
  (zu verdrahtenden) Liefer-Ledger, **keine** Stripe-Integration vor ≥1 Vertrag.
- **G4 · T3 (Bestand Teileinspeiser) verwaist; Volleinspeisung/Teileinspeisung-Hartfilter (Spec §2) nicht
  erzwungen** [Substanz-Lücke/Feinschliff] [S-M].

### 3.2 — Korrektheit
- **G5 · QA-Fingerprint ignoriert `flags`** [Substanz-Lücke] [S] — `qa_gate.py:108-116` hasht nicht die
  QA-Flags. Ein **neu** geflaggter, zuvor approve-ter Lead bleibt approved und wird geliefert (live verifiziert:
  approve, dann VEREIN_PRUEFEN ergänzt → bleibt „approved"). Asymmetrisches Gegenstück zum (korrekten) R6-Fix.
  **Fix:** QA-relevante Flag-Menge in den Fingerprint aufnehmen (Hinzufügen invalidiert Approve; Entfernen ehrt
  Reject weiter).
- **G6 · cohort-T2-SQL-Statusfilter strenger als der dokumentiert-tolerante Python-Check** [Feinschliff] [S] —
  `cohort.py:152-155` `WHERE betriebsstatus='In Betrieb'` (exakt) vs. `normalize` ohne SQL-Filter → der tolerante
  `_in_betrieb` ist im cohort-Pfad für NULL/leer/kleingeschrieben tot; zwei Lead-Pfade widersprechen sich.
- **G7 · `HEUTE` auf Modulebene** [Feinschliff] [S] — Stale-Datum in langlebigen Prozessen. **Fix:** `heute`-Param,
  zur Aufrufzeit ausgewertet.
- **Korrektur (Phase 4):** Die 14 mypy-Fehler sind **keine** latenten Crashes (3 Agenten + Orchestrator-Verifikation).
  Echter Defekt = **fehlendes Typ-Gate**, nicht 14 Bugs.

### 3.3 — Datenqualität & -integrität
- **G0** (s.o.) ist primär hier verortet.
- **G8 · Snapshot-Stand-Datum fällt still auf `today()` zurück** [Feinschliff] [S] — `store.py:120` schluckt jeden
  Schema-Drift ohne Warnung → Snapshot trägt evtl. Laufdatum statt Export-Stand (verfälscht Diff-Wochenzuordnung
  & Retention). **Fix:** beim Fallback warnen/fehlschlagen.
- **G9 · Globaler `einheit_nr`-PK + `INSERT OR REPLACE`** [Feinschliff] [S] — eine (theoretische) solar/storage-
  Kollision droppt still den PV-Lead. **Fix:** zusammengesetzter Key (traeger, einheit_nr) oder Kollisions-Log.
- **G10 · Kein explizites Transaktions-Bracket in QA-Gate/Snapshot** [Feinschliff] [S] — per-Record-Autocommit;
  Mid-Batch-Abbruch hinterlässt Teilzustand. **Fix:** `BEGIN/COMMIT`-Klammer.
- **G11 · Monats-Anker-Retention (D2, „~13 Mt") nicht implementiert** [Not-Yet-Built] [S] — `prune` macht nur das
  8-Wochen-Fenster; T5/T6-Historie ginge verloren (heute ok, weil T5/T6 default-aus).
- **Plus (eigener Befund):** kein `fsync` vor `os.replace` → Durability bei Stromausfall nicht garantiert (Laptop-
  ok, Top-Tier würde fsyncen).

### 3.4 — Performance
- **G12 · Wochen-Diff-Peak ~13 GB RAM (nicht „~4 GB")** [Substanz-Lücke] [M] — gemessen auf echtem Snapshot:
  `diff._load` 3,34 GB/Snapshot, `diff()` lädt prev+curr = 6,73 GB, dazu hält `diff_based_signals` `prev_index`
  (~0,7 GB) **und** `_load_snapshot_rows` (`SELECT *` Dict-of-Dicts ~6,5 GB) gleichzeitig → `ru_maxrss ≈ 13,2 GB`.
  **OOM-Risiko auf 16-GB-Laptop = das eine, das den Kern-IP-Lauf killt.** **Fix:** redundante Loads streichen —
  `_load_snapshot_rows` löschen und die 2 benötigten Felder in `DiffEvent` falten; Diff als Streaming-MERGE-JOIN
  (`ATTACH` beider Snapshots, SQL-seitiger Set-Diff) statt In-Memory.
- **G13 · `PrevIndex.from_snapshot` Full-DISTINCT-Scan ohne Index (15,8 s)**; **G14 · jede Region = Full-Scan
  6,2 Mio Zeilen** [Feinschliff] [S] — Indizes/Single-Scan-über-mehrere-Gebiete. **G15 · Dashboard
  single-threaded** [Not-Yet-Built] [S]. **G16 · keine Perf-Regression-Guard** [Feinschliff] [S].

### 3.5 — Observability / Tracking / Steuerbarkeit
- **G17 · Diff/Snapshot-Engine schreibt KEINE Metriken** [Fundament-Defizit] [M] — `grep metrics. snapshot/
  diff_based.py` = nichts; nur T2-Pfad schreibt Metriken (hardcoded `trigger='T2'`). Für ein Change-Detection-
  Produkt ist Diff-Volumen je Gebiet×Trigger der **Herzschlag**; ein stiller Diff-Kollaps (z. B. MaStR-Format-
  Bruch) liefert leere Listen an zahlende Kunden **ohne Warnung**. **Fix:** je `(woche,gebiet,trigger)`
  new/changed/signals + `diff_volume` schreiben; Woche-über-Woche-Δ-Spalte mit Rotmarkierung.
- **G18 · Lieferprotokoll/Exklusivität strukturell leer** (= G0-Manifestation im Cockpit) [Substanz-Lücke] [M].
- **G19 · Kein Anomalie-/Alerting-Layer** [Not-Yet-Built] [M] — kein Schwellenwert/WoW-Vergleich; ein Datenbruch
  schippert still. **Fix:** z-Score/%-Change vs. 4-Wochen-Median, Dashboard-Rotflag + Log-WARNING (später
  smtplib-Mail).
- **G20 · „Frische"-Spalte = Metrik-Schreibzeit, nicht Datenstand** [Substanz-Lücke] [S]; **G21 · keine
  Run-History/Audit** [Not-Yet-Built] [M]; **G22 · print-getrieben** (63 print vs 23 logging), kein Log-File/
  Error-Tracking [Feinschliff] [M].

### 3.6 — Sicherheit & Compliance
- **G23 · DSGVO: Verkauf personenbezogener Daten natürlicher Personen (e.K.) ohne dokumentierte Rechtsgrundlage**
  [Substanz-Lücke; **existenziell**] [M] — `qa_gate.py:62` mappt `NATUERLICHE_PERSON_PRUEFEN → REC_PRUEFEN`
  (Review, **nicht** Reject); ein human-approved natürlicher Mensch fließt in `Buckets.lieferbar` →
  Kunden-CSV/Mail. `hierarchy.py:52` ausdrücklich „flaggen, NICHT hart ausschließen". Keine Art-6-Abwägung,
  kein DPIA, keine Art-14-Info. **Fix (zweischichtig):** (1) **Code** — e.K./natürliche Person per Default
  **hart** aus jedem Kunden-Deliverable (nur juristische Personen in v1), hinter Config-Flag mit dokumentiertem
  Rechts-OK. (2) **Recht** — Fachanwalt IT-/Datenschutzrecht + dokumentierte Interessenabwägung + Art-14-Konzept
  vor jeder bezahlten Lieferung.
- **G24 · dl-de/by-2.0 kommerzielle Weiterverbreitung** [~~Launch-Blocker~~ → **entschärft durch Research**] [S] —
  **Research-Update (Phase 5):** der offizielle Lizenztext (govdata.de) **erlaubt** die kommerzielle
  Weiterverbreitung abgeleiteter Datensätze; einzige Pflicht = **Quellenvermerk** (Attribution ist bereits
  verdrahtet, `diff_based.py:192`/`deliver.py:26`). Verbleibend: (a) schriftliche Endbestätigung inkl. BNetzA-
  MaStR-Sonder-Nutzungsbedingungen, (b) Attributions-Wortlaut um **Lizenz-URL** + „kein amtlicher Datensatz/
  keine Gewähr"-Disclaimer ergänzen. **Der echte existenzielle Blocker ist G23 (DSGVO), nicht die Lizenz.**
- **G25 · MaStR-Web-JSON-API mit gespooftem Browser-User-Agent gescraped** (`mastr_resolve.py:31,51`) [Substanz-
  Lücke] [M] — ToS prüfen; ggf. offizieller Weg/Rate-Limit-Vertrag.
- **G26 · Null Security-Tooling/Secret-Scanning im Lifecycle** [Fundament-Defizit] [S]; **G27 · reflektierter
  XSS-Sink** im Dashboard-Fehlerpfad `app.py:151 f'<p>{e}</p>'` [Feinschliff, localhost] [S].
- **Korrekt NICHT über-geflaggt (verifiziert):** die 26 S608-f-string-SQL sind **nicht injizierbar** (nur
  config-kontrollierte Identifier, Werte parametrisiert); `sha1` (`qa_gate.py:116`) ist nur Change-Fingerprint,
  kein Sicherheits-Hash.

### 3.7 — Wartbarkeit / Architektur
- **G28 · CLI-God-Modul** (`cli.py` 646 LOC, `cmd_signals` CC=37) fusioniert argparse + Orchestrierung +
  DB-Lifecycle + Business-Regeln + stdout-Formatierung; **der Kern-T2-Funnel ist 4× reimplementiert** (`cli.py:174,
  344, 404` + `deliver.py:52`), das Headline-Command ruft `run_region` **nicht** auf [Substanz-Lücke] [M]. **Fix:**
  `deliver.run_region` zur einzigen Funnel-Stelle promoten; ~120 Zeilen CLI-Orchestrierung löschen.
- **G29 · D4-`RegisterAdapter`-Protocol/`MastrAdapter`/`NormalizedUnit` von Produktion ungenutzt** [Substanz-
  Lücke] [L] — nur Tests konsumieren sie; Produktion liest über `normalize.iter_leads`; `adapters/mastr.py`
  ist eine **3./4. Kopie** des Query-Layers. Der Architektur-Claim „Quelle entkoppelt" ist im Code **falsch**.
  **Fix:** Entweder real machen (normalize/cohort über den Adapter routen) **oder ehrlich löschen** (YAGNI bis 2.
  Register existiert) — bei 1 Register & pre-revenue: **jetzt löschen**.
- **G30 · Kein Typ-Gate, 28 % Annotationen** [Fundament-Defizit] [M] (s. 3.2).

### 3.8 — Deploy-/Betriebsreife
- **G31 · Kein Dependency-Lockfile** [Substanz-Lücke] [S] — `requirements.txt` = nur `open-mastr>=0.17.1`; `pip
  freeze` zeigt 35 ungepinnte Pakete (pandas 3.0.3, numpy 2.4.6, SQLAlchemy 2.0.51 …). Ein Rebuild zieht einen
  anderen Graph → bricht `build-db` evtl. kurz vor der Demo. **Fix:** `uv`/pip-tools Hash-Lock, aus Known-Good-venv.
- **G32 · Kein Backup/DR für `pipeline_state.db`** [Substanz-Lücke] [S] — hält QA-Verdikte + Ledger + Metriken,
  **nicht regenerierbar**, gitignored, Laptop ohne Sync. **Fix:** wöchentlich `con.backup()`/litestream nach
  off-disk/cloud.
- **G33 · Keine CI / kein Quality-Gate** [Not-Yet-Built] [S/M]; **G34 · Wochenlauf voll manuell** (definierende
  Kadenz „wöchentlich" = Handarbeit, 26-min-Block-Download) [Not-Yet-Built] [M]; **G35 · `config_store`
  `schema_version` ohne Migrationspfad** [Feinschliff] [S]; **G36 · keine Containerisierung/Hosting/Mandanten-
  fähigkeit/Auth** [Not-Yet-Built] [XL].

### 3.9 — UX & visuelle Professionalität (eigene Bewertung)
- **G37 · Kein kundenseitiges Produkt** [Not-Yet-Built] [L] — Lieferung = CSV + E-Mail-Text (`deliver.py`).
  Für „höchstprofessionell/flüssig" gibt es schlicht *kein* Kunden-Frontend (Portal/Lieferansicht/Login).
- **G38 · Internes Dashboard spartanisch** [Feinschliff/Substanz] [M] — `dashboard/app.py` = single-thread stdlib
  `http.server`, server-rendertes Plain-HTML (1 Style-Ref, **0 JS**), keine Charts, kein Auth/CSRF (localhost).
  Solide *als internes Tool*, aber kein „Cockpit"-Eindruck. **Fix:** s. Research-Brief (Streamlit/FastAPI+HTMX+
  Tailwind/shadcn + Charts) — und **erst dann** polieren, wenn Tracking-Daten (G17-G21) real sind.

### 3.10 — Was WEG muss (Ballast / Tech-Debt / Totes)
- **Dekorativer Adapter-Layer** `adapters/mastr.py` + `register.py`-Protocol **+ dessen Tests** — solange kein 2.
  Register existiert, ist das gepflegte Totlast & eine divergierende Query-Kopie (G29). **Löschen oder real machen.**
- **3-/4-fache Funnel-Reimplementierung in `cli.py`** (G28) — auf eine getestete Stelle reduzieren.
- **`record_delivery`/`reserve` als „getestete, aber tote" Bibliothek** — entweder verdrahten (G0) oder die Tests
  als „nicht-verdrahtet" kennzeichnen (sie erzeugen sonst falsche Sicherheit).
- **5 unused imports / 2 vulture-Dead-Items / 1 unused `kwargs`** — trivialer Aufräum (`ruff --fix`).
- **`make_sample.py` (Legacy-CSV-Pfad)** — als bewusster Fallback dokumentiert; ok zu behalten, aber als „legacy"
  markieren, damit er nicht als Zweitpfad gepflegt wird.

---

## 4 · Self-Improving-Loop — Change-Log (Konvergenz sichtbar)

**Runde 1 (Breite, 9 Dimensionen parallel):** Erstentwurf je Dimension mit Ist/Ziel + Funden.

**Runde 2 (Skeptiker-Verifikation, je Dimension 1 Refuter + „was übersehen"):**
- **Hochgestuft:** Der `record_delivery`-Befund wurde vom Korrektheits-Reviewer als „Not-Yet-Built" geführt, vom
  Verifier auf **high/confirmed** korrigiert; Datenintegrität stuft ihn **critical**. → In **G0** als Querschnitts-
  Top-Befund konsolidiert (statt 6× doppelt zu zählen).
- **Herabgestuft:** FAKTURIEREN: Reviewer „HIGH", Verifier-`corrected_severity` = **low** (pre-revenue korrekt
  deferred). → G3 als „Not-Yet-Built, jetzt korrekt de-scoped".
- **Nuanciert:** T1/T4-„non-functional": Verifier = `partially_confirmed` → als **Zeit/Daten-Gap, kein Code-Defekt**
  präzisiert (Engine gebaut & verifiziert korrekt; braucht nur 2. Snapshot). → G1.
- **Bauchgefühl gestrichen:** Die „14 latenten mypy-Bugs" wurden von 3 Agenten **und** vom Orchestrator als False
  Positives belegt → in der Korrektheits-Bewertung explizit korrigiert (Ist 4, nicht abgewertet für Phantom-Bugs);
  echter Defekt = fehlendes Gate.
- **Über-Flagging vermieden (verifiziert):** S608-SQL nicht injizierbar, sha1 = Fingerprint, S324 unkritisch — nicht
  als Sicherheitslücken gewertet.

**Runde 3 (Orchestrator-Synthese, dieser Bericht):**
- Querschnitts-Dedup: G0 einmal, Manifestationen je Dimension verlinkt.
- **UX-Dimension ergänzt** (kein eigener Agent gelaufen) — eigenbewertet aus Dashboard-Inspektion + „kein
  Kunden-Frontend" (G37/G38).
- Eigene, von Agenten unabhängige Funde eingearbeitet: `_load_snapshot_rows`-Vollload (deckt sich mit G12),
  fehlendes `fsync`, Snapshot-Datums-Kollision/Overwrite, Modul-`HEUTE`.
- **Ehrliche Kalibrierung der „Ist=3"-Funktionsnote** als „großzügig; effektiv 2 für das *differenzierte* Produkt".

**Runde 4 (Research-getriebene Revision, Phase 5):**
- **Schlussfolgerung geändert:** G24 (dl-de/by-2.0-Resale) war als „Launch-Blocker, ungeprüft" eingestuft;
  Web-Research (govdata.de-Lizenztext) belegt: **kommerzielle Weiterverbreitung erlaubt** (nur Quellenvermerk).
  → G24 entschärft; der existenzielle Rechts-Blocker konzentriert sich auf **G23 (DSGVO/Art 6(1)(f))**, gestützt
  durch EuGH C-621/22 + OLG Stuttgart 2 U 63/22.
- **G33-Risiko relativiert:** open-mastr-„Format-Bruch"-Angst (Guardrail 01.10.2025) weitgehend entschärft —
  Projekt aktiv gepflegt, bereits auf XSD-getriebene dynamische Tabellen umgebaut.

**Konvergenz erreicht:** Kein materieller Befund blieb unverifiziert oder einseitig; die Severities wurden in beide
Richtungen korrigiert. Weiteres Bug-Hunting im Kern-IP zeigt **abnehmenden Grenzertrag** (Engine mehrfach unabhängig
als korrekt bestätigt). Die größten Hebel sind nicht „mehr Bugs", sondern die **5 strukturellen Lücken**: G0
(USP erzwingen), G1 (IP beweisen), G17/G19 (Datenbruch sichtbar machen), G23/G24 (Recht klären), G33/G31/G32
(Quality-/Repro-/Backup-Gate).

---

## 5 · Research-Brief (extern, copy-paste-fertig)
Web-recherchiert (2025/2026), gekoppelt an die Gaps. Empfehlungsstufen: **adopt** (jetzt) · **trial** (klein
testen) · **assess** (beobachten) · **avoid**. Volle Quellen-URLs je Item im Workflow-Output (`task w6z0thmwv`).
Bewertungskriterien je Item: Reife · Wartung · Lizenz · Passung (solo→SaaS, low-ops, Python/Claude-nativ, kein
Duplikat zu Vorhandenem).

### 5.0 · Research-Korrekturen (ändern Phase-3-Schlüsse)
1. **dl-de/by-2.0-Resale ist erlaubt** (govdata.de) → G24 vom Blocker zur Formsache (Quellenvermerk + Disclaimer).
2. **Echter existenzieller Blocker = G23 (DSGVO)**: Verkauf register-abgeleiteter personenbezogener Daten
   natürlicher Personen (e.K.) braucht eine anwaltlich gezeichnete **Interessenabwägung (Art 6(1)(f))** —
   Leitentscheide EuGH C-621/22 (KNLTB, 04.10.2024) + OLG Stuttgart 2 U 63/22 (02.02.2024); ggf. **DPIA** (Art 35)
   + **Art-14-Info** (bzw. Ausnahme 14(5)(b)).
3. **open-mastr-Format-Bruch-Angst entschärft**: aktiv gepflegt, auf XSD-getriebene dynamische Tabellen umgebaut.

### 5.1 · Claude-Code-Build-Setup — „bring Claude bei, das auf Top-Niveau zu bauen" (META, höchste Hebelwirkung)
*Gekoppelt an: alle Gaps (das ist das Werkzeug, mit dem der Rest gebaut wird).*
- **JETZT (adopt, null neue Infra):**
  - **Anthropic Plugin-Marketplace** (`~/.claude/plugins`, bereits lokal) → ins Pipeline-Projekt installieren.
  - **`claude-automation-recommender`** Skill — scannt das Repo read-only, empfiehlt die Top-Automationen
    (MCP/Skills/Hooks/Subagents). **Als Erstes laufen lassen** — er konkretisiert 5.2.
  - **`settings.json`-Hooks** (hand-geschrieben): `PostToolUse` auf `*.py` → `ruff check --fix && ruff format`;
    `Stop` → `unittest discover` (Exit 2 bei Rot speist den Fehler an Claude zurück). Macht die 313 Tests zum Gate.
  - **Serena MCP** (schon via `sc:load`) — symbolische Code-Navigation statt Datei-Dumps (Token-sparend).
  - **plan mode / `/ultraplan`** für jede Änderung an ≥3 Dateien/Schema/Security; **pr-review-toolkit**
    (`silent-failure-hunter`, `type-design-analyzer`); **`/code-review ultra`** (bereits vorhanden).
- **BALD (trial, beim Bau des Web-Stacks):** **Context7 MCP** (aktuelle, versions-spezifische Lib-Docs →
  killt veraltete-API-Halluzination bei FastAPI/Supabase); **`claude-md-management`**; **`security-guidance`** +
  Secret-Scan-`PreToolUse`-Hook; **hookify** (Regeln statt settings.json-Handarbeit).
- **SPÄTER (assess, bei Hosting):** **GitHub MCP** + `claude-code-action` (gehärtet, ≥2.1.128, eng-scoped wegen
  Prompt-Injection-Risiko); **genau eines** von **Supabase MCP** / **Postgres MCP Pro**; **Playwright MCP** (UI);
  **Sentry MCP**.
- **Hinweis:** Die reichen Hooks (SessionStart/PreToolUse/Stop) liegen aktuell nur im `research/.claude/` — prüfen,
  ob sie auch im Pipeline-Projekt aktiv sein sollen.

### 5.2 · Quality-Gates, Typsicherheit & Reproduzierbarkeit  → schließt G30, G33, G31, G7, G26
- **adopt:** **uv** (Astral) — hashed `uv.lock` + `uv export` → hash-gepinnte `requirements.txt`; eine Binary
  ersetzt pip/venv/pip-tools; pinnt `open-mastr`+Transitive, hält den stdlib-Kern dep-frei (G31). · **ruff**
  (Lint+Format, eine `pyproject.toml`; `extend-select` statt `select`, ISC001 aus). · **mypy** als Gate, aber
  **lenient starten** (kein `--strict`, per-Modul ratchet — sonst blockiert es jeden Claude-Edit bei 28 % Hints).
  · **pytest + pytest-cov + `fail_under`** (läuft die bestehende unittest-Suite unverändert; `--cov-config=
  pyproject.toml`). · **ruff-pre-commit** + **pre-commit** + **GitHub Actions** (`setup-uv` → `uv sync --locked`
  → ruff/mypy/pytest).
- **assess:** **ty** (Astral, 10-100× schneller, aber 0.0.x, instabile Diagnostics → noch **nicht** als Gate, nur
  als schneller Editor-Checker); **prek**/**lefthook** (schnellere pre-commit-Alternativen);
  **`simple-modern-uv`** (Projekt-Template als Referenz); **mcp-server-analyzer** (ruff/ty/vulture als MCP).
- **avoid:** `python-lft-mcp` (unreif).
- **Offene Fragen:** initiale mypy-Strenge/Scope bei 28 % Hints (Erfolgskrit.: Gate fängt echte None-Fehler an
  I/O-Rändern, blockiert aber nicht den Build-Loop) · pinnt `uv.lock` open-mastr-Transitive sauber per Hash, während
  der stdlib-Kern zero-dep installierbar bleibt · läuft die `unittest`-Suite unverändert unter pytest+cov.

### 5.3 · Datenqualität, Observability & Anomalie-Alerting  → schließt G17, G19, G20, G21, G22, G8
- **adopt:** **Sentry** (`sentry-sdk` MIT + **Cron Monitors**, Free-Tier) — `init()` + `@monitor` macht aus dem
  stillen „Job tot / lief nie" einen Alarm; **höchster ROI**. · **structlog** — run-scoped JSON-Logs
  (`run_id`+`woche`) statt 63× `print`; **+ neue `pipeline_run`-History-Tabelle** in `pipeline_state.db` (G21). ·
  **In-App-Trailing-Baseline-Anomalie-Check (stdlib, ~50 LOC)** — rollender z-Score/EWMA über das vorhandene
  `metrics_event` je `(woche,gebiet,trigger)`; rot-flaggen bei Diff-Volumen-Ausreißer (G17/G19), **kein Dep**,
  ehrt stdlib-first.
- **trial:** **Sentry MCP** (Issues/Stacktraces in Claude); **Pydantic v2** für Record-Level-Validierung (DataFrame-
  frei, passt zu den Lead-Dicts/SignalRecords).
- **assess:** **Pandera**/**Soda Core**/**reladiff** (gepflegter data-diff-Fork) — erst wenn Postgres/DataFrames
  da sind; **OpenTelemetry** (erst bei Hosting). · **avoid:** **Great Expectations** (Overkill für stdlib-Solo).
- **Offene Fragen:** welche Metriken je Lauf sind die richtigen Frühwarnsignale (global vs. je Gebiet) · Sentry
  **PII-/Egress-Policy** (die Pipeline erzeugt B2B-Personendaten — `send_default_pii=False`, Scrubbing!) ·
  Cold-Start des Baselines (Kadenz erst seit 2026-06-15 → erste ~4 Wochen ohne stabile Baseline).

### 5.4 · Laptop → hosted (multi-tenant) SaaS  → schließt G36, G34, G32, G31, G12-Skalierung
- **Architektur-Leitsatz:** **SPLIT** — billige Always-on-Web+DB-Schicht **+** ephemere Heavy-Batch-Schicht. Der
  8,6-GB-Export / ~4-13-GB-Wochenjob ist ein **EVENT, kein Service** → nicht dauerhaft groß dimensionieren.
- **Default-Stack (wenigste bewegliche Teile, adopt):** **Supabase** (managed Postgres + Auth/RLS-Mandanten +
  PITR-Backup, ~$25/mo; direktes Ziel für `MASTR_DB_ENGINE=postgres`, das der Code schon vorsieht) +
  **GitHub Actions cron** (Scheduling G34) + **Doppler** (Secrets) + **restic** (Backups G32) + **Supabase MCP**.
- **Cost-min-Alternative (trial):** **Neon** (scale-to-zero ~$3/mo für 8,6 GB, Branch-then-promote für den
  Wochen-Rebuild) + **Clerk** (B2B-Org-Auth) + **Modal** (Python-nativer Heavy-Batch, `@app.schedule`).
- **trial:** **Fly.io** (microVM-Hosting, auto-stop), **Litestream** (SQLite→S3-Replikation als Brücke),
  **Postgres MCP Pro** (Index-Tuning/EXPLAIN). · **assess:** Prefect/Dagster (erst wenn cron nicht reicht),
  Railway/Render, Auth0, pgloader (SQLite→PG-Migration). · **avoid:** **AWS RDS** (Overkill für Solo).
- **Offene Fragen:** passt der Wochenjob nach G12-Opt in einen 7-GB-Actions-Runner · Mandantenmodell (RLS vs.
  Schema-pro-Tenant) für **region-exklusive** Listen · DB live-mutieren vs. offline bauen + promoten (Neon-Branch-
  Swap) · reale Monatskosten bei 0 und bei ~N Kunden · Litestream überhaupt nötig oder direkt managed-PG-PITR.

### 5.5 · Kunden-Frontend + Ops-Cockpit + visuelle Politur  → schließt G37, G38, G15
- **Leitsatz:** **EIN** Python-ASGI-Stack deckt beides ab. **adopt:** **FastAPI + HTMX + Jinja2 + Tailwind/
  Basecoat** — Kundenportal (wöchentliche exklusive Lieferung + Provenance-Direktlinks) **und** Ersatz für den
  spartanischen single-thread `http.server` (G38, G15). · **Anthropic `frontend-design` Skill** + **Basecoat**
  (MIT, shadcn-Optik ohne React) = **High-End-Look praktisch gratis**. · **Playwright MCP** (Microsoft, Apache-2.0)
  → Claude treibt+verifiziert Portal & Cockpit end-to-end, generiert E2E-Tests (deckt zugleich die 0 %-getestete
  HTTP-Schicht ab!). · **Plotly** für Charts.
- **trial:** **FastHX** (HTMX-Helfer für FastAPI), **Streamlit** (nur internes Cockpit, schnellster Weg). ·
  **assess:** FastHTML+MonsterUI (Wartung prüfen), **Figma Dev-Mode MCP** (falls Designs entstehen), **Clerk**. ·
  **avoid (jetzt):** **Next.js/React** (zu schwer für Solo), **Retool/Appsmith** (Lock-in, Kosten).
- **Offene Fragen:** Cockpit build (FastAPI+HTMX) vs. buy (Streamlit) · Portal-Auth managed (Clerk/Supabase) vs.
  Python-nativ (Magic-Link) bei kleiner Kundenzahl · **wie eng koppelt das Portal an G0** (record_delivery/
  Exklusivität — das Portal macht das Exklusiv-Versprechen erst sichtbar) · bestes Provenance-Anzeige-Muster
  (Evidenz-Direktlink + dl-de-Lizenz + Konfidenz-mit-Disclaimer).

### 5.6 · MaStR-Quelle & Recht/Compliance  → schließt G23, G24, G25, G33-Risiko
- **adopt (Quellen/Belege):** **open-mastr** (aktiv, XSD-dynamisch) · **BNetzA Gesamtdatenexport-Doku Rev 25.2** ·
  **dl-de/by-2.0 Lizenztext (govdata.de)** — Resale erlaubt + Quellenvermerk-Pflicht · **EuGH C-621/22 + OLG
  Stuttgart 2 U 63/22** (Leitentscheide Art 6(1)(f) Adresshandel) · **MaStR robots.txt/Nutzungsbedingungen** (für
  G25-Scraping). · **trial:** Art-14(5)(b)-Aufwand-Ausnahme; DSFA/DPIA-Trigger (Art 35 + DSK-Muss-Liste). ·
  **assess:** `marktstammdatenregister-dev/mastr` (Go-Alternative als Fallback), `bundesAPI/marktstammdaten-api`,
  **DDV-Ehrenkodex Adresshandel** (Branchen-Selbstregulierung).
- **Offene Fragen (→ Fachanwalt IT-/Datenschutzrecht, schriftlich VOR der 1. bezahlten Lieferung — Erfolgskrit.:
  belastbares Schreiben, das im Streitfall trägt):**
  - Deckt dl-de/by-2.0 *unser konkretes* Modell (wöchentlich exklusive abgeleitete Leadlisten gegen Geld)? Exakter
    Quellenvermerk-Wortlaut?
  - Ist Art 6(1)(f) für den **Verkauf** register-abgeleiteter e.K.-/Einzelunternehmer-Personendaten haltbar?
  - Greift Art 14(5)(b) (unverhältnismäßiger Aufwand) für nicht-filterbare e.K.-Restfälle, oder Info-Pflicht?
  - Löst die Verarbeitung eine **Pflicht-DSFA** aus (Art 35 + Land-DSK-Muss-Liste: großvolumig + Brokering)?
  - Ist die programmatische Auflösung öffentlicher MaStR-Detailseiten/Web-JSON innerhalb der ToS (UWG/DB-Recht)?

### 5.7 · „Was zuerst" — gekoppelte Reihenfolge (Vorschlag, kein Auftrag)
1. **Rechts-Klärung G23/G24** anstoßen (parallel, blockiert Verkauf, nicht Bau) + e.K. per Default hart filtern.
2. **Quality-Gate** (uv-Lock + ruff/mypy-lenient/pytest-cov + settings.json-Hooks + minimal CI) — billigster
   Fundament-Hebel, schützt alles Weitere (G30/G33/G31).
3. **G0 Exklusivität verdrahten** + **G1 2. Snapshot** (USP erzwingen + Kern-IP auf Flussdaten beweisen).
4. **G12 Diff-RAM** + **G17/G19 Diff-Metriken/Anomalie** + **G32 Backup** (Lauf übersteht Laptop & Datenbruch).
5. **Dann erst** Hosting (5.4) + Kunden-UI (5.5) — wenn ≥1 Zusage da ist.

---

## Anhang — Methoden-Transparenz
- **Diagnostik-Tools** (read-only, außerhalb des Projekts in `/tmp/gt-lib`): coverage, ruff 0.15.17, mypy 2.1.0,
  vulture 2.16, radon 6.0.1, pip-audit. Tests/Coverage via Projekt-venv (open-mastr vorhanden), `COVERAGE_FILE`
  außerhalb des Projekts. **Kein Code/Config im Projekt verändert; dieser Bericht liegt außerhalb des git-Repos.**
- **Review-Workflows:** (1) 9-Dimensionen-Review je adversarial verifiziert (18 Agenten, 1,46 Mio Tokens,
  401 Tool-Calls); (2) 6-Cluster-Web-Research (6 Agenten, 0,39 Mio Tokens, 155 Tool-Calls). Plus eigene
  Code-Verifikation des Orchestrators (Snapshot-Atomarität, Diff-Klassifikation, mypy-False-Positives, Ledger-
  Inertheit, Snapshot-Anzahl, Compliance-Doc).
- **Belegketten:** alle `Datei:Zeile`-Verweise gegen die Arbeitskopie `main` (Commit `081ec90`, 17.06.2026) geprüft.
