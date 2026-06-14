# HTTP/3 Adoption in 2025 — What Changed
_Run: 2026-06-14 · Mode: deep-research · Slug: _selftest_
_(Environment self-test: built-in tools only, no API keys; ran the full pipeline incl. parallel subagents + adversarial verification.)_

## TL;DR
In 2025, HTTP/3 **traffic share plateaued** while its **footprint widened**. By Cloudflare's network,
HTTP/3 held ~21% of requests, essentially flat year-over-year [1][2]. By W3Techs' site-level survey, ~39–40%
of websites advertise HTTP/3 support — a *different metric* (sites vs. traffic), not a contradiction [4].
Adoption stayed **CDN-driven**, with origin servers near zero [3]. The headline 2025 ecosystem event was
**OpenSSL 3.5 LTS (8 Apr 2025) shipping server-side QUIC** [5], closing a long-standing gap, even as
language standard libraries and common servers stayed largely without built-in support [7]. Multipath QUIC
advanced at the IETF but did **not** become an RFC in 2025 [6].

## Key findings
- **Traffic share was roughly flat in 2025.** Cloudflare's 2025 review reports "21% of requests" over HTTP/3
  and that "HTTP/2 and HTTP/3 gained just fractions of a percentage point this year" [1]; the 2024 baseline
  was 20.5% [2]. (confidence: **high** — answers SQ1)
- **Site-level support is much higher than traffic share — a distinct metric.** W3Techs: "HTTP/3 is used by
  39.8% of all the websites" (site-advertised support, read June 2026; trends slightly over time) [4]. This
  measures sites advertising HTTP/3, not request volume, so the gap vs. the ~21% traffic figure is expected.
  (confidence: **medium** — answers SQ1)
- **Geographic spread widened even though the global share didn't.** Cloudflare: "15 countries/regions sent
  more than a third of requests over HTTP/3" in 2025, up from eight in 2024, led by Georgia (~38%) [1].
  (confidence: **high** — answers SQ1)
- **Adoption remained CDN-driven; origins near zero.** Web Almanac 2025: for **mobile HTML** requests, "CDNs
  saw 29% traffic from HTTP/3 with effectively 0% for origin traffic," and HTTP/1.1 on CDN HTML fell from 16%
  (2024) to 2% (2025) [3]. (confidence: **high**, with the scope precisely *mobile HTML* — answers SQ1/SQ2)
- **OpenSSL 3.5 LTS added server-side QUIC (8 Apr 2025).** The most consequential library milestone of the
  year: "OpenSSL 3.5 adds support for server-side QUIC," an LTS release supported to 2030 [5], corroborated by
  trade press [9]. (confidence: **high** — answers SQ2)
- **But broad open-source support stayed fragmented.** As of 2025, "neither QUIC nor HTTP/3 are included in
  the standard libraries of any major languages including Node.js, Go, Rust, Python or Ruby," and curl's
  support was "experimental and disabled in most distributions" [7]. (confidence: **medium/high** — answers SQ2)
- **Multipath QUIC advanced but is not yet an RFC.** It remained an IETF Internet-Draft through 2025 and sits
  in the RFC Editor queue as of mid-2026 [6]. (confidence: **high** — answers SQ2)

## Uncertainties & contradictions
- **Two metrics, often conflated.** "Traffic/request share" (~21%, Cloudflare/HTTP Archive) and "site-level
  support" (~40%, W3Techs) measure different things; both are vendor/aggregator vantage points, not a neutral
  internet census [1][3][4]. State which one you mean.
- **Precise endpoints not available.** Clean Jan-2025 vs Dec-2025 snapshots were not retrievable; Cloudflare
  reports full-year aggregates and W3Techs' page didn't expose dated 2025 monthlies — marked **not found**
  rather than estimated.
- **Verification fix applied:** an earlier draft stated the 29%/~0% split for "HTML requests" generally; the
  source scopes it to **mobile HTML** specifically [3] — corrected above.
- **Unverified claims dropped:** a "~35% global adoption (Oct 2025)" snippet and a quantified
  "QUIC CPU/syscall overhead" claim appeared only in search snippets and could not be confirmed on a primary
  page — excluded.

## Open questions / next steps (for a `/deepen _selftest` run)
- Pull exact Jan→Dec 2025 W3Techs monthlies from its historical chart/API for a precise growth delta.
- Get the **desktop** HTML HTTP/3 figure from Web Almanac to pair with the mobile number [3].
- Track Node.js 25's experimental QUIC (Oct 2025) toward stable, and curl/NGINX default-on timelines [7].

## Quellen
1. Cloudflare Radar — 2025 Year in Review — https://blog.cloudflare.com/radar-2025-year-in-review/ — abgerufen 2026-06-14 — primary/measurement, strong.
2. Cloudflare Radar — 2024 Year in Review (2024 baseline) — https://blog.cloudflare.com/radar-2024-year-in-review/ — abgerufen 2026-06-14 — primary/measurement, strong.
3. HTTP Archive — Web Almanac 2025, CDN chapter — https://almanac.httparchive.org/en/2025/cdn — abgerufen 2026-06-14 — primary/measurement, strong.
4. W3Techs — Usage statistics of HTTP/3 — https://w3techs.com/technologies/details/ce-http3 — abgerufen 2026-06-14 — site-level survey, moderate (live figure).
5. OpenSSL Project — OpenSSL 3.5 final release (server-side QUIC, LTS) — https://openssl-library.org/post/2025-04-08-openssl-35-final-release/ — abgerufen 2026-06-14 — official, strong.
6. IETF Datatracker — draft-ietf-quic-multipath — https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/ — abgerufen 2026-06-14 — official, strong.
7. HTTP Toolkit — "HTTP/3 & QUIC open-source support is nowhere" (Mar 2025) — https://httptoolkit.com/blog/http3-quic-open-source-support-nowhere/ — abgerufen 2026-06-14 — secondary, moderate.
8. DebugBear — HTTP/3 vs HTTP/2 performance (Jun 2025) — https://www.debugbear.com/blog/http3-vs-http2-performance — abgerufen 2026-06-14 — secondary, moderate.
9. Help Net Security — OpenSSL 3.5.0 released (corroboration of [5]) — https://www.helpnetsecurity.com/2025/04/09/openssl-3-5-0-released/ — abgerufen 2026-06-14 — secondary, moderate.
