"""
Render-Schicht des Admin-Dashboards (K8, Briefing §6) — REINE Funktionen, ohne Server/Socket.

Hier liegt NUR HTML-Erzeugung: jede Funktion nimmt fertige Daten (ConfigStore + aggregierte
Metrik-Zeilen + Ledger-Overview) und gibt einen HTML-String zurück. Dadurch ist die gesamte
Darstellung ohne ``http.server`` testbar (test_dashboard.py prüft den String direkt).

Bewusst stdlib-only und ohne externe Assets: schlankes Inline-CSS, ``html.escape`` gegen Injection
(Gebietsnamen/Labels kommen aus dem editierbaren Config-Store). KEIN Import aus der Pipeline-Logik
(triggers/qualify/cohort) — das Dashboard ist reine Steuer-/Lese-Schicht.
"""
from __future__ import annotations

import html

from ..control.config_store import ConfigStore, VALID_MODULES, VALID_TRIGGERS

# Inline-CSS — schlank, keine externen Dateien (Dashboard läuft offline/intern).
_CSS = """
:root { color-scheme: light dark; }
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
       margin: 1.5rem; line-height: 1.4; }
h1 { font-size: 1.4rem; }
h2 { font-size: 1.1rem; margin-top: 1.8rem; border-bottom: 1px solid #8884; padding-bottom: .2rem; }
table { border-collapse: collapse; margin: .5rem 0 1rem; width: 100%; max-width: 60rem; }
th, td { border: 1px solid #8884; padding: .3rem .55rem; text-align: left; font-size: .9rem; }
th { background: #8881; }
.an { color: #1a7f37; font-weight: 600; }
.aus { color: #b34; font-weight: 600; }
.toggle { display: inline; margin: 0; }
button { cursor: pointer; padding: .15rem .6rem; border: 1px solid #8886; border-radius: .3rem;
         background: #8881; font-size: .85rem; }
.muted { color: #8889; font-size: .8rem; }
code { background: #8881; padding: 0 .25rem; border-radius: .2rem; }
"""


def _esc(value: object) -> str:
    """HTML-sicher escapen (None → leer). Config-Werte sind menschlich editierbar → nie roh ausgeben."""
    return html.escape("" if value is None else str(value))


def _status_zelle(enabled: bool) -> str:
    """Einheitliche AN/AUS-Zelle (grün/rot) für alle Schalter-Tabellen."""
    return ('<span class="an">AN</span>' if enabled
            else '<span class="aus">AUS</span>')


def _toggle_form(kind: str, key: str, enabled: bool) -> str:
    """Mini-POST-Form je Schalter: kippt ``enabled`` (setzt das Gegenteil des Ist-Werts).

    Ein Button pro Zeile (`http.server` + Form-POST, kein JS nötig). ``kind`` steuert, welchen
    Schalter app.py setzt (trigger | module | gebiet), ``key`` ist der Trigger-/Modul-/Gebiet-Schlüssel.
    """
    ziel = "0" if enabled else "1"
    label = "ausschalten" if enabled else "einschalten"
    return (
        '<form class="toggle" method="post" action="/toggle">'
        f'<input type="hidden" name="kind" value="{_esc(kind)}">'
        f'<input type="hidden" name="key" value="{_esc(key)}">'
        f'<input type="hidden" name="enabled" value="{ziel}">'
        f'<button type="submit">{label}</button>'
        '</form>'
    )


def _trigger_tabelle(store: ConfigStore) -> str:
    """Trigger-Schalter T1..PV_ERWEITERUNG (an/aus) mit Label + Umschalt-Button."""
    zeilen = []
    for key in VALID_TRIGGERS:
        t = store.triggers.get(key, {})
        enabled = store.is_trigger_enabled(key)
        label = t.get("label", "")
        zeilen.append(
            f"<tr><td><code>{_esc(key)}</code></td><td>{_esc(label)}</td>"
            f"<td>{_status_zelle(enabled)}</td>"
            f"<td>{_toggle_form('trigger', key, enabled)}</td></tr>"
        )
    return (
        "<h2>Trigger</h2>"
        "<table><thead><tr><th>Schlüssel</th><th>Bezeichnung</th>"
        "<th>Zustand</th><th>Aktion</th></tr></thead>"
        f"<tbody>{''.join(zeilen)}</tbody></table>"
    )


def _modul_tabelle(store: ConfigStore) -> str:
    """Modul-Schalter (z.B. Anreicherung an/aus) — default aus, scharf erst nach Call + Lizenz."""
    zeilen = []
    for name in VALID_MODULES:
        m = store.modules.get(name, {})
        enabled = store.is_module_enabled(name)
        label = m.get("label", "")
        zeilen.append(
            f"<tr><td><code>{_esc(name)}</code></td><td>{_esc(label)}</td>"
            f"<td>{_status_zelle(enabled)}</td>"
            f"<td>{_toggle_form('module', name, enabled)}</td></tr>"
        )
    return (
        "<h2>Module</h2>"
        "<table><thead><tr><th>Modul</th><th>Bezeichnung</th>"
        "<th>Zustand</th><th>Aktion</th></tr></thead>"
        f"<tbody>{''.join(zeilen)}</tbody></table>"
    )


