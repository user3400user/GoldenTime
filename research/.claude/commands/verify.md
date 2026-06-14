---
description: Run only the Phase-7 adversarial red-team pass on an existing report — verify citations, hunt counter-evidence. No new scope.
argument-hint: <slug>
---

Target slug: **$ARGUMENTS**

Run **only** the Phase-7 adversarial verification on `research/$ARGUMENTS/report.md`:

1. Confirm the file exists (Read it). If not, list the available slugs under `research/` and stop.
2. Launch the **`fact-checker`** subagent on the report: verify every non-trivial claim traces to a real
   source that actually supports it (no over-reach, no out-of-context quotes), hunt for counter-evidence and
   more-recent/more-authoritative sources, and confirm the strongest counter-position is present.
3. Apply the returned issues by severity: fix or add citations, downgrade confidence levels, or remove
   unsupported claims. Then append a `## Verification (<date>)` section summarizing what was checked, the
   issues found (CRITICAL/MAJOR/MINOR), and what changed.
4. Ensure `## Quellen` still covers every cited source after edits.

Do not expand the research scope — this is verification only.
