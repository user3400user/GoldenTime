"""
Export-Adapter: MaStR-Gesamtdatenexport -> lokale SQLite, via open-mastr.

Das ist der Einstieg ins B-Backbone (Architektur-Entscheid 14.06.). open-mastr lädt das
tägliche ZIP (~2,96 GB komprimiert, Stand vom Vortag ~05:00) und schreibt die gewählten
Objekte in SQLite. Wichtig (R3/SQ2): KEIN inkrementelles Update — pro Lauf voller
Tagesstand; ``method="API"`` ist seit >v0.16.0 entfernt, Default ist Bulk.

Bewusst dünn: Der eigentliche Download gehört auf das ZBook (3-GB-Handling, Zeit). Die
Query-/Normalisierungs-Logik (speicher_check, normalize) braucht open-mastr NICHT und ist
gegen ein synthetisches SQLite getestet (tests/). open-mastr wird erst hier importiert,
damit der Rest ohne die Schwergewichts-Abhängigkeit läuft.

Guardrail (Architektur-Doku §6): Entpuppt sich der Lauf als >~2 CC-Sessions (Format-Bruch
01.10.2025, 3-GB-Handling), auf den CSV-Demo-Pfad (make_sample.py) zurückfallen und B nach
dem 27.06.-Gate fertigstellen.
"""
from __future__ import annotations

import logging
from pathlib import Path

from . import config

log = logging.getLogger(__name__)


def build_db(
    data: tuple[str, ...] = config.OPENMASTR_DATA,
    engine: str = "sqlite",
) -> Path:
    """Lädt den Gesamtdatenexport via open-mastr in eine lokale SQLite.

    Args:
        data:   Objekt-Auswahl (open-mastr ``data=``). Default = solar+storage+location+market.
        engine: "sqlite" (Default) oder ein SQLAlchemy-Engine-String für Postgres.

    Returns:
        Pfad zur befüllten SQLite-DB.

    Raises:
        ImportError: open-mastr nicht installiert (siehe requirements.txt).
    """
    try:
        from open_mastr import Mastr
    except ImportError as exc:  # pragma: no cover - reine Abhängigkeits-Weiche
        raise ImportError(
            "open-mastr ist nicht installiert.  pip install -r pipeline/requirements.txt\n"
            "Für die reine Query-/Normalisierungs-Logik wird es nicht gebraucht (tests/ laufen ohne)."
        ) from exc

    log.info("open-mastr Bulk-Download startet (data=%s) — das ~3-GB-ZIP kann dauern.", data)
    db = Mastr(engine=engine)
    # method='bulk' ist seit >v0.16.0 Default; explizit für Klarheit.
    db.download(method="bulk", data=list(data))
    log.info("Export geladen -> %s", config.DEFAULT_DB_PATH)
    # open-mastr schreibt an den Standardpfad; exakten Pfad beim ersten Realdownload
    # gegen `Mastr`-Attribute verifizieren, falls abweichend.
    return config.DEFAULT_DB_PATH
