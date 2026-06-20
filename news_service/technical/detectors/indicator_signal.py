from __future__ import annotations

import logging
from typing import Literal

from ..models import DetectedPattern
from .base import BaseDetector

logger = logging.getLogger(__name__)


class IndicatorSignalDetector(BaseDetector):
    """技术指标信号检测器。

    检测 RSI 超买/超卖、MACD 金叉/死叉等常见技术指标信号。
    """

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
    ) -> None:
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    @property
    def name(self) -> str:
        return "indicator_signal"

    async def detect(
        self,
        symbol: str,
        ohlcv: list[dict[str, float | int | str]],
        timeframe: str,
    ) -> list[DetectedPattern]:
        if len(ohlcv) < self.rsi_period + 1:
            return []

        patterns: list[DetectedPattern] = []

        # RSI 信号
        closes = [float(c["close"]) for c in ohlcv]
        rsi = self._calc_rsi(closes)
        if rsi is not None:
            if rsi >= self.rsi_overbought:
                patterns.append(self._make_rsi_pattern(
                    symbol, timeframe, rsi, "overbought",
                ))
            elif rsi <= self.rsi_oversold:
                patterns.append(self._make_rsi_pattern(
                    symbol, timeframe, rsi, "oversold",
                ))

        # MACD 信号
        macd_line, signal_line = self._calc_macd(closes)
        if macd_line is not None and signal_line is not None and len(macd_line) >= 2 and len(signal_line) >= 2:
            # 扫描最近 10 根 K 线，检测 MACD 交叉
            scan_start = max(1, len(macd_line) - 20)
            for i in range(scan_start, len(macd_line)):
                if signal_line[i - 1] != 0.0 and signal_line[i] != 0.0:
                    # 金叉：MACD 上穿 Signal
                    if macd_line[i - 1] <= signal_line[i - 1] and macd_line[i] > signal_line[i]:
                        patterns.append(self._make_macd_pattern(
                            symbol, timeframe, "golden_cross",
                        ))
                        break
                    # 死叉：MACD 下穿 Signal
                    elif macd_line[i - 1] >= signal_line[i - 1] and macd_line[i] < signal_line[i]:
                        patterns.append(self._make_macd_pattern(
                            symbol, timeframe, "death_cross",
                        ))
                        break

        return patterns

    def _make_rsi_pattern(
        self,
        symbol: str,
        timeframe: str,
        rsi: float,
        signal_type: Literal["overbought", "oversold"],
    ) -> DetectedPattern:
        base = symbol.replace("/USDT", "")
        tf_label = {"1d": "日线", "4h": "4小时", "1h": "1小时"}.get(timeframe, timeframe)

        if signal_type == "overbought":
            direction: Literal["bullish", "bearish"] = "bearish"
            title = f"{base} {tf_label} RSI 进入超买区 ({rsi:.1f})"
            description = (
                f"{base} {tf_label} RSI 达到 {rsi:.1f}，"
                f"进入超买区（阈值 {self.rsi_overbought}），短期回调风险增加"
            )
            severity = 3
        else:
            direction = "bullish"
            title = f"{base} {tf_label} RSI 进入超卖区 ({rsi:.1f})"
            description = (
                f"{base} {tf_label} RSI 跌至 {rsi:.1f}，"
                f"进入超卖区（阈值 {self.rsi_oversold}），短期反弹机会增加"
            )
            severity = 3

        return DetectedPattern(
            symbol=symbol,
            pattern_type=f"rsi_{signal_type}_{timeframe}",
            direction=direction,
            title=title,
            description=description,
            severity=severity,
            metadata={"rsi": f"{rsi:.1f}", "timeframe": timeframe},
        )

    def _make_macd_pattern(
        self,
        symbol: str,
        timeframe: str,
        cross_type: Literal["golden_cross", "death_cross"],
    ) -> DetectedPattern:
        base = symbol.replace("/USDT", "")
        tf_label = {"1d": "日线", "4h": "4小时", "1h": "1小时"}.get(timeframe, timeframe)

        if cross_type == "golden_cross":
            direction: Literal["bullish", "bearish"] = "bullish"
            title = f"{base} {tf_label} MACD 金叉"
            description = f"{base} {tf_label} MACD 上穿信号线，形成金叉，趋势转多信号"
            severity = 4
        else:
            direction = "bearish"
            title = f"{base} {tf_label} MACD 死叉"
            description = f"{base} {tf_label} MACD 下穿信号线，形成死叉，趋势转空信号"
            severity = 4

        return DetectedPattern(
            symbol=symbol,
            pattern_type=f"macd_{cross_type}_{timeframe}",
            direction=direction,
            title=title,
            description=description,
            severity=severity,
            metadata={"cross_type": cross_type, "timeframe": timeframe},
        )

    @staticmethod
    def _calc_rsi(closes: list[float], period: int = 14) -> float | None:
        """计算 RSI 指标。"""
        if len(closes) < period + 1:
            return None

        deltas: list[float] = []
        for i in range(1, len(closes)):
            deltas.append(closes[i] - closes[i - 1])

        recent_deltas = deltas[-period:]
        gains = sum(d for d in recent_deltas if d > 0)
        losses = sum(-d for d in recent_deltas if d < 0)

        if losses == 0:
            return 100.0
        if gains == 0:
            return 0.0

        avg_gain = gains / period
        avg_loss = losses / period
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _calc_macd(
        closes: list[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple[list[float] | None, list[float] | None]:
        """计算 MACD 线和信号线。

        返回的 MACD 线和信号线长度相同，信号线前 (signal-1) 个值为 0.0。
        """
        if len(closes) < slow + signal:
            return None, None

        def ema(data: list[float], period: int) -> list[float]:
            result: list[float] = []
            multiplier = 2.0 / (period + 1)
            ema_val = sum(data[:period]) / period
            result.append(ema_val)
            for price in data[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
                result.append(ema_val)
            return result

        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)

        # 对齐：fast EMA 比 slow EMA 多 (slow - fast) 个值，截取尾部对齐
        offset = len(ema_fast) - len(ema_slow)
        ema_fast_aligned = ema_fast[offset:]

        # MACD line = fast EMA - slow EMA
        macd_line: list[float] = []
        for f, s in zip(ema_fast_aligned, ema_slow):
            macd_line.append(f - s)

        # Signal line = EMA of MACD line，补齐到与 MACD line 等长
        raw_signal = ema(macd_line, signal)
        pad_len = len(macd_line) - len(raw_signal)
        signal_line: list[float] = [0.0] * pad_len + raw_signal

        return macd_line, signal_line
