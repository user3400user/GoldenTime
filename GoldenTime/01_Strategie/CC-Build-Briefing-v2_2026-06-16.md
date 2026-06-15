# CC-Build-Briefing v2 — Vollpaket-Architektur für Claude Code
**Erstellt 16.06.2026 · Gehört in: 01_Strategie/ · Ersetzt CC-Build-Briefing v1 (v1/v2-Gate-Logik überholt).**

> Frame: Wir bauen das technische **Vollpaket** — die generische Plattform-Schicht, nicht ein bewusst beschnittenes v1. Begrenzte Gebiete/Nischen zum Start sind **Dashboard-Konfiguration**, kein Architektur-Verzicht. Heikle Teile (Anreicherung) werden **gebaut, aber zuschaltbar** — scharf erst nach Kundencall + Lizenzklärung.
>
> Diese Datei gibt CC den vollen Bau-Kontext + die technischen Fakten. Die genaue Code-Struktur erarbeitet CC interaktiv mit dem Gründer in Session 1 (Start-Prompt am Ende). Geschäftskontext: STATE.md. Skalierungs-Logik: `Analyse-Expansionslandkarte-vs-Vollpaket_2026-06-16.md`.

---

## 1 · Die Bauphilosophie in einem Satz
**Volle Architektur bauen, schmal konfiguriert starten, alles über ein Dashboard schaltbar.** Fast jede künftige Erweiterung (neue Trigger, Gebiete, Käufer-Funktionen, sogar eine zweite Vertikale) ist auf dieser Plattform nur Konfiguration — kein Umbau. Genau das macht die Plattform zum Vollpaket.

## 2 · Was schon steht (Fundament, committed `96def26`)
Nicht neu bauen — darauf aufsetzen:
- `export_adapter.py` (open-mastr → SQLite) — Code steht, **noch kein echter 3-GB-Lauf**.
- `speicher_check.py` (ABR-Speicher-Anywhere, 3-Wege: kein Speicher gemeldet / Premium anderswo / colocated=Ausschluss) — getestet. Das technisch Schwierigste steht.
- `normalize.py` (Trigger T1/T2/T3 + Inbetriebnahme-Frische) — getestet.
- `cli.py` (`inspect` / `build-db` / `leads`), `tests/` 9/9 grün (synthetisch), `CLAUDE.md` als Technik-Gedächtnis.

## 3 · Die Vollpaket-Architektur (8 Komponenten)
```
                    ┌─────────────────────────────────────────┐
                    │   ADMIN-DASHBOARD (Steuer-Schicht)        │
                    │   Gebiete/Trigger/Module an·aus ·         │
                    │   Volumen-/Kosten-/Frische-Monitoring     │
                    └───────────────┬───────────────────────────┘
                                    │ liest Config, schreibt nichts in die Pipeline
   ┌────────────┐   ┌───────────────▼──────────┐   ┌──────────────────┐
   │ 1 BACKBONE │──▶│ 2 SNAPSHOT+DIFF-ENGINE    │──▶│ 3 TRIGGER-KLASSIF.│
   │ generisch  │   │ versionierte Wochen-Snaps │   │ T1/T2/T4/DV scharf│
   │ open-mastr │   │ + Diff = Kern-IP          │   │ T5/T6/PV-Erw. aus │
   └────────────┘   └──────────────────────────┘   └─────────┬────────┘
                                                              │
   ┌────────────┐   ┌──────────────────────────┐   ┌─────────▼────────┐
   │ 7 ENRICH-   │◀──│ 5 SIGNAL-RECORD-SCHEMA    │◀──│ 4 QUALIFIZIERER  │
   │ MODUL (AUS) │   │ +Konfidenz +Evidenz-URL   │   │ Ausschluss+QA    │
   └────────────┘   └───────────┬──────────────┘   └──────────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │ 6 EXKLUSIVITÄTS-LEDGER     │
                    │ pro Funktion × Gebiet ×    │
                    │ Trigger (ABR-Schlüssel)    │
                    └────────────────────────────┘
```

