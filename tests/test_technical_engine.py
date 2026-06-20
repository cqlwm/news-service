from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from news_service.technical.engine import TechnicalEngine
from news_service.technical.models import TechnicalConfig, DetectedPattern


class TestTechnicalEngine:
    """测试技术面检测引擎。"""

    @pytest.fixture
    def engine(self) -> TechnicalEngine:
        cfg = TechnicalConfig(
            symbols=["BTCUSDT", "ETHUSDT"],
            timeframes=["1d"],
            top_n=5,
            min_consecutive=3,
            rsi_period=14,
            rsi_overbought=70.0,
            rsi_oversold=30.0,
            volume_period=10,
            volume_multiplier=2.0,
            min_volume_usdt=100_000,
            min_price_change_pct=0.5,
        )
        return TechnicalEngine(config=cfg)

    @pytest.mark.asyncio
    async def test_deduplicate_same_pattern(self) -> None:
        """相同 symbol + pattern_type 应去重，保留 severity 最高的。"""
        patterns = [
            DetectedPattern(
                symbol="BTC/USDT", pattern_type="consecutive_bullish_1d",
                direction="bullish", title="test1", description="desc1", severity=3,
            ),
            DetectedPattern(
                symbol="BTC/USDT", pattern_type="consecutive_bullish_1d",
                direction="bullish", title="test2", description="desc2", severity=5,
            ),
            DetectedPattern(
                symbol="ETH/USDT", pattern_type="rsi_oversold_1d",
                direction="bullish", title="test3", description="desc3", severity=2,
            ),
        ]
        result = TechnicalEngine._deduplicate(patterns)
        assert len(result) == 2
        btc = [p for p in result if p.symbol == "BTC/USDT"][0]
        assert btc.severity == 5  # 保留了 severity 更高的

    def test_to_news_detail(self) -> None:
        """DetectedPattern 应正确转换为 NewsDetail。"""
        pattern = DetectedPattern(
            symbol="BTC/USDT",
            pattern_type="consecutive_bullish_1d",
            direction="bullish",
            title="BTC 日线连续3根上涨",
            description="BTC 日线连续3根上涨，最新价格 50000 USDT",
            severity=3,
        )
        news = TechnicalEngine._to_news_detail(pattern)
        assert news.title == "BTC 日线连续3根上涨"
        assert news.content == "BTC 日线连续3根上涨，最新价格 50000 USDT"
        assert news.source == "Technical Analysis"
        assert news.id.startswith("tech_")

    @pytest.mark.asyncio
    async def test_run_with_mocked_detectors(self, engine: TechnicalEngine) -> None:
        """使用 mock 检测器验证 run 流程。"""
        # Mock ranker to return a fixed symbol
        engine.ranker.rank = AsyncMock(return_value=[])
        engine.config.symbols = ["BTCUSDT"]

        # Mock market_data to return empty (no patterns expected)
        engine.market_data.get_top_symbols_ohlcv = AsyncMock(return_value={})

        results = await engine.run()
        assert len(results) == 0

    def test_update_config(self, engine: TechnicalEngine) -> None:
        """运行时更新配置应生效。"""
        new_cfg = TechnicalConfig(top_n=10, min_consecutive=5)
        engine.update_config(new_cfg)
        assert engine.ranker.top_n == 10
        assert engine.config.min_consecutive == 5
