"""
Komponente 8 — Admin-Dashboard (K8, Briefing §6): interne Steuer-Schicht.

Schlanker stdlib-``http.server``, KEIN Framework. LIEST Config-Store + Metriken (read-only) +
Ledger-Overview; SCHREIBT ausschliesslich Config-Store-Schalter (Trigger/Module/Gebiete). NIEMALS
in die Pipeline-Logik — importiert nur ``control`` + ``ledger`` (Briefing §6, einseitige Kopplung).

  views — reine Render-Funktionen (HTML, ohne Server testbar): ``render_dashboard``
  app   — HTTP-Hülle (``serve``) + Schalter-Mutation (``apply_toggle``)
"""
from .app import apply_toggle, gather_view_data, serve
from .views import render_dashboard

__all__ = ["render_dashboard", "apply_toggle", "gather_view_data", "serve"]
