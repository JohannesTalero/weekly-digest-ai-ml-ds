"""Núcleo del pipeline: dedup, filtro ya enviados, prefiltro y orquestación (Fase 4)."""

from pathlib import Path

from digest.config.history import load_sent_urls
from digest.config.sources import SourcesConfig
from digest.domain.models import Item
from digest.domain.urls import normalize_url

from digest.adapters.fetch_all import fetch_all_items


def dedup_by_url(items: list[Item]) -> list[Item]:
    """
    Deduplica por URL normalizada: se queda con un ítem por URL (el primero visto).
    """
    seen: set[str] = set()
    result: list[Item] = []
    for item in items:
        key = normalize_url(item.url)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def filter_already_sent(items: list[Item], sent_urls: set[str]) -> list[Item]:
    """
    Descarta ítems cuya URL normalizada está en el historial de ya enviados.
    """
    sent_normalized = {normalize_url(u) for u in sent_urls}
    return [i for i in items if normalize_url(i.url) not in sent_normalized]


def prefilter_candidates(
    items: list[Item],
    limit: int | None = 30,
) -> list[Item]:
    """
    Si hay más de `limit` candidatos, recorta la lista (p. ej. primeros N).
    Si limit es None, no recorta. Usado para acotar coste/tiempo de LLM (RNF-02).
    """
    if limit is None or len(items) <= limit:
        return items
    return items[:limit]


def run_core_pipeline(
    sources_config: SourcesConfig,
    links_path: str | Path,
    history_path: str | Path,
    *,
    prefilter_limit: int | None = 30,
    fetch_timeout: float = 15.0,
) -> list[Item]:
    """
    Orquesta: carga historial → fetch todas las fuentes → unión → dedup
    → filtro ya enviados → prefiltro. Devuelve lista de candidatos lista para LLM.
    No llama a LLM ni email.
    """
    sent_urls = load_sent_urls(history_path)
    combined = fetch_all_items(sources_config, links_path, timeout=fetch_timeout)
    deduped = dedup_by_url(combined)
    filtered = filter_already_sent(deduped, sent_urls)
    return prefilter_candidates(filtered, limit=prefilter_limit)
