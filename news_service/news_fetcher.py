from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import logging
import re

import httpx

from .models import NewsDetail, NewsListItem, Provider, AstNode

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self, list_url: str, detail_url: str):
        self.list_url = list_url
        self.detail_url = detail_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_news_list(self) -> list[NewsListItem]:
        params: dict[str, Any] = {
            "filter": ["lang:zh-Hans", "market:crypto,stock"],
            "client": "screener",
            "streaming": "true",
            "user_prostatus": "non_pro",
        }

        try:
            response = await self.client.get(self.list_url, params=params)
            response.raise_for_status()
            data = response.json()

            items: list[NewsListItem] = []
            for item in data.get("items", []):
                raw_id = item.get("id")
                if not raw_id:
                    continue
                provider_raw = item.get("provider", {})
                provider = Provider(
                    id=provider_raw.get("id", ""),
                    name=provider_raw.get("name", ""),
                    logo_id=provider_raw.get("logo_id", ""),
                    url=provider_raw.get("url"),
                )
                items.append(NewsListItem(
                    id=raw_id,
                    title=item.get("title", ""),
                    published=item.get("published", 0),
                    urgency=item.get("urgency", 0),
                    story_path=item.get("storyPath", ""),
                    provider=provider,
                    link=item.get("link"),
                ))

            return items
        except Exception as e:
            logger.error(f"Failed to fetch news list: {e}")
            return []

    async def fetch_news_detail(self, news_id: str) -> NewsDetail | None:
        params: dict[str, str | int] = {
            "id": news_id,
            "lang": "zh-Hans",
            "user_prostatus": "non_pro",
        }

        try:
            response = await self.client.get(self.detail_url, params=params)
            response.raise_for_status()
            data = response.json()

            return NewsDetail(
                id=news_id,
                title=data.get("title", ""),
                content=self._extract_content(data),
                source=self._extract_source(data),
                url=data.get("link", ""),
                published_at=self._format_published(data.get("published")),
                images=self._extract_images(data),
            )
        except Exception as e:
            logger.error(f"Failed to fetch news detail {news_id}: {e}")
            return None

    def _extract_content(self, data: dict[str, Any]) -> str:
        short_desc = data.get("short_description", "")
        if short_desc:
            return short_desc

        ast = data.get("ast_description")
        if ast:
            return self._extract_ast_text(ast)

        return ""

    def _extract_ast_text(self, node: Any) -> str:
        if isinstance(node, str):
            return node
        if isinstance(node, dict):
            children = node.get("children", [])
            return "".join(self._extract_ast_text(child) for child in children)
        if isinstance(node, list):
            return "".join(self._extract_ast_text(child) for child in node)
        return ""

    def _extract_source(self, data: dict[str, Any]) -> str:
        provider = data.get("provider", {})
        if isinstance(provider, dict):
            return provider.get("name", "")
        return str(provider) if provider else ""

    def _format_published(self, published: Any) -> str | None:
        if isinstance(published, (int, float)):
            dt = datetime.fromtimestamp(published, tz=timezone.utc)
            return dt.isoformat()
        return None

    def _extract_images(self, data: dict[str, Any]) -> list[str]:
        images: list[str] = []

        if data.get("image"):
            images.append(data["image"])

        if data.get("images"):
            images.extend(data["images"])

        content = data.get("short_description", "")
        if content:
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
            images.extend(re.findall(img_pattern, content))

        return images

    async def close(self) -> None:
        await self.client.aclose()
