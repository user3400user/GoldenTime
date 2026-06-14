# Session- & Memory-Management
**Stand 13.06.2026 · Gehört in: 01_Strategie/ · Zweck: dauerhaft den Überblick behalten, über Chat UND Claude Code hinweg.**

---

## Das Grundproblem
Jede Claude-Session (Chat oder CC) startet ohne Erinnerung an die vorherige. Kontext muss aktiv übergeben werden, sonst wird jede Session ein Neustart. Lösung: **Dateien als Gedächtnis, Rituale als Disziplin.**

## Die drei Gedächtnis-Ebenen
1. **STATE.md** — der Master. Geschäftsstand, Funnel, Entscheidungen, nächste Aktionen. Wird von Chat UND CC gelesen. EINE Wahrheit.
2. **CLAUDE.md** (im Code-Projekt) — technisches Gedächtnis für CC. Stack, Pfade, Konventionen. Verweist auf STATE.md für Geschäftskontext.
3. **Projekt-Memory** (Claude.ai) — Dauerfakten per „merke dir …". Ergänzt STATE.md, ersetzt es nicht.

## Die Rituale (nicht verhandelbar)
- **Session-Start:** „Lies STATE.md" (Chat) bzw. CC liest STATE.md + CLAUDE.md. IMMER der erste Schritt.
- **Session-Ende:** „Update STATE.md" — neue Erkenntnisse, Funnel-Änderungen, Entscheidungen rein. Dann finale Dateien ins Drive.
- **Ein Arbeitsblock = ein Chat.** Kurz und fokussiert. Lange Chats verlieren Kontext und werden teuer/langsam. Lieber neuer Chat mit „Lies STATE.md".

## Wann neuer Chat, wann weiter?
- **Neuer Chat:** neues Thema (Pricing ≠ Mail-Drafts ≠ Build-Konzept), oder Chat wird lang/träge.
- **Weiter im Chat:** dasselbe Thema, aufeinander aufbauend, innerhalb einer Arbeitssitzung.
- **Faustregel:** Wenn du den ersten Satz mit „Also, zurück zu …" beginnen müsstest → neuer Chat + STATE.md.

## Trennung Chat ↔ Claude Code
| | Chat (claude.ai) | Claude Code (ZBook) |
|---|---|---|
| Rolle | Konzept, Strategie, Vertrieb, Doku | technischer Build |
| Gedächtnis | STATE.md + Projekt-Memory | CLAUDE.md + STATE.md (gesynced) |
| Output | Docs, Drafts, Auswertungen, STATE-Pflege | versionierte Pipeline, Code |
| Drive | liest + lädt Dateien | über lokalen Sync |

**Schnittstelle:** Build-Fortschritt wird in STATE.md §7 vermerkt → der Chat „weiß" beim nächsten Start, was CC gebaut hat. Umgekehrt liest CC den Geschäftskontext aus STATE.md.

## Wochenrhythmus (Vorschlag)
- **Mo:** STATE.md lesen, Woche planen, Funnel-Stand prüfen, Drafts senden.
- **Laufend:** Antworten triagieren (Mobile), Kostproben generieren (Chat).
- **Fr/So:** STATE.md-Wochenupdate, finale Dateien ins Drive, Monatskopie von STATE.md in 01_Strategie/ (Audit-Trail).

## Hygiene-Regeln
- Dateien IMMER mit Datum benennen, nie überschreiben; Altes → „deprecated" im Namen.
- Sensible Zugänge (Domain, Mail, API-Keys) in 05_Brand/ bzw. Passwortmanager — NIE in STATE.md oder Code.
- Nach jedem Meeting/Call: Ergebnis sofort in STATE.md §3/§10, sonst geht es verloren.
