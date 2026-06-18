"""
Cohort-Trigger T2 — Post-EEG-Jahrgänge + DV-Flag (Komponente 3, Briefing Phase 1, demo-kritisch).

Mechanik (KEIN Snapshot-Diff nötig, reine Stichtags-Kohorte): PV-Einheiten, deren EEG-
**Inbetriebnahmejahr** in den Post-EEG-Jahrgängen (2006/2007 → Förderende 2026/2027) liegt.
Für diese Betreiber steht jetzt die Eigenverbrauchs-/Speicher-Entscheidung an (Buy-Relevanz T2).

Präzision (Phase-0-Befund): ``solar_eeg`` ist 1:1 zu ``solar_extended``; ``EegInbetriebnahmedatum``
ist zu ~99 % befüllt (Review 16.06.: 64.697 Zeilen leer) — wir prüfen das **EEG-Jahr exakt** per LEFT
JOIN über ``EegMastrNummer``. Fehlt der EEG-Datensatz (NULL), fällt der Check auf das Einheiten-
``Inbetriebnahmedatum`` zurück — dieser Fallback ist REAL nötig (kein Schmuck), nicht nur Ausnahme.

Region wird in SQL gefiltert (PLZ-Präfix), kWp-Band ebenfalls (mit Python-Nachfilter, weil
``Bruttoleistung`` als Text vorliegen kann). Speicher-Status kommt aus dem vorberechneten
``StorageIndex`` (ABR-Anywhere); **co-lokal belegte Einheiten (COLOCATED) werden ausgeschlossen** —
dort ist der Speicherbedarf bereits gedeckt (Lead-Spec §2 Regel 8).

Pro Treffer wird ein Lead-Dict mit denselben Schlüsseln wie ``normalize.iter_leads`` gebaut und
über ``signal.from_lead`` zum ``SignalRecord`` gemappt (setzt Konfidenz, DV-Flag ≥100 kWp,
Buy-Relevanz). ``entity`` (Firmenname) bleibt None — den Namen liefert erst der Qualifizierer
(market_actors-Join), nicht der Trigger.
"""
from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from collections.abc import Iterable, Iterator

from .. import config
from .. import db as dbmod
from ..signal import SignalRecord, from_lead
from ..speicher_check import COLOCATED, LABEL, OPERATOR_ELSEWHERE, StorageIndex

log = logging.getLogger(__name__)
HEUTE = dt.date.today()

#: Trigger-Schlüssel im Config-Store (Briefing: T1..T6, DV_FLAG, PV_ERWEITERUNG).
TRIGGER_KEY = "T2"

# Felder, die wir je Solar-Zeile lesen (logische Namen -> config.COL). Spiegelt das
# normalize._SELECT, plus ``eeg_nr`` für den exakten solar_eeg-Join.
_SELECT = (
    "einheit_nr", "abr", "lokation_nr", "betreiber_name", "personenart",
    "plz", "ort", "bundesland", "brutto_kw", "netto_kw", "reg_datum",
    "inbetriebnahme", "eeg_nr", "einspeisung", "betriebsstatus",
    "speicher_gleicher_ort",
)


def _to_float(v: object) -> float | None:
    """Bruttoleistung tolerant nach float (Komma-Dezimal, Whitespace)."""
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _parse_date(v: object) -> dt.date | None:
    if not v:
        return None
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _eeg_jahr(eeg_ibn: dt.date | None, ibn: dt.date | None) -> int | None:
    """Maßgebliches EEG-Jahr: EEG-Inbetriebnahme schlägt Einheiten-IBN (Phase-0-Präzision)."""
    if eeg_ibn is not None:
        return eeg_ibn.year
    if ibn is not None:
        return ibn.year
    return None


def _in_betrieb(status: object) -> bool:
    """Tolerant: hält die Einheit für 'in Betrieb', solange nichts dagegen spricht."""
    if status in (None, ""):
        return True
    s = str(status).strip().lower()
    return s == str(config.BETRIEBSSTATUS_IN_BETRIEB).lower() or s.startswith("in betrieb")


