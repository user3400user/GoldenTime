"""
Config-Store (D3) — die EINE Quelle der Dashboard-Schaltungen (Gebiete/Trigger/Module an·aus).

Versionierte JSON-Datei (``pipeline/config_store.json``): git-diff-/blame-/revert-bar, von Pipeline
UND Dashboard gelesen; das Dashboard ist der **einzige Writer** (atomic ``os.replace``). stdlib-only
(JSON liest+schreibt; YAML wäre neue Dep, tomllib kann nicht schreiben).

Effektiver Trigger-Zustand pro Gebiet = globaler Schalter UND (kein Override ODER Override=True).
Ein ``trigger_overrides``-Eintrag kann also nur ABschalten, nie global Ausgeschaltetes scharfstellen —
verhindert versehentliches Scharfschalten der default-aus-Trigger (T5/T6/PV_ERWEITERUNG) pro Gebiet.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .. import config

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1
VALID_TRIGGERS = ("T1", "T2", "T3", "T4", "T5", "T6", "DV_FLAG", "PV_ERWEITERUNG")
VALID_MODULES = ("anreicherung",)


class ConfigError(ValueError):
    """Ungültiger Config-Store — mit ALLEN Fehlern auf einmal (UX wie cli inspect)."""


@dataclass(frozen=True)
class ConfigStore:
    schema_version: int
    triggers: dict          # {key: {"enabled": bool, "label": str}}
    modules: dict           # {name: {"enabled": bool, "label": str}}
    gebiete: tuple          # (dict, ...) je {id, name, enabled, plz_prefixes, trigger_overrides}
    updated_at: str = ""
    updated_by: str = ""
    extras: dict = field(default_factory=dict)   # _comment + unbekannte Top-Level-Keys (Passthrough)

    # --- Reader-Helfer (Pipeline + Dashboard konsumieren diese, nie hartcodierte Schalter) ---
    def is_trigger_enabled(self, trigger: str) -> bool:
        t = self.triggers.get(trigger)
        return bool(t and t.get("enabled"))

    def is_module_enabled(self, name: str) -> bool:
        m = self.modules.get(name)
        return bool(m and m.get("enabled"))

    def active_triggers(self) -> tuple[str, ...]:
        return tuple(k for k in VALID_TRIGGERS if self.is_trigger_enabled(k))

    def active_gebiete(self) -> tuple[dict, ...]:
        return tuple(g for g in self.gebiete if g.get("enabled"))

    def gebiet(self, gebiet_id: str) -> dict | None:
        for g in self.gebiete:
            if g.get("id") == gebiet_id:
                return g
        return None

    def effective_trigger(self, gebiet_id: str, trigger: str) -> bool:
        """Globaler Schalter UND (kein Override ODER Override True). Override kann nur ABschalten."""
        if not self.is_trigger_enabled(trigger):
            return False
        g = self.gebiet(gebiet_id)
        if not g:
            return True
        ov = (g.get("trigger_overrides") or {}).get(trigger)
        return ov is None or bool(ov)

    def natuerliche_personen_freigegeben(self) -> bool:
        """Politik-Gate (S0 · §0 · I7): dürfen natürliche Personen / e.K. an Kunden geliefert werden?

        Default **AUS** — bis ein Mensch nach anwaltlichem Art-6(1)(f)-Verdikt freischaltet (Bisnode/UODO
        + LG Kiel: 'öffentliche Herkunft' legitimiert den Resale NICHT automatisch). Liegt in
        ``extras['policy']`` (Top-Level-Passthrough), damit ein älteres config_store.json OHNE den
        Schlüssel sicher auf False defaultet — fail-safe in Richtung 'nicht liefern'. Robust gegen
        korruptes ``policy`` (non-dict) → False statt Crash im Invarianten-Gate.
        """
        pol = self.extras.get("policy")
        return bool(pol.get("natuerliche_personen_freigegeben", False)) if isinstance(pol, dict) else False


def _default_raw() -> dict:
    """Eingebaute Default-Struktur (Default-Aus exakt nach Briefing §3 / Expansions-Analyse §3)."""
    return {
        "_comment": ("GoldenTime Config-Store (D3). Geschrieben vom Admin-Dashboard, gelesen von "
                     "Pipeline + Dashboard. Manuell editierbar; muss schema_version + Validierung bestehen."),
        "schema_version": SCHEMA_VERSION,
        "updated_at": "",
        "updated_by": "default",
        "triggers": {
            "T1": {"enabled": True,  "label": "Neuregistrierung PV o. Speicher"},
            "T2": {"enabled": True,  "label": "Post-EEG 2006/07"},
            "T3": {"enabled": True,  "label": "Bestand o. Speicher"},
            "T4": {"enabled": True,  "label": "Speicher-Retrofit"},
            "T5": {"enabled": False, "label": "Betreiberwechsel (gebaut, default aus)"},
            "T6": {"enabled": False, "label": "Stilllegung (gebaut, default aus)"},
            "DV_FLAG": {"enabled": True, "label": "Direktvermarkter >=100 kWp"},
            "PV_ERWEITERUNG": {"enabled": False, "label": "Zweit-Einheit an Bestands-ABR (default aus)"},
        },
        "modules": {
            "anreicherung": {"enabled": False, "label": "Entscheider/Kontakt — scharf erst nach Call + Lizenz"},
        },
        # Politik-Schalter (Passthrough via extras; nicht-strukturell, von _validate ignoriert).
        "policy": {
            "natuerliche_personen_freigegeben": False,
            "_comment": ("S0/§0/I7: natürliche Personen / e.K. erst nach anwaltlicher Art-6(1)(f)-"
                         "Freigabe an Kunden liefern. Default aus → e.K. werden hart aus dem "
                         "lieferbar-Bucket gefiltert (Bisnode/UODO + LG Kiel)."),
        },
        "gebiete": [
            {"id": "muensterland", "name": "Münsterland", "enabled": True,
             "plz_prefixes": ["48", "59"], "trigger_overrides": {}},
            {"id": "osnabrueck", "name": "Raum Osnabrück", "enabled": True,
             "plz_prefixes": ["49"], "trigger_overrides": {}},
            {"id": "stuttgart", "name": "Raum Stuttgart", "enabled": False,
             "plz_prefixes": ["70", "71"], "trigger_overrides": {}},
        ],
    }


def _validate(raw: dict) -> list[str]:
    """Sammle ALLE Fehler (nicht beim ersten abbrechen)."""
    errors: list[str] = []
    if raw.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version {raw.get('schema_version')!r} != unterstützt ({SCHEMA_VERSION})")
    triggers = raw.get("triggers")
    if not isinstance(triggers, dict):
        errors.append("'triggers' fehlt oder ist kein Objekt")
    else:
        for k, v in triggers.items():
            if k not in VALID_TRIGGERS:
                errors.append(f"unbekannter Trigger '{k}' (erlaubt: {VALID_TRIGGERS})")
            if not isinstance(v, dict) or not isinstance(v.get("enabled"), bool):
                errors.append(f"Trigger '{k}': 'enabled' muss bool sein")
    modules = raw.get("modules")
    if not isinstance(modules, dict):
        errors.append("'modules' fehlt oder ist kein Objekt")
    gebiete = raw.get("gebiete")
    if not isinstance(gebiete, list):
        errors.append("'gebiete' fehlt oder ist keine Liste")
    else:
        seen = set()
        for i, g in enumerate(gebiete):
            gid = g.get("id")
            if not gid:
                errors.append(f"gebiet[{i}] ohne 'id'")
            elif gid in seen:
                errors.append(f"doppelte gebiet.id '{gid}'")
            else:
                seen.add(gid)
            if not isinstance(g.get("enabled"), bool):
                errors.append(f"gebiet '{gid}': 'enabled' muss bool sein")
            pp = g.get("plz_prefixes")
            if not isinstance(pp, list) or not all(isinstance(p, str) and p for p in pp):
                errors.append(f"gebiet '{gid}': 'plz_prefixes' muss nichtleere Strings sein")
            elif not all(p.isdigit() for p in pp):
                # PLZ-Präfixe = reine Ziffern. Diese EINE Invariante macht den SQL-LIKE-Region-Filter
                # ohne Escaping sicher (kein %/_ in einer Ziffern-PLZ möglich).
                errors.append(f"gebiet '{gid}': 'plz_prefixes' muss reine Ziffern sein (PLZ)")
            ov = g.get("trigger_overrides", {})
            if not isinstance(ov, dict):
                errors.append(f"gebiet '{gid}': 'trigger_overrides' muss ein Objekt sein")
            else:
                for ok in ov:
                    if ok not in VALID_TRIGGERS:
                        errors.append(f"gebiet '{gid}': Override für unbekannten Trigger '{ok}'")
    return errors


# Strukturelle Top-Level-Keys; alles andere (z.B. _comment, manuelle Notizen) wird als ``extras``
# durchgereicht (Passthrough), damit ein Dashboard-save() menschliche Annotationen nicht verwirft.
_STRUCT_KEYS = frozenset({"schema_version", "updated_at", "updated_by", "triggers", "modules", "gebiete"})


def _from_raw(raw: dict) -> ConfigStore:
    extras = {k: v for k, v in raw.items() if k not in _STRUCT_KEYS}
    return ConfigStore(
        schema_version=raw["schema_version"],
        triggers=raw.get("triggers", {}),
        modules=raw.get("modules", {}),
        gebiete=tuple(raw.get("gebiete", ())),
        updated_at=raw.get("updated_at", ""),
        updated_by=raw.get("updated_by", ""),
        extras=extras,
    )


def _to_raw(store: ConfigStore) -> dict:
    raw = dict(store.extras)                       # _comment + unbekannte Keys zuerst (Passthrough)
    raw.setdefault("_comment", _default_raw()["_comment"])
    raw.update({
        "schema_version": store.schema_version,
        "updated_at": store.updated_at,
        "updated_by": store.updated_by,
        "triggers": store.triggers,
        "modules": store.modules,
        "gebiete": list(store.gebiete),
    })
    return raw


def defaults() -> ConfigStore:
    """Eingebauter Default-Store (Fallback, wenn die Datei fehlt oder ungültig ist)."""
    return _from_raw(_default_raw())


def load(path: Path | str | None = None) -> ConfigStore:
    """Lade den Config-Store. Fehlt die Datei → Defaults + Warn-Log (Pipeline crasht nicht)."""
    p = Path(path or config.CONFIG_STORE_PATH)
    if not p.exists():
        log.warning("Config-Store %s fehlt — fahre mit eingebauten Defaults fort.", p)
        return _from_raw(_default_raw())
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config-Store {p} ist kein gültiges JSON: {e}") from e
    errors = _validate(raw)
    if errors:
        raise ConfigError(f"Config-Store {p} ungültig:\n  - " + "\n  - ".join(errors))
    return _from_raw(raw)


def save(store: ConfigStore, *, updated_by: str = "dashboard",
         path: Path | str | None = None, _now: str | None = None) -> ConfigStore:
    """Atomar schreiben (nur vom Dashboard). os.replace → Reader sieht nie eine halbe Datei."""
    p = Path(path or config.CONFIG_STORE_PATH)
    now = _now or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    # extras (u.a. der invarianten-tragende policy-Block) MUSS durchgereicht werden — sonst löscht
    # jeder Dashboard-Toggle die natuerliche_personen_freigegeben-Freigabe + den Audit-Kommentar
    # still (Refute MEDIUM: fail-safe zwar re-locked, aber ein realer Operability-Defekt).
    stamped = ConfigStore(store.schema_version, store.triggers, store.modules,
                          store.gebiete, updated_at=now, updated_by=updated_by, extras=store.extras)
    errors = _validate(_to_raw(stamped))
    if errors:
        raise ConfigError("save() abgelehnt — ungültiger Store:\n  - " + "\n  - ".join(errors))
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".config_store.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(_to_raw(stamped), f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return stamped
