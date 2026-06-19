from __future__ import annotations

from pathlib import Path

import pytest

from news_service.image_downloader import ImageDownloader

REAL_IMAGE_URL = (
    "https://images.google.com/images/branding/google_wordmark/v1/2x/googlelogo_color_272x92dp.png"
)
FAKE_IMAGE_URL = "https://example.com/nonexistent-image.jpg"


@pytest.mark.asyncio
async def test_download_real_image(tmp_path: Path) -> None:
    """验证真实图片 URL 能成功下载并保存到本地。"""
    downloader = ImageDownloader(tmp_path)
    try:
        local_path = await downloader.download_image(REAL_IMAGE_URL, "google_logo", 0)
        assert local_path is not None, "真实图片下载应成功"
        assert Path(local_path).exists(), "下载后的文件应存在于磁盘"
        assert Path(local_path).stat().st_size > 0, "下载的文件不应为空"
        assert local_path.endswith(".png"), "Google logo 扩展名应为 .png"
    finally:
        await downloader.close()


@pytest.mark.asyncio
async def test_download_real_image_with_news_id(tmp_path: Path) -> None:
    """验证下载的文件名包含 news_id 和 index。"""
    downloader = ImageDownloader(tmp_path)
    try:
        local_path = await downloader.download_image(REAL_IMAGE_URL, "news_001", 0)
        assert local_path is not None
        filename = Path(local_path).name
        assert "news_001" in filename, f"文件名应包含 news_id: {filename}"
        assert "0" in filename, f"文件名应包含 index: {filename}"
    finally:
        await downloader.close()


@pytest.mark.asyncio
async def test_download_fake_image_returns_none(tmp_path: Path) -> None:
    """验证不存在的图片 URL 返回 None。"""
    downloader = ImageDownloader(tmp_path)
    try:
        local_path = await downloader.download_image(FAKE_IMAGE_URL, "fake_news", 0)
        assert local_path is None, "不存在的图片应返回 None"
    finally:
        await downloader.close()


@pytest.mark.asyncio
async def test_download_creates_images_directory(tmp_path: Path) -> None:
    """验证下载器会自动创建不存在的目标目录。"""
    nested_dir = tmp_path / "sub" / "images"
    assert not nested_dir.exists(), "测试前目录不应存在"

    downloader = ImageDownloader(nested_dir)
    try:
        assert nested_dir.exists(), "下载器初始化时应自动创建目录"
        local_path = await downloader.download_image(REAL_IMAGE_URL, "dir_test", 0)
        assert local_path is not None
        assert Path(local_path).exists()
    finally:
        await downloader.close()


@pytest.mark.asyncio
async def test_download_multiple_images(tmp_path: Path) -> None:
    """验证多次下载不同图片均能成功。"""
    downloader = ImageDownloader(tmp_path)
    try:
        path1 = await downloader.download_image(REAL_IMAGE_URL, "multi", 0)
        path2 = await downloader.download_image(REAL_IMAGE_URL, "multi", 1)

        assert path1 is not None
        assert path2 is not None
        assert path1 != path2, "两次下载的文件路径应不同"
        assert Path(path1).exists()
        assert Path(path2).exists()
    finally:
        await downloader.close()


@pytest.mark.asyncio
async def test_extension_inference(tmp_path: Path) -> None:
    """验证从 URL 推断扩展名的逻辑（不依赖下载结果）。"""
    downloader = ImageDownloader(tmp_path)
    try:
        # PNG URL → .png
        assert downloader._get_extension("https://example.com/image.png") == ".png"
        # GIF URL → .gif
        assert downloader._get_extension("https://example.com/animated.gif") == ".gif"
        # JPG URL → .jpg
        assert downloader._get_extension("https://example.com/photo.jpg") == ".jpg"
        # URL 中包含 .png 但不以 .png 结尾
        assert downloader._get_extension("https://example.com/image.png?w=200") == ".png"
        # 未知扩展名 → .jpg
        assert downloader._get_extension("https://example.com/image.webp") == ".jpg"
        # 无扩展名 → .jpg
        assert downloader._get_extension("https://example.com/photo") == ".jpg"
    finally:
        await downloader.close()


@pytest.mark.asyncio
async def test_close_releases_resources(tmp_path: Path) -> None:
    """验证 close 后客户端被正确关闭。"""
    downloader = ImageDownloader(tmp_path)
    await downloader.close()
    # close 后不应抛出异常
    await downloader.close()
