from __future__ import annotations

import pytest

from news_service.technical.detectors import (
    ConsecutiveCandleDetector,
    IndicatorSignalDetector,
    VolumeSpikeDetector,
)


def _make_ohlcv(
    closes: list[float],
    opens: list[float] | None = None,
    volumes: list[float] | None = None,
) -> list[dict[str, float | int | str]]:
    """生成模拟 OHLCV 数据。"""
    if opens is None:
        opens = [c * 0.99 for c in closes]
    if volumes is None:
        volumes = [1000.0] * len(closes)

    result: list[dict[str, float | int | str]] = []
    for i in range(len(closes)):
        result.append({
            "timestamp": 1700000000000 + i * 86400000,
            "datetime_utc": "",
            "open": opens[i],
            "high": max(opens[i], closes[i]) * 1.02,
            "low": min(opens[i], closes[i]) * 0.98,
            "close": closes[i],
            "volume": volumes[i],
        })
    return result


class TestConsecutiveCandleDetector:
    """测试连续涨跌检测器。"""

    @pytest.fixture
    def detector(self) -> ConsecutiveCandleDetector:
        return ConsecutiveCandleDetector(min_consecutive=3)

    @pytest.mark.asyncio
    async def test_detect_bullish_streak(self, detector: ConsecutiveCandleDetector) -> None:
        """连续 5 根阳线应被检测到。"""
        closes = [100.0, 102.0, 105.0, 108.0, 112.0]
        ohlcv = _make_ohlcv(closes)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")

        bullish = [p for p in patterns if p.direction == "bullish"]
        assert len(bullish) == 1
        assert bullish[0].pattern_type == "consecutive_bullish_1d"
        assert bullish[0].severity >= 3
        assert "BTC" in bullish[0].title

    @pytest.mark.asyncio
    async def test_detect_bearish_streak(self, detector: ConsecutiveCandleDetector) -> None:
        """连续 4 根阴线应被检测到。"""
        closes = [100.0, 97.0, 95.0, 92.0]
        opens = [101.0, 98.0, 96.0, 93.0]  # open > close = 阴线
        ohlcv = _make_ohlcv(closes, opens=opens)
        patterns = await detector.detect("ETH/USDT", ohlcv, "4h")

        bearish = [p for p in patterns if p.direction == "bearish"]
        assert len(bearish) == 1
        assert bearish[0].pattern_type == "consecutive_bearish_4h"

    @pytest.mark.asyncio
    async def test_no_pattern_when_below_threshold(
        self, detector: ConsecutiveCandleDetector,
    ) -> None:
        """连续 2 根阳线（低于阈值 3）不应被检测到。"""
        closes = [100.0, 102.0, 99.0, 101.0]
        opens = [99.0, 101.0, 100.0, 100.0]
        ohlcv = _make_ohlcv(closes, opens=opens)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_insufficient_data(self, detector: ConsecutiveCandleDetector) -> None:
        """数据不足时不应返回模式。"""
        closes = [100.0, 102.0]
        ohlcv = _make_ohlcv(closes)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")
        assert len(patterns) == 0


