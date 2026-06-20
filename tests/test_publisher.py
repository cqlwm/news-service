from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from news_service.publisher import Publisher


class TestPublisher:
    """测试 Publisher 的发布逻辑。"""

    @pytest.mark.asyncio
    async def test_publish_with_image(self, mocker: MockerFixture) -> None:
        """提供图片时直接发布，不触发截图。"""
        mock_post = mocker.patch("binance_service.poster.post")
        mock_screenshot = mocker.patch.object(Publisher, "_take_screenshot")
        publisher = Publisher()

        result = await publisher.publish("DOGE", "Test content", "/tmp/test.png")

        mock_post.assert_called_once_with(
            base_asset="DOGE",
            content="Test content",
            image_path="/tmp/test.png",
            headless=False,
        )
        mock_screenshot.assert_not_called()
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_without_image_triggers_screenshot(self, mocker: MockerFixture) -> None:
        """未提供图片时自动截图后发布。"""
        mock_post = mocker.patch("binance_service.poster.post")
        mocker.patch.object(
            Publisher,
            "_take_screenshot",
            return_value="/tmp/screenshot_doge.png",
        )
        publisher = Publisher()

        result = await publisher.publish("DOGE", "Test content")

        mock_post.assert_called_once_with(
            base_asset="DOGE",
            content="Test content",
            image_path="/tmp/screenshot_doge.png",
            headless=False,
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_failure(self, mocker: MockerFixture) -> None:
        """发布失败时返回 False。"""
        mocker.patch(
            "binance_service.poster.post",
            side_effect=RuntimeError("Chrome not available"),
        )
        publisher = Publisher()

        result = await publisher.publish("ETH", "Ethereum news")

        assert result is False

    @pytest.mark.asyncio
    async def test_screenshot_failure_falls_to_publish_failure(self, mocker: MockerFixture) -> None:
        """截图失败时 publish 也返回 False。"""
        mocker.patch.object(
            Publisher,
            "_take_screenshot",
            side_effect=RuntimeError("Screenshot failed"),
        )
        publisher = Publisher()

        result = await publisher.publish("BTC", "Bitcoin news")

        assert result is False

    @pytest.mark.asyncio
    async def test_take_screenshot_uses_headless(self, mocker: MockerFixture) -> None:
        """截图使用 headless=True。"""
        mock_screenshot = mocker.patch(
            "binance_service.screenshot.take_futures_screenshot",
            return_value="/tmp/test_btc.png",
        )
        mocker.patch("news_service.publisher.AppConfig")
        mocker.patch("news_service.publisher.tempfile.NamedTemporaryFile")

        publisher = Publisher()
        result = await publisher._take_screenshot("BTC")

        mock_screenshot.assert_called_once()
        # 验证 headless=True 被传入
        _, kwargs = mock_screenshot.call_args
        assert kwargs.get("headless") is True
        assert result == "/tmp/test_btc.png"
