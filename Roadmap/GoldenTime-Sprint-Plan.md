# GoldenTime — Sprint-Plan (operativ)
**Stand: 18.06.2026 · Die Datei zum sprint-für-sprint-Anweisen. Read-only erzeugt, kein Code verändert.**
**Endbild → `GoldenTime-Zielbild.md` · Fern-Teil/Provenienz → `GoldenTime-Roadmap-Fern.md`.**

> Nah-Teil (S0–S3, PT1) ist **gefroren** (konvergiert via Plan-Turnier). Diese Fassung ergänzt nur die
> **Risiko-Härtung (Pass B)**, ohne die Sequenz zu ändern — neue Punkte sind mit ⊕ markiert und hängen sich an
> bestehende Sprints/Tracks. Exit-Kriterien sind **prüfbar** (Befehl/Beobachtung). Belege: Datei:Zeile gegen `main`.

---

## 1 · Annahmen & Ist-Position
Lokales stdlib-Python-CLI, T2-Kohorte end-to-end lieferbar, 313 Tests grün, demo-fertig. Schnitt **Ist ≈ 2,6/5**.
Pre-revenue, 1 Gründer (BPV-Nebengig), 0 Kunden, manueller Wochenlauf (ZBook, 64 GB). Verifiziert: USP
(Exklusivität/Dedupe) im Code **nicht erzwungen** (`ledger.record_delivery` 0 Produktions-Aufrufer;
`deliver.run_region` `deliver.py:48` berührt den Ledger nicht; `cmd_signals` `cli.py:188-192` = vierter,
ungeschützter Funnel und einziger heutiger `filter_deliverable`-Aufrufer); T1/T4-Diff nie gelaufen (1 Snapshot);
DSGVO ungeklärt, e.K. nur geflaggt nicht gefiltert; dl-de-Resale erlaubt; 14 mypy-Fehler = False Positives.

## 2 · Meilenstein-Arc
| MS | Trigger | Definition-of-Done (verkürzt) |
|---|---|---|
| **M0** Demo/Essen (~27.06.) | Essen-Termin; ~erreicht | `gate-demo` reproduzierbar; QA-Queue der Demo-Gebiete 1× durchlaufen (nur PENDING-Grenzfälle; auto_ok ist heuristisch gedeckt, **nicht** handgeprüft — so pitchen); e.K./nat. Person **nicht** im gezeigten lieferbar-Bucket; Mail+CSV mit dl-de-Quellenvermerk+URL+Disclaimer; **T1/T4 als „kommt", nicht „live"**. ⊕ Aufwand des QA-Durchlaufs geschätzt (s. M0-Notiz). |
| **M1** erster zahlender Kunde lieferbar | ≥1 unterschriebene Zusage; Lieferung erst nach DoD | (1) Recht freigegeben (PT1) + e.K. hart aus jedem Deliverable; (2) USP in **allen** Pfaden erzwungen (G0a+G0b, `--commit`/`--dry-run`, Transaktion); (3) G5 asymmetrisch gefixt; (4) Datenbruch sichtbar (T2-Metriken+Anomalie); (5) Backup läuft; (6) Frische-Score geführt+sortiert; ⊕ (7) **Go/No-Go-Mengenzahl nach e.K.-Filter liegt vor**. *(T1/T4-Beweis ist NICHT M1.)* |
| **M2** verlässliche Auslieferung | Kunde #1 zahlt + #2 in Sicht | direktional → `GoldenTime-Roadmap-Fern.md` |
| **M3** skalierungsreif | mehr Kunden als manuell bedienbar | direktional; Endbild → `GoldenTime-Zielbild.md` |

**M0-Notiz ⊕ (Pass B.3 — Aufwand sichtbar):** Der manuelle „QA-Queue 1× durchlaufen"-Schritt ist **begrenzt und
schätzbar**: lt. STATE.md §7 ~**66 PENDING in Münsterland** (+ Osnabrück) → grob **~70–90 Grenzfälle** für die zwei
Demo-Gebiete. `qa suggest` (`cli.py:256`, `suggest_for_flags`) gruppiert sie in ~7 Flag-Muster (Energie-Firma /
öffentlich / Verein / Immo / Kette / nat. Person / Premium-Speicher) mit Copy-Paste-`reject`-Kommandos → die meisten
sind Massen-Rejects. **Grobe Zeit: ~1–2 h fokussierter Batch-Durchlauf.** Exakte Zahl vor dem Essen via `cli qa list`
abrufbar — **das ist das prüfbare Exit dieses Schritts** (Zahl vor dem Essen notiert, nicht offener Aufwand).

