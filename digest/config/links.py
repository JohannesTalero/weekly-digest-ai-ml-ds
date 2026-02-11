"""Lectura de config/links.md: una URL por línea, opcionalmente título (RF-05)."""

from pathlib import Path

from digest.domain.models import Item


def load_links(path: str | Path) -> list[Item]:
    """
    Lee config/links.md: una URL por línea, opcionalmente título en la misma línea.

    - Ignora líneas vacías y comentarios (líneas que empiezan por #).
    - Formato: URL sola o "URL  título/resto de línea".
    - Devuelve ítems con source="manual".
    """
    p = Path(path)
    if not p.exists():
        return []

    items: list[Item] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # URL + opcional título: primera palabra/token que parezca URL es la URL, resto título
        parts = stripped.split(maxsplit=1)
        url = parts[0].strip()
        if not url or not _looks_like_url(url):
            continue
        title = parts[1].strip() if len(parts) > 1 else ""
        items.append(Item(title=title, url=url, source="manual"))
    return items


def _looks_like_url(s: str) -> bool:
    """Heurística: empieza por http:// o https://."""
    return s.startswith("http://") or s.startswith("https://")
