"""Orquestador de adaptadores de entrada: llama a todos y une resultados (T3.5)."""

import logging
from pathlib import Path

from digest.config.sources import SourcesConfig
from digest.domain.models import Item

from .input_hacker_news import fetch_hacker_news_items
from .input_manual import fetch_manual_items
from .input_reddit import fetch_reddit_items
from .input_rss import fetch_rss_items

logger = logging.getLogger(__name__)


def fetch_all_items(
    sources_config: SourcesConfig,
    links_path: str | Path,
    *,
    timeout: float = 15.0,
) -> list[Item]:
    """
    Ejecuta todos los adaptadores de entrada y une sus resultados en una sola lista.

    Cada fuente se ejecuta en try/except: si una falla se registra el error y
    se sigue con el resto (resiliencia por fuente, RNF-06). No se lanza excepción
    por fallos individuales.
    """
    combined: list[Item] = []

    # RSS
    if sources_config.rss:
        try:
            items = fetch_rss_items(sources_config.rss, timeout=timeout)
            combined.extend(items)
            logger.info("RSS: %d ítems", len(items))
        except Exception as e:  # noqa: BLE001
            logger.warning("Adaptador RSS falló: %s", e)

    # Manual (links.md)
    try:
        items = fetch_manual_items(links_path)
        combined.extend(items)
        if items:
            logger.info("Manual: %d ítems", len(items))
    except Exception as e:  # noqa: BLE001
        logger.warning("Adaptador manual (links) falló: %s", e)

    # Hacker News
    if sources_config.hacker_news:
        try:
            items = fetch_hacker_news_items(sources_config.hacker_news, timeout=timeout)
            combined.extend(items)
            logger.info("Hacker News: %d ítems", len(items))
        except Exception as e:  # noqa: BLE001
            logger.warning("Adaptador Hacker News falló: %s", e)

    # Reddit
    if sources_config.reddit:
        try:
            items = fetch_reddit_items(sources_config.reddit, timeout=timeout)
            combined.extend(items)
            logger.info("Reddit: %d ítems", len(items))
        except Exception as e:  # noqa: BLE001
            logger.warning("Adaptador Reddit falló: %s", e)

    return combined
