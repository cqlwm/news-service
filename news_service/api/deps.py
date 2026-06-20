from __future__ import annotations

from ..config import DB_PATH
from ..database import NewsDatabase
from ..service import NewsService, Scheduler

# 全局单例
_service: NewsService | None = None
_scheduler: Scheduler | None = None


def get_db() -> NewsDatabase:
    return NewsDatabase(DB_PATH)


def get_service() -> NewsService:
    global _service
    if _service is None:
        _service = NewsService()
    return _service


def get_service_instance() -> NewsService | None:
    """获取已初始化的服务实例（可能为 None）。"""
    return _service


def get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(get_service())
    return _scheduler
