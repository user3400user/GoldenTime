"""
Direkt-Tests der bisher nur INDIREKT (über iter_leads/cohort) abgedeckten Helfer in
``pipeline/normalize.py`` — stdlib ``unittest``, synthetisch, KEIN Netz / KEINE Export-DB.

Gegenstand:
  * _to_float       — Komma/Punkt/Tausenderpunkt, None/''/'abc', wissenschaftlich, Vorzeichen.
  * _parse_date     — ISO, Teil-/Über-langes-Datum, Müll, None/''/0.
  * _year           — Jahres-Extraktion / None-Durchreichung.
  * _in_betrieb     — Casing/Whitespace, Tippfehler/Fremdstatus, None/''.
  * _is_natuerliche_person — natür./natuer.-Varianten, juristisch, None.
  * derive_trigger  — T2 (Post-EEG-Grenzjahrgänge), T1 (Frische-Fenster-Grenze + Speicher),
                      T3 (Bestand), EEG-Jahr schlägt Einheiten-IBN.
  * freshness_check  — fehlende reg/ibn, IBN-vor-reg-Lücke (Grenzwert).
  * iter_leads       — Region-/kWp-Band-/Status-Filter über eine synthetische In-Memory-
                      solar_extended + StorageIndex (Muster: test_cohort / test_speicher_abr).

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_normalize -v
"""
from __future__ import annotations

import datetime as dt
import sqlite3
import unittest

from pipeline import config, normalize
from pipeline.speicher_check import (
    COLOCATED,
    NONE_REPORTED,
    OPERATOR_ELSEWHERE,
    build_storage_index,
)

HEUTE = normalize.HEUTE   # an dasselbe „heute" binden, das das Modul benutzt


# ---------------------------------------------------------------------------
# _to_float — Zahl-Parsing aus rohen MaStR-Strings
# ---------------------------------------------------------------------------
class TestToFloat(unittest.TestCase):
    def test_plain_and_int(self):
        self.assertEqual(normalize._to_float("120"), 120.0)
        self.assertEqual(normalize._to_float(250), 250.0)
        self.assertEqual(normalize._to_float(30.0), 30.0)

    def test_punkt_dezimal(self):
        self.assertEqual(normalize._to_float("123.45"), 123.45)

    def test_komma_dezimal(self):
        # Deutsches Dezimalkomma -> Punkt.
        self.assertEqual(normalize._to_float("123,45"), 123.45)
        self.assertEqual(normalize._to_float("0,9"), 0.9)

    def test_whitespace_getrimmt(self):
        self.assertEqual(normalize._to_float("  90  "), 90.0)
        self.assertEqual(normalize._to_float("\t12,5\n"), 12.5)

    def test_negativ_und_vorzeichen(self):
        self.assertEqual(normalize._to_float("-5"), -5.0)
        self.assertEqual(normalize._to_float("+7,5"), 7.5)

    def test_wissenschaftlich(self):
        self.assertEqual(normalize._to_float("1e3"), 1000.0)
        self.assertEqual(normalize._to_float("1.5e2"), 150.0)

    def test_none_und_leer(self):
        self.assertIsNone(normalize._to_float(None))
        self.assertIsNone(normalize._to_float(""))
        self.assertIsNone(normalize._to_float("   "))

    def test_muell(self):
        self.assertIsNone(normalize._to_float("abc"))
        self.assertIsNone(normalize._to_float("12,5,6"))
        self.assertIsNone(normalize._to_float("kWp"))

    def test_tausenderpunkt_aktuelles_verhalten(self):
        # DOKUMENTIERT das IST-Verhalten: nur ',' -> '.' wird ersetzt. Ein deutscher
        # Tausenderpunkt-mit-Dezimalkomma '1.234,56' wird damit NICHT korrekt geparst
        # (würde '1.234.56' -> float-Fehler -> None). MaStR-Bruttoleistung ist in der Praxis
        # ohne Tausenderpunkt, daher kein Bug; dieser Test pinnt das Verhalten fest.
        self.assertIsNone(normalize._to_float("1.234,56"))
        # Reiner ASCII-Punkt als (vermeintlicher) Tausendertrenner wird als Dezimalpunkt gelesen:
        self.assertEqual(normalize._to_float("1.234"), 1.234)


