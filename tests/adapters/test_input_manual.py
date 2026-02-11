"""Tests del adaptador manual/links (T3.2)."""

import tempfile
from pathlib import Path

from digest.adapters.input_manual import fetch_manual_items


def test_fetch_manual_items_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Comentario\n\n")
        path = f.name
    try:
        items = fetch_manual_items(path)
        assert items == []
    finally:
        Path(path).unlink(missing_ok=True)


def test_fetch_manual_items_returns_items():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("https://example.com/one\nhttps://example.com/two  Titulo opcional\n")
        path = f.name
    try:
        items = fetch_manual_items(path)
        assert len(items) == 2
        assert all(i.source == "manual" for i in items)
        assert items[0].url == "https://example.com/one"
        assert items[1].url == "https://example.com/two"
        assert items[1].title == "Titulo opcional"
    finally:
        Path(path).unlink(missing_ok=True)


def test_fetch_manual_items_missing_path():
    assert fetch_manual_items("/nonexistent/links.md") == []
