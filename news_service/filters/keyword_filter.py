from __future__ import annotations

from .base import NewsFilter
from news_service.models import NewsDetail


class KeywordFilter(NewsFilter):
    def __init__(self, keywords: list[str], match_source: bool = True):
        self.keywords = [k.lower() for k in keywords]
        self.match_source = match_source

    async def should_include(self, news: NewsDetail) -> bool:
        if not self.keywords:
            return True

        text_to_search = f"{news.title} {news.content}"
        if self.match_source:
            text_to_search += f" {news.source}"

        text_to_search = text_to_search.lower()
        return any(kw in text_to_search for kw in self.keywords)

    @property
    def name(self) -> str:
        return "keyword_filter"
