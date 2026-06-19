from __future__ import annotations

import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from news_service.database import NewsDatabase
from news_service.filters import KeywordFilter
from news_service.image_downloader import ImageDownloader
from news_service.models import NewsDetail


@pytest.fixture
def db_path() -> Path:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = Path(f.name)
    yield tmp_path
    tmp_path.unlink(missing_ok=True)


@pytest.fixture
def news_database(db_path: Path) -> NewsDatabase:
    return NewsDatabase(db_path)


@pytest.fixture
def images_dir() -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest_asyncio.fixture
async def image_downloader(images_dir: Path) -> AsyncGenerator[ImageDownloader, None]:
    downloader = ImageDownloader(images_dir)
    yield downloader
    await downloader.close()


@pytest.fixture
def keyword_filter() -> KeywordFilter:
    return KeywordFilter(keywords=["BTC", "ETH"])


@pytest.fixture
def sample_news() -> NewsDetail:
    return NewsDetail(
        id="news_001",
        title="Bitcoin Surges Past $100,000 as BTC Hits New All-Time High",
        content="Bitcoin has reached a new milestone, surpassing the $100,000 mark.",
        source="CoinDesk",
        url="https://example.com/news/001",
        published_at="2026-06-19T10:00:00Z",
        images=["https://example.com/images/btc.jpg"],
    )


@pytest.fixture
def sample_news_detail() -> NewsDetail:
    return NewsDetail(
        id="news_002",
        title="Ethereum ETF Approved by SEC",
        content="The SEC has approved the first spot Ethereum ETF.",
        source="Binance Research",
        url="https://example.com/news/002",
        published_at="2026-06-19T12:00:00Z",
        images=["https://example.com/images/eth.png"],
    )
