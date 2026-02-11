"""Persistencia de cada digest como archivo Markdown (historial legible)."""

from pathlib import Path

from digest.domain.llm_port import ItemWithSummary

SOURCE_LABELS = {
    "rss": "RSS",
    "hacker_news": "Hacker News",
    "reddit": "Reddit",
    "manual": "Manual",
}


def _source_label(source: str) -> str:
    return SOURCE_LABELS.get(source, source)


def save_digest_markdown(items: list[ItemWithSummary], output_dir: str | Path) -> Path:
    """
    Guarda el digest como un archivo Markdown con fecha actual.

    Ubicación: output_dir/YYYY-MM-DD.md
    Incluye por artículo: título, URL, resumen, fuente, ranking y fecha del digest.
    Crea output_dir si no existe.

    Returns:
        Ruta del archivo creado.
    """
    from datetime import datetime

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filepath = out / f"{date_str}.md"

    lines = [
        f"# Digest AI/ML/DS -- {date_str}",
        "",
        f"> Generado automáticamente. {len(items)} artículo(s) seleccionado(s) para esta semana.",
        "",
        "---",
        "",
    ]

    for rank, x in enumerate(items, start=1):
        title = x.item.title.replace("|", "\\|")  # escape pipe en tablas opcionales
        label = _source_label(x.item.source)
        lines.extend(
            [
                f"## {rank}. {title}",
                "",
                f"- **Fuente:** {label}",
                f"- **URL:** {x.item.url}",
                f"- **Ranking:** #{rank}",
                "",
                x.summary.strip(),
                "",
                "---",
                "",
            ]
        )

    filepath.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return filepath