# ---------------------------------------------------------------------------
# _parse_date — Datum aus rohem String (ISO, Teil/Müll)
# ---------------------------------------------------------------------------
class TestParseDate(unittest.TestCase):
    def test_iso_datum(self):
        self.assertEqual(normalize._parse_date("2006-04-01"), dt.date(2006, 4, 1))

    def test_iso_mit_zeitstempel_wird_abgeschnitten(self):
        # [:10] schneidet die Zeitkomponente weg.
        self.assertEqual(
            normalize._parse_date("2007-07-20T13:45:00"), dt.date(2007, 7, 20)
        )
        self.assertEqual(
            normalize._parse_date("2007-07-20 00:00:00"), dt.date(2007, 7, 20)
        )

    def test_date_objekt_durchgereicht(self):
        # str(date) == ISO -> rundläuft.
        self.assertEqual(
            normalize._parse_date(dt.date(2020, 12, 31)), dt.date(2020, 12, 31)
        )

    def test_none_leer_und_null(self):
        # `if not v` fängt None, '' und 0.
        self.assertIsNone(normalize._parse_date(None))
        self.assertIsNone(normalize._parse_date(""))
        self.assertIsNone(normalize._parse_date(0))

    def test_teil_datum_ist_muell(self):
        # Nur Jahr/Jahr-Monat ist kein gültiges ISO-Datum -> None (kein Crash).
        self.assertIsNone(normalize._parse_date("2006"))
        self.assertIsNone(normalize._parse_date("2006-04"))

    def test_muell(self):
        self.assertIsNone(normalize._parse_date("kein-datum"))
        self.assertIsNone(normalize._parse_date("31.12.2020"))   # deutsches Format, kein ISO
        self.assertIsNone(normalize._parse_date("2006-13-01"))   # ungültiger Monat


# ---------------------------------------------------------------------------
# _year — Jahr aus optionalem date
# ---------------------------------------------------------------------------
class TestYear(unittest.TestCase):
    def test_jahr(self):
        self.assertEqual(normalize._year(dt.date(2006, 4, 1)), 2006)

    def test_none(self):
        self.assertIsNone(normalize._year(None))


# ---------------------------------------------------------------------------
# _in_betrieb — toleranter Betriebsstatus-Check
# ---------------------------------------------------------------------------
class TestInBetrieb(unittest.TestCase):
    def test_none_und_leer_gilt_als_in_betrieb(self):
        # Unbekannt nicht wegwerfen.
        self.assertTrue(normalize._in_betrieb(None))
        self.assertTrue(normalize._in_betrieb(""))

    def test_config_klartext(self):
        self.assertTrue(normalize._in_betrieb(config.BETRIEBSSTATUS_IN_BETRIEB))
        self.assertTrue(normalize._in_betrieb("In Betrieb"))

    def test_casing_und_whitespace(self):
        # Exakt-Vergleich lowert beide Seiten; startswith greift zusätzlich.
        self.assertTrue(normalize._in_betrieb("in betrieb"))
        self.assertTrue(normalize._in_betrieb("IN BETRIEB"))
        self.assertTrue(normalize._in_betrieb("  In Betrieb  "))
        self.assertTrue(normalize._in_betrieb("\tIn Betrieb\n"))

    def test_startswith_suffix(self):
        # startswith('in betrieb') fängt Status-Erweiterungen.
        self.assertTrue(normalize._in_betrieb("In Betrieb (Teil)"))
        self.assertTrue(normalize._in_betrieb("in betrieb seit 2020"))

    def test_stillgelegt_und_fremdstatus_nicht_in_betrieb(self):
        self.assertFalse(normalize._in_betrieb("Endgültig stillgelegt"))
        self.assertFalse(normalize._in_betrieb("Vorübergehend stillgelegt"))
        self.assertFalse(normalize._in_betrieb("In Planung"))

    def test_tippfehler_faellt_durch(self):
        # 'Inbetrieb' (ohne Leerzeichen) bzw. 'im Betrieb' matchen weder == noch startswith.
        self.assertFalse(normalize._in_betrieb("Inbetrieb"))
        self.assertFalse(normalize._in_betrieb("im Betrieb"))


