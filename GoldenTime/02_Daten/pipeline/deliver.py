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

from .control import metrics
from .enrich import mastr_resolve
from .ledger import ledger as ledgermod
from .qualify import hierarchy, qa_gate
from .speicher_check import GEPLANT, build_storage_index
from .triggers import cohort

# T2/T3 = Bestand (Kohorte, einmal ausschöpfbar); Diff-Trigger = Fluss (wiederkehrend pro Woche).
TRIGGER_ART = {
    "T2": "BESTAND (einmalig)", "T3": "BESTAND (einmalig)",
    "T1": "FLUSS (wöchentlich)", "T4": "FLUSS (wöchentlich)",
    "T5": "FLUSS (wöchentlich)", "T6": "FLUSS (wöchentlich)", "PV_ERW": "FLUSS (wöchentlich)",
}
# dl-de/by-2.0 erlaubt den kommerziellen Resale abgeleiteter Datensätze — Pflicht ist der Quellenvermerk
# (G24: Lizenz-URL + 'kein amtlicher Datensatz/keine Gewähr'-Disclaimer im Wortlaut, in Mail UND CSV).
DL_DE = ("Datenbasis: Marktstammdatenregister (MaStR) der Bundesnetzagentur, Lizenz dl-de/by-2.0 "
         "(https://www.govdata.de/dl-de/by-2-0). Kein amtlicher Datensatz, keine Gewähr — "
         "abgeleitete Auswertung; Quelle: Bundesnetzagentur, Marktstammdatenregister.")


@dataclass
class Buckets:
    """Die vier sauber getrennten Liefer-Buckets einer Region + Transparenz-Zähler."""

    region: str
    gebiet_id: str = ""
    lieferbar: list = field(default_factory=list)   # gewerblich, QA-ok, mit Name, e.K.-gefiltert
    pending: list = field(default_factory=list)     # Grenzfälle in manueller QA
    namenlos: list = field(default_factory=list)    # Privatperson (redacted) -> Anreicherung
    rejected: list = field(default_factory=list)
    nat_person_gesperrt: list = field(default_factory=list)  # e.K./nat. Person — §0-Hartfilter (Default)
    speicher_geplant: list = field(default_factory=list)  # Speicher am Standort in Planung -> Re-Opportunity
    colocated_ausgeschlossen: int = 0               # wegen Speicher am Standort (In Betrieb) verworfen
    roh: int = 0
    ledger_trigger: str = ""                        # Trigger-Schlüssel fürs Ledger (reserve/record_delivery)

    def betriebe(self) -> int:
        """Distinct ABR unter den Lieferbaren — ehrliche Dichte: ein Lead = ein Betrieb (Q4)."""
        return len({r.betreiber_mastr_nr for r in self.lieferbar if r.betreiber_mastr_nr})


