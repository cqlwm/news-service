from __future__ import annotations

import logging
from typing import Literal

from ..models import DetectedPattern
from .base import BaseDetector

logger = logging.getLogger(__name__)


class ConsecutiveCandleDetector(BaseDetector):
    """连续涨跌检测器。

    检测交易对是否出现连续 N 根阳线（上涨）或阴线（下跌）。
    支持多时间周期（1d 连续涨跌、4h 连续涨跌）。
    """

    def __init__(self, min_consecutive: int = 3) -> None:
        self.min_consecutive = min_consecutive

    @property
    def name(self) -> str:
        return "consecutive_candle"

    async def detect(
        self,
        symbol: str,
        ohlcv: list[dict[str, float | int | str]],
        timeframe: str,
    ) -> list[DetectedPattern]:
        if len(ohlcv) < self.min_consecutive:
            return []

        patterns: list[DetectedPattern] = []

        # 检测连续上涨
        bull_streak = self._count_consecutive(ohlcv, "bullish")
        if bull_streak >= self.min_consecutive:
            close = float(ohlcv[-1]["close"])
            change_pct = self._streak_change_pct(ohlcv, bull_streak)
            patterns.append(DetectedPattern(
                symbol=symbol,
                pattern_type=f"consecutive_bullish_{timeframe}",
                direction="bullish",
                title=self._format_title(symbol, bull_streak, "上涨", timeframe),
                description=self._format_description(
                    symbol, bull_streak, "上涨", timeframe, close, change_pct,
                ),
                severity=self._calc_severity(bull_streak),
                metadata={
                    "streak": bull_streak,
                    "close_price": str(close),
                    "change_pct": f"{change_pct:.2f}",
                    "timeframe": timeframe,
                },
            ))

        # 检测连续下跌
        bear_streak = self._count_consecutive(ohlcv, "bearish")
        if bear_streak >= self.min_consecutive:
            close = float(ohlcv[-1]["close"])
            change_pct = self._streak_change_pct(ohlcv, bear_streak)
            patterns.append(DetectedPattern(
                symbol=symbol,
                pattern_type=f"consecutive_bearish_{timeframe}",
                direction="bearish",
                title=self._format_title(symbol, bear_streak, "下跌", timeframe),
                description=self._format_description(
                    symbol, bear_streak, "下跌", timeframe, close, change_pct,
                ),
                severity=self._calc_severity(bear_streak),
                metadata={
                    "streak": bear_streak,
                    "close_price": str(close),
                    "change_pct": f"{change_pct:.2f}",
                    "timeframe": timeframe,
                },
            ))

        return patterns

    @staticmethod
    def _count_consecutive(
        ohlcv: list[dict[str, float | int | str]],
        direction: Literal["bullish", "bearish"],
    ) -> int:
        """从最新数据向前统计连续阳线/阴线数量。"""
        count = 0
        for candle in reversed(ohlcv):
            close = float(candle["close"])
            open_ = float(candle["open"])
            if direction == "bullish" and close > open_:
                count += 1
            elif direction == "bearish" and close < open_:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _streak_change_pct(
        ohlcv: list[dict[str, float | int | str]],
        streak: int,
    ) -> float:
        """计算连续涨跌区间的累计涨跌幅。"""
        relevant = ohlcv[-streak:]
        if len(relevant) < 2:
            return 0.0
        start_open = float(relevant[0]["open"])
        end_close = float(relevant[-1]["close"])
        if start_open == 0:
            return 0.0
        return (end_close - start_open) / start_open * 100

    @staticmethod
    def _format_title(symbol: str, streak: int, direction: str, timeframe: str) -> str:
        base = symbol.replace("/USDT", "")
        tf_label = {"1d": "日线", "4h": "4小时", "1h": "1小时"}.get(timeframe, timeframe)
        return f"{base} {tf_label}连续{streak}根{direction}"

    @staticmethod
    def _format_description(
        symbol: str, streak: int, direction: str, timeframe: str,
        close: float, change_pct: float,
    ) -> str:
        base = symbol.replace("/USDT", "")
        tf_label = {"1d": "日线", "4h": "4小时", "1h": "1小时"}.get(timeframe, timeframe)
        return (
            f"{base} {tf_label}连续{streak}根{direction}，"
            f"最新价格 {close:.2f} USDT，区间累计涨跌幅 {change_pct:.2f}%"
        )

    @staticmethod
    def _calc_severity(streak: int) -> int:
        if streak >= 7:
            return 5
        if streak >= 5:
            return 4
        if streak >= 3:
            return 3
        return 1
