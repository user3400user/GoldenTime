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
import re
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
    "immobilien.txt": "IMMOBILIEN_PRUEFEN",
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

# §2.4: Rechtsform SE/AG als Konzern-Warnsignal -> KETTE_PRUEFEN (manuell bestätigen).
_RECHTSFORM_SE_AG = re.compile(r"\b(se|ag)\b", re.IGNORECASE)

# market_actors.Rechtsform (Katalog-Klartext, exakt) -> QA-Flag. Die Rechtsform ist die WAHRHEIT zur
# Vereins-/Gemeinnützigkeits-/öffentlich-rechtlichen/Konzern-Form, die der FIRMENNAME oft nicht trägt
# (R3-Befund: 'Seniorenhilfe St. Franziskus GmbH' = gGmbH, 'INI' = e.V. — beide rutschten namensbasiert
# durch). Werte empirisch aus dem market_actors-Katalog. Treffer -> Flag (Mensch-QA), NIE harte Streichung.
_RECHTSFORM_FLAG: dict[str, str] = {
    "e.v.": "VEREIN_PRUEFEN",
    "e. v.": "VEREIN_PRUEFEN",
    "ggmbh": "VEREIN_PRUEFEN",
    "eg": "VEREIN_PRUEFEN",
    "stiftung des privatrechts": "VEREIN_PRUEFEN",
    "stiftung des öffentlichen rechts": "OEFFENTLICH_PRUEFEN",
    "vvag": "VEREIN_PRUEFEN",
    "körperschaft des öffentlichen rechts": "OEFFENTLICH_PRUEFEN",
    "anstalt des öffentlichen rechts": "OEFFENTLICH_PRUEFEN",
    "eigenbetrieb": "OEFFENTLICH_PRUEFEN",
}
# Aktien-/Konzernformen (auch Misch-/KGaA) tokenbasiert -> KETTE. Fängt AG/SE/KGaA, AG & Co. KGaA,
# SE ＆ Co. KG, GmbH & Co. KGaA ohne jede Variante einzeln pflegen zu müssen (R4-Befund).
_RECHTSFORM_KONZERN = re.compile(r"\b(ag|se|kgaa)\b")


def _rechtsform_flag(rechtsform: object) -> str | None:
    """Katalog-Rechtsform -> QA-Flag, sonst None.

    Normalisiert robust gegen Katalog-Drift (R4-Befund): Voll-Breiten-'＆' -> '&', interner
    Whitespace kollabiert (der echte Wert 'Stiftung  des öffentlichen Rechts' trägt ZWEI Leerzeichen),
    getrimmt + lower. Erst exakter Verein/öffentlich-Treffer, dann tokenbasiert AG/SE/KGaA -> KETTE.
    """
    s = re.sub(r"\s+", " ", str(rechtsform or "").replace("＆", "&")).strip().lower()
    if not s:
        return None
    if s in _RECHTSFORM_FLAG:
        return _RECHTSFORM_FLAG[s]
    if _RECHTSFORM_KONZERN.search(s):
        return "KETTE_PRUEFEN"
    return None

# §2.1: Firmen-/Rechtsform-/Branchen-Tokens, deren Vorkommen einen Namen als FIRMA (nicht
# bloße Person) ausweist — Gegenprobe zum Personennamen-Muster.
_FIRMA_TOKEN = re.compile(
    r"\b(gmbh|mbh|ohg|kg|gbr|ug|ag|se|e\.?\s?k|e\.?\s?v|e\.?\s?g|eg|inh|co|"
    r"gesellschaft|verwaltung|firma|stiftung|verein|hof|bau|technik|service|"
    r"handel|logistik|transport|energie|solar|immobil|agrar|metall|stahl|holz|"
    r"dach|garten|elektro|kraft|werk|gut|mühle)\b",
    re.IGNORECASE,
)
# Ein einzelnes Namens-Token: Großbuchstabe + Kleinbuchstaben (mit optionalem Bindestrich-Teil).
_NAME_TOKEN = re.compile(r"^[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?$")


