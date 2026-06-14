# HTTP/3 Adoption — state as of 2025 (distilled)

_From `research/_selftest/report.md` (2026-06-14). Reusable facts + vetted sources._

- **Two metrics, never conflate:** request/traffic share (~21%, Cloudflare/HTTP Archive) vs. site-level
  advertised support (~39–40%, W3Techs). Always say which.
- 2025 traffic share was **roughly flat** YoY (~20.5% → 21%); adoption is **CDN-driven**, origins ~0%.
- Key 2025 ecosystem event: **OpenSSL 3.5 LTS (8 Apr 2025) added server-side QUIC**; language stdlibs/servers
  still largely lacked built-in support; Multipath QUIC still a draft (not an RFC).

## Vetted measurement sources for web-protocol adoption (reuse these)
- Cloudflare Radar Year-in-Review — traffic share, by-country (strong, primary vantage).
- HTTP Archive / Web Almanac — by CDN vs. origin, mobile vs. desktop (strong; check exact scope of each figure).
- W3Techs — site-level support survey (moderate; live figure, pin the access date).
- IETF Datatracker — authoritative for RFC/draft status.
