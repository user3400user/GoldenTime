# Research Environment — Operating Manual

This file is the **binding methodology** for this environment. It is not advice; it is how research is done
here. Follow it on every research task. The moat is this process, not the tools.

## Mission

Detect **B2B buy signals ("Kaufmomente")** — observable, public evidence that an organization is moving
toward a purchase — from openly accessible internet data, and produce defensible, cited findings.
Two modes share one pipeline:
- **Deep research** — one-off questions answered thoroughly with sources.
- **Monitoring** — repeated runs over *defined sources/entities* to extract fresh, structured signals.

A buy signal is anything that raises purchase intent or surfaces a trigger event, e.g.: new funding /
budget; leadership or role changes (esp. new VP/Director in the buying function); **hiring posts** that
imply an unmet need or a tool gap; tech-stack adds/removes; expansion (new market, office, headcount);
M&A; product launches; public RFPs/tenders; regulatory/compliance deadlines; partnership announcements;
earnings-call or 10-K language; review-site / community activity; conference participation.

## Non-negotiable operating rules

1. **No fabricated citations.** Every non-trivial factual claim traces to a source that is (a) actually read
   and (b) actually says it. When you cannot find support, write **"not found"** — never guess or paraphrase
   into a claim. Inventing or stretching a citation is the worst possible failure here.
2. **Cite sparingly and prefer primary sources.** Short, exact quotes only. Primary > secondary > tertiary.
3. **Carry a confidence level on every finding** (`high` / `medium` / `low`) with a one-clause reason.
4. **Keep the orchestrator context clean.** Heavy reading, crawling, and raw search dumps happen **inside
   subagents**. Subagents return distilled digests; raw pages never land in the main thread.
5. **Reproducibility.** Log every search query and every fetched URL (the ledger hook does the URLs/queries
   automatically; you record the queries you chose in `notes.md`).
6. **Separate evidence from inference.** Mark what is well-supported vs. speculative, and always state the
   strongest counter-position.
7. **Every `report.md` must end with a `## Quellen` section.** A Stop-hook blocks the turn if it is missing.

## The pipeline — 8 phases (run in order)

### 1. Scope & decomposition
Restate the question in your own words; resolve ambiguity (if a choice materially changes the answer, ask).
Define what a *complete* answer requires. Decompose into **3–7 sub-questions / claims**. Record what is
**already known** vs. **must be looked up**. Write explicit **success criteria** and a **stop condition**
(e.g., "every sub-question has ≥2 independent sources, or is marked not-found"). For monitoring runs, scope =
the entity list + source list + the time window since the last run.

### 2. Search strategy
For each sub-question, pick the tool deliberately:
- **Breadth / discovery / "what exists" / fresh facts** → `Tavily search` (relevance scoring, domain
  filters, recency) and the built-in **WebSearch**.
- **Depth / full text of a known-good page / monitoring a defined signal page** → **Firecrawl**
  (scrape / extract / crawl / structured extraction) or the built-in **WebFetch** for a single page.
