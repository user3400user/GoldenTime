#!/usr/bin/env bash
# Stop hook — citation gate. If a report.md written this session lacks a "## Quellen" section,
# block the turn (exit 2) so the model must add the sources before finishing.
INPUT=$(cat 2>/dev/null)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
BASE="${CLAUDE_PROJECT_DIR:-${CWD:-.}}"
SID=$(printf '%s' "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)
LIST="$BASE/_sources/.reports-$SID.list"

[ -s "$LIST" ] || exit 0   # no report written this session → nothing to enforce

MISSING=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue
  if ! grep -qiE '^[[:space:]]*#{1,6}[[:space:]]*Quellen' "$f"; then
    MISSING="$MISSING\n  - $f"
  fi
done < "$LIST"

if [ -n "$MISSING" ]; then
  printf 'BLOCKED (citation gate): a report.md written this session is missing its "## Quellen" section:%b\n' "$MISSING" >&2
  printf 'Add a "## Quellen" heading listing every cited source (Title — URL — retrieved date), then finish.\n' >&2
  exit 2
fi
exit 0
