"""
Tests der Liefer-Schicht (TEIL 5) — Buckets/Betriebe-Zählung, Liefer-Mail, Mengen-Report. stdlib.

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_deliver
"""
from __future__ import annotations

import unittest

from pipeline.deliver import Buckets, liefer_mail, mengen_report
from pipeline.signal import SignalRecord


def _r(see, abr, entity, kwp=120.0, dv=True, detail_id=None):
    return SignalRecord(see, abr, "T2", "2006-01-01", 0.9, "Post-EEG-Jahrgang …",
                        entity=entity, kwp=kwp, plz="48143", ort="Münster",
                        speicher_label="kein Speicher gemeldet", dv_flag=dv, detail_id=detail_id)


class TestBetriebeZaehlung(unittest.TestCase):
    def test_distinct_abr(self):
        # 3 Einheiten, 2 Betriebe (ABR1 doppelt) -> ehrliche Dichte = 2
        b = Buckets("M", lieferbar=[_r("S1", "ABR1", "A GmbH"), _r("S2", "ABR1", "A GmbH"),
                                    _r("S3", "ABR2", "B GmbH")])
        self.assertEqual(b.betriebe(), 2)
        self.assertEqual(len(b.lieferbar), 3)


class TestLieferMail(unittest.TestCase):
    def test_mail_has_stamp_exclusivity_evidence(self):
        b = Buckets("Münsterland",
                    lieferbar=[_r("SEE1", "ABR1", "Wegener Stahlservice GmbH", detail_id=2618388)],
                    pending=[_r("SEE2", "ABR2", "Grenzfall GmbH")],
                    namenlos=[_r("SEE3", "ABR3", None)])
        m = liefer_mail(b, kaeufer="AceFlex", funktion="Speicher-Installateur")
        for token in ["Münsterland", "AceFlex", "1 lieferbare", "1 Betriebe", "Exklusivität",
                      "Speicher-Installateur", "dl-de/by-2.0", "Wegener Stahlservice GmbH",
                      "IndexOeffentlich/2618388", "SEE1", "BESTAND", "DV-pflichtig"]:
            self.assertIn(token, m, token)


class TestMengenReport(unittest.TestCase):
    def test_report_shows_betriebe_and_einheiten(self):
        b = Buckets("Münsterland",
                    lieferbar=[_r("S1", "ABR1", "A"), _r("S2", "ABR1", "A"), _r("S3", "ABR2", "B")],
                    pending=[_r("S4", "ABR4", "X")], colocated_ausgeschlossen=3, roh=10)
        rep = mengen_report([b])
        self.assertIn("Betriebe", rep)
        self.assertIn("Einheiten", rep)
        self.assertIn("BESTAND", rep)
        zeile = next(l for l in rep.splitlines() if l.startswith("Münsterland"))
        # 2 Betriebe, 3 Einheiten, 1 QA-pend, 3 colocated-aus, 10 roh in der Zeile
        for n in ("2", "3", "1", "10"):
            self.assertIn(n, zeile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