def _gebiete_tabelle(store: ConfigStore) -> str:
    """Gebiete mit enabled + PLZ-Präfixen + aktiven Trigger-Overrides (nur AB-Schaltung)."""
    zeilen = []
    for g in store.gebiete:
        gid = g.get("id", "")
        enabled = bool(g.get("enabled"))
        prefixes = ", ".join(g.get("plz_prefixes") or [])
        overrides = g.get("trigger_overrides") or {}
        # Overrides können nur ABschalten (config_store-Semantik) -> nur die False-Einträge zeigen.
        aus = [k for k, v in overrides.items() if v is False]
        ov_txt = ", ".join(aus) if aus else "—"
        zeilen.append(
            f"<tr><td><code>{_esc(gid)}</code></td><td>{_esc(g.get('name'))}</td>"
            f"<td>{_status_zelle(enabled)}</td><td>{_esc(prefixes)}</td>"
            f"<td>{_esc(ov_txt)}</td>"
            f"<td>{_toggle_form('gebiet', gid, enabled)}</td></tr>"
        )
    return (
        "<h2>Gebiete</h2>"
        "<table><thead><tr><th>ID</th><th>Name</th><th>Zustand</th>"
        "<th>PLZ-Präfixe</th><th>Trigger aus (Override)</th><th>Aktion</th></tr></thead>"
        f"<tbody>{''.join(zeilen)}</tbody></table>"
    )


def _monitoring_tabelle(metrics_rows: list[dict]) -> str:
    """Monitoring je Gebiet × Trigger × Woche × Metrik (Volumen/Frische) aus metrics.aggregate."""
    if not metrics_rows:
        body = '<tr><td colspan="5" class="muted">Noch keine Metriken erfasst.</td></tr>'
    else:
        zeilen = []
        for r in metrics_rows:
            wert = r.get("summe")
            wert_txt = "" if wert is None else f"{wert:g}"
            zeilen.append(
                f"<tr><td>{_esc(r.get('woche'))}</td>"
                f"<td>{_esc(r.get('gebiet') or '—')}</td>"
                f"<td>{_esc(r.get('trigger') or '—')}</td>"
                f"<td>{_esc(r.get('metrik'))}</td>"
                f"<td>{_esc(wert_txt)}</td></tr>"
            )
        body = "".join(zeilen)
    return (
        "<h2>Monitoring</h2>"
        "<table><thead><tr><th>Woche</th><th>Gebiet</th><th>Trigger</th>"
        "<th>Metrik</th><th>Wert</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _exklusivitaet_tabelle(ledger_rows: list[dict]) -> str:
    """Exklusivitäts-Übersicht aus ledger.overview: wer hält welches Gebiet × Trigger je Funktion."""
    if not ledger_rows:
        body = '<tr><td colspan="5" class="muted">Keine aktiven Reservierungen.</td></tr>'
    else:
        zeilen = []
        for r in ledger_rows:
            zeilen.append(
                f"<tr><td>{_esc(r.get('funktion'))}</td>"
                f"<td>{_esc(r.get('gebiet'))}</td>"
                f"<td>{_esc(r.get('trigger'))}</td>"
                f"<td>{_esc(r.get('kaeufer'))}</td>"
                f"<td>{_esc(r.get('reserviert_am'))}</td></tr>"
            )
        body = "".join(zeilen)
    return (
        "<h2>Exklusivität</h2>"
        "<table><thead><tr><th>Funktion</th><th>Gebiet</th><th>Trigger</th>"
        "<th>Käufer</th><th>reserviert am</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _qa_queue_tabelle(qa_rows: list) -> str:
    """Offene QA-Queue (Grenzfälle): EinheitMastrNummer · Betreiber (ABR) · Flags. Entscheidung via CLI."""
    if not qa_rows:
        body = '<tr><td colspan="3" class="muted">Keine offenen QA-Fälle.</td></tr>'
    else:
        body = "".join(
            f"<tr><td><code>{_esc(r['einheit_mastr_nr'])}</code></td>"
            f"<td>{_esc(r['betreiber_mastr_nr'])}</td>"
            f"<td>{_esc(r['flags_at_review'])}</td></tr>"
            for r in qa_rows
        )
    return (
        f"<h2>QA-Queue (offene Grenzfälle: {len(qa_rows)})</h2>"
        '<p class="muted">Entscheiden via CLI: <code>qa approve &lt;SEE&gt;</code> · '
        '<code>qa reject &lt;SEE&gt; --grund …</code> · <code>qa approve-abr &lt;ABR&gt;</code> (Sammel).</p>'
        "<table><thead><tr><th>EinheitMastrNummer</th><th>Betreiber (ABR)</th><th>Flags</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def render_dashboard(
    store: ConfigStore,
    metrics_rows: list[dict],
    ledger_rows: list[dict],
    qa_rows: list | None = None,
) -> str:
    """Vollständige Dashboard-Seite als HTML-String (reine Funktion, testbar ohne Server).

    Setzt sich aus sechs Blöcken zusammen: Trigger-Schalter, Modul-Schalter, Gebiete-Tabelle,
    Monitoring (aus ``metrics.aggregate``), Exklusivität (aus ``ledger.overview``) und QA-Queue
    (aus ``state.qa_pending``). ``store`` liefert die Provenance-Fußzeile (updated_at/updated_by).
    """
    fuss = ""
    if store.updated_at or store.updated_by:
        fuss = (f'<p class="muted">Config zuletzt geändert: {_esc(store.updated_at) or "—"}'
                f' von {_esc(store.updated_by) or "—"}.</p>')
    return (
        "<!doctype html><html lang=\"de\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>GoldenTime — Admin-Dashboard</title>"
        f"<style>{_CSS}</style></head><body>"
        "<h1>GoldenTime — Admin-Dashboard</h1>"
        '<p class="muted">Interne Steuer-Schicht: Trigger/Module/Gebiete schalten, '
        "Monitoring + Exklusivität lesen.</p>"
        + _trigger_tabelle(store)
        + _modul_tabelle(store)
        + _gebiete_tabelle(store)
        + _monitoring_tabelle(metrics_rows)
        + _qa_queue_tabelle(qa_rows or [])
        + _exklusivitaet_tabelle(ledger_rows)
        + fuss
        + "</body></html>"
    )
