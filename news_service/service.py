from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .config import (
    DB_PATH,
    FETCH_INTERVAL,
    IMAGES_DIR,
    MAX_NEWS_PER_FETCH,
    NEWS_DETAIL_URL,
    NEWS_LIST_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from .content_generator import ContentGenerator, ConfigError
from .database import NewsDatabase, NewsStatus
from .filters import NewsFilter
from .image_downloader import ImageDownloader
from .news_fetcher import NewsFetcher
from .publisher import Publisher
from .technical import TechnicalEngine, TechnicalConfig

logger = logging.getLogger(__name__)


class NewsService:
    """新闻服务核心编排层。

    封装新闻采集、过滤、生成、发布的完整流程，
    供 API 层和后台调度器调用。
    """

    def __init__(self) -> None:
        self.db = NewsDatabase(DB_PATH)
        self.fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
        self.downloader = ImageDownloader(IMAGES_DIR)
        self.generator = ContentGenerator(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
        self.publisher = Publisher()
        self.technical_engine = TechnicalEngine()

        self.filters: list[NewsFilter] = []
        # 启动时从数据库加载运行时配置
        self.reload_config()

    # ── 采集 ───────────────────────────────────────────────

    async def fetch_news(self) -> list[str]:
        """采集新闻列表，拉取详情并入库，返回新入库的新闻 ID 列表。"""
        logger.info("Fetching news list...")
        news_items = await self.fetcher.fetch_news_list()

        new_ids: list[str] = []
        for item in news_items:
            if self.db.news_exists(item.id):
                continue
            # 拉取详情并入库
            detail = await self.fetcher.fetch_news_detail(item.id)
            if not detail:
                continue
            published_at = detail.published_at
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at)
            self.db.save_news(
                news_id=detail.id,
                title=detail.title,
                content=detail.content,
                source=detail.source,
                url=detail.url,
                published_at=published_at,
            )
            new_ids.append(detail.id)

        logger.info(f"Fetched and saved {len(new_ids)} new news out of {len(news_items)} total")
        return new_ids

    # ── 单条新闻处理 ───────────────────────────────────────

    async def process_news(self, news_id: str) -> bool:
        """对单条新闻执行完整处理流程：过滤 → 入库 → 下载图片 → 生成贴文 → 发布。

        返回 True 表示成功发布，False 表示被过滤或失败。
        """
        try:
            # 优先从本地数据库获取（技术面新闻等已入库的新闻）
            db_news = self.db.get_news_by_id(news_id)
            if db_news:
                title = db_news["title"]
                content = db_news.get("content", "")
                image_path: str | None = None
            else:
                # 不在本地库中，从外部 API 拉取
                news_detail = await self.fetcher.fetch_news_detail(news_id)
                if not news_detail:
                    return False

                # 过滤
                for filter_ in self.filters:
                    if not await filter_.should_include(news_detail):
                        logger.info(f"News {news_id} filtered out by {filter_.name}")
                        return False

                # 入库
                published_at = news_detail.published_at
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at)
                self.db.save_news(
                    news_id=news_detail.id,
                    title=news_detail.title,
                    content=news_detail.content,
                    source=news_detail.source,
                    url=news_detail.url,
                    published_at=published_at,
                )

                # 下载图片
                image_path = None
                if news_detail.images:
                    local_path = await self.downloader.download_image(
                        news_detail.images[0], news_detail.id, 0
                    )
                    if local_path:
                        self.db.save_image(news_detail.id, news_detail.images[0], local_path)
                        image_path = local_path

                title = news_detail.title
                content = news_detail.content

            # 生成贴文
            try:
                base_asset, post_content = await self.generator.generate_post(title, content)
            except ConfigError as e:
                logger.warning(f"Cannot generate post for {news_id}: LLM not configured")
                self.db.update_news_status(news_id, NewsStatus.GENERATION_FAILED, error_message=str(e))
                return False
            self.db.save_post(news_id, base_asset, post_content)
            self.db.update_news_status(news_id, NewsStatus.POST_GENERATED)

            # 发布
            success = await self.publisher.publish(base_asset, post_content, image_path)
            if success:
                self.db.mark_post_published(news_id)
                self.db.update_news_status(news_id, NewsStatus.PUBLISHED)
                logger.info(f"Successfully published news: {title}")
            else:
                self.db.update_news_status(news_id, NewsStatus.PUBLISH_FAILED, error_message="Publisher returned failure")
                logger.error(f"Failed to publish news: {title}")

            return success

        except ConfigError:
            logger.warning(f"Cannot process news {news_id}: LLM not configured")
            return False
        except Exception as e:
            logger.error(f"Error processing news {news_id}: {e}")
            self.db.update_news_status(news_id, NewsStatus.GENERATION_FAILED, error_message=str(e))
            return False

    # ── 仅生成贴文（不发布） ───────────────────────────────

    async def generate_post_only(self, news_id: str) -> tuple[str, str] | None:
        """仅为新闻生成贴文内容，不发布。返回 (base_asset, content) 或 None。

        仅允许在 PENDING / GENERATION_FAILED 状态下生成。
        已发布（PUBLISHED）或已废弃（DISCARDED）的新闻不可再生成。
        """
        news = self.db.get_news_by_id(news_id)
        if not news:
            return None

        current_status = news.get("status", "")
        if current_status in (NewsStatus.PUBLISHED.value, NewsStatus.DISCARDED.value):
            logger.warning(f"Cannot generate post for {news_id}: terminal status {current_status}")
            return None

        try:
            base_asset, content = await self.generator.generate_post(
                news["title"], news.get("content", "")
            )
        except ConfigError as e:
            logger.error(f"Cannot generate post for {news_id}: {e}")
            return None

        self.db.save_post(news_id, base_asset, content)
        self.db.update_news_status(news_id, NewsStatus.POST_GENERATED)
        return base_asset, content

    # ── 批量处理 ───────────────────────────────────────────

    async def process_pending_news(self, limit: int = 5) -> dict[str, bool]:
        """批量处理待处理新闻，返回 {news_id: success} 映射。"""
        pending = self.db.get_unprocessed_news(limit=limit)
        results: dict[str, bool] = {}
        for news in pending:
            results[news["id"]] = await self.process_news(news["id"])
        return results

    # ── 重试 ───────────────────────────────────────────────

    async def retry_news(self, news_id: str) -> bool:
        """重试失败的新闻。

        仅允许在 GENERATION_FAILED / PUBLISH_FAILED 状态下重试。
        - GENERATION_FAILED：重新生成贴文后发布
        - PUBLISH_FAILED：仅重试发布
        """
        news = self.db.get_news_by_id(news_id)
        if not news:
            return False

        current_status = news.get("status", "")

        if current_status == NewsStatus.PUBLISH_FAILED.value:
            # 仅重试发布
            success = await self.publish_post(news_id)
            if success:
                logger.info(f"Retry publish succeeded for news: {news_id}")
            else:
                logger.error(f"Retry publish failed for news: {news_id}")
            return success

        if current_status == NewsStatus.GENERATION_FAILED.value:
            # 重新生成贴文后发布
            result = await self.generate_post_only(news_id)
            if not result:
                logger.error(f"Retry generation failed for news: {news_id}")
                return False
            return await self.publish_post(news_id)

        logger.warning(f"Cannot retry news {news_id}: invalid status {current_status}")
        return False

    # ── 发布 ───────────────────────────────────────────────

    async def publish_post(self, news_id: str) -> bool:
        """发布已生成的贴文。

        仅允许在 POST_GENERATED / PUBLISH_FAILED 状态下发布。
        已发布（PUBLISHED）或已废弃（DISCARDED）的新闻不可再发布。
        """
        news = self.db.get_news_by_id(news_id)
        if not news:
            return False

        current_status = news.get("status", "")
        if current_status in (NewsStatus.PUBLISHED.value, NewsStatus.DISCARDED.value):
            logger.warning(f"Cannot publish news {news_id}: terminal status {current_status}")
            return False

        post = self.db.get_post_by_news_id(news_id)
        if not post:
            return False

        image_path = self.db.get_first_image(news_id)
        success = await self.publisher.publish(post["base_asset"], post["content"], image_path)
        if success:
            self.db.mark_post_published(news_id)
            self.db.update_news_status(news_id, NewsStatus.PUBLISHED)
        else:
            self.db.update_news_status(news_id, NewsStatus.PUBLISH_FAILED, error_message="Publisher returned failure")
        return success

    # ── 废弃 ───────────────────────────────────────────────

    def discard_news(self, news_id: str) -> bool:
        """废弃新闻（终态）。

        仅允许在 GENERATION_FAILED / PUBLISH_FAILED 状态下废弃。
        废弃后不可再恢复。
        """
        news = self.db.get_news_by_id(news_id)
        if not news:
            return False

        current_status = news.get("status", "")
        if current_status not in (NewsStatus.GENERATION_FAILED.value, NewsStatus.PUBLISH_FAILED.value):
            logger.warning(f"Cannot discard news {news_id}: invalid status {current_status}")
            return False

        self.db.update_news_status(news_id, NewsStatus.DISCARDED)
        logger.info(f"News {news_id} discarded")
        return True

    # ── 资源清理 ───────────────────────────────────────────

    async def fetch_technical_news(self) -> list[str]:
        """运行技术面检测，生成技术新闻并入库，返回新入库的新闻 ID 列表。"""
        logger.info("Fetching technical news...")
        news_items = await self.technical_engine.run()

        new_ids: list[str] = []
        for item in news_items:
            if self.db.news_exists(item.id):
                continue
            published_at = datetime.fromisoformat(item.published_at) if item.published_at else None
            # 合并所有 pattern_type（逗号分隔）
            pattern_type = ""
            self.db.save_technical_news(
                news_id=item.id,
                title=item.title,
                content=item.content,
                source=item.source,
                url=item.url,
                published_at=published_at,
                pattern_type=pattern_type,
            )
            new_ids.append(item.id)

        logger.info(f"Fetched {len(new_ids)} technical news")
        return new_ids

    def reload_config(self) -> None:
        """从数据库重新加载运行时配置。"""
        settings = self.db.get_all_settings()

        # 更新 ContentGenerator
        api_key = settings.get('openai_api_key', '')
        base_url = settings.get('openai_base_url', '')
        model = settings.get('openai_model', '')
        if api_key or base_url or model:
            self.generator.update_config(
                api_key=api_key or None,
                base_url=base_url or None,
                model=model or None,
            )

        logger.info(f'Configuration reloaded from DB: {len(settings)} keys')

    async def close(self) -> None:
        await self.fetcher.close()
        await self.technical_engine.close()
        await self.downloader.close()


