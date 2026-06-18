"""
§6-Monitoring — Metrik-Erfassung + Aggregation auf ``metrics_event`` (pipeline_state.db, D1/D6).

Append-only: die Pipeline schreibt je Lauf Ereignisse (Volumen/Frische/… je Gebiet × Trigger ×
Woche), das Admin-Dashboard LIEST und aggregiert sie nur. Bewusst getrennt von der Schalter-Seite
(config_store.py): Metriken = Ist-Zustand (Schreiber: Pipeline), Config = Soll-Zustand (Schreiber:
Dashboard) — die einseitige Kopplung aus Briefing §6.

Schema-Eigentümer ist control/state.py (Tabelle ``metrics_event`` mit Index ``ix_metrics_dim``);
dieses Modul kennt nur INSERT + GROUP-BY-SELECT, kein eigenes DDL. stdlib-only (sqlite3 + datetime).
Alle Funktionen nehmen eine offene ``state.connect()``-Verbindung (sqlite3.Row) entgegen.
"""
from __future__ import annotations

import datetime as dt
import sqlite3


def iso_woche(tag: dt.date | None = None) -> str:
    """ISO-Wochen-Label ``YYYY-Www`` (z.B. ``2026-W25``) — Default = heutige Woche.

    Stabiler, sortierbarer Schlüssel für die Monitoring-Dimension ``woche``: ISO-8601-Woche,
    nullgepolstert, damit String-Sort = chronologischer Sort bleibt.
    """
    t = tag or dt.date.today()
    jahr, woche, _ = t.isocalendar()
    return f"{jahr:04d}-W{woche:02d}"


def _jetzt() -> str:
    """Erfassungs-Zeitstempel (UTC, sekundengenau) — Audit, wann das Ereignis geschrieben wurde."""
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def record(
    con: sqlite3.Connection,
    *,
    metrik: str,
    wert: float,
    woche: str | None = None,
    gebiet: str | None = None,
    trigger: str | None = None,
) -> None:
    """Erfasse EIN Monitoring-Ereignis (append-only INSERT in ``metrics_event``).

    ``woche`` default = ISO-Woche von heute. ``gebiet``/``trigger`` sind die optionalen
    Dimensionen (None = aggregiert/dimensionslos). ``metrik`` ist Pflicht (z.B. 'signale',
    'lieferbar', 'pending_qa', 'frische_median'), ``wert`` wird als REAL gespeichert.
    Committet selbst — die Pipeline ruft das je Lauf einmal pro Kennzahl.
    """
    if not metrik:
        raise ValueError("metrics.record: 'metrik' ist Pflicht (leerer Name unzulässig).")
    w = woche or iso_woche()
    # Idempotent je (woche, gebiet, trigger, metrik): ein erneuter Lauf DERSELBEN Woche ERSETZT den
    # Wert, statt ihn zu addieren — sonst zeigt aggregate() (SUM) bei 2 Läufen 2x den Count.
    # `IS` ist NULL-sicher (dimensionslose Metriken mit gebiet/trigger=None).
    con.execute(
        "DELETE FROM metrics_event WHERE woche = ? AND gebiet IS ? AND trigger IS ? AND metrik = ?",
        (w, gebiet, trigger, metrik),
    )
    con.execute(
        "INSERT INTO metrics_event(woche, gebiet, trigger, metrik, wert, erfasst_am) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        (w, gebiet, trigger, metrik, float(wert), _jetzt()),
    )
    con.commit()


