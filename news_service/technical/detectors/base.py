from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import DetectedPattern


class BaseDetector(ABC):
    """技术模式检测器基类。

    每个检测器负责检测一种特定类型的技术模式，
    接收 OHLCV 数据，返回检测到的模式列表。
    """

    @abstractmethod
    async def detect(
        self,
        symbol: str,
        ohlcv: list[dict[str, float | int | str]],
        timeframe: str,
    ) -> list[DetectedPattern]:
        """对单个交易对执行模式检测。

        Args:
            symbol: 交易对（CCXT 格式，如 "BTC/USDT"）。
            ohlcv: OHLCV 数据列表。
            timeframe: 时间周期。

        Returns:
            检测到的模式列表。
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """检测器名称，用于日志和 API 展示。"""
        ...
