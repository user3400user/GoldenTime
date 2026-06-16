"""
Diff-basierte Trigger (Komponente 3b, Briefing Phase 2 / K3) — zeitliche Kaufsignale.

Brückt den Snapshot-Diff (``snapshot.diff`` + ``snapshot.rules``) an den zentralen
``SignalRecord``. Während ``cohort.py`` eine reine Stichtags-Kohorte (T2) ohne Diff liefert,
erkennen DIESE Trigger die *Veränderung zwischen zwei Wochen-Snapshots*:

  T1  Neuregistrierung      NEW_UNIT solar an NEUER ABR        (frische Erst-Anmeldung)
  T4  Speicher-Retrofit     NEW_UNIT storage an Solar-Betreiber (SCHARF, aktiver Invest-Zyklus)
  T5  Betreiberwechsel      abr-Wechsel an Bestands-Einheit     (DEFAULT AUS)
  T6  Stilllegung           Stilllegungsdatum leer -> gesetzt   (DEFAULT AUS)
  PV_ERWEITERUNG  Zweit-Einheit an Bestands-ABR (Ausbau)       (DEFAULT AUS)

Die §4-Klassifikation (Zubau ist NEW_UNIT, ABR-Wechsel ≠ immer Eigentümerwechsel, Retrofit-
Meldung lückenhaft, Stilllegung nur leer->gesetzt) liegt vollständig in ``rules.classify_diff``;
dieses Modul übersetzt nur das Ergebnis in einen ``SignalRecord`` UND respektiert den
Config-Store: **emittiert wird ein Trigger nur, wenn ``store.effective_trigger(gebiet_id, t)``
True ist.** T5/T6/PV_ERWEITERUNG sind im Config-Store default-AUS und werden darum standardmäßig
NICHT emittiert — sie werden hier vollständig gebaut, aber erst über das Dashboard (D3)
scharfgeschaltet.

Konfidenz: die §4-Gotchas kommen aus zwei Quellen — (1) der trigger-spezifische Abschlag aus
``record.compute_konfidenz`` (T4 Retrofit-Lücke; „kein Speicher gemeldet"-Abschlag), (2) das
Konfidenz-Flag aus ``rules.classify_diff`` (z. B. T5-Umfirmierungs-Vorbehalt). Beide werden in
``konfidenz_gruende`` als Klartext mitgeführt.

stdlib-only. ``con`` (die open-mastr-Arbeits-DB) ist OPTIONAL und reichert — falls vorhanden —
Region/Name/PLZ aus der Einheit an; ohne ``con`` trägt das Signal die im Snapshot vorhandenen
Felder (Schlüssel, kWp, Datum) und überlässt Name/Region dem nachgelagerten Qualifizierer.
"""
from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from pathlib import Path
from typing import Iterator

from .. import config
from .. import db as dbmod
from ..signal import SignalRecord, compute_konfidenz
from ..signal.record import BUY_RELEVANZ, is_dv_pflichtig
from ..speicher_check import NONE_REPORTED
from ..snapshot import diff as diffmod
from ..snapshot import rules as rulesmod

log = logging.getLogger(__name__)

HEUTE = dt.date.today()

#: Trigger-Schlüssel, die dieses Modul ableiten kann (Config-Store-kompatibel, s. rules.py).
DIFF_TRIGGERS: tuple[str, ...] = (
    rulesmod.T1,
    rulesmod.T4,
    rulesmod.T5,
    rulesmod.T6,
    rulesmod.PV_ERWEITERUNG,
)

# Trigger-Schlüssel des Config-Stores -> trigger_typ im SignalRecord. Der Config-Store
# führt 'PV_ERWEITERUNG', der Record/BUY_RELEVANZ kennt die Kurzform 'PV_ERW' — hier gemappt,
# damit konfidenz/buy_relevanz korrekt aufgelöst werden. T1/T4/T5/T6 sind identisch.
_RECORD_TRIGGER: dict[str, str] = {
    rulesmod.T1: "T1",
    rulesmod.T4: "T4",
    rulesmod.T5: "T5",
    rulesmod.T6: "T6",
    rulesmod.PV_ERWEITERUNG: "PV_ERW",
}

# Klartext-Beleg je Konfidenz-Flag (rules.classify_diff liefert nur das bool); ergänzt die
# Gründe aus compute_konfidenz, damit das Signal seine §4-Unsicherheit transparent macht.
_FLAG_GRUND: dict[str, str] = {
    rulesmod.T5: "Betreiberwechsel oder reine Umfirmierung — aus dem Diff nicht trennbar (QA prüft)",
    rulesmod.T4: "Speicher-Retrofit am Standort/Betreiber gemeldet — Meldung lückenhaft (~40 %)",
}

# Felder, die wir je Einheit OPTIONAL aus der open-mastr-DB nachladen (Region/Name).
_ENRICH_SELECT = ("plz", "ort", "bundesland", "personenart", "einspeisung")


