"""Caso de uso: pipeline completo hasta top N con resúmenes (fetch → dedup → filter → LLM → top)."""

from pathlib import Path

from digest.config.sources import SourcesConfig
from digest.domain.llm_port import ItemWithSummary, LLMPort
from digest.domain.models import Item

from digest.use_cases.pipeline_core import run_core_pipeline


def build_digest(
    sources_config: SourcesConfig,
    links_path: str | Path,
    history_path: str | Path,
    llm: LLMPort,
    *,
    prefilter_limit: int | None = 30,
    top_n: int = 5,
    fetch_timeout: float = 15.0,
) -> list[ItemWithSummary]:
    """
    Ejecuta el pipeline: candidatos (run_core_pipeline) → resumir cada uno → rankear → top_n.
    Devuelve la lista de ítems con resumen ya ordenada para el email.
    """
    candidates = run_core_pipeline(
        sources_config,
        links_path,
        history_path,
        prefilter_limit=prefilter_limit,
        fetch_timeout=fetch_timeout,
    )
    if not candidates:
        return []
    # Resumir cada candidato
    with_summaries: list[ItemWithSummary] = []
    for item in candidates:
        snippet = (item.description or "")[:1500]
        summary = llm.summarize(item.title, snippet)
        with_summaries.append(ItemWithSummary(item=item, summary=summary))
    # Rankear y quedarnos con top_n
    return llm.rank(with_summaries, top_n=top_n)
