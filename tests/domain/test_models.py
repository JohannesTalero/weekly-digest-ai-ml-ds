"""Tests del modelo Item (validación)."""

import pytest

from digest.domain.models import Item


class TestItem:
    def test_valid_item_creates(self) -> None:
        item = Item(title="T", url="https://x.com/a", source="rss")
        assert item.title == "T" and item.url == "https://x.com/a" and item.source == "rss"

    def test_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url no puede estar vacío"):
            Item(title="T", url="", source="manual")

    def test_whitespace_only_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url no puede estar vacío"):
            Item(title="T", url="   ", source="manual")

    def test_invalid_source_raises(self) -> None:
        with pytest.raises(ValueError, match="source debe ser"):
            Item(title="T", url="https://x.com", source="unknown")

    def test_all_sources_accepted(self) -> None:
        for src in ("rss", "manual", "hacker_news", "reddit"):
            item = Item(title="T", url="https://x.com", source=src)
            assert item.source == src
