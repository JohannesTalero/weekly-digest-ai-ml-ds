"""Adaptador RSS/Atom: GET a URLs de sources.yaml, parsear feed, devolver list[Item] (T3.1)."""

import logging
import feedparser
import httpx

from digest.config.sources import RssSource
from digest.domain.models import Item

logger = logging.getLogger(__name__)


def fetch_rss_items(sources: list[RssSource], timeout: float = 15.0) -> list[Item]:
    """
    Obtiene ítems de cada fuente RSS/Atom configurada.

    Por cada feed: GET a la URL, parseo con feedparser; si un feed falla
    se registra el error y se sigue con el resto (RNF-06).
    Devuelve ítems con source="rss"; título, URL y descripción/fecha si existen.
    """
    items: list[Item] = []
    for src in sources:
        try:
            feed_items = _fetch_one_feed(src.url, timeout)
            for entry in feed_items:
                items.append(entry)
        except Exception as e:  # noqa: BLE001
            logger.warning("RSS feed falló %s: %s", src.url, e)
    return items


def _fetch_one_feed(url: str, timeout: float) -> list[Item]:
    """Hace GET a una URL de feed, parsea y devuelve lista de Item."""
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        text = response.text

    parsed = feedparser.parse(text)
    out: list[Item] = []

    for entry in parsed.entries:
        link = _get_entry_link(entry)
        if not link:
            continue
        title = (entry.get("title") or "").strip() or "(sin título)"
        description = _get_entry_description(entry)
        date_str = _get_entry_date(entry)
        out.append(
            Item(
                title=title,
                url=link,
                source="rss",
                description=description or None,
                date=date_str or None,
            )
        )
    return out


def _get_entry_link(entry) -> str | None:
    """Extrae la URL canónica del entry (link o enlaces)."""
    link = getattr(entry, "link", None)
    if link and isinstance(link, str) and link.strip().startswith("http"):
        return link.strip()
    links = getattr(entry, "links", None)
    if links:
        for ln in links:
            href = getattr(ln, "href", None)
            if href and str(href).strip().startswith("http"):
                return str(href).strip()
    return None


def _get_entry_description(entry) -> str | None:
    """Extrae descripción/snippet del entry."""
    for attr in ("summary", "description", "content"):
        val = getattr(entry, attr, None)
        if val:
            if hasattr(val, "value"):
                return (val.value or "").strip() or None
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def _get_entry_date(entry) -> str | None:
    """Extrae fecha publicada si existe (ISO o legible)."""
    for attr in ("published", "updated", "created"):
        val = getattr(entry, f"{attr}_parsed", None)
        if val:
            try:
                import time

                return time.strftime("%Y-%m-%d", val)
            except Exception:
                pass
    published = getattr(entry, "published", None)
    if published and isinstance(published, str):
        return published.strip()
    return None
