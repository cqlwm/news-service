from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class DetectedPattern:
    """单个检测到的技术模式。"""
    symbol: str
    pattern_type: str
    direction: Literal["bullish", "bearish"]
    title: str
    description: str
    severity: int  # 1-5，5 为最重要
    metadata: dict[str, str | int | float] = field(default_factory=dict)
    detected_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.detected_at is None:
            from datetime import timezone
            self.detected_at = datetime.now(timezone.utc)


@dataclass
class TechnicalConfig:
    """技术模块运行时配置。"""
    symbols: list[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT"])
    timeframes: list[str] = field(default_factory=lambda: ["1d", "4h"])
    top_n: int = 20
    min_consecutive: int = 3
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_period: int = 20
    volume_multiplier: float = 2.0
    interval_seconds: int = 300

    # 排名参数
    min_volume_usdt: float = 1_000_000  # 最低 24h 成交量（USDT）
    min_price_change_pct: float = 1.0   # 最低 24h 涨跌幅绝对值（%）
