"""
CLI der MaStR-Pipeline.  Aufruf aus 02_Daten/:

  python -m pipeline.cli inspect                  # reale Tabellen/Spalten der DB prüfen
  python -m pipeline.cli build-db                 # Gesamtexport via open-mastr -> SQLite (~3 GB)
  python -m pipeline.cli leads --plz 48,59         # Region -> klassifizierte Leads (ABR-Check)
  python -m pipeline.cli leads --bundesland Bayern --limit 50

`inspect` zuerst laufen lassen, um die echten open-mastr-Namen gegen config.py zu verifizieren.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import re
import secrets
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from . import config, deliver, export_adapter
from . import db as dbmod
from .control import config_store as cs
from .control import metrics as metricsmod
from .control import state as statemod
from .enrich import mastr_resolve
from .ledger import ledger as ledgermod
from .normalize import iter_leads
from .qualify import hierarchy, qa_gate
from .signal import SignalRecord, mastr_detail_url, mastr_suchlink
from .snapshot import store as snapstore
from .speicher_check import GEPLANT, build_storage_index
from .triggers import cohort, diff_based

log = logging.getLogger("pipeline")


def _slug(s: str) -> str:
    s = (s or "").lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "region"


def _plz_prefixes(roh: str) -> tuple[str, ...]:
    """Ad-hoc ``--plz`` parsen UND die Ziffern-Invariante erzwingen. Damit ist der escapefreie SQL-
    LIKE-Filter sicher (PLZ-Präfix kann kein %/_ enthalten) — die Gegen-Stelle ist config_store._validate."""
    prefixes = tuple(p.strip() for p in roh.split(",") if p.strip())
    bad = [p for p in prefixes if not p.isdigit()]
    if bad:
        raise SystemExit(f"--plz: PLZ-Präfixe müssen reine Ziffern sein, ungültig: {bad}")
    return prefixes


def _write_csv(path: Path, leads: list[dict]) -> None:
    fields = [k for k in leads[0] if k != "flags"] + ["flags"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for lead in leads:
            row = dict(lead)
            row["flags"] = "|".join(lead["flags"])
            w.writerow(row)


def _write_signals_csv(path: Path, records: list) -> None:
    """SignalRecords im Liefer-Schema (record.CSV_FIELDS) als CSV schreiben."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(SignalRecord.CSV_FIELDS))
        w.writeheader()
        for rec in records:
            w.writerow(rec.to_row())


def cmd_inspect(args: argparse.Namespace) -> int:
    con = dbmod.connect(args.db)
    tables = dbmod.list_tables(con)
    print(f"DB: {args.db or config.DEFAULT_DB_PATH}")
    print(f"{len(tables)} Tabellen gefunden.")
    for logical in ("solar", "storage", "location", "market"):
        try:
            t = dbmod.resolve_table(con, logical)
        except LookupError as e:
            print(f"  [{logical:8}] -> NICHT GEFUNDEN: {e}")
            continue
        cols = dbmod.table_columns(con, t)
        cmap = dbmod.column_map(cols, *config.COL.keys())
        found = {k: v for k, v in cmap.items() if v}
        missing = [k for k, v in cmap.items() if not v]
        print(f"  [{logical:8}] -> {t}  ({len(cols)} Spalten)")
        print(f"      erkannt: {found}")
        if missing:
            print(f"      fehlend: {missing}")
    con.close()
    return 0


def cmd_build_db(args: argparse.Namespace) -> int:
    data = tuple(args.data) if args.data else config.OPENMASTR_DATA
    out = export_adapter.build_db(data=data)
    print(f"OK -> {out}")
    return 0


def cmd_leads(args: argparse.Namespace) -> int:
    con = dbmod.connect(args.db)
    index = build_storage_index(con)
    prefixes = _plz_prefixes(args.plz) if args.plz else ()
    leads = list(
        iter_leads(con, index, plz_prefixes=prefixes, bundesland=args.bundesland, limit=args.limit)
    )
    con.close()

    deliver = [x for x in leads if x["ausschluss_grund"] is None]
    excluded = [x for x in leads if x["ausschluss_grund"] is not None]
    # e.K./natürliche Person auch aus dem (Legacy-)leads-CSV halten (§0/I7), solange nicht freigegeben.
    # Dict-Pfad ohne SignalRecord: am e.K.-Namensmuster bzw. einem NATUERLICHE/PRIVATPERSON-Flag.
    if not cs.load().natuerliche_personen_freigegeben():
        nat = [x for x in deliver
               if hierarchy.ist_natuerliche_person_name(x.get("betreiber"))
               or any("NATUERLICHE" in f or "PRIVATPERSON" in f for f in (x.get("flags") or ()))]
        if nat:
            nat_ids = {id(x) for x in nat}
            deliver = [x for x in deliver if id(x) not in nat_ids]
            print(f"  e.K./nat. Person aus Lieferliste gefiltert (§0): {len(nat)}")
    deliver.sort(key=lambda x: (x["reg_datum"] or "", x["kwp"]), reverse=True)  # frischeste oben

    region = args.region_name or (("PLZ " + "/".join(prefixes)) if prefixes else (args.bundesland or "alle"))
    heute = dt.date.today().isoformat()
    out = Path(args.out) if args.out else Path(f"leads_{_slug(region)}_{heute}.csv")

    print(f"Region {region}: {len(leads)} klassifiziert · {len(deliver)} lieferbar · "
          f"{len(excluded)} ausgeschlossen (Speicher am Standort gemeldet).")
    print(f"  Trigger (lieferbar): {dict(Counter(x['trigger_typ'] for x in deliver))}")
    print(f"  Speicher-Status (alle): {dict(Counter(x['speicher_status'] for x in leads))}")
    if deliver:
        _write_csv(out, deliver)
        print(f"  -> {out}")
        for x in deliver[:12]:
            warn = "  ⚠FRISCHE" if not x["frische_valide"] else ""
            print(f"    {(x['betreiber'] or '')[:32]:32s} {x['kwp']:>6.0f} kWp  {x['plz'] or '?????'} "
                  f"{(x['ort'] or '')[:14]:14s} {x['trigger_typ']}  {x['speicher_label']}{warn}")
    else:
        print("  Keine lieferbaren Leads für diese Region (Filter/Region prüfen).")
    return 0