def _to_float(v: object) -> float | None:
    """kWp tolerant nach float (deutsches Dezimalkomma erlaubt)."""
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _load_snapshot_rows(path: Path | str) -> dict[str, dict]:
    """curr-Snapshot als {einheit_nr: Zeilen-Dict} (kWp/Datum/Status je Treffer nachschlagen)."""
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        return {r["einheit_nr"]: dict(r) for r in con.execute("SELECT * FROM snapshot")}
    finally:
        con.close()


def _enrich_units(
    con: sqlite3.Connection | None, einheiten: set[str]
) -> dict[str, dict]:
    """Lade Region/Name-Felder zu den Treffer-Einheiten aus solar_extended UND storage_extended.

    Zweit-Review-Fix (Befund 13): T1/T5/T6/PV liegen in solar, **T4 (Speicher) in storage_extended**.
    Beide Tabellen tragen EinheitMastrNummer als PK + Postleitzahl/Ort/Bundesland — sonst wären die
    T4-Signale region-blind (plz immer None). Ohne ``con`` oder bei fehlenden Spalten bleibt das Dict
    leer (das Signal trägt dann nur die Snapshot-Felder).
    """
    if con is None or not einheiten:
        return {}
    out: dict[str, dict] = {}
    ids = list(einheiten)
    chunk = 500
    for traeger in ("solar", "storage"):   # solar+storage decken alle Diff-Träger ab
        try:
            table = dbmod.resolve_table(con, traeger)
        except LookupError:
            continue
        cols = dbmod.table_columns(con, table)
        einheit_real = dbmod.resolve_column(cols, "einheit_nr")
        if not einheit_real:
            continue
        present = {lg: c for lg, c in dbmod.column_map(cols, *_ENRICH_SELECT).items() if c}
        select_parts = [f'"{einheit_real}" AS einheit_nr'] + [
            f'"{c}" AS {lg}' for lg, c in present.items()
        ]
        base = "SELECT " + ", ".join(select_parts) + f' FROM "{table}" WHERE "{einheit_real}" IN '
        for i in range(0, len(ids), chunk):
            teil = ids[i : i + chunk]
            ph = ", ".join("?" for _ in teil)
            for row in con.execute(base + f"({ph})", teil):
                d = dict(row)
                out.setdefault(d["einheit_nr"], d)   # solar/storage sind disjunkte PKs
    return out


def _build_record(
    ev: diffmod.DiffEvent,
    trigger_key: str,
    konfidenz_flag: bool,
    curr_row: dict | None,
    enrich: dict | None,
) -> SignalRecord:
    """Baue EINEN SignalRecord aus DiffEvent + rules-Ergebnis (+ optionaler Anreicherung).

    Speicher-Status: ein Diff-Treffer läuft NICHT durch den vollen Speicher-Check; wir setzen
    konservativ ``none_reported`` (löst den „kein Speicher gemeldet"-Abschlag aus). Für T4 ist
    der gemeldete Speicher das Signal selbst — der Retrofit-Lücken-Abschlag kommt dort über
    ``compute_konfidenz(trigger_typ='T4', …)`` dazu (nicht über den Speicher-Status).
    """
    record_typ = _RECORD_TRIGGER[trigger_key]
    curr_row = curr_row or {}
    enrich = enrich or {}

    is_t4 = trigger_key == rulesmod.T4
    kwp = _to_float(curr_row.get("brutto_kw"))
    # T4: curr_row ist die SPEICHER-Zeile -> brutto_kw ist Speicher-, nicht PV-Leistung. Weder als
    # kWp ausgeben noch DV daraus ableiten (DV-Pflicht ≥100 kWp bezieht sich auf die PV-Einheit).
    if is_t4:
        kwp = None
    # Maßgebliches Datum: bei T6 das auslösende Stilllegungsdatum (ev.new), sonst Inbetriebnahme.
    if trigger_key == rulesmod.T6 and ev.new is not None:
        datum = str(ev.new)[:10]
    else:
        datum = curr_row.get("inbetriebnahme") or None

    # Speicher-Status: für T4 IST der gemeldete Speicher das Signal -> NICHT none_reported setzen
    # (sonst widersprüchlicher Grund 'kein Speicher gemeldet' + falscher 0.10-Abschlag + falscher
    # QA-Fingerprint-Seed). none_reported nur für T1/T5/T6/PV_ERW (solar ohne gemeldeten Speicher).
    status_seed = "" if is_t4 else NONE_REPORTED
    konfidenz, gruende = compute_konfidenz(record_typ, status_seed, frische_valide=True)
    gruende = list(gruende)
    if konfidenz_flag:
        grund = _FLAG_GRUND.get(trigger_key)
        if grund and grund not in gruende:
            gruende.append(grund)

    buy = BUY_RELEVANZ.get(record_typ, "Kaufsignal aus MaStR-Registerdaten (Wochen-Diff).")
    dv = is_dv_pflichtig(kwp)
    if dv:
        buy += " Direktvermarktungs-pflichtig (≥100 kWp)."

    flags: list[str] = [f"DIFF_{ev.change_type}"]
    if konfidenz_flag and trigger_key == rulesmod.T5:
        flags.append("UMFIRMIERUNG_PRUEFEN")
    if trigger_key == rulesmod.T4:
        flags.append("RETROFIT_GEMELDET")

    provenance = (
        "MaStR Gesamtdatenexport (dl-de/by-2.0); Trigger "
        f"{record_typ} (Wochen-Diff {ev.change_type}); " + HEUTE.isoformat()
    )

    return SignalRecord(
        einheit_mastr_nr=ev.einheit_nr,
        betreiber_mastr_nr=ev.abr or None,
        trigger_typ=record_typ,
        datum=datum,
        konfidenz=konfidenz,
        buy_relevanz=buy,
        entity=None,                       # Name macht der Qualifizierer (market_actors-Join)
        plz=enrich.get("plz"),
        ort=enrich.get("ort"),
        bundesland=enrich.get("bundesland"),
        kwp=round(kwp, 1) if kwp is not None else None,
        einspeisung=enrich.get("einspeisung"),
        speicher_status=status_seed,       # T4: '' (Speicher ist das Signal); sonst none_reported
        speicher_label="",                 # Diff-Signal: voller Speicher-Check kommt im Qualifizierer
        konfidenz_gruende=tuple(gruende),
        flags=tuple(flags),
        dv_flag=dv,
        qa_status="auto_ok",
        geprueft_am=HEUTE.isoformat(),
        provenance=provenance,
    )


