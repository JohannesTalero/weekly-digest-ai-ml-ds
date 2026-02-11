"""Tests de extracción de imagen OG (Open Graph) de artículos.

Nueva funcionalidad: cada artículo del digest debe incluir una imagen thumbnail
extraída de la meta tag og:image de la página del artículo.
"""

from digest.adapters.fetch_og_image import fetch_og_image


# HTML típico con og:image
HTML_WITH_OG_IMAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Test Article">
    <meta property="og:image" content="https://example.com/images/thumbnail.jpg">
    <meta property="og:description" content="A test article">
    <title>Test</title>
</head>
<body><p>Content</p></body>
</html>
"""

# HTML con twitter:image como fallback
HTML_WITH_TWITTER_IMAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="twitter:image" content="https://example.com/images/twitter-card.png">
    <title>Test</title>
</head>
<body><p>Content</p></body>
</html>
"""

# HTML con ambas tags (og:image debe tener prioridad)
HTML_WITH_BOTH = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:image" content="https://example.com/og.jpg">
    <meta name="twitter:image" content="https://example.com/twitter.png">
    <title>Test</title>
</head>
<body><p>Content</p></body>
</html>
"""

# HTML sin ninguna meta de imagen
HTML_WITHOUT_IMAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="No image here">
    <title>Test</title>
</head>
<body><p>Content</p></body>
</html>
"""

# HTML con og:image vacío
HTML_EMPTY_OG_IMAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:image" content="">
    <title>Test</title>
</head>
<body><p>Content</p></body>
</html>
"""

# HTML con og:image relativo (debería ser ignorado o convertido a absoluto)
HTML_RELATIVE_OG_IMAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:image" content="/images/local.jpg">
    <title>Test</title>
</head>
<body><p>Content</p></body>
</html>
"""


class TestFetchOgImage:
    """Extracción de og:image de una URL de artículo."""

    def test_extracts_og_image(self, httpx_mock) -> None:
        """Extrae og:image de HTML con meta tag estándar."""
        httpx_mock.add_response(
            url="https://example.com/article",
            text=HTML_WITH_OG_IMAGE,
        )
        result = fetch_og_image("https://example.com/article")
        assert result == "https://example.com/images/thumbnail.jpg"

    def test_falls_back_to_twitter_image(self, httpx_mock) -> None:
        """Si no hay og:image, usa twitter:image como fallback."""
        httpx_mock.add_response(
            url="https://example.com/article",
            text=HTML_WITH_TWITTER_IMAGE,
        )
        result = fetch_og_image("https://example.com/article")
        assert result == "https://example.com/images/twitter-card.png"

    def test_og_image_takes_priority_over_twitter(self, httpx_mock) -> None:
        """og:image tiene prioridad sobre twitter:image."""
        httpx_mock.add_response(
            url="https://example.com/article",
            text=HTML_WITH_BOTH,
        )
        result = fetch_og_image("https://example.com/article")
        assert result == "https://example.com/og.jpg"

    def test_returns_none_when_no_image_meta(self, httpx_mock) -> None:
        """Devuelve None si no hay meta tags de imagen."""
        httpx_mock.add_response(
            url="https://example.com/article",
            text=HTML_WITHOUT_IMAGE,
        )
        result = fetch_og_image("https://example.com/article")
        assert result is None

    def test_returns_none_on_empty_og_image(self, httpx_mock) -> None:
        """og:image con content vacío devuelve None."""
        httpx_mock.add_response(
            url="https://example.com/article",
            text=HTML_EMPTY_OG_IMAGE,
        )
        result = fetch_og_image("https://example.com/article")
        assert result is None

    def test_returns_none_on_http_error(self, httpx_mock) -> None:
        """Si la URL devuelve error HTTP, devuelve None (no rompe el pipeline)."""
        httpx_mock.add_response(
            url="https://example.com/article",
            status_code=404,
        )
        result = fetch_og_image("https://example.com/article")
        assert result is None

    def test_returns_none_on_timeout(self, httpx_mock) -> None:
        """Si hay timeout, devuelve None (no rompe el pipeline)."""
        import httpx

        httpx_mock.add_exception(
            httpx.ReadTimeout("timeout"),
            url="https://example.com/article",
        )
        result = fetch_og_image("https://example.com/article")
        assert result is None

    def test_returns_none_on_connection_error(self, httpx_mock) -> None:
        """Error de conexión devuelve None."""
        import httpx

        httpx_mock.add_exception(
            httpx.ConnectError("connection refused"),
            url="https://example.com/article",
        )
        result = fetch_og_image("https://example.com/article")
        assert result is None

    def test_relative_og_image_handled(self, httpx_mock) -> None:
        """og:image con URL relativa: se ignora o convierte a absoluta."""
        httpx_mock.add_response(
            url="https://example.com/article",
            text=HTML_RELATIVE_OG_IMAGE,
        )
        result = fetch_og_image("https://example.com/article")
        # Debe ser None (URL relativa no es usable en email) o URL absoluta
        if result is not None:
            assert result.startswith("http"), "Si se devuelve, debe ser URL absoluta"
