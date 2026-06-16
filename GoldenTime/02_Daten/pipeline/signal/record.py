"""
SignalRecord — die zentrale Datenstruktur des Vollpakets (Briefing §5, Komponente 5).

Jedes Kaufsignal (Trigger-Treffer) wird als SignalRecord ausgegeben. **Trigger-Klassifikator,
Qualifizierer, Exklusivitäts-Ledger und Anreicherungs-Modul hängen alle hieran.** Pflichtfelder
nach Briefing §5: Entity · Trigger-Typ · Evidenz-URL · Region · Datum · Konfidenz · Buy-Relevanz.

**Konfidenz ist Pflichtfeld** (kein Schmuck): die MaStR-Melde-Gotchas (Briefing §4) — „kein Speicher
gemeldet" ≠ „kein Speicher" (~9 % unregistriert), Nachregistrierungs-Scheinfrische, lückenhafte
Retrofit-Meldung (~40 % fristgerecht) — werden als **benannte Abschläge** in die Konfidenz gerechnet
und mitgeführt (``konfidenz_gruende``). ``__post_init__`` erzwingt das Feld und den Wertebereich.

Bewusst stdlib-only (dataclasses). Die Quell-/Schema-Logik bleibt in normalize/db; dieser Record
ist quell-neutral — ``from_lead`` mappt das normalize-Lead-Dict hierher (kein Bruch bestehender Tests).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .. import config

# Öffentliche MaStR-Einheitsseite — die belegbare Evidenz-URL je Einheit (Briefing §5).
MASTR_EINHEIT_URL = (
    "https://www.marktstammdatenregister.de/MaStR/Einheit/Detail/IndexOeffentlich/{einheit}"
)

# --- Konfidenz-Modell: Abschläge zentral, nicht verstreut (Briefing §4 Gotchas) ---
KONF_BASIS = 1.0
ABSCHLAG_KEIN_SPEICHER_GEMELDET = 0.10   # "nicht gemeldet" ≠ "existiert nicht" (~9 % unregistriert)
ABSCHLAG_FRISCHE_WARNUNG = 0.25          # IBN ≪ reg_datum → Nachregistrierungs-Verdacht (R3 §7b)
ABSCHLAG_RETROFIT_LUECKE = 0.15          # Speicher-Retrofit nur ~40 % fristgerecht gemeldet (T4)
KONF_MIN = 0.30                          # Untergrenze: ein gemeldeter Datensatz bleibt belastbar

# Warum-jetzt je Trigger (Buy-Relevanz, Briefing §5).
BUY_RELEVANZ = {
    "T1": "Frische PV-Anmeldung ohne gemeldeten Speicher — Retrofit-Fenster offen.",
    "T2": "Post-EEG-Jahrgang (Förderende) — Eigenverbrauch-/Speicher-Entscheidung steht an.",
    "T3": "Bestands-PV ohne gemeldeten Speicher — latenter Retrofit-Bedarf.",
    "T4": "Speicher-Retrofit am Standort/Betreiber gemeldet — aktiver Investitionszyklus.",
    "T5": "Betreiberwechsel an Bestands-Einheit — neue Entscheidungsträger.",
    "T6": "Stilllegung gemeldet — Repowering-/Reaktivierungs-Entscheidung.",
    "PV_ERW": "Zweit-Einheit an Bestands-Betreiber — Ausbau-Signal.",
}


def mastr_einheit_url(einheit_mastr_nr: str | None) -> str:
    """Öffentliche MaStR-Detailseite zur Einheit (Evidenz-URL, 1-Klick-Verifikation)."""
    return MASTR_EINHEIT_URL.format(einheit=einheit_mastr_nr or "")


def compute_konfidenz(
    trigger_typ: str, speicher_status: str, frische_valide: bool
) -> tuple[float, tuple[str, ...]]:
    """Konfidenz + benannte Belege aus den Melde-Gotchas (Briefing §4).

    Startet bei 1.0, zieht benannte Abschläge ab, Untergrenze KONF_MIN. Jeder Abschlag wird als
    Klartext-Grund mitgeführt, damit das Signal seine eigene Unsicherheit transparent macht.
    """
    k = KONF_BASIS
    gruende: list[str] = []
    if speicher_status == "none_reported":
        k -= ABSCHLAG_KEIN_SPEICHER_GEMELDET
        gruende.append("„kein Speicher gemeldet\" ≠ keiner (~9 % unregistriert)")
    if not frische_valide:
        k -= ABSCHLAG_FRISCHE_WARNUNG
        gruende.append("Frische-Warnung — Inbetriebnahme deutlich vor Registrierung (Nachregistrierung)")
    if trigger_typ == "T4":
        k -= ABSCHLAG_RETROFIT_LUECKE
        gruende.append("Retrofit-Meldung lückenhaft (~40 % fristgerecht gemeldet)")
    return max(KONF_MIN, round(k, 2)), tuple(gruende)


@dataclass
class SignalRecord:
    """Ein Kaufsignal. Pflichtfelder ohne Default (Briefing §5), Rest angereichert/optional."""

    # --- Identität (stabile Schlüssel; Ledger-/QA-/Join-Basis) ---
    einheit_mastr_nr: str
    betreiber_mastr_nr: str | None
    # --- Signal (Briefing §5 Pflichtfelder) ---
    trigger_typ: str                 # T1/T2/T3/T4/T5/T6/PV_ERW
    datum: str | None                # maßgebliches Datum (IBN bzw. EEG-IBN), ISO
    konfidenz: float                 # PFLICHT, 0..1 — __post_init__ erzwingt
    buy_relevanz: str                # „warum jetzt", kurz
    # --- Entity / Region ---
    entity: str | None = None        # Firmenname (market_actors-Join); None = noch nicht angereichert
    plz: str | None = None
    ort: str | None = None
    bundesland: str | None = None
    region: str | None = None        # Gebiets-Label (Config-Store), optional
    kwp: float | None = None
    einspeisung: str | None = None
    # --- Speicher-Status (Kern-IP, 3-Wege) ---
    speicher_status: str = ""        # none_reported | operator_elsewhere | colocated
    speicher_label: str = ""
    # --- Konfidenz-Belege / Flags / DV ---
    konfidenz_gruende: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    dv_flag: bool = False            # Direktvermarktungs-Pflicht ≥100 kWp (Multiplikator)
    # --- QA / Provenance ---
    qa_status: str = "auto_ok"       # auto_ok | pending | approved | rejected
    geprueft_am: str = field(default_factory=lambda: dt.date.today().isoformat())
    provenance: str = ""

    def __post_init__(self) -> None:
        if not self.einheit_mastr_nr:
            raise ValueError("SignalRecord ohne einheit_mastr_nr (Entity-/Evidenz-Schlüssel).")
        if self.konfidenz is None:
            raise ValueError("SignalRecord.konfidenz ist Pflichtfeld (Briefing §5).")
        if not (0.0 <= float(self.konfidenz) <= 1.0):
            raise ValueError(f"SignalRecord.konfidenz {self.konfidenz!r} außerhalb 0..1.")

    @property
    def evidenz_url(self) -> str:
        return mastr_einheit_url(self.einheit_mastr_nr)

    # CSV-Spaltenreihenfolge der Lieferung (frischeste/heißeste oben sortiert der Aufrufer).
    CSV_FIELDS = (
        "trigger_typ", "dv_flag", "entity", "kwp", "plz", "ort", "bundesland",
        "datum", "speicher_label", "konfidenz", "buy_relevanz", "qa_status",
        "einheit_mastr_nr", "betreiber_mastr_nr", "evidenz_url",
        "konfidenz_gruende", "flags", "geprueft_am", "provenance",
    )

    def to_row(self) -> dict:
        """Flaches Dict für CSV/Lieferung (Tupel → '|'-join, Evidenz-URL inklusive)."""
        return {
            "trigger_typ": self.trigger_typ,
            "dv_flag": "ja" if self.dv_flag else "",
            "entity": self.entity or "",
            "kwp": "" if self.kwp is None else round(self.kwp, 1),
            "plz": self.plz or "",
            "ort": self.ort or "",
            "bundesland": self.bundesland or "",
            "datum": self.datum or "",
            "speicher_label": self.speicher_label,
            "konfidenz": self.konfidenz,
            "buy_relevanz": self.buy_relevanz,
            "qa_status": self.qa_status,
            "einheit_mastr_nr": self.einheit_mastr_nr,
            "betreiber_mastr_nr": self.betreiber_mastr_nr or "",
            "evidenz_url": self.evidenz_url,
            "konfidenz_gruende": " | ".join(self.konfidenz_gruende),
            "flags": "|".join(self.flags),
            "geprueft_am": self.geprueft_am,
            "provenance": self.provenance,
        }


def is_dv_pflichtig(kwp: float | None) -> bool:
    """Direktvermarktungs-Flag: Pflicht ab DV_FLAG_MIN_KWP (Briefing/Expansions-Analyse)."""
    return kwp is not None and kwp >= config.DV_FLAG_MIN_KWP
