"""Tests de User-Agent en adaptadores HTTP (RSS, HN, Reddit).

Muchos sitios (Medium/TDS, Reddit) bloquean requests sin User-Agent adecuado.
Estos tests verifican que TODOS los adaptadores HTTP envían un User-Agent personalizado.
"""

from digest.adapters.input_rss import _fetch_one_feed
from digest.adapters.input_hacker_news import _search_hn
from digest.adapters.input_reddit import _fetch_subreddit_rss


SIMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Test</title>
      <link>https://example.com/1</link>
    </item>
  </channel>
</rss>
"""

SIMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Test</title>
    <link href="https://example.com/1"/>
  </entry>
</feed>
"""

HN_RESPONSE = {
    "hits": [
        {
            "title": "Test",
            "url": "https://example.com/1",
            "objectID": "1",
            "created_at": "2026-01-01T00:00:00Z",
        }
    ]
}


class TestRssUserAgent:
    """El adaptador RSS debe enviar User-Agent personalizado."""

    def test_rss_sends_user_agent(self, httpx_mock) -> None:
        """Verificar que la petición RSS incluye User-Agent != httpx default."""
        httpx_mock.add_response(
            url="https://example.com/feed.xml",
            text=SIMPLE_RSS,
        )
        _fetch_one_feed("https://example.com/feed.xml", timeout=5.0)

        request = httpx_mock.get_request()
        assert request is not None
        ua = request.headers.get("user-agent", "")
        # No debe ser el user-agent por defecto de httpx (que es "python-httpx/X.Y.Z")
        assert "python-httpx" not in ua.lower(), (
            f"User-Agent debe ser personalizado, no el default de httpx: {ua}"
        )
        assert len(ua) > 0, "User-Agent no debe estar vacío"


class TestHackerNewsUserAgent:
    """El adaptador HN debe enviar User-Agent personalizado."""

    def test_hn_sends_user_agent(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://hn.algolia.com/api/v1/search?query=test&tags=story&hitsPerPage=5",
            json=HN_RESPONSE,
        )
        _search_hn("test", 5, timeout=5.0)

        request = httpx_mock.get_request()
        assert request is not None
        ua = request.headers.get("user-agent", "")
        assert "python-httpx" not in ua.lower(), f"User-Agent debe ser personalizado: {ua}"


class TestRedditUserAgent:
    """El adaptador Reddit debe enviar User-Agent personalizado (Reddit requiere UA)."""

    def test_reddit_sends_user_agent(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://www.reddit.com/r/test/.rss?limit=5",
            text=SIMPLE_ATOM,
        )
        _fetch_subreddit_rss("test", 5, timeout=5.0)

        request = httpx_mock.get_request()
        assert request is not None
        ua = request.headers.get("user-agent", "")
        assert "python-httpx" not in ua.lower(), (
            f"User-Agent debe ser personalizado para Reddit: {ua}"
        )
        assert len(ua) > 0, "User-Agent no debe estar vacío"
