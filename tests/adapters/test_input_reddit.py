"""Tests del adaptador Reddit (T3.4) con mocks."""

from digest.adapters.input_reddit import fetch_reddit_items, _fetch_subreddit_rss
from digest.config.sources import RedditConfig


def test_fetch_reddit_items_empty_config():
    cfg = RedditConfig(subreddits=[], limit_per_sub=10)
    assert fetch_reddit_items(cfg) == []
    cfg2 = RedditConfig(subreddits=["ml"], limit_per_sub=0)
    assert fetch_reddit_items(cfg2) == []


def test_fetch_subreddit_rss_parses_external_and_selfposts(httpx_mock):
    """Incluye enlaces externos y self-posts (reddit.com)."""
    httpx_mock.add_response(
        url="https://www.reddit.com/r/MachineLearning/.rss?limit=10",
        text="""
        <?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>External post</title>
              <link>https://arxiv.org/abs/1234</link>
            </item>
            <item>
              <title>Reddit only</title>
              <link>https://www.reddit.com/r/MachineLearning/comments/abc</link>
            </item>
          </channel>
        </rss>
        """,
    )
    items = _fetch_subreddit_rss("MachineLearning", 10, timeout=5.0)
    assert len(items) == 2
    assert items[0].title == "External post"
    assert items[0].url == "https://arxiv.org/abs/1234"
    assert items[0].source == "reddit"
    assert items[1].title == "Reddit only"
    assert "reddit.com" in items[1].url
    assert items[1].source == "reddit"
