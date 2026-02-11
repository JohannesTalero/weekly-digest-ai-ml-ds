"""Tests del adaptador RSS (T3.1) con mocks."""

from digest.adapters.input_rss import _fetch_one_feed, fetch_rss_items
from digest.config.sources import RssSource


def test_fetch_rss_items_empty_sources():
    assert fetch_rss_items([]) == []


def test_fetch_one_feed_parses_entries(httpx_mock):
    httpx_mock.add_response(
        url="https://example.com/feed.xml",
        text="""
        <?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <title>Test</title>
            <item>
              <title>Post One</title>
              <link>https://example.com/post-one</link>
              <description>Summary</description>
            </item>
            <item>
              <title>Post Two</title>
              <link>https://example.com/post-two</link>
            </item>
          </channel>
        </rss>
        """,
    )
    items = _fetch_one_feed("https://example.com/feed.xml", timeout=5.0)
    assert len(items) == 2
    assert items[0].title == "Post One"
    assert items[0].url == "https://example.com/post-one"
    assert items[0].source == "rss"
    assert items[1].title == "Post Two"
    assert items[1].url == "https://example.com/post-two"


def test_fetch_rss_items_continues_after_one_feed_fails(httpx_mock):
    httpx_mock.add_response(
        url="https://good.com/feed.xml",
        text="<rss><channel><item><title>A</title><link>https://a.com/1</link></item></channel></rss>",
    )
    httpx_mock.add_response(url="https://bad.com/feed.xml", status_code=500)
    sources = [
        RssSource(name="Good", url="https://good.com/feed.xml"),
        RssSource(name="Bad", url="https://bad.com/feed.xml"),
    ]
    items = fetch_rss_items(sources, timeout=5.0)
    assert len(items) == 1
    assert items[0].url == "https://a.com/1"
