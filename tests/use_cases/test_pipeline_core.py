"""Tests del núcleo del pipeline: dedup, filtro ya enviados, prefiltro (T8.2)."""

from pathlib import Path

import pytest

from digest.config.sources import SourcesConfig
from digest.domain.models import Item
from digest.use_cases.pipeline_core import (
    dedup_by_url,
    filter_already_sent,
    prefilter_candidates,
    run_core_pipeline,
)


def _item(title: str, url: str, source: str = "rss") -> Item:
    return Item(title=title, url=url, source=source)


class TestDedupByUrl:
    def test_empty_returns_empty(self) -> None:
        assert dedup_by_url([]) == []

    def test_one_item_unchanged(self) -> None:
        items = [_item("A", "https://a.com/1")]
        assert dedup_by_url(items) == items

    def test_duplicate_url_keeps_first(self) -> None:
        a = _item("First", "https://x.com/page")
        b = _item("Second", "https://x.com/page")
        result = dedup_by_url([a, b])
        assert result == [a]

    def test_same_url_different_query_deduped(self) -> None:
        a = _item("A", "https://site.com/article?utm=1")
        b = _item("B", "https://site.com/article?ref=2")
        result = dedup_by_url([a, b])
        assert len(result) == 1
        assert result[0].title == "A"

    def test_different_urls_all_kept(self) -> None:
        items = [
            _item("A", "https://a.com/1"),
            _item("B", "https://b.com/2"),
        ]
        assert dedup_by_url(items) == items


class TestFilterAlreadySent:
    def test_empty_items_returns_empty(self) -> None:
        assert filter_already_sent([], {"https://any.com"}) == []

    def test_empty_history_keeps_all(self) -> None:
        items = [_item("A", "https://a.com/1"), _item("B", "https://b.com/2")]
        assert filter_already_sent(items, set()) == items

    def test_removes_item_in_history(self) -> None:
        items = [
            _item("A", "https://site.com/a"),
            _item("B", "https://site.com/b"),
        ]
        sent = {"https://site.com/a"}
        result = filter_already_sent(items, sent)
        assert len(result) == 1 and result[0].url == "https://site.com/b"

    def test_normalized_match(self) -> None:
        items = [_item("X", "https://site.com/page?ref=1#top")]
        sent = {"https://site.com/page"}
        assert filter_already_sent(items, sent) == []


class TestPrefilterCandidates:
    def test_empty_returns_empty(self) -> None:
        assert prefilter_candidates([]) == []
        assert prefilter_candidates([], limit=10) == []

    def test_under_limit_unchanged(self) -> None:
        items = [_item("A", "https://a.com/1"), _item("B", "https://b.com/2")]
        assert prefilter_candidates(items, limit=30) == items

    def test_over_limit_truncates(self) -> None:
        items = [_item("A", f"https://x.com/{i}") for i in range(35)]
        result = prefilter_candidates(items, limit=30)
        assert len(result) == 30
        assert result[0].url == "https://x.com/0"

    def test_none_limit_keeps_all(self) -> None:
        items = [_item("A", f"https://x.com/{i}") for i in range(50)]
        assert prefilter_candidates(items, limit=None) == items


class TestRunCorePipeline:
    def test_returns_filtered_candidates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        history_file = tmp_path / "sent.json"
        history_file.write_text('{"urls": [], "updated": "2025-01-01"}')
        links_file = tmp_path / "links.md"
        links_file.write_text("")

        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        def mock_fetch(*args, **kwargs):
            return [
                _item("New", "https://new.com/1"),
                _item("Old", "https://old.com/2"),
            ]

        monkeypatch.setattr(
            "digest.use_cases.pipeline_core.fetch_all_items",
            mock_fetch,
        )
        result = run_core_pipeline(sources, links_file, history_file)
        assert len(result) == 2
        urls = {i.url for i in result}
        assert "https://new.com/1" in urls and "https://old.com/2" in urls

    def test_filters_already_sent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        history_file = tmp_path / "sent.json"
        history_file.write_text('{"urls": ["https://already.com/sent"], "updated": "2025-01-01"}')
        links_file = tmp_path / "links.md"
        links_file.write_text("")

        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        def mock_fetch(*args, **kwargs):
            return [
                _item("Already sent", "https://already.com/sent"),
                _item("New", "https://new.com/1"),
            ]

        monkeypatch.setattr(
            "digest.use_cases.pipeline_core.fetch_all_items",
            mock_fetch,
        )
        result = run_core_pipeline(sources, links_file, history_file)
        assert len(result) == 1
        assert result[0].url == "https://new.com/1"
