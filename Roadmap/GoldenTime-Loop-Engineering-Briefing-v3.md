# GoldenTime — Loop-Engineering-Briefing v3 (für Claude Code)
**Stand: 18.06.2026 · Ziel: ein demo-perfektes, verkaufbares Vollsystem auf Best-in-Class-Niveau — gebaut über einen langen, selbst-verbessernden, markt-geerdeten Engineering-Loop, der seinen nächsten Schritt aus Evidenz ableitet, nicht aus diesem Dokument.**
**v3-Änderung:** Wedge-Filter ist jetzt ein **3-Wege-Entscheid** mit „Ressourcen-Vorteil automatisieren oder killen" (§4b, I10).

> **Diese Datei ist KEINE Task-Liste.** Sie ist die Betriebsanleitung für einen Loop. Sie sagt CC, *wie* zu arbeiten ist (§1–§6) und gibt ein *Hypothesen-Backlog* möglicher Bau-Schleifen (§7), das der Loop **umbaut**. Autoritäts-Rangfolge bei Widerspruch: **Invarianten (§3) > Loop-Modus (§1) > die zwei Ziele (§4) > Backlog (§7).**

---

## 0 · Auftrag in einem Satz — und die eine harte Grenze
**Auftrag:** Bringe GoldenTime vom Ist (≈ 2,6/5) auf das Zielband, indem du die volle Plattform baust und verkaufbar machst (inkl. Kundenportal mit Login/Auth), den Bau an **erfolgreichen, ehrlichen Markt-Vorbildern** schärfst, und auf **echten** MaStR-Daten beweist, dass das Kernprodukt funktioniert.

**Die EINE harte Grenze (nie überschreiten):**
> Alles **bauen** und auf **Sample-/synthetischen Daten** betreiben/vorführen ist erlaubt. **Echte** personenbezogene Registerdaten natürlicher Personen / e.K. an einen **zahlenden Kunden** ausliefern ist verboten, bis die anwaltliche Art-6(1)(f)-Freigabe vorliegt (PT1).

Datenfluss-Grenze, kein Bau-Stopp. Folgen: `LIVE_DELIVERY_ENABLED` Default **aus** (nur ein Mensch schaltet nach Freigabe um); Portal/Auth mit **vollem** Test-/Korrektheits-Anspruch (dort wird „läuft" sonst „Datenleck"); Demos auf Sample-Daten oder mit e.K./natürlichen Personen **hart gefiltert**.

---

## 1 · LOOP-MODUS, NICHT CHECKLISTE *(die wichtigste Regel des ganzen Dokuments)*
Der Wert dieses Runs liegt darin, dass der Loop **entscheidet, was als Nächstes am meisten hilft** — nicht, dass er ein Dokument von oben nach unten abarbeitet.

**Hart-Regeln gegen den Abarbeit-Fehlermodus:**
1. **Jede Iteration beginnt mit einer schriftlichen Ziel-Ableitung** in `LOOP-LOG.md`: *welches* Ziel als Nächstes, und *warum es die größte Hebel-Lücke ist* — belegt aus den lebenden Artefakten (§4a Engineering-Scorecard, §4b Konzept-Landkarte, letztes Loop-Log). **Kein Bau startet ohne diese Begründung.**
2. **Das Backlog (§7) ist eine Hypothese, keine Reihenfolge.** Der Loop darf Schleifen **umordnen, zusammenlegen, teilen, streichen oder neue erfinden**, wenn die Evidenz es sagt. Die dort genannte Reihenfolge ist eine Default-Vermutung, kein Skript.
3. **Verbot:** „die nächste Position in §7" als Default zu nehmen. Wer sich beim Durcharbeiten der Liste ertappt, ohne neu abzuleiten, ist im Fehlermodus → **anhalten und neu ableiten.**
4. **Challenge-Pflicht je Loop:** Die Recherche-Stufe muss mindestens einen besseren Weg vorschlagen **oder** schriftlich begründen, warum der aktuelle Plan noch der beste ist. Rubber-Stamping ist nicht erlaubt.
5. **Die lebenden Artefakte steuern**, nicht dieses Dokument: `LOOP-LOG.md` (Lehren), `KONZEPT-LANDKARTE.md` (Markt-Ziel), `LOOP-METRICS.md` (Echtdaten-Zahlen). Sie sind nach jedem Loop aktueller als dieses Briefing.

---

