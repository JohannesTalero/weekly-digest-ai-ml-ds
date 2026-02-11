"""Tests del adaptador Hacker News (T3.3) con mocks."""

import pytest
from digest.adapters.input_hacker_news import fetch_hacker_news_items, _search_hn
from digest.config.sources import HackerNewsConfig
from digest.domain.models import Item


def test_fetch_hacker_news_items_empty_config():
    cfg = HackerNewsConfig(queries=[], limit=10)
    assert fetch_hacker_news_items(cfg) == []
    cfg2 = HackerNewsConfig(queries=["x"], limit=0)
    assert fetch_hacker_news_items(cfg2) == []


def test_search_hn_parses_hits(httpx_mock):
    httpx_mock.add_response(
        url="https://hn.algolia.com/api/v1/search?query=test&tags=story&hitsPerPage=5",
        json={
            "hits": [
                {"title": "Story A", "url": "https://external.com/a", "objectID": "123", "created_at": "2024-01-15T10:00:00Z"},
                {"title": "Ask HN", "objectID": "456"},
            ],
        },
    )
    items = _search_hn("test", 5, timeout=5.0)
    assert len(items) == 2
    assert items[0].title == "Story A"
    assert items[0].url == "https://external.com/a"
    assert items[0].source == "hacker_news"
    assert items[1].title == "Ask HN"
    assert items[1].url == "https://news.ycombinator.com/item?id=456"


def test_fetch_hacker_news_items_respects_limit(httpx_mock):
    # limit=3 con una query → hitsPerPage=3
    httpx_mock.add_response(
        url="https://hn.algolia.com/api/v1/search?query=ml&tags=story&hitsPerPage=3",
        json={
            "hits": [
                {"title": f"Story {i}", "url": f"https://example.com/{i}", "objectID": str(i), "created_at": "2024-01-01T00:00:00Z"}
                for i in range(5)
            ],
        },
    )
    cfg = HackerNewsConfig(queries=["ml"], limit=3)
    items = fetch_hacker_news_items(cfg, timeout=5.0)
    assert len(items) == 3
