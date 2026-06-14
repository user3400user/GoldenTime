"""
MaStR-Lead-Pipeline (B-Backbone) — Gewerbespeicher-Leads.

Architektur-Entscheid FINAL 14.06. (R3 eingearbeitet): Der MaStR-Gesamtdatenexport ist
das Backbone. open-mastr lädt ihn als SQLite; die Verarbeitung kennt nur das
normalisierte Lead-Objekt (Adapter-Prinzip). Web-JSON/CSV (make_sample.py) bleiben als
Spot-Tool/Demo-Fallback.

Module:
  config           — Tabellen-/Spaltennamen, Katalog-Codes, Produkt-Konstanten (1 Quelle)
  db               — SQLite-Verbindung + tolerante Schema-Auflösung
  export_adapter   — open-mastr Bulk-Export -> lokale SQLite (Export-Adapter)
  speicher_check   — ABR-Speicher-Anywhere-Query (Kern, R3 §7a)
  normalize        — Roh-Solar-Zeile -> normalisiertes Lead-Objekt (Trigger, Frische)
  cli              — Einstiegspunkt (inspect / build-db / leads)

Geschäftskontext: 01_Strategie/STATE.md. Technik: ../../CLAUDE.md.
"""

__version__ = "0.1.0"