# ---------------------------------------------------------------------------
# _is_natuerliche_person — e.K.-Caveat-Flag
# ---------------------------------------------------------------------------
class TestIsNatuerlichePerson(unittest.TestCase):
    def test_natuerliche_varianten(self):
        self.assertTrue(normalize._is_natuerliche_person("Natürliche Person"))
        # ASCII-Umschrift 'natuer' wird ebenfalls erkannt.
        self.assertTrue(normalize._is_natuerliche_person("natuerliche person"))
        self.assertTrue(
            normalize._is_natuerliche_person(
                "Natürliche Person oder Organisation mit Personenbezug"
            )
        )

    def test_juristisch_und_organisation_false(self):
        self.assertFalse(normalize._is_natuerliche_person("Organisation (Unternehmen)"))
        self.assertFalse(normalize._is_natuerliche_person("Juristische Person"))

    def test_none_und_leer(self):
        self.assertFalse(normalize._is_natuerliche_person(None))
        self.assertFalse(normalize._is_natuerliche_person(""))


# ---------------------------------------------------------------------------
# derive_trigger — Trigger-Ableitung (T1/T2/T3) mit Grenzwerten
# ---------------------------------------------------------------------------
class TestDeriveTrigger(unittest.TestCase):
    def _frisch_reg(self, tage_alt: int) -> dt.date:
        return HEUTE - dt.timedelta(days=tage_alt)

    def test_t2_post_eeg_jahrgaenge(self):
        # EEG-Jahr in POST_EEG_JAHRGAENGE -> T2 (auch ohne Frische).
        for jahr in config.POST_EEG_JAHRGAENGE:
            eeg = dt.date(jahr, 6, 1)
            self.assertEqual(
                normalize.derive_trigger(None, None, eeg, NONE_REPORTED), "T2"
            )

    def test_t2_grenzjahrgaenge_aussen_kein_t2(self):
        # Direkt vor/nach der Post-EEG-Spanne (2005 / 2008) -> NICHT T2.
        rand = sorted(config.POST_EEG_JAHRGAENGE)
        davor, danach = rand[0] - 1, rand[-1] + 1
        for jahr in (davor, danach):
            eeg = dt.date(jahr, 6, 1)
            self.assertNotEqual(
                normalize.derive_trigger(None, None, eeg, NONE_REPORTED), "T2"
            )

    def test_eeg_jahr_schlaegt_einheiten_ibn(self):
        # eeg_ibn hat Vorrang: Einheiten-IBN 2006 (Post-EEG), aber EEG-IBN 2010 -> kein T2.
        ibn_post = dt.date(2006, 3, 1)
        eeg_modern = dt.date(2010, 3, 1)
        self.assertNotEqual(
            normalize.derive_trigger(None, ibn_post, eeg_modern, NONE_REPORTED), "T2"
        )

    def test_eeg_fehlt_fallback_auf_einheiten_ibn(self):
        # Ohne eeg_ibn zieht das Einheiten-IBN-Jahr -> Post-EEG -> T2.
        self.assertEqual(
            normalize.derive_trigger(None, dt.date(2007, 8, 8), None, NONE_REPORTED),
            "T2",
        )

    def test_t1_frische_innerhalb_fenster_ohne_colocation(self):
        reg = self._frisch_reg(config.FRISCHE_FENSTER_TAGE - 1)
        self.assertEqual(
            normalize.derive_trigger(reg, None, None, NONE_REPORTED), "T1"
        )

    def test_t1_grenzwert_genau_am_fenster(self):
        # Genau am Fenster-Rand (== FRISCHE_FENSTER_TAGE) gilt noch als frisch (<=).
        reg_grenze = self._frisch_reg(config.FRISCHE_FENSTER_TAGE)
        self.assertEqual(
            normalize.derive_trigger(reg_grenze, None, None, NONE_REPORTED), "T1"
        )
        # Einen Tag jenseits des Fensters -> nicht mehr frisch -> T3.
        reg_alt = self._frisch_reg(config.FRISCHE_FENSTER_TAGE + 1)
        self.assertEqual(
            normalize.derive_trigger(reg_alt, None, None, NONE_REPORTED), "T3"
        )

    def test_t1_unterdrueckt_bei_colocation(self):
        # Frisch, aber Speicher am Standort -> kein T1 (frische PV o. Speicher).
        reg = self._frisch_reg(5)
        self.assertEqual(
            normalize.derive_trigger(reg, None, None, COLOCATED), "T3"
        )

    def test_t1_bei_operator_elsewhere_erlaubt(self):
        # operator_elsewhere ist NICHT colocated -> frisch -> T1 bleibt.
        reg = self._frisch_reg(5)
        self.assertEqual(
            normalize.derive_trigger(reg, None, None, OPERATOR_ELSEWHERE), "T1"
        )

    def test_t3_bestand_default(self):
        # Weder Post-EEG noch frisch -> Bestand T3.
        alt_reg = self._frisch_reg(config.FRISCHE_FENSTER_TAGE + 100)
        self.assertEqual(
            normalize.derive_trigger(alt_reg, dt.date(2015, 1, 1), None, NONE_REPORTED),
            "T3",
        )

    def test_t3_ohne_jegliches_datum(self):
        self.assertEqual(
            normalize.derive_trigger(None, None, None, NONE_REPORTED), "T3"
        )


