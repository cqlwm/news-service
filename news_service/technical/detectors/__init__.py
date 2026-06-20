from __future__ import annotations

from .base import BaseDetector
from .consecutive_candle import ConsecutiveCandleDetector
from .indicator_signal import IndicatorSignalDetector
from .volume_spike import VolumeSpikeDetector

__all__ = [
    "BaseDetector",
    "ConsecutiveCandleDetector",
    "IndicatorSignalDetector",
    "VolumeSpikeDetector",
]