## 3 · Abhängigkeits-Karte & harte Reihenfolge-Zwänge (gefroren)
```
PT1 G23 Anwalt (Art-6(1)(f) + Lizenz-OK) ──────► gated M1   [KALENDER-LANGPOL; blockiert LIEFERUNG, nicht BAU]
S0 Vorbedingungen → S1 G0a Dedupe → { S2 G0b Exklusivität ; S3 Korrektheits-/Sicht-Leaks } → M1
```
**Kritischer Pfad zu M1 = KALENDER, nicht Code:** langer Pol = Anwalts-Vorlaufzeit. Technisch ist M1 in ~1–2 Wochen
baubar; die *Lieferung* wartet auf den Anwalt. **PT1 am Tag der ersten Zusage starten.**

**Harte Zwänge (nicht verhandelbar):**
1. Anwalt + e.K.-Politik vor erster **bezahlter** Lieferung — nicht vor Bau/Verkauf.
2. G0-Wiring in `deliver.run_region` **und** `cmd_signals`-Lücke schließen (`cli.py:188-192`).
3. `--commit`/`--dry-run` existiert, **bevor** je ein Live-`record_delivery` läuft (Demo füllt das Live-Ledger nie).
4. `is_available` + `filter_deliverable` + `record_delivery` in **einer** `BEGIN IMMEDIATE`-Transaktion; aber
   `record_delivery` erst **nach** bestätigtem Versand. ⊕ **Verfeinerung:** Es gibt **kein SMTP im Code** (verifiziert:
   `deliver.liefer_mail` `deliver.py:98` gibt nur Text zurück) → Versand ist **manuell** → `--commit` ist eine
   **bewusste Post-Versand-Bestätigung durch den Gründer**, kein Auto-Versand. Das Design muss das so abbilden.