# ---------------------------------------------------------------------------
# freshness_check — R3 §7b Nachregistrierungs-Verdacht
# ---------------------------------------------------------------------------
class TestFreshnessCheck(unittest.TestCase):
    def test_kein_reg_datum_invalide(self):
        ok, warn = normalize.freshness_check(None, dt.date(2020, 1, 1))
        self.assertFalse(ok)
        self.assertIn("Registrierungsdatum", warn)

    def test_ibn_fehlt_valide_mit_hinweis(self):
        ok, warn = normalize.freshness_check(dt.date(2020, 1, 1), None)
        self.assertTrue(ok)
        self.assertIn("nicht validierbar", warn)

    def test_plausibel_kurz_vor_reg_valide(self):
        reg = dt.date(2020, 1, 10)
        ibn = dt.date(2020, 1, 1)   # 9 Tage davor -> plausibel
        ok, warn = normalize.freshness_check(reg, ibn)
        self.assertTrue(ok)
        self.assertIsNone(warn)

    def test_grenzwert_luecke(self):
        reg = dt.date(2021, 1, 1)
        # Genau IBN_REG_LUECKE_WARN_TAGE Tage davor -> noch valide (> ist die Bedingung).
        ibn_grenze = reg - dt.timedelta(days=config.IBN_REG_LUECKE_WARN_TAGE)
        ok, _ = normalize.freshness_check(reg, ibn_grenze)
        self.assertTrue(ok)
        # Einen Tag weiter zurück -> Lücke überschreitet -> Verdacht.
        ibn_zu_alt = reg - dt.timedelta(days=config.IBN_REG_LUECKE_WARN_TAGE + 1)
        ok2, warn2 = normalize.freshness_check(reg, ibn_zu_alt)
        self.assertFalse(ok2)
        self.assertIn("Nachregistrierung", warn2)

    def test_ibn_nach_reg_keine_warnung(self):
        # IBN nach Reg (negative Lücke) ist nie ein Nachregistrierungs-Verdacht.
        reg = dt.date(2020, 1, 1)
        ibn = dt.date(2020, 6, 1)
        ok, warn = normalize.freshness_check(reg, ibn)
        self.assertTrue(ok)
        self.assertIsNone(warn)


