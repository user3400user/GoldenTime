#!/usr/bin/env bash
# PreToolUse hook (Bash): cheap baseline safety. Deny obviously destructive commands (exit 2 = block).
INPUT=$(cat 2>/dev/null)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$CMD" ] && exit 0

# Destructive patterns (extended regex, matched case-insensitively):
#  rm -rf / -fr / -r…-f, fork bomb, mkfs, dd if=, writes to raw block devices,
#  SQL DROP/TRUNCATE, recursive chmod 777, git force-push, sudo rm.
DANGER='rm[[:space:]]+-[a-z]*r[a-z]*f|rm[[:space:]]+-[a-z]*f[a-z]*r|rm[[:space:]]+-r[[:space:]].*-f|rm[[:space:]]+-f[[:space:]].*-r|:[[:space:]]*\(\)[[:space:]]*\{|mkfs|[[:space:]]dd[[:space:]]+if=|>[[:space:]]*/dev/(sd|nvme|hd)|drop[[:space:]]+(table|database)|truncate[[:space:]]+table|chmod[[:space:]]+-r[[:space:]]+777|git[[:space:]]+push[[:space:]].*--force|sudo[[:space:]]+rm[[:space:]]'

if printf '%s' "$CMD" | grep -qiE "$DANGER"; then
  printf 'BLOCKED by guard-bash: this command matches a destructive pattern and was denied:\n  %s\nIf it is intentional and safe, run it yourself outside the agent.\n' "$CMD" >&2
  exit 2
fi
exit 0