# --- Vollpaket-Kommandos (Komponenten 2-8) ---------------------------------

def _resolve_targets(store, args) -> list[tuple[str, str, tuple[str, ...]]]:
    """(gebiet_id, name, plz_prefixes) aus --plz (ad-hoc), --gebiet oder allen aktiven Gebieten."""
    if args.plz:
        prefixes = _plz_prefixes(args.plz)
        return [("adhoc", args.region_name or ("PLZ " + "/".join(prefixes)), prefixes)]
    if args.gebiet:
        g = store.gebiet(args.gebiet)
        if not g:
            raise SystemExit(f"Gebiet '{args.gebiet}' nicht im Config-Store ({config.CONFIG_STORE_PATH}).")
        return [(g["id"], g.get("name", g["id"]), tuple(g.get("plz_prefixes", ())))]
    return [(g["id"], g.get("name", g["id"]), tuple(g.get("plz_prefixes", ())))
            for g in store.active_gebiete()]


def cmd_signals(args: argparse.Namespace) -> int:
    """Post-EEG-Signal-Shipper (T2): cohort -> qualify (market-Join) -> QA-Gate -> SignalRecord-CSV."""
    store = cs.load()
    nat_frei = store.natuerliche_personen_freigegeben()   # §0/I7: e.K./nat. Person liefern? Default aus.
    con = dbmod.connect(args.db)
    qa_con = statemod.connect()
    woche = metricsmod.iso_woche()
    heute = dt.date.today().isoformat()
    targets = _resolve_targets(store, args)
    multi = len(targets) > 1
    gesamt = 0
    try:
        index = build_storage_index(con)
        for gid, name, prefixes in targets:
            aktiv = (store.effective_trigger(gid, cohort.TRIGGER_KEY) if gid != "adhoc"
                     else store.is_trigger_enabled(cohort.TRIGGER_KEY))
            if not aktiv:
                print(f"Gebiet {name}: Trigger T2 inaktiv (Config-Store) — übersprungen.")
                continue

            records = list(cohort.cohort_signals(con, index, plz_prefixes=prefixes, region=name))
            hierarchy.enrich_and_qualify(records, con)
            for rec in records:
                qa_gate.apply_qa(rec, qa_con)

            # Geplanter Speicher -> eigener Bucket (nicht heiß); aus allen anderen Buckets raushalten.
            geplant = [r for r in records if r.speicher_status == GEPLANT]
            rest = [r for r in records if r.speicher_status != GEPLANT]
            # Lieferbar = QA-ok UND mit Namen (ohne Firmenname kein B2B-Kontakt -> namenlos-Bucket).
            deliver = [r for r in rest if r.qa_status in (qa_gate.AUTO_OK, qa_gate.APPROVED) and r.entity]
            namenlos = [r for r in rest if not r.entity]
            pending = [r for r in rest if r.qa_status == qa_gate.PENDING]
            rejected = [r for r in rest if r.qa_status == qa_gate.REJECTED]
            # e.K./natürliche Person HART aus der Lieferliste (§0/I7) über den gemeinsamen Choke-Point —
            # kein Funnel darf die Rechts-Invariante umgehen (S0: Filter in ALLEN Funneln).
            deliver, gesperrt = hierarchy.partition_natuerliche(deliver, nat_frei)
            # Monitoring-Metrik = lieferbare Dichte NACH e.K.-Filter, aber VOR käuferspezifischem Ledger-
            # Dedup, damit sie mit deliver.run_region/_record_metrics konsistent ist (Bug-Hunt: sonst
            # clobbern sich die 'lieferbar'/'dv_flag'-Werte je nachdem, welcher Befehl zuletzt lief).
            roh_lieferbar, roh_dv = len(deliver), sum(r.dv_flag for r in deliver)
            if args.kaeufer and args.funktion:   # optionales Ledger-Gate (Exklusivität+Dedupe, read-only Vorschau)
                deliver = ledgermod.filter_deliverable(qa_con, deliver, args.kaeufer, args.funktion, gid, "T2")
            deliver.sort(key=lambda r: (r.dv_flag, r.kwp or 0), reverse=True)  # DV + größte zuerst

            # Evidenz-Direktlinks (SEE -> interne MaStR-ID) für die LIEFERBAREN auflösen, gecacht in
            # pipeline_state.db. Offline/Fehler -> Records behalten den robusten Such-Link (kein Crash).
            aufgeloest = 0
            if not args.offline and deliver:
                aufgeloest = mastr_resolve.EvidenzResolver(cache_con=qa_con).resolve_records(deliver)

            for metrik, wert in (("signale", len(records)), ("lieferbar", roh_lieferbar),
                                 ("pending_qa", len(pending)), ("namenlos", len(namenlos)),
                                 ("nat_gesperrt", len(gesperrt)),
                                 ("speicher_geplant", len(geplant)),
                                 ("dv_flag", roh_dv)):
                metricsmod.record(qa_con, metrik=metrik, wert=wert, woche=woche, gebiet=gid, trigger="T2")

            print(f"Gebiet {name}: {len(records)} T2-Signale · {len(deliver)} lieferbar · "
                  f"{len(pending)} QA-pending · {len(namenlos)} namenlos · {len(gesperrt)} e.K.-gesperrt · "
                  f"{len(geplant)} Speicher-geplant · {len(rejected)} rejected · "
                  f"DV-Flag {sum(r.dv_flag for r in deliver)}.")
            if deliver and not args.offline:
                print(f"  Evidenz-Direktlinks: {aufgeloest}/{len(deliver)} aufgelöst "
                      f"(Rest: robuster Such-Link + SEE-Prüf-Nummer).")
            if deliver:
                if args.out:
                    base = Path(args.out)
                    out = base.with_stem(f"{base.stem}_{_slug(name)}") if multi else base
                else:
                    out = Path(f"signals_{_slug(name)}_{heute}.csv")
                _write_signals_csv(out, deliver)
                print(f"  -> {out}")
                for r in deliver[:10]:
                    dv = " DV" if r.dv_flag else "   "
                    print(f"    {(r.entity or '—')[:30]:30s} {(r.kwp or 0):>6.0f} kWp  {r.plz or '?????'} "
                          f"{(r.ort or '')[:14]:14s} K={r.konfidenz}{dv} {r.speicher_label}")
            gesamt += len(deliver)
    finally:
        con.close()
        qa_con.close()
    print(f"Σ lieferbar (alle Gebiete): {gesamt}")
    return 0