5. G0a Dedupe vor G0b Exklusivität (Dedupe beißt Kunde #1, Exklusivität erst #2).
6. G32 Backup vor dem ersten `--commit` (`pipeline_state.db` nicht regenerierbar).
7. G17 T2-Metrik + Anomalie-Flag vor M2-Scheduling.
8. `cmd_diff`/FLUSS (`triggers/diff_based.py`, 0 Ledger-/0 Metrik-Aufrufe) ist bis M2 **nicht** kundentauglich.

---

## 4 · Parallel-Track PT1 · Recht (sofort bei erster Zusage starten)
Fachanwalt IT-/Datenschutzrecht: belastbare **Art-6(1)(f)-Abwägung** für den Verkauf register-abgeleiteter
Personendaten natürlicher Personen (e.K.); **Fragenkatalog inkl. „sind e.K. gar-nicht / nur-nach-QA verkäuflich?"**;
Art-14 / 14(5)(b); DPIA-Pflicht. + dl-de-Endbestätigung. Bezug: EuGH C-621/22, OLG Stuttgart 2 U 63/22.

### ⊕ PT1-Branch (Pass B.1): Was, wenn der Anwalt NEIN sagt (e.K. nicht verkäuflich)
**Kein offenes Ende — Fallback steht fest:**
- **Code:** der e.K.-Hartfilter (S0) bleibt **permanent Default-an**; das Deliverable = **nur juristische Personen /
  Organisationen**. Keine weitere Code-Arbeit nötig (der Filter wird ohnehin in S0 gebaut).
- **Mengen-Folge:** die lieferbare Menge sinkt. **Wie stark = wird gemessen** (⊕ B.2, S0/M1-Gate) — *nicht* geschätzt.
- **Wertversprechen / Kunde #1, ehrliche Hebel** (Frische-Fenster ist KEIN Hebel: für das T2-Bestandsprodukt
  irrelevant, und `config.FRISCHE_FENSTER_TAGE` steht bereits auf 45 = `config.py:113`):
  1. **Größeres Exklusiv-Gebiet** anbieten (mehr PLZ-Cluster pro Kunde) → hebt die Dichte ohne neue Daten.
  2. **Multi-Trigger-Bündelung** (T2 jetzt; T1/T4-FLUSS als Upsell ab M2) statt nur einer dünnen T2-Liste.
  3. **Ehrlichkeit als Grenze:** ist eine Region auch dann zu dünn → diese Region **nicht** an Kunde #1 verkaufen
     (eine dünne Liste als „exklusiv-wertvoll" zu pitchen zerstört genau das Vertrauen, das das Produkt verkauft).
- **Entscheidung:** dieser Branch verändert die **Sequenz nicht** — er ändert nur den **Default-Wert** des bereits
  gebauten Filters und die **Gebiets-/Pitch-Auswahl** für Kunde #1.

---

## 5 · Sprints (gefroren + ⊕ Pass-B-Ergänzungen)

### S0 · Existenzielle Vorbedingungen (abhängigkeitsfrei) — Effort M · depends_on: —
- **[G23-Mechanik, qa-unabhängig]** hartes Liefer-Gate in `deliver.run_region` **und** `cmd_signals`: Records mit
  `hierarchy.personenart_of(record)=='natuerlich'` (`hierarchy.py:217`) oder `FLAG_NATUERLICHE_PERSON` werden
  **nach** dem QA-Routing — übersteuert auch versehentliches `approve` — in einen **nicht-lieferbaren** Bucket
  geleitet. Schaltbar via neuem `config_store`-Flag `natuerliche_personen_freigegeben` (Default **aus**). Politik
  (gar-nicht vs. nur-nach-QA) erst **nach** Anwalts-Verdikt setzen (Mechanik jetzt, Politik später).
- **[G32]** `cron` + `sqlite3 pipeline_state.db .backup` → tägliche off-disk-Kopie (+ restic/rclone).
- **[G31]** `uv export` → hash-gepinnte `requirements.lock` (nur Rebuild-Absicherung gegen den 35-Dep-Graph, **nicht**
  das volle CI-Gate).
- **[G24]** `DL_DE` (`deliver.py:26`) um Lizenz-URL + „kein amtlicher Datensatz/keine Gewähr"-Disclaimer; in Mail UND CSV.
- ⊕ **[Pass B.2] Liefermengen-Messung nach e.K.-Filter:** mit aktivem Hartfilter `cli mengen --gebiete <demo>` bzw.
  `gate-demo` laufen (`deliver.mengen_report` `deliver.py:159`, `Buckets.betriebe()` `deliver.py:43`, `lieferbar`)
  und die **lieferbar/Betriebe-Zahl je Gebiet notieren**.
**Exit:** Anwalts-Mandat schriftlich erteilt (Datum dok.) · simulierter Restore öffnet Backup, `SELECT count(*) FROM
qa_decision` korrekt · `uv sync --locked` ohne Lock-Änderung, Suite grün · e.K./nat. Person erscheint **nicht** im
lieferbar-Bucket (Test) · `DL_DE`-Wortlaut in Mail+CSV · ⊕ **konkrete lieferbare Menge je Demo-Gebiet nach
e.K.-Filter liegt als Zahl vor.**
**Risiken:** Anwalts-Antwort dauert Wochen → M1-*Lieferung* verzögert sich real (akzeptiert). e.K.-Filter senkt die
Menge → mit Kunde #1 abgleichen (PT3 + B.2).

### S1 · G0a Dedupe im echten Lieferpfad erzwingen (+ cmd_signals-Lücke) — Effort M · depends_on: S0
`ledger.py` ist vollständig gebaut+getestet → **Wiring, kein Neubau**. `run_region(..., kaeufer, funktion,
commit=False)`; bei `commit=True`: `filter_deliverable` (Dedupe) → *(manueller Versand)* → `record_delivery` je
Einheit, in `BEGIN IMMEDIATE … COMMIT`, `record_delivery` **nach** der Gründer-Bestätigung (Zwang 4). `cmd_signals`
über `run_region` führen (löst G28) **oder** `--commit` gegen `cmd_signals` mit klarer Fehlermeldung sperren.
**Exit:** Integrationstest: 2 aufeinanderfolgende `--commit`-Läufe an denselben `(kaeufer,funktion)` → 2. Lauf
**0 neue Einheiten** (für jeden bezahlbaren Liefer-Befehl) · Demo-Lauf (`--dry-run`) hinterlässt **0 Zeilen** in
`delivery`/`exclusivity`.
**Risiken:** `cmd_signals`-Umbau ist mehr als reines Wiring (eigener Funnel) — realistisch M.

### S2 · G0b Exklusivität (is_available-Gate) im selben Pfad — Effort S · depends_on: S1
Setzt auf dem S1-Transaktions-Design auf (beißt erst bei Kunde #2). `is_available`-Check in **dieselbe**
`BEGIN IMMEDIATE`-Transaktion.
**Exit:** Integrationstest: `reserve(A)` → `filter_deliverable`/`is_available` für Käufer B in derselben Kombination
gibt `[]`/blockt · Dashboard-Exklusiv-Panel zeigt nach `--commit` die aktive Reservierung · Race-Test: zwei
quasi-gleichzeitige `--commit` → **nicht** zwei Reservierungen.
**Risiken:** Exklusiv-Granularität (Funktion×Gebiet×Trigger) mit dem Vertragsversprechen abgleichen (PT3).

### S3 · Korrektheits- & Sichtbarkeits-Leaks vor der ersten Lieferung — Effort M · depends_on: S1
- **[G5 — asymmetrisch, NICHT „Flags in Fingerprint"]:** `fingerprint()` (`qa_gate.py:101-114`) schließt Flags
  bewusst aus; der gespeicherte Entscheid hält unabhängig vom Flag-Feuern (R6, `qa_gate.py:155-157`) — Flags in den
  Fingerprint zu nehmen würde einen `rejected` wieder lieferbar machen. Korrekt: in `apply_qa` (Zweig „Fingerprint
  gleich", Z.159-161) — wenn `status == APPROVED` **und** die aktuelle QA-Flag-Menge **echte Obermenge** von
  `flags_at_review` (gespeichert Z.146-149) → `PENDING`. **`rejected` bleibt `rejected`. Kein Fingerprint-Eingriff.**
- **[G17 — Exit auf T2 beschränkt]:** `run_region` übergibt den realen Trigger; `_record_metrics` (`deliver.py:81`,
  heute `trigger="T2"` hardcoded) gruppiert je `trigger_typ` und schreibt je `(woche,gebiet,trigger)`; + simpler
  Anomalie-Flag (0 lieferbare / Einbruch → `log.warning`). **Kein Diff-Metrik-Exit an M1** (`cmd_diff` schreibt 0
  Metriken → sonst falsch-grün); volle Diff-Metriken = M2.
- **[G2/G20]** Frische-Score aus dem **Datenstand**; `b.lieferbar` nach Frische sortiert (`deliver.py:70`).
**Exit:** Test: zuvor approve-ter Lead bekommt NEU einen QA-Flag (ohne PersonenArt/Speicher/kWp-Änderung) → `PENDING`;
zuvor `rejected` bleibt `rejected` · gemischte Buckets → getrennte Metrik-Zeilen je Trigger · Lauf mit 0 lieferbaren →
WARNING · Frische-Sortierung durch Test gedeckt.

---

## 6 · M1-Gate (Go/No-Go)
M1 erreicht = **S0 ∧ S1 ∧ S2 ∧ S3 abgehakt UND PT1 (Anwalt) freigegeben.** Erst dann erste bezahlte Lieferung.
⊕ **Zusätzliches Go/No-Go (Pass B.2):** vor dem Pitch an Kunde #1 muss die **gemessene** lieferbare Menge (nach
e.K.-Filter, aus S0/B.2) gegen die Mengenerwartung des Kunden (PT3) gehalten werden. **No-Go**, wenn die Region zu
dünn ist → erst Gebiet vergrößern (PT1-Branch-Hebel 1) oder Region nicht verkaufen; **nie** eine zu dünne Liste als
exklusiv-wertvoll pitchen.

---

## ⊕ 7 · Weitere echte Nah-Teil-Lücken (mit Beleg, knapp — hängen an bestehende Sprints, keine Umsequenzierung)
- **Versand-Bestätigung ist ein menschlicher Schritt** (kein SMTP, `deliver.py:98`): `--commit` muss als
  *Nachweis-nach-Versand* dokumentiert sein, sonst markiert man Leads als geliefert, die nie raus sind → hängt an S1
  (Zwang 4, bereits oben).
- **`_record_metrics` Trigger-Hardcode** (`deliver.py:81` `trigger="T2"`): bei gemischten Buckets entstehen sonst
  falsche je-Trigger-Zahlen → in S3/G17 adressiert (oben).
- **e.K.-Erkennung ist nur so gut wie `personenart_of`/`market_actors`-Join:** fällt der Join aus, greift der
  Hartfilter evtl. nicht → der **G5-Fix (S3)** und das qa-unabhängige Gate (S0) müssen zusammen den Schutz tragen;
  als bewusste Doppel-Sicherung notiert, **keine** neue Sequenz.
