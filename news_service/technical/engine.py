from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ..models import NewsDetail
from .detectors import BaseDetector, ConsecutiveCandleDetector, IndicatorSignalDetector, VolumeSpikeDetector
from .market_data import MarketDataProvider, convert_symbol_to_ccxt, convert_symbol_from_ccxt
from .models import TechnicalConfig, DetectedPattern
from .symbol_ranker import SymbolRanker

logger = logging.getLogger(__name__)


class TechnicalEngine:
    """技术面检测引擎。

    协调行情获取、动态币种排名、模式检测和新闻生成。
    每次 run() 执行一轮完整的技术面检测流程。
    """

    def __init__(
        self,
        config: TechnicalConfig | None = None,
    ) -> None:
        self.config = config or TechnicalConfig()
        self.ranker = SymbolRanker(
            top_n=self.config.top_n,
            min_volume_usdt=self.config.min_volume_usdt,
            min_price_change_pct=self.config.min_price_change_pct,
        )
        self.market_data = MarketDataProvider()

        # 注册默认检测器
        self.detectors: list[BaseDetector] = [
            ConsecutiveCandleDetector(min_consecutive=self.config.min_consecutive),
            IndicatorSignalDetector(
                rsi_period=self.config.rsi_period,
                rsi_overbought=self.config.rsi_overbought,
                rsi_oversold=self.config.rsi_oversold,
            ),
            VolumeSpikeDetector(
                period=self.config.volume_period,
                multiplier=self.config.volume_multiplier,
            ),
        ]

    async def run(self) -> list[NewsDetail]:
        """执行一轮完整的技术面检测，返回技术新闻列表。"""
        logger.info("TechnicalEngine: starting detection cycle")

        # 1. 动态排名获取监控标的
        ranked_symbols = await self.ranker.rank()
        if not ranked_symbols:
            logger.warning("TechnicalEngine: no symbols ranked, using configured symbols")
            ccxt_symbols = [convert_symbol_to_ccxt(s) for s in self.config.symbols]
        else:
            ccxt_symbols = [convert_symbol_to_ccxt(rs.symbol) for rs in ranked_symbols]

        logger.info(f"TechnicalEngine: monitoring {len(ccxt_symbols)} symbols")

        # 2. 获取各时间周期的 OHLCV 数据
        all_patterns: list[DetectedPattern] = []
        for timeframe in self.config.timeframes:
            ohlcv_map = await self.market_data.get_top_symbols_ohlcv(
                ccxt_symbols, timeframe=timeframe, limit=100,
            )

            # 3. 运行所有检测器
            for symbol, ohlcv in ohlcv_map.items():
                for detector in self.detectors:
                    try:
                        patterns = await detector.detect(symbol, ohlcv, timeframe)
                        all_patterns.extend(patterns)
                    except Exception as e:
                        logger.error(
                            "TechnicalEngine: detector %s failed for %s (%s): %s",
                            detector.name, symbol, timeframe, e,
                        )

        # 4. 去重：相同 symbol + pattern_type 只保留 severity 最高的
        unique_patterns = self._deduplicate(all_patterns)

        # 5. 按 severity 降序排列
        unique_patterns.sort(key=lambda p: p.severity, reverse=True)

        logger.info(
            "TechnicalEngine: detected %d patterns (unique: %d)",
            len(all_patterns), len(unique_patterns),
        )

        # 6. 转换为 NewsDetail
        return [self._to_news_detail(p) for p in unique_patterns]

    @staticmethod
    def _deduplicate(patterns: list[DetectedPattern]) -> list[DetectedPattern]:
        """去重：相同 symbol + pattern_type 只保留 severity 最高的。"""
        seen: dict[tuple[str, str], DetectedPattern] = {}
        for p in patterns:
            key = (p.symbol, p.pattern_type)
            if key not in seen or p.severity > seen[key].severity:
                seen[key] = p
        return list(seen.values())

    @staticmethod
    def _to_news_detail(pattern: DetectedPattern) -> NewsDetail:
        """将检测到的模式转换为 NewsDetail，复用现有流水线。"""
        base = pattern.symbol.replace("/USDT", "")
        now_iso = datetime.now(timezone.utc).isoformat()

        return NewsDetail(
            id=f"tech_{pattern.pattern_type}_{base}_{int(datetime.now(timezone.utc).timestamp())}",
            title=pattern.title,
            content=pattern.description,
            source="Technical Analysis",
            url="",
            published_at=now_iso,
            images=[],
        )

    def update_config(self, config: TechnicalConfig) -> None:
        """运行时更新配置。"""
        self.config = config
        self.ranker.top_n = config.top_n
        self.ranker.min_volume_usdt = config.min_volume_usdt
        self.ranker.min_price_change_pct = config.min_price_change_pct

        # 重建检测器
        self.detectors = [
            ConsecutiveCandleDetector(min_consecutive=config.min_consecutive),
            IndicatorSignalDetector(
                rsi_period=config.rsi_period,
                rsi_overbought=config.rsi_overbought,
                rsi_oversold=config.rsi_oversold,
            ),
            VolumeSpikeDetector(
                period=config.volume_period,
                multiplier=config.volume_multiplier,
            ),
        ]

    async def close(self) -> None:
        await self.ranker.close()
        await self.market_data.close()
