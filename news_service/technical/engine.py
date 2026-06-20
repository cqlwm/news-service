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

        # (symbol, timeframe) -> 最后一次分析时最后一根 K 线的时间戳（毫秒）
        self._last_candle_ts: dict[tuple[str, str], int] = {}

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
        """执行一轮完整的技术面检测，返回技术新闻列表。

        每个 symbol 在不同时间框架、不同检测器下的所有模式
        合并为一条技术新闻。
        """
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

            # 3. 逐 symbol 检查 K 线是否更新，跳过未变化的
            for symbol, ohlcv in ohlcv_map.items():
                if not ohlcv:
                    continue

                last_ts = int(ohlcv[-1]["timestamp"])  # type: ignore[arg-type]
                cache_key = (symbol, timeframe)
                cached_ts = self._last_candle_ts.get(cache_key)

                if cached_ts is not None and last_ts == cached_ts:
                    logger.debug(
                        "TechnicalEngine: %s %s no new candle (ts=%d), skipping",
                        symbol, timeframe, last_ts,
                    )
                    continue

                logger.info(
                    "TechnicalEngine: %s %s new candle detected (ts=%d), running detectors",
                    symbol, timeframe, last_ts,
                )

                # 4. 运行所有检测器
                for detector in self.detectors:
                    try:
                        patterns = await detector.detect(symbol, ohlcv, timeframe)
                        all_patterns.extend(patterns)
                    except Exception as e:
                        logger.error(
                            "TechnicalEngine: detector %s failed for %s (%s): %s",
                            detector.name, symbol, timeframe, e,
                        )

                # 5. 更新缓存时间戳
                self._last_candle_ts[cache_key] = last_ts

        # 6. 按 symbol 分组，每个 symbol 合并为一条新闻
        symbol_patterns: dict[str, list[DetectedPattern]] = {}
        for p in all_patterns:
            symbol_patterns.setdefault(p.symbol, []).append(p)

        logger.info(
            "TechnicalEngine: detected %d patterns across %d symbols",
            len(all_patterns), len(symbol_patterns),
        )

        # 7. 每个 symbol 去重后合并为一条 NewsDetail
        news_list: list[NewsDetail] = []
        for symbol, patterns in symbol_patterns.items():
            unique = self._deduplicate(patterns)
            news_list.append(self._merge_to_news_detail(symbol, unique))

        # 8. 按最高 severity 降序排列
        news_list.sort(
            key=lambda n: max(
                (p.severity for p in symbol_patterns.get(
                    convert_symbol_to_ccxt(n.title.split(" ")[0]), []
                )),
                default=0,
            ),
            reverse=True,
        )

        return news_list

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
    def _merge_to_news_detail(symbol: str, patterns: list[DetectedPattern]) -> NewsDetail:
        """将同一个 symbol 的所有模式合并为一条 NewsDetail。"""
        base = symbol.replace("/USDT", "")
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        now_ts = int(now.timestamp())

        # 按 severity 降序排列
        sorted_patterns = sorted(patterns, key=lambda p: p.severity, reverse=True)

        # 标题：取 severity 最高的模式标题
        primary = sorted_patterns[0]
        title = primary.title

        # 内容：组合所有模式的描述
        lines: list[str] = []
        for i, p in enumerate(sorted_patterns, 1):
            lines.append(f"{i}. [{p.direction.upper()}] {p.title}")
            lines.append(f"   {p.description}")
        content = "\n".join(lines)

        return NewsDetail(
            id=f"tech_{base}_{now_ts}",
            title=title,
            content=content,
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
