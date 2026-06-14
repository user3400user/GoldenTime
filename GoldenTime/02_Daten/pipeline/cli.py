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

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
