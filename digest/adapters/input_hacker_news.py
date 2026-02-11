"""Adaptador Hacker News vía Algolia API; queries y límite desde sources.yaml (T3.3)."""

import logging
from urllib.parse import quote_plus

import httpx

from digest.config.sources import HackerNewsConfig
from digest.domain.models import Item

logger = logging.getLogger(__name__)

ALGOLIA_HN_SEARCH = "https://hn.algolia.com/api/v1/search"


def fetch_hacker_news_items(config: HackerNewsConfig, timeout: float = 15.0) -> list[Item]:
    """
    Obtiene ítems de Hacker News usando la API de Algolia.

    Busca por cada query en config.queries, con límite config.limit (por query
    o total según implementación). Devuelve ítems con source="hacker_news".
    Errores de red/API se capturan y se devuelve lista vacía (no detener flujo).
    """
    if not config.queries or config.limit <= 0:
        return []

    seen_urls: set[str] = set()
    items: list[Item] = []
    limit_per_query = max(1, (config.limit + len(config.queries) - 1) // len(config.queries))

    for query in config.queries:
        if len(items) >= config.limit:
            break
        try:
            batch = _search_hn(query, limit_per_query, timeout)
            for it in batch:
                if it.url not in seen_urls and len(items) < config.limit:
                    seen_urls.add(it.url)
                    items.append(it)
        except Exception as e:  # noqa: BLE001
            logger.warning("Hacker News query %r falló: %s", query, e)

    return items[: config.limit]


def _search_hn(query: str, hits_per_page: int, timeout: float) -> list[Item]:
    """Una petición a Algolia HN search; devuelve list[Item]."""
    params = {
        "query": query,
        "tags": "story",
        "hitsPerPage": min(hits_per_page, 100),
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.get(ALGOLIA_HN_SEARCH, params=params)
        response.raise_for_status()
        data = response.json()

    out: list[Item] = []
    for hit in data.get("hits") or []:
        title = (hit.get("title") or "").strip()
        if not title:
            continue
        url = hit.get("url")
        if not url or not str(url).strip().startswith("http"):
            # Ask HN u otros sin URL externa: usar enlace al item en HN
            object_id = hit.get("objectID")
            if object_id:
                url = f"https://news.ycombinator.com/item?id={object_id}"
            else:
                continue
        url = str(url).strip()
        created = hit.get("created_at")
        date_str = created[:10] if isinstance(created, str) and len(created) >= 10 else None
        out.append(
            Item(
                title=title,
                url=url,
                source="hacker_news",
                description=None,
                date=date_str,
            )
        )
    return out
