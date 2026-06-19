from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from news_service.image_downloader import ImageDownloader


class TestImageDownloader:
    """测试 ImageDownloader 的图片下载与扩展名推断逻辑。"""

    @pytest.mark.asyncio
    async def test_download_image_success(
        self, image_downloader: ImageDownloader, mocker: MockerFixture,
    ) -> None:
        mock_response = mocker.AsyncMock()
        mock_response.content = b"fake_image_bytes"
        mock_response.raise_for_status = mocker.MagicMock()

        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        image_downloader.client = mock_client

        local_path = await image_downloader.download_image(
            "https://example.com/image.jpg", "news_001", 0,
        )
        assert local_path is not None
        assert local_path.endswith(".jpg")
        assert Path(local_path).exists()
        assert Path(local_path).read_bytes() == b"fake_image_bytes"

    @pytest.mark.asyncio
    async def test_download_image_png_extension(
        self, image_downloader: ImageDownloader, mocker: MockerFixture,
    ) -> None:
        mock_response = mocker.AsyncMock()
        mock_response.content = b"png_bytes"
        mock_response.raise_for_status = mocker.MagicMock()

        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        image_downloader.client = mock_client

        local_path = await image_downloader.download_image(
            "https://example.com/image.png", "news_002", 0,
        )
        assert local_path is not None
        assert local_path.endswith(".png")

    @pytest.mark.asyncio
    async def test_download_image_gif_extension(
        self, image_downloader: ImageDownloader, mocker: MockerFixture,
    ) -> None:
        mock_response = mocker.AsyncMock()
        mock_response.content = b"gif_bytes"
        mock_response.raise_for_status = mocker.MagicMock()

        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        image_downloader.client = mock_client

        local_path = await image_downloader.download_image(
            "https://example.com/animated.gif", "news_003", 0,
        )
        assert local_path is not None
        assert local_path.endswith(".gif")

    @pytest.mark.asyncio
    async def test_download_image_unknown_extension_defaults_to_jpg(
        self, image_downloader: ImageDownloader, mocker: MockerFixture,
    ) -> None:
        mock_response = mocker.AsyncMock()
        mock_response.content = b"webp_bytes"
        mock_response.raise_for_status = mocker.MagicMock()

        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        image_downloader.client = mock_client

        local_path = await image_downloader.download_image(
            "https://example.com/image.webp", "news_004", 0,
        )
        assert local_path is not None
        assert local_path.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_download_image_failure_returns_none(
        self, image_downloader: ImageDownloader, mocker: MockerFixture,
    ) -> None:
        mock_client = mocker.AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        image_downloader.client = mock_client

        local_path = await image_downloader.download_image(
            "https://example.com/fail.jpg", "news_005", 0,
        )
        assert local_path is None

    @pytest.mark.asyncio
    async def test_download_image_creates_subdirectories(
        self, tmp_path: Path, mocker: MockerFixture,
    ) -> None:
        """确保下载器在嵌套目录中也能正确创建。"""
        nested_dir = tmp_path / "sub" / "dir"
        downloader = ImageDownloader(nested_dir)
        mock_response = mocker.AsyncMock()
        mock_response.content = b"bytes"
        mock_response.raise_for_status = mocker.MagicMock()

        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        downloader.client = mock_client

        local_path = await downloader.download_image(
            "https://example.com/test.jpg", "news_006", 0,
        )
        assert local_path is not None
        assert Path(local_path).exists()
        await downloader.close()

    @pytest.mark.asyncio
    async def test_close(self, image_downloader: ImageDownloader, mocker: MockerFixture) -> None:
        mock_client = mocker.AsyncMock()
        image_downloader.client = mock_client

        await image_downloader.close()
        mock_client.aclose.assert_called_once()