def run_region(con, qa_con, *, plz_prefixes, region, gebiet_id="", resolve=True, index=None,
               kaeufer="", funktion="", trigger=None, nat_personen_frei=False) -> Buckets:
    """cohort -> qualify -> QA -> e.K.-Hartfilter (§0) -> optionale Ledger-VORSCHAU -> Evidenz.

    **Schreibt NIE ins Ledger.** Bei ``kaeufer``+``funktion`` wird nur READ-ONLY vorgefiltert
    (Exklusivität via ``is_available`` + Dedupe via ``already_delivered``) — der echte ``--commit``
    (reserve + record_delivery, ``BEGIN IMMEDIATE``) passiert bewusst erst im CLI nach dem
    ``LIVE_DELIVERY_ENABLED``-Guard. Default = Dry-Run-Vorschau (0 Ledger-Zeilen). Gibt die Buckets zurück.

    ``nat_personen_frei`` (aus ``config_store.natuerliche_personen_freigegeben``, Default False) AUS →
    natürliche Personen / e.K. werden HART aus ``lieferbar`` in ``nat_person_gesperrt`` umgeleitet,
    qa-unabhängig (übersteuert auch ein versehentliches ``approve``) — die §0-Rechts-Invariante (I7).
    """
    index = index if index is not None else build_storage_index(con)
    trig = trigger or cohort.TRIGGER_KEY
    stats: dict = {}
    recs = list(cohort.cohort_signals(con, index, plz_prefixes=tuple(plz_prefixes),
                                      region=region, stats=stats))
    hierarchy.enrich_and_qualify(recs, con)
    for r in recs:
        qa_gate.apply_qa(r, qa_con)
    b = Buckets(region=region, gebiet_id=gebiet_id, roh=len(recs),
                colocated_ausgeschlossen=stats.get("colocated_ausgeschlossen", 0), ledger_trigger=trig)
    for r in recs:
        if r.speicher_status == GEPLANT:           # eigener Bucket: nicht heiß, für Re-Opportunity
            b.speicher_geplant.append(r)
        elif not r.entity:
            b.namenlos.append(r)
        elif r.qa_status == qa_gate.REJECTED:
            b.rejected.append(r)
        elif r.qa_status in (qa_gate.AUTO_OK, qa_gate.APPROVED):
            b.lieferbar.append(r)
        else:
            b.pending.append(r)
    # e.K./natürliche Person HART aus lieferbar (qa-unabhängig, übersteuert approve) — §0/I7, über den
    # gemeinsamen Choke-Point. Carve-out => Reconciliation bleibt: lieferbar + nat_gesperrt + pending
    # + namenlos + rejected + geplant = roh.
    b.lieferbar, b.nat_person_gesperrt = hierarchy.partition_natuerliche(b.lieferbar, nat_personen_frei)
    b.lieferbar.sort(key=lambda r: (r.dv_flag, r.kwp or 0), reverse=True)
    # Ledger-VORSCHAU (read-only): gehört Gebiet×Trigger schon einem ANDEREN Käufer -> [] (Exklusivität);
    # schon an diesen Käufer gelieferte Einheiten fallen raus (Dedupe). KEIN Schreibvorgang.
    if kaeufer and funktion:
        b.lieferbar = ledgermod.filter_deliverable(qa_con, b.lieferbar, kaeufer, funktion, gebiet_id, trig)
    # Evidenz-Direktlinks setzen. Im Offline-Modus (resolve=False) GECACHTE IDs trotzdem anwenden
    # (cache_only) — sonst fällt jeder Nachweis auf die leere Suchmaske zurück, obwohl die ID im
    # Cache liegt (R4-Befund, demo-kritisch bei --offline).
    if b.lieferbar:
        mastr_resolve.EvidenzResolver(cache_con=qa_con).resolve_records(
            b.lieferbar, cache_only=not resolve)
    _record_metrics(b, qa_con, trigger=trig)
    return b


def _record_metrics(b: Buckets, qa_con, *, trigger: str = "T2") -> None:
    """Trichter-Kennzahlen je Gebiet in pipeline_state.db (Dashboard-Monitoring) — idempotent.

    R4-Befund: bisher schrieb NUR ``cmd_signals`` Metriken; gate-demo/liefern/mengen ließen das
    Monitoring stale/lückenhaft. ``metrics.record`` ist idempotent je (woche,gebiet,trigger,metrik),
    Mehrfachläufe ersetzen also nur. Ohne gebiet_id (anonyme Buckets in Tests) wird nichts geschrieben.
    """
    if not b.gebiet_id:
        return
    woche = metrics.iso_woche()
    for metrik, wert in (("signale", b.roh), ("lieferbar", len(b.lieferbar)),
                         ("pending_qa", len(b.pending)), ("namenlos", len(b.namenlos)),
                         ("nat_gesperrt", len(b.nat_person_gesperrt)),
                         ("speicher_geplant", len(b.speicher_geplant)),
                         ("dv_flag", sum(r.dv_flag for r in b.lieferbar))):
        metrics.record(qa_con, metrik=metrik, wert=wert, woche=woche, gebiet=b.gebiet_id, trigger=trigger)


