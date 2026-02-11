"""Lectura y escritura del historial data/sent-urls.* (RF-03b, RNF-06b)."""

import json
from datetime import datetime
from pathlib import Path


def load_sent_urls(path: str | Path) -> set[str]:
    """
    Carga el set de URLs ya enviadas desde data/sent-urls.json (o .txt).

    Si el archivo no existe, devuelve set vacío. Formato JSON: {"urls": [...], "updated": "..."}.
    Si el path es .txt, se espera una URL por línea.
    """
    p = Path(path)
    if not p.exists():
        return set()

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return set()

    suffix = p.suffix.lower()
    if suffix == ".json":
        try:
            data = json.loads(text)
            urls = data.get("urls")
            if isinstance(urls, list):
                return {u for u in urls if isinstance(u, str) and u.strip()}
            return set()
        except (json.JSONDecodeError, TypeError):
            return set()
    if suffix == ".txt":
        return {line.strip() for line in text.splitlines() if line.strip() and _looks_like_url(line.strip())}
    return set()


def save_sent_urls(path: str | Path, urls: set[str] | list[str]) -> None:
    """
    Escribe el historial de URLs enviadas en data/sent-urls.json.

    Formato: {"urls": [...], "updated": "YYYY-MM-DD"}.
    Crea el directorio padre si no existe.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    url_list = sorted(set(urls)) if urls else []
    payload = {
        "urls": url_list,
        "updated": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _looks_like_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")
