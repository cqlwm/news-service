from __future__ import annotations

from fastapi import APIRouter

from . import system, news, pipeline, filters, scheduler, settings, technical

api_router = APIRouter()

api_router.include_router(system.router, tags=["system"])
api_router.include_router(news.router, prefix="/api/news", tags=["news"])
api_router.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
api_router.include_router(filters.router, prefix="/api/filters", tags=["filters"])
api_router.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])
api_router.include_router(settings.router, prefix="/api/settings", tags=["settings"])
