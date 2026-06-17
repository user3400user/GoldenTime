"""
Tests für den Config-Store (D3) — stdlib, synthetisch, gegen temporäre Dateien (nie die echte JSON).

Lauf (aus 02_Daten/):  python -m unittest pipeline.tests.test_config_store
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipeline.control import config_store as cs


def _write(tmp: Path, raw: dict) -> Path:
    p = tmp / "config_store.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    return p


class TestLoad(unittest.TestCase):
    def test_missing_file_falls_back_to_defaults(self):
        store = cs.load(Path("/nonexistent/dir/config_store.json"))
        self.assertEqual(store.schema_version, cs.SCHEMA_VERSION)
        self.assertTrue(store.is_trigger_enabled("T1"))
        self.assertFalse(store.is_trigger_enabled("T5"))   # default aus
        self.assertFalse(store.is_module_enabled("anreicherung"))

    def test_default_json_on_disk_is_valid(self):
        # die echte versionierte Datei muss ladbar/valide sein
        store = cs.load()
        self.assertTrue(store.is_trigger_enabled("T2"))
        self.assertIn("muensterland", {g["id"] for g in store.gebiete})

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config_store.json"
            p.write_text("{nope", encoding="utf-8")
            with self.assertRaises(cs.ConfigError):
                cs.load(p)

    def test_validate_collects_all_errors(self):
        with tempfile.TemporaryDirectory() as d:
            raw = {
                "schema_version": 99,
                "triggers": {"T1": {"enabled": "yes"}, "TX": {"enabled": True}},
                "modules": {},
                "gebiete": [{"id": "a", "enabled": True, "plz_prefixes": ["48"]},
                            {"id": "a", "enabled": True, "plz_prefixes": ["49"]}],
            }
            with self.assertRaises(cs.ConfigError) as ctx:
                cs.load(_write(Path(d), raw))
            msg = str(ctx.exception)
            self.assertIn("schema_version", msg)
            self.assertIn("TX", msg)
            self.assertIn("doppelte gebiet.id", msg)


    def test_plz_prefixes_muss_ziffern_sein(self):
        # C3: Buchstaben-Präfix -> Validierungsfehler (sichert den escapefreien SQL-LIKE-Region-Filter).
        raw = {
            "schema_version": cs.SCHEMA_VERSION,
            "triggers": {}, "modules": {},
            "gebiete": [{"id": "x", "enabled": True, "plz_prefixes": ["48", "4a"],
                         "trigger_overrides": {}}],
        }
        self.assertTrue(any("reine Ziffern" in e for e in cs._validate(raw)))
        raw["gebiete"][0]["plz_prefixes"] = ["48", "59"]      # reine Ziffern -> kein solcher Fehler
        self.assertFalse(any("reine Ziffern" in e for e in cs._validate(raw)))


class TestEffectiveTrigger(unittest.TestCase):
    def setUp(self):
        self.store = cs.load(Path("/nonexistent/config_store.json"))  # Defaults

    def test_inherits_global(self):
        self.assertTrue(self.store.effective_trigger("muensterland", "T2"))
        self.assertFalse(self.store.effective_trigger("muensterland", "T5"))  # global aus

    def test_override_can_only_disable(self):
        # Override T2=False in einem Gebiet -> aus; Override T5=True kann NICHT scharfstellen.
        gebiete = list(self.store.gebiete)
        gebiete[0] = {**gebiete[0], "trigger_overrides": {"T2": False, "T5": True}}
        store = cs.ConfigStore(self.store.schema_version, self.store.triggers,
                               self.store.modules, tuple(gebiete))
        gid = gebiete[0]["id"]
        self.assertFalse(store.effective_trigger(gid, "T2"))   # lokal abgeschaltet
        self.assertFalse(store.effective_trigger(gid, "T5"))   # global aus -> Override True wirkungslos
        self.assertTrue(store.effective_trigger(gid, "T1"))    # unberührt


class TestSaveRoundtrip(unittest.TestCase):
    def test_save_then_load(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config_store.json"
            store = cs.load(Path("/nonexistent"))            # Defaults
            saved = cs.save(store, updated_by="test", path=p, _now="2026-06-16T12:00:00+00:00")
            self.assertEqual(saved.updated_by, "test")
            reloaded = cs.load(p)
            self.assertEqual(reloaded.updated_at, "2026-06-16T12:00:00+00:00")
            self.assertEqual(reloaded.active_triggers(), store.active_triggers())

    def test_save_is_atomic_no_partial(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config_store.json"
            store = cs.load(Path("/nonexistent"))
            cs.save(store, path=p)
            # gültige Datei + kein .tmp-Rest
            self.assertEqual(cs.load(p).schema_version, cs.SCHEMA_VERSION)
            self.assertEqual(list(Path(d).glob(".config_store.*.tmp")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
