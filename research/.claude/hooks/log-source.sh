#!/usr/bin/env bash
# PostToolUse hook (WebFetch + tavily/firecrawl tools): append "timestamp | tool | locator" to the ledger.
# Deterministic source logging the model cannot forget. Never blocks.
INPUT=$(cat 2>/dev/null)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
BASE="${CLAUDE_PROJECT_DIR:-${CWD:-.}}"
LEDGER="$BASE/_sources/ledger.log"
mkdir -p "$BASE/_sources" 2>/dev/null

TOOL=$(printf '%s' "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)
# Pull whatever locator the tool used: a single url, a urls[] array, or a search query.
LOC=$(printf '%s' "$INPUT" | jq -r '
  .tool_input as $i
  | ( $i.url
      // ( ($i.urls // empty) | if type=="array" then join(", ") else tostring end )
      // $i.query
      // $i.search_query
      // empty )' 2>/dev/null)
[ -z "$LOC" ] && LOC="(no locator in tool_input)"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s | %s | %s\n' "$TS" "$TOOL" "$LOC" >> "$LEDGER" 2>/dev/null
exit 0