def liefer_mail(b: Buckets, *, kaeufer: str = "", funktion: str = "Speicher-Installateur",
                absender: str = "GoldenTime", max_zeilen: int | None = 25) -> str:
    """Käufer-Liefer-Mail im Signal-Format (Stempel · Buckets-Legende · Exklusivität · Evidenz-Links)."""
    heute = dt.date.today()
    arten = sorted({TRIGGER_ART.get(r.trigger_typ, r.trigger_typ) for r in b.lieferbar}) or ["BESTAND (einmalig)"]
    trigger = ", ".join(sorted({r.trigger_typ for r in b.lieferbar})) or "T2"
    zeilen = b.lieferbar if max_zeilen is None else b.lieferbar[:max_zeilen]
    # Evidenz-Aussage ehrlich an den realen Auflösungsgrad koppeln (R0): nur wenn ALLE einen
    # aufgelösten Direktlink haben, ist es '1 Klick'; sonst offen ausweisen (Such-Link-Anteil).
    n_lief = len(b.lieferbar)
    direkt = sum(1 for r in b.lieferbar if getattr(r, "detail_id", None))
    if n_lief and direkt == n_lief:
        evidenz_satz = "Evidenz (öffentliche MaStR-Detailseite, 1 Klick)."
    elif direkt:
        evidenz_satz = (f"Evidenz: {direkt}/{n_lief} direkter MaStR-Detaillink, "
                        "Rest robuster Such-Link (MaStR-Nr. als Prüfnummer).")
    else:
        evidenz_satz = "Evidenz: öffentlicher MaStR-Such-Link (MaStR-Nr. als Prüfnummer)."
    L = [
        f"Betreff: Gewerbespeicher-Leads {b.region} — {len(b.lieferbar)} Signale "
        f"(KW {heute.isocalendar().week}/{heute.year})",
        "",
        f"Hallo{(' ' + kaeufer) if kaeufer else ''},",
        "",
        f"hier die qualifizierten Kaufsignale für {b.region} (Stand {heute.isoformat()}). Jedes Signal",
        "ist ein Betrieb mit erkennbarem Kaufanlass.",
        "",
        f"WAS DRIN IST: {len(b.lieferbar)} lieferbare gewerbliche Signale ({b.betriebe()} Betriebe). "
        f"Trigger-Art: {', '.join(arten)}.",
        f"Zurückgehalten: {len(b.pending)} QA-Grenzfälle, {len(b.namenlos)} Privatpersonen, "
        f"{len(b.speicher_geplant)} mit geplantem Speicher (Re-Opportunity, nicht heiß).",
        f"Exklusivität ({funktion}): Jeder gelieferte BETRIEB gehört ausschließlich dir — kein anderer",
        "Käufer dieser Funktion erhält ihn, gebiets- UND trigger-übergreifend (im Liefer-Ledger erzwungen,",
        f"erst mit bestätigter Lieferung wirksam). Dieses Paket: {b.region} × {trigger}. Du bekommst keinen",
        "Betrieb zweimal und keinen, der bereits einem anderen Käufer gehört.",
        "",
        f"Je Signal: Betrieb · kWp · Ort · Trigger · Konfidenz · Speicher-Status · {evidenz_satz}",
        "",
    ]
    for i, r in enumerate(zeilen, 1):
        dv = " [DV-pflichtig ≥100 kWp]" if r.dv_flag else ""
        L.append(f"{i:2d}. {r.entity}  ·  {(r.kwp or 0):.0f} kWp  ·  {r.plz or '?????'} {r.ort or ''}  ·  {r.trigger_typ}{dv}")
        L.append(f"    Konfidenz {r.konfidenz} (grob, nicht kalibriert) · {r.speicher_label} · Inbetriebnahme {r.datum or '—'}")
        gr = getattr(r, "konfidenz_gruende", None)
        gr_txt = " · ".join(str(g) for g in gr) if isinstance(gr, (list, tuple)) else str(gr or "")
        if gr_txt:
            L.append(f"      Konfidenz-Basis: {gr_txt}")
        L.append(f"    Nachweis: {r.evidenz_url}  (MaStR-Nr. {r.einheit_mastr_nr})")
    if max_zeilen is not None and len(b.lieferbar) > max_zeilen:
        L.append(f"    … und {len(b.lieferbar) - max_zeilen} weitere in der beigefügten CSV.")
    L += [
        "",
        "Hinweis Speicher: „kein Speicher gemeldet\" = im MaStR nicht eingetragen (~9 % sind un-/spät",
        "registriert) — kein 100-%-Beweis, aber belastbares Signal. Frische/Trigger pro Lead transparent.",
        "Hinweis Konfidenz: grober ordinaler Vertrauens-Indikator (0–1), KEINE kalibrierte",
        "Wahrscheinlichkeit — empirisch verankert ist nur der ~9-%-Abschlag für nicht gemeldete Speicher;",
        "übrige Abschläge sind benannte Heuristik (Konfidenz-Basis je Lead oben).",
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
        f"{'Gebiet':16s} {'Art':9s} {'Betriebe':>9s} {'Einheit.':>9s} {'eK-gesp':>8s} {'QA-pend':>8s} "
        f"{'namenlos':>9s} {'rejected':>9s} {'geplant':>8s} {'coloc-aus':>10s} {'roh':>6s}",
        "-" * 113,
    ]
    s_einh = 0
    for b in buckets:
        L.append(f"{b.region[:16]:16s} {'BESTAND':9s} {b.betriebe():>9d} {len(b.lieferbar):>9d} "
                 f"{len(b.nat_person_gesperrt):>8d} {len(b.pending):>8d} {len(b.namenlos):>9d} "
                 f"{len(b.rejected):>9d} {len(b.speicher_geplant):>8d} "
                 f"{b.colocated_ausgeschlossen:>10d} {b.roh:>6d}")
        s_einh += len(b.lieferbar)
    # Σ-Betriebe DISTINCT über alle Gebiete (R0): ein ABR mit Anlagen in mehreren Gebieten zählt 1×,
    # nicht je Gebiet — sonst Doppelzählung (real: 423 ABR betreiben in PLZ 48/59 UND 49).
    s_betr = len({r.betreiber_mastr_nr for b in buckets for r in b.lieferbar if r.betreiber_mastr_nr})
    L += [
        "-" * 113,
        f"{'Σ':16s} {'':9s} {s_betr:>9d} {s_einh:>9d}",
        "",
        "Lesart (Pricing-relevant, NICHT geschönt):",
        "· T2 (Post-EEG) ist BESTAND — die Kohorte wird EINMAL ausgeschöpft, danach kein Nachschub.",
        "· Wiederkehrender FLUSS (Retainer-Basis) kommt aus T1/T4 (Wochen-Diff), sobald ein 2. Snapshot",
        "  vorliegt — diese Zahlen stehen erst nach dem ersten echten Wochen-Diff.",
        "· 'eK-gesp' = e.K./natürliche Personen, hart aus 'lieferbar' gefiltert (§0, bis Anwalts-Freigabe).",
        "· 'Betriebe' < 'Einheiten': ein Betrieb mit mehreren Anlagen = EIN Lead (ein Anruf, ein Entscheider).",
        "· Σ 'Betriebe' = DISTINCT über alle Gebiete — ein ABR in mehreren Gebieten zählt 1×, daher kann",
        "  die Σ-Zeile kleiner sein als die Summe der Gebiets-Zeilen (keine Doppelzählung über Gebiete).",
        "· Reconciliation je Gebiet: lieferbar + eK-gesperrt + QA-pend + namenlos + rejected + geplant = roh",
        "  (coloc-aus liegt ausserhalb 'roh' — bereits vor der Qualifizierung verworfen).",
    ]
    return "\n".join(L)
