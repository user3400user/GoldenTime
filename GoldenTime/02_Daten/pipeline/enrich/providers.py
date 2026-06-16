"""
Provider-Schicht des Anreicherungs-Moduls (K7) — die austauschbare Kontakt-Quelle.

Ein Provider beschafft zu einer Entity (Firma) deren Direktkontakt: Domain → Impressum →
Geschäftsführung/Telefon. Das eigentliche Scraping ist in Phase 1 **bewusst nicht gebaut**
(rechtliches/lizenztechnisches Thema, Briefing §3: „scharf erst nach Call + Lizenz").
Deshalb hier nur:

- ``Provider`` — das ``@runtime_checkable`` Protocol, an dem die Pipeline hängt (D4-Stil:
  Interface statt zweiter Implementierung; quell-neutral, kennt nur ``entity``/``plz``).
- ``StubProvider`` — die default, netzfreie Implementierung: liefert immer ``{}`` (kein
  Kontakt beschafft). Der Enricher leitet daraus deterministisch Stufe ``C`` ab.

nimble = P2: der echte Web-/Impressums-Provider (Nimble-Scraping-API) wird erst in Phase 2
gegen dieses Protocol implementiert — KEINE Code-/Test-Änderung am Enricher nötig.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    """Kontakt-Quelle für die Anreicherung (austauschbar; D4-Adapter-Prinzip).

    ``lookup`` beschafft zu einer Entity deren Direktkontakt-Felder. Rückgabe ist ein
    flaches dict (leeres dict = „nichts beschafft"). Erwartete, optionale Schlüssel — der
    Enricher liest sie defensiv per ``.get`` und toleriert jeden fehlenden Schlüssel:

    - ``geschaeftsfuehrer`` : str  — Name der/des Entscheider:in (→ Stufe A/B)
    - ``telefon``           : str  — Direktdurchwahl (→ Stufe A) bzw. Zentrale (→ Stufe B)
    - ``telefon_typ``       : str  — "direkt" | "zentrale" (steuert A vs. B)
    - ``domain``            : str  — Firmen-Domain
    - ``impressum_url``     : str  — Beleg-URL des Kontakts
    - ``quelle``            : str  — Provider-Kennung (Provenance)
    """

    def lookup(self, entity: str, plz: str | None) -> dict:
        """Beschaffe Kontaktdaten zu ``entity`` (im PLZ-Kontext ``plz``). ``{}`` = nichts."""
        ...


class StubProvider:
    """Netzfreier Default-Provider — beschafft NICHTS, gibt immer ``{}`` zurück.

    Phase 1: kein Scraping, kein Netzwerk (HARTE REGEL für Tests). Der Stub ist trotzdem ein
    vollwertiger ``Provider`` (erfüllt das ``@runtime_checkable`` Protocol), damit der gesamte
    Enricher-Pfad (Schalter, Stufen-Vergabe, Provenance) bereits jetzt deterministisch und
    ohne Netz testbar ist. Der echte Provider (nimble, P2) wird hier 1:1 ausgetauscht.
    """

    #: Provenance-Kennung — taucht im SignalRecord.provenance auf, damit nachvollziehbar
    #: bleibt, dass diese Anreicherung aus dem Stub (nicht aus echter Quelle) stammt.
    QUELLE = "enrich:stub"

    def lookup(self, entity: str, plz: str | None) -> dict:
        # TODO(P2/nimble): echte Beschaffung Domain -> Impressum -> GF/Telefon implementieren.
        #   Bis dahin bewusst leer: „kein Kontakt beschafft" -> Enricher vergibt Stufe C.
        return {}