def cohort_signals(
    con: sqlite3.Connection,
    index: StorageIndex,
    *,
    plz_prefixes: tuple[str, ...] = (),
    kwp_min: float = config.KWP_MIN,
    kwp_max: float = config.KWP_MAX,
    jahrgaenge: tuple[int, ...] = config.POST_EEG_JAHRGAENGE,
    region: str | None = None,
    stats: dict | None = None,
) -> Iterator[SignalRecord]:
    """Erzeuge T2-Kaufsignale (Post-EEG-Kohorte) für eine Region.

    SELECT aus ``solar_extended`` (LEFT JOIN ``solar_eeg`` über ``EegMastrNummer``), gefiltert auf
    PLZ-Präfixe + ``EinheitBetriebsstatus='In Betrieb'`` + kWp-Band; behalten werden nur Zeilen,
    deren EEG-Inbetriebnahmejahr in ``jahrgaenge`` liegt (Fallback: Einheiten-IBN-Jahr). Co-lokal
    belegte Einheiten (Speicher am Standort) werden ausgeschlossen.

    Yields je Treffer einen ``SignalRecord`` (trigger_typ='T2', Konfidenz/DV-Flag/Buy-Relevanz aus
    ``from_lead``; ``entity=None`` — Name macht der Qualifizierer).
    """
    if not jahrgaenge:
        return

    solar = dbmod.resolve_table(con, "solar")
    eeg = dbmod.resolve_table(con, "solar_eeg")

    s_cols = dbmod.table_columns(con, solar)
    s_map = dbmod.column_map(s_cols, *_SELECT)
    for need in ("einheit_nr", "abr", "brutto_kw"):
        if not s_map.get(need):
            raise LookupError(
                f"Solar-Tabelle '{solar}' ohne Pflichtspalte '{need}'. Spalten: {s_cols}"
            )

    # EEG-Tabelle: Inbetriebnahmedatum + Join-Schlüssel (EegMastrNummer) auflösen.
    e_cols = dbmod.table_columns(con, eeg)
    e_map = dbmod.column_map(e_cols, "eeg_inbetriebnahme", "eeg_nr")
    eeg_join_ok = bool(s_map.get("eeg_nr") and e_map.get("eeg_nr") and e_map.get("eeg_inbetriebnahme"))

    # SELECT-Liste: alle vorhandenen Solar-Spalten mit Alias = logischer Name.
    present = {lg: c for lg, c in s_map.items() if c}
    select_parts = [f's."{c}" AS {lg}' for lg, c in present.items()]
    sql = "SELECT " + ", ".join(select_parts)
    if eeg_join_ok:
        # EEG-Inbetriebnahmedatum als eigener Alias dazu (exakter Jahres-Check).
        sql += f', e."{e_map["eeg_inbetriebnahme"]}" AS eeg_inbetriebnahme'
    sql += f' FROM "{solar}" AS s'
    if eeg_join_ok:
        sql += (
            f' LEFT JOIN "{eeg}" AS e '
            f'ON s."{s_map["eeg_nr"]}" = e."{e_map["eeg_nr"]}"'
        )

    where: list[str] = []
    params: list[object] = []
    if plz_prefixes:
        if not s_map.get("plz"):
            raise LookupError(
                f"PLZ-Filter verlangt, aber Solar-Tabelle '{solar}' ohne Postleitzahl-Spalte."
            )
        # PLZ-Präfixe sind ziffern-gegated (config_store._validate + cli._plz_prefixes) -> LIKE 'präfix%'
        # braucht KEIN Escape (kein %/_ in einer Ziffern-PLZ möglich). Bewusst kein re.escape.
        where.append("(" + " OR ".join(f's."{s_map["plz"]}" LIKE ?' for _ in plz_prefixes) + ")")
        params.extend(f"{p}%" for p in plz_prefixes)
    if s_map.get("betriebsstatus"):
        # Betriebsstatus ist Klartext ('In Betrieb') — direkt in SQL vorfiltern.
        where.append(f's."{s_map["betriebsstatus"]}" = ?')
        params.append(config.BETRIEBSSTATUS_IN_BETRIEB)
    if where:
        sql += " WHERE " + " AND ".join(where)

    jahrgaenge_set = set(jahrgaenge)
    for row in con.execute(sql, params):
        r = dict(row)
        if not _in_betrieb(r.get("betriebsstatus")):
            continue
        kwp = _to_float(r.get("brutto_kw"))
        if kwp is None or not (kwp_min <= kwp <= kwp_max):
            continue

        # EEG-Jahr exakt: EEG-Inbetriebnahme bevorzugt, Fallback Einheiten-IBN.
        eeg_ibn = _parse_date(r.get("eeg_inbetriebnahme"))
        ibn = _parse_date(r.get("inbetriebnahme"))
        if _eeg_jahr(eeg_ibn, ibn) not in jahrgaenge_set:
            continue

        abr = r.get("abr")
        lokation = r.get("lokation_nr")
        status = index.classify(abr, lokation, r.get("speicher_gleicher_ort"),
                                einheit_nr=r.get("einheit_nr"))
        if status == COLOCATED:
            # Transparenz (Zweit-Review): die stille Ausschluss-Menge zählbar machen, statt nur
            # `continue`. Der Mengen-Report zeigt, wie viele Leads warum verschwinden.
            if stats is not None:
                stats["colocated_ausgeschlossen"] = stats.get("colocated_ausgeschlossen", 0) + 1
            continue  # Speicher am Standort gemeldet -> Bedarf gedeckt -> ausschließen
        if stats is not None:
            stats["kohorte_kandidaten"] = stats.get("kohorte_kandidaten", 0) + 1

        reg = _parse_date(r.get("reg_datum"))

        flags: list[str] = []
        if status == OPERATOR_ELSEWHERE:
            flags.append("PREMIUM_SPEICHER_ANDERER_STANDORT")

        lead = {
            "einheit_mastr_nr": r.get("einheit_nr"),
            "betreiber_mastr_nr": abr,
            "lokation_mastr_nr": lokation,
            "betreiber": None,                 # Name macht der Qualifizierer (market_actors-Join)
            "personenart": r.get("personenart"),
            "plz": r.get("plz"),
            "ort": r.get("ort"),
            "bundesland": r.get("bundesland"),
            "kwp": round(kwp, 1),
            "einspeisung": r.get("einspeisung"),
            "reg_datum": reg.isoformat() if reg else None,
            # Datum = maßgebliche EEG-Inbetriebnahme (Förderende-Bezug), sonst Einheiten-IBN.
            "inbetriebnahme": ibn_eff.isoformat() if (ibn_eff := (eeg_ibn or ibn)) else None,
            "speicher_status": status,
            "speicher_label": LABEL[status],
            "trigger_typ": TRIGGER_KEY,
            "frische_valide": True,            # T2 ist Stichtags-Kohorte, kein Frische-CLAIM
            "flags": flags,
            "geprueft_am": HEUTE.isoformat(),
            "provenance": (
                "MaStR Gesamtdatenexport (dl-de/by-2.0); Trigger T2 Post-EEG "
                f"(EEG-IBN-Jahr {sorted(jahrgaenge_set)}); Speicher-Check: ABR-betreiberweit "
                "+ Lokation; " + HEUTE.isoformat()
            ),
        }
        yield from_lead(lead, region=region)


def dv_flag_count(records: Iterable[SignalRecord]) -> int:
    """Helfer: Anzahl direktvermarktungs-pflichtiger Signale (DV-Flag, ≥100 kWp)."""
    return sum(1 for rec in records if rec.dv_flag)
