from __future__ import annotations

import logging
from statistics import mean

from ..models import DetectedPattern
from .base import BaseDetector

logger = logging.getLogger(__name__)


class VolumeSpikeDetector(BaseDetector):
    """成交量异动检测器。

    检测成交量相对于 N 周期均值的显著放大或缩小。
    """

    def __init__(self, period: int = 20, multiplier: float = 2.0) -> None:
        self.period = period
        self.multiplier = multiplier

    @property
    def name(self) -> str:
        return "volume_spike"

    async def detect(
        self,
        symbol: str,
        ohlcv: list[dict[str, float | int | str]],
        timeframe: str,
    ) -> list[DetectedPattern]:
        if len(ohlcv) < self.period + 1:
            return []

        patterns: list[DetectedPattern] = []

        volumes = [float(c["volume"]) for c in ohlcv]
        closes = [float(c["close"]) for c in ohlcv]
        latest_volume = volumes[-1]
        avg_volume = mean(volumes[-(self.period + 1):-1])  # 前 N 根均值（不含最新）

        if avg_volume == 0:
            return []

        volume_ratio = latest_volume / avg_volume
        latest_change = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0.0

        # 放量检测
        if volume_ratio >= self.multiplier:
            direction: str = "bullish" if latest_change > 0 else "bearish"
            patterns.append(self._make_pattern(
                symbol, timeframe, "spike", volume_ratio, latest_change, direction,
            ))

        # 缩量检测（成交量小于均值的 1/multiplier）
        if volume_ratio <= 1.0 / self.multiplier:
            direction = "bullish" if latest_change > 0 else "bearish"
            patterns.append(self._make_pattern(
                symbol, timeframe, "shrink", volume_ratio, latest_change, direction,
            ))

        return patterns

    def _make_pattern(
        self,
        symbol: str,
        timeframe: str,
        spike_type: str,
        volume_ratio: float,
        price_change: float,
        direction: str,
    ) -> DetectedPattern:
        base = symbol.replace("/USDT", "")
        tf_label = {"1d": "日线", "4h": "4小时", "1h": "1小时"}.get(timeframe, timeframe)

        if spike_type == "spike":
            title = f"{base} {tf_label} 成交量放量 {volume_ratio:.1f} 倍"
            description = (
                f"{base} {tf_label} 成交量达到近 {self.period} 周期均值的 "
                f"{volume_ratio:.1f} 倍（阈值 {self.multiplier} 倍），"
                f"价格变动 {price_change:+.2f}%"
            )
            severity = 3 if volume_ratio >= self.multiplier * 2 else 2
        else:
            title = f"{base} {tf_label} 成交量缩量至 {volume_ratio:.2f} 倍"
            description = (
                f"{base} {tf_label} 成交量仅为近 {self.period} 周期均值的 "
                f"{volume_ratio:.2f} 倍，市场交投萎缩，价格变动 {price_change:+.2f}%"
            )
            severity = 2

        return DetectedPattern(
            symbol=symbol,
            pattern_type=f"volume_{spike_type}_{timeframe}",
            direction=direction,  # type: ignore[arg-type]
            title=title,
            description=description,
            severity=severity,
            metadata={
                "volume_ratio": f"{volume_ratio:.2f}",
                "price_change_pct": f"{price_change:.2f}",
                "timeframe": timeframe,
            },
        )