class TestIndicatorSignalDetector:
    """测试技术指标信号检测器。"""

    @pytest.fixture
    def detector(self) -> IndicatorSignalDetector:
        return IndicatorSignalDetector(rsi_period=14, rsi_overbought=70.0, rsi_oversold=30.0)

    @pytest.mark.asyncio
    async def test_rsi_overbought(self, detector: IndicatorSignalDetector) -> None:
        """RSI 进入超买区应返回 bearish 信号。"""
        closes = [100.0 + i * 3 for i in range(20)]
        ohlcv = _make_ohlcv(closes)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")

        overbought = [p for p in patterns if "rsi_overbought" in p.pattern_type]
        assert len(overbought) >= 1
        assert overbought[0].direction == "bearish"

    @pytest.mark.asyncio
    async def test_rsi_oversold(self, detector: IndicatorSignalDetector) -> None:
        """RSI 进入超卖区应返回 bullish 信号。"""
        closes = [100.0 - i * 3 for i in range(20)]
        ohlcv = _make_ohlcv(closes)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")

        oversold = [p for p in patterns if "rsi_oversold" in p.pattern_type]
        assert len(oversold) >= 1
        assert oversold[0].direction == "bullish"

    def test_calc_rsi(self) -> None:
        """RSI 计算逻辑验证。"""
        detector = IndicatorSignalDetector()
        # 持续上涨 → RSI = 100
        closes = [100.0 + i for i in range(15)]
        rsi = detector._calc_rsi(closes, period=14)
        assert rsi == 100.0

        # 持续下跌 → RSI = 0
        closes = [100.0 - i for i in range(15)]
        rsi = detector._calc_rsi(closes, period=14)
        assert rsi == 0.0

        # 数据不足
        closes = [100.0, 101.0]
        rsi = detector._calc_rsi(closes, period=14)
        assert rsi is None

    def test_calc_macd_basic(self) -> None:
        """MACD 计算应返回等长列表。"""
        detector = IndicatorSignalDetector()
        closes = [100.0 + i * 0.5 for i in range(50)]
        macd, signal = detector._calc_macd(closes)
        assert macd is not None
        assert signal is not None
        assert len(macd) == len(signal)
        assert len(macd) > 0

    def test_calc_macd_insufficient_data(self) -> None:
        """数据不足时 MACD 应返回 None。"""
        detector = IndicatorSignalDetector()
        closes = [100.0] * 30  # 少于 slow(26) + signal(9) = 35
        macd, signal = detector._calc_macd(closes)
        assert macd is None
        assert signal is None

    def test_macd_crossover_detection(self) -> None:
        """验证 MACD 交叉检测逻辑。"""
        detector = IndicatorSignalDetector()

        # 构造数据：先跌后涨，使 MACD 产生金叉
        closes = list(range(100, 50, -1)) + list(range(50, 80))
        macd, signal = detector._calc_macd(closes)

        assert macd is not None
        assert signal is not None

        # 验证存在至少一个金叉
        golden_found = False
        for i in range(1, len(macd)):
            if signal[i - 1] != 0.0 and signal[i] != 0.0:
                if macd[i - 1] <= signal[i - 1] and macd[i] > signal[i]:
                    golden_found = True
                    break
        assert golden_found, "应在数据中检测到 MACD 金叉"

    @pytest.mark.asyncio
    async def test_macd_golden_cross(self, detector: IndicatorSignalDetector) -> None:
        """MACD 金叉应被 detect() 返回。"""
        # 长横盘 → 急跌 → 快速反弹，MACD 在尾部产生金叉
        closes = [100.0] * 60 + [100.0 - i * 3.0 for i in range(5)] + [85.0 + i * 4.0 for i in range(15)]
        ohlcv = _make_ohlcv(closes)
        patterns = await detector.detect("ETH/USDT", ohlcv, "1d")

        golden = [p for p in patterns if "macd_golden_cross" in p.pattern_type]
        assert len(golden) >= 1
        assert golden[0].direction == "bullish"


class TestVolumeSpikeDetector:
    """测试成交量异动检测器。"""

    @pytest.fixture
    def detector(self) -> VolumeSpikeDetector:
        return VolumeSpikeDetector(period=10, multiplier=2.0)

    @pytest.mark.asyncio
    async def test_volume_spike_bullish(self, detector: VolumeSpikeDetector) -> None:
        """放量上涨应被检测到。"""
        volumes = [1000.0] * 10 + [3000.0]
        closes = [100.0 + i * 0.5 for i in range(11)]
        ohlcv = _make_ohlcv(closes, volumes=volumes)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")

        spikes = [p for p in patterns if "volume_spike" in p.pattern_type]
        assert len(spikes) >= 1
        assert spikes[0].direction == "bullish"

    @pytest.mark.asyncio
    async def test_volume_spike_bearish(self, detector: VolumeSpikeDetector) -> None:
        """放量下跌应被检测到。"""
        volumes = [1000.0] * 10 + [3000.0]
        closes = [100.0 - i * 0.5 for i in range(11)]
        ohlcv = _make_ohlcv(closes, volumes=volumes)
        patterns = await detector.detect("ETH/USDT", ohlcv, "1d")

        spikes = [p for p in patterns if "volume_spike" in p.pattern_type]
        assert len(spikes) >= 1
        assert spikes[0].direction == "bearish"

    @pytest.mark.asyncio
    async def test_no_spike_when_normal_volume(self, detector: VolumeSpikeDetector) -> None:
        """正常成交量不应触发检测。"""
        volumes = [1000.0] * 12
        closes = [100.0] * 12
        ohlcv = _make_ohlcv(closes, volumes=volumes)
        patterns = await detector.detect("BTC/USDT", ohlcv, "1d")
        assert len(patterns) == 0
