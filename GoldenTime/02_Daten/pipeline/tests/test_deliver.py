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

    def test_mail_konfidenz_disclaimer_honest(self):
        # R0-Fix (Konfidenz-Ehrlichkeit): die Zahl darf nicht nackt als '90%' lesbar sein.
        b = Buckets("Münsterland", lieferbar=[_r("SEE1", "ABR1", "A GmbH", detail_id=2618388)])
        m = liefer_mail(b)
        self.assertIn("nicht kalibriert", m)        # Inline-Label an der Konfidenz-Zahl
        self.assertIn("KEINE kalibrierte", m)        # Fuss-Disclaimer

    def test_mail_evidenz_satz_konditional(self):
        # R0-Fix: '1 Klick' nur wenn ALLE einen Direktlink haben; sonst Such-Link offen ausweisen.
        voll = Buckets("M", lieferbar=[_r("SEE1", "ABR1", "A GmbH", detail_id=2618388)])
        self.assertIn("1 Klick", liefer_mail(voll))
        teil = Buckets("M", lieferbar=[_r("SEE1", "ABR1", "A GmbH", detail_id=2618388),
                                       _r("SEE2", "ABR2", "B GmbH", detail_id=None)])
        self.assertIn("Such-Link", liefer_mail(teil))


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

    def test_sigma_betriebe_distinct_ueber_gebiete(self):
        # R0-Fix (Doppelzählung): ABR1 in BEIDEN Gebieten -> Σ-Betriebe distinct = 2, nicht 2+1=3.
        b1 = Buckets("Münsterland", lieferbar=[_r("S1", "ABR1", "A GmbH"), _r("S2", "ABR2", "B GmbH")], roh=2)
        b2 = Buckets("Osnabrück", lieferbar=[_r("S3", "ABR1", "A GmbH")], roh=1)
        rep = mengen_report([b1, b2])
        sigma = next(l for l in rep.splitlines() if l.strip().startswith("Σ"))
        self.assertRegex(sigma, r"Σ\s+2\s+3")   # distinct Betriebe=2, Einheiten=3 (2+1)

    def test_report_rejected_spalte_und_reconciliation(self):
        # R0-Fix: 'rejected' als eigene Spalte + Reconciliation-Hinweis (Buckets summieren auf 'roh').
        b = Buckets("Münsterland", lieferbar=[_r("S1", "ABR1", "A")], rejected=[_r("S2", "ABR2", "B")], roh=2)
        rep = mengen_report([b])
        self.assertIn("rejected", rep)
        self.assertIn("Reconciliation", rep)


class TestResolverCacheOnly(unittest.TestCase):
    def test_cache_only_wendet_cache_an_ohne_netz(self):
        # R4 (--offline): gecachte Direktlinks anwenden, bei Miss None — NIE eine Session öffnen.
        import pathlib
        import tempfile
        from pipeline.control import state
        from pipeline.enrich.mastr_resolve import EvidenzResolver
        with tempfile.TemporaryDirectory() as d:
            con = state.connect(pathlib.Path(d) / "s.db")
            con.execute("INSERT INTO mastr_url_cache(einheit_mastr_nr, detail_id, resolved_at) "
                        "VALUES('SEE1', 12345, '2026-06-16')")
            con.commit()
            r = EvidenzResolver(cache_con=con)
            self.assertEqual(r.resolve_id("SEE1", cache_only=True), 12345)   # Cache-Treffer
            self.assertIsNone(r.resolve_id("SEE_MISS", cache_only=True))     # Miss -> None
            self.assertIsNone(r._session)                                    # Session NIE geöffnet
            con.close()


class TestRecordMetrics(unittest.TestCase):
    def test_record_metrics_schreibt_trichter(self):
        # R4: run_region/_record_metrics speist das Dashboard-Monitoring (idempotent).
        import pathlib
        import tempfile
        from pipeline import deliver as D
        from pipeline.control import metrics, state
        with tempfile.TemporaryDirectory() as d:
            con = state.connect(pathlib.Path(d) / "s.db")
            b = Buckets("Münsterland", gebiet_id="muensterland", roh=312,
                        lieferbar=[_r("S1", "ABR1", "A", dv=True)],
                        pending=[_r("S2", "ABR2", "B")], namenlos=[_r("S3", "ABR3", None)])
            D._record_metrics(b, con)
            rows = {r["metrik"]: r["summe"] for r in metrics.aggregate(con)}
            self.assertEqual(rows["signale"], 312)
            self.assertEqual(rows["lieferbar"], 1)
            self.assertEqual(rows["pending_qa"], 1)
            self.assertEqual(rows["namenlos"], 1)
            self.assertEqual(rows["dv_flag"], 1)
            con.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
