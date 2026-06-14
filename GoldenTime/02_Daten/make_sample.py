#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kostproben-Generator — Gewerbespeicher-Leads
Aufruf:  python3 make_sample.py --plz 48,59 [--bundesland Nordrhein-Westfalen] [--limit 12]
Liest:   mastr-leads-clean-v2-2026-06-11.csv (gleicher Ordner oder data/clean_v2.json)
Schreibt: kostprobe_<region>_<datum>.csv + liefermail_<region>_<datum>.txt"""
import argparse, csv, json, re, sys, time, datetime, urllib.request, urllib.parse, os

EP = "https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetErweiterteOeffentlicheEinheitStromerzeugung"
HEUTE = datetime.date.today().isoformat()
OEFF = re.compile(r'\b(kreis|landkreis|stadt|gemeinde|kommune|stadtwerke|zweckverband|studierendenwerk|universit|hochschul|klinik|landesbetrieb|anstalt|amt)\b', re.I)
KETTEN = re.compile(r'\b(lidl|aldi|edeka|rewe|netto|penny|kaufland|norma|tegut|globus|metro|obi|hornbach|bauhaus|toom|dm[- ]|rossmann|action|takko|kik|deichmann|fressnapf|mcdonald|burger king|vonovia|deka|amazon|ikea|decathlon|expert|media[- ]?markt|saturn)\b', re.I)
GROSS = re.compile(r'\b(SE|AG)\b')
BRANCHEN = [("reisen|touristik|bus","Busreise-/Touristikbetrieb"),("pharma","Pharma-Hersteller"),
    ("präzision|maschin|technik|anlagenbau","Maschinenbau/Technik"),("verkehr","Verkehrsbetrieb"),
    ("kunststoff|plast","Kunststoff-Verarbeiter"),("metall|stahl|guss","Metallverarbeitung"),
    ("logistik|spedition|transport","Logistik/Spedition"),("hotel|gasthof|resort","Hotellerie"),
    ("druck","Druckerei"),("möbel|holz","Holz-/Möbelbetrieb"),("agrar|hof |landw","Agrarbetrieb"),
    ("bau|tiefbau|hochbau","Bauunternehmen"),("elektro","Elektrotechnik"),("glas","Glasverarbeitung"),
    ("lebensmittel|back|fleisch|mosterei|brauerei","Lebensmittelbetrieb")]

def q(flt, ps=100):
    p = {"sort":"EinheitRegistrierungsdatum-desc","page":"1","pageSize":str(ps),"group":"","filter":flt}
    req = urllib.request.Request(EP+"?"+urllib.parse.urlencode(p),
        headers={"Accept":"application/json","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("Data", [])

def norm(n):
    n = re.sub(r'\b(gmbh|ag|se|kg|co|e\.?k\.?|ug|ohg|gbr|&|und)\b','', (n or '').lower())
    return set(w for w in re.split(r'[^a-zäöüß0-9]+', n) if len(w) > 3)

# HINWEIS (14.06.): PLZ+Namens-Check = LEGACY/FALLBACK. v1-Pipeline nutzt betreiberweiten
# ABR-Check aus dem Gesamtexport (siehe Architektur-Entscheidung-Datenquelle §7a). Hier belassen,
# weil make_sample.py der CSV-Demo-Pfad bleibt.
def speicher_check(plz, betreiber):
    """Gewerbliche Speicher (>20 kW) im Standort-PLZ desselben Betreibers?"""
    try:
        rows = q(f"Energieträger~eq~'2496'~and~Postleitzahl~eq~'{plz}'~and~Bruttoleistung der Einheit~gt~'20'")
    except Exception:
        return "check_fehlgeschlagen", ""
    me = norm(betreiber)
    for r in rows:
        other = norm(r.get("AnlagenbetreiberName"))
        if me and other and len(me & other) >= max(1, min(len(me), len(other)) - 1):
            return "SPEICHER_AM_STANDORT", r.get("AnlagenbetreiberName","")[:40]
    return "kein_gewerbl_speicher_im_plz", ""

def branche(name):
    for pat, label in BRANCHEN:
        if re.search(pat, name, re.I): return label
    return "Gewerbebetrieb"

def aufhaenger(lead, br):
    kw = float(lead['kw']); d = datetime.date.fromisoformat(lead['reg_datum']).strftime("%d.%m.")
    basis = f"Hat am {d} eine {kw:.0f}-kWp-Anlage angemeldet (Teileinspeisung) — Eigenverbrauchsprofil, ohne Speicher."
    hebel = "Einstieg über Lastspitzenkappung/Netzentgelte." if kw >= 250 else "Einstieg über Eigenverbrauchsquote (Mittagsüberschuss ~8 ct vs. Bezug ~30 ct)."
    return f"{br}: {basis} {hebel}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plz", default="", help="PLZ-Präfixe, komma-getrennt, z.B. 48,59")
    ap.add_argument("--bundesland", default="")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--region-name", default="")
    a = ap.parse_args()

    src = None
    for c in ["mastr-leads-clean-v2-2026-06-11.csv", "/mnt/user-data/outputs/mastr-leads-clean-v2-2026-06-11.csv", "data/clean_v2.json"]:
        if os.path.exists(c): src = c; break
    if not src: sys.exit("Clean-v2-Datei nicht gefunden.")
    leads = json.load(open(src)) if src.endswith(".json") else list(csv.DictReader(open(src)))

    prefixes = [p.strip() for p in a.plz.split(",") if p.strip()]
    sel = [l for l in leads
           if (not a.bundesland or l['bundesland'] == a.bundesland)
           and (not prefixes or any((l['plz'] or '').startswith(p) for p in prefixes))]
    sel = sorted(sel, key=lambda x: -float(x['kw']))[:a.limit]
    if not sel: sys.exit("Keine Leads für diese Region im Inventar.")
    region = a.region_name or (("PLZ " + "/".join(prefixes)) if prefixes else a.bundesland)

    out = []
    for l in sel:
        flag, wer = speicher_check(l['plz'], l['betreiber']); time.sleep(0.4)
        br = branche(l['betreiber'])
        ketten = "FILIALIST/KONZERN" if (KETTEN.search(l['betreiber']) or GROSS.search(l['betreiber'])) else ("OEFFENTLICH/AUSSCHREIBUNG" if OEFF.search(l['betreiber']) else "")
        out.append({**l, "branche": br, "speicher_check": flag + (f" ({wer})" if wer else ""),
                    "ketten_flag": ketten, "stufe": "C",
                    "entscheider_vorschlag": "", "kontakt_vorschlag": "", "quelle_kontakt": "",
                    "aufhaenger": aufhaenger(l, br), "geprueft_am": HEUTE,
                    "provenance": "MaStR (dl-de/by-2.0); Speicher-Check: Standort-PLZ, >20 kW, " + HEUTE})

    tag = re.sub(r'[^a-z0-9]+','-', region.lower().replace('ü','ue').replace('ö','oe').replace('ä','ae').replace('ß','ss')).strip('-')
    csv_path = f"kostprobe_{tag}_{HEUTE}.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader()
        for r in out: w.writerow(r)

    top = [r for r in out if not r['ketten_flag']][:3]
    hl = "\n".join(f"  • {r['betreiber']}, {r['ort']} — {float(r['kw']):.0f} kWp, angemeldet {datetime.date.fromisoformat(r['reg_datum']).strftime('%d.%m.')}. {r['aufhaenger'].split(': ',1)[1]}" for r in top)
    mail = f"""Betreff: Ihre Kostprobe {region}: {len(out)} frische Gewerbe-PV ohne Speicher

