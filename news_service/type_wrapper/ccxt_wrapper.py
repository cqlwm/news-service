"""CCXT 第三方库封装模块。

本模块提供全类型注解的 CCXT API 封装，项目代码不直接调用 ccxt。
本模块在 pyright strict 模式下被排除检查（见 pyproject.toml）。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ccxt.pro as ccxt_pro

logger = logging.getLogger(__name__)

# 公开类型别名
OHLCV: type = list[list[float | int]]
"""OHLCV 数据结构: [[timestamp, open, high, low, close, volume], ...]"""

TickerData: type = dict[str, Any]
"""Ticker 数据结构。"""


def create_exchange(
    exchange_id: str = "binance",
    sandbox: bool = False,
    config: dict[str, str | int | float | bool] | None = None,
) -> ccxt_pro.Exchange:
    """创建并返回交易所实例。

    Args:
        exchange_id: 交易所 ID，默认 binance。
        sandbox: 是否使用沙箱环境。
        config: 额外配置项。

    Returns:
        已初始化的交易所实例。
    """
    merged: dict[str, Any] = {"enableRateLimit": True}
    if sandbox:
        merged["sandbox"] = True
    if config:
        merged.update(config)

    exchange_class = getattr(ccxt_pro, exchange_id)
    exchange: ccxt_pro.Exchange = exchange_class(merged)
    return exchange


async def fetch_ohlcv(
    exchange: ccxt_pro.Exchange,
    symbol: str,
    timeframe: str = "1d",
    limit: int = 100,
) -> list[list[float | int]]:
    """获取 OHLCV 数据。

    Args:
        exchange: 交易所实例。
        symbol: 交易对，如 "BTC/USDT"。
        timeframe: 时间周期，如 "1d", "4h", "1h"。
        limit: 返回的 K 线数量。

    Returns:
        OHLCV 数据列表，每项为 [timestamp, open, high, low, close, volume]。
    """
    try:
        raw: list[list] = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        result: list[list[float | int]] = []
        for item in raw:
            result.append([float(v) if isinstance(v, (int, float)) else 0.0 for v in item])
        return result
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV for {symbol} ({timeframe}): {e}")
        return []


async def fetch_tickers(
    exchange: ccxt_pro.Exchange,
    symbols: list[str] | None = None,
) -> dict[str, TickerData]:
    """获取多个交易对的 24 小时 Ticker 数据。

    Args:
        exchange: 交易所实例。
        symbols: 交易对列表，为 None 时获取所有。

    Returns:
        symbol -> ticker 数据的字典。
    """
    try:
        raw: dict[str, Any] = await exchange.fetch_tickers(symbols)
        return raw
    except Exception as e:
        logger.error(f"Failed to fetch tickers: {e}")
        return {}


async def close_exchange(exchange: ccxt_pro.Exchange) -> None:
    """关闭交易所连接。"""
    try:
        await exchange.close()
    except Exception as e:
        logger.warning(f"Error closing exchange: {e}")


def ohlcv_to_dataframe(
    ohlcv: list[list[float | int]],
) -> list[dict[str, float | int | str]]:
    """将 OHLCV 原始数据转换为字典列表，便于后续处理。

    返回的每项包含: timestamp, datetime_utc, open, high, low, close, volume。
    """
    result: list[dict[str, float | int | str]] = []
    for item in ohlcv:
        ts = int(item[0])
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        result.append({
            "timestamp": ts,
            "datetime_utc": dt.isoformat(),
            "open": item[1],
            "high": item[2],
            "low": item[3],
            "close": item[4],
            "volume": item[5],
        })
    return result
