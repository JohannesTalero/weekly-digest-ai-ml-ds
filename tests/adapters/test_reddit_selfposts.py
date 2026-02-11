"""Tests del adaptador Reddit: inclusión de self-posts (fix de 0 ítems).

El filtro actual descarta TODOS los links a reddit.com, lo que elimina self-posts
(la mayoría del contenido de r/MachineLearning). Estos tests verifican que
self-posts se incluyan como ítems válidos.
"""

from digest.adapters.input_reddit import fetch_reddit_items, _fetch_subreddit_rss
from digest.config.sources import RedditConfig


# RSS típico de un subreddit con mezcla de self-posts y links externos
SAMPLE_REDDIT_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>[D] New paper on transformers</title>
    <link href="https://www.reddit.com/r/MachineLearning/comments/abc123/d_new_paper/"/>
    <updated>2026-02-10T12:00:00Z</updated>
    <content type="html">&lt;a href="https://arxiv.org/abs/2601.12345"&gt;arxiv link&lt;/a&gt;</content>
  </entry>
  <entry>
    <title>GPT-5 released by OpenAI</title>
    <link href="https://openai.com/blog/gpt5"/>
    <updated>2026-02-09T10:00:00Z</updated>
  </entry>
  <entry>
    <title>[R] My research on RL alignment</title>
    <link href="https://www.reddit.com/r/MachineLearning/comments/def456/r_my_research/"/>
    <updated>2026-02-08T08:00:00Z</updated>
  </entry>
  <entry>
    <title>Cool arxiv paper on diffusion</title>
    <link href="https://arxiv.org/abs/2601.99999"/>
    <updated>2026-02-07T06:00:00Z</updated>
  </entry>
</feed>
"""

# RSS donde TODOS son self-posts (escenario real en r/MachineLearning)
ALL_SELFPOSTS_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>[D] Weekly discussion thread</title>
    <link href="https://www.reddit.com/r/MachineLearning/comments/aaa/weekly/"/>
    <updated>2026-02-10T12:00:00Z</updated>
  </entry>
  <entry>
    <title>[P] I built an ML pipeline</title>
    <link href="https://www.reddit.com/r/MachineLearning/comments/bbb/pipeline/"/>
    <updated>2026-02-09T10:00:00Z</updated>
  </entry>
  <entry>
    <title>[D] What LLM are you using in production?</title>
    <link href="https://www.reddit.com/r/MachineLearning/comments/ccc/llm_prod/"/>
    <updated>2026-02-08T08:00:00Z</updated>
  </entry>
</feed>
"""


class TestRedditSelfPosts:
    """Los self-posts de Reddit deben incluirse como ítems válidos."""

    def test_selfposts_not_discarded(self, httpx_mock) -> None:
        """Self-posts (link a reddit.com) NO deben ser descartados completamente."""
        httpx_mock.add_response(
            url="https://www.reddit.com/r/MachineLearning/.rss?limit=10",
            text=SAMPLE_REDDIT_RSS,
        )
        items = _fetch_subreddit_rss("MachineLearning", 10, timeout=5.0)
        # Debe haber más de solo los 2 enlaces externos
        # Los self-posts deben incluirse también
        assert len(items) >= 3, (
            f"Esperaba al menos 3 ítems (2 externos + self-posts), obtuve {len(items)}"
        )

    def test_external_links_still_included(self, httpx_mock) -> None:
        """Los enlaces externos (arxiv, openai, etc.) siguen incluidos."""
        httpx_mock.add_response(
            url="https://www.reddit.com/r/MachineLearning/.rss?limit=10",
            text=SAMPLE_REDDIT_RSS,
        )
        items = _fetch_subreddit_rss("MachineLearning", 10, timeout=5.0)
        external_urls = [it.url for it in items if "reddit.com" not in it.url]
        assert len(external_urls) >= 2, "Los enlaces externos deben seguir presentes"

    def test_all_selfposts_subreddit_returns_items(self, httpx_mock) -> None:
        """Un subreddit donde TODOS los posts son self-posts NO debe devolver 0 ítems."""
        httpx_mock.add_response(
            url="https://www.reddit.com/r/MachineLearning/.rss?limit=10",
            text=ALL_SELFPOSTS_RSS,
        )
        items = _fetch_subreddit_rss("MachineLearning", 10, timeout=5.0)
        assert len(items) > 0, (
            "Un subreddit con solo self-posts NO debe devolver 0 ítems "
            "(bug actual: reddit.com filter elimina todo)"
        )

    def test_selfpost_items_have_source_reddit(self, httpx_mock) -> None:
        """Self-posts incluidos deben tener source='reddit'."""
        httpx_mock.add_response(
            url="https://www.reddit.com/r/MachineLearning/.rss?limit=10",
            text=ALL_SELFPOSTS_RSS,
        )
        items = _fetch_subreddit_rss("MachineLearning", 10, timeout=5.0)
        for item in items:
            assert item.source == "reddit"

    def test_fetch_reddit_items_returns_mixed(self, httpx_mock) -> None:
        """fetch_reddit_items con config real devuelve ítems de self-posts + externos."""
        httpx_mock.add_response(
            url="https://www.reddit.com/r/MachineLearning/.rss?limit=10",
            text=SAMPLE_REDDIT_RSS,
        )
        httpx_mock.add_response(
            url="https://www.reddit.com/r/artificial/.rss?limit=10",
            text=ALL_SELFPOSTS_RSS,
        )
        cfg = RedditConfig(subreddits=["MachineLearning", "artificial"], limit_per_sub=10)
        items = fetch_reddit_items(cfg, timeout=5.0)
        assert len(items) > 2, (
            f"Con 2 subreddits activos, esperaba más de 2 ítems, obtuve {len(items)}"
        )
        # Verificar que hay diversidad (no solo externos)
        sources_urls = [it.url for it in items]
        has_external = any("reddit.com" not in u for u in sources_urls)
        assert has_external, "Debe incluir enlaces externos cuando los hay"
