"""Núcleo del pipeline: dedup, filtro ya enviados, frescura, prefiltro y orquestación (Fase 4)."""

from datetime import datetime, timedelta
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


def filter_stale(
    items: list[Item],
    max_age_days: int = 90,
) -> list[Item]:
    """
    Descarta ítems cuya fecha es anterior a max_age_days.
    Ítems sin fecha (date=None) se mantienen.
    Si todos son viejos, devuelve la lista original (fallback).
    """
    if not items:
        return items
    cutoff = (datetime.utcnow() - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
    fresh = [i for i in items if not i.date or i.date >= cutoff]
    return fresh if fresh else items


def prefilter_candidates(
    items: list[Item],
    limit: int | None = 30,
) -> list[Item]:
    """
    Si hay más de `limit` candidatos, selecciona round-robin por fuente
    para que todas las fuentes estén representadas (evita que RSS acapare todo).
    Si limit es None, no recorta. Usado para acotar coste/tiempo de LLM (RNF-02).
    """
    if limit is None or len(items) <= limit:
        return items
    by_source: dict[str, list[Item]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)
    result: list[Item] = []
    source_iters = {s: iter(lst) for s, lst in by_source.items()}
    while len(result) < limit and source_iters:
        exhausted = []
        for source, it in list(source_iters.items()):
            if len(result) >= limit:
                break
            try:
                result.append(next(it))
            except StopIteration:
                exhausted.append(source)
        for s in exhausted:
            del source_iters[s]
    return result


def run_core_pipeline(
    sources_config: SourcesConfig,
    links_path: str | Path,
    history_path: str | Path,
    *,
    prefilter_limit: int | None = 30,
    fetch_timeout: float = 15.0,
    max_age_days: int = 90,
) -> list[Item]:
    """
    Orquesta: carga historial → fetch todas las fuentes → unión → dedup
    → filtro ya enviados → filtro frescura → prefiltro balanceado.
    Devuelve lista de candidatos lista para LLM. No llama a LLM ni email.
    """
    sent_urls = load_sent_urls(history_path)
    combined = fetch_all_items(sources_config, links_path, timeout=fetch_timeout)
    deduped = dedup_by_url(combined)
    filtered = filter_already_sent(deduped, sent_urls)
    fresh = filter_stale(filtered, max_age_days=max_age_days)
    return prefilter_candidates(fresh, limit=prefilter_limit)
