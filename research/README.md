# Research Environment — B2B Buy-Signal Detection

A lean, **methodology-first** Claude Code workspace for detecting B2B buy signals ("Kaufmomente") from
public web data — and for general deep research. The value is the **pipeline in [`CLAUDE.md`](CLAUDE.md)**,
not a pile of tools. Subagents keep raw search dumps out of the main context; hooks deterministically log
sources and enforce citations; findings accumulate in `knowledge/` across runs; secrets stay out of git.

## Works out of the box
Runs immediately on Claude Code's built-in **WebSearch + WebFetch** — no API keys required.
Adding keys for **Tavily** (search/discovery + extraction) and **Firecrawl** (deep scrape/crawl/structured
extraction) raises reach and quality but is optional.

## Quick start
```bash
# 1. (optional) enable the MCP research tools
cp .env.example .env            # then paste your TAVILY_API_KEY / FIRECRAWL_API_KEY
set -a; source .env; set +a     # Claude Code does NOT auto-load .env — export before launching

# 2. start Claude Code in this folder (loads .mcp.json, agents, skills, hooks)
claude

# 3. research
/research Which mid-market German SaaS firms showed hiring signals for RevOps tooling in 2025?
```

## Commands
| Command | What it does |
| :------ | :----------- |
| `/research <question>` | Full 8-phase pipeline → cited report under `research/<slug>/`. Main entry point. |
| `/deepen <slug>` | Run N+1 — load an existing report, research only its gaps/open questions, merge. |
| `/verify <slug>` | Adversarial red-team pass (Phase 7 only) on an existing report. |
| `/sources [slug]` | Print the append-only source ledger (all, or filtered). |

## The pipeline (see CLAUDE.md for the binding version)
`scope & decompose → search strategy → scout in parallel → triage → deep-read → synthesize → adversarial
verify → cited report`. Heavy reading always happens inside subagents; synthesis stays with the orchestrator.

## Where things land
```
research/<slug>/report.md   the deliverable (TL;DR · cited findings · uncertainties · ## Quellen)
research/<slug>/notes.md     queries run, scratch, dropped sources
research/<slug>/sources.md   this run's source list
knowledge/<topic>.md         distilled cross-run insights (indexed in knowledge/index.md)
_sources/ledger.log          append-only URL/query + timestamp log (written by a hook)
```

## What's enforced automatically (hooks → `.claude/settings.json`)
- **SessionStart** — prints the active project + a one-line methodology reminder so every session starts oriented.
- **PostToolUse** — every WebFetch / Tavily / Firecrawl call appends its URL or query + timestamp to `_sources/ledger.log`.
- **Stop** — if a `report.md` written this session lacks a `## Quellen` section, the turn is **blocked** until citations are added.
- **PreToolUse(Bash)** — blocks obviously destructive commands (`rm -rf`, `DROP TABLE`, …).

## Subagents (`.claude/agents/`) — minimal privilege, no file writes
- **source-scout** — finds & ranks candidate sources for a sub-question (read-only).
- **deep-reader** — extracts claims + short quotes from one URL.
- **fact-checker** — red-teams the draft for unsupported/over-reached claims.

## Tools (`.mcp.json`) — deliberately just two, plus the built-ins
- **Tavily** (`tavily-mcp`, `TAVILY_API_KEY`) — breadth/discovery + extraction with relevance scoring & domain filters.
- **Firecrawl** (`firecrawl-mcp`, `FIRECRAWL_API_KEY`) — deep scrape, crawl, and structured extraction of defined sources (ideal for monitoring).

## Security
`.env` is gitignored; never commit keys. The repo is git-managed so research history is versioned.

## Grow it with use
When a workflow repeats, capture it as another command or skill — let the environment grow from real usage
instead of being over-built up front.
