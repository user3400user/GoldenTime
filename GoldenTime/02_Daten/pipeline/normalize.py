"""
Normalisierung: Roh-Solar-Zeile (open-mastr) -> Lead-Objekt (Lead-Spec / Architektur §4).

Erzeugt das normalisierte Lead-Dict mit stabilen Schlüsseln, Speicher-Status (aus dem
ABR-Anywhere-Check), Trigger-Typ und der Frische-Validierung aus R3 §7b
(``Inbetriebnahmedatum`` validiert den Frische-CLAIM; ``reg_datum`` allein genügt nicht).

Bewusst NICHT enthalten: die volle Ausschluss-Hierarchie aus Lead-Spec §2 (öffentliche
Hand, Konzern, Energie-Firmen …) — das ist der Schritt QUALIFIZIEREN und folgt separat.
Hier werden Betriebsstatus/kWp/Region/Speicher gefiltert und PersonenArt nur GEFLAGGT
(e.K.-Caveat -> Mensch-QA entscheidet), nicht hart ausgeschlossen.
"""
from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from typing import Iterator

from . import config
from . import db as dbmod
from .speicher_check import COLOCATED, LABEL, OPERATOR_ELSEWHERE, StorageIndex

log = logging.getLogger(__name__)
HEUTE = dt.date.today()

# Felder, die wir je Solar-Zeile lesen wollen (logische Namen -> config.COL).
_SELECT = (
    "einheit_nr", "abr", "lokation_nr", "betreiber_name", "personenart",
    "plz", "ort", "bundesland", "brutto_kw", "netto_kw", "reg_datum",
    "inbetriebnahme", "eeg_inbetriebnahme", "einspeisung", "betriebsstatus",
    "speicher_gleicher_ort",
)


def _to_float(v: object) -> float | None:
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


def _year(d: dt.date | None) -> int | None:
    return d.year if d else None


def derive_trigger(reg: dt.date | None, ibn: dt.date | None,
                   eeg_ibn: dt.date | None, speicher_status: str) -> str:
    """T1 frische PV o. Speicher · T2 Post-EEG 2006/07 · T3 Bestand o. Speicher."""
    eeg_year = _year(eeg_ibn) or _year(ibn)
    if eeg_year in config.POST_EEG_JAHRGAENGE:
        return "T2"
    frisch = reg is not None and (HEUTE - reg).days <= config.FRISCHE_FENSTER_TAGE
    if frisch and speicher_status != COLOCATED:
        return "T1"
    return "T3"


def freshness_check(reg: dt.date | None, ibn: dt.date | None) -> tuple[bool, str | None]:
    """R3 §7b: reg_datum allein ist kein Neubau-Beweis (Nachregistrierung bis 2021).

    Returns (valide, warnung). valide=False, wenn die Inbetriebnahme deutlich vor der
    Registrierung liegt (Nachregistrierungs-Verdacht).
    """
    if reg is None:
        return False, "kein Registrierungsdatum"
    if ibn is None:
        return True, "Inbetriebnahmedatum fehlt — Frische nicht validierbar"
    luecke = (reg - ibn).days
    if luecke > config.IBN_REG_LUECKE_WARN_TAGE:
        return False, (f"IBN {ibn} liegt {luecke} Tage vor Registrierung {reg} "
                       f"— Nachregistrierungs-Verdacht")
    return True, None


def _is_natuerliche_person(personenart: object) -> bool:
    return "natür" in str(personenart or "").lower() or "natuer" in str(personenart or "").lower()


def _in_betrieb(status: object) -> bool:
    """Tolerant: hält Einheit für 'in Betrieb', solange nichts dagegen spricht."""
    if status in (None, ""):
        return True  # unbekannt nicht wegwerfen
    s = str(status).strip().lower()
    return s == str(config.BETRIEBSSTATUS_IN_BETRIEB) or s.startswith("in betrieb")