## 2 · Operating Principles
1. **Doppelt gemessen:** Jede Schleife endet mit Neu-Bewertung der **Engineering-Scorecard** (§4a) **und** einem Abgleich gegen die **Konzept-Landkarte** (§4b) — „sauber gebaut" UND „das Richtige, gemessen am Markt".
2. **Sicher:** Der Invarianten-Satz (§3) darf nie regredieren — die Verfassung gegen Qualitäts-Drift im langen Run.
3. **Markt- & Research-augmentiert:** Die Planung gleicht nicht nur Ist↔Ziel ab, sondern Ist↔*was-erfolgreiche-Vorbilder-tun* (§4b). Abweichen vom Plan erlaubt, mit Begründung + Log (§6.3).
4. **Echtdaten-gegated:** Jede Pipeline-berührende Schleife beweist sich auf echten MaStR-Daten und schreibt Kennzahlen in `LOOP-METRICS.md`.
5. **Human-Checkpoint an Schleifen-Grenzen:** Innerhalb autonom; zwischen Schleifen Vorlage an den Gründer (Re-Score-Delta + Markt-Funde + Plan-Abweichungen + Echtdaten-Zahlen) → Freigabe. Knappe Ressource = Review-Aufmerksamkeit + Essenstermin, nicht Compute.

---

## 3 · Frozen Invariants (bei JEDEM Schritt prüfen, nie brechen)
- **I1** Tests bleiben grün (Stand 313); neue Oberflächen bringen Tests mit.
- **I2** Snapshot-Atomarität (`tempfile`→`os.replace`, BaseException-sicher) bleibt.
- **I3** Diff-Klassifikation (T1/T4/PV_ERWEITERUNG) bleibt korrekt, Golden-File-gedeckt.
- **I4** Ehrlichkeit: keine unkalibrierte Konfidenz ohne Disclaimer; T2 = BESTAND; dl-de-Quellenvermerk + Disclaimer in jeder Lieferung (Mail/CSV/Portal).
- **I5** Mengen-Reconciliation geht immer auf (sonst blockiert der Lauf).
- **I6** Exklusivität/Dedupe bleibt erzwungen, sobald verdrahtet — **ein** Liefer-Funnel, kein Umgehungspfad.
- **I7** e.K./natürliche Personen nie im an zahlende Kunden lieferbaren Bucket, solange die Schalter aus sind; Demo-Buckets filtern sie hart.
- **I8** `LIVE_DELIVERY_ENABLED` = aus, bis ein Mensch nach Anwalts-Freigabe umschaltet. CC setzt ihn **nie** selbst.
- **I9** Kein Roh-Personendaten-Egress an Dritt-Dienste (Sentry/MCP etc.): PII aus, Scrubbing.
- **I10** **Wedge-Treue & Anti-Theater:** Keine markt-importierte Funktion wird gebaut, ohne den 3-Wege-Wedge-Filter (§4b) zu bestehen. Eine Automatisierungs-Lösung für einen Ressourcen-Vorteil wird nur „adopted", wenn sie auf Echtdaten **nachweisbar funktioniert** und die Käufer-Frage besteht; sonst wird die Idee **gekillt**, nicht als toter Code gebaut.

---

## 4 · Die ZWEI Ziele (Doppel-Target)
Der nächste Loop-Schritt wird aus der **größten Lücke über beide Ziele** abgeleitet.

### 4a · Engineering-Scorecard — „was ist" (intern, beleggestützt)
Re-Score je Loop, je Dimension 1–5 **mit Beleg** (Befehl/Test/Beobachtung), Delta in `LOOP-LOG.md`.

| # | Dimension | Ist (17.06.) | Zielband | In-Scope |
|---|---|:--:|:--:|:--:|
| 1 | Funktionsumfang | 3 (eff. 2) | 4,5 | ✅ |
| 2 | Korrektheit | 4 | 5,0 | ✅ |
| 3 | UX & visuelle Professionalität | 2 | 4,5 | ✅ |
| 4 | Performance | 3 | 4,5 | ✅ |
| 5 | Observability/Tracking | 2 | 5,0 | ✅ |
| 6 | Sicherheit (Recht/Daten · Infra) | 2 | 5,0 · 4,5 | ✅ Code; Recht = PT1 (Mensch) |
| 7 | Datenqualität & -integrität | 3 | 5,0 | ✅ |
| 8 | Wartbarkeit/Codequalität | 3 | 4,5 | ✅ |
| 9 | Deploy-/Betriebsreife | 2 | 4,5 | ✅ |

### 4b · Konzept-/Markt-Landkarte — „was könnte werden" (extern, marktgeerdet) · `KONZEPT-LANDKARTE.md`
Das **zweite Ziel**: nicht eine a-priori-Spec, sondern aus **erfolgreichen, ehrlichen Vorbildern** abgeleitet. Lebendes Artefakt — im Konzept-Vorlauf (§5) erstellt, danach in jeder Recherche-Stufe geprüft, erweitert, verbessert.