def _looks_like_person(firmenname: str | None) -> bool:
    """§2.1: sieht der Name wie ein bloßer Personenname aus ('Vorname Nachname', evtl. mehrere
    Personen via '/', 'und', '&') OHNE Rechtsform/Firmen-/Branchen-Token und ohne Ziffer?

    Konservativ + auf Flag-zu-QA ausgelegt (e.K.-Caveat): lieber einen Grenzfall flaggen als
    durchrutschen lassen. Belege der Zweit-Review: 'Oliver Topmöller', 'Jan Ritschny',
    'Christina Rahmann/Astrid Schröter', 'Hildegard Schulze-Icking und Gerd …'.
    """
    if not firmenname:
        return False
    # Zweit-Review: Voll-Breiten-Ampersand '＆' (U+FF06) ist im Export 22x häufiger als ASCII '&'
    # -> normalisieren, sonst rutschen 'Krühler ＆ Sander'-Personengesellschaften ungeflaggt durch.
    n = firmenname.strip().replace("＆", "&")
    if any(c.isdigit() for c in n) or _FIRMA_TOKEN.search(n):
        return False
    # Trenner: / & , sowie ' und ' / ' u. ' (Letzteres mit korrekter Wortgrenze — \bu\.\b matchte nie,
    # weil auf '.' ein Leerzeichen folgt). 'Linus u. Astrid Olbrich' wird so als Person erkannt.
    teile = [t for t in re.split(r"\s*[/&,]\s*|\s+(?:und|u\.)\s+", n) if t.strip()]
    if not (1 <= len(teile) <= 3):
        return False
    for teil in teile:
        woerter = teil.split()
        if not (1 <= len(woerter) <= 3) or not all(_NAME_TOKEN.match(w) for w in woerter):
            return False
    # mind. eine 'Vorname Nachname'-Struktur (>=2 Wörter) ODER mehrere Personen-Teile.
    return len(teile) > 1 or any(len(t.split()) >= 2 for t in teile)


def _load_patterns(dateiname: str) -> tuple:
    """Lese eine Heuristik-Liste: eine Zeile = ein Muster, getrimmt. Präfix 're:' = Regex
    (Wortgrenze für kurze/kollisionsanfällige Tokens), sonst Substring (klein).

    Kommentar-Zeilen ('#') und Leerzeilen werden übersprungen. Fehlt die Datei, wird leer
    zurückgegeben (Pipeline crasht nicht, nur dieser Filter greift nicht). Rückgabe: Tupel von
    ``("sub", lower-str)`` bzw. ``("re", compiled)``.
    """
    pfad = HEURISTICS_DIR / dateiname
    if not pfad.exists():
        log.warning("Heuristik-Liste %s fehlt — Filter '%s' inaktiv.", pfad, dateiname)
        return ()
    muster: list[tuple] = []
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        s = zeile.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("re:"):
            try:
                muster.append(("re", re.compile(s[3:].strip(), re.IGNORECASE)))
            except re.error as e:
                log.warning("Ungültiges Regex in %s: %r (%s)", dateiname, s, e)
        else:
            muster.append(("sub", s.lower()))
    return tuple(muster)


def _load_alle_listen() -> dict[str, tuple]:
    """Alle Heuristik-Listen einmal laden (Datei-Muster je Kategorie)."""
    return {datei: _load_patterns(datei) for datei in LISTE_FLAGS}


def _is_natuerliche_person(personenart: object) -> bool:
    """PersonenArt-Klartext 'Natürliche Person ...' (e.K.-Caveat). Tolerant ggü. Umlaut-Schreibweise."""
    s = str(personenart or "").lower()
    return "natür" in s or "natuer" in s


def _matcht(firmenname: str | None, muster: tuple) -> bool:
    """True, wenn irgendein Muster (Substring oder Regex) auf den Firmennamen passt."""
    if not firmenname:
        return False
    name = firmenname.lower()
    for kind, pat in muster:
        if kind == "sub":
            if pat in name:
                return True
        elif pat.search(firmenname):     # Regex trägt IGNORECASE
            return True
    return False


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


# e.K./Einzelunternehmen-Namensmuster (Eingetragener Kaufmann = juristisch eine natürliche Person).
# Fängt 'Müller Elektro e.K.' / 'Schmidt e. Kfm.' AUCH dann, wenn der market_actors-Join keine
# PersonenArt liefert (Join-Ausfall) — die Rechtsform e.K. steht oft nur im Namen, nicht in der
# (fehlenden) PersonenArt. Konservativ: verlangt 'e.' MIT Punkt, damit 'Eckert'/'Beckmann' nicht treffen.
_EK_NAME = re.compile(r"\be\.\s?k(?:fm|fr)?\.?\b|einzelkaufm|einzelunternehm", re.IGNORECASE)


def ist_natuerliche_person(record: SignalRecord) -> bool:
    """Harte e.K./natürliche-Person-Erkennung für das qa-unabhängige Liefer-Gate (S0 · §0 · I7).

    Liefert True, wenn der Record eine natürliche Person / e.K. ist — über DREI robuste Wege, damit
    ein einzelner Ausfall den DSGVO-/Rechts-relevanten Fall NICHT durchrutschen lässt (Bisnode/UODO:
    Resale von Register-Daten über Einzelgewerbetreibende löst die Art-14-Informationspflicht aus):
      1. PersonenArt-Proxy (market_actors-Join) == 'natuerlich',
      2. das additive ``FLAG_NATUERLICHE_PERSON`` aus ``enrich_and_qualify`` (Namensmuster/PersonenArt),
      3. ein e.K.-/Einzelunternehmen-Namensmuster (greift auch ohne PersonenArt, Join-Ausfall).

    Bewusst konservativ (lieber eine Firma fälschlich aus der Lieferung halten als eine e.K. ausliefern)
    — die Grenze ist eine Rechts-Invariante (§0), keine Qualitäts-Heuristik. Greift ERST, wenn der
    Politik-Schalter ``natuerliche_personen_freigegeben`` AUS ist (Default; bis Anwalts-Verdikt).
    """
    if personenart_of(record) == "natuerlich":
        return True
    if FLAG_NATUERLICHE_PERSON in record.flags:
        return True
    return bool(record.entity and _EK_NAME.search(record.entity))


