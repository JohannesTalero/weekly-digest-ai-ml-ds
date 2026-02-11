"""Tests de load_sent_urls y save_sent_urls (data/sent-urls.*)."""

from pathlib import Path

import json
import pytest

from digest.config.history import load_sent_urls, save_sent_urls


class TestLoadSentUrls:
    def test_missing_file_returns_empty_set(self, tmp_path: Path) -> None:
        assert load_sent_urls(tmp_path / "sent.json") == set()

    def test_empty_json_returns_empty_set(self, tmp_path: Path) -> None:
        (tmp_path / "s.json").write_text("{}")
        assert load_sent_urls(tmp_path / "s.json") == set()

    def test_parses_json_urls(self, tmp_path: Path) -> None:
        (tmp_path / "s.json").write_text('{"urls": ["https://a.com", "https://b.com"], "updated": "2025-01-01"}')
        got = load_sent_urls(tmp_path / "s.json")
        assert got == {"https://a.com", "https://b.com"}

    def test_ignores_non_string_entries(self, tmp_path: Path) -> None:
        (tmp_path / "s.json").write_text('{"urls": ["https://a.com", 1, null], "updated": null}')
        assert load_sent_urls(tmp_path / "s.json") == {"https://a.com"}

    def test_txt_one_per_line(self, tmp_path: Path) -> None:
        (tmp_path / "s.txt").write_text("https://x.com/1\nhttps://x.com/2\n")
        assert load_sent_urls(tmp_path / "s.txt") == {"https://x.com/1", "https://x.com/2"}

    def test_invalid_json_returns_empty_set(self, tmp_path: Path) -> None:
        (tmp_path / "s.json").write_text("not json {")
        assert load_sent_urls(tmp_path / "s.json") == set()


class TestSaveSentUrls:
    def test_writes_json_with_updated(self, tmp_path: Path) -> None:
        path = tmp_path / "out" / "sent.json"
        save_sent_urls(path, {"https://c.com", "https://a.com"})
        assert path.exists()
        data = json.loads(path.read_text())
        assert set(data["urls"]) == {"https://a.com", "https://c.com"}
        assert "updated" in data and len(data["updated"]) == 10  # YYYY-MM-DD

    def test_accepts_list(self, tmp_path: Path) -> None:
        path = tmp_path / "sent.json"
        save_sent_urls(path, ["https://x.com", "https://x.com"])
        data = json.loads(path.read_text())
        assert data["urls"] == ["https://x.com"]

    def test_empty_list_writes_empty_urls(self, tmp_path: Path) -> None:
        path = tmp_path / "sent.json"
        save_sent_urls(path, [])
        data = json.loads(path.read_text())
        assert data["urls"] == []
