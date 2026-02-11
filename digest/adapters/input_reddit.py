"""Adaptador Reddit: RSS de subreddits; subreddits y límite desde config (T3.4)."""

import logging
from urllib.parse import quote_plus

import feedparser
import httpx

from digest.config.sources import RedditConfig
from digest.domain.models import Item

logger = logging.getLogger(__name__)

REDDIT_RSS_BASE = "https://www.reddit.com/r/{subreddit}/.rss"
DEFAULT_UA = "DigestBot/1.0 (weekly AI/ML digest)"


def fetch_reddit_items(config: RedditConfig, timeout: float = 15.0) -> list[Item]:
    """
    Obtiene ítems de Reddit vía RSS de cada subreddit.

    Por cada subreddit hace GET a .rss con límite; filtra posts con enlace
    externo (no reddit.com). source="reddit". Errores por subreddit no
    detienen el flujo (RNF-06).
    """
    if not config.subreddits or config.limit_per_sub <= 0:
        return []

    items: list[Item] = []
    for sub in config.subreddits:
        sub = (sub or "").strip()
        if not sub or sub.startswith("/"):
            continue
        try:
            batch = _fetch_subreddit_rss(sub, config.limit_per_sub, timeout)
            items.extend(batch)
        except Exception as e:  # noqa: BLE001
            logger.warning("Reddit r/%s falló: %s", sub, e)

    return items


def _fetch_subreddit_rss(subreddit: str, limit: int, timeout: float) -> list[Item]:
    """Obtiene posts del subreddit vía RSS: enlaces externos y self-posts (reddit.com)."""
    url = REDDIT_RSS_BASE.format(subreddit=quote_plus(subreddit))
    headers = {"User-Agent": DEFAULT_UA}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.get(url, params={"limit": min(limit, 25)})
        response.raise_for_status()
        text = response.text

    parsed = feedparser.parse(text)
    out: list[Item] = []

    for entry in parsed.entries:
        link = _get_entry_link(entry)
        if not link:
            continue
        # Incluir tanto enlaces externos como self-posts (link a reddit.com)
        title = (entry.get("title") or "").strip() or "(sin título)"
        date_str = _get_entry_date(entry)
        out.append(
            Item(
                title=title,
                url=link,
                source="reddit",
                description=None,
                date=date_str,
            )
        )
        if len(out) >= limit:
            break

    return out


def _get_entry_link(entry) -> str | None:
    """Extrae la URL del enlace externo si existe; si no, link del post."""
    link = getattr(entry, "link", None)
    if link and isinstance(link, str) and link.strip().startswith("http"):
        return link.strip()
    links = getattr(entry, "links", None)
    if links:
        for ln in links:
            href = getattr(ln, "href", None)
            if href:
                h = str(href).strip()
                if h.startswith("http"):
                    return h
    return None


def _get_entry_date(entry) -> str | None:
    """Extrae fecha publicada si existe."""
    val = getattr(entry, "published_parsed", None)
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
