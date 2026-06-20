from __future__ import annotations

import argparse
import asyncio
import logging

from .app import run_server
from .config import API_HOST, API_PORT
from .service import NewsService, Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_cli() -> None:
    """以 CLI 模式运行：启动后台调度器，定时采集并处理新闻。"""
    service = NewsService()
    scheduler = Scheduler(service)
    scheduler.start()

    logger.info("News service CLI mode started")
    logger.info(f"Fetch interval: {scheduler.interval}s")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()
        await service.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="News Service")
    parser.add_argument(
        "--mode",
        choices=["api", "cli"],
        default="api",
        help="运行模式: api (FastAPI 服务, 默认) / cli (后台定时采集)",
    )
    parser.add_argument("--host", default=API_HOST, help="API 监听地址")
    parser.add_argument("--port", type=int, default=API_PORT, help="API 监听端口")
    parser.add_argument("--reload", action="store_true", help="热重载（仅 API 模式）")

    args = parser.parse_args()

    if args.mode == "api":
        logger.info(f"Starting API server on {args.host}:{args.port}")
        run_server(host=args.host, port=args.port, reload=args.reload)
    else:
        asyncio.run(run_cli())


if __name__ == "__main__":
    main()
