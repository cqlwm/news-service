from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from binance_service._config import AppConfig, WindowConfig

logger = logging.getLogger(__name__)

SCREENSHOT_SYMBOL_SUFFIX = "USDT"
SCREENSHOT_WINDOW_WIDTH = 430
SCREENSHOT_WINDOW_HEIGHT = 932


class Publisher:
    """发布器，将生成的贴文发布到 Binance Square。

    通过 binance-service 的 Chrome 自动化能力实现发布。
    发布走 CDP 连接已登录的 Chrome（headed），截图走 headless 模式。
    """

    async def publish(self, base_asset: str, content: str, image_path: str | None = None) -> bool:
        """发布贴文到 Binance Square。

        Args:
            base_asset: 基础资产名称，如 DOGE
            content: 贴文内容
            image_path: 可选，本地图片路径。为 None 时自动截图

        Returns:
            发布成功返回 True，失败返回 False
        """
        try:
            resolved_image = image_path
            if resolved_image is None:
                resolved_image = await self._take_screenshot(base_asset)

            from binance_service.poster import post

            # 发布需要登录态，走 CDP 连接已登录的 Chrome（headed=False）
            await asyncio.to_thread(
                post,
                base_asset=base_asset,
                content=content,
                image_path=resolved_image,
                headless=True,
            )
            logger.info("Published post for %s", base_asset)
            return True
        except Exception:
            logger.exception("Failed to publish post for %s", base_asset)
            return False

    async def _take_screenshot(self, base_asset: str) -> str:
        """截取合约 K 线图，返回临时图片路径。"""
        from binance_service.screenshot import take_futures_screenshot

        config = AppConfig.load()
        symbol = f"{base_asset}{SCREENSHOT_SYMBOL_SUFFIX}"
        tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()

        screenshot_config = AppConfig(
            chrome=config.chrome,
            window=WindowConfig(
                width=SCREENSHOT_WINDOW_WIDTH,
                height=SCREENSHOT_WINDOW_HEIGHT,
            ),
        )

        # 截图不需要登录态，走 headless 模式
        output_path = await asyncio.to_thread(
            take_futures_screenshot,
            config=screenshot_config,
            symbol=symbol,
            output=tmp_path,
            headless=True,
        )
        logger.info("Screenshot taken for %s: %s", symbol, output_path)
        return str(output_path)
