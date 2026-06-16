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
import sys
from collections import Counter
from pathlib import Path

from . import config
from . import db as dbmod
from . import export_adapter
from .normalize import iter_leads
from .speicher_check import build_storage_index
from .signal import SignalRecord
from .triggers import cohort, diff_based
from .qualify import hierarchy, qa_gate
from .snapshot import store as snapstore
from .ledger import ledger as ledgermod
from .control import config_store as cs
from .control import state as statemod
from .control import metrics as metricsmod

log = logging.getLogger("pipeline")


def _slug(s: str) -> str:
    s = (s or "").lower().replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "region"


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
    prefixes = tuple(p.strip() for p in args.plz.split(",") if p.strip()) if args.plz else ()
    leads = list(
        iter_leads(con, index, plz_prefixes=prefixes, bundesland=args.bundesland, limit=args.limit)
    )
    con.close()

    deliver = [x for x in leads if x["ausschluss_grund"] is None]
    excluded = [x for x in leads if x["ausschluss_grund"] is not None]
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
        prefixes = tuple(p.strip() for p in args.plz.split(",") if p.strip())
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

            # Lieferbar = QA-ok UND mit Namen (ohne Firmenname kein B2B-Kontakt -> namenlos-Bucket).
            deliver = [r for r in records
                       if r.qa_status in (qa_gate.AUTO_OK, qa_gate.APPROVED) and r.entity]
            namenlos = [r for r in records if not r.entity]
            pending = [r for r in records if r.qa_status == qa_gate.PENDING]
            rejected = [r for r in records if r.qa_status == qa_gate.REJECTED]
            if args.kaeufer and args.funktion:   # optionales Ledger-Gate (Exklusivität + Dedupe)
                deliver = ledgermod.filter_deliverable(qa_con, deliver, args.kaeufer, args.funktion, gid, "T2")
            deliver.sort(key=lambda r: (r.dv_flag, r.kwp or 0), reverse=True)  # DV + größte zuerst

            for metrik, wert in (("signale", len(records)), ("lieferbar", len(deliver)),
                                 ("pending_qa", len(pending)), ("namenlos", len(namenlos)),
                                 ("dv_flag", sum(r.dv_flag for r in deliver))):
                metricsmod.record(qa_con, metrik=metrik, wert=wert, woche=woche, gebiet=gid, trigger="T2")

            print(f"Gebiet {name}: {len(records)} T2-Signale · {len(deliver)} lieferbar · "
                  f"{len(pending)} QA-pending · {len(namenlos)} namenlos (Privatperson) · "
                  f"{len(rejected)} rejected · DV-Flag {sum(r.dv_flag for r in deliver)}.")
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
        for r in rows:
            url = f"https://www.marktstammdatenregister.de/MaStR/Einheit/Detail/IndexOeffentlich/{r['einheit_mastr_nr']}"
            print(f"  {r['einheit_mastr_nr']:16s} {r['status']:9s} ABR={r['betreiber_mastr_nr'] or '—':16s} "
                  f"flags={r['flags_at_review'] or ''}  {url}")
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
    """Wochen-Diff der zwei jüngsten Snapshots -> diff-basierte Signale (T1/T4 scharf; T5/T6/PV aus)."""
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
        pending = [r for r in records if r.qa_status == qa_gate.PENDING]
        namenlos = [r for r in records if not r.entity]
    finally:
        if con:
            con.close()
        qa_con.close()
    print(f"Diff {prev.name} -> {curr.name}: {len(records)} Signale "
          f"(Trigger: {dict(Counter(r.trigger_typ for r in records))}) · {len(deliver)} lieferbar · "
          f"{len(pending)} QA-pending · {len(namenlos)} namenlos.")
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
            print(f"  {r['funktion']:22s} {r['gebiet']:14s} {r['trigger']:6s} -> {r['kaeufer']}  ({r['reserviert_am']})")
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
    ss.add_argument("--out", default="")
    ss.set_defaults(func=cmd_signals)

    sq = sub.add_parser("qa", help="Mensch-QA-Gate (D5): Queue / approve / reject / approve-abr")
    sq.add_argument("action", choices=["list", "approve", "reject", "approve-abr"])
    sq.add_argument("einheit", nargs="?", default="", help="EinheitMastrNummer (bzw. ABR bei approve-abr)")
    sq.add_argument("--grund", default="")
    sq.add_argument("--notiz", default="")
    sq.add_argument("--status", default="pending", help="list-Filter: pending|approved|rejected|alle")
    sq.add_argument("--limit", type=int, default=None)
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

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