**1 · Backbone (generisch).** open-mastr → DB, alle relevanten joinbaren Tabellen, NICHT solar-only. Begründung: die Expansion-Trigger hängen alle daran.
**2 · Snapshot+Diff-Engine (das Kern-IP).** open-mastr baut je Lauf NEU (kein Inkrement) → eigene versionierte Snapshot-Ablage (dated) + Diff-Logik drumherum. Jedes Signal ist ein Diff, kein WHERE.
**3 · Trigger-Klassifikator.** Config-getrieben: T1/T2/T4/DV scharf, T5/T6/PV-Erweiterung gebaut-aber-default-aus (im Dashboard schaltbar).
**4 · Qualifizierer.** Ausschluss-Hierarchie (natürliche Person → öffentliche Hand → Verein → Konzern → PV-/Energie-Firma → Immo) + Mensch-QA-Gate. Heuristik-Listen als **pflegbare Datei**, nicht hartcodiert.
**5 · Signal-Record-Schema.** `Entity · Trigger-Typ · Evidenz-URL (öffentl. MaStR-Einheits-Link) · Region · Datum · Konfidenz · Buy-Relevanz`. **Konfidenz ist Pflichtfeld** (wegen der Melde-Gotchas, §4).
**6 · Exklusivitäts-Ledger.** Schlüssel **pro Funktion × Gebiet × Trigger** — nicht nur pro Gebiet. Macht Mehrfachverwertung (ein Gebiet, mehrere nicht-konkurrierende Käufer-Funktionen) zur Konfiguration.
**7 · Anreicherungs-Modul.** Domain → Impressum → GF/Tel + Mensch-QA + Stufe A/B/C (Design liegt in Lead-Spec §4). **Gebaut, aber DEFAULT AUS.** Scharf erst nach Kundencall (Wert-Frage) + Redistributions-Lizenz. Sauber als eigenes Modul kapseln, damit An/Aus ein Schalter ist.
**8 · Admin-Dashboard.** Siehe §6 — gleichwertige Komponente, hohe Priorität.

## 4 · Eingebettete technische Fakten aus der Expansions-Landkarte (NICHT neu recherchieren)
Die Landkarte hat diese build-relevanten Fakten bereits belegt (Quellen dort). Direkt verwenden:

**Joinbare Tabellen im Gesamtexport:** `storage_extended`, `wind_extended`, `biomass_extended`, `combustion_extended`, `kwk`, plus `*_eeg`-Tabellen, `electricity_consumer` (nur Großverbraucher HV/EHV), `GelöschteUndDeaktivierte`, Änderungs-Objekte. Backbone generisch über diese bauen.

**Diff-Schlüssel-Felder:** `Bruttoleistung`, `Inbetriebnahmedatum`, `DatumEndgueltigeStilllegung`, `DatumBeginnVoruebergehendeStilllegung`, `AnlagenbetreiberMastrNummer` (= ABR), `EinheitMastrNummer`, `EegMaStRNummer`. Maßgebliches Datenwörterbuch: offizielle Gesamtexport-Doku Rev. 26.1.2 (2026-06-11).

**Diff-Regeln (sparen Fehlbau):**
- **PV-Leistung:** Erhöhung ist NICHT als Feldänderung erkennbar (nur Reduzierung); PV-Zubau = **separate neue Einheit**. → PV-Erweiterung wird über „neue Einheit an Bestands-ABR" erkannt, nicht über Leistungs-Diff.
- **Wind/Biomasse/Verbrennung:** Erhöhungen werden als Leistungshistorie gespeichert → echter Repowering-Diff möglich (Backlog-Trigger).
- **Betreiberwechsel:** erzeugt KEINE Neuregistrierung → Signal = `AnlagenbetreiberMastrNummer`-Wechsel bei gleicher `EinheitMastrNummer`. Achtung False-Positive: Umfirmierung sauber abgrenzen.
- **Speicher-Retrofit:** neuer `EinheitenStromSpeicher` an ABR/Standort mit bestehender Solar-Einheit.

