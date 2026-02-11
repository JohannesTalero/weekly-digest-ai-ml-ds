"""Tests E2E de diversidad de fuentes en el digest final.

Verifica que el pipeline completo (fetch → dedup → filter → prefilter → LLM → email)
produce un digest con artículos de MÚLTIPLES fuentes, no solo de una.
"""

import pytest
from pathlib import Path

from digest.config.sources import SourcesConfig
from digest.domain.llm_port import ItemWithSummary
from digest.domain.models import Item
from digest.use_cases.build_digest import build_digest


def _item(title: str, url: str, source: str = "rss", date: str | None = None) -> Item:
    return Item(title=title, url=url, source=source, date=date)


class MockLLM:
    """LLM mock que preserva el orden original para aislar el test del ranking."""

    def summarize(self, title: str, snippet: str) -> str:
        return f"Resumen de: {title}"

    def rank(self, items: list[ItemWithSummary], top_n: int = 5) -> list[ItemWithSummary]:
        # No reordena, para que el test valide la diversidad del prefiltro
        return items[:top_n]


class TestSourceDiversityE2E:
    """El digest final debe incluir artículos de fuentes variadas."""

    def test_digest_includes_multiple_sources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Con RSS + HN disponibles, el digest final debe tener ítems de ambas fuentes."""
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        # Simular candidatos ya en orden round-robin (como produce prefilter_candidates)
        rss_items = [
            _item(f"RSS {i}", f"https://rss.com/{i}", "rss", "2026-02-10") for i in range(40)
        ]
        hn_items = [
            _item(f"HN {i}", f"https://hn.com/{i}", "hacker_news", "2026-02-10") for i in range(10)
        ]
        candidates = []
        for i in range(max(len(rss_items), len(hn_items))):
            if i < len(rss_items):
                candidates.append(rss_items[i])
            if i < len(hn_items):
                candidates.append(hn_items[i])

        def mock_core_pipeline(*args, **kwargs):
            return candidates

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_core_pipeline,
        )

        result = build_digest(sources, links_file, history_file, MockLLM(), top_n=5)
        sources_in_result = {x.item.source for x in result}

        assert len(result) == 5
        assert "hacker_news" in sources_in_result, (
            f"HN debe estar en el digest. Fuentes: {sources_in_result}"
        )

    def test_digest_with_three_sources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Con RSS + HN + Reddit, el digest debe tener al menos 2 fuentes distintas."""
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        rss_items = [
            _item(f"RSS {i}", f"https://rss.com/{i}", "rss", "2026-02-10") for i in range(30)
        ]
        hn_items = [
            _item(f"HN {i}", f"https://hn.com/{i}", "hacker_news", "2026-02-10") for i in range(8)
        ]
        rd_items = [
            _item(f"RD {i}", f"https://reddit.com/r/ml/{i}", "reddit", "2026-02-10")
            for i in range(5)
        ]
        candidates = []
        for i in range(max(len(rss_items), len(hn_items), len(rd_items))):
            if i < len(rss_items):
                candidates.append(rss_items[i])
            if i < len(hn_items):
                candidates.append(hn_items[i])
            if i < len(rd_items):
                candidates.append(rd_items[i])

        def mock_core_pipeline(*args, **kwargs):
            return candidates

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_core_pipeline,
        )

        result = build_digest(sources, links_file, history_file, MockLLM(), top_n=5)
        sources_in_result = {x.item.source for x in result}

        assert len(sources_in_result) >= 2, (
            f"El digest debe tener al menos 2 fuentes distintas, tiene: {sources_in_result}"
        )

    def test_no_single_source_dominates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ninguna fuente única debe acaparar todos los slots del digest."""
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        # Candidatos en orden round-robin (como produce prefilter_candidates)
        rss_items = [
            _item(f"RSS {i}", f"https://rss.com/{i}", "rss", "2026-02-10") for i in range(50)
        ]
        hn_items = [
            _item(f"HN {i}", f"https://hn.com/{i}", "hacker_news", "2026-02-10") for i in range(15)
        ]
        rd_items = [
            _item(f"RD {i}", f"https://reddit.com/r/ml/{i}", "reddit", "2026-02-10")
            for i in range(5)
        ]
        candidates = []
        for i in range(max(len(rss_items), len(hn_items), len(rd_items))):
            if i < len(rss_items):
                candidates.append(rss_items[i])
            if i < len(hn_items):
                candidates.append(hn_items[i])
            if i < len(rd_items):
                candidates.append(rd_items[i])

        def mock_core_pipeline(*args, **kwargs):
            return candidates

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_core_pipeline,
        )

        result = build_digest(
            sources,
            links_file,
            history_file,
            MockLLM(),
            prefilter_limit=30,
            top_n=5,
        )

        # Contar por fuente
        source_counts = {}
        for x in result:
            source_counts[x.item.source] = source_counts.get(x.item.source, 0) + 1

        # Ninguna fuente sola debe tener los 5 slots si hay otras disponibles
        for src, count in source_counts.items():
            assert count < 5, (
                f"La fuente '{src}' tiene {count}/5 slots. "
                f"No debe dominar completamente. Distribución: {source_counts}"
            )


class TestImageEnrichment:
    """Cada ítem del digest final debe tener un campo image_url."""

    def test_items_have_image_url_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Los ItemWithSummary del resultado deben tener el atributo image_url."""
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        candidates = [
            _item("Article", "https://example.com/article", "rss", "2026-02-10"),
        ]

        def mock_core_pipeline(*args, **kwargs):
            return candidates

        # Mock OG image fetching para no hacer HTTP real
        def mock_fetch_og_image(url, **kwargs):
            return "https://example.com/image.jpg"

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_core_pipeline,
        )
        monkeypatch.setattr(
            "digest.use_cases.build_digest.fetch_og_image",
            mock_fetch_og_image,
        )

        result = build_digest(sources, links_file, history_file, MockLLM(), top_n=5)
        assert len(result) == 1
        assert hasattr(result[0], "image_url"), "ItemWithSummary debe tener el campo image_url"

    def test_image_url_populated_from_og(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """image_url debe llenarse con la imagen OG del artículo."""
        history_file = tmp_path / "sent.json"
        history_file.write_text("{}")
        links_file = tmp_path / "links.md"
        links_file.write_text("")
        sources = SourcesConfig(rss=[], hacker_news=None, reddit=None)

        candidates = [
            _item("Art 1", "https://example.com/1", "rss", "2026-02-10"),
            _item("Art 2", "https://example.com/2", "hacker_news", "2026-02-10"),
        ]

        og_images = {
            "https://example.com/1": "https://example.com/img1.jpg",
            "https://example.com/2": None,  # No tiene imagen
        }

        def mock_core_pipeline(*args, **kwargs):
            return candidates

        def mock_fetch_og_image(url, **kwargs):
            return og_images.get(url)

        monkeypatch.setattr(
            "digest.use_cases.build_digest.run_core_pipeline",
            mock_core_pipeline,
        )
        monkeypatch.setattr(
            "digest.use_cases.build_digest.fetch_og_image",
            mock_fetch_og_image,
        )

        result = build_digest(sources, links_file, history_file, MockLLM(), top_n=5)
        assert result[0].image_url == "https://example.com/img1.jpg"
        assert result[1].image_url is None
