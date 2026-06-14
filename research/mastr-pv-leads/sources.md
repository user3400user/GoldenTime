# Sources — mastr-pv-leads (run 2026-06-14)

Triaged sources actually deep-read this run. Credibility per source-triage rubric (primary > secondary > tertiary).

## Primary — official Bundesnetzagentur / MaStR
1. **BNetzA Webhilfe – Datenexport** — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/datenexport.html — format, size, daily 05:00 update, download constraints. (read)
2. **MaStR Datendownload (live)** — https://www.marktstammdatenregister.de/MaStR/Datendownload — current ZIP name/size, Stichtag exports, new Fassung seit 01.10.2025. (read)
3. **Dokumentation MaStR Gesamtdatenexport (PDF, Rev 26.1.2, 11.06.2026)** — https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf — KEYSTONE field-level data dictionary (EinheitenSolar, AnlagenEegSolar, EinheitenStromSpeicher, Lokationen). (read, 142 pp.)
10. **MaStR-Gesamtkonzept (PDF, 2018)** — https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Gesamtkonzept.pdf — Lokation/Speicher as grouping objects; data-responsibility split; Korrektur-caveat. (read)
11. **Registrierungshilfe Stromspeicher (PDF, 2021)** — https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/Registrierungshilfe%20Stromspeicher.pdf — storage = separate but co-registered unit. (read)
12. **MaStR Hilfe / FAQ** — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/faq.html — one-operator principle; storage separate. (read)
15. **MaStR-Newsletter 2019 (via Wayback)** — http://web.archive.org/web/20241127233330/https://www.marktstammdatenregister.de/MaStRHilfe/files/newsletter/MaStR-Newsletter%202019_1-7.pdf — registration-date "bug" + intended immutability + fix/reset. (read; live URL 404)
16. **MaStR Hilfe – Daten ändern** — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitDatenaenderung.html — correction vs change; Leistungshistorie. (read)
17. **MaStR Hilfe – Betreiberwechsel** — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitBetreiberwechsel.html — operator change keeps unit (no re-registration). (read)

## Primary — tool repos / package indexes (recency verified via API)
5. **open-mastr GitHub** — https://github.com/OpenEnergyPlatform/open-MaStR — commit 2026-06-09, 134★, active. **PyPI** https://pypi.org/project/open-mastr/ — 0.17.1 (2026-04-13).
6. **marktstammdatenregister-dev/mastr GitHub** — https://github.com/marktstammdatenregister-dev/mastr — Go CLI → SQLite; last commit 2023-11-23 (dormant), spec v23.1, 9★.
8. **bundesAPI/deutschland GitHub** — https://github.com/bundesAPI/deutschland — NO MaStR module (verified in README + src tree); active (commit 2025-08-17), 1406★.
9. **bundesAPI/marktstammdaten-api GitHub** — https://github.com/bundesAPI/marktstammdaten-api — OpenAPI spec of the web-JSON `GetErweiterteOeffentlicheEinheitStromerzeugung`; frozen 2022-07-17.

## Secondary — tool docs / academic / trade
4. **open-mastr docs** — https://open-mastr.readthedocs.io/en/latest/ (getting_started, advanced, dataset) — bulk vs SOAP, SQLite/Postgres, `data=[...]`, `to_csv`, Inbetriebnahmedatum(2007,7,20). (read)
7. **marktstammdatenregister.dev (Datasette)** — https://marktstammdatenregister.dev/ — SQL filtering over the export. (read)
13. **Figgener et al., Battery storage market review (status 2023), arXiv:2203.06762** — https://arxiv.org/pdf/2203.06762 — PV↔storage matching is statistical, ~75% co-install, ~9% storage under/late-registration. (read)
14. **Data Quality Analysis of the MaStR, arXiv:2304.10581** — https://arxiv.org/pdf/2304.10581 — operator-id completeness ~95–100%; PV coordinates ~95% missing; no clean storage coverage figure. (read)
18. **green-energy-law – Nachmeldefrist** — https://www.green-energy-law.com/?p=1016 — Bestandsanlagen back-registration deadline 31.01.2021. (read)
19. **Verbraucherzentrale – Ü20/EEG-Förderende** — https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/photovoltaik-was-tun-mit-der-ue20anlage-wenn-die-eegfoerderung-endet-50846 — 21. Betriebsjahr-Regel; 2006→31.12.2026. (read)

## Dropped / not deep-read (with reason)
- Zenodo open-MaStR mirrors (records 14843222, 8225106, 10200980) — dated redistributions; superseded by reading the live official export pages + open-mastr docs. Keep as fallback for record counts.
- Fraunhofer ISE storage study (landing page) — under-recording figure; the RWTH paper [13] already supplies a sourced ~9% under/late figure, so not separately read.
- Clearingstelle EEG / C.A.R.M.E.N. / Nürnberg / photovoltaik-bw — EEG 20-yr rule already nailed by Verbraucherzentrale [19].
- de.wikipedia MaStR, photovoltaikforum threads, topagrar (~150k figure) — tertiary/forum; not load-bearing. "~150.000 missed deadline" NOT used (unverified).
- Scout claim "~15% PV mislocated" — REJECTED: data-quality paper [14] shows PV coordinate errors 0.5–2% (present) + ~95% missing; the 21.3% figure is power-density plausibility, not location.

## Added in run N+1 (deepen, 2026-06-14)
20. **MaStR public web-JSON endpoint (own live measurement)** — https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetErweiterteOeffentlicheEinheitStromerzeugung — primary live data; counts + cohort + caps measured 2026-06-14 (queries in notes.md). (measured)
21. **MaStR filter-metadata endpoint** — .../GetFilterColumnsErweiterteOeffentlicheEinheitStromerzeugung — primary; column/catalog schema (Energieträger Speicher=2496 etc.). (read)
22. **MaStR-Nummernkonzept** (BNetzA; Clearingstelle copy, 2017) — https://www.clearingstelle-eeg-kwkg.de/sites/default/files/Nummernkonzept_MaStR_170301-1.pdf — primary; SEE/SEL/SSE/ABR/SNB prefixes + number structure. (read, text-extractable)
23. **§ 14 MaStRV** — https://www.buzer.de/14_MaStRV.htm (canonical: gesetze-im-internet.de/mastrv/__14.html) — primary law; Stromerzeugungslokation definition. (read; fact-checker confirmed verbatim vs gesetze-im-internet)

### N+1 dropped / not used
- Datasette `ds.marktstammdatenregister.dev` — intended for the co-location SQL but the host was DOWN (L7 unresponsive, 6 vantage points). G3 left unmeasured; SQL preserved in notes.md.
- BNetzA EE-Statistik PDF / netztransparenz EEG-Anlagenstammdaten — viable primary cohort sources, but the cohort was measured directly off the live register instead (more current, exact).
- de.wikipedia / docplayer mirror of Nummernkonzept — superseded by the Clearingstelle PDF + gesetze-im-internet cross-check.
