# Notes — _selftest (HTTP/3 adoption 2025)

## Purpose
Environment self-test of the full pipeline using **built-in tools only** (no Tavily/Firecrawl keys).

## Scope & decomposition (Phase 1)
Question: "What happened with HTTP/3 adoption in 2025?"
Sub-questions:
- SQ1 — adoption magnitude/growth (traffic share vs. site-level support; geography).
- SQ2 — ecosystem developments (libraries, servers/CDNs, standards, performance).
Success criterion: each sub-question backed by ≥2 credible (ideally primary/measurement) sources, with
unverifiable items explicitly marked "not found". Stop when both SQs meet that bar.

## Search strategy & queries (Phase 2)
Delegated to two parallel research subagents (scout+read combined), each restricted to WebSearch+WebFetch:
- SQ1 agent — query themes: "HTTP/3 adoption 2025 percentage", "Cloudflare Radar 2025 HTTP/3 share",
  "W3Techs HTTP/3 usage", "Web Almanac 2025 HTTP/3".
- SQ2 agent — query themes: "HTTP/3 2025 developments", "OpenSSL 3.5 QUIC", "QUIC RFC 2025",
  "Multipath QUIC IETF 2025", "HTTP/3 performance 2025".

## Pipeline execution
- Phase 3–5: 2 parallel subagents returned distilled digests (raw pages stayed in subagent context). ✓ isolation
- Phase 6: synthesized by question structure (orchestrator).
- Phase 7: fact-checker subagent → verdict **fix-then-ship**; verified A–D,F,G; flagged Web Almanac figure as
  *mobile HTML*-specific (corrected), plus minor precision/currency notes on the Cloudflare baseline and W3Techs.

## Dropped / unverified
- "~35% global HTTP/3 (Oct 2025)" — search snippet only, no primary page → excluded.
- "QUIC higher CPU/syscall overhead" quantified claim — snippet only → excluded.
- Precise Jan-2025/Dec-2025 W3Techs endpoints — not retrievable from page text → "not found".
