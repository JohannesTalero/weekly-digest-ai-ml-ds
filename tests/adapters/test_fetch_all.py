"""Tests del orquestador fetch_all (T3.5)."""

import tempfile
from pathlib import Path

import pytest
from digest.adapters.fetch_all import fetch_all_items
from digest.config.sources import RssSource, SourcesConfig


def test_fetch_all_items_empty_config():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("")
        path = f.name
    try:
        config = SourcesConfig(rss=[], hacker_news=None, reddit=None)
        items = fetch_all_items(config, path)
        assert items == []
    finally:
        Path(path).unlink(missing_ok=True)


def test_fetch_all_items_manual_only():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("https://example.com/manual\n")
        path = f.name
    try:
        config = SourcesConfig(rss=[], hacker_news=None, reddit=None)
        items = fetch_all_items(config, path)
        assert len(items) == 1
        assert items[0].source == "manual"
        assert items[0].url == "https://example.com/manual"
    finally:
        Path(path).unlink(missing_ok=True)


def test_fetch_all_continues_if_rss_fails(httpx_mock):
    httpx_mock.add_response(url="https://broken.com/feed", status_code=500)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("https://manual.com/one\n")
        path = f.name
    try:
        config = SourcesConfig(
            rss=[RssSource(name="Broken", url="https://broken.com/feed")],
            hacker_news=None,
            reddit=None,
        )
        items = fetch_all_items(config, path, timeout=5.0)
        # Manual sigue funcionando aunque RSS falle
        assert len(items) == 1
        assert items[0].url == "https://manual.com/one"
    finally:
        Path(path).unlink(missing_ok=True)
