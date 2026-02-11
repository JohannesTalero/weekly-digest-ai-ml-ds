"""Tests del prefiltro balanceado por fuente (fix crítico: diversidad de fuentes).

El prefiltro actual hace items[:limit] que favorece la fuente que se agrega primero
(RSS/Distill). Estos tests verifican que el nuevo prefiltro seleccione ítems de TODAS
las fuentes de forma proporcional (round-robin).
"""

from digest.domain.models import Item
from digest.use_cases.pipeline_core import prefilter_candidates


def _item(title: str, url: str, source: str = "rss") -> Item:
    return Item(title=title, url=url, source=source)


class TestPrefilterBalanced:
    """El prefiltro debe distribuir slots entre fuentes disponibles."""

    def test_single_source_returns_first_n(self) -> None:
        """Si solo hay una fuente, devuelve los primeros N."""
        items = [_item(f"RSS {i}", f"https://rss.com/{i}", "rss") for i in range(10)]
        result = prefilter_candidates(items, limit=5)
        assert len(result) == 5
        assert all(it.source == "rss" for it in result)

    def test_two_sources_balanced(self) -> None:
        """Con 2 fuentes (50 RSS + 15 HN), limit=10 debe incluir ítems de ambas."""
        rss_items = [_item(f"RSS {i}", f"https://rss.com/{i}", "rss") for i in range(50)]
        hn_items = [_item(f"HN {i}", f"https://hn.com/{i}", "hacker_news") for i in range(15)]
        combined = rss_items + hn_items  # RSS primero, igual que en fetch_all

        result = prefilter_candidates(combined, limit=10)
        sources = {it.source for it in result}
        assert "rss" in sources, "Debe incluir ítems RSS"
        assert "hacker_news" in sources, "Debe incluir ítems de Hacker News"

    def test_three_sources_all_represented(self) -> None:
        """Con 3 fuentes, limit=9 debe incluir ítems de las 3."""
        rss = [_item(f"RSS {i}", f"https://rss.com/{i}", "rss") for i in range(40)]
        hn = [_item(f"HN {i}", f"https://hn.com/{i}", "hacker_news") for i in range(10)]
        reddit = [_item(f"RD {i}", f"https://rd.com/{i}", "reddit") for i in range(5)]
        combined = rss + hn + reddit

        result = prefilter_candidates(combined, limit=9)
        sources = {it.source for it in result}
        assert sources == {"rss", "hacker_news", "reddit"}, (
            f"Las 3 fuentes deben estar representadas, obtuve: {sources}"
        )

    def test_four_sources_all_represented(self) -> None:
        """Con 4 fuentes, limit=8 debe incluir ítems de las 4."""
        rss = [_item(f"RSS {i}", f"https://rss.com/{i}", "rss") for i in range(30)]
        hn = [_item(f"HN {i}", f"https://hn.com/{i}", "hacker_news") for i in range(10)]
        reddit = [_item(f"RD {i}", f"https://rd.com/{i}", "reddit") for i in range(5)]
        manual = [_item(f"MN {i}", f"https://mn.com/{i}", "manual") for i in range(3)]
        combined = rss + manual + hn + reddit

        result = prefilter_candidates(combined, limit=8)
        sources = {it.source for it in result}
        assert sources == {"rss", "hacker_news", "reddit", "manual"}, (
            f"Las 4 fuentes deben estar representadas, obtuve: {sources}"
        )

    def test_small_source_exhausted_fills_from_others(self) -> None:
        """Si una fuente tiene pocos ítems, se agotan y los slots restantes van a otras."""
        rss = [_item(f"RSS {i}", f"https://rss.com/{i}", "rss") for i in range(50)]
        hn = [_item(f"HN {i}", f"https://hn.com/{i}", "hacker_news") for i in range(2)]
        combined = rss + hn

        result = prefilter_candidates(combined, limit=10)
        assert len(result) == 10
        hn_count = sum(1 for it in result if it.source == "hacker_news")
        rss_count = sum(1 for it in result if it.source == "rss")
        assert hn_count == 2, "Debe incluir los 2 ítems de HN disponibles"
        assert rss_count == 8, "El resto se llena con RSS"

    def test_limit_none_returns_all(self) -> None:
        """limit=None no recorta, devuelve todo."""
        items = [_item(f"A {i}", f"https://a.com/{i}", "rss") for i in range(5)]
        result = prefilter_candidates(items, limit=None)
        assert len(result) == 5

    def test_fewer_items_than_limit_returns_all(self) -> None:
        """Si hay menos ítems que el límite, devuelve todos sin recortar."""
        items = [
            _item("RSS", "https://rss.com/1", "rss"),
            _item("HN", "https://hn.com/1", "hacker_news"),
        ]
        result = prefilter_candidates(items, limit=30)
        assert len(result) == 2

    def test_realistic_scenario_distill_plus_hn(self) -> None:
        """Escenario real: 47 Distill (RSS) + 15 HN, limit=30. HN NO debe ser cortado."""
        distill = [_item(f"Distill {i}", f"https://distill.pub/{i}", "rss") for i in range(47)]
        hn = [_item(f"HN {i}", f"https://hn.com/{i}", "hacker_news") for i in range(15)]
        combined = distill + hn  # Orden real de fetch_all

        result = prefilter_candidates(combined, limit=30)
        hn_in_result = [it for it in result if it.source == "hacker_news"]
        rss_in_result = [it for it in result if it.source == "rss"]

        assert len(hn_in_result) > 0, (
            "HN DEBE estar en el resultado (bug principal: antes se cortaba)"
        )
        assert len(hn_in_result) >= 10, (
            f"Con limit=30, HN debería tener al menos 10 slots, tiene {len(hn_in_result)}"
        )
        assert len(rss_in_result) > 0, "RSS también debe estar"
        assert len(result) == 30

    def test_respects_total_limit(self) -> None:
        """El resultado nunca excede el límite."""
        items = [_item(f"RSS {i}", f"https://rss.com/{i}", "rss") for i in range(20)] + [
            _item(f"HN {i}", f"https://hn.com/{i}", "hacker_news") for i in range(20)
        ]
        result = prefilter_candidates(items, limit=15)
        assert len(result) == 15