def iter_leads(
    con: sqlite3.Connection,
    index: StorageIndex,
    *,
    plz_prefixes: tuple[str, ...] = (),
    bundesland: str = "",
    kwp_min: float = config.KWP_MIN,
    kwp_max: float = config.KWP_MAX,
    nur_in_betrieb: bool = True,
    limit: int | None = None,
    solar_table: str | None = None,
) -> Iterator[dict]:
    """Iteriere klassifizierte Solar-Leads für eine Region.

    Region (plz_prefixes oder bundesland) wird in SQL gefiltert; kWp/Status/Speicher in
    Python. ``ausschluss_grund`` markiert co-lokal-belegte (Speicher am Ort) statt sie
    still zu verwerfen — Transparenz wie bei den Ketten-Flags.
    """
    if not plz_prefixes and not bundesland and limit is None:
        raise ValueError(
            "Ohne Region (plz_prefixes/bundesland) bitte ein limit setzen — "
            "die Solar-Tabelle hat ~6,2 Mio. Zeilen."
        )

    table = solar_table or dbmod.resolve_table(con, "solar")
    cols = dbmod.table_columns(con, table)
    cmap = dbmod.column_map(cols, *_SELECT)
    for need in ("einheit_nr", "abr", "brutto_kw"):
        if not cmap.get(need):
            raise LookupError(
                f"Solar-Tabelle '{table}' ohne Pflichtspalte '{need}'. Spalten: {cols}"
            )

    present = {lg: c for lg, c in cmap.items() if c}
    sql = "SELECT " + ", ".join(f'"{c}" AS {lg}' for lg, c in present.items()) + f' FROM "{table}"'

    where: list[str] = []
    params: list[object] = []
    if plz_prefixes:
        if not cmap.get("plz"):
            raise LookupError(f"PLZ-Filter verlangt, aber Solar-Tabelle '{table}' ohne Postleitzahl-Spalte.")
        where.append("(" + " OR ".join(f'"{cmap["plz"]}" LIKE ?' for _ in plz_prefixes) + ")")
        params.extend(f"{p}%" for p in plz_prefixes)
    if bundesland and cmap.get("bundesland"):
        where.append(f'"{cmap["bundesland"]}" = ?')
        params.append(bundesland)
    if where:
        sql += " WHERE " + " AND ".join(where)
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))

    emitted = 0
    for row in con.execute(sql, params):
        r = dict(row)
        if nur_in_betrieb and not _in_betrieb(r.get("betriebsstatus")):
            continue
        kwp = _to_float(r.get("brutto_kw"))
        if kwp is None or not (kwp_min <= kwp <= kwp_max):
            continue

        abr = r.get("abr")
        lokation = r.get("lokation_nr")
        status = index.classify(abr, lokation, r.get("speicher_gleicher_ort"))

        reg = _parse_date(r.get("reg_datum"))
        ibn = _parse_date(r.get("inbetriebnahme"))
        eeg_ibn = _parse_date(r.get("eeg_inbetriebnahme"))
        trigger = derive_trigger(reg, ibn, eeg_ibn, status)
        fresh_ok, fresh_warn = freshness_check(reg, ibn)

        flags: list[str] = []
        if status == OPERATOR_ELSEWHERE:
            flags.append("PREMIUM_SPEICHER_ANDERER_STANDORT")
        if _is_natuerliche_person(r.get("personenart")):
            flags.append("NATUERLICHE_PERSON_PRUEFEN")  # e.K.-Caveat: QA statt Auto-Ausschluss
        if not fresh_ok:
            flags.append("FRISCHE_WARNUNG")

        yield {
            "einheit_mastr_nr": r.get("einheit_nr"),
            "betreiber_mastr_nr": abr,
            "lokation_mastr_nr": lokation,
            "betreiber": r.get("betreiber_name"),
            "personenart": r.get("personenart"),
            "plz": r.get("plz"),
            "ort": r.get("ort"),
            "bundesland": r.get("bundesland"),
            "kwp": round(kwp, 1),
            "einspeisung": r.get("einspeisung"),
            "reg_datum": reg.isoformat() if reg else None,
            "inbetriebnahme": ibn.isoformat() if ibn else None,
            "speicher_status": status,
            "speicher_label": LABEL[status],
            "trigger_typ": trigger,
            "frische_valide": fresh_ok,
            "frische_warnung": fresh_warn,
            "ausschluss_grund": "speicher_colocated" if status == COLOCATED else None,
            "flags": flags,
            "geprueft_am": HEUTE.isoformat(),
            "provenance": ("MaStR Gesamtdatenexport (dl-de/by-2.0); "
                           "Speicher-Check: ABR-betreiberweit + Lokation; " + HEUTE.isoformat()),
        }
        emitted += 1
        if limit is not None and emitted >= limit:
            break
