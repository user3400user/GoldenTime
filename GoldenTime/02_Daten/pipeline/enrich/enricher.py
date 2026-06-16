"""
Anreicherungs-Modul (K7, Briefing §3) — GEKAPSELT, DEFAULT AUS, EIN Schalter.

Reichert einen ``SignalRecord`` um Entscheider/Direktkontakt an und vergibt eine
**Kontakt-Stufe** A/B/C als Qualitätsklasse des Leads:

- ``A`` = Name (Geschäftsführung) **+ Direktkontakt** (Durchwahl)        → höchster Wert
- ``B`` = Name **+ Zentrale** (nur Hauptnummer)
- ``C`` = **nur Firma** bekannt (keine Person, kein Telefon)             → Basis

**Default AUS (ein Schalter):** Ist das Modul ``anreicherung`` im Config-Store (D3) nicht
``enabled``, ist ``enrich`` ein striktes NO-OP — derselbe Record kommt unverändert zurück.
So bleibt die Anreicherung scharf erst „nach Call + Lizenz" (Briefing §3), ohne die übrige
Pipeline zu berühren.

**Phase 1 ohne Scraping (HARTE REGEL: kein Netz):** Der Default-``StubProvider`` beschafft
nichts (``{}``). Bei vorhandener ``entity`` (Firmenname aus dem market_actors-Join) vergibt
der Enricher deterministisch Stufe ``C`` und markiert das am Record über ``flags`` (Tupel)
und ``provenance`` — **kein neues Pflichtfeld** an ``SignalRecord`` (Contract unverändert).
Der echte Provider (nimble, P2) wird in providers.py 1:1 gegen das Protocol getauscht; dann
liefern dieselben Pfade B/A.
"""
from __future__ import annotations

import dataclasses

from ..signal import SignalRecord
from .providers import Provider, StubProvider

# --- Modul-Name im Config-Store (D3, VALID_MODULES = ("anreicherung",)) ----
MODUL_NAME = "anreicherung"

# --- Kontakt-Stufen (Qualitätsklasse des Leads) ----------------------------
STUFE_A = "A"   # Name + Direktkontakt (Durchwahl)
STUFE_B = "B"   # Name + Zentrale
STUFE_C = "C"   # nur Firma bekannt

# Flag-Präfix für die Stufe (taucht in record.flags auf; eindeutig parsebar, da '='-getrennt).
FLAG_STUFE_PREFIX = "ENRICH_STUFE="
# Flag: angereichert, aber ohne beschafften Kontakt (Stub-/Leerpfad) — Marker für QA/Provider-Wechsel.
FLAG_STUB = "ENRICH_STUB_KEIN_KONTAKT"
# Flag: Schalter an, aber Record hatte keine entity -> nichts anzureichern.
FLAG_KEINE_ENTITY = "ENRICH_KEINE_ENTITY"


def _stufe_flag(stufe: str) -> str:
    """Baue das Stufen-Flag (z. B. 'ENRICH_STUFE=C')."""
    return f"{FLAG_STUFE_PREFIX}{stufe}"


def _bestimme_stufe(kontakt: dict) -> str:
    """Leite die Kontakt-Stufe aus den beschafften Feldern ab (A/B/C).

    Reine Funktion über das Provider-dict — defensiv (jeder Schlüssel optional):
    - GF-Name **und** Direktdurchwahl  → A
    - GF-Name **und** (irgend-)Telefon → B
    - sonst (nur Firma / leer)         → C
    """
    gf = (kontakt.get("geschaeftsfuehrer") or "").strip()
    tel = (kontakt.get("telefon") or "").strip()
    tel_typ = (kontakt.get("telefon_typ") or "").strip().lower()
    if gf and tel and tel_typ == "direkt":
        return STUFE_A
    if gf and tel:
        return STUFE_B
    return STUFE_C


def _merge_provenance(alt: str, zusatz: str) -> str:
    """Hänge einen Provenance-Eintrag an (bestehende Kette nicht überschreiben)."""
    alt = (alt or "").strip()
    return f"{alt} | {zusatz}" if alt else zusatz


def enrich(
    record: SignalRecord,
    store=None,
    provider: Provider | None = None,
) -> SignalRecord:
    """Reichere einen ``SignalRecord`` um Entscheider/Kontakt an (gekapselt, default aus).

    Args:
        record:   der anzureichernde SignalRecord (Trigger-Treffer).
        store:    Config-Store (D3). ``None`` → ``config_store.load()`` (1 Snapshot/Lauf).
        provider: Kontakt-Quelle (austauschbar). ``None`` → netzfreier ``StubProvider``.

    Returns:
        Den (ggf. neuen) SignalRecord. **NO-OP**, falls das Modul ``anreicherung`` nicht
        ``enabled`` ist: dann wird der *unveränderte, identische* Record zurückgegeben.

    Hinweis: ``SignalRecord`` ist eine (nicht-frozen) dataclass — wir bauen die angereicherte
    Variante trotzdem mit ``dataclasses.replace`` (kopierend, keine versteckte Mutation des
    Eingangs-Records). Es wird **kein** neues SignalRecord-Feld eingeführt; Stufe + Marker
    leben in ``flags`` (Tupel) und ``provenance`` (Contract bleibt unangetastet).
    """
    # --- EIN Schalter: Modul aus -> striktes NO-OP (identischer Record) -----
    if store is None:
        # Lazy import: Test/Aufrufer kann einen Mini-Store injizieren, ohne Datei-I/O.
        from ..control import config_store as cs
        store = cs.load()
    if not store.is_module_enabled(MODUL_NAME):
        return record

    if provider is None:
        provider = StubProvider()

    # --- Ohne entity gibt es nichts anzureichern (kein market_actors-Join erfolgt) ---
    if not record.entity:
        neue_flags = record.flags + (FLAG_KEINE_ENTITY,)
        return dataclasses.replace(record, flags=neue_flags)

    # --- Kontakt beschaffen (Stub = netzfrei, {}) ---------------------------
    kontakt = provider.lookup(record.entity, record.plz) or {}
    stufe = _bestimme_stufe(kontakt)

    # --- Stufe + Marker an flags/provenance hängen (kein neues Pflichtfeld) -
    neue_flags = record.flags + (_stufe_flag(stufe),)
    quelle = kontakt.get("quelle") or getattr(provider, "QUELLE", "enrich:unbekannt")
    if not kontakt:
        # Stub-/Leerpfad: angereichert, aber kein Kontakt beschafft -> markieren (QA/Provider-Wechsel).
        neue_flags += (FLAG_STUB,)
    prov = _merge_provenance(record.provenance, f"anreicherung[{quelle}]=Stufe {stufe}")

    return dataclasses.replace(record, flags=neue_flags, provenance=prov)
