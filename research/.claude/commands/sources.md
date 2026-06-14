---
description: Print the append-only source ledger — all logged URLs/queries, or filtered to a slug/term.
argument-hint: "[slug or term]"
allowed-tools: Bash(cat:*), Bash(test:*), Bash(echo:*)
---

Filter: **$ARGUMENTS**

## Source ledger (raw)
!`L="${CLAUDE_PROJECT_DIR:-.}/_sources/ledger.log"; test -s "$L" && cat "$L" || echo "(ledger is empty — no sources logged yet)"`

## Instructions
The block above is the append-only source ledger written by the logging hook (one line per fetched URL or
search query: `timestamp | tool | locator`).

- If a filter (`$ARGUMENTS`) was given, show only the lines that match it (by slug, domain, term, or date);
  otherwise show everything.
- Then summarize: total entries, distinct domains, and the date range covered. Group by domain if useful.
- Keep it concise — this is an audit/reproducibility view, not a research task.
