from __future__ import annotations

import pytest

from news_service.filters import KeywordFilter
from news_service.filters.base import NewsFilter
from news_service.models import NewsDetail


class TestKeywordFilter:
    """测试 KeywordFilter 关键词匹配逻辑。"""

    @pytest.mark.asyncio
    async def test_match_title(self, keyword_filter: KeywordFilter) -> None:
        news = NewsDetail(
            id="t1", title="BTC price surges", content="Some content",
            source="CoinDesk", url="https://example.com", published_at=None,
        )
        assert await keyword_filter.should_include(news) is True

    @pytest.mark.asyncio
    async def test_match_content(self, keyword_filter: KeywordFilter) -> None:
        news = NewsDetail(
            id="t2", title="Market update", content="ETH is rallying today",
            source="CoinDesk", url="https://example.com", published_at=None,
        )
        assert await keyword_filter.should_include(news) is True

    @pytest.mark.asyncio
    async def test_match_source(self, keyword_filter: KeywordFilter) -> None:
        news = NewsDetail(
            id="t3", title="Market update", content="Nothing special",
            source="BTC News", url="https://example.com", published_at=None,
        )
        assert await keyword_filter.should_include(news) is True

    @pytest.mark.asyncio
    async def test_no_match(self, keyword_filter: KeywordFilter) -> None:
        news = NewsDetail(
            id="t4", title="Apple stock rises", content="AAPL hits new high",
            source="Bloomberg", url="https://example.com", published_at=None,
        )
        assert await keyword_filter.should_include(news) is False

    @pytest.mark.asyncio
    async def test_empty_keywords(self) -> None:
        filter_ = KeywordFilter(keywords=[])
        news = NewsDetail(
            id="t5", title="Anything", content="Nothing relevant",
            source="Unknown", url="https://example.com", published_at=None,
        )
        assert await filter_.should_include(news) is True

    @pytest.mark.asyncio
    async def test_case_insensitive(self, keyword_filter: KeywordFilter) -> None:
        news = NewsDetail(
            id="t6", title="bitcoin is great", content="btc to the moon",
            source="Reddit", url="https://example.com", published_at=None,
        )
        assert await keyword_filter.should_include(news) is True

    @pytest.mark.asyncio
    async def test_match_source_disabled(self) -> None:
        filter_ = KeywordFilter(keywords=["BTC"], match_source=False)
        news = NewsDetail(
            id="t7", title="Hello", content="World",
            source="BTC News", url="https://example.com", published_at=None,
        )
        assert await filter_.should_include(news) is False

    @pytest.mark.asyncio
    async def test_partial_keyword_match(self, keyword_filter: KeywordFilter) -> None:
        news = NewsDetail(
            id="t8", title="ETHEREUM 2.0 launch", content="Details here",
            source="Cointelegraph", url="https://example.com", published_at=None,
        )
        assert await keyword_filter.should_include(news) is True

    def test_name(self, keyword_filter: KeywordFilter) -> None:
        assert keyword_filter.name == "keyword_filter"


class TestNewsFilterBase:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            NewsFilter()  # type: ignore[abstract]
