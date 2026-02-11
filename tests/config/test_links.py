"""Tests de load_links (config/links.md)."""

from pathlib import Path


from digest.config.links import load_links


class TestLoadLinks:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert load_links(tmp_path / "no.md") == []

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "l.md").write_text("")
        assert load_links(tmp_path / "l.md") == []

    def test_ignores_empty_lines_and_comments(self, tmp_path: Path) -> None:
        (tmp_path / "l.md").write_text("""
# comment
https://example.com/one

# another
https://example.com/two
""")
        items = load_links(tmp_path / "l.md")
        assert len(items) == 2
        assert items[0].url == "https://example.com/one" and items[0].source == "manual"
        assert items[1].url == "https://example.com/two"

    def test_url_with_optional_title(self, tmp_path: Path) -> None:
        (tmp_path / "l.md").write_text("https://site.com/post  My optional title\n")
        items = load_links(tmp_path / "l.md")
        assert len(items) == 1
        assert items[0].url == "https://site.com/post" and items[0].title == "My optional title"

    def test_skips_line_without_http_url(self, tmp_path: Path) -> None:
        (tmp_path / "l.md").write_text("not-a-url\nftp://old.com/skip\nhttps://ok.com/yes\n")
        items = load_links(tmp_path / "l.md")
        assert len(items) == 1 and items[0].url == "https://ok.com/yes"