**Daten-Gotchas (müssen in den Konfidenz-Score):**
- Speicher-Nachrüstungen nur **~40 % fristgerecht gemeldet** → Retrofit-Signal lückenhaft/verzögert.
- „ohne Speicher"/„kein Ladepunkt" heißt **„nicht gemeldet", nicht „existiert nicht"** → grundsätzlicher MaStR-Vorbehalt, pro Negativ-Trigger als Konfidenz-Abschlag führen.
- Freshness über **Inbetriebnahmedatum, nicht Registrierungsdatum** (gegen Korrektur-Scheinfrische).

**Format-Hinweis:** MaStR-Format-Bruch 01.10.2025 — beim ersten echten `build-db` aufs Parsing achten.

## 5 · Bau-Sequenz (jede Phase hat einen zeigbaren Zustand)

**Phase 0 — Reality-Check (zuerst, P0).** `build-db` auf dem ZBook (echter ~3-GB-Lauf) + `inspect` → reale open-mastr-Tabellen/Spalten gegen `config.py` verifizieren. Entkoppelt ALLES Folgende vom Namens-Risiko. *Zeigbar: echte Inventarzahlen.*

**Phase 1 — Früher Win: Post-EEG-Signal-Shipper (T2).** Kohorten-Query (EEG-Jahr 2006/07 + kein Speicher gemeldet via ABR + Region) → Signal-Record-Output (Schema #5). **Kein Diff nötig** → sofort nach erstem Ingest lieferbar. Dazu DV-Flag (≥100 kWp, trivial) und Qualifizierer (#4) auf den Fluss. *Zeigbar: echte Signal-Liste für 1–2 Gebiete + Liefer-Mail — trägt das Berater-Essen.*

**Phase 2 — Das Kern-IP: Snapshot+Diff-Engine.** Versionierte Wochen-Snapshots + Diff-Logik. Damit T1 (Neuregistrierung), T4 (Retrofit), T5 (Betreiberwechsel), T6 (Stilllegung), PV-Erweiterung — letztere drei gebaut-aber-default-aus. *Zeigbar: „diese Woche neu gegenüber letzter" als echter Diff.*

**Phase 3 — Admin-Dashboard + Exklusivitäts-Ledger.** Steuer-Schicht (§6) auf die laufende Pipeline. Ledger pro Funktion × Gebiet × Trigger. *Zeigbar: Gebiet an/abschalten, Volumen/Kosten je Gebiet sehen.*

**Parallel, kein Bau-Blocker:** Anreicherungs-Modul (#7) als gekapseltes, default-ausgeschaltetes Modul.

## 6 · Admin-Dashboard — Komponenten-Spec (hohe Priorität)
Das Dashboard ist die Steuer-Schicht, die „alles bauen, schmal starten" bedienbar macht. Es **liest** Konfiguration und Metriken; es **greift nicht** in die Pipeline-Logik ein (saubere Trennung).

**Muss-Funktionen (MVP):**
- **Gebiets-Schaltung:** jedes Einzugsgebiet (PLZ-Cluster) einzeln an/aus. Grund: Gebiete abschalten, wo Leistung/Kosten es nicht tragen (ausdrückliche Anforderung).
- **Trigger-Schaltung:** T1–T6 + DV-Flag + PV-Erweiterung je einzeln an/aus (global und perspektivisch pro Gebiet).
- **Modul-Schaltung:** Anreicherung an/aus (der zentrale Zuschalt-Schalter).
- **Monitoring je Dimension:** Lead-/Signal-Volumen pro Gebiet × Trigger × Woche · Frische-Verteilung · Kosten-Proxy (Compute/Storage/Laufzeit). So wird „lohnt sich dieses Gebiet?" sichtbar.
- **Exklusivitäts-Übersicht:** welche Käufer-Funktion hält welches Gebiet (aus dem Ledger).

**Bewusst NICHT im MVP:** Kunden-Self-Service, Billing-Integration, CRM-Push, Mandantenfähigkeit. Das Dashboard ist zunächst **rein intern (Admin)**, kein Kundenprodukt.

**Technische Form (Vorschlag, in Session 1 mit CC bestätigen):** schlanke Web-App, die Config aus einem Config-Store liest und Metriken aus der Pipeline-DB. Kein schweres Framework, wenn ein leichtes reicht. Die Pipeline schreibt Metriken; das Dashboard liest — keine Kopplung in die Gegenrichtung.

## 7 · Offene Architektur-Entscheidungen für CC-Session 1 (mit Gründer klären)
1. **Stack DB:** SQLite vs. Postgres. *Empfehlung: Engine-Abstraktion behalten, auf SQLite iterieren (trägt das Volumen, schnellere Iteration), Postgres als Config-Switch, sobald das Dashboard nebenläufige Leser braucht oder gehostet wird.* Vollpaket-Architektur ja — aber Infra pragmatisch, nicht prophylaktisch.
2. **Snapshot-Kadenz & Retention:** wöchentlich, dated — wie viele Wochen aufbewahren? (Diff braucht ≥2; Historie für T5/T6 mehr.)
3. **Wo lebt der Config-Store** (Dashboard-Schaltungen): DB-Tabelle vs. Datei. Muss von Pipeline UND Dashboard gelesen werden.
4. **Register-Adapter-Interface:** wie abstrahieren wir die Pull-Schicht, damit ein zweites Register (EV-Ladesäulen, Auslands) später ein Adapter ist? (Nur Interface vorbereiten, nicht bauen.)
5. **Mensch-QA-Gate:** wie technisch einbinden (Review-Queue? Flag-Spalte? separates UI im Dashboard?).

## 8 · Realismus & explizit außer Scope
**Ambitioniert in ~2 Wochen — aber das Fundament (Pull + ABR-Check) steht getestet.** Die großen neuen Brocken sind Diff-Engine und Dashboard. Wenn die Zeit knapp wird, ist die **Demo-kritische Kette** Phase 0→1 (echter Ingest + Post-EEG-Signal-Liste) — die trägt das Essen allein. Diff-Engine (Phase 2) und Dashboard (Phase 3) sind die Vollpaket-Substanz; sie dürfen über das Essen hinausreichen, ohne die Demo zu gefährden.

**Außer Scope (Backlog, NICHT bauen — Begründung in der Expansions-Analyse):** zweite Vertikale (EV-CPO), Auslands-Register, andere Energieträger als scharfe Produkte, CRM-/API-/White-Label-Integrationen, Abo-Billing, Auktions-Marktplatz. **Kills nicht anfassen:** WP/Wallbox aus MaStR, AT-Register, Gewerbeanmeldungen, Handelsregister-Live, Vergabe-Auftraggeber.

## 9 · Start-Prompt für CC-Session 1
> „Lies STATE.md, CLAUDE.md, das CC-Build-Briefing v2 und die Expansions-Analyse in diesem Projektordner. Wir bauen das in §3 des Briefings beschriebene Vollpaket. Bevor du Code schreibst: (1) Führe Phase 0 aus — `build-db` echter Lauf + `inspect`, und verifiziere die realen open-mastr-Tabellen/Spalten gegen config.py. (2) Schlag mir dann eine saubere Projektstruktur für die 8 Komponenten vor und die 5 offenen Architektur-Entscheidungen aus §7 zur gemeinsamen Klärung. Danach bauen wir Phase für Phase, beginnend mit dem Post-EEG-Signal-Shipper (Phase 1). Halte CLAUDE.md als technisches Gedächtnis aktuell, und vermerke Build-Fortschritt so, dass STATE.md §7 ihn übernehmen kann."
