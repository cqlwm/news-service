from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news_service.technical.symbol_ranker import SymbolRanker


class TestSymbolRanker:
    """测试动态币种排名器。"""

    @pytest.fixture
    def ranker(self) -> SymbolRanker:
        return SymbolRanker(top_n=5, min_volume_usdt=1_000_000, min_price_change_pct=1.0)

    @pytest.mark.asyncio
    async def test_rank_filters_and_sorts(self, ranker: SymbolRanker) -> None:
        """排名器应正确过滤和排序交易对。"""
        mock_tickers = [
            {"symbol": "BTCUSDT", "quoteVolume": "10000000", "priceChangePercent": "5.0"},
            {"symbol": "ETHUSDT", "quoteVolume": "5000000", "priceChangePercent": "3.0"},
            {"symbol": "LOWVOLUSDT", "quoteVolume": "100", "priceChangePercent": "10.0"},
            {"symbol": "STABLEUSDT", "quoteVolume": "10000000", "priceChangePercent": "0.1"},
            {"symbol": "SOLUSDT", "quoteVolume": "3000000", "priceChangePercent": "8.0"},
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = mock_tickers

        async def mock_get(*args, **kwargs):
            return mock_response

        with patch.object(ranker._client, "get", side_effect=mock_get):
            result = await ranker.rank()

        symbols = [r.symbol for r in result]
        assert "LOWVOLUSDT" not in symbols
        assert "STABLEUSDT" not in symbols
        assert result[0].symbol == "BTCUSDT"
        assert result[0].score > result[1].score
        assert len(result) <= 5

    @pytest.mark.asyncio
    async def test_rank_empty_response(self, ranker: SymbolRanker) -> None:
        """API 返回空列表时应返回空列表。"""
        mock_response = MagicMock()
        mock_response.json.return_value = []

        async def mock_get(*args, **kwargs):
            return mock_response

        with patch.object(ranker._client, "get", side_effect=mock_get):
            result = await ranker.rank()
            assert result == []

    @pytest.mark.asyncio
    async def test_rank_api_error(self, ranker: SymbolRanker) -> None:
        """API 请求失败时应返回空列表。"""
        async def mock_get(*args, **kwargs):
            raise Exception("Connection error")

        with patch.object(ranker._client, "get", side_effect=mock_get):
            result = await ranker.rank()
            assert result == []
