"""
Evidenz-URL-Resolver (Komponente 7-Teil) — SEE-Nummer -> interne MaStR-ID -> direkter Detail-Link.

Hintergrund (Zweit-Review, verkaufskritisch): die öffentliche Detailseite
``IndexOeffentlich/<ID>`` braucht eine INTERNE numerische ID. Die SEE-Nummer liefert dort HTTP 400,
und die ID liegt NICHT im Gesamtdatenexport. Wir lösen sie über die öffentliche MaStR-Web-JSON-API
auf (Session-Cookie + Filter auf die Display-Spalte ``MaStR-Nr. der Einheit``). Verifiziert:
SEE -> Id -> ``IndexOeffentlich/<Id>`` liefert HTTP 200.

Caching: pipeline_state.db ``mastr_url_cache`` — jede SEE wird nur EINMAL aufgelöst, Folgeläufe
treffen den Cache (höflich gegenüber der MaStR, schnell). Robust: bei fehlendem ``requests``,
Netz- oder API-Fehler bleibt ``detail_id`` None und der SignalRecord fällt auf den Such-Link zurück
(Übersicht + SEE als Prüf-Nummer) — KEIN Crash, kein Bau-Blocker.
"""
from __future__ import annotations

import datetime as dt
import logging
import time

log = logging.getLogger(__name__)

# Kleine Höflichkeits-Pause nach jedem ECHTEN Netz-Resolve (nicht bei Cache-Treffern) — schont den
# öffentlichen MaStR-Server (Modul-Designziel). Cache-Läufe bleiben sofort.
_PAUSE_S = 0.15

_OVERVIEW = "https://www.marktstammdatenregister.de/MaStR/Einheit/Einheiten/OeffentlicheEinheitenuebersicht"
_JSON = ("https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/"
         "GetErweiterteOeffentlicheEinheitStromerzeugung")
_DETAIL = "https://www.marktstammdatenregister.de/MaStR/Einheit/Detail/IndexOeffentlich/{}"
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/124.0 Safari/537.36")
_MISS = object()   # Sentinel: Cache-Miss (unterscheidbar von gecachtem None)


class EvidenzResolver:
    """Löst SEE -> interne MaStR-ID auf, mit lazy Session + optionalem persistenten Cache."""

    def __init__(self, cache_con=None, timeout: float = 25.0):
        self._session = None         # None=ungestartet, False=offline-Sentinel, Session=aktiv
        self._cache_con = cache_con  # optionale state.connect()-Verbindung (mastr_url_cache)
        self._mem: dict[str, int | None] = {}
        self._timeout = timeout

    # --- Session (lazy, fällt bei Fehler in den Offline-Modus) ---
    def _session_or_none(self):
        if self._session is None:
            try:
                import requests
                s = requests.Session()
                s.headers.update({"User-Agent": _UA, "X-Requested-With": "XMLHttpRequest",
                                  "Referer": _OVERVIEW})
                s.get(_OVERVIEW, timeout=self._timeout)   # Session-Cookie holen
                self._session = s
            except Exception as e:   # requests fehlt ODER Netz weg -> Fallback-Modus
                log.warning("Evidenz-Resolver offline (%s) — Signale nutzen den Such-Link.", e)
                self._session = False
        return self._session or None

    # --- Cache ---
    def _cache_get(self, see):
        if see in self._mem:
            return self._mem[see]
        if self._cache_con is not None:
            try:
                row = self._cache_con.execute(
                    "SELECT detail_id FROM mastr_url_cache WHERE einheit_mastr_nr = ?", (see,)).fetchone()
            except Exception as e:   # Cache ist Optimierung, nie Abbruchgrund (R0-Härtung)
                log.debug("Cache-Lesen für %s fehlgeschlagen: %s", see, e)
                return _MISS
            if row is not None:
                self._mem[see] = row[0]
                return row[0]
        return _MISS

    def _cache_put(self, see, detail_id):
        self._mem[see] = detail_id
        if self._cache_con is not None and detail_id is not None:   # Misses NICHT persistieren
            try:
                self._cache_con.execute(
                    "INSERT OR REPLACE INTO mastr_url_cache(einheit_mastr_nr, detail_id, resolved_at) "
                    "VALUES(?, ?, ?)",
                    (see, int(detail_id), dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))
                self._cache_con.commit()
            except Exception as e:   # DB locked/zu/voll -> Lauf NICHT abbrechen (Docstring-Vertrag, R0-Härtung)
                log.debug("Cache-Schreiben für %s fehlgeschlagen: %s", see, e)

    # --- Auflösung ---
    def resolve_id(self, see: str) -> int | None:
        """SEE -> interne MaStR-ID (oder None, wenn nicht auflösbar/offline)."""
        if not see:
            return None
        cached = self._cache_get(see)
        if cached is not _MISS:
            return cached
        detail_id = None
        s = self._session_or_none()
        if s is not None:
            try:
                d = s.get(_JSON, params={
                    "sort": "", "page": 1, "pageSize": 1, "group": "",
                    "filter": f"MaStR-Nr. der Einheit~eq~'{see}'",
                }, timeout=self._timeout).json()
                data = d.get("Data") or []
                if data and data[0].get("Id"):
                    detail_id = int(data[0]["Id"])
            except Exception as e:
                log.debug("Auflösung %s fehlgeschlagen: %s", see, e)
            time.sleep(_PAUSE_S)   # nur bei echtem Netz-Call (Cache-Treffer kehren oben früher zurück)
        self._cache_put(see, detail_id)
        return detail_id

    def resolve_records(self, records) -> int:
        """Setze ``record.detail_id`` für jeden Record. Gibt die Zahl aufgelöster Direktlinks zurück."""
        n = 0
        for r in records:
            mid = self.resolve_id(getattr(r, "einheit_mastr_nr", None))
            if mid:
                r.detail_id = mid
                n += 1
        return n


def validate_urls(records, *, sample: int = 10, timeout: float = 20.0) -> dict:
    """Stichproben-Erreichbarkeitscheck der Evidenz-URLs (TEIL 5): liefert {ok, fehler, geprüft, details}.

    Prüft bis zu ``sample`` Record-URLs auf HTTP 200. Reine Verifikation (keine Mutation). Bei
    fehlendem ``requests`` wird ``geprüft=0`` zurückgegeben (offen kommuniziert, nicht vorgetäuscht).
    """
    out = {"ok": 0, "fehler": 0, "geprueft": 0, "details": []}
    try:
        import requests
    except Exception:
        out["hinweis"] = "requests nicht verfügbar — URL-Validierung übersprungen."
        return out
    for r in records[:sample]:
        url = r.evidenz_url
        try:
            code = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout).status_code
        except Exception as e:
            code = f"EXC {e}"
        ok = code == 200
        out["geprueft"] += 1
        out["ok" if ok else "fehler"] += 1
        out["details"].append((r.einheit_mastr_nr, bool(r.detail_id), url, code))
    return out
