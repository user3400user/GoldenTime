#!/usr/bin/env bash
# PostToolUse hook (Write|Edit): if a report.md was written this session, remember it for the Stop-time
# citation gate. Never blocks.
INPUT=$(cat 2>/dev/null)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
BASE="${CLAUDE_PROJECT_DIR:-${CWD:-.}}"
SID=$(printf '%s' "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)
FP=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)

case "$FP" in
  */report.md|report.md)
    mkdir -p "$BASE/_sources" 2>/dev/null
    LIST="$BASE/_sources/.reports-$SID.list"
    grep -qxF -- "$FP" "$LIST" 2>/dev/null || echo "$FP" >> "$LIST"
    ;;
esac
exit 0
