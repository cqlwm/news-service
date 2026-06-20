from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

TICKER_24HR_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr"


@dataclass
class RankedSymbol:
    """排名后的交易对信息。"""
    symbol: str
    volume_usdt: float
    price_change_pct: float
    score: float


class SymbolRanker:
    """动态交易对排名器。

    从币安 U 本位永续合约市场获取所有 USDT 交易对的 24 小时数据，
    按成交量 × 波动率综合评分排序，选取 Top N 作为监控标的。
    """

    def __init__(
        self,
        top_n: int = 20,
        min_volume_usdt: float = 1_000_000,
        min_price_change_pct: float = 1.0,
    ) -> None:
        self.top_n = top_n
        self.min_volume_usdt = min_volume_usdt
        self.min_price_change_pct = min_price_change_pct
        self._client = httpx.AsyncClient(timeout=15.0)

    async def rank(self) -> list[RankedSymbol]:
        """执行排名，返回 Top N 交易对列表。"""
        try:
            response = await self._client.get(TICKER_24HR_URL)
            response.raise_for_status()
            tickers: list[dict] = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch 24hr tickers: {e}")
            return []

        candidates: list[RankedSymbol] = []
        for t in tickers:
            symbol: str = t.get("symbol", "")
            # 只保留 USDT 永续合约
            if not symbol.endswith("USDT"):
                continue

            quote_volume = float(t.get("quoteVolume", 0))
            price_change_pct = abs(float(t.get("priceChangePercent", 0)))

            # 过滤低成交量、低波动率
            if quote_volume < self.min_volume_usdt:
                continue
            if price_change_pct < self.min_price_change_pct:
                continue

            # 综合评分 = 成交量(USDT) × 波动率(%)
            score = quote_volume * price_change_pct

            candidates.append(RankedSymbol(
                symbol=symbol,
                volume_usdt=quote_volume,
                price_change_pct=price_change_pct,
                score=score,
            ))

        # 按评分降序排列，取 Top N
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:self.top_n]

    async def close(self) -> None:
        await self._client.aclose()
