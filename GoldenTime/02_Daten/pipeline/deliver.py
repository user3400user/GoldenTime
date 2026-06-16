"""
Liefer-Schicht (TEIL 5, Zweit-Review) — Buckets, Liefer-Mail-Vorlage, ehrlicher Mengen-Report.

Trennt die vier Buckets sauber (lieferbar gewerblich / QA-pending / namenlos / rejected), baut die
Käufer-Liefer-Mail im Signal-Format (Stempel + Evidenz-Direktlink + Exklusivität + dl-de/by-2.0) und
einen EHRLICHEN Mengen-Report: pro Gebiet zählt er BETRIEBE (distinct ABR) UND Einheiten und
kennzeichnet T2 als BESTAND (einmalige Ausschöpfung) vs. T1/T4 als FLUSS (wiederkehrend, Wochen-Diff).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .enrich import mastr_resolve
from .qualify import hierarchy, qa_gate
from .speicher_check import build_storage_index
from .triggers import cohort

# T2/T3 = Bestand (Kohorte, einmal ausschöpfbar); Diff-Trigger = Fluss (wiederkehrend pro Woche).
TRIGGER_ART = {
    "T2": "BESTAND (einmalig)", "T3": "BESTAND (einmalig)",
    "T1": "FLUSS (wöchentlich)", "T4": "FLUSS (wöchentlich)",
    "T5": "FLUSS (wöchentlich)", "T6": "FLUSS (wöchentlich)", "PV_ERW": "FLUSS (wöchentlich)",
}
DL_DE = "Datenbasis: MaStR-Gesamtdatenexport der Bundesnetzagentur, Lizenz dl-de/by-2.0."


@dataclass
class Buckets:
    """Die vier sauber getrennten Liefer-Buckets einer Region + Transparenz-Zähler."""

    region: str
    gebiet_id: str = ""
    lieferbar: list = field(default_factory=list)   # gewerblich, QA-ok, mit Name
    pending: list = field(default_factory=list)     # Grenzfälle in manueller QA
    namenlos: list = field(default_factory=list)    # Privatperson (redacted) -> Anreicherung
    rejected: list = field(default_factory=list)
    colocated_ausgeschlossen: int = 0               # wegen Speicher am Standort verworfen (Transparenz)
    roh: int = 0

    def betriebe(self) -> int:
        """Distinct ABR unter den Lieferbaren — ehrliche Dichte: ein Lead = ein Betrieb (Q4)."""
        return len({r.betreiber_mastr_nr for r in self.lieferbar if r.betreiber_mastr_nr})


def run_region(con, qa_con, *, plz_prefixes, region, gebiet_id="", resolve=True, index=None) -> Buckets:
    """cohort -> qualify -> QA -> (Evidenz-Auflösung); gibt die vier Buckets zurück."""
    index = index if index is not None else build_storage_index(con)
    stats: dict = {}
    recs = list(cohort.cohort_signals(con, index, plz_prefixes=tuple(plz_prefixes),
                                      region=region, stats=stats))
    hierarchy.enrich_and_qualify(recs, con)
    for r in recs:
        qa_gate.apply_qa(r, qa_con)
    b = Buckets(region=region, gebiet_id=gebiet_id, roh=len(recs),
                colocated_ausgeschlossen=stats.get("colocated_ausgeschlossen", 0))
    for r in recs:
        if not r.entity:
            b.namenlos.append(r)
        elif r.qa_status == qa_gate.REJECTED:
            b.rejected.append(r)
        elif r.qa_status in (qa_gate.AUTO_OK, qa_gate.APPROVED):
            b.lieferbar.append(r)
        else:
            b.pending.append(r)
    b.lieferbar.sort(key=lambda r: (r.dv_flag, r.kwp or 0), reverse=True)
    if resolve and b.lieferbar:
        mastr_resolve.EvidenzResolver(cache_con=qa_con).resolve_records(b.lieferbar)
    return b


def liefer_mail(b: Buckets, *, kaeufer: str = "", funktion: str = "Speicher-Installateur",
                absender: str = "GoldenTime", max_zeilen: int | None = 25) -> str:
    """Käufer-Liefer-Mail im Signal-Format (Stempel · Buckets-Legende · Exklusivität · Evidenz-Links)."""
    heute = dt.date.today()
    arten = sorted({TRIGGER_ART.get(r.trigger_typ, r.trigger_typ) for r in b.lieferbar}) or ["BESTAND (einmalig)"]
    trigger = ", ".join(sorted({r.trigger_typ for r in b.lieferbar})) or "T2"
    zeilen = b.lieferbar if max_zeilen is None else b.lieferbar[:max_zeilen]
    L = [
        f"Betreff: Gewerbespeicher-Leads {b.region} — {len(b.lieferbar)} Signale "
        f"(KW {heute.isocalendar().week}/{heute.year})",
        "",
        f"Hallo{(' ' + kaeufer) if kaeufer else ''},",
        "",
        f"hier die qualifizierten Kaufsignale für {b.region} (Stand {heute.isoformat()}). Jedes Signal",
        "ist ein Betrieb mit erkennbarem Kaufanlass — exklusiv für dich in deiner Spur.",
        "",
        f"WAS DRIN IST: {len(b.lieferbar)} lieferbare gewerbliche Signale ({b.betriebe()} Betriebe). "
        f"Trigger-Art: {', '.join(arten)}.",
        f"Zurückgehalten (Qualität): {len(b.pending)} Grenzfälle in manueller Prüfung, "
        f"{len(b.namenlos)} Privatpersonen (kein Gewerbe-Kontakt).",
        f"Exklusivität: {funktion} × {b.region} × {trigger} — exklusiv für dich, vertraglich zugesichert.",
        "",
        "Je Signal: Betrieb · kWp · Ort · Trigger · Konfidenz · Speicher-Status · Evidenz "
        "(öffentliche MaStR-Detailseite, 1 Klick).",
        "",
    ]
    for i, r in enumerate(zeilen, 1):
        dv = " [DV-pflichtig ≥100 kWp]" if r.dv_flag else ""
        L.append(f"{i:2d}. {r.entity}  ·  {(r.kwp or 0):.0f} kWp  ·  {r.plz or '?????'} {r.ort or ''}  ·  {r.trigger_typ}{dv}")
        L.append(f"    Konfidenz {r.konfidenz} · {r.speicher_label} · Inbetriebnahme {r.datum or '—'}")
        L.append(f"    Nachweis: {r.evidenz_url}  (MaStR-Nr. {r.einheit_mastr_nr})")
    if max_zeilen is not None and len(b.lieferbar) > max_zeilen:
        L.append(f"    … und {len(b.lieferbar) - max_zeilen} weitere in der beigefügten CSV.")
    L += [
        "",
        "Hinweis Speicher: „kein Speicher gemeldet\" = im MaStR nicht eingetragen (~9 % sind un-/spät",
        "registriert) — kein 100-%-Beweis, aber belastbares Signal. Frische/Trigger pro Lead transparent.",
        "",
        DL_DE,
        f"— {absender}",
    ]
    return "\n".join(L)


def mengen_report(buckets: list) -> str:
    """Ehrlicher Mengen-/Dichte-Report: je Gebiet Betriebe UND Einheiten, T2=Bestand / T1·T4=Fluss."""
    L = [
        "EHRLICHER MENGEN-/DICHTE-REPORT (Zweit-Review TEIL 5)",
        f"Stand {dt.date.today().isoformat()} · Zählung: Betriebe (distinct ABR) UND Einheiten · Trigger T2",
        "",
        f"{'Gebiet':16s} {'Art':12s} {'Betriebe':>9s} {'Einheiten':>10s} {'QA-pend':>8s} "
        f"{'namenlos':>9s} {'coloc-aus':>10s} {'roh':>6s}",
        "-" * 86,
    ]
    s_betr = s_einh = 0
    for b in buckets:
        L.append(f"{b.region[:16]:16s} {'BESTAND':12s} {b.betriebe():>9d} {len(b.lieferbar):>10d} "
                 f"{len(b.pending):>8d} {len(b.namenlos):>9d} {b.colocated_ausgeschlossen:>10d} {b.roh:>6d}")
        s_betr += b.betriebe()
        s_einh += len(b.lieferbar)
    L += [
        "-" * 86,
        f"{'Σ':16s} {'':12s} {s_betr:>9d} {s_einh:>10d}",
        "",
        "Lesart (Pricing-relevant, NICHT geschönt):",
        "· T2 (Post-EEG) ist BESTAND — die Kohorte wird EINMAL ausgeschöpft, danach kein Nachschub.",
        "· Wiederkehrender FLUSS (Retainer-Basis) kommt aus T1/T4 (Wochen-Diff), sobald ein 2. Snapshot",
        "  vorliegt — diese Zahlen stehen erst nach dem ersten echten Wochen-Diff.",
        "· 'Betriebe' < 'Einheiten': ein Betrieb mit mehreren Anlagen = EIN Lead (ein Anruf, ein Entscheider).",
    ]
    return "\n".join(L)
