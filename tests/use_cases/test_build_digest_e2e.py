"""Tests E2E del flujo build_digest con mocks de LLM y fuentes (T8.3)."""

from pathlib import Path

import pytest

from digest.config.sources import SourcesConfig
from digest.domain.llm_port import ItemWithSummary
from digest.domain.models import Item
from digest.use_cases.build_digest import build_digest


def _item(title: str, url: str, source: str = "rss") -> Item:
    return Item(title=title, url=url, source=source)


class MockLLM:
    """LLM que devuelve resúmenes y orden fijos para tests."""

    def summarize(self, title: str, snippet: str) -> str:
        return f"Resumen de: {title}"

    def rank(self, items: list[ItemWithSummary], top_n: int = 5) -> list[ItemWithSummary]:
        return items[:top_n]


class TestBuildDigestE2E:
    def test_empty_candidates_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        def mock_run(*args, **kwargs):
            return []

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_run,
        )
        result = build_digest(sources, links_file, history_file, MockLLM())
        assert result == []

    def test_returns_top_n_with_summaries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)
        candidates = [
            _item("Artículo A", "https://a.com/1"),
            _item("Artículo B", "https://b.com/2"),
            _item("Artículo C", "https://c.com/3"),
        ]

        def mock_run(*args, **kwargs):
            return candidates

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_run,
        )
        result = build_digest(sources, links_file, history_file, MockLLM(), top_n=2)
        assert len(result) == 2
        assert result[0].summary == "Resumen de: Artículo A"
        assert result[1].summary == "Resumen de: Artículo B"
        assert result[0].item.url == "https://a.com/1"
        assert result[1].item.url == "https://b.com/2"

    def test_rank_called_with_all_summaries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)
        candidates = [_item("One", "https://x.com/1")]

        def mock_run(*args, **kwargs):
            return candidates

        rank_calls: list[list[ItemWithSummary]] = []

        class CaptureRankLLM(MockLLM):
            def rank(self, items, top_n=5):
                rank_calls.append(list(items))
                return super().rank(items, top_n)

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_run,
        )
        build_digest(sources, links_file, history_file, CaptureRankLLM())
        assert len(rank_calls) == 1
        assert len(rank_calls[0]) == 1
        assert rank_calls[0][0].summary == "Resumen de: One"
