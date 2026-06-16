"""
Qualifizierer (Komponente 4, Briefing §3/§7.5) — Anreicherung + Ausschluss-Hierarchie.

Zwei Schritte auf einem Stapel SignalRecords:

(1) **market_actors-Join** (Pflicht, Phase-0-Befund): Betreibername UND PersonenArt liegen
    NICHT auf der Einheit, sondern auf ``market_actors`` (Join Einheit.AnlagenbetreiberMastrNummer
    -> market_actors.MastrNummer). Wir sammeln die betreiber_mastr_nr aller Records, fragen sie
    in Chunks (SQLite-Parameter-Limit) ab und setzen ``record.entity`` = Firmenname.

(2) **Ausschluss-Hierarchie** über pflegbare Substring-Listen (``heuristics/*.txt``, je eine Zeile
    = ein Muster, case-insensitiv gegen den Firmennamen): natürliche Person (e.K.-Caveat — flaggen,
    NICHT hart ausschließen), öffentliche Hand, Energie-/PV-Firmen, Ketten/Filialisten, Vereine.
    Treffer setzen **additiv** ein ``*_PRUEFEN``-Flag in ``record.flags``; der Mensch-QA (qa_gate)
    entscheidet. Wir streichen hier NICHTS hart — Transparenz wie bei den bestehenden normalize-Flags.

Bewusst stdlib-only; die PersonenArt aus dem Join wird in ``record.provenance`` mitgeführt, damit
der QA-Fingerprint (qa_gate) einen PersonenArt-Proxy hat, ohne ein neues Record-Feld zu brauchen.
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from .. import db as dbmod
from ..signal import SignalRecord

log = logging.getLogger(__name__)

# Verzeichnis der pflegbaren Heuristik-Listen (eine Datei je Ausschluss-Kategorie).
HEURISTICS_DIR = Path(__file__).resolve().parent / "heuristics"

# SQLite bindet maximal 999 Parameter je Statement (SQLITE_MAX_VARIABLE_NUMBER) — wir bleiben
# mit 500 deutlich darunter und sind robust gegen ältere Builds.
CHUNK = 500

# Flag-Marker (in record.provenance) für den PersonenArt-Proxy. So bleibt die Information für
# den QA-Fingerprint erhalten, ohne SignalRecord (read-only Contract) um ein Feld zu erweitern.
PA_MARKER = "personenart="

# Heuristik-Datei -> Flag. Eine Datei = eine Ausschluss-Kategorie der Lead-Spec-Hierarchie.
LISTE_FLAGS: dict[str, str] = {
    "oeffentliche_hand.txt": "OEFFENTLICH_PRUEFEN",
    "energie_pv_firmen.txt": "ENERGIE_FIRMA_PRUEFEN",
    "ketten_filialisten.txt": "KETTE_PRUEFEN",
    "vereine_stiftungen.txt": "VEREIN_PRUEFEN",
}

# Flag für natürliche Personen MIT ausgewiesenem Namen (e.K.-Caveat): flaggen, NICHT hart ausschließen.
FLAG_NATUERLICHE_PERSON = "NATUERLICHE_PERSON_PRUEFEN"

# Natürliche Person OHNE im Export ausgewiesenen Namen (MaStR redacted Personennamen).
# Befund (Review 16.06.): 94,6 % aller market_actors tragen die Klasse 'Natürliche Person oder
# Organisation mit Personenbezug', und für genau diese ist der Firmenname leer. Ein pauschales
# QA-Flag würde die Queue fluten (real 202/239 in Münsterland). Diese Fälle sind in Phase 1
# nicht lieferbar (kein Kontaktname) und überwiegend private Dachanlagen -> KEIN QA-Flag
# (nicht reviewbar ohne Namen), separater 'namenlos'-Bucket, via Anreicherung (K7) später erreichbar.
FLAG_PRIVAT_REDACTED = "PRIVATPERSON_REDACTED"


def _load_patterns(dateiname: str) -> tuple[str, ...]:
    """Lese eine Heuristik-Liste: eine Zeile = ein Substring-Muster (klein, getrimmt).

    Kommentar-Zeilen ('#') und Leerzeilen werden übersprungen. Fehlt die Datei, wird
    leer zurückgegeben (Pipeline crasht nicht, nur dieser Filter greift nicht).
    """
    pfad = HEURISTICS_DIR / dateiname
    if not pfad.exists():
        log.warning("Heuristik-Liste %s fehlt — Filter '%s' inaktiv.", pfad, dateiname)
        return ()
    muster: list[str] = []
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        s = zeile.strip()
        if not s or s.startswith("#"):
            continue
        muster.append(s.lower())
    return tuple(muster)


def _load_alle_listen() -> dict[str, tuple[str, ...]]:
    """Alle Heuristik-Listen einmal laden (Datei-Muster je Kategorie)."""
    return {datei: _load_patterns(datei) for datei in LISTE_FLAGS}


def _is_natuerliche_person(personenart: object) -> bool:
    """PersonenArt-Klartext 'Natürliche Person ...' (e.K.-Caveat). Tolerant ggü. Umlaut-Schreibweise."""
    s = str(personenart or "").lower()
    return "natür" in s or "natuer" in s


def _matcht(firmenname: str | None, muster: tuple[str, ...]) -> bool:
    """True, wenn irgendein Substring-Muster (klein) im Firmennamen (klein) vorkommt."""
    if not firmenname:
        return False
    name = firmenname.lower()
    return any(m in name for m in muster)


def _add_flags(record: SignalRecord, *neue: str) -> None:
    """Flags additiv setzen, ohne Duplikate, Reihenfolge stabil (tuple-Contract des Records)."""
    vorhanden = list(record.flags)
    for f in neue:
        if f not in vorhanden:
            vorhanden.append(f)
    record.flags = tuple(vorhanden)


def _merke_personenart(record: SignalRecord, personenart: str | None) -> None:
    """PersonenArt-Proxy in provenance ablegen (für QA-Fingerprint), ohne Record-Feld zu erweitern."""
    if not personenart:
        return
    # Klartext kann '|' enthalten -> auf eine knappe Klasse normalisieren (juristisch/natuerlich).
    klasse = "natuerlich" if _is_natuerliche_person(personenart) else "juristisch"
    marker = f"{PA_MARKER}{klasse}"
    if PA_MARKER in record.provenance:
        return
    record.provenance = (record.provenance + "; " + marker) if record.provenance else marker


def personenart_of(record: SignalRecord) -> str:
    """Den in provenance hinterlegten PersonenArt-Proxy auslesen ('juristisch'|'natuerlich'|'')."""
    for teil in record.provenance.split(";"):
        teil = teil.strip()
        if teil.startswith(PA_MARKER):
            return teil[len(PA_MARKER):]
    return ""


def _join_market_actors(
    records: list[SignalRecord], con: sqlite3.Connection
) -> dict[str, sqlite3.Row]:
    """Batched-Join: betreiber_mastr_nr -> {Firmenname, Personenart} aus market_actors.

    Sammelt die eindeutigen ABR-Nummern, fragt sie in Chunks ab (IN (...)) und gibt eine
    Lookup-Map MastrNummer -> Row zurück. Fehlt die Tabelle/Spalte, wird leer zurückgegeben
    (die Records behalten ihr ggf. schon gesetztes entity).
    """
    abrs = sorted({r.betreiber_mastr_nr for r in records if r.betreiber_mastr_nr})
    if not abrs:
        return {}

    try:
        table = dbmod.resolve_table(con, "market")
    except LookupError:
        log.warning("market_actors-Tabelle nicht gefunden — Name/PersonenArt-Join übersprungen.")
        return {}
    cols = dbmod.table_columns(con, table)
    key_col = dbmod.resolve_column(cols, "markt_mastr_nr")
    name_col = dbmod.resolve_column(cols, "firmenname")
    pa_col = dbmod.resolve_column(cols, "personenart")
    if not key_col:
        log.warning("market_actors '%s' ohne MastrNummer-Spalte — Join übersprungen.", table)
        return {}

    select = [f'"{key_col}" AS markt_mastr_nr']
    if name_col:
        select.append(f'"{name_col}" AS firmenname')
    if pa_col:
        select.append(f'"{pa_col}" AS personenart')
    select_sql = "SELECT " + ", ".join(select) + f' FROM "{table}" WHERE "{key_col}" IN '

    lookup: dict[str, sqlite3.Row] = {}
    for i in range(0, len(abrs), CHUNK):
        chunk = abrs[i:i + CHUNK]
        platzhalter = "(" + ", ".join("?" for _ in chunk) + ")"
        for row in con.execute(select_sql + platzhalter, chunk):
            lookup[row["markt_mastr_nr"]] = row
    return lookup


def enrich_and_qualify(
    records: list[SignalRecord], con: sqlite3.Connection
) -> list[SignalRecord]:
    """Reichere die Records an (Name/PersonenArt-Join) und flagge Ausschluss-Grenzfälle.

    (1) market_actors-Join (batched, Chunks von ~500): setzt ``record.entity`` = Firmenname,
        sofern noch nicht gesetzt, und legt den PersonenArt-Proxy in ``provenance`` ab.
    (2) Ausschluss-Hierarchie über die pflegbaren ``heuristics/*.txt``: natürliche Person und
        Listen-Treffer setzen additiv ``*_PRUEFEN``-Flags. **Keine harte Streichung** — der
        Mensch-QA (qa_gate) entscheidet (Lead-Spec §2, e.K.-Caveat).

    Mutiert die übergebenen Records in-place und gibt dieselbe Liste zurück (bequem zum Verketten).
    """
    listen = _load_alle_listen()
    lookup = _join_market_actors(records, con)

    for record in records:
        row = lookup.get(record.betreiber_mastr_nr) if record.betreiber_mastr_nr else None
        firmenname = record.entity
        personenart: str | None = None
        if row is not None:
            keys = row.keys()
            if "firmenname" in keys and row["firmenname"]:
                firmenname = row["firmenname"]
                # entity nur überschreiben, wenn der Join etwas liefert (Anreicherung).
                record.entity = firmenname
            if "personenart" in keys:
                personenart = row["personenart"]

        _merke_personenart(record, personenart)

        # (2) Hierarchie: natürliche Person. MIT Namen = echter QA-Grenzfall (e.K./benannte GbR);
        # OHNE Namen (redacted) = Privatperson -> Phase 1 nicht lieferbar, KEIN QA (s. FLAG_PRIVAT_REDACTED).
        if personenart is not None and _is_natuerliche_person(personenart):
            _add_flags(record, FLAG_NATUERLICHE_PERSON if record.entity else FLAG_PRIVAT_REDACTED)

        # Listen-Treffer gegen den (angereicherten) Firmennamen.
        for datei, flag in LISTE_FLAGS.items():
            if _matcht(firmenname, listen[datei]):
                _add_flags(record, flag)

    return records
