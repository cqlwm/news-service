from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..type_wrapper.ccxt_wrapper import (
    create_exchange,
    fetch_ohlcv,
    fetch_tickers,
    close_exchange,
    ohlcv_to_dataframe,
)

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """行情数据提供者。

    封装 CCXT 的 OHLCV 和 Ticker 数据获取逻辑，
    提供项目代码可直接调用的类型安全接口。
    """

    def __init__(self) -> None:
        self._exchange = create_exchange("binance")
        self._initialized = True

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
    ) -> list[dict[str, float | int | str]]:
        """获取 OHLCV 数据并转换为字典列表。

        Args:
            symbol: 交易对，如 "BTC/USDT"（CCXT 格式，带斜杠）。
            timeframe: 时间周期。
            limit: K 线数量。

        Returns:
            每项包含 timestamp, datetime_utc, open, high, low, close, volume 的列表。
        """
        raw = await fetch_ohlcv(self._exchange, symbol, timeframe, limit=limit)
        return ohlcv_to_dataframe(raw)

    async def get_top_symbols_ohlcv(
        self,
        symbols: list[str],
        timeframe: str = "1d",
        limit: int = 100,
    ) -> dict[str, list[dict[str, float | int | str]]]:
        """批量获取多个交易对的 OHLCV 数据。

        Args:
            symbols: 交易对列表（CCXT 格式，如 "BTC/USDT"）。
            timeframe: 时间周期。
            limit: K 线数量。

        Returns:
            symbol -> OHLCV 列表的字典。
        """
        result: dict[str, list[dict[str, float | int | str]]] = {}
        for symbol in symbols:
            ohlcv = await self.get_ohlcv(symbol, timeframe, limit)
            if ohlcv:
                result[symbol] = ohlcv
        return result

    async def close(self) -> None:
        if self._initialized:
            await close_exchange(self._exchange)
            self._initialized = False


def convert_symbol_to_ccxt(symbol: str) -> str:
    """将币安格式的交易对转换为 CCXT 格式。

    "BTCUSDT" -> "BTC/USDT"
    """
    if "/" in symbol:
        return symbol
    if symbol.endswith("USDT"):
        base = symbol[:-4]
        return f"{base}/USDT"
    return symbol


def convert_symbol_from_ccxt(symbol: str) -> str:
    """将 CCXT 格式的交易对转换为币安格式。

    "BTC/USDT" -> "BTCUSDT"
    """
    return symbol.replace("/", "")
