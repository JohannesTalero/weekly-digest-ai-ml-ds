"""Puerto para el servicio LLM: resumen y ranking (RF-09 a RF-12)."""

from dataclasses import dataclass
from typing import Protocol

from digest.domain.models import Item


@dataclass
class ItemWithSummary:
    """Ítem con mini resumen generado por el LLM y opcionalmente URL de imagen OG."""

    item: Item
    summary: str
    image_url: str | None = None


class LLMPort(Protocol):
    """Contrato del servicio LLM: resumir y rankear."""

    def summarize(self, title: str, snippet: str) -> str:
        """Genera un mini resumen en español (2-3 líneas) a partir de título y snippet."""
        ...

    def rank(self, items: list[ItemWithSummary], top_n: int = 5) -> list[ItemWithSummary]:
        """Ordena por relevancia y devuelve los top_n más interesantes para AI/ML/DS."""
        ...
