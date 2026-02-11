"""Tests del filtro de frescura por fecha (excluir artículos viejos).

Distill.pub no publica desde 2021, así que sus 52 artículos son de 2017-2021.
El filtro de frescura evita que artículos antiguos consuman slots del digest.
"""

from datetime import datetime, timedelta

from digest.domain.models import Item
from digest.use_cases.pipeline_core import filter_stale


def _item(title: str, url: str, source: str = "rss", date: str | None = None) -> Item:
    return Item(title=title, url=url, source=source, date=date)


class TestFilterStale:
    """Filtro de frescura: descarta artículos más viejos que max_age_days."""

    def test_removes_old_articles(self) -> None:
        """Artículos con fecha > max_age_days se eliminan."""
        old_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
        recent_date = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")

        items = [
            _item("Old", "https://old.com/1", date=old_date),
            _item("Recent", "https://new.com/1", date=recent_date),
        ]
        result = filter_stale(items, max_age_days=90)
        assert len(result) == 1
        assert result[0].title == "Recent"

    def test_keeps_items_without_date(self) -> None:
        """Ítems sin fecha (date=None) se mantienen (no podemos saber si son viejos)."""
        old_date = "2020-01-01"
        items = [
            _item("No date", "https://a.com/1", date=None),
            _item("Old", "https://b.com/1", date=old_date),
        ]
        result = filter_stale(items, max_age_days=90)
        assert len(result) == 1
        assert result[0].title == "No date"

    def test_keeps_recent_articles(self) -> None:
        """Artículos dentro del rango de frescura se mantienen."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        items = [
            _item("Today", "https://a.com/1", date=today),
            _item("Yesterday", "https://b.com/1", date=yesterday),
        ]
        result = filter_stale(items, max_age_days=90)
        assert len(result) == 2

    def test_fallback_if_all_old(self) -> None:
        """Si TODOS los artículos son viejos, devuelve todos (fallback para no vaciar)."""
        old = [_item(f"Old {i}", f"https://old.com/{i}", date="2019-06-01") for i in range(5)]
        result = filter_stale(old, max_age_days=90)
        assert len(result) == 5, "Si todo es viejo, fallback devuelve todos"

    def test_empty_list_returns_empty(self) -> None:
        assert filter_stale([], max_age_days=90) == []

    def test_distill_2021_filtered_out(self) -> None:
        """Escenario real: artículos de Distill 2021 se filtran si hay contenido fresco."""
        distill_items = [
            _item(f"Distill {i}", f"https://distill.pub/{i}", "rss", date="2021-03-15")
            for i in range(10)
        ]
        fresh_items = [
            _item(
                "HN fresh",
                "https://hn.com/1",
                "hacker_news",
                date=datetime.utcnow().strftime("%Y-%m-%d"),
            ),
        ]
        combined = distill_items + fresh_items
        result = filter_stale(combined, max_age_days=90)
        assert len(result) == 1
        assert result[0].source == "hacker_news"

    def test_custom_max_age(self) -> None:
        """max_age_days configurable: 30 días es más estricto que 90."""
        date_60_days_ago = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
        date_10_days_ago = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d")
        items = [
            _item("60 days", "https://a.com/1", date=date_60_days_ago),
            _item("10 days", "https://b.com/1", date=date_10_days_ago),
        ]
        result_30 = filter_stale(items, max_age_days=30)
        result_90 = filter_stale(items, max_age_days=90)
        assert len(result_30) == 1
        assert result_30[0].title == "10 days"
        assert len(result_90) == 2
