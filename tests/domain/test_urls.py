"""Tests para normalización de URL y lógica de filtro de ya enviados (T8.1)."""

from digest.domain.models import Item
from digest.domain.urls import normalize_url


class TestNormalizeUrl:
    """Normalización de URL para dedup y comparación con historial."""

    def test_removes_fragment_and_query(self) -> None:
        assert (
            normalize_url("https://example.com/path?q=1&utm=x#section")
            == "https://example.com/path"
        )

    def test_lowercases_scheme_and_host(self) -> None:
        assert normalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"

    def test_removes_trailing_slash_from_path(self) -> None:
        assert normalize_url("https://example.com/foo/") == "https://example.com/foo"

    def test_empty_path_becomes_slash(self) -> None:
        assert normalize_url("https://example.com") == "https://example.com/"

    def test_strips_whitespace(self) -> None:
        assert normalize_url("  https://example.com/a  ") == "https://example.com/a"

    def test_empty_string_returns_empty(self) -> None:
        assert normalize_url("") == ""
        assert normalize_url("   ") == ""

    def test_same_url_different_query_normalize_equal(self) -> None:
        u1 = normalize_url("https://site.com/article?utm=twitter")
        u2 = normalize_url("https://site.com/article?utm=email")
        assert u1 == u2 == "https://site.com/article"


class TestFilterAlreadySent:
    """Filtro de ya enviados: excluir ítems cuya URL normalizada está en el historial."""

    def _filter_sent(self, items: list[Item], sent_urls: set[str]) -> list[Item]:
        """Lógica del filtro: historial contiene URLs normalizadas."""
        sent_normalized = {normalize_url(u) for u in sent_urls}
        return [i for i in items if normalize_url(i.url) not in sent_normalized]

    def test_keeps_item_not_in_history(self) -> None:
        items = [Item(title="A", url="https://new.com/post", source="rss")]
        sent = {"https://old.com/other"}
        assert self._filter_sent(items, sent) == items

    def test_removes_item_whose_url_was_sent(self) -> None:
        items = [
            Item(title="A", url="https://site.com/a", source="rss"),
            Item(title="B", url="https://site.com/b", source="manual"),
        ]
        sent = {"https://site.com/a"}
        result = self._filter_sent(items, sent)
        assert len(result) == 1 and result[0].url == "https://site.com/b"

    def test_removes_by_normalized_url(self) -> None:
        """URL con query/fragment debe coincidir con la misma base en historial."""
        items = [Item(title="X", url="https://site.com/page?ref=1#top", source="rss")]
        sent = {"https://site.com/page"}
        assert self._filter_sent(items, sent) == []

    def test_empty_history_keeps_all(self) -> None:
        items = [
            Item(title="A", url="https://a.com/1", source="rss"),
            Item(title="B", url="https://b.com/2", source="manual"),
        ]
        assert self._filter_sent(items, set()) == items

    def test_empty_items_returns_empty(self) -> None:
        assert self._filter_sent([], {"https://any.com"}) == []