class Scheduler:
    """后台定时采集调度器。"""

    def __init__(self, service: NewsService) -> None:
        self.service = service
        self._task: asyncio.Task[None] | None = None
        self._technical_task: asyncio.Task[None] | None = None
        self._interval: int = FETCH_INTERVAL
        self._technical_interval: int = 300
        self._last_run: datetime | None = None
        self._last_technical_run: datetime | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def is_technical_running(self) -> bool:
        return self._technical_task is not None and not self._technical_task.done()

    @property
    def technical_interval(self) -> int:
        return self._technical_interval

    @technical_interval.setter
    def technical_interval(self, value: int) -> None:
        self._technical_interval = max(30, value)

    @property
    def last_technical_run(self) -> datetime | None:
        return self._last_technical_run

    @property
    def interval(self) -> int:
        return self._interval

    @interval.setter
    def interval(self, value: int) -> None:
        self._interval = max(10, value)

    @property
    def last_run(self) -> datetime | None:
        return self._last_run

    async def _loop(self) -> None:
        while True:
            try:
                logger.info("Scheduler: starting fetch cycle...")
                await self.service.fetch_news()
                self._last_run = datetime.utcnow()
            except Exception as e:
                logger.error(f"Scheduler cycle error: {e}")
            await asyncio.sleep(self._interval)

    async def _technical_loop(self) -> None:
        while True:
            try:
                logger.info("Scheduler: starting technical analysis cycle...")
                await self.service.fetch_technical_news()
                self._last_technical_run = datetime.utcnow()
            except Exception as e:
                logger.error(f"Scheduler technical cycle error: {e}")
            await asyncio.sleep(self._technical_interval)

    def start(self) -> None:
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        self._task = asyncio.create_task(self._loop())
        if not self.is_technical_running:
            self._technical_task = asyncio.create_task(self._technical_loop())
        logger.info("Scheduler started")

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        if self._technical_task and not self._technical_task.done():
            self._technical_task.cancel()
            self._technical_task = None
        logger.info("Scheduler stopped")
