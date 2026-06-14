---
description: Extend an existing research report (run N+1) — load it, find gaps and open questions, research only those, and merge.
argument-hint: <slug>
---

Target slug: **$ARGUMENTS**

Extend the existing investigation at `research/$ARGUMENTS/` (this is run N+1, not a fresh start):

1. **Load** `research/$ARGUMENTS/report.md` and `notes.md` (Read them). If the folder is missing, list the
   available slugs under `research/` and stop.
2. **Find gaps** — the report's "Open questions / next steps", any `low`-confidence findings, unresolved
   contradictions, and anything that has gone stale since the run date.
3. **Re-scope only those gaps** into sub-questions, then run pipeline phases 2–7 (search → scout → triage →
   deep-read → synthesize → fact-check) on the gaps **only**. Reuse the same subagents and the
   `source-triage` skill.
4. **Merge** into `report.md`: update/append Key findings (mark new ones and date them), refresh
   Uncertainties and TL;DR, and **extend** `## Quellen` with the new sources. Keep prior findings unless
   contradicted — if contradicted, update them and cite the change.
5. For **monitoring** slugs, surface only NEW or changed signals since the last run and state the window covered.

Preserve the slug and the report structure from `CLAUDE.md`. Keep heavy reading inside subagents.
