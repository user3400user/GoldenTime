# Decision Record — mastr-pv-leads (Konzeptphase)
_Stand: 2026-06-14 · Grundlage: report.md (N0+N+1), knowledge/mastr-buy-signals.md, knowledge/expansion-map.md_

## Gelockte Entscheidungen (2026-06-14)

**D1 — Wedge: BEIDE parallel (Neuinstallation + Post-EEG-Retrofit).** Beide aus derselben Pipeline.
Post-EEG = wachsende Kohorte (gemessen 63.807 in 2026 → 180–260k/Jahr ab 2029), harter Trigger (Förderende
31.12.); Neuinstallation = frischer Wochenfluss. Eine Pipeline, zwei Signallinien.

**D2 — v1 Ingestion: BULK-BACKBONE sofort (open-mastr → Postgres).** Voller Gesamtdatenexport, kein
Web-JSON-Pilot. Begründung: trägt den Speicher-Anywhere-Rollup, reproduzierbare Diffs UND das gesamte
Expansions-Trigger-Portfolio (expansion-map). Web-JSON bleibt punktuelle Echtzeit-Anreicherung.

**D3 — Produktform: SIGNAL-LEADS (Käufer kontaktiert).** Wir liefern strukturierte MaStR-Signale
(Entity · Signal-Typ · Evidenz-URL · Region · Datum · Konfidenz · Buy-Relevanz — CLAUDE.md-Schema); der
Käufer macht Outreach unter eigener Rechtsbasis. Kein Kontaktdaten-Enrichment, keine UWG §7/DSGVO-Outreach-
Haftung bei uns → schnellster Launch.

## Bedeutung der Kombination: „Full Foundation, Lean Product"
Kern-Artefakt = **Change-Detection-Engine über wöchentliche MaStR-Snapshots**: ingest → diff vs. letzter
Snapshot → klassifiziere Änderungen in Trigger-Typen (Neuregistrierung · Speicher-Retrofit · Betreiberwechsel ·
Direktvermarktungs-Schwelle · Status). Das Produkt ist damit weniger „Daten filtern" als „**Daten diffen**".

## Build-Konsequenzen
- **Backbone generisch** bauen (alle Energieträger + Lokationen + EEG-Anlagen + GelöschteUndDeaktivierte +
  Änderungen-Objekte), NICHT solar-only — die Expansion-Trigger hängen alle daran.
- **Snapshot+Diff-Schicht selbst bauen:** open-mastr baut Tabellen je Lauf NEU (kein Inkrement/Diff) → eigene
  versionierte Snapshot-Ablage + Diff-Logik drumherum.
- **Operator-Graph (ABR)** + **Freshness-Regel (IBN, nicht Reg-Datum)** + **Speicher-Score (mit Konfidenz)**.
- **NICHT bauen (v1, durch D3 deferred):** Kontaktdaten-Enrichment, Outreach-Tooling, Consent-Mgmt.
- **Build-Sequenz mit frühem Win:** Post-EEG-Signale shippen ZUERST (reine Kohorten-Query, kein Diff-Engine
  nötig, sofort nach Ingest lieferbar) → dann die Diff-Engine-Trigger (Neuinstallation/Retrofit/Betreiberwechsel).

## Nächste offene Entscheidungen
- Stack-Detail bestätigen (open-mastr→Postgres) · Snapshot-Kadenz & Retention (wöchentlich, dated).
- Trigger-Portfolio v1: welche Expansion-Trigger zusätzlich zu den 2 Wedges (Speicher-Retrofit naheliegend).
- Pricing/Packaging der Signal-Leads (per Signal / Abo / Regional-Exklusivität).
- Design-Partner / Erstkäufer (Speicher-/Retrofit-Vendor, Direktvermarkter).

## Offenes Rechts-Item (überlebt D3!)
Auch Signal-Leads = kommerzielle **Weiterverbreitung** MaStR-abgeleiteter Daten. Die MaStR-Nutzungsbedingungen
(Weiterverbreitung / Attribution / kommerzielle Nutzung; Sonderfall personenbezogene Daten natürlicher Personen)
sind NOCH NICHT geprüft. D3 entfernt die *Outreach*-Haftung, nicht die *Redistributions*-Lizenzfrage.
→ vor Launch klären (`/deepen mastr-pv-leads` „MaStR Nutzungsbedingungen kommerzielle Weiterverbreitung").
