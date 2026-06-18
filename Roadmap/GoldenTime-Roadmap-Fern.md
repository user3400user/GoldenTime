# GoldenTime — Roadmap Fern-Teil (direktional) + Provenienz
**Stand: 18.06.2026 · Post-Kunde-Richtung, bewusst grob. Read-only erzeugt, kein Code verändert.**
**Operativer Nah-Teil → `GoldenTime-Sprint-Plan.md` · Endbild → `GoldenTime-Zielbild.md`.**

> **Bewusst grob:** M2/M3 werden vom ersten Kunden geformt. Hier stehen **keine Tickets und keine Feinplanung** —
> nur Meilenstein-Arc, Trigger, Entscheidungs-Gates und offene Fragen für Kunde #1–3. Feinplanung heute = Wegwerf
> (Detailtiefe ∝ Sicherheit). Das Exzellenz-Endbild dazu steht in `GoldenTime-Zielbild.md`.

---

## M2 · Verlässliche Auslieferung an die ersten Kunden
**Trigger:** Kunde #1 zahlt + #2 in Sicht; Wochenkadenz wird Pflicht; T1/T4-FLUSS wird als Retainer/Upsell relevant.
**Arc (grob):** FLUSS kundentauglich machen **+** Betrieb verlässlich. Größte Bauarbeit: **`cmd_diff` in den
Konsolidierungspunkt ziehen** — `run_region` ist heute cohort-only, `_record_metrics` T2-fixiert, `cmd_diff` hat eine
andere Signatur und 0 Ledger-/Metrik-Aufrufe → echter **M-Block**, damit FLUSS denselben Ledger+Metrik+e.K.-Filter
durchläuft wie T2. Dazu: Scheduling (cron/Actions) + Cron-Monitor; Anomalie-Alerting (≥4 Wo. Baseline); **volles
CI-Gate** (ruff/mypy-lenient/pytest-cov — amortisiert sich jetzt unter Umsatz); structlog statt print;
Run-History/Audit; dünner Faktura-Layer über dem Liefer-Ledger (kein Stripe).
**Entscheidungs-Gates:** Scheduling lokal (cron/ZBook) vs. Cloud · FLUSS eigener Preis-Tier vs. im T2-Abo enthalten.
**Offene Fragen für Kunde #1:** wöchentlich vs. monatlich beliefert? · ist T1/T4 ein eigener Preis-Tier?
**Bewusst offen:** Scheduling-Plattform; Faktura manuell vs. Stripe — vom Kundenvolumen geformt.

## M3 · Skalierungsreif (gehostetes, mandantenfähiges SaaS)
**Trigger:** mehr Kunden als manuell/lokal bedienbar; Region-Exklusivität+Dedupe muss über Mandanten garantiert sein.
**Arc (grob):** gehostet (managed Postgres + Auth/RLS-Mandanten); Kundenportal + Cockpit (FastAPI+HTMX+Tailwind/
Basecoat; `frontend-design`-Skill; Playwright-MCP); im Code erzwungene region-exklusive deduplizierte Listen über
**mehrere** Mandanten; Backup/DR (PITR); Datenbruch-Alerting produktiv; Fakturierung; Diff-RAM cloud-tauglich (G12);
ToS (G25) final. **Ziel-Exzellenz je Dimension → `GoldenTime-Zielbild.md` (4,5–5,0).**
**Entscheidungs-Gates:** SQLite→Postgres auslösen, wenn Concurrency/Mandanten es erzwingen · Self-Service-Portal
bauen, wenn manuelles Onboarding zum Engpass wird · Mandanten-Modell (RLS vs. Schema-pro-Tenant).
**Offene Fragen für Kunden:** Self-Service-Zugang oder kuratierte Lieferung? · wie überlappen Regionen über Kunden?
**Bewusst offen:** Hosting-Provider, Auth-Stack, Billing-Anbieter — alle vom realen Kunden-Pull geformt, heute Wegwerf.

---

## Bewusst gestrichen / kein Bau
- **G29 RegisterAdapter/MastrAdapter:** von Produktion ungenutzt → **löschen**, nicht ausbauen (bis 2. Register real).
- **G11 Monats-Anker-Retention:** YAGNI bis T5/T6 scharf.
- **G12 Diff-RAM-Opt:** auf 64-GB-ZBook unkritisch → erst bei Cloud/≤16 GB (M3).
- **G3 Fakturieren (voll/Stripe):** Kunde #1 manuell; dünner Ledger-Layer M2, Stripe M3.
- **G30/G33 volles Typ-/CI-Gate:** 14 mypy-Fehler = verifizierte False Positives; Gate amortisiert sich erst unter
  Umsatz → M2 (im Nah-Teil nur `uv.lock`).
- **G25 MaStR-Web-ToS:** kein M1-Blocker (Direktlinks öffentlich) → mit M3 bündeln.

---

# Anhang — Provenienz (aus dem operativen File ausgelagert)

