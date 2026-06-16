"""
Register-Adapter (Komponente 1 / D4): quell-spezifische Implementierungen des
``register.RegisterAdapter``-Protocols.

Vorerst nur ``mastr.MastrAdapter`` (open-mastr-Gesamtdatenexport) — KEIN zweites Register
(YAGNI). Das Protocol + ``NormalizedUnit`` liegen in ``pipeline.register``.
"""
from .mastr import MastrAdapter

__all__ = ["MastrAdapter"]
