"""
Adapter: normalize-Lead-Dict → SignalRecord (Komponente 5).

Bewusst getrennt von normalize.py: das bestehende Lead-Dict bleibt unverändert (die 9 Tests
bleiben grün), und dieser Mapper baut daraus den zentralen SignalRecord — inkl. Konfidenz aus den
Melde-Gotchas (record.compute_konfidenz), DV-Flag und Buy-Relevanz. Trigger/Qualifizierer/Ledger
konsumieren ab hier nur noch den Record, nicht das Dict.
"""
from __future__ import annotations

import datetime as dt

from .record import BUY_RELEVANZ, SignalRecord, compute_konfidenz, is_dv_pflichtig


def from_lead(lead: dict, *, region: str | None = None) -> SignalRecord:
    """Mappe ein normalize.iter_leads-Dict auf einen SignalRecord.

    ``region`` ist das optionale Gebiets-Label (aus dem Config-Store). ``entity`` (Firmenname) kommt
    aus ``lead['betreiber']`` — beim reinen Einheiten-Pull ist das None und wird erst durch den
    market_actors-Join (Qualifizierer) oder die Anreicherung gefüllt.
    """
    trigger = lead.get("trigger_typ", "")
    speicher_status = lead.get("speicher_status", "")
    frische_valide = bool(lead.get("frische_valide", True))
    kwp = lead.get("kwp")

    konfidenz, gruende = compute_konfidenz(trigger, speicher_status, frische_valide)
    dv = is_dv_pflichtig(kwp)

    buy = BUY_RELEVANZ.get(trigger, "Kaufsignal aus MaStR-Registerdaten.")
    if dv:
        buy += " Direktvermarktungs-pflichtig (≥100 kWp)."
    if speicher_status == "operator_elsewhere":
        buy += " Betreiber kennt Speicher bereits (anderer Standort) → Premium."

    return SignalRecord(
        einheit_mastr_nr=lead["einheit_mastr_nr"],
        betreiber_mastr_nr=lead.get("betreiber_mastr_nr"),
        trigger_typ=trigger,
        datum=lead.get("inbetriebnahme") or lead.get("reg_datum"),
        konfidenz=konfidenz,
        buy_relevanz=buy,
        entity=lead.get("betreiber"),
        plz=lead.get("plz"),
        ort=lead.get("ort"),
        bundesland=lead.get("bundesland"),
        region=region,
        kwp=kwp,
        einspeisung=lead.get("einspeisung"),
        speicher_status=speicher_status,
        speicher_label=lead.get("speicher_label", ""),
        konfidenz_gruende=gruende,
        flags=tuple(lead.get("flags", ())),
        dv_flag=dv,
        qa_status=lead.get("qa_status", "auto_ok"),
        geprueft_am=lead.get("geprueft_am") or dt.date.today().isoformat(),
        provenance=lead.get("provenance", ""),
    )
