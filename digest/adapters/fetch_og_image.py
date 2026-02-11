"""Extracción de imagen OG (Open Graph) de URLs de artículos para el email del digest."""

import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_UA = "DigestBot/1.0 (weekly AI/ML digest)"
FETCH_TIMEOUT = 5.0


def fetch_og_image(url: str, *, timeout: float = FETCH_TIMEOUT) -> str | None:
    """
    Obtiene la URL de la imagen OG (og:image) o twitter:image de la página.

    Devuelve None si no hay meta de imagen, error HTTP, timeout o conexión.
    No lanza excepciones (resiliente para el pipeline).
    """
    if not url or not url.strip().startswith("http"):
        return None
    try:
        headers = {"User-Agent": DEFAULT_UA}
        with httpx.Client(timeout=timeout, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            text = response.text
    except (httpx.HTTPStatusError, httpx.ReadTimeout, httpx.ConnectError) as e:
        logger.debug("OG image fetch failed for %s: %s", url, e)
        return None

    soup = BeautifulSoup(text, "html.parser")
    head = soup.find("head")
    if not head:
        return None

    # og:image tiene prioridad
    for meta in head.find_all("meta", attrs={"property": "og:image"}):
        content = meta.get("content")
        if content and (content := content.strip()):
            if content.startswith("http://") or content.startswith("https://"):
                return content
            # URL relativa: convertir a absoluta respecto a la página
            return urljoin(url, content)

    # Fallback: twitter:image
    for meta in head.find_all("meta", attrs={"name": "twitter:image"}):
        content = meta.get("content")
        if content and (content := content.strip()):
            if content.startswith("http://") or content.startswith("https://"):
                return content
            return urljoin(url, content)

    return None
