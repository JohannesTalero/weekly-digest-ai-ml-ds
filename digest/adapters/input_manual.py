"""Adaptador enlaces manuales: ítems leídos de config/links.md; fuente = manual (T3.2)."""

from pathlib import Path

from digest.config.links import load_links
from digest.domain.models import Item


def fetch_manual_items(path: str | Path) -> list[Item]:
    """
    Devuelve ítems de enlaces manuales desde links.md.

    Usa la lectura ya implementada en config/links (T2.3); todos los ítems
    tienen source="manual". No hace llamadas de red.
    """
    return load_links(path)