def cmd_qa(args: argparse.Namespace) -> int:
    """Mensch-QA-Gate (D5): Queue ansehen / freigeben / ablehnen / je Betreiber sammeln."""
    con = statemod.connect()
    if args.action == "list":
        rows = qa_gate.list_queue(con, status=(None if args.status == "alle" else args.status),
                                  limit=args.limit)
        print(f"QA-Queue ({args.status}): {len(rows)} Einträge")
        # Evidenz-Links klickbar machen (R0, demo-kritisch): der Gründer läuft GENAU diesen Pfad vor
        # dem Essen ab. Default = nur Cache (instant); --online löst fehlende SEE -> interne MaStR-ID
        # live auf (langsamer bei kaltem Cache, daher opt-in). Cache-Miss -> robuster Such-Link
        # (HTTP 200) statt totem SEE-Direktlink ('IndexOeffentlich/SEE…' liefert HTTP 400).
        resolver = mastr_resolve.EvidenzResolver(cache_con=con) if args.online else None
        for r in rows:
            see = r["einheit_mastr_nr"]
            if resolver is not None:
                detail_id = resolver.resolve_id(see)            # online auflösen (+ cachen)
            else:
                hit = con.execute("SELECT detail_id FROM mastr_url_cache WHERE einheit_mastr_nr = ?",
                                  (see,)).fetchone()
                detail_id = hit[0] if hit else None             # nur Cache; Miss -> Such-Link
            url = mastr_detail_url(detail_id) if detail_id else mastr_suchlink(see)
            print(f"  {see:16s} {r['status']:9s} ABR={r['betreiber_mastr_nr'] or '—':16s} "
                  f"flags={r['flags_at_review'] or ''}  {url}")
    elif args.action == "suggest":
        # Vor-dem-Essen-Helfer: Pending nach Flag-Muster GRUPPIEREN + je Fall einen Approve/Reject-
        # VORSCHLAG + Copy-Paste-Kommando ausgeben. NICHTS wird automatisch entschieden — der Mensch
        # setzt 'qa approve/reject/approve-abr' bewusst ab. Links wie 'qa list' (Default Cache, --online live).
        rows = qa_gate.list_queue(con, status=qa_gate.PENDING, limit=args.limit)
        hist = Counter(r["flags_at_review"] or "(kein flag)" for r in rows)
        print(f"QA-Vorschlag (pending): {len(rows)} Fälle · NICHTS wird automatisch entschieden.")
        for muster, n in hist.most_common():
            empf, _ = qa_gate.suggest_for_flags(None if muster == "(kein flag)" else muster)
            print(f"  {n:4d}×  {muster:42s} -> {empf}")
        resolver = mastr_resolve.EvidenzResolver(cache_con=con) if args.online else None
        aktuelles_muster = object()
        for r in sorted(rows, key=lambda r: (r["flags_at_review"] or "", r["einheit_mastr_nr"])):
            muster = r["flags_at_review"] or "(kein flag)"
            empf, grund = qa_gate.suggest_for_flags(r["flags_at_review"])
            if muster != aktuelles_muster:
                print(f"\n=== {muster}  [{empf}] ===")
                aktuelles_muster = muster
            see = r["einheit_mastr_nr"]
            if resolver is not None:
                detail_id = resolver.resolve_id(see)
            else:
                hit = con.execute("SELECT detail_id FROM mastr_url_cache WHERE einheit_mastr_nr = ?",
                                  (see,)).fetchone()
                detail_id = hit[0] if hit else None
            url = mastr_detail_url(detail_id) if detail_id else mastr_suchlink(see)
            if empf == qa_gate.REC_REJECT:
                cmd = f"qa reject {see} --grund {grund}"
            elif empf == qa_gate.REC_APPROVE:
                cmd = f"qa approve {see}"
            else:
                cmd = f"# {see} prüfen, dann qa approve/reject"
            print(f"  {see:16s} ABR={r['betreiber_mastr_nr'] or '—':16s} {empf:16s} {url}")
            print(f"      -> {cmd}")
    elif args.action == "approve":
        n = qa_gate.approve(con, args.einheit, grund=args.grund, notiz=args.notiz)
        print(f"approved: {n} Einheit(en).")
    elif args.action == "reject":
        n = qa_gate.reject(con, args.einheit, grund=args.grund or "manuell abgelehnt", notiz=args.notiz)
        print(f"rejected: {n} Einheit(en).")
    elif args.action == "approve-abr":
        n = qa_gate.approve_abr(con, args.einheit, grund=args.grund, notiz=args.notiz)
        print(f"approve-abr {args.einheit}: {n} Einheit(en) freigegeben.")
    con.close()
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Schreibe einen schlanken, dated Wochen-Snapshot (D2) + optionales Prune."""
    con = dbmod.connect(args.db)
    out = snapstore.write_snapshot(con, datum=args.datum or None)
    con.close()
    print(f"OK -> {out}")
    if args.prune:
        geloescht = snapstore.prune()
        print(f"Prune: {len(geloescht)} alte Snapshots gelöscht.")
    metas = snapstore.list_snapshots()
    print(f"Vorhandene Snapshots: {[m.datum for m in metas]}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Wochen-Diff der zwei jüngsten Snapshots -> diff-basierte Signale (T1/T4 scharf; T5/T6/PV aus).

    Peak-RAM: ``diff`` lädt beide Snapshots als kompakte Tupel-Dicts (nur die 6 Diff-Felder) — ~4 GB RSS
    bei ~8,8 Mio Einheiten (Zweit-Review: von ~12 GB gesenkt). Auf dem ZBook unkritisch; ``weekly`` läuft
    build-db und diff sequenziell, der Export-Speicher ist beim Diff also schon frei.
    """
    paar = snapstore.latest_two()
    if paar is None:
        print("Weniger als 2 Snapshots vorhanden — erst zweimal `snapshot` (in verschiedenen Wochen) laufen.")
        return 1
    prev, curr = paar
    store = cs.load()
    # Region aus dem Gebiet auflösen (Befund 14: Diff filtert nach PLZ, nicht nur Trigger-Schalter).
    prefixes: tuple[str, ...] = ()
    if args.gebiet:
        g = store.gebiet(args.gebiet)
        if not g:
            raise SystemExit(f"Gebiet '{args.gebiet}' nicht im Config-Store ({config.CONFIG_STORE_PATH}).")
        prefixes = tuple(g.get("plz_prefixes", ()))
    con = dbmod.connect(args.db) if not args.no_enrich else None
    qa_con = statemod.connect()
    try:
        records = list(diff_based.diff_based_signals(
            prev, curr, store, gebiet_id=args.gebiet or None, plz_prefixes=prefixes, con=con))
        # Befund 12: Diff-Pfad durch Qualifizierer + QA-Gate (wie cmd_signals), nicht ungefiltert liefern.
        if con:
            hierarchy.enrich_and_qualify(records, con)
            for r in records:
                qa_gate.apply_qa(r, qa_con)
        deliver = [r for r in records if r.qa_status in (qa_gate.AUTO_OK, qa_gate.APPROVED) and r.entity]
        # e.K./natürliche Person HART aus dem FLUSS-Liefer-CSV (§0/I7) — derselbe Choke-Point wie die
        # anderen Funnel (Refute HIGH: cmd_diff schrieb e.K. ungefiltert ins kundenfähige diff_signals_*.csv;
        # latent bis zum 2. Snapshot, dann scharf). nat_frei aus dem Config-Store (Default aus).
        deliver, nat_gesperrt = hierarchy.partition_natuerliche(deliver, store.natuerliche_personen_freigegeben())
        pending = [r for r in records if r.qa_status == qa_gate.PENDING]
        namenlos = [r for r in records if not r.entity]
    finally:
        if con:
            con.close()
        qa_con.close()
    print(f"Diff {prev.name} -> {curr.name}: {len(records)} Signale "
          f"(Trigger: {dict(Counter(r.trigger_typ for r in records))}) · {len(deliver)} lieferbar · "
          f"{len(nat_gesperrt)} e.K.-gesperrt · {len(pending)} QA-pending · {len(namenlos)} namenlos.")
    if deliver:
        out = Path(args.out) if args.out else Path(f"diff_signals_{dt.date.today().isoformat()}.csv")
        _write_signals_csv(out, deliver)
        print(f"  -> {out}")
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    """Exklusivitäts-Ledger (D6): reservieren / freigeben / Übersicht."""
    con = statemod.connect()
    if args.action == "overview":
        rows = ledgermod.overview(con)
        print(f"Exklusivität ({len(rows)} aktive Reservierungen):")
        for r in rows:
            print(f"  {r['funktion']:22s} {r['gebiet']:14s} {r['trigger']:6s} -> {r['kaeufer']}  "
                  f"({r['reserviert_am']})")
    elif args.action == "reserve":
        ok = ledgermod.reserve(con, args.funktion, args.gebiet, args.trigger, args.kaeufer)
        print(f"reserve {args.funktion}×{args.gebiet}×{args.trigger} -> {args.kaeufer}: "
              f"{'OK' if ok else 'BLOCKIERT (anderer Käufer hält den Schlüssel)'}.")
    elif args.action == "release":
        ledgermod.release(con, args.funktion, args.gebiet, args.trigger)
        print(f"freigegeben: {args.funktion}×{args.gebiet}×{args.trigger}.")
    con.close()
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Admin-Dashboard starten (stdlib http.server, localhost) — Gebiete/Trigger/Module schalten + Monitoring."""
    from .dashboard import app as dashapp
    print(f"Admin-Dashboard: http://127.0.0.1:{args.port}/  (Strg+C zum Beenden)")
    dashapp.serve(port=args.port)
    return 0


def cmd_evidenz_check(args: argparse.Namespace) -> int:
    """Stichproben-Check der Evidenz-URLs auf Erreichbarkeit (HTTP 200) — TEIL-5-Validierung."""
    store = cs.load()
    if args.plz:
        prefixes = _plz_prefixes(args.plz)
    elif args.gebiet and (g := store.gebiet(args.gebiet)):
        prefixes = tuple(g.get("plz_prefixes", ()))
    else:
        raise SystemExit("Bitte --gebiet <id> oder --plz <präfixe> angeben.")
    con = dbmod.connect(args.db)
    qa_con = statemod.connect()
    try:
        index = build_storage_index(con)
        recs = list(cohort.cohort_signals(con, index, plz_prefixes=prefixes, region="check"))
        hierarchy.enrich_and_qualify(recs, con)
        for r in recs:
            qa_gate.apply_qa(r, qa_con)
        deliver = [r for r in recs if r.qa_status in (qa_gate.AUTO_OK, qa_gate.APPROVED) and r.entity]
        mastr_resolve.EvidenzResolver(cache_con=qa_con).resolve_records(deliver)
        res = mastr_resolve.validate_urls(deliver, sample=args.sample)
    finally:
        con.close()
        qa_con.close()
    print(f"Evidenz-URL-Check: {res['ok']}/{res['geprueft']} erreichbar (HTTP 200), {res['fehler']} Fehler.")
    if res.get("hinweis"):
        print("  " + res["hinweis"])
    for see, direct, url, code in res["details"]:
        print(f"  {'direkt' if direct else 'such  '} HTTP {code}  {see}  {url}")
    return 0 if res["fehler"] == 0 else 1


def _commit_guard(kaeufer: str, funktion: str) -> str | None:
    """Darf ein echtes ``--commit`` (reserve + record_delivery ins Live-Ledger) laufen?

    Gibt eine Fehlermeldung zurück (→ abbrechen) oder ``None`` (→ erlaubt). Zwei harte Gates:
      * Käufer+Funktion Pflicht — eine echte Lieferung ist käufer-/funktionsgebunden.
      * ``config.LIVE_DELIVERY_ENABLED`` muss AN sein (§0/I8) — sonst ist die echte Lieferung an einen
        zahlenden Kunden bis zur anwaltlichen Art-6(1)(f)-Freigabe gesperrt; Demos nutzen den Dry-Run.
    """
    if not (kaeufer and funktion):
        return "--commit verlangt --kaeufer UND --funktion (echte Lieferung ist käufer-/funktionsgebunden)."
    if not config.LIVE_DELIVERY_ENABLED:
        return ("--commit GESPERRT: LIVE_DELIVERY_ENABLED ist aus (§0). Echte Lieferung an einen zahlenden "
                "Kunden ist bis zur anwaltlichen Art-6(1)(f)-Freigabe verboten; ein Mensch setzt den Schalter. "
                "Für Demos den Dry-Run nutzen (ohne --commit) — er füllt das Live-Ledger nie.")
    return None


def _commit_buckets(qa_con, buckets: list, kaeufer: str, funktion: str) -> int:
    """Backup → atomares reserve+record_delivery je Bucket (``commit_delivery``, BEGIN IMMEDIATE).

    Gibt Σ NEU protokollierter Einheiten zurück. NUR nach bestandenem ``_commit_guard`` aufrufen
    (LIVE_DELIVERY_ENABLED an). Backup VOR dem ersten Schreibvorgang (Sprint-Zwang 6, Ledger nicht
    regenerierbar).
    """
    bpath = statemod.backup_state_db()
    print(f"  Backup pipeline_state.db -> {bpath}")
    gesamt = 0
    for b in buckets:
        if not b.gebiet_id:
            continue
        neu = ledgermod.commit_delivery(qa_con, b.lieferbar, kaeufer, funktion, b.gebiet_id, b.ledger_trigger)
        print(f"  COMMIT {b.region}: {len(neu)} Einheiten neu protokolliert · Exklusivität "
              f"{funktion}×{b.gebiet_id}×{b.ledger_trigger} reserviert für {kaeufer}.")
        gesamt += len(neu)
    # WICHTIG (Refute HIGH): es gibt kein SMTP — --commit FÜHRT DEN VERSAND NICHT DURCH. Es protokolliert
    # die Leads als 'geliefert' (nicht regenerierbarer Ledger). Der Versand des Liefer-Pakets (oben
    # geschriebene CSV+Mail) ist ein MANUELLER Schritt; --commit ist die bewusste Post-Versand-Bestätigung.
    print(f"  ⚠ --commit hat {gesamt} Einheiten als GELIEFERT an '{kaeufer}' protokolliert (Dedupe-/"
          "Exklusiv-Sperre dauerhaft). KEIN automatischer Versand — stelle sicher, dass das Paket "
          "tatsächlich an den Käufer versendet wurde/wird, sonst weicht der Ledger-Stand vom realen Versand ab.")
    return gesamt


def cmd_liefern(args: argparse.Namespace) -> int:
    """Liefer-Paket für ein Gebiet: getrennte Bucket-CSVs (lieferbar/QA/namenlos) + Liefer-Mail (TEIL 5).

    Default = Dry-Run (read-only Vorschau, 0 Ledger-Zeilen). Mit ``--commit`` (+ --kaeufer/--funktion,
    nur bei ``LIVE_DELIVERY_ENABLED=1``) wird die Lieferung atomar protokolliert (Exklusivität+Dedupe).
    """
    store = cs.load()
    nat_frei = store.natuerliche_personen_freigegeben()
    commit = getattr(args, "commit", False)
    if commit:
        fehler = _commit_guard(args.kaeufer, args.funktion)
        if fehler:
            print("ABBRUCH: " + fehler)
            return 2
    g = store.gebiet(args.gebiet)
    if not g:
        raise SystemExit(f"Gebiet '{args.gebiet}' nicht im Config-Store ({config.CONFIG_STORE_PATH}).")
    name = g.get("name", args.gebiet)
    con = dbmod.connect(args.db)
    qa_con = statemod.connect()
    try:
        b = deliver.run_region(con, qa_con, plz_prefixes=tuple(g.get("plz_prefixes", ())),
                               region=name, gebiet_id=args.gebiet, resolve=not args.offline,
                               kaeufer=args.kaeufer, funktion=args.funktion, nat_personen_frei=nat_frei)
        slug, heute = _slug(name), dt.date.today().isoformat()
        outdir = Path(args.out_dir) if args.out_dir else Path(".")
        outdir.mkdir(parents=True, exist_ok=True)
        for label, recs in (("lieferbar", b.lieferbar), ("qa_pending", b.pending),
                            ("namenlos", b.namenlos), ("speicher_geplant", b.speicher_geplant)):
            if recs:
                p = outdir / f"{slug}_{label}_{heute}.csv"
                _write_signals_csv(p, recs)
                print(f"  {label:16s}: {len(recs):4d} -> {p}")
        mail = deliver.liefer_mail(b, kaeufer=args.kaeufer, funktion=args.funktion or "Speicher-Installateur")
        mp = outdir / f"{slug}_liefermail_{heute}.txt"
        mp.write_text(mail, encoding="utf-8")
        print(f"  mail            :      -> {mp}")
        print(f"Gebiet {name}: {len(b.lieferbar)} lieferbar ({b.betriebe()} Betriebe) · {len(b.pending)} QA-pending · "
              f"{len(b.namenlos)} namenlos · {len(b.speicher_geplant)} Speicher-geplant · "
              f"{b.colocated_ausgeschlossen} colocated-ausgeschlossen.")
        if args.print_mail:
            print("\n" + "=" * 78 + "\n" + mail)
        # Commit ZULETZT — erst nachdem CSV+Mail auf der Platte liegen (Refute HIGH: nie 'geliefert'
        # protokollieren, bevor das Liefer-Paket existiert).
        if commit:
            n = _commit_buckets(qa_con, [b], args.kaeufer, args.funktion)
            print(f"  → {n} Einheiten ins Live-Ledger protokolliert.")
    finally:
        con.close()
        qa_con.close()
    return 0


def cmd_mengen(args: argparse.Namespace) -> int:
    """Ehrlicher Mengen-/Dichte-Report (Betriebe UND Einheiten) je Gebiet (TEIL 5)."""
    store = cs.load()
    targets = [store.gebiet(args.gebiet)] if args.gebiet else list(store.active_gebiete())
    con = dbmod.connect(args.db)
    qa_con = statemod.connect()
    buckets = []
    try:
        index = build_storage_index(con)
        for g in targets:
            if not g:
                continue
            buckets.append(deliver.run_region(
                con, qa_con, plz_prefixes=tuple(g.get("plz_prefixes", ())),
                region=g.get("name", g["id"]), gebiet_id=g["id"], resolve=False, index=index))
    finally:
        con.close()
        qa_con.close()
    print(deliver.mengen_report(buckets))
    return 0


def cmd_weekly(args: argparse.Namespace) -> int:
    """Wöchentlicher Takt (A): Export neu laden -> dated Snapshot -> Prune -> Hinweis auf echten Diff."""
    if not args.skip_build:
        print("1/3 build-db: Export neu laden (kann ~5-30 min dauern) …")
        export_adapter.build_db()
    con = dbmod.connect(args.db)
    try:
        print("2/3 Snapshot schreiben …")
        out = snapstore.write_snapshot(con)
    finally:
        con.close()
    print(f"      -> {out.name}")
    geloescht = snapstore.prune()
    metas = snapstore.list_snapshots()
    print(f"3/3 Prune: {len(geloescht)} alte gelöscht · vorhandene Snapshots: {[m.datum for m in metas]}")
    if len(metas) >= 2:
        print("✓ ≥2 Snapshots — `diff --gebiet <id>` liefert jetzt ECHTE FLUSS-Signale (T1/T4).")
    else:
        print("→ Erst 1 Snapshot. Nächste Woche denselben Befehl = erster echter Wochen-Diff.")
    return 0


def cmd_gate_demo(args: argparse.Namespace) -> int:
    """Gate-Demo-Paket (B): Liefer-Pakete für die Demo-Gebiete + ehrlicher Mengen-Report, ein Lauf.

    Default = Dry-Run (read-only Vorschau, 0 Ledger-Zeilen — so wird die Demo gezeigt). Mit ``--commit``
    (+ --kaeufer/--funktion, nur bei ``LIVE_DELIVERY_ENABLED=1``) würde echt protokolliert; bei
    ausgeschaltetem Schalter bricht der Befehl mit klarer Meldung ab (§0, Demo füllt das Live-Ledger nie).
    """
    store = cs.load()
    nat_frei = store.natuerliche_personen_freigegeben()
    commit = getattr(args, "commit", False)
    if commit:
        fehler = _commit_guard(args.kaeufer, args.funktion)
        if fehler:
            print("ABBRUCH: " + fehler)
            return 2
    gids = ([g.strip() for g in args.gebiete.split(",") if g.strip()]
            if args.gebiete else [g["id"] for g in store.active_gebiete()])
    outdir = Path(args.out_dir) if args.out_dir else Path("gate_demo")
    outdir.mkdir(parents=True, exist_ok=True)
    heute = dt.date.today().isoformat()
    con = dbmod.connect(args.db)
    qa_con = statemod.connect()
    buckets = []
    try:
        index = build_storage_index(con)
        for gid in gids:
            g = store.gebiet(gid)
            if not g:
                print(f"  Gebiet '{gid}' unbekannt — übersprungen.")
                continue
            name = g.get("name", gid)
            b = deliver.run_region(con, qa_con, plz_prefixes=tuple(g.get("plz_prefixes", ())),
                                   region=name, gebiet_id=gid, resolve=not args.offline, index=index,
                                   kaeufer=args.kaeufer, funktion=args.funktion, nat_personen_frei=nat_frei)
            buckets.append(b)
            slug = _slug(name)
            for label, recs in (("lieferbar", b.lieferbar), ("qa_pending", b.pending),
                                ("namenlos", b.namenlos), ("speicher_geplant", b.speicher_geplant)):
                if recs:
                    _write_signals_csv(outdir / f"{slug}_{label}_{heute}.csv", recs)
            (outdir / f"{slug}_liefermail_{heute}.txt").write_text(
                deliver.liefer_mail(b, kaeufer=args.kaeufer,
                                    funktion=args.funktion or "Speicher-Installateur"), encoding="utf-8")
            print(f"  {name}: {len(b.lieferbar)} lieferbar ({b.betriebe()} Betriebe) "
                  f"-> {slug}_lieferbar/qa_pending/namenlos/speicher_geplant_*.csv + Mail")
        if commit:
            n = _commit_buckets(qa_con, buckets, args.kaeufer, args.funktion)
            print(f"Σ {n} Einheiten ins Live-Ledger protokolliert.")
    finally:
        con.close()
        qa_con.close()
    report = deliver.mengen_report(buckets)
    (outdir / f"mengen_report_{heute}.txt").write_text(report, encoding="utf-8")
    print(f"\nGate-Demo-Paket -> {outdir}/\n")
    print(report)
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    """Sichere die nicht-regenerierbare pipeline_state.db (QA + Exklusiv-/Liefer-Ledger + Metriken)."""
    p = statemod.backup_state_db()
    backups = statemod.list_backups()
    print(f"Backup -> {p}")
    print(f"Vorhandene Backups: {len(backups)} (neuestes: {backups[0].name if backups else '—'})")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    """Stelle pipeline_state.db aus einem Backup wieder her (Default: neuestes) — validiert + atomar (DoD §9.5)."""
    if args.from_backup:
        bp = Path(args.from_backup)
    else:
        backups = statemod.list_backups()
        if not backups:
            raise SystemExit("Keine Backups in pipeline/backups/ — erst `backup` laufen lassen.")
        bp = backups[0]
    dest = statemod.restore_state_db(bp)
    print(f"Restore: {bp.name} -> {dest}  (validiert, WAL/SHM bereinigt)")
    con = statemod.connect(dest)
    try:
        for t in ("qa_decision", "exclusivity", "delivery"):
            n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {n} Zeilen wiederhergestellt")
    finally:
        con.close()
    return 0


def cmd_portal(args: argparse.Namespace) -> int:
    """Kundenportal (DoD §9.4): serve / seed-demo / add-customer. Läuft auf Sample-Daten; LIVE aus → Demo."""
    from .portal import app as portalapp
    from .portal import auth as pauth
    from .portal import seed as pseed
    if args.action == "serve":
        if config.LIVE_DELIVERY_ENABLED:
            print("HINWEIS: LIVE_DELIVERY_ENABLED ist AN — das Portal zeigt KEINE Demo-Kennzeichnung mehr.")
        print(f"Kundenportal: http://127.0.0.1:{args.port}/  (Strg+C zum Beenden)")
        portalapp.serve(port=args.port)
        return 0
    con = statemod.connect()
    try:
        if args.action == "seed-demo":
            n = pseed.seed_demo_leads(con)
            print(f"Demo-Leads gesetzt: {n} (synthetisch, §0-sicher).")
        elif args.action == "add-customer":
            if not (args.login and args.gebiet):
                raise SystemExit("add-customer verlangt --login und --gebiet.")
            pw = args.password or secrets.token_urlsafe(9)
            try:
                cid = pauth.create_customer(con, login=args.login, password=pw, name=args.name or args.login,
                                            gebiet=args.gebiet, funktion=args.funktion or "speicher_installateur")
            except sqlite3.IntegrityError:
                raise SystemExit(f"Login '{args.login}' existiert bereits.") from None
            print(f"Kunde #{cid} angelegt: login={args.login.strip().lower()} · gebiet={args.gebiet}")
            if not args.password:
                print(f"  generiertes Passwort: {pw}   (JETZT notieren — wird nicht erneut angezeigt)")
    finally:
        con.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="pipeline", description="MaStR-Lead-Pipeline (B-Backbone)")
    p.add_argument("--db", default=None, help="Pfad zur open-mastr SQLite (Default: ~/.open-MaStR/...).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("inspect", help="Tabellen/Spalten der DB auflösen + gegen config.py prüfen")
    sp.set_defaults(func=cmd_inspect)

    sb = sub.add_parser("build-db", help="Gesamtexport via open-mastr -> SQLite laden (~3 GB)")
    sb.add_argument("--data", nargs="*", help=f"open-mastr data= (Default {config.OPENMASTR_DATA})")
    sb.set_defaults(func=cmd_build_db)

    sl = sub.add_parser("leads", help="Region -> klassifizierte Leads (ABR-Speicher-Anywhere-Check)")
    sl.add_argument("--plz", default="", help="PLZ-Präfixe, komma-getrennt, z.B. 48,59")
    sl.add_argument("--bundesland", default="")
    sl.add_argument("--limit", type=int, default=None)
    sl.add_argument("--region-name", default="")
    sl.add_argument("--out", default="")
    sl.set_defaults(func=cmd_leads)

    ss = sub.add_parser("signals", help="Post-EEG-Signal-Shipper T2 (cohort+qualify+QA) -> SignalRecord-CSV")
    ss.add_argument("--gebiet", default="", help="Gebiet-ID aus dem Config-Store (z.B. muensterland)")
    ss.add_argument("--plz", default="", help="Ad-hoc PLZ-Präfixe (überschreibt --gebiet)")
    ss.add_argument("--region-name", default="")
    ss.add_argument("--kaeufer", default="", help="optional: Ledger-Käufer (Exklusivität+Dedupe)")
    ss.add_argument("--funktion", default="", help="optional: Käufer-Funktion fürs Ledger")
    ss.add_argument("--offline", action="store_true", help="ohne Evidenz-Direktlink-Auflösung (kein Netz)")
    ss.add_argument("--out", default="")
    ss.set_defaults(func=cmd_signals)

    se = sub.add_parser("evidenz-check", help="Stichprobe der Evidenz-URLs auf Erreichbarkeit prüfen")
    se.add_argument("--gebiet", default="")
    se.add_argument("--plz", default="")
    se.add_argument("--sample", type=int, default=10)
    se.set_defaults(func=cmd_evidenz_check)

    sf = sub.add_parser("liefern", help="Liefer-Paket: getrennte Bucket-CSVs + Liefer-Mail (TEIL 5)")
    sf.add_argument("--gebiet", required=True, help="Gebiet-ID aus dem Config-Store")
    sf.add_argument("--kaeufer", default="")
    sf.add_argument("--funktion", default="")
    sf.add_argument("--out-dir", default="")
    sf.add_argument("--offline", action="store_true", help="ohne Evidenz-Direktlink-Auflösung")
    sf.add_argument("--print-mail", action="store_true", help="Liefer-Mail zusätzlich ausgeben")
    sf.add_argument("--commit", action="store_true",
                    help="echte Lieferung ins Live-Ledger protokollieren (Exklusivität+Dedupe); "
                         "nur bei LIVE_DELIVERY_ENABLED=1, sonst Abbruch. Default = Dry-Run.")
    sf.set_defaults(func=cmd_liefern)

    sm = sub.add_parser("mengen", help="ehrlicher Mengen-/Dichte-Report (Betriebe UND Einheiten)")
    sm.add_argument("--gebiet", default="", help="ein Gebiet (Default: alle aktiven)")
    sm.set_defaults(func=cmd_mengen)

    sw = sub.add_parser("weekly", help="Wochen-Takt: build-db -> dated Snapshot -> prune (für FLUSS-Diff)")
    sw.add_argument("--skip-build", action="store_true",
                    help="Export NICHT neu laden, nur Snapshot aus vorhandener DB")
    sw.set_defaults(func=cmd_weekly)

    sgd = sub.add_parser("gate-demo", help="Gate-Demo-Paket: Liefer-Pakete + Mengen-Report (reproduzierbar)")
    sgd.add_argument("--gebiete", default="", help="Gebiet-IDs komma-getrennt (Default: alle aktiven)")
    sgd.add_argument("--kaeufer", default="")
    sgd.add_argument("--funktion", default="")
    sgd.add_argument("--out-dir", default="")
    sgd.add_argument("--offline", action="store_true")
    sgd.add_argument("--commit", action="store_true",
                     help="echte Lieferung ins Live-Ledger protokollieren; nur bei LIVE_DELIVERY_ENABLED=1, "
                          "sonst Abbruch. Default = Dry-Run (read-only, füllt das Live-Ledger nie).")
    sgd.set_defaults(func=cmd_gate_demo)

    sq = sub.add_parser("qa", help="Mensch-QA-Gate (D5): Queue / approve / reject / approve-abr")
    sq.add_argument("action", choices=["list", "suggest", "approve", "reject", "approve-abr"])
    sq.add_argument("einheit", nargs="?", default="", help="EinheitMastrNummer (bzw. ABR bei approve-abr)")
    sq.add_argument("--grund", default="")
    sq.add_argument("--notiz", default="")
    sq.add_argument("--status", default="pending", help="list-Filter: pending|approved|rejected|alle")
    sq.add_argument("--limit", type=int, default=None)
    sq.add_argument("--online", action="store_true",
                    help="list: fehlende Evidenz-IDs live auflösen (langsamer, füllt Cache) statt nur Cache")
    sq.set_defaults(func=cmd_qa)

    sn = sub.add_parser("snapshot", help="schlanken, dated Wochen-Snapshot schreiben (D2)")
    sn.add_argument("--datum", default="", help="ISO-Stand (Default date.today())")
    sn.add_argument("--prune", action="store_true", help="alte Snapshots nach Retention löschen")
    sn.set_defaults(func=cmd_snapshot)

    sd = sub.add_parser("diff", help="Wochen-Diff der 2 jüngsten Snapshots -> Signale (T1/T4 scharf)")
    sd.add_argument("--gebiet", default="", help="Gebiet-ID für effektive Trigger-Schaltung")
    sd.add_argument("--no-enrich", action="store_true", help="ohne Region/Name-Anreicherung aus der DB")
    sd.add_argument("--out", default="")
    sd.set_defaults(func=cmd_diff)

    sg = sub.add_parser("ledger", help="Exklusivitäts-Ledger (D6): overview / reserve / release")
    sg.add_argument("action", choices=["overview", "reserve", "release"])
    sg.add_argument("--funktion", default="")
    sg.add_argument("--gebiet", default="")
    sg.add_argument("--trigger", default="")
    sg.add_argument("--kaeufer", default="")
    sg.set_defaults(func=cmd_ledger)

    sh = sub.add_parser("dashboard", help="Admin-Dashboard starten (Steuer-Schicht, localhost)")
    sh.add_argument("--port", type=int, default=8765)
    sh.set_defaults(func=cmd_dashboard)

    sbk = sub.add_parser("backup", help="pipeline_state.db sichern (QA + Ledger + Metriken, nicht regenerierbar)")
    sbk.set_defaults(func=cmd_backup)

    srs = sub.add_parser("restore", help="pipeline_state.db aus einem Backup wiederherstellen (Default: neuestes)")
    srs.add_argument("--from", dest="from_backup", default="", help="Backup-Pfad (Default: neuestes in backups/)")
    srs.set_defaults(func=cmd_restore)

    spo = sub.add_parser("portal", help="Kundenportal (Login/Auth, Mandanten-Sicht) — Sample-Daten, DoD §9.4")
    spo.add_argument("action", choices=["serve", "seed-demo", "add-customer"])
    spo.add_argument("--port", type=int, default=8770)
    spo.add_argument("--login", default="", help="add-customer: Login (E-Mail/Benutzername)")
    spo.add_argument("--name", default="", help="add-customer: Anzeigename")
    spo.add_argument("--gebiet", default="", help="add-customer: zugeordnetes Gebiet (Mandant)")
    spo.add_argument("--funktion", default="", help="add-customer: Funktion (Default speicher_installateur)")
    spo.add_argument("--password", default="", help="add-customer: Passwort (leer = generiert + angezeigt)")
    spo.set_defaults(func=cmd_portal)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
