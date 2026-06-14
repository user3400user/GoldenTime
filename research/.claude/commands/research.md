---
description: Run the full 8-phase research pipeline on a question or monitoring target and save a cited report. Main entry point.
argument-hint: <research question or monitoring target>
---

Research request: **$ARGUMENTS**

Execute the full pipeline defined in `CLAUDE.md` (phases 1–8) on the request above. Do not shortcut it.

1. **Scope & decompose** into 3–7 sub-questions/claims; record known vs. must-look-up; set success criteria
   and a stop condition; choose a short, stable kebab-case `<slug>`.
2. **Search strategy** per sub-question — Tavily/WebSearch for breadth & discovery, Firecrawl/WebFetch for
   depth & defined-source monitoring. Record the queries you run in `notes.md`.
3. **Collect in parallel** — spawn one `source-scout` subagent per sub-question (single message, multiple
   Agent calls). Get back ranked candidates only.
4. **Triage** with the `source-triage` skill — dedupe, score credibility, select top sources, drop weak ones.
5. **Deep read** — spawn `deep-reader` subagents on the selected sources for digests + short quotes.
6. **Synthesize yourself** by question structure (agree/conflict/silent; evidence vs. speculation; name the
   strongest counter-position). For monitoring tasks, build the signals table from CLAUDE.md.
7. **Adversarial verification** — run the `fact-checker` subagent; fix or downgrade every issue. Never skip.
8. **Output** — write `research/<slug>/report.md` using the CLAUDE.md template (TL;DR, cited key findings,
   uncertainties/contradictions, open questions, and a mandatory `## Quellen` section). Keep `notes.md` and
   `sources.md`. Distil durable insights into `knowledge/<topic>.md` and link them from `knowledge/index.md`.

Create `research/<slug>/` if needed. Keep all heavy reading inside subagents so this thread stays clean.
