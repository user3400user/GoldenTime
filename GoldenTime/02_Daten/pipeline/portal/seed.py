"""
Synthetische Demo-Leads fürs Kundenportal (Loop 3, §0-sicher).

Komplett ERFUNDENE Gewerbe-PV-Betriebe (juristische Personen, GmbH) — NULL echte Personendaten, damit
die Portal-Demo den Sample-Daten-Anspruch (DoD §9.4) bulletproof erfüllt. Ein ``evidenz_url`` zeigt auf
die öffentliche MaStR-Suchmaske (kein erfundener Direktlink). Befüllt ``portal_lead`` (demo=1).
"""
from __future__ import annotations

import sqlite3

from ..signal import mastr_suchlink

# (see, entity, kwp, plz, ort, trigger, datum) — je Gebiet ein paar plausible, ERFUNDENE Betriebe.
SAMPLE_LEADS: dict[str, list[tuple]] = {
    "muensterland": [
        ("SEE-DEMO-MS-01", "Wiesmann Metallbau GmbH", 180.0, "48143", "Münster", "T2", "2006-05-01"),
        ("SEE-DEMO-MS-02", "Telgte Logistik & Lager GmbH", 320.0, "48291", "Telgte", "T2", "2007-03-12"),
        ("SEE-DEMO-MS-03", "Coesfeld Kunststofftechnik GmbH", 96.0, "48653", "Coesfeld", "T2", "2006-09-20"),
        ("SEE-DEMO-MS-04", "Hörstmann Agrar GmbH & Co. KG", 540.0, "59302", "Oelde", "T2", "2007-06-30"),
        ("SEE-DEMO-MS-05", "Borken Werkzeugbau GmbH", 132.0, "46325", "Borken", "T2", "2006-11-05"),
    ],
    "osnabrueck": [
        ("SEE-DEMO-OS-01", "Hasetal Lebensmittel GmbH", 240.0, "49074", "Osnabrück", "T2", "2006-04-18"),
        ("SEE-DEMO-OS-02", "Bramsche Textilveredelung GmbH", 88.0, "49565", "Bramsche", "T2", "2007-02-09"),
        ("SEE-DEMO-OS-03", "Melle Maschinenbau GmbH", 410.0, "49324", "Melle", "T2", "2006-08-22"),
        ("SEE-DEMO-OS-04", "Georgsmarienhütte Galvanik GmbH", 165.0, "49124", "GMHütte", "T2", "2007-05-14"),
    ],
}


def seed_demo_leads(con: sqlite3.Connection) -> int:
    """Setze die Demo-Leads frisch (ersetzt vorhandene demo=1-Leads). Gibt die eingefügte Anzahl zurück."""
    con.execute("DELETE FROM portal_lead WHERE demo = 1")
    n = 0
    for gebiet, leads in SAMPLE_LEADS.items():
        for see, entity, kwp, plz, ort, trig, datum in leads:
            con.execute(
                "INSERT INTO portal_lead(gebiet, see, entity, kwp, plz, ort, trigger, datum, evidenz_url, demo) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (gebiet, see, entity, kwp, plz, ort, trig, datum, mastr_suchlink(see)),
            )
            n += 1
    con.commit()
    return n
