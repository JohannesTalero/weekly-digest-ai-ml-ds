"""Modelos de dominio del digest: ítem/candidato y tipos de fuente."""

from dataclasses import dataclass
from typing import Literal

# Tipo de fuente para cada ítem (alineado con arquitectura y tareas T2.1)
SourceType = Literal["rss", "manual", "hacker_news", "reddit"]


@dataclass(frozen=True)
class Item:
    """Un candidato a incluir en el digest: título, URL, fuente y metadatos opcionales."""

    title: str
    url: str
    source: SourceType
    description: str | None = None
    date: str | None = None

    def __post_init__(self) -> None:
        if not self.url or not self.url.strip():
            raise ValueError("Item.url no puede estar vacío")
        if self.source not in ("rss", "manual", "hacker_news", "reddit"):
            raise ValueError(
                f"Item.source debe ser rss|manual|hacker_news|reddit, recibido: {self.source!r}"
            )
