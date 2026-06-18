"""
Diff-Regeln (D2, Briefing §4) — Diff-Event -> (Trigger | None, Konfidenz-Flag).

Übersetzt die rohen DiffEvents aus ``diff.py`` in die zeitlichen Trigger des Vollpakets.
Die §4-FALLEN sind hier bewusst auskommentiert, weil sie die häufigsten False-Positives sind:

  §4-Falle 1 — PV-Zubau ist KEIN Leistungs-Diff.
    Eine erweiterte PV-Anlage wird im MaStR als NEUE Einheit (NEW_UNIT) an der bestehenden
    ABR/Standort gemeldet, NICHT als Bruttoleistungs-Erhöhung der alten Einheit. Darum gilt:
      * NEW_UNIT solar an BESTANDS-ABR  -> 'PV_ERWEITERUNG' (Zweit-Einheit = Ausbau-Signal)
      * NEW_UNIT solar an NEUER  ABR    -> 'T1' (frische Erst-Anmeldung)
    Eine brutto_kw-ERHÖHUNG derselben Einheit ist dagegen meist eine Korrektur/Nachmeldung —
    NICHT als Zubau werten. Nur eine brutto_kw-REDUZIERUNG ist als Rückbau erkennbar (-> Flag,
    kein scharfer Trigger; Default-aus-Logik liegt im Config-Store, nicht hier).

  §4-Falle 2 — ABR-Wechsel ≠ immer Eigentümerwechsel (T5).
    Ein abr-Wechsel an derselben einheit_nr ist das T5-Signal (neue Entscheidungsträger),
    ABER eine reine UMFIRMIERUNG (gleicher Betrieb, neue MaStR-Akteursnummer) sieht identisch
    aus. Das ist nicht aus dem Diff allein auflösbar -> Trigger T5 MIT Konfidenz-Flag, damit
    der Qualifizierer/QA die Umfirmierung prüfen kann (statt blind als Eigentümerwechsel zu liefern).

  §4-Falle 3 — Speicher-Retrofit (T4) ist nur ~40 % fristgerecht gemeldet.
    NEW_UNIT storage an einer ABR/einem Standort mit Bestands-Solar ist das T4-Signal
    (aktiver Investitionszyklus). Die lückenhafte Meldung schlägt sich im Konfidenz-Abschlag
    nieder (record.ABSCHLAG_RETROFIT_LUECKE) — hier setzen wir das Flag, das ihn auslöst.

  §4-Falle 4 — Stilllegung leer->gesetzt = T6; gesetzt->leer = Wiederaufnahme (kein T6).
    Nur der Übergang von „kein Stilllegungsdatum" zu „Datum gesetzt" ist das Repowering-Signal.

Konfidenz-Flag (zweiter Rückgabewert): True = „dieses Signal trägt eine benannte §4-Unsicherheit"
(z. B. mögliche Umfirmierung bei T5). False = Diff ist eindeutig. Der Flag steuert den
Konfidenz-Abschlag im SignalRecord; die exakte Punktzahl rechnet record.compute_konfidenz.

stdlib-only. ``prev_index`` (optional) liefert den Bestand aus dem PREV-Snapshot (welche ABR/
Standorte schon Solar führten), damit NEW_UNIT korrekt in T1 vs. PV_ERWEITERUNG bzw. T4 fällt.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from . import diff as diffmod

# Trigger-Keys (Config-Store VALID_TRIGGERS-kompatibel). PV_ERWEITERUNG/T5/T6 sind im
# Config-Store default-AUS — diese Regeln schlagen sie nur vor; scharfgeschaltet wird über D3.
T1 = "T1"
T4 = "T4"
T5 = "T5"
T6 = "T6"
PV_ERWEITERUNG = "PV_ERWEITERUNG"


@dataclass(frozen=True)
class PrevIndex:
    """Bestand aus dem PREV-Snapshot: welche ABR Solar führte (für NEW_UNIT-Verzweigung).

    ``solar_operators`` = ABR mit >=1 Solar-Einheit im prev-Snapshot. Damit unterscheidet
    die Regel eine frische Erst-Anmeldung (T1) von einer Zweit-Einheit an Bestands-ABR
    (PV_ERWEITERUNG, §4-Falle 1) und einen Speicher an Solar-Betreiber (T4) vom Speicher
    eines Nur-Speicher-Akteurs (kein Solar-Bezug -> kein T4).
    """

    solar_operators: frozenset[str]

    @classmethod
    def from_snapshot(cls, prev_path: Path | str) -> PrevIndex:
        """Baue den PrevIndex aus einem prev-Snapshot (traeger='solar' -> ABR-Set)."""
        con = sqlite3.connect(str(prev_path))
        try:
            ops = {
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT abr FROM snapshot "
                    "WHERE traeger = 'solar' AND abr IS NOT NULL AND abr <> ''"
                )
            }
        finally:
            con.close()
        return cls(frozenset(ops))

    def hat_solar(self, abr: str | None) -> bool:
        return bool(abr) and abr in self.solar_operators


def classify_diff(
    ev: diffmod.DiffEvent, prev_index: PrevIndex | None = None
) -> tuple[str | None, bool]:
    """Klassifiziere ein DiffEvent nach Briefing §4 -> (Trigger | None, Konfidenz-Flag).

    Gibt ``(None, False)`` zurück, wenn das Event kein Buy-Signal ist (z. B. REMOVED,
    brutto_kw-Erhöhung, Stilllegungs-Aufhebung). Der zweite Wert ist der Konfidenz-Flag
    (True = benannte §4-Unsicherheit, s. Modul-Doc).
    """
    ct = ev.change_type

    # --- NEW_UNIT: Existenz-Diff -> §4-Falle 1 (Zubau ist NEW_UNIT, kein Leistungs-Diff) ---
    if ct == diffmod.NEW_UNIT:
        if ev.traeger == "solar":
            # Zweit-Einheit an Bestands-ABR -> Ausbau-Signal; sonst frische Erst-Anmeldung.
            if prev_index is not None and prev_index.hat_solar(ev.abr):
                return PV_ERWEITERUNG, False
            return T1, False
        if ev.traeger == "storage":
            # T4 nur, wenn der Betreiber/Standort Bestands-Solar führt (Retrofit-Bezug).
            # Ohne prev_index nehmen wir T4 an (B-Backbone lädt nur solar+storage; ein
            # neuer Speicher IST i. d. R. retrofit-relevant) — aber mit Konfidenz-Flag
            # wegen §4-Falle 3 (Retrofit-Meldung lückenhaft).
            if prev_index is None or prev_index.hat_solar(ev.abr):
                return T4, True
            # Kein Bestands-Solar (prev) -> kein Retrofit-Bezug -> kein T4. Das schließt BEWUSST die
            # Greenfield-Co-Registrierung aus (PV+Speicher in DERSELBEN Woche an neuer ABR): eine neue
            # Anlage, die direkt mit Speicher kommt, ist KEIN Retrofit-Lead (Bedarf bereits gedeckt).
            return None, False
        return None, False

    # --- REMOVED: Abgang. Kein eigener Trigger (Repowering kommt als T6/NEW_UNIT). ---
    if ct == diffmod.REMOVED:
        return None, False

    # --- FIELD_CHANGED: feldspezifisch (T5 / T6 / Reduzierung) ---
    if ct == diffmod.FIELD_CHANGED:
        if ev.field == "abr":
            # §4-Falle 2: Betreiberwechsel ODER reine Umfirmierung — nicht trennbar
            # -> T5 MIT Konfidenz-Flag (QA/Qualifizierer prüft die Umfirmierung).
            # ABER (Zweit-Review): NULL/leer -> gesetzt (oder umgekehrt) ist eine verspätete
            # Erst-Registrierung des Betreibers (gleicher Eigentümer), KEIN Wechsel -> kein T5.
            if diffmod._norm(ev.old) is None or diffmod._norm(ev.new) is None:
                return None, False
            return T5, True
        if ev.field in ("datum_stilllegung_endg", "datum_stilllegung_vorueb"):
            # §4-Falle 4: nur leer -> gesetzt ist das Repowering-Signal (T6).
            # gesetzt -> leer = Wiederaufnahme (kein T6).
            if diffmod._norm(ev.old) is None and diffmod._norm(ev.new) is not None:
                return T6, False
            return None, False
        if ev.field == "brutto_kw":
            # §4-Falle 1: PV-Zubau ist NICHT die Leistungs-Erhöhung derselben Einheit.
            # Erhöhung = meist Korrektur/Nachmeldung -> kein Trigger.
            # Nur eine REDUZIERUNG ist als Rückbau erkennbar -> Flag (kein scharfer Trigger).
            alt = diffmod._kw(ev.old)
            neu = diffmod._kw(ev.new)
            if alt is not None and neu is not None and neu < alt - 1e-9:
                return None, True   # Rückbau erkannt: Konfidenz-Flag, kein eigener Trigger
            return None, False

    return None, False
