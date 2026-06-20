from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..service import NewsService
from .deps import get_service

router = APIRouter()


@router.post("/run")
async def trigger_technical_analysis(
    service: NewsService = Depends(get_service),
) -> dict:
    """手动触发一轮技术面检测。"""
    new_ids = await service.fetch_technical_news()
    return {
        "message": f"Technical analysis complete, {len(new_ids)} new items",
        "new_ids": new_ids,
    }


@router.get("/detectors")
async def list_detectors(
    service: NewsService = Depends(get_service),
) -> list[dict]:
    """查看当前启用的技术检测器列表。"""
    return [
        {
            "name": d.name,
            "type": d.__class__.__name__,
        }
        for d in service.technical_engine.detectors
    ]


@router.get("/config")
async def get_technical_config(
    service: NewsService = Depends(get_service),
) -> dict:
    """查看技术模块配置。"""
    cfg = service.technical_engine.config
    return {
        "top_n": cfg.top_n,
        "timeframes": cfg.timeframes,
        "min_consecutive": cfg.min_consecutive,
        "rsi_period": cfg.rsi_period,
        "rsi_overbought": cfg.rsi_overbought,
        "rsi_oversold": cfg.rsi_oversold,
        "volume_period": cfg.volume_period,
        "volume_multiplier": cfg.volume_multiplier,
        "min_volume_usdt": cfg.min_volume_usdt,
        "min_price_change_pct": cfg.min_price_change_pct,
        "interval_seconds": cfg.interval_seconds,
    }


@router.put("/config")
async def update_technical_config(
    config: dict,
    service: NewsService = Depends(get_service),
) -> dict:
    """更新技术模块配置。"""
    from ..technical.models import TechnicalConfig

    cfg = service.technical_engine.config

    if "top_n" in config:
        cfg.top_n = int(config["top_n"])
    if "timeframes" in config:
        cfg.timeframes = list(config["timeframes"])
    if "min_consecutive" in config:
        cfg.min_consecutive = int(config["min_consecutive"])
    if "rsi_period" in config:
        cfg.rsi_period = int(config["rsi_period"])
    if "rsi_overbought" in config:
        cfg.rsi_overbought = float(config["rsi_overbought"])
    if "rsi_oversold" in config:
        cfg.rsi_oversold = float(config["rsi_oversold"])
    if "volume_period" in config:
        cfg.volume_period = int(config["volume_period"])
    if "volume_multiplier" in config:
        cfg.volume_multiplier = float(config["volume_multiplier"])
    if "min_volume_usdt" in config:
        cfg.min_volume_usdt = float(config["min_volume_usdt"])
    if "min_price_change_pct" in config:
        cfg.min_price_change_pct = float(config["min_price_change_pct"])
    if "interval_seconds" in config:
        cfg.interval_seconds = int(config["interval_seconds"])

    service.technical_engine.update_config(cfg)
    return {"message": "Technical config updated", "config": config}