def diff_based_signals(
    prev_snapshot_path: Path | str,
    curr_snapshot_path: Path | str,
    store,
    *,
    gebiet_id: str | None = None,
    plz_prefixes: tuple[str, ...] = (),
    con: sqlite3.Connection | None = None,
) -> Iterator[SignalRecord]:
    """Erzeuge diff-basierte Kaufsignale zwischen zwei Wochen-Snapshots (prev -> curr).

    Ablauf: ``snapshot.diff`` liefert die DiffEvents, ``snapshot.rules.classify_diff`` (mit
    ``PrevIndex`` aus dem prev-Snapshot für die T1/PV_ERWEITERUNG- bzw. T4-Verzweigung) den
    abgeleiteten Trigger. **Emittiert wird nur, wenn ``store.effective_trigger(gebiet_id, t)``
    True ist** — die default-aus-Trigger T5/T6/PV_ERWEITERUNG fallen damit ohne Scharfschaltung
    durch den Config-Store still raus.

    ``store``: ein ``control.config_store.ConfigStore`` (Reader; effective_trigger/is_trigger_enabled).
    ``gebiet_id``: optionales Gebiet für den effektiven Trigger-Zustand (None = nur globaler Schalter).
    ``con``: optionale open-mastr-DB für Region/Name-Anreicherung (ohne sie trägt das Signal nur
    die Snapshot-Felder). Yields je Treffer einen ``SignalRecord``.
    """
    prev_index = rulesmod.PrevIndex.from_snapshot(prev_snapshot_path)
    curr_rows = _load_snapshot_rows(curr_snapshot_path)

    # 1. Diff klassifizieren und nach emittierbaren Treffern filtern (Config-Store-Gate).
    treffer: list[tuple[diffmod.DiffEvent, str, bool]] = []
    for ev in diffmod.diff(prev_snapshot_path, curr_snapshot_path):
        trigger_key, konfidenz_flag = rulesmod.classify_diff(ev, prev_index)
        if trigger_key is None:
            continue
        if not store.effective_trigger(gebiet_id, trigger_key):
            # Default-aus (T5/T6/PV_ERWEITERUNG) oder pro Gebiet abgeschaltet -> nicht emittieren.
            continue
        treffer.append((ev, trigger_key, konfidenz_flag))

    # 2. Anreicherung in EINEM Batch (nur die Treffer-Einheiten), dann Records bauen.
    enrich = _enrich_units(con, {ev.einheit_nr for ev, _, _ in treffer})
    gesehen: set[tuple[str, str]] = set()   # (einheit, trigger): kein Doppelsignal (z.B. 2x T6,
    for ev, trigger_key, konfidenz_flag in treffer:   # wenn beide Stilllegungsfelder zugleich gesetzt werden)
        schluessel = (ev.einheit_nr, trigger_key)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        rec = _build_record(
            ev,
            trigger_key,
            konfidenz_flag,
            curr_rows.get(ev.einheit_nr),
            enrich.get(ev.einheit_nr),
        )
        # Region-Filter (Befund 14): ein Gebiets-Lauf darf NUR Treffer im PLZ-Cluster emittieren.
        # Ohne bestätigte PLZ (Anreicherung fehlt) wird bei aktivem Filter konservativ verworfen.
        if plz_prefixes and not (rec.plz and any(rec.plz.startswith(p) for p in plz_prefixes)):
            continue
        yield rec
