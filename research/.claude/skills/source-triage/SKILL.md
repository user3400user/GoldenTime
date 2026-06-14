---
name: source-triage
description: >-
  Credibility and triage rubric for evaluating, deduplicating, and ranking research sources. Use when
  assessing whether a source is trustworthy, deciding which sources to deep-read, weighing primary vs.
  secondary vs. tertiary, or judging recency, author authority, bias, conflicts of interest, and
  corroboration — including buy-signal sources (job posts, filings, press releases, tenders).
---

# Source Triage Rubric (Phase 4)

Use this to turn a raw candidate list into a defensible shortlist for deep reading.

## 1. Tier the source
- **Primary** — the original artifact: regulatory filings, official company pages/press releases, the actual
  job posting or tender, datasets, the law/standard itself, first-hand statements. **Prefer these.**
- **Secondary** — reputable outlets/analysts summarizing primary material with named authorship.
- **Tertiary** — aggregators, wikis, listicles, SEO/affiliate content, AI-generated filler. **Treat as leads,
  not evidence**; trace them back to a primary source.

## 2. Score each source on these dimensions
- **Authority** — identifiable author/institution with relevant standing and track record.
- **Recency** — date vs. the question's time-sensitivity. For buy signals, freshness *is* the signal.
- **Independence** — conflicts of interest: is the source selling the thing, an affiliate, or pure PR?
- **Directness** — first-hand vs. hearsay/"reportedly".
- **Verifiability** — does it link to evidence, show methodology, and is the claim checkable?
- **Corroboration** — can an independent source confirm it?

Assign each: **credibility = strong | moderate | weak**, plus its tier and date.

## 3. Buy-signal specifics
- Prefer the **actual artifact** (the posting/filing/release) over coverage *about* it.
- Check dates ruthlessly — beware **recycled/evergreen job posts** and re-published wire stories presented as new.
- Confirm **entity identity**: right legal entity, right division/region, not a same-name lookalike.
- A signal needs a **trigger + a date + attribution**; without all three, downgrade it.

## 4. Triage procedure
1. **Deduplicate** — by URL *and* by underlying source (the same wire story republished across sites counts once).
2. **Tag** each survivor: tier · credibility · date.
3. **Drop** weak and redundant items; note briefly why anything strong was dropped.
4. **Select a diverse top set** — independent origins, not five copies of one story.
5. For any **strong claim**, require **≥2 independent sources** or explicitly mark it single-source.

## 5. Red flags (downgrade or drop)
No date · no author · domain/entity mismatch · circular sourcing · content farm · undisclosed sponsorship ·
screenshots without origin · numbers with no methodology · claims that only appear on one low-authority page.

## Output
A ranked shortlist — each line: `URL · tier · credibility · date · keep/drop + one-line rationale` — and a
note on which sub-question(s) the kept sources serve.
