"""
Beweist das Anreicherungs-Modul (K7) — gekapselt, DEFAULT AUS, ein Schalter — OHNE Netzwerk.

Deckt ab:
- Modul AUS (Default): ``enrich`` ist striktes NO-OP (identischer Record).
- Modul AN (injizierter Mini-Config-Store): Stub-Pfad läuft netzfrei, vergibt Stufe C,
  markiert sie an ``flags``/``provenance`` — und mutiert den Eingangs-Record NICHT.
- Stufen-Ableitung A/B/C aus dem Provider-dict (reine Funktion).
- StubProvider erfüllt das ``@runtime_checkable`` Provider-Protocol und ist netzfrei.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_enrich
"""
from __future__ import annotations

import unittest

from pipeline.control import config_store as cs
from pipeline.enrich import (
    STUFE_A,
    STUFE_B,
    STUFE_C,
    Provider,
    StubProvider,
    enrich,
)
from pipeline.enrich.enricher import (
    FLAG_KEINE_ENTITY,
    FLAG_STUB,
    MODUL_NAME,
    _bestimme_stufe,
    _stufe_flag,
)
from pipeline.signal import SignalRecord


def _record(**over) -> SignalRecord:
    """Minimaler, valider SignalRecord (Konfidenz = Pflicht) — Felder per kwargs überschreibbar."""
    base = dict(
        einheit_mastr_nr="SEE_TEST_1",
        betreiber_mastr_nr="ABR_TEST_1",
        trigger_typ="T1",
        datum="2024-01-15",
        konfidenz=0.9,
        buy_relevanz="Testsignal.",
        entity="Müller GmbH",
        plz="48143",
        ort="Münster",
        bundesland="Nordrhein-Westfalen",
        kwp=120.0,
    )
    base.update(over)
    return SignalRecord(**base)


def _store(*, anreicherung_an: bool) -> cs.ConfigStore:
    """Mini-Config-Store rein im Speicher (kein Datei-I/O): nur das Modul-Flag zählt hier."""
    return cs.ConfigStore(
        schema_version=cs.SCHEMA_VERSION,
        triggers={"T1": {"enabled": True, "label": "x"}},
        modules={MODUL_NAME: {"enabled": anreicherung_an, "label": "Anreicherung"}},
        gebiete=(),
    )


class StaticProvider:
    """Test-Provider (netzfrei): gibt ein festes Kontakt-dict zurück — steuert die Stufe."""

    QUELLE = "enrich:test"

    def __init__(self, kontakt: dict):
        self._kontakt = kontakt

    def lookup(self, entity: str, plz):  # noqa: D401 - Protocol-Implementierung
        return dict(self._kontakt)


class TestModulAusIstNoop(unittest.TestCase):
    def test_default_store_modul_aus(self):
        """Geladener Default-Store hat anreicherung=AUS -> enrich ist NO-OP."""
        store = cs.load()  # liest config_store.json (Default: anreicherung disabled)
        self.assertFalse(store.is_module_enabled(MODUL_NAME))
        rec = _record()
        out = enrich(rec, store=store)
        self.assertIs(out, rec)  # identisches Objekt, nichts kopiert/verändert

    def test_mini_store_modul_aus(self):
        rec = _record(flags=("BESTAND_FLAG",))
        out = enrich(rec, store=_store(anreicherung_an=False))
        self.assertIs(out, rec)
        self.assertEqual(out.flags, ("BESTAND_FLAG",))  # Flags unverändert


class TestModulAnStubPfad(unittest.TestCase):
    def setUp(self):
        self.store = _store(anreicherung_an=True)

    def test_stub_vergibt_stufe_c_netzfrei(self):
        """Modul AN + Default-Stub (kein Netz): Stufe C, markiert, Eingang unmutiert."""
        rec = _record(flags=("BESTAND_FLAG",), provenance="qualify")
        out = enrich(rec, store=self.store)  # provider=None -> StubProvider

        # Eingangs-Record bleibt unangetastet (replace kopiert, mutiert nicht).
        self.assertEqual(rec.flags, ("BESTAND_FLAG",))
        self.assertEqual(rec.provenance, "qualify")

        # Stufe C + Stub-Marker an flags; Bestands-Flag erhalten.
        self.assertIn("BESTAND_FLAG", out.flags)
        self.assertIn(_stufe_flag(STUFE_C), out.flags)
        self.assertIn(FLAG_STUB, out.flags)
        # Provenance angehängt (Kette erhalten).
        self.assertIn("qualify", out.provenance)
        self.assertIn("Stufe C", out.provenance)
        self.assertIn("enrich:stub", out.provenance)

    def test_explizit_uebergebener_stub(self):
        out = enrich(_record(), store=self.store, provider=StubProvider())
        self.assertIn(_stufe_flag(STUFE_C), out.flags)
        self.assertIn(FLAG_STUB, out.flags)

    def test_modul_an_ohne_entity(self):
        """Schalter an, aber keine entity -> markiert, aber keine Stufe (nichts anzureichern)."""
        rec = _record(entity=None)
        out = enrich(rec, store=self.store)
        self.assertIn(FLAG_KEINE_ENTITY, out.flags)
        self.assertNotIn(_stufe_flag(STUFE_C), out.flags)

    def test_provider_mit_direktkontakt_gibt_stufe_a(self):
        """Test-Provider (netzfrei) mit GF + Direktdurchwahl -> Stufe A, kein Stub-Marker."""
        prov = StaticProvider(
            {"geschaeftsfuehrer": "Anna Müller", "telefon": "0251-123",
             "telefon_typ": "direkt", "quelle": "enrich:test"}
        )
        out = enrich(_record(), store=self.store, provider=prov)
        self.assertIn(_stufe_flag(STUFE_A), out.flags)
        self.assertNotIn(FLAG_STUB, out.flags)
        self.assertIn("enrich:test", out.provenance)

    def test_provider_mit_zentrale_gibt_stufe_b(self):
        prov = StaticProvider(
            {"geschaeftsfuehrer": "Anna Müller", "telefon": "0251-0",
             "telefon_typ": "zentrale"}
        )
        out = enrich(_record(), store=self.store, provider=prov)
        self.assertIn(_stufe_flag(STUFE_B), out.flags)


class TestStufenAbleitung(unittest.TestCase):
    def test_a_b_c(self):
        self.assertEqual(
            _bestimme_stufe({"geschaeftsfuehrer": "X", "telefon": "1", "telefon_typ": "direkt"}),
            STUFE_A,
        )
        self.assertEqual(
            _bestimme_stufe({"geschaeftsfuehrer": "X", "telefon": "1", "telefon_typ": "zentrale"}),
            STUFE_B,
        )
        self.assertEqual(_bestimme_stufe({}), STUFE_C)
        self.assertEqual(_bestimme_stufe({"geschaeftsfuehrer": "X"}), STUFE_C)  # GF ohne Tel -> C


class TestProviderProtocol(unittest.TestCase):
    def test_stub_erfuellt_protocol(self):
        self.assertIsInstance(StubProvider(), Provider)

    def test_stub_ist_netzfrei_und_leer(self):
        self.assertEqual(StubProvider().lookup("Müller GmbH", "48143"), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
