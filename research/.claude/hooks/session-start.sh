#!/usr/bin/env bash
# SessionStart hook — its stdout is injected into Claude's context to orient each session.
INPUT=$(cat 2>/dev/null)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
BASE="${CLAUDE_PROJECT_DIR:-${CWD:-$(pwd)}}"

echo "🔎 Research environment active — the methodology in CLAUDE.md is binding."
echo "Pipeline: scope → search → scout (parallel) → triage → deep-read → synthesize → fact-check (never skip) → cited report."
echo "Rules: no fabricated citations · confidence per finding · heavy reading stays in subagents · every report.md needs a ## Quellen section."
echo "Commands: /research <q> · /deepen <slug> · /verify <slug> · /sources [slug]"

if [ -d "$BASE/research" ]; then
  RECENT=$(find "$BASE/research" -maxdepth 1 -mindepth 1 -type d -printf '%f ' 2>/dev/null)
  [ -n "$RECENT" ] && echo "Investigations so far: $RECENT"
fi

if [ -s "$BASE/knowledge/index.md" ]; then
  echo "--- knowledge/index.md (head) ---"
  head -n 10 "$BASE/knowledge/index.md" 2>/dev/null
fi

if [ -s "$BASE/_sources/ledger.log" ]; then
  N=$(wc -l < "$BASE/_sources/ledger.log" 2>/dev/null | tr -d ' ')
  echo "Source ledger: ${N} entries logged (run /sources to inspect)."
fi
exit 0
