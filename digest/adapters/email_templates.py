"""Generación del cuerpo del email (HTML y texto) para el digest (RF-15, RNF-08)."""

from digest.domain.llm_port import ItemWithSummary


def render_digest_html(items: list[ItemWithSummary]) -> str:
    """Genera el cuerpo HTML del email: lista de ítems con título, URL, resumen y fuente."""
    if not items:
        return "<p>No hay artículos en este digest.</p>"
    lines = ["<ul>"]
    for x in items:
        title = _escape_html(x.item.title)
        url = _escape_html(x.item.url)
        summary = _escape_html(x.summary)
        source = _escape_html(x.item.source)
        lines.append(
            f'<li><strong><a href="{url}">{title}</a></strong> '
            f"<small>({source})</small><br>{summary}</li>"
        )
    lines.append("</ul>")
    return "\n".join(lines)


def render_digest_text(items: list[ItemWithSummary]) -> str:
    """Genera el cuerpo en texto plano del email."""
    if not items:
        return "No hay artículos en este digest."
    lines = []
    for x in items:
        lines.append(f"- {x.item.title}")
        lines.append(f"  {x.item.url}")
        lines.append(f"  {x.summary}")
        lines.append(f"  Fuente: {x.item.source}")
        lines.append("")
    return "\n".join(lines).strip()


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
