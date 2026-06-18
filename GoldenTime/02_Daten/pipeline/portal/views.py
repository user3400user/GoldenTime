"""
Kundenportal — HTML-Rendering (Loop 3, stdlib, KEIN Framework/Template-Engine).

Reine Render-Funktionen (str → str), alles via ``html.escape`` ausgegeben (kein XSS). Bewusst
schlank + vertrauenswürdig (Zielbild UX 4,5: „sauberes, vertrauenswürdiges Kundenportal, signalisiert
seriöser Datenpartner" — NICHT Consumer-Design-System). Provenance 1-Klick (MaStR-Direktlink je Lead)
+ dl-de-Quellenvermerk im Footer. Demo-Banner, solange ``LIVE_DELIVERY_ENABLED`` aus ist (§0).
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from html import escape as e

_CSS = """
:root { --fg:#1a2332; --muted:#667085; --line:#e4e7ec; --bg:#f7f8fa; --accent:#11633f; --warn:#8a5a00; }
* { box-sizing:border-box; }
body { margin:0; font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; color:var(--fg); background:var(--bg); }
header { background:#fff; border-bottom:1px solid var(--line); padding:14px 22px; display:flex; align-items:center; justify-content:space-between; }
.brand { font-weight:700; letter-spacing:.2px; } .brand span { color:var(--accent); }
.wrap { max-width:980px; margin:0 auto; padding:22px; }
.demo { background:#fff7e6; border:1px solid #f0d399; color:var(--warn); padding:8px 14px; border-radius:8px; font-size:13px; margin-bottom:18px; }
table { width:100%; border-collapse:collapse; background:#fff; border:1px solid var(--line); border-radius:10px; overflow:hidden; }
th,td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); font-size:14px; }
th { background:#fafbfc; color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.4px; }
tr:last-child td { border-bottom:0; }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
.muted { color:var(--muted); } .pill { display:inline-block; background:#eef4f0; color:var(--accent); padding:1px 8px; border-radius:20px; font-size:12px; }
footer { color:var(--muted); font-size:12px; padding:22px; max-width:980px; margin:0 auto; border-top:1px solid var(--line); }
.card { background:#fff; border:1px solid var(--line); border-radius:10px; padding:22px; }
.login { max-width:380px; margin:8vh auto; }
label { display:block; font-size:13px; color:var(--muted); margin:12px 0 4px; }
input { width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:8px; font-size:15px; }
button { margin-top:18px; width:100%; padding:11px; background:var(--accent); color:#fff; border:0; border-radius:8px; font-size:15px; cursor:pointer; }
button.link { width:auto; margin:0; background:none; color:var(--muted); padding:0; font-size:13px; }
.err { background:#fdecec; border:1px solid #f3c0c0; color:#9b2c2c; padding:8px 12px; border-radius:8px; font-size:14px; margin-top:14px; }
.kv { display:grid; grid-template-columns:170px 1fr; gap:8px 16px; font-size:14px; } .kv dt { color:var(--muted); }
"""

_DL_DE = ("Datenbasis: Marktstammdatenregister (MaStR) der Bundesnetzagentur, Lizenz dl-de/by-2.0 "
          "(govdata.de/dl-de/by-2-0). Kein amtlicher Datensatz, keine Gewähr — abgeleitete Auswertung.")


def _layout(inhalt: str, *, kunde: sqlite3.Row | None = None, demo: bool = True, title: str = "Portal") -> str:
    kopf_rechts = (
        f'<span class="muted">{e(kunde["name"] or kunde["login"])} · {e(kunde["gebiet"])}</span>'
        if kunde is not None else ""
    )
    abmelden = ""  # Logout-Button wird vom Aufrufer mit CSRF-Token in den Inhalt gesetzt
    demo_banner = ('<div class="demo">DEMO-Ansicht · Sample-/öffentliche Gewerbedaten, '
                   'natürliche Personen / e.K. hart gefiltert · keine echten Personendaten '
                   '(Live-Lieferung gesperrt bis zur Rechtsfreigabe).</div>') if demo else ""
    return (
        f"<!doctype html><html lang=de><head><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{e(title)} · GoldenTime</title><style>{_CSS}</style></head><body>"
        f"<header><div class=brand>Golden<span>Time</span> · Kaufsignale</div><div>{kopf_rechts}{abmelden}</div></header>"
        f"<div class=wrap>{demo_banner}{inhalt}</div>"
        f"<footer>{e(_DL_DE)}</footer></body></html>"
    )


def render_login(*, fehler: str | None = None, csrf: str = "") -> str:
    err = f'<div class=err>{e(fehler)}</div>' if fehler else ""
    inhalt = (
        f'<div class="card login"><h2 style="margin-top:0">Anmeldung</h2>'
        f'<p class=muted style="margin-top:-6px">Zugang zu Ihren exklusiven Kaufsignalen.</p>'
        f'<form method=post action="/login">'
        f'<input type=hidden name=csrf value="{e(csrf)}">'
        f'<label for=login>Login</label><input id=login name=login autocomplete=username autofocus>'
        f'<label for=pw>Passwort</label><input id=pw name=password type=password autocomplete=current-password>'
        f'<button type=submit>Anmelden</button>{err}</form></div>'
    )
    return _layout(inhalt, kunde=None, demo=False, title="Anmeldung")


def render_leads(kunde: sqlite3.Row, leads: list[sqlite3.Row], *, csrf: str = "", demo: bool = True) -> str:
    heute = dt.date.today().isoformat()
    logout = (f'<form method=post action="/logout" style="display:inline">'
              f'<input type=hidden name=csrf value="{e(csrf)}">'
              f'<button class=link type=submit>Abmelden</button></form>')
    if leads:
        zeilen = "".join(
            f"<tr><td><a href='/lead/{e(r['see'])}'>{e(r['entity'] or '—')}</a></td>"
            f"<td>{format(r['kwp'], '.0f') if r['kwp'] is not None else '—'} kWp</td>"
            f"<td>{e(r['plz'] or '')} {e(r['ort'] or '')}</td>"
            f"<td><span class=pill>{e(r['trigger'] or 'T2')}</span></td>"
            f"<td>{'<a href=\"'+e(r['evidenz_url'])+'\" target=_blank rel=noopener>MaStR ↗</a>' if r['evidenz_url'] else '—'}</td></tr>"
            for r in leads
        )
        tabelle = (
            "<table><thead><tr><th>Betrieb</th><th>Leistung</th><th>Ort</th>"
            "<th>Anlass</th><th>Nachweis</th></tr></thead><tbody>" + zeilen + "</tbody></table>"
        )
    else:
        tabelle = ('<div class=card><p class=muted style="margin:0">Aktuell keine Signale in Ihrem '
                   'Gebiet. Die nächste exklusive Lieferung erscheint hier automatisch.</p></div>')
    inhalt = (
        f'<div style="display:flex;align-items:baseline;justify-content:space-between">'
        f'<h2 style="margin:0 0 4px">Ihre Kaufsignale · {e(kunde["gebiet"])}</h2>{logout}</div>'
        f'<p class=muted>Exklusiv für Sie ({e(kunde["funktion"])}) · {len(leads)} Signale · Stand {e(heute)}. '
        f'Jeder Betrieb gehört für diese Funktion ausschließlich Ihnen — gebiets- und anlass-übergreifend.</p>'
        + tabelle
    )
    return _layout(inhalt, kunde=kunde, demo=demo, title="Kaufsignale")


def render_lead(kunde: sqlite3.Row, r: sqlite3.Row, *, csrf: str = "", demo: bool = True) -> str:
    logout = (f'<form method=post action="/logout" style="display:inline">'
              f'<input type=hidden name=csrf value="{e(csrf)}">'
              f'<button class=link type=submit>Abmelden</button></form>')
    evid = (f'<a href="{e(r["evidenz_url"])}" target=_blank rel=noopener>Im Marktstammdatenregister öffnen ↗</a>'
            if r["evidenz_url"] else '<span class=muted>—</span>')
    inhalt = (
        f'<div style="display:flex;align-items:baseline;justify-content:space-between">'
        f'<h2 style="margin:0"><a href="/" class=muted>&larr;</a> {e(r["entity"] or "—")}</h2>{logout}</div>'
        f'<div class=card style="margin-top:14px"><dl class=kv>'
        f'<dt>Leistung</dt><dd>{format(r["kwp"], ".0f") if r["kwp"] is not None else "—"} kWp</dd>'
        f'<dt>Ort</dt><dd>{e(r["plz"] or "")} {e(r["ort"] or "")}</dd>'
        f'<dt>Kaufanlass</dt><dd><span class=pill>{e(r["trigger"] or "T2")}</span></dd>'
        f'<dt>Inbetriebnahme</dt><dd>{e(r["datum"] or "—")}</dd>'
        f'<dt>MaStR-Nr.</dt><dd>{e(r["see"])}</dd>'
        f'<dt>Nachweis (1 Klick)</dt><dd>{evid}</dd>'
        f'<dt>Herkunft</dt><dd>verifiziert via Marktstammdatenregister (Bundesnetzagentur), dl-de/by-2.0</dd>'
        f'</dl></div>'
    )
    return _layout(inhalt, kunde=kunde, demo=demo, title=str(r["entity"] or "Lead"))
