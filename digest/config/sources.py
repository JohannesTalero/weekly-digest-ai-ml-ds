"""Lectura de config/sources.yaml: RSS, Hacker News y Reddit (RF-04, RF-06, RF-07, RF-08)."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class RssSource:
    """Una fuente RSS/Atom: nombre y URL del feed."""

    name: str
    url: str


@dataclass
class HackerNewsConfig:
    """Parámetros de Hacker News: queries y límite de ítems."""

    queries: list[str]
    limit: int


@dataclass
class RedditConfig:
    """Parámetros de Reddit: subreddits y límite por subreddit."""

    subreddits: list[str]
    limit_per_sub: int


@dataclass
class SourcesConfig:
    """Configuración de fuentes en memoria (parseada desde sources.yaml)."""

    rss: list[RssSource]
    hacker_news: HackerNewsConfig | None
    reddit: RedditConfig | None


def load_sources(path: str | Path) -> SourcesConfig:
    """
    Lee config/sources.yaml y devuelve estructuras en memoria.

    Si una sección (rss, hacker_news, reddit) falta o está vacía, se usa lista vacía
    o None según corresponda. No lanza si el archivo tiene solo comentarios o secciones opcionales.
    """
    p = Path(path)
    if not p.exists():
        return SourcesConfig(rss=[], hacker_news=None, reddit=None)

    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not raw:
        return SourcesConfig(rss=[], hacker_news=None, reddit=None)

    rss_list: list[RssSource] = []
    for entry in raw.get("rss") or []:
        if isinstance(entry, dict) and entry.get("url"):
            rss_list.append(
                RssSource(
                    name=entry.get("name") or "",
                    url=entry["url"].strip(),
                )
            )

    hn = raw.get("hacker_news")
    if hn and isinstance(hn, dict) and (hn.get("queries") or hn.get("limit") is not None):
        hacker_news = HackerNewsConfig(
            queries=[q for q in (hn.get("queries") or []) if isinstance(q, str)],
            limit=hn.get("limit") if isinstance(hn.get("limit"), int) else 15,
        )
    else:
        hacker_news = None

    rd = raw.get("reddit")
    if (
        rd
        and isinstance(rd, dict)
        and (rd.get("subreddits") or rd.get("limit_per_sub") is not None)
    ):
        reddit = RedditConfig(
            subreddits=[s for s in (rd.get("subreddits") or []) if isinstance(s, str)],
            limit_per_sub=rd.get("limit_per_sub")
            if isinstance(rd.get("limit_per_sub"), int)
            else 10,
        )
    else:
        reddit = None

    return SourcesConfig(rss=rss_list, hacker_news=hacker_news, reddit=reddit)
