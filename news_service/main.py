import asyncio
import logging
from pathlib import Path
from datetime import datetime

from .config import (
    NEWS_LIST_URL, NEWS_DETAIL_URL, IMAGES_DIR, DB_PATH,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    FETCH_INTERVAL, MAX_NEWS_PER_FETCH
)
from .database import NewsDatabase
from .news_fetcher import NewsFetcher
from .image_downloader import ImageDownloader
from .content_generator import ContentGenerator
from .publisher import Publisher
from .filters import NewsFilter, KeywordFilter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self.db = NewsDatabase(DB_PATH)
        self.fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
        self.downloader = ImageDownloader(IMAGES_DIR)
        self.generator = ContentGenerator(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
        self.publisher = Publisher()
        
        self.filters: list[NewsFilter] = []
    
    async def process_news_cycle(self):
        logger.info("Fetching news list...")
        news_ids = await self.fetcher.fetch_news_list()
        
        new_news_ids = [nid for nid in news_ids if not self.db.news_exists(nid)]
        logger.info(f"Found {len(new_news_ids)} new news out of {len(news_ids)} total")
        
        for news_id in new_news_ids[:MAX_NEWS_PER_FETCH]:
            await self._process_single_news(news_id)
    
    async def _process_single_news(self, news_id: str):
        try:
            news_detail = await self.fetcher.fetch_news_detail(news_id)
            if not news_detail:
                return
            
            for filter in self.filters:
                if not await filter.should_include(news_detail):
                    logger.info(f"News {news_id} filtered out by {filter.name}")
                    return
            
            published_at = news_detail.get("published_at")
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at)
            
            self.db.save_news(
                news_id=news_id,
                title=news_detail["title"],
                content=news_detail["content"],
                source=news_detail["source"],
                url=news_detail["url"],
                published_at=published_at
            )
            
            image_path = None
            images = news_detail.get("images", [])
            if images:
                local_path = await self.downloader.download_image(images[0], news_id, 0)
                if local_path:
                    self.db.save_image(news_id, images[0], local_path)
                    image_path = local_path
            
            base_asset, post_content = await self.generator.generate_post(
                news_detail["title"],
                news_detail["content"]
            )
            
            success = self.publisher.publish(base_asset, post_content, image_path)
            
            if success:
                self.db.mark_processed(news_id)
                logger.info(f"Successfully published news: {news_detail['title']}")
            else:
                logger.error(f"Failed to publish news: {news_detail['title']}")
        
        except Exception as e:
            logger.error(f"Error processing news {news_id}: {e}")
    
    async def run(self):
        logger.info("News service starting...")
        
        try:
            while True:
                await self.process_news_cycle()
                logger.info(f"Sleeping for {FETCH_INTERVAL} seconds...")
                await asyncio.sleep(FETCH_INTERVAL)
        except KeyboardInterrupt:
            logger.info("News service stopped by user")
        finally:
            await self.fetcher.close()
            await self.downloader.close()


async def main():
    service = NewsService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
