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

    def test_merge_to_news_detail_single_pattern(self) -> None:
        """单个模式应正确合并为 NewsDetail。"""
        patterns = [
            DetectedPattern(
                symbol="BTC/USDT",
                pattern_type="consecutive_bullish_1d",
                direction="bullish",
                title="BTC 日线连续3根上涨",
                description="BTC 日线连续3根上涨，最新价格 50000 USDT",
                severity=3,
            ),
        ]
        news = TechnicalEngine._merge_to_news_detail("BTC/USDT", patterns)
        assert news.title == "BTC 日线连续3根上涨"
        assert "BTC 日线连续3根上涨" in news.content
        assert news.source == "Technical Analysis"
        assert news.id.startswith("tech_BTC_")

    def test_merge_to_news_detail_multiple_patterns(self) -> None:
        """多个模式应合并为一条 NewsDetail，标题取 severity 最高的。"""
        patterns = [
            DetectedPattern(
                symbol="BTC/USDT",
                pattern_type="consecutive_bullish_1d",
                direction="bullish",
                title="BTC 日线连续3根上涨",
                description="BTC 日线连续3根上涨，最新价格 50000 USDT",
                severity=3,
            ),
            DetectedPattern(
                symbol="BTC/USDT",
                pattern_type="rsi_oversold_1d",
                direction="bullish",
                title="BTC RSI 超卖",
                description="BTC 14日RSI 低于30",
                severity=4,
            ),
        ]
        news = TechnicalEngine._merge_to_news_detail("BTC/USDT", patterns)
        # 标题取 severity 最高的（RSI 超卖 severity=4 > 连阳 severity=3）
        assert news.title == "BTC RSI 超卖"
        assert "[BULLISH]" in news.content
        assert "BTC RSI 超卖" in news.content
        assert "BTC 日线连续3根上涨" in news.content

    @pytest.mark.asyncio
    async def test_run_with_mocked_detectors(self, engine: TechnicalEngine) -> None:
        """使用 mock 检测器验证 run 流程。"""
        engine.ranker.rank = AsyncMock(return_value=[])
        engine.config.symbols = ["BTCUSDT"]

        # Mock market_data to return empty OHLCV (no patterns expected)
        engine.market_data.get_top_symbols_ohlcv = AsyncMock(return_value={})

        results = await engine.run()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_skip_when_candle_not_changed(self, engine: TechnicalEngine) -> None:
        """同一 K 线时间戳下，第二次 run 应跳过检测器。"""
        engine.ranker.rank = AsyncMock(return_value=[])
        engine.config.symbols = ["BTCUSDT"]

        candle_ts = 1700000000000
        mock_ohlcv = {
            "BTC/USDT": [
                {"timestamp": candle_ts - 86400000, "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
                {"timestamp": candle_ts, "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1200},
            ],
        }
        engine.market_data.get_top_symbols_ohlcv = AsyncMock(return_value=mock_ohlcv)

        # 第一次运行：应调用检测器
        with patch.object(engine.detectors[0], "detect", new=AsyncMock(return_value=[])) as mock_detect:
            await engine.run()
            assert mock_detect.call_count >= 1

        # 第二次运行（相同 K 线）：应跳过检测器
        with patch.object(engine.detectors[0], "detect", new=AsyncMock(return_value=[])) as mock_detect:
            await engine.run()
            assert mock_detect.call_count == 0, "K 线未变化时应跳过检测器"

    @pytest.mark.asyncio
    async def test_run_again_when_candle_changed(self, engine: TechnicalEngine) -> None:
        """K 线时间戳变化后，第二次 run 应重新运行检测器。"""
        engine.ranker.rank = AsyncMock(return_value=[])
        engine.config.symbols = ["BTCUSDT"]

        old_ts = 1700000000000
        new_ts = 1700086400000

        def make_ohlcv(last_ts: int) -> dict:
            return {
                "BTC/USDT": [
                    {"timestamp": last_ts - 86400000, "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
                    {"timestamp": last_ts, "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1200},
                ],
            }

        engine.market_data.get_top_symbols_ohlcv = AsyncMock(return_value=make_ohlcv(old_ts))

        # 第一次运行
        with patch.object(engine.detectors[0], "detect", new=AsyncMock(return_value=[])) as mock_detect:
            await engine.run()
            assert mock_detect.call_count >= 1

        # 第二次运行（K 线更新）
        engine.market_data.get_top_symbols_ohlcv = AsyncMock(return_value=make_ohlcv(new_ts))
        with patch.object(engine.detectors[0], "detect", new=AsyncMock(return_value=[])) as mock_detect:
            await engine.run()
            assert mock_detect.call_count >= 1, "K 线变化后应重新运行检测器"

    @pytest.mark.asyncio
    async def test_run_merges_patterns_by_symbol(self, engine: TechnicalEngine) -> None:
        """同一个 symbol 的多个模式应合并为一条新闻。"""
        engine.ranker.rank = AsyncMock(return_value=[])
        engine.config.symbols = ["BTCUSDT", "ETHUSDT"]

        candle_ts = 1700000000000
        mock_ohlcv = {
            "BTC/USDT": [
                {"timestamp": candle_ts - 86400000, "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
                {"timestamp": candle_ts, "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1200},
            ],
            "ETH/USDT": [
                {"timestamp": candle_ts - 86400000, "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 5000},
                {"timestamp": candle_ts, "open": 10.5, "high": 11.5, "low": 9.5, "close": 11, "volume": 6000},
            ],
        }
        engine.market_data.get_top_symbols_ohlcv = AsyncMock(return_value=mock_ohlcv)

        # Mock detectors to return patterns for both symbols
        async def mock_detect_btc(symbol: str, ohlcv: list, timeframe: str) -> list:
            if symbol == "BTC/USDT":
                return [
                    DetectedPattern(symbol="BTC/USDT", pattern_type="consecutive_bullish_1d",
                                    direction="bullish", title="BTC 连阳", description="BTC 连阳描述", severity=3),
                    DetectedPattern(symbol="BTC/USDT", pattern_type="rsi_oversold_1d",
                                    direction="bullish", title="BTC RSI", description="BTC RSI 描述", severity=4),
                ]
            return []

        async def mock_detect_eth(symbol: str, ohlcv: list, timeframe: str) -> list:
            if symbol == "ETH/USDT":
                return [
                    DetectedPattern(symbol="ETH/USDT", pattern_type="volume_spike_1d",
                                    direction="bullish", title="ETH 放量", description="ETH 放量描述", severity=2),
                ]
            return []

        # Patch all 3 detectors
        for d in engine.detectors:
            if "ConsecutiveCandle" in type(d).__name__:
                d.detect = mock_detect_btc
            elif "IndicatorSignal" in type(d).__name__:
                d.detect = mock_detect_btc
            else:
                d.detect = mock_detect_eth

        results = await engine.run()
        assert len(results) == 2, "2 个 symbol 应生成 2 条新闻"

        # BTC 新闻标题取 severity 最高的（RSI severity=4）
        btc_news = [n for n in results if "BTC" in n.title][0]
        assert btc_news.title == "BTC RSI"
        assert "BTC 连阳" in btc_news.content
        assert "BTC RSI" in btc_news.content

        # ETH 新闻只有一个模式
        eth_news = [n for n in results if "ETH" in n.title][0]
        assert eth_news.title == "ETH 放量"

    def test_update_config(self, engine: TechnicalEngine) -> None:
        """运行时更新配置应生效。"""
        new_cfg = TechnicalConfig(top_n=10, min_consecutive=5)
        engine.update_config(new_cfg)
        assert engine.ranker.top_n == 10
        assert engine.config.min_consecutive == 5
