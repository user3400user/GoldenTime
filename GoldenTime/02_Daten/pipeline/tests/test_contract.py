"""
Daten-Kontrakt / Schema-Drift-Gate (Loop 5, Zielbild Datenqualität 5,0) — stdlib, synthetische DBs.

Deckt ab: gültiges Schema → keine Verletzung; fehlende Tabelle / fehlende Pflicht-Spalte / Katalog-Drift
(``EinheitBetriebsstatus`` ohne Klartext 'In Betrieb') → gemeldet; ``assert_contract`` wirft bei Drift.

Lauf (aus 02_Daten/):  .venv/bin/python -m unittest pipeline.tests.test_contract -v
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.control import contract

SOLAR_COLS = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "Postleitzahl", "Bruttoleistung",
              "Inbetriebnahmedatum", "EinheitBetriebsstatus", "Einspeisungsart", "EegMastrNummer"]


def _build(path: Path, *, solar_cols=None, drop_market=False, betrieb="In Betrieb") -> None:
    sc = solar_cols if solar_cols is not None else SOLAR_COLS
    con = sqlite3.connect(str(path))
    con.execute(f'CREATE TABLE solar_extended ({", ".join(chr(34) + c + chr(34) + " TEXT" for c in sc)})')
    con.execute('CREATE TABLE solar_eeg ("EegMastrNummer" TEXT, "EegInbetriebnahmedatum" TEXT)')
    if not drop_market:
        con.execute('CREATE TABLE market_actors ("MastrNummer" TEXT, "Firmenname" TEXT, "Personenart" TEXT)')
    con.execute('CREATE TABLE storage_extended ("EinheitMastrNummer" TEXT, "AnlagenbetreiberMastrNummer" TEXT)')
    werte = dict.fromkeys(sc, "x")
    if "EinheitBetriebsstatus" in werte:
        werte["EinheitBetriebsstatus"] = betrieb
    spalten = ", ".join(chr(34) + c + chr(34) for c in sc)
    platz = ", ".join("?" for _ in sc)
    con.execute(f"INSERT INTO solar_extended ({spalten}) VALUES ({platz})", [werte[c] for c in sc])
    con.commit()
    con.close()


class TestContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "src.db"

    def tearDown(self):
        self._tmp.cleanup()

    def _con(self):
        con = sqlite3.connect(str(self.path))
        con.row_factory = sqlite3.Row
        return con

    def test_gueltiges_schema_keine_verletzung(self):
        _build(self.path)
        con = self._con()
        try:
            self.assertEqual(contract.verify_contract(con), [])
            contract.assert_contract(con)        # wirft NICHT
        finally:
            con.close()

    def test_fehlende_tabelle(self):
        _build(self.path, drop_market=True)
        con = self._con()
        try:
            probleme = contract.verify_contract(con)
            self.assertTrue(any("'market'" in p for p in probleme), probleme)
        finally:
            con.close()

    def test_fehlende_pflichtspalte(self):
        ohne_plz = [c for c in SOLAR_COLS if c != "Postleitzahl"]
        _build(self.path, solar_cols=ohne_plz)
        con = self._con()
        try:
            probleme = contract.verify_contract(con)
            self.assertTrue(any("solar.plz" in p for p in probleme), probleme)
        finally:
            con.close()

    def test_katalog_drift_betriebsstatus(self):
        # Betriebsstatus als Code '35' statt Klartext 'In Betrieb' (Web-JSON-Drift) -> würde leere Leads liefern.
        _build(self.path, betrieb="35")
        con = self._con()
        try:
            probleme = contract.verify_contract(con)
            self.assertTrue(any("Katalog-Drift" in p for p in probleme), probleme)
        finally:
            con.close()

    def test_assert_wirft_bei_drift(self):
        _build(self.path, drop_market=True)
        con = self._con()
        try:
            with self.assertRaises(contract.ContractError):
                contract.assert_contract(con)
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
