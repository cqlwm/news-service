from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    app = FastAPI(
        title="News Service API",
        description="新闻采集、处理与发布服务 REST API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """启动 uvicorn 服务器。"""
    uvicorn.run(
        "news_service.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
