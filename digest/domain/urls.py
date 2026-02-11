"""Utilidades de URL: normalización para dedup y filtro de ya enviados."""

from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Normaliza una URL para deduplicación y comparación con el historial de enviados.

    - Elimina fragmento (#...) y query (?...) para considerar la misma página.
    - Normaliza esquema a minúsculas y host a minúsculas.
    - Elimina trailing slash en path (opcional pero coherente).
    - No modifica mayúsculas/minúsculas del path (algunos servidores son case-sensitive).

    Usado en: dedup (paso 4) y filtro de ya enviados (paso 5) del flujo de datos.
    """
    if not url or not url.strip():
        return ""
    s = url.strip()
    parsed = urlparse(s)
    # Reconstruir sin fragment ni query; esquema y netloc en minúsculas
    normalized = urlunparse(
        (
            parsed.scheme.lower() if parsed.scheme else "",
            parsed.netloc.lower() if parsed.netloc else "",
            parsed.path.rstrip("/") or "/",
            "",  # params
            "",  # query
            "",  # fragment
        )
    )
    return normalized
