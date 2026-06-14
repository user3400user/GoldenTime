# Sprint-Plan — 2 Wochen bis zum Berater-Essen (~27.06.2026)
**Erstellt 13.06. · Ziel: zeigbares Halb-Business. Danach fehlt nur ITIL „Deliver".**

> Prinzip: Produkt vorbauen, Kanal/Skalierung offen halten (Netzwerk-Input beim Essen). Verkauf läuft parallel.

---

## Woche 1 (13.–20.06.) — Fundament + Prototyp-Kern

### Identität & Ablage (Wochenende, ~2h, DU)
- [ ] **Domain registrieren** (Empfehlung kaufmoment.de + speicherleads.de defensiv). Anbieter: z.B. Infomaniak/Hostpoint (CH) oder Namecheap.
- [ ] **Google Workspace** einrichten, Arbeitsmail z.B. matthias@kaufmoment.de (~7 CHF/Mt). SPF/DKIM aktiviert Workspace automatisch.
- [ ] **LinkedIn-Profil** mit neuer Arbeitsmail (persönliches Profil, KEINE Company-Page).
- [ ] **Drive-Baum** anlegen (Struktur unten) + alle aktuellen Dateien einsortieren.

### Vertrieb läuft weiter (Mo 15.06., Klicks — DU; Drafts — CLAUDE)
- [ ] Claude legt 10 Nachfass-Einzeiler an (Welle-1-Threads) → DU sendest.
- [ ] Claude legt 10–12 Welle-2-Drafts an neue Käufer aus call-sheet an → DU sendest.
- [ ] Optional Telefonfenster Di–Do 8:00–8:45.

### Prototyp-Kern (CLAUDE baut, in Claude Code / lokal)
- [ ] **Pull-v2** stabil: MaStR-Abfrage modular, mit stabilen Schlüsseln (Basis steht: repull_ids.py).
- [ ] **Qualifizieren** als sauberer Schritt: Filter parametrisierbar, Ketten-/ÖFFENTLICH-Flags, Heuristik-Doku.
- [ ] **Anreicherung-Halbautomatik:** Domain→Impressum→GF/Tel-Vorschlag + Feld-Provenance, Mensch-QA-Spalte. (Basis: enrich_test.py — Extraktion härten.)

## Woche 2 (20.–27.06.) — Demo + Mechanik + Essen-Vorbereitung

### Zeigbarer Prototyp (CLAUDE)
- [ ] **Kostproben-Demo end-to-end:** Region rein → qualifizierte, angereicherte, geflaggte Liste + Liefer-Mail raus. (Basis: make_sample.py — auf v2-Anreicherung heben.)
- [ ] Optional: schlichtes Ein-Datei-Frontend, das den Fluss vorführt (kein Produktions-UI).

### Konzept-Dokumente (CLAUDE, diese Woche bereits angelegt — dann verfeinern)
- [ ] Geschäftsmodell-Canvas (1 Seite)
- [ ] Vertriebs-Mechanik (wie aus Kostprobe ein zahlender Retainer wird)
- [ ] Pricing-Logik (Anker, Stufen, Exklusivitäts-Aufschlag)
- [ ] Fragenkatalog fürs Netzwerk

### Essen-Vorbereitung (DU + CLAUDE)
- [ ] Prototyp auf einem Gerät vorführbar.
- [ ] Onepager + 1 Demo-Kostprobe gedruckt.
- [ ] Fragenkatalog präsent (Kanal, Pricing-Realität, Technik-Skills, weitere DE-Kontakte).

---

## Was bewusst NICHT in diesen 2 Wochen passiert
- Keine Vollautomation der Anreicherung (nimble) — erst wenn Kanal klar (P2).
- Kein Logo/CI, keine Website, keine Rechtsform/Handelsregister/MWST (erst ab Gate bzw. 100k).
- Kein CRM — Funnel-Tabelle in STATE.md reicht.
- Kein BPV-Gesuch (erst Trigger 3.5k MRR oder nach August).

## Drive-Struktur (manuell anlegen)
```
Gewerbespeicher-Leads/
├─ 00_README.md
├─ 01_Strategie/   Onepager, STATE-Kopien, Canvas, dieser Sprint-Plan
├─ 02_Daten/       clean-v2 CSV, Kostproben, make_sample.py, Pull-/Enrich-Skripte
├─ 03_Vertrieb/    Funnel-Log, Antworten, Liefermails, Vertriebs-Mechanik, Pricing
├─ 04_Compliance/  BPV-Mailbestätigung, Provenance, dl-de/by-2.0
└─ 05_Brand/       Domain-/Mail-Zugänge, Signatur, LinkedIn-Texte, Fragenkatalog
```