def ist_natuerliche_person_name(name: str | None) -> bool:
    """e.K./Einzelunternehmen NUR am Namen erkennen — für dict-basierte Legacy-Pfade (cmd_leads),
    die keinen SignalRecord mit PersonenArt-Proxy/Flags tragen."""
    return bool(name and _EK_NAME.search(name))


def partition_natuerliche(records: list, nat_frei: bool) -> tuple[list, list]:
    """Der EINE e.K./§0-Choke-Point: teile SignalRecords in (behalten, gesperrt).

    ``nat_frei=True`` (Politik-Schalter an, nach Anwalts-Freigabe) → alles behalten. Sonst werden
    natürliche Personen / e.K. (``ist_natuerliche_person``) qa-unabhängig in ``gesperrt`` umgeleitet.
    JEDER kundenfähige Funnel (run_region · cmd_signals · cmd_diff) MUSS diese Funktion durchlaufen,
    damit kein neuer Funnel den I7-Hartfilter wieder vergisst (Refute HIGH: cmd_diff lief ungefiltert).
    """
    if nat_frei:
        return list(records), []
    behalten: list = []
    gesperrt: list = []
    for r in records:
        (gesperrt if ist_natuerliche_person(r) else behalten).append(r)
    return behalten, gesperrt


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
    rf_col = dbmod.resolve_column(cols, "rechtsform")
    if not key_col:
        log.warning("market_actors '%s' ohne MastrNummer-Spalte — Join übersprungen.", table)
        return {}

    select = [f'"{key_col}" AS markt_mastr_nr']
    if name_col:
        select.append(f'"{name_col}" AS firmenname')
    if pa_col:
        select.append(f'"{pa_col}" AS personenart')
    if rf_col:
        select.append(f'"{rf_col}" AS rechtsform')
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
        rechtsform: str | None = None
        if row is not None:
            keys = row.keys()
            if "firmenname" in keys and row["firmenname"]:
                firmenname = row["firmenname"]
                # entity nur überschreiben, wenn der Join etwas liefert (Anreicherung).
                record.entity = firmenname
            if "personenart" in keys:
                personenart = row["personenart"]
            if "rechtsform" in keys:
                rechtsform = row["rechtsform"]

        _merke_personenart(record, personenart)

        # (2a) Spezifische Listen-Hierarchie (öffentl. Hand / Energie-PV / Kette-Konzern / Verein /
        # Immobilien) + §2.4 SE/AG-Konzern-Warnung. Diese präzisen Regeln haben VORRANG vor dem
        # groben Namensmuster (sonst bekäme 'Klinikum Stuttgart' fälschlich AUCH ein Personen-Flag).
        liste_griff = False
        for datei, flag in LISTE_FLAGS.items():
            if _matcht(firmenname, listen[datei]):
                _add_flags(record, flag)
                liste_griff = True
        if record.entity and _RECHTSFORM_SE_AG.search(record.entity):
            _add_flags(record, "KETTE_PRUEFEN")
            liste_griff = True
        # (2a') Rechtsform-Feld (market_actors) — fängt Verein/gemeinnützig/öffentl./Konzern, die der
        # Name NICHT zeigt (gGmbH/e.V./KöR). Hat wie die Listen Vorrang vor dem groben Personenmuster.
        rf_flag = _rechtsform_flag(rechtsform)
        if rf_flag:
            _add_flags(record, rf_flag)
            liste_griff = True

        # (2b) §2.1 natürliche Person: PersonenArt-Klasse (immer) ODER bloßer Personenname (auch bei
        # PersonenArt='Organisation' — Zweit-Review-Befund), Letzteres nur, wenn keine spezifischere
        # Regel schon griff. MIT Namen -> QA (e.K.-Caveat); OHNE Namen (redacted) -> Privatperson-Bucket.
        by_pa = personenart is not None and _is_natuerliche_person(personenart)
        by_name = (not liste_griff) and _looks_like_person(record.entity)
        if by_pa or by_name:
            _add_flags(record, FLAG_NATUERLICHE_PERSON if record.entity else FLAG_PRIVAT_REDACTED)

    return records
