import httpx
from datetime import datetime
from typing import Any
import logging
import re

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self, list_url: str, detail_url: str):
        self.list_url = list_url
        self.detail_url = detail_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_news_list(self) -> list[str]:
        params = {
            "filter": ["lang:zh-Hans", "market:crypto,stock"],
            "client": "screener",
            "streaming": "true",
            "user_prostatus": "non_pro"
        }
        
        try:
            response = await self.client.get(self.list_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            news_ids = []
            for item in data.get("news", []):
                news_id = item.get("id")
                if news_id:
                    news_ids.append(news_id)
            
            return news_ids
        except Exception as e:
            logger.error(f"Failed to fetch news list: {e}")
            return []
    
    async def fetch_news_detail(self, news_id: str) -> dict[str, Any] | None:
        params = {
            "id": news_id,
            "lang": "zh-Hans",
            "user_prostatus": "non_pro"
        }
        
        try:
            response = await self.client.get(self.detail_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            story = data.get("story", {})
            return {
                "id": news_id,
                "title": story.get("title", ""),
                "content": story.get("content", ""),
                "source": story.get("source", ""),
                "url": story.get("url", ""),
                "published_at": story.get("published_at"),
                "images": self._extract_images(story)
            }
        except Exception as e:
            logger.error(f"Failed to fetch news detail {news_id}: {e}")
            return None
    
    def _extract_images(self, story: dict) -> list[str]:
        images = []
        
        if story.get("image"):
            images.append(story["image"])
        
        if story.get("images"):
            images.extend(story["images"])
        
        content = story.get("content", "")
        if content:
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
            images.extend(re.findall(img_pattern, content))
        
        return images
    
    async def close(self):
        await self.client.aclose()