## A · Varianten-Vergleich (warum das Backbone)
Backbone = **SCHNELLSTER-UMSATZ**, veredelt mit Grafts aus den anderen zwei Varianten.

| Kriterium | Sieger | Warum |
|---|---|---|
| Billigster-korrekter-Pfad zu M1 | Schnellster-Umsatz | T1/T4-Beweis/CI/Hosting gehören nicht in den M1-Korridor. |
| Abhängigkeits-Ehrlichkeit | Risiko-zuerst | ehrlichste hard-ordering-Zwänge (Backup-vor-commit, Transaktion, Anwalt≠Bau-Blocker). |
| Risiko-Abdeckung | Risiko-zuerst | alle 4 Bruchklassen (illegal/falsch/doppelt/still-kaputt) vor die 1. bezahlte Lieferung. |
| Detailtiefe ∝ Sicherheit | Schnellster-Umsatz | hält Fern grob, investiert Detail nur wo M1 es zwingt. |
| Prüfbarkeit der Exit-Kriterien | Risiko-zuerst | befehl-/beobachtbare Integrationstests fürs USP-Versprechen. |
| M0/Essen-Tauglichkeit | Schnellster-Umsatz | hält M0 auf dem real erreichten T2-Ist, ohne auf einen 2. Snapshot zu warten. |

**Grafts:** Backup (G32) in S0 vorgezogen · `record_delivery` **nach** bestätigtem Versand · `uv.lock` als reine
Rebuild-Absicherung (nicht das volle Gate) · `_record_metrics`-Trigger-Hardcode-Befund · **G0a vor G0b** · Datenbruch-
Sichtbarkeit (G17) in den M1-Korridor.

## B · Change-Log des Loops (Konvergenz-Provenienz)
- **Runde 1 — 3 Varianten** (Risiko-zuerst · schnellster-Umsatz · Fundament-zuerst), je voller Plan, unabhängig.
- **Runde 2 — adversariale Kritik** je Variante (versteckte Abhängigkeiten, Scheinpräzision, falsche Sequenz, schwammige Exits).
- **Runde 3 — Vergleich + Synthese:** Backbone gewählt; Code-Faktkorrekturen (cmd_signals ist 4. Funnel; cmd_diff
  0 Ledger/Metrik; `_record_metrics` T2-hardcoded; **T1/T4-Beweis aus M1 entfernt** — T2 trägt Kunde #1).
- **Runde 4 — Synthese-Verifikation (Verdikt: needs-another-round) → 4 Korrekturen eingearbeitet:**
  1. **[CRITICAL] G5 ent-kollidiert:** „Flags in `fingerprint()`" kollidierte mit R6 (`qa_gate.py:155-157`) → am Code
     bestätigt; korrigiert auf **asymmetrischen `apply_qa`-Fix** (kein Fingerprint-Eingriff).
  2. **[HIGH] e.K.-Hartfilter unterschätzt:** `PersonenArt` kein Record-Feld → qa-unabhängiges Gate in `run_region`
     **und** `cmd_signals`, Effort S→M.
  3. **[MEDIUM] M2-FLUSS-Konsolidierung unterschätzt** → als echter M-Block markiert.
  4. **[LOW] M1-Metrik-Exit auf T2 beschränkt** (`cmd_diff` schreibt 0 Metriken).
- **Finalisierung (18.06., Pass A + B):**
  - **Pass A:** Endbild von ~4,2 auf **4,5–5,0** angehoben (→ `GoldenTime-Zielbild.md`); Nah-Teil bewusst **nicht**
    angefasst (Exzellenz nicht in Sprint 0–3 vorgezogen).
  - **Pass B (Risiko-Härtung, ohne Umsequenzierung):** PT1-Negativ-Verdikt-Branch (e.K. nicht verkäuflich →
    Default-an + Gebiets-/Pitch-Hebel); Liefermengen-Messung nach e.K.-Filter als Go/No-Go (S0/M1-Gate, via
    `mengen_report`); M0-QA-Aufwand geschätzt (~70–90 Grenzfälle, ~1–2 h, via `qa suggest`); + Versand-ist-manuell-
    Verfeinerung (S1).
  - **Selbst-Check-Korrektur:** der „Frische-Fenster weiten"-Fallback wurde **verworfen** — `config.FRISCHE_FENSTER_TAGE`
    steht bereits auf 45 (`config.py:113`) und ist fürs T2-Bestandsprodukt ohnehin kein Dichte-Hebel; stattdessen die
    ehrlichen M1-Hebel (größeres Gebiet / dünne Region nicht verkaufen).

**Konvergenz:** Nah-Teil widerspruchsfrei, kein Meilenstein durch eine ungeplante Lücke blockiert, Detailtiefe
proportional zur Sicherheit, Exit-Kriterien prüfbar. Weitere Runden über dem Fern-Teil brächten nur Scheinpräzision
→ bewusst gestoppt. **Dies ist die Finalisierung, kein weiterer Loop.**
