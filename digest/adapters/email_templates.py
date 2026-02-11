"""Generación del cuerpo del email (HTML y texto) para el digest (RF-15, RNF-08)."""

from datetime import datetime

from digest.domain.llm_port import ItemWithSummary

# Colores para badges de fuente (email HTML inline)
SOURCE_COLORS = {
    "rss": "#059669",
    "hacker_news": "#F97316",
    "reddit": "#EF4444",
    "manual": "#8B5CF6",
}

SOURCE_LABELS = {
    "rss": "RSS",
    "hacker_news": "Hacker News",
    "reddit": "Reddit",
    "manual": "Manual",
}


def _source_color(source: str) -> str:
    """Devuelve el color hex para el tipo de fuente."""
    return SOURCE_COLORS.get(source, "#6b7280")


def _source_label(source: str) -> str:
    """Devuelve la etiqueta legible para el tipo de fuente."""
    return SOURCE_LABELS.get(source, source)


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _digest_date() -> str:
    """Fecha del digest para header (español-friendly)."""
    return datetime.utcnow().strftime("%Y-%m-%d")


def render_digest_html(items: list[ItemWithSummary]) -> str:
    """Genera el cuerpo HTML del email: tabla profesional con header, proceso, artículos rankeados y footer."""
    if not items:
        return "<p>No hay artículos en este digest.</p>"

    date_str = _digest_date()

    # Wrapper y contenedor principal (table-based para clientes de email)
    parts = [
        '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f0f2f5; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Arial, sans-serif;">',
        '<tr><td align="center" style="padding:24px 16px;">',
        '<table width="100%" max-width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px; width:100%; background-color:#ffffff; border-radius:12px; overflow:hidden;">',
        # HEADER
        '<tr><td style="background-color:#4F46E5; color:#ffffff; padding:32px 24px; border-radius:12px 12px 0 0;">',
        '<h1 style="margin:0 0 8px 0; font-size:24px; font-weight:700;">Digest AI/ML/DS</h1>',
        f'<p style="margin:0; font-size:14px; opacity:0.95;">Semana del {date_str}</p>',
        '<p style="margin:12px 0 0 0; font-size:14px; opacity:0.9;">Tu selección semanal de artículos sobre IA, ML y Data Science.</p>',
        "</td></tr>",
        # SECCIÓN PROCESO
        '<tr><td style="background-color:#EEF2FF; padding:24px; border-bottom:1px solid #E5E7EB;">',
        '<p style="margin:0 0 12px 0; font-size:12px; font-weight:600; color:#4F46E5; text-transform:uppercase; letter-spacing:0.5px;">Cómo se construyó este digest</p>',
        '<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>',
        '<td style="padding:8px 12px 8px 0; font-size:13px; color:#374151; vertical-align:top;"><strong>1. Recopilación</strong><br/><span style="color:#6b7280;">RSS, Hacker News, Reddit y enlaces manuales</span></td>',
        '<td style="padding:8px 12px 8px 0; font-size:13px; color:#374151; vertical-align:top;"><strong>2. Resumen IA</strong><br/><span style="color:#6b7280;">Un LLM generó mini-resúmenes en español</span></td>',
        '<td style="padding:8px 0; font-size:13px; color:#374151; vertical-align:top;"><strong>3. Ranking</strong><br/><span style="color:#6b7280;">Selección por relevancia para ti</span></td>',
        "</tr></table>",
        "</td></tr>",
        # ARTÍCULOS
        '<tr><td style="padding:24px;">',
    ]

    for rank, x in enumerate(items, start=1):
        title = _escape_html(x.item.title)
        url = _escape_html(x.item.url)
        summary = _escape_html(x.summary)
        source = x.item.source
        label = _escape_html(_source_label(source))
        color = _source_color(source)

        parts.extend(
            [
                '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">',
                "<tr>",
                f'<td width="48" style="vertical-align:top; padding-right:16px;"><span style="font-size:28px; font-weight:700; color:#4F46E5; line-height:1;">{rank}</span></td>',
                '<td style="vertical-align:top;">',
                f'<a href="{url}" style="color:#1f2937; font-size:16px; font-weight:600; text-decoration:none;">{title}</a>',
                f' &nbsp; <span style="display:inline-block; background-color:{color}; color:#ffffff; font-size:11px; padding:2px 8px; border-radius:12px; margin-bottom:6px;">{label}</span>',
                f'<p style="margin:8px 0 0 0; font-size:14px; line-height:1.5; color:#4b5563;">{summary}</p>',
                f'<p style="margin:6px 0 0 0;"><a href="{url}" style="font-size:13px; color:#4F46E5;">Leer artículo →</a></p>',
                "</td>",
                "</tr>",
                "</table>",
            ]
        )

    parts.extend(
        [
            # FOOTER
            '<tr><td style="background-color:#f9fafb; padding:24px; color:#6b7280; font-size:12px; border-radius:0 0 12px 12px; border-top:1px solid #E5E7EB;">',
            "<p style='margin:0;'>Este digest se genera automáticamente cada semana. Las URLs ya enviadas no se repiten.</p>",
            "</td></tr>",
            "</table>",
            "</td></tr>",
            "</table>",
        ]
    )

    return "\n".join(parts)


def render_digest_text(items: list[ItemWithSummary]) -> str:
    """Genera el cuerpo en texto plano del email con encabezado, proceso y artículos numerados."""
    if not items:
        return "No hay artículos en este digest."

    date_str = _digest_date()
    lines = [
        "DIGEST AI/ML/DS",
        f"Semana del {date_str}",
        "",
        "--- Cómo se construyó este digest ---",
        "1. Recopilación: RSS, Hacker News, Reddit y enlaces manuales",
        "2. Resumen IA: un LLM generó mini-resúmenes en español",
        "3. Ranking: selección por relevancia para ti",
        "",
        "--- Artículos seleccionados ---",
        "",
    ]

    for rank, x in enumerate(items, start=1):
        label = _source_label(x.item.source)
        lines.append(f"{rank}. {x.item.title}")
        lines.append(f"   Fuente: {label}")
        lines.append(f"   {x.item.url}")
        lines.append(f"   {x.summary}")
        lines.append("")

    lines.append("---")
    lines.append("Generado automáticamente. Las URLs ya enviadas no se repiten.")

    return "\n".join(lines).strip()