- Prefer **primary sources** (company sites, filings, official blogs, job boards, the actual posting).
- **Log the queries** you run (into `notes.md`) so the run is reproducible. Use domain filters for
  monitoring (e.g., restrict to a company's careers page, a regulator, a specific board).

### 3. Collect in parallel
Launch **one `source-scout` subagent per sub-question** (in parallel). Each returns a **ranked candidate
list** — one line per source: `URL · type · why-relevant · credibility-flag`. **No raw dumps, no deep
reading.** This keeps breadth cheap and the main thread clean.

### 4. Source triage
Deduplicate. Score credibility with the **`source-triage` skill** rubric (primary > secondary > tertiary;
recency; author/institution; conflicts of interest; corroboration). Select the **top sources** for deep
reading; discard weak/redundant ones. State why anything strong was dropped.

### 5. Deep read
Dispatch **`deep-reader` subagents** onto the selected sources (parallel where independent). Each returns,
per source: key claims relevant to the question, supporting evidence, **short verbatim quotes with the
URL**, caveats/limitations, and a confidence level — and **which sub-question each finding answers**.
Digests only; the source text stays in the subagent.

### 6. Synthesis (orchestrator does this — never a subagent)
Integrate findings **by the structure of the question**, not source-by-source. For each sub-question note
where sources **agree, conflict, or are silent**. Separate well-evidenced from speculative. State the
**strongest counter-position** explicitly. For monitoring, assemble the **signal table** (schema below).

### 7. Adversarial verification (never skip)
Run the **`fact-checker` subagent** on the draft. It actively hunts counter-evidence and checks that **every
non-trivial claim has a real source that genuinely supports it** (no over-reach, no quote taken out of
context). It returns issues ranked by severity. Fix or downgrade every issue before output. **This phase is
what separates research from confident-sounding garbage.**

### 8. Output
Write the structured report (template below) to `research/<slug>/report.md`; keep working notes in
`research/<slug>/notes.md` and the per-investigation source list in `research/<slug>/sources.md`. The global
ledger `_sources/ledger.log` is appended automatically by a hook. Distil durable, reusable insights into
`knowledge/<topic>.md` and link them from `knowledge/index.md`.

## Subagent routing

| Use this agent  | When                                                              | Returns                              |
| :-------------- | :--------------------------------------------------------------- | :----------------------------------- |
| `source-scout`  | Phase 3 — find & rank candidate sources for a sub-question       | ranked URL list, 1 line each         |
| `deep-reader`   | Phase 5 — extract claims/quotes from a chosen URL                | per-source digest + quotes + confidence |
| `fact-checker`  | Phase 7 — red-team the draft for unsupported/over-reached claims | severity-ranked issue list           |

Run scouts and readers **in parallel** (one message, multiple Agent calls) when the items are independent.
Always delegate heavy reading; synthesis stays with you.

## Signal extraction schema (monitoring runs)

When the task is signal detection/monitoring, output findings as a table where each row is one signal:

`entity · signal_type · what_happened · evidence_url · date_observed · source_credibility · buy_relevance(why now) · confidence · suggested_action`

Deduplicate against prior runs (check the existing `report.md` and `knowledge/`); only surface **new or
changed** signals, and note the window covered.

## Report template (`research/<slug>/report.md`)

```
# <Title>
_Run: <date> · Mode: deep-research | monitoring · Slug: <slug>_

## TL;DR
<3–6 sentences: the direct answer / the signals that matter most.>

## Key findings
- <finding> — <short quote/evidence> [<source>] (confidence: high/med/low)
  (answers sub-question N)
...
## (Signals table — monitoring runs only)
<the schema above as a table>

## Uncertainties & contradictions
- <where sources disagree or are silent; open risks>

## Open questions / next steps
- <what a follow-up /deepen run should chase>

## Quellen
1. <Title> — <URL> — abgerufen <YYYY-MM-DD> — <primary/secondary/tertiary, credibility note>
...
```

The `## Quellen` section is **mandatory** (Stop-hook enforced) and lists every cited source with URL and
retrieval date.

## File & naming conventions
- `research/<slug>/` per investigation — `slug` is short, kebab-case, stable (reuse it for `/deepen`/`/verify`).
- `report.md` (the deliverable), `notes.md` (queries, scratch, dropped sources), `sources.md` (this run's sources).
- `knowledge/` — distilled cross-run truths (entities, source quality notes, recurring signal patterns);
  index every file in `knowledge/index.md`.
- `_sources/ledger.log` — append-only, hook-written URL/query + timestamp log (don't hand-edit).
- Secrets live only in `.env` (gitignored). Never write keys into any tracked file.

## Commands
- `/research <question>` — full pipeline (phases 1–8). Main entry point.
- `/deepen <slug>` — run N+1: load the existing report, find gaps/open questions, research only those, merge.
- `/verify <slug>` — run only the Phase-7 red-team pass on an existing report.
- `/sources [<slug>]` — print the source ledger (all, or filtered to a slug).

## Defaults & judgment
- Bias to **primary sources** and **recent** material; date-stamp everything.
- If keys for Tavily/Firecrawl are absent, the pipeline still runs on **WebSearch + WebFetch** — just with
  less reach; say so rather than pretending coverage was complete.
- Note any coverage limits explicitly (paywalls, blocked domains, "not found"). Silent gaps read as
  completeness — they are not.
