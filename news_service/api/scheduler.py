from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..service import Scheduler
from .deps import get_scheduler

router = APIRouter()


@router.post("/start")
async def start_scheduler(
    scheduler: Scheduler = Depends(get_scheduler),
) -> dict:
    """启动后台定时采集。"""
    if scheduler.is_running:
        return {"message": "Scheduler already running", "running": True}
    scheduler.start()
    return {"message": "Scheduler started", "running": True}


@router.post("/stop")
async def stop_scheduler(
    scheduler: Scheduler = Depends(get_scheduler),
) -> dict:
    """停止后台定时采集。"""
    if not scheduler.is_running:
        return {"message": "Scheduler not running", "running": False}
    scheduler.stop()
    return {"message": "Scheduler stopped", "running": False}


@router.get("/status")
async def scheduler_status(
    scheduler: Scheduler = Depends(get_scheduler),
) -> dict:
    """查看调度器当前状态。"""
    return {
        "running": scheduler.is_running,
        "interval": scheduler.interval,
        "last_run": scheduler.last_run.isoformat() if scheduler.last_run else None,
        "technical": {
            "running": scheduler.is_technical_running,
            "interval": scheduler.technical_interval,
            "last_run": scheduler.last_technical_run.isoformat() if scheduler.last_technical_run else None,
        },
    }


@router.put("/interval")
async def update_interval(
    interval: int,
    scheduler: Scheduler = Depends(get_scheduler),
) -> dict:
    """动态调整采集间隔（秒）。"""
    if interval < 10:
        raise HTTPException(status_code=400, detail="Interval must be at least 10 seconds")
    scheduler.interval = interval
    return {"message": f"Interval updated to {interval}s", "interval": interval}