def anomaly_check(
    con: sqlite3.Connection,
    *,
    gebiet: str | None,
    trigger: str | None,
    wert: float,
    metrik: str = "lieferbar",
    min_history: int = 2,
    collapse_factor: float = 0.5,
) -> str | None:
    """Datenbruch-/Anomalie-Heuristik für eine Kennzahl — gibt eine Warn-Meldung zurück oder ``None``.

    Zwei Stufen (G17): (a) **0 lieferbar** = harte Warnung (eine leere Liste an einen Exklusiv-Kunden
    ist katastrophal und ohne Tracking unsichtbar — Zielbild: Diff-Volumen = Herzschlag). (b)
    **Trailing-Baseline**: liegt der aktuelle Wert unter ``collapse_factor`` × Median der VORHERIGEN
    Wochen (≥ ``min_history`` Wochen Historie), Einbruch-Warnung. Ohne genug Historie greift nur (a)
    — ehrlich: die volle Baseline-Erkennung wird erst mit mehreren Wochen Metrik-Historie wirksam.

    Die aktuelle ISO-Woche wird aus der Baseline ausgeschlossen (sie wurde gerade geschrieben).
    """
    if wert <= 0:
        return (f"ANOMALIE {gebiet}/{trigger}/{metrik}: 0 — leere Liste, NICHT an Kunden ausliefern "
                "(Datenbruch / Region / Join prüfen).")
    aktuelle = iso_woche()
    rows = con.execute(
        "SELECT woche, SUM(wert) AS w FROM metrics_event "
        "WHERE gebiet IS ? AND trigger IS ? AND metrik = ? GROUP BY woche ORDER BY woche DESC",
        (gebiet, trigger, metrik),
    ).fetchall()
    vor = sorted(r["w"] for r in rows if r["woche"] != aktuelle)
    if len(vor) < min_history:
        return None                                  # noch keine belastbare Baseline
    median = vor[len(vor) // 2]
    if median > 0 and wert < collapse_factor * median:
        return (f"ANOMALIE {gebiet}/{trigger}/{metrik}: {wert:.0f} << Median Vorwochen {median:.0f} "
                f"(unter {int(collapse_factor * 100)} %) — möglicher Datenbruch, vor Auslieferung prüfen.")
    return None


def aggregate(con: sqlite3.Connection, *, gebiet: str | None = None) -> list[dict]:
    """Aggregiere Ereignisse je Gebiet × Trigger × Metrik × Woche (Dashboard-Monitoring-Tabelle).

    GROUP BY über die vier Dimensionen; pro Gruppe Summe, Letztwert (jüngstes ``erfasst_am``) und
    Anzahl Ereignisse. Optional auf ein ``gebiet`` eingeschränkt. Sortiert (woche desc, gebiet,
    trigger, metrik) → frischeste Woche oben, stabile Reihenfolge. Flache Dicts (nicht sqlite3.Row),
    direkt serialisierbar fürs Dashboard.

    'letzter_wert' nutzt ``MAX(erfasst_am)`` als Tie-Breaker korrelierter Subquery-frei: bei mehreren
    Ereignissen derselben Dimension+Woche zählt der Summenwert; der Letztwert dient der Frische-Anzeige.
    """
    sql = (
        "SELECT woche, gebiet, trigger, metrik, "
        "       SUM(wert) AS summe, "
        "       COUNT(*) AS anzahl, "
        "       MAX(erfasst_am) AS letzte_erfassung "
        "FROM metrics_event "
    )
    params: tuple = ()
    if gebiet is not None:
        sql += "WHERE gebiet = ? "
        params = (gebiet,)
    sql += (
        "GROUP BY woche, gebiet, trigger, metrik "
        "ORDER BY woche DESC, gebiet, trigger, metrik"
    )
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def latest_by_dimension(con: sqlite3.Connection) -> list[dict]:
    """Je Dimension (Gebiet × Trigger × Metrik) das Ereignis der JÜNGSTEN Woche — Kompakt-Sicht.

    Für die Dashboard-Übersicht, die nicht die Wochenhistorie, sondern nur den aktuellen Stand je
    Kennzahl zeigt. Wählt pro (gebiet, trigger, metrik) die Zeile mit der lexikografisch größten
    ``woche`` (ISO-Label ist sort = chronologisch) und deren Summenwert in dieser Woche.
    Sortiert nach gebiet/trigger/metrik für eine stabile Tabelle.
    """
    rows = con.execute(
        "SELECT a.gebiet, a.trigger, a.metrik, a.woche, SUM(a.wert) AS summe, "
        "       COUNT(*) AS anzahl "
        "FROM metrics_event a "
        "WHERE a.woche = ("
        "   SELECT MAX(b.woche) FROM metrics_event b "
        "   WHERE b.gebiet IS a.gebiet AND b.trigger IS a.trigger AND b.metrik IS a.metrik"
        ") "
        "GROUP BY a.gebiet, a.trigger, a.metrik, a.woche "
        "ORDER BY a.gebiet, a.trigger, a.metrik"
    ).fetchall()
    return [dict(r) for r in rows]