# ---------------------------------------------------------------------------
# iter_leads — Region-/kWp-/Status-Filter über synthetische In-Memory-DB
# ---------------------------------------------------------------------------
FRISCH_REG = (HEUTE - dt.timedelta(days=5)).isoformat()
FRISCH_IBN = (HEUTE - dt.timedelta(days=9)).isoformat()

SOLAR_COLS = [
    "EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer",
    "AnlagenbetreiberName", "AnlagenbetreiberPersonenArt", "Postleitzahl", "Ort",
    "Bundesland", "Bruttoleistung", "Registrierungsdatum", "Inbetriebnahmedatum",
    "EegInbetriebnahmedatum", "Einspeisungsart", "EinheitBetriebsstatus",
    "SpeicherAmGleichenOrt",
]
STORAGE_COLS = ["EinheitMastrNummer", "AnlagenbetreiberMastrNummer", "LokationMaStRNummer"]

#   Einheit, ABR, Lokation, Name, PersonenArt, PLZ, Ort, BL, kWp, reg, ibn, eeg, Einsp, Status, SpAmOrt
SOLAR_ROWS = [
    # L1 — 48er, kein Speicher, frisch, 100 kWp, Komma-Dezimal -> lieferbar, T1
    ("SEE1", "ABR_A", "SEL_A1", "Müller GmbH", "Organisation (Unternehmen)", "48143",
     "Münster", "NRW", "100,0", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L2 — 48er, SpeicherAmGleichenOrt=1 -> colocated (ausschluss_grund gesetzt, bleibt im Lead-Strom)
    ("SEE2", "ABR_B", "SEL_B2", "Bäcker KG", "Organisation (Unternehmen)", "48155",
     "Münster", "NRW", "200", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "1"),
    # L3 — 59er, Betreiber hat Speicher anderswo -> operator_elsewhere -> Premium-Flag
    ("SEE3", "ABR_C", "SEL_C3", "Schmidt AG", "Organisation (Unternehmen)", "59065",
     "Hamm", "NRW", "150", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L4 — 70er, natürliche Person -> NATUERLICHE_PERSON_PRUEFEN-Flag (nicht hart raus)
    ("SEE4", "ABR_D", "SEL_D4", "Weber e.K.", "Natürliche Person", "70173",
     "Stuttgart", "BW", "300", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L5 — 49er, frisches reg, aber IBN 2014 -> Frische-Warnung
    ("SEE5", "ABR_E", "SEL_E5", "Klein OHG", "Organisation (Unternehmen)", "49074",
     "Osnabrück", "NDS", "500", FRISCH_REG, "2014-05-01", None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L6 — 48er, kWp 5 (< KWP_MIN=30) -> herausgefiltert
    ("SEE6", "ABR_F", "SEL_F6", "Mini UG", "Organisation (Unternehmen)", "48999",
     "Münster", "NRW", "5", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L7 — 48er, kWp 800 (> KWP_MAX=750) -> herausgefiltert
    ("SEE7", "ABR_G", "SEL_G7", "Groß AG", "Organisation (Unternehmen)", "48777",
     "Münster", "NRW", "800", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L8 — 48er, stillgelegt -> bei nur_in_betrieb raus
    ("SEE8", "ABR_H", "SEL_H8", "Alt GmbH", "Organisation (Unternehmen)", "48888",
     "Münster", "NRW", "120", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "Endgültig stillgelegt", "0"),
    # L9 — 80er, Post-EEG 2006 -> T2 (andere Region als 48/59)
    ("SEE9", "ABR_I", "SEL_I9", "Fischer GmbH", "Organisation (Unternehmen)", "80331",
     "München", "BY", "90", FRISCH_REG, "2006-04-01", "2006-04-01", "Volleinspeisung",
     "In Betrieb", "0"),
    # L10 — 48er, kWp unparsebar ('kWp') -> _to_float None -> herausgefiltert
    ("SEE10", "ABR_J", "SEL_J10", "Krumm GbR", "Organisation (Unternehmen)", "48000",
     "Münster", "NRW", "kWp", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L11 — 48er, exakt KWP_MIN=30.0 -> Bandgrenze inklusiv -> lieferbar
    ("SEE11", "ABR_K", "SEL_K11", "Rand-Min GmbH", "Organisation (Unternehmen)", "48100",
     "Münster", "NRW", "30", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
    # L12 — 48er, exakt KWP_MAX=750.0 -> Bandgrenze inklusiv -> lieferbar
    ("SEE12", "ABR_L", "SEL_L12", "Rand-Max GmbH", "Organisation (Unternehmen)", "48200",
     "Münster", "NRW", "750", FRISCH_REG, FRISCH_IBN, None, "Teileinspeisung",
     "In Betrieb", "0"),
]
STORAGE_ROWS = [
    ("SSE_C", "ABR_C", "SEL_C99"),   # Speicher von ABR_C an anderer Lokation -> L3 operator_elsewhere
    ("SSE_X", "", ""),                # leere ABR -> aus dem Index gefiltert
]


def _build_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        f'CREATE TABLE solar_extended ({", ".join(f"\"{c}\" TEXT" for c in SOLAR_COLS)})'
    )
    con.execute(
        f'CREATE TABLE storage_extended ({", ".join(f"\"{c}\" TEXT" for c in STORAGE_COLS)})'
    )
    con.executemany(
        f'INSERT INTO solar_extended VALUES ({", ".join("?" for _ in SOLAR_COLS)})',
        SOLAR_ROWS,
    )
    con.executemany(
        f'INSERT INTO storage_extended VALUES ({", ".join("?" for _ in STORAGE_COLS)})',
        STORAGE_ROWS,
    )
    con.commit()
    return con


class TestIterLeads(unittest.TestCase):
    def setUp(self):
        self.con = _build_db()
        self.index = build_storage_index(self.con)

    def tearDown(self):
        self.con.close()

    def _by_id(self, **kw):
        return {
            l["einheit_mastr_nr"]: l
            for l in normalize.iter_leads(self.con, self.index, **kw)
        }

    def test_no_region_no_limit_raises(self):
        # Schutz gegen Voll-Scan der 6,2-Mio-Tabelle.
        with self.assertRaises(ValueError):
            list(normalize.iter_leads(self.con, self.index))

    def test_region_plz_filter(self):
        leads = self._by_id(plz_prefixes=("48",))
        # 48er, die durchkommen: L1, L2 (colocated bleibt im Strom), L11, L12.
        # NICHT: L6 (klein), L7 (groß), L8 (stillgelegt), L10 (kWp unparsebar).
        self.assertEqual(set(leads), {"SEE1", "SEE2", "SEE11", "SEE12"})
        # Andere Regionen sind nicht enthalten.
        self.assertNotIn("SEE3", leads)   # 59er
        self.assertNotIn("SEE9", leads)   # 80er

    def test_mehrere_plz_prefixe(self):
        leads = self._by_id(plz_prefixes=("48", "59"))
        self.assertIn("SEE3", leads)      # 59er nun dabei
        self.assertIn("SEE1", leads)

    def test_bundesland_filter(self):
        leads = self._by_id(bundesland="BY")
        self.assertEqual(set(leads), {"SEE9"})

    def test_kwp_band_grenzen_inklusiv(self):
        leads = self._by_id(plz_prefixes=("48",))
        self.assertIn("SEE11", leads)     # exakt KWP_MIN=30
        self.assertIn("SEE12", leads)     # exakt KWP_MAX=750
        self.assertNotIn("SEE6", leads)   # 5 < 30
        self.assertNotIn("SEE7", leads)   # 800 > 750
        self.assertEqual(config.KWP_MIN, 30.0)
        self.assertEqual(config.KWP_MAX, 750.0)

    def test_kwp_band_parametrisierbar(self):
        # Band über Parameter zuziehen: nur 100..200 -> L1(100), L2(200) bleiben,
        # L11(30) und L12(750) fallen raus.
        leads = self._by_id(plz_prefixes=("48",), kwp_min=100.0, kwp_max=200.0)
        self.assertEqual(set(leads), {"SEE1", "SEE2"})

    def test_unparsebare_kwp_herausgefiltert(self):
        self.assertNotIn("SEE10", self._by_id(plz_prefixes=("48",)))

    def test_komma_dezimal_kwp_geparst(self):
        # L1 kWp '100,0' -> 100.0, gerundet auf 1 Stelle.
        self.assertEqual(self._by_id(plz_prefixes=("48",))["SEE1"]["kwp"], 100.0)

    def test_status_filter_an(self):
        # Default nur_in_betrieb=True -> stillgelegte L8 raus.
        self.assertNotIn("SEE8", self._by_id(plz_prefixes=("48",)))

    def test_status_filter_aus_laesst_stillgelegte_durch(self):
        leads = self._by_id(plz_prefixes=("48",), nur_in_betrieb=False)
        self.assertIn("SEE8", leads)

    def test_colocated_markiert_nicht_verworfen(self):
        leads = self._by_id(plz_prefixes=("48",))
        self.assertEqual(leads["SEE2"]["speicher_status"], COLOCATED)
        self.assertEqual(leads["SEE2"]["ausschluss_grund"], "speicher_colocated")
        self.assertIsNone(leads["SEE1"]["ausschluss_grund"])

    def test_premium_flag_und_label(self):
        l3 = self._by_id(plz_prefixes=("59",))["SEE3"]
        self.assertEqual(l3["speicher_status"], OPERATOR_ELSEWHERE)
        self.assertIn("PREMIUM_SPEICHER_ANDERER_STANDORT", l3["flags"])
        l1 = self._by_id(plz_prefixes=("48",))["SEE1"]
        self.assertEqual(l1["speicher_status"], NONE_REPORTED)
        self.assertEqual(l1["speicher_label"], "kein Speicher gemeldet")

    def test_trigger_klassifikation(self):
        self.assertEqual(self._by_id(plz_prefixes=("48",))["SEE1"]["trigger_typ"], "T1")
        self.assertEqual(self._by_id(plz_prefixes=("80",))["SEE9"]["trigger_typ"], "T2")

    def test_freshness_warnung(self):
        l5 = self._by_id(plz_prefixes=("49",))["SEE5"]
        self.assertFalse(l5["frische_valide"])
        self.assertIn("FRISCHE_WARNUNG", l5["flags"])
        self.assertIn("Nachregistrierung", l5["frische_warnung"])

    def test_natuerliche_person_geflaggt(self):
        l4 = self._by_id(plz_prefixes=("70",))["SEE4"]
        self.assertIn("NATUERLICHE_PERSON_PRUEFEN", l4["flags"])

    def test_lead_shape_und_provenance(self):
        l1 = self._by_id(plz_prefixes=("48",))["SEE1"]
        self.assertEqual(l1["betreiber_mastr_nr"], "ABR_A")
        self.assertEqual(l1["lokation_mastr_nr"], "SEL_A1")
        self.assertEqual(l1["betreiber"], "Müller GmbH")
        self.assertEqual(l1["plz"], "48143")
        self.assertEqual(l1["geprueft_am"], HEUTE.isoformat())
        self.assertIn("MaStR", l1["provenance"])
        # reg_datum/inbetriebnahme als ISO-Strings durchgereicht (oder None).
        self.assertEqual(l1["reg_datum"], FRISCH_REG)
        self.assertEqual(l1["inbetriebnahme"], FRISCH_IBN)

    def test_limit_begrenzt_ausgabe(self):
        # limit erlaubt einen regionslosen Lauf und deckelt die Ausgabe.
        leads = list(normalize.iter_leads(self.con, self.index, limit=3))
        self.assertLessEqual(len(leads), 3)

    def test_explizite_solar_table(self):
        # solar_table-Parameter umgeht resolve_table.
        leads = {
            l["einheit_mastr_nr"]: l
            for l in normalize.iter_leads(
                self.con, self.index, plz_prefixes=("48",), solar_table="solar_extended"
            )
        }
        self.assertIn("SEE1", leads)


if __name__ == "__main__":
    unittest.main(verbosity=2)
