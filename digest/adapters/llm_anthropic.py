"""Adaptador LLM con Anthropic (opcional, seleccionado vía LLM_PROVIDER=anthropic)."""

import os

from anthropic import Anthropic

from digest.domain.llm_port import ItemWithSummary


class AnthropicLLM:
    """Implementación del puerto LLM usando la API de Anthropic."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("LLM_API_KEY")
        # Permitimos reutilizar LLM_MODEL; si no se define, usamos un modelo razonable por defecto.
        self._model = model or os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        if not self._api_key:
            raise ValueError("LLM_API_KEY no está definida")

        self._client = Anthropic(api_key=self._api_key)

    def summarize(self, title: str, snippet: str) -> str:
        """Genera un mini resumen en español (2-3 líneas)."""
        prompt = f"""Resume en español en 2 o 3 líneas el siguiente artículo. Solo devuelve el resumen, sin introducción ni título.

Título: {title}

Fragmento o descripción:
{snippet or "(sin descripción)"}"""

        resp = self._client.messages.create(
            model=self._model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        # La API de Anthropic devuelve una lista de bloques de contenido.
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )
        return text.strip()

    def rank(self, items: list[ItemWithSummary], top_n: int = 5) -> list[ItemWithSummary]:
        """Ordena por relevancia para alguien interesado en AI/ML/DS y devuelve top_n."""
        if not items:
            return []
        if len(items) <= top_n:
            return list(items)

        lines = []
        for i, x in enumerate(items):
            lines.append(
                f"[{i}] Título: {x.item.title}\nURL: {x.item.url}\nResumen: {x.summary}\nFuente: {x.item.source}"
            )
        block = "\n\n".join(lines)

        prompt = f"""Eres un experto en IA, aprendizaje automático y ciencia de datos. A continuación hay una lista de artículos con título, URL, resumen y fuente.

Ordena los artículos del más interesante/relevante al menos (para alguien que quiere estar al día en AI/ML/DS). Responde ÚNICAMENTE con una lista de números en el orden elegido, separados por comas, por ejemplo: 2, 0, 4, 1, 3

Artículos:

{block}"""

        resp = self._client.messages.create(
            model=self._model,
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        raw = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()

        order: list[int] = []
        for part in raw.replace(" ", "").split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part)
                if 0 <= idx < len(items) and idx not in order:
                    order.append(idx)

        for i in range(len(items)):
            if i not in order:
                order.append(i)

        return [items[i] for i in order[:top_n]]