**Strukturierte Recherche in Tiers (gezielt, nicht „schau Konkurrenten an"):**
- **Tier 1 — direkte Analoga:** Wer verkauft register-/MaStR-abgeleitete B2B-Signale, wöchentlich/exklusiv, im DACH-Energiemarkt? *(Dünne Trefferlage ist selbst ein Befund — loggen: bestätigt sie die Marktlücke?)*
- **Tier 2 — angrenzende Sales-Intelligence / Lead-Signal-Produkte** (z. B. Dealfront/Echobot, Cognism, ZoomInfo): **NICHT zum Feature-Kopieren**, sondern für Muster — wie zeigen sie **Evidenz/Provenance**, wie kommunizieren sie **Frische/Vertrauen**, welche **Pricing-/Territory-/Exklusivitäts-Modelle**, welche **Liefer-/Portal-UX**.
- **Tier 3 — „ehrliche" Datenprodukte auf öffentlichen/Register-Daten**, die auf **Transparenz/Provenance** gewonnen haben → mappt direkt auf I4.
- **Tier 4 — die Käuferwelt:** Worauf reagieren Speicher-Installateure real (Verbände, Foren, wie kaufen sie heute Leads)? → speist die Käufer-Frage-Batterie (§6.2) und das Wert-Framing.

**Werkzeuge:** Live-Web-Recherche (`web_search`/`web_fetch`); wo verfügbar die dedizierten Skills `competitor-intel`, `company-deep-dive`, `competitor-positioning`, `market-finder`.

**Wedge-Filter (Pflicht-Urteil je Fund) — der Wedge = Kaufmoment-Timing + regionale Exklusivität + Frische + ehrliche Provenance.** Drei-Wege-Entscheid, **in dieser Reihenfolge** (Reihenfolge ist load-bearing: erst Wedge-Relevanz, sonst öffnet die Automatisierungs-Frage die Bloat-Tür wieder):
1. **Wedge-relevant?** Stärkt der Fund den Wedge (oder reagiert der Käufer nachweislich darauf)? **Nein → verwerfen** (off-wedge Bloat, auch wenn jeder Konkurrent es hat). Ja → weiter.
2. **Solo von Hand machbar?** Ja → **direkt bauen.**
3. **Solo NICHT von Hand machbar** (Quantitäts-/Ressourcen-Vorteil — großes Team, manuelle Kuratierung)? Dann die Kern-Frage: **Lässt sich der Vorteil zu einer ECHTEN, funktionierenden Fähigkeit automatisieren — auf Echtdaten bewiesen UND die Käufer-Frage (§6.2) bestehend?**
   - **Ja → als Automatisierungs-Play bauen.** Genau das ist unser Solo-Edge: eine technische Lösung auf ein Quantitäts-/Ressourcenproblem.
   - **Nein → die Idee KILLEN.** Kein halb-automatisierter Schein wird gebaut — sonst entsteht nur Code ohne Funktion (Automatisierungs-Theater). „Funktioniert" = liefert den Wert auf Echtdaten, nicht „der Code läuft".
- Jeder Eintrag mit: **Quelle/Beleg · Tier · Entscheid (verwerfen / direkt / Automatisierungs-Play / killen) + Grund · Übersetzung in eine GoldenTime-Anforderung.**

---

## 5 · Konzept-Vorlauf (Loop −1) — die konzeptionelle Phase VOR dem Bau perfektionieren
Bevor scharf gebaut wird: ein **strukturierter Recherche-Pass** (Tiers §4b) → **v1 der `KONZEPT-LANDKARTE.md`** mit wedge-gefilterten, belegten Anforderungen. Danach lebt sie weiter (jede Recherche-Stufe prüft: hat sich etwas geändert, haben wir gelernt, dass der Käufer X will?).
**Exit:** `KONZEPT-LANDKARTE.md` existiert mit ≥ den Mustern aus Tier 2–4, je mit Beleg + Wedge-Urteil + GoldenTime-Übersetzung; offene Markt-Fragen für den Gründer markiert. *(Dies ist die einzige Schleife, die NICHT mit einem Echtdaten-Lauf endet — sie endet mit der Landkarte.)*

---

## 6 · Anatomie EINER Iteration
### 6.1 · Rollen (Multi-Agent — R0–R7-Methode, sauber strukturiert)
- **Planner** — leitet das nächste Ziel aus der größten Lücke über §4a+§4b ab; schreibt die Ziel-Begründung (§1.1) + Schleifen-Plan mit prüfbaren Exits.
- **Benchmarker/Researcher** — prüft *vor* dem Bau zwei Fragen: (a) besserer technischer Weg? (b) was tun erfolgreiche Vorbilder hier, das den Wedge stärkt (§4b)? Aktualisiert die Konzept-Landkarte. Darf den Plan verbessern (§6.3).
- **Builder** — implementiert; Skills/MCP (§6.4); Plan-Mode bei ≥3 Dateien/Schema/Security.
- **Refuter (adversarial)** — Code-Review + **Käufer-Frage-Batterie** (§6.2). Sucht, was die Demo zerbricht.
- **Verifier** — Tests grün + **Echtdaten-Lauf** + Reconciliation + Metriken→`LOOP-METRICS.md`.

### 6.2 · Käufer-Frage-Batterie (der Refuter MUSS bestehen)
Scharfer Speicher-Installateur/Berater bohrt; was nicht hält, wird gefixt: „Wie *garantiert* ihr Exklusivität?" · „Wie frisch wirklich — zeig Frische je Lead." · „Woher die Daten, dürft ihr sie verkaufen?" · „Wie viele Leads/Woche in *meinem* Gebiet — echte Zahl?" · „Bekomme ich denselben Lead zweimal?" · „Was sehe ich als Kunde?" *(Diese Liste wächst mit Tier-4-Funden aus der Konzept-Landkarte.)*

### 6.3 · Deviation-Protokoll (wann der Loop vom Plan abweichen darf)
Besserer Weg gefunden → abweichen erlaubt, aber (1) Begründung in `LOOP-LOG.md` (gegen Scorecard **und** Wedge, nicht „weil neuer"), (2) gegen Invarianten geprüft, (3) an der Schleifen-Grenze markiert vorgelegt. Verboten: Scope-Wucherung in Nicht-In-Scope-Dimensionen ohne Checkpoint; Wedge-verwässernde Features (I10).

### 6.4 · Skills- & MCP-Nutzung
`frontend-design`-Skill (UX/UI in Bau-Schleifen) · Playwright-MCP (Portal/Cockpit E2E **+** erzeugt Tests für die heute 0 %-getestete HTTP-Schicht) · Context7-MCP (aktuelle Lib-Docs → killt veraltete-API-Halluzination) · GitHub-MCP (eng-scoped) · `competitor-intel`/`company-deep-dive`/`competitor-positioning`/`market-finder` (Konzept-Landkarte) · `settings.json`-Hooks (`PostToolUse` ruff-fix; `Stop` Test-Suite → I1 automatisch). Stufen je Tool: Standortbestimmung §5.1–5.7.

### 6.5 · Schleifen-Template
```
0. ABLEITEN  Ziel + schriftliche Begründung der größten Hebel-Lücke (§1.1) → LOOP-LOG.md. KEIN Bau davor.
1. PLAN      Schleifen-Plan mit prüfbaren Exits.
2. RESEARCH  besserer Weg? + Markt-Abgleich (§4b) → Konzept-Landkarte aktualisieren; ggf. Plan verbessern.
3. BUILD     implementieren (Skills/MCP §6.4).
4. REFUTE    Code-Review + Käufer-Frage-Batterie (§6.2).
5. VERIFY    Tests grün + ECHTDATEN-Lauf + Reconciliation + Metriken→LOOP-METRICS.md.
6. RE-SCORE  Engineering-Scorecard neu (Beleg) + Konzept-Landkarte-Abgleich → Delta in LOOP-LOG.md.
7. CHECKPOINT  An den Gründer: Delta + Markt-Funde + Abweichungen + Echtdaten-Zahlen → Freigabe.
```

---

## 7 · Kandidaten-Backlog der Bau-Schleifen *(Hypothese — der Loop baut das um; §1 gilt)*
> Reihenfolge hier = Default-Vermutung „Demo-Hebel zuerst, Asset-Härtung danach". Der Loop ordnet nach Evidenz neu.

- **Loop 0 · Echtdaten-Lauf + echte Zahlen:** 2. Snapshot → Diff → echte T1/T4-Counts + Dichte je Gebiet (2–3 Einzugsgebiete). *Exit:* ≥1 echtes T1/T4-Signal auf Echtdaten; Zahlen in `LOOP-METRICS.md`; RAM/Laufzeit gemessen.
- **Loop 1 · Fundament tragfähig:** G0 (Exklusivität/Dedupe in **einem** Funnel, `--commit`/`--dry-run`, `BEGIN IMMEDIATE`, `record_delivery` nach Versand) · G5 · e.K.-Hartfilter (I7) · G12 RAM-Fix. *Exit:* 2. `--commit`-Lauf = 0 neue Einheiten; Region A schließt B aus; e.K. nicht im Bucket; Diff unter RAM-Ceiling.
- **Loop 2 · Kundenseitige Lieferung + Cockpit:** polierte Lieferung + Provenance 1-Klick + konfigurierbares Cockpit (FastAPI+HTMX+Tailwind/Basecoat; `frontend-design`; Playwright-E2E). *Exit:* E2E grün; Provenance 1-Klick; Cockpit zeigt Trichter je Gebiet×Trigger + Frische aus echtem Stand.
- **Loop 3 · Kundenportal mit Login/Auth (verkaufbares Asset, auf Sample-Daten):** Auth + wöchentliche exklusive Lieferung pro Kunde; **voller** Test-Anspruch auf Auth/Datenpfad; `LIVE_DELIVERY_ENABLED` aus. *Exit:* Auth E2E-gedeckt; Mandanten-Trennung getestet (A sieht nie Bucket B); läuft auf Sample-Daten; kein Pfad liefert echte Personendaten ohne Schalter.
- **Loop 4 · Asset-Härtung:** uv-Lock · ruff+mypy-lenient+pytest-cov+CI · structlog+Run-History · Anomalie-Alerting (Trailing-Baseline) · Backup/DR mit **getestetem** Restore · God-CLI → **ein** Funnel · toten Adapter-Layer entfernen. *Exit:* CI grün; Restore getestet; Anomalie-Flag feuert im Test; nur ein `filter_deliverable`-Aufrufer.
- **Loop 5 · Hosting/Mandantenfähigkeit (optional, Gründer-Entscheid):** Split-Architektur; managed Postgres (Supabase/Neon)+RLS+PITR; Scheduling; Secrets. *Exit:* Wochenjob gehostet in Runner-Limits; region-exklusive Listen über **mehrere** Mandanten erzwungen+getestet; PITR-Restore getestet.
- **Loop N (wiederkehrend) · Demo-Generalprobe:** `gate-demo` end-to-end auf echten Daten (e.K. gefiltert) → volle Käufer-Frage-Batterie → fixen. **Run-Done, wenn Batterie steht, beide Ziele im Zielband, Konzept-Landkarte erfüllt (wo wedge-stärkend).**

---

## 8 · Logistik & Reporting
- **Branch:** Feature-Branch `loop-engineering`; Merge nach `main` an sauberen Schleifen-Grenzen nach Checkpoint (schützt die demo-fertige `main`).
- **Lebende Artefakte (Source of Truth des Loops):** `LOOP-LOG.md` (Ziel-Ableitung, Abweichungen, Re-Score-Delta je Loop) · `LOOP-METRICS.md` (Lead-Counts T1/T2/T4, Dichte je Gebiet, Diff-RAM, Laufzeit) · `KONZEPT-LANDKARTE.md` (Markt-Ziel, wedge-gefiltert, versioniert).
- **Checkpoint-Format:** knapp — (1) Re-Score-Delta, (2) Markt-Funde + Landkarte-Änderungen, (3) markierte Plan-Abweichungen, (4) Echtdaten-Zahlen, (5) Empfehlung nächste Schleife.
- **Mensch behält:** Anwalts-Mandat (PT1) · `LIVE_DELIVERY_ENABLED`-Schalter · Freigabe an jeder Schleifen-Grenze · Entscheid über Loop 5 · Bestätigung der Wedge-Definition.

---

## 9 · Definition of Done (des gesamten Runs)
1. Engineering-Scorecard je In-Scope-Dimension im Zielband (§4a), je mit Beleg.
2. Konzept-Landkarte (§4b) erfüllt, **wo wedge-stärkend** — markt-geerdet, nicht nur intern bewertet.
3. Käufer-Frage-Batterie (§6.2) besteht vollständig auf echten Daten (e.K. gefiltert).
4. Portal (mit Auth) läuft demonstrierbar auf Sample-Daten; `LIVE_DELIVERY_ENABLED` aus.
5. Invarianten (§3, inkl. I10 Wedge-Treue) intakt; CI grün; getesteter Restore.
6. `LOOP-METRICS.md` enthält echte Lead-/Dichte-Zahlen je Demo-Gebiet.
7. **Bewusst NICHT enthalten:** echte bezahlte Lieferung an einen Kunden — wartet auf Anwalts-Freigabe + menschlichen Schalter.
