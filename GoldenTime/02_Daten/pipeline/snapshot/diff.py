"""
Snapshot-Diff (D2) — Set-/Feld-Diff zweier dated „Skinny"-Snapshots.

Diff über ``einheit_nr`` (PRIMARY KEY) als Set-Diff plus Feldvergleich der vier
signal-tragenden Felder (abr, brutto_kw, inbetriebnahme, beide Stilllegungs-Daten):

  NEW_UNIT       Einheit in curr, nicht in prev  -> Zubau (T1/T4/PV_ERWEITERUNG-Kandidat)
  REMOVED        Einheit in prev, nicht in curr  -> Abgang (i. d. R. kein Signal, s. rules)
  FIELD_CHANGED  Einheit in beiden, Feld geändert -> abr=T5, Stilllegung=T6, brutto_kw=Reduzierung

Float-tolerant (kWp über Epsilon) und Datum-/Leerstring-tolerant (None == "" wird NICHT
als Änderung gewertet), damit Rauschen aus Formatierungs-/Casing-Unterschieden keinen
False-Positive-Trigger erzeugt.

stdlib-only (sqlite3, dataclasses). Lädt beide Snapshots als Dicts (einheit_nr -> Zeile);
bei <~9 Mio. schlanken Zeilen ist das in-memory handhabbar (vgl. speicher_check-Index).
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Change-Types
NEW_UNIT = "NEW_UNIT"
REMOVED = "REMOVED"
FIELD_CHANGED = "FIELD_CHANGED"

# Geladene Zeile = kompaktes TUPEL statt dict je Zeile (Zweit-Review: senkt Peak-RAM des Wochen-Diffs
# bei 8,8 Mio Zeilen x2 von ~12 GB auf ~4 GB -> kein OOM-Risiko auf dem Laptop). Reihenfolge MUSS
# zum SELECT in _load passen.
_T_TRAEGER, _T_ABR, _T_KW, _T_IBN, _T_STE, _T_STV = range(6)
# Vergleichsfeld-Name -> Tupel-Index. rules.py prüft ev.field als STRING, daher Namen behalten.
# brutto_kw wird float-tolerant verglichen, der Rest als normalisierter String.
_FELD_INDEX: dict[str, int] = {
    "abr": _T_ABR,
    "brutto_kw": _T_KW,
    "inbetriebnahme": _T_IBN,
    "datum_stilllegung_endg": _T_STE,
    "datum_stilllegung_vorueb": _T_STV,
}
_VERGLEICHSFELDER: tuple[str, ...] = tuple(_FELD_INDEX)

# kWp gilt erst ab dieser Differenz als geändert (Rundungs-/Formatrauschen abfangen).
_KW_EPSILON = 0.05


@dataclass(frozen=True)
class DiffEvent:
    """Ein Unterschied zwischen prev und curr für GENAU eine Einheit.

    ``change_type`` = NEW_UNIT | REMOVED | FIELD_CHANGED. Bei FIELD_CHANGED sind
    ``field``/``old``/``new`` gesetzt (ein Event je geändertem Feld); bei NEW_UNIT/REMOVED
    bleiben sie None. ``traeger`` und ``abr`` stammen aus der maßgeblichen Seite
    (curr bei NEW_UNIT/FIELD_CHANGED, prev bei REMOVED) für die nachgelagerte Regel.
    """

    einheit_nr: str
    traeger: str | None
    abr: str | None
    change_type: str
    field: str | None = None
    old: object = None
    new: object = None


def _load(path: Path | str) -> dict[str, tuple]:
    """Snapshot als {einheit_nr: (traeger, abr, brutto_kw, inbetriebnahme, st_endg, st_vorueb)} laden.

    Kompaktes Tupel (nur die Diff-Felder) statt dict je Zeile — deutlich weniger Peak-RAM beim
    Wochen-Diff über ~8,8 Mio Zeilen. einheit_nr ist der Schlüssel (PK -> Set-Diff-Basis).
    """
    con = sqlite3.connect(str(path))
    try:
        return {
            r[0]: r[1:]
            for r in con.execute(
                "SELECT einheit_nr, traeger, abr, brutto_kw, inbetriebnahme, "
                "datum_stilllegung_endg, datum_stilllegung_vorueb FROM snapshot")
        }
    finally:
        con.close()


def _norm(v: object) -> str | None:
    """String-Normalisierung für den Feldvergleich: None und '' sind gleich (kein Diff)."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _kw(v: object) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _field_changed(field: str, old: object, new: object) -> bool:
    """True, wenn sich ``field`` echt geändert hat (float-/leerstring-tolerant)."""
    if field == "brutto_kw":
        a, b = _kw(old), _kw(new)
        if a is None and b is None:
            return False
        if a is None or b is None:
            return True
        return abs(a - b) > _KW_EPSILON
    return _norm(old) != _norm(new)


def diff(prev_path: Path | str, curr_path: Path | str) -> Iterator[DiffEvent]:
    """Iteriere die DiffEvents zwischen zwei Snapshots (prev -> curr).

    Reihenfolge: erst alle NEW_UNIT/FIELD_CHANGED (über curr iteriert), dann REMOVED.
    Pro geändertem Feld ein eigenes FIELD_CHANGED-Event — so kann ``rules`` jedes Feld
    isoliert klassifizieren (eine Einheit kann z. B. gleichzeitig T5 und T6 auslösen).
    """
    prev = _load(prev_path)
    curr = _load(curr_path)

    for einheit, c in curr.items():
        p = prev.get(einheit)
        if p is None:
            yield DiffEvent(einheit, c[_T_TRAEGER], c[_T_ABR], NEW_UNIT)
            continue
        for field, idx in _FELD_INDEX.items():
            old, new = p[idx], c[idx]
            if _field_changed(field, old, new):
                yield DiffEvent(einheit, c[_T_TRAEGER], c[_T_ABR], FIELD_CHANGED, field, old, new)

    for einheit, p in prev.items():
        if einheit not in curr:
            yield DiffEvent(einheit, p[_T_TRAEGER], p[_T_ABR], REMOVED)
