"""Tests de load_sources (config/sources.yaml)."""

from pathlib import Path

import pytest

from digest.config.sources import (
    HackerNewsConfig,
    RedditConfig,
    RssSource,
    SourcesConfig,
    load_sources,
)


class TestLoadSources:
    def test_missing_file_returns_empty_config(self, tmp_path: Path) -> None:
        cfg = load_sources(tmp_path / "nonexistent.yaml")
        assert cfg.rss == [] and cfg.hacker_news is None and cfg.reddit is None

    def test_empty_file_returns_empty_config(self, tmp_path: Path) -> None:
        (tmp_path / "s.yaml").write_text("")
        cfg = load_sources(tmp_path / "s.yaml")
        assert cfg.rss == [] and cfg.hacker_news is None and cfg.reddit is None

    def test_parses_rss_list(self, tmp_path: Path) -> None:
        (tmp_path / "s.yaml").write_text("""
rss:
  - name: "Feed One"
    url: "https://one.com/feed"
  - name: "Feed Two"
    url: "https://two.com/rss"
""")
        cfg = load_sources(tmp_path / "s.yaml")
        assert len(cfg.rss) == 2
        assert cfg.rss[0] == RssSource(name="Feed One", url="https://one.com/feed")
        assert cfg.rss[1] == RssSource(name="Feed Two", url="https://two.com/rss")

    def test_parses_hacker_news(self, tmp_path: Path) -> None:
        (tmp_path / "s.yaml").write_text("""
hacker_news:
  queries:
    - "machine learning"
    - "LLM"
  limit: 20
""")
        cfg = load_sources(tmp_path / "s.yaml")
        assert cfg.hacker_news == HackerNewsConfig(queries=["machine learning", "LLM"], limit=20)

    def test_parses_reddit(self, tmp_path: Path) -> None:
        (tmp_path / "s.yaml").write_text("""
reddit:
  subreddits:
    - "MachineLearning"
    - "artificial"
  limit_per_sub: 5
""")
        cfg = load_sources(tmp_path / "s.yaml")
        assert cfg.reddit == RedditConfig(subreddits=["MachineLearning", "artificial"], limit_per_sub=5)

    def test_full_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "s.yaml").write_text("""
rss:
  - name: "R"
    url: "https://r.com/feed"
hacker_news:
  queries: ["ai"]
  limit: 10
reddit:
  subreddits: ["ML"]
  limit_per_sub: 3
""")
        cfg = load_sources(tmp_path / "s.yaml")
        assert len(cfg.rss) == 1 and cfg.rss[0].url == "https://r.com/feed"
        assert cfg.hacker_news and cfg.hacker_news.queries == ["ai"] and cfg.hacker_news.limit == 10
        assert cfg.reddit and cfg.reddit.subreddits == ["ML"] and cfg.reddit.limit_per_sub == 3
