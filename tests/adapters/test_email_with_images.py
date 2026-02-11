"""Tests del template de email con imágenes OG.

Verifica que el email HTML incluye thumbnails de los artículos cuando
image_url está disponible en los ItemWithSummary.
"""

from digest.adapters.email_templates import render_digest_html, render_digest_text
from digest.domain.llm_port import ItemWithSummary
from digest.domain.models import Item


def _item_with_summary(
    title: str,
    url: str,
    source: str = "rss",
    summary: str = "Un resumen de prueba.",
    image_url: str | None = None,
) -> ItemWithSummary:
    item = Item(title=title, url=url, source=source)
    return ItemWithSummary(item=item, summary=summary, image_url=image_url)


class TestEmailHtmlWithImages:
    """El HTML del email debe incluir thumbnails cuando image_url existe."""

    def test_renders_image_when_available(self) -> None:
        """Si image_url está presente, el HTML debe incluir un <img> con esa URL."""
        items = [
            _item_with_summary(
                "Article with image",
                "https://example.com/article",
                image_url="https://example.com/thumbnail.jpg",
            ),
        ]
        html = render_digest_html(items)
        assert "https://example.com/thumbnail.jpg" in html, (
            "La URL de la imagen debe aparecer en el HTML"
        )
        assert "<img" in html, "Debe haber una tag <img> para la imagen"

    def test_no_image_tag_when_no_image(self) -> None:
        """Si image_url es None, no debe haber <img> roto."""
        items = [
            _item_with_summary(
                "Article without image",
                "https://example.com/article",
                image_url=None,
            ),
        ]
        html = render_digest_html(items)
        # No debe haber img tags para este artículo
        assert 'src=""' not in html, "No debe haber img con src vacío"

    def test_mixed_items_some_with_images(self) -> None:
        """Con mezcla de ítems con y sin imagen, solo los que tienen muestran thumbnail."""
        items = [
            _item_with_summary(
                "Con imagen",
                "https://a.com/1",
                image_url="https://a.com/img.jpg",
            ),
            _item_with_summary(
                "Sin imagen",
                "https://b.com/2",
                image_url=None,
            ),
        ]
        html = render_digest_html(items)
        assert "https://a.com/img.jpg" in html
        assert html.count("<img") == 1, "Solo 1 imagen para 1 artículo con image_url"

    def test_image_is_clickable_link(self) -> None:
        """La imagen debe estar dentro de un enlace al artículo."""
        items = [
            _item_with_summary(
                "Clickable",
                "https://example.com/post",
                image_url="https://example.com/og.jpg",
            ),
        ]
        html = render_digest_html(items)
        # Verificar que la imagen está dentro de un <a href="...">
        img_pos = html.find("<img")
        assert img_pos > 0
        # Buscar el <a> más cercano antes del <img>
        preceding = html[:img_pos]
        last_a = preceding.rfind("<a ")
        assert last_a >= 0, "La imagen debe estar precedida por un <a>"
        a_snippet = html[last_a:img_pos]
        assert "https://example.com/post" in a_snippet, (
            "El link envolvente debe apuntar al artículo"
        )


class TestEmailTextWithImages:
    """El texto plano debe incluir la URL de la imagen cuando está disponible."""

    def test_includes_image_url_in_text(self) -> None:
        """El texto plano debe mencionar la URL de la imagen."""
        items = [
            _item_with_summary(
                "Article",
                "https://example.com/1",
                image_url="https://example.com/img.jpg",
            ),
        ]
        text = render_digest_text(items)
        assert "https://example.com/img.jpg" in text or "Imagen:" in text, (
            "El texto plano debe incluir referencia a la imagen"
        )

    def test_no_image_line_when_no_image(self) -> None:
        """Sin image_url, no debe haber línea de imagen vacía."""
        items = [
            _item_with_summary(
                "Article",
                "https://example.com/1",
                image_url=None,
            ),
        ]
        text = render_digest_text(items)
        assert "Imagen:" not in text or "Imagen: None" not in text
