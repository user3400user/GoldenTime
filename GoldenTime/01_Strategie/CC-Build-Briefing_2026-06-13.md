# CC-Build-Briefing — ZBook-Umgebung & Kontext-Übergabe
**Stand 13.06.2026 · Gehört in: 01_Strategie/ · Zweck: Claude Code auf dem ZBook startklar machen + mit vollem Kontext versorgen.**

> Diese Datei beschreibt das SETUP und den KONTEXT für den Build — nicht die Build-Spec selbst. Die Spec erarbeitet CC interaktiv mit dir in der ersten Session (Prompt dafür unten).

---

## 1 · Wichtige Korrektur vorab: CC hat KEINEN direkten Drive-Zugriff
Der Drive-Connector ist an die Claude-Chat-Oberfläche gebunden, NICHT an Claude Code. CC arbeitet auf dem **lokalen Dateisystem** des ZBooks.
**Lösung:** Google Drive Desktop auf dem ZBook installieren → den Projektordner lokal synchronisieren → CC sieht ihn als normalen lokalen Pfad. Damit hat CC den vollen Kontext (STATE.md, alle Konzept-Docs, Daten, Skripte).

## 2 · Installation (verifiziert 13.06.2026, code.claude.com/docs)
**Voraussetzungen:**
- Node.js 18+ (`node --version` prüfen; sonst via nvm oder nodejs.org LTS installieren, danach Terminal neu öffnen — PATH-Refresh).
- Bezahlter Claude-Plan (Pro/Max) oder Console/API-Guthaben. Free-Plan deckt CC NICHT.
- Git 2.23+ empfohlen (Versionierung).
- Windows: WSL empfohlen (CC läuft in der Linux-Umgebung; Node.js IN der WSL installieren, nicht nur Windows-seitig).

**Installation (zwei Wege):**
- Empfohlen (zero-dependency, auto-update): nativer Installer — siehe code.claude.com/docs/en/setup.
- npm-Weg: `npm install -g @anthropic-ai/claude-code@latest` — NIE mit sudo. Bei EACCES: `npm config set prefix '~/.npm-global'` oder nvm.

**Verifizieren:** `claude --version` · `claude doctor` (prüft Install-Typ, Auth, Settings).

## 3 · Projekt aufsetzen (auf dem ZBook)
1. Drive-Ordner lokal gesynced (s.o.), z.B. `~/GoogleDrive/Gewerbespeicher-Leads/`.
2. Terminal dort öffnen, `claude` starten, Browser-Auth.
3. CC eine `CLAUDE.md` im Projektordner anlegen lassen (sein Dauegedächtnis — Pendant zu STATE.md, aber für den technischen Build). Inhalt: Tech-Stack-Entscheide, Pfadkonventionen, Datenquellen, „lies STATE.md für Geschäftskontext".
4. MCP-Server bei Bedarf einbinden (z.B. später nimble für Anreicherung) — erst wenn der Kern steht.

## 4 · Vorhandene Assets, auf denen CC aufbaut (im 02_Daten/)
- `mastr-leads-clean-v2-2026-06-11.csv` — 208 Leads MIT stabilen Schlüsseln (Betreiber-Nr. `abr`, Einheits-Nr.).
- `make_sample.py` — funktionierender Kostproben-Generator (Regionalfilter + Speicher-Gegencheck PLZ-Ebene + Flags + Aufhänger + Liefer-Mail). **Referenz-Implementierung, die CC zu einer sauberen Pipeline ausbauen soll.**
- Pull-Logik (in make_sample.py + frühere repull-Skripte) — MaStR-JSON-Endpoint verifiziert.

## 5 · Der Build-Auftrag (grob — Details erarbeitet CC mit dir)
Ziel bis ~27.06.: **end-to-end Prototyp** der 6-Schritt-Kette als saubere, versionierte Pipeline:
PULL → QUALIFIZIEREN → ANREICHERN (Halbautomatik + QA) → PAKETIEREN → (LIEFERN/FAKTURIEREN als Stubs).
Offene Architektur-Entscheide für die erste CC-Session: **ENTSCHIEDEN (14.06.):** Gesamtexport-Backbone via open-mastr (siehe Architektur-Entscheid), CC baut zuerst Export-Adapter + betreiberweiten ABR-Speicher-Check. Offen bleibt: Sprache/Struktur (Python-Module vs. Notebook vs. kleines CLI) · wie die Mensch-QA in der Anreicherung eingebaut wird · wo das Liefer-Ledger (Exklusivität) lebt.

## 6 · Prompt zum Start der ersten CC-Session
> „Lies STATE.md und alle Konzept-Dokumente in diesem Projektordner für den vollen Geschäftskontext. Wir bauen die in §6 von STATE.md beschriebene 6-Schritt-Pipeline als versionierten Prototyp. Bevor du Code schreibst: Schau dir make_sample.py und das clean-v2-CSV als Referenz an, dann schlag mir eine saubere Projektstruktur und die offenen Architektur-Entscheide aus dem CC-Build-Briefing §5 zur Entscheidung vor. Die Datenquelle ist entschieden (Gesamtexport via open-mastr, siehe Architektur-Entscheid) — beginne mit dem Export-Adapter + betreiberweitem ABR-Speicher-Check. Wir entscheiden gemeinsam, dann baust du Schritt für Schritt. Halte CLAUDE.md als technisches Gedächtnis aktuell."

## 7 · Arbeitsteilung Chat ↔ CC (sauber trennen)
- **Dieser Chat (Konzept):** Strategie, Pricing, Doku, Funnel-Auswertung, Mail-Drafts, STATE.md-Pflege.
- **Claude Code (Build):** die technische Pipeline, lokal, versioniert, mit eigener CLAUDE.md.
- **Schnittstelle:** STATE.md (Geschäftskontext, von beiden gelesen) + Drive-Sync. Was CC baut, wird als Stand in STATE.md §7 vermerkt.