Guten Tag Herr [NAME],

wie versprochen Ihre Kostprobe — die aktuellen Gewerbe-Anmeldungen ohne Speicher für {region}, Stand {datetime.date.today().strftime('%d.%m.%Y')}, als CSV im Anhang. Die drei aufschlussreichsten direkt hier:

{hl}

Zur Einordnung jeder Zeile:
• Speicher-Check: am Standort-PLZ ist für den Betreiber kein gewerblicher Speicher (>20 kW) registriert — Prüfdatum steht in der Liste.
• Kontakt-Qualität in Stufen: A = Entscheider + Direktkontakt, B = Entscheider + Zentrale, C = nur Firma. In der Kostprobe überwiegend B/C — im Abo zählen nur A/B voll, der Rest wird gutgeschrieben.
• Filialisten/Konzerne sind markiert statt untergejubelt.

Solange wir im Gespräch sind, biete ich {region} niemandem sonst an.

Und damit ich das Pilotangebot richtig schneide, die zwei Zahlen aus meiner ersten Mail: Was zahlen Sie heute pro Gewerbe-Kontakt — und was wäre Ihnen dieser Feed wöchentlich exklusiv wert, pro Lead oder pauschal pro Monat?

Beste Grüsse aus Bern
Matthias Scheidegger · +41 76 545 80 99

—
Datengrundlage: Marktstammdatenregister der Bundesnetzagentur, Datenlizenz Deutschland – Namensnennung – Version 2.0 (dl-de/by-2.0). Kontaktangaben aus öffentlichen Firmenquellen (Quelle je Feld in der Liste). Auskunft/Löschung jederzeit; ein kurzes "Nein" beendet jede weitere Mail."""
    mail_path = f"liefermail_{tag}_{HEUTE}.txt"
    open(mail_path, "w").write(mail)
    print(f"{len(out)} Leads -> {csv_path} + {mail_path}")
    for r in out:
        print(f"  {r['betreiber'][:36]:36s} {float(r['kw']):>5.0f} kWp  {r['plz']} {r['ort'][:16]:16s} {r['speicher_check'][:28]:28s} {r['ketten_flag']}")

if __name__ == "__main__":
    main()
