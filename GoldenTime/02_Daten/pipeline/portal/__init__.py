"""Kundenportal (Loop 3) — Auth + Mandanten-Sicht auf Liefer-Leads, stdlib http.server.

Subpakete: ``auth`` (Kunden/Sessions/Mandanten-Filter, reine Funktionen), ``views`` (HTML),
``app`` (HTTP-Hülle), ``seed`` (synthetische Demo-Leads für die Sample-Daten-Demo, §0-sicher).
"""
from . import auth, seed, views

__all__ = ["auth", "seed", "views"]
