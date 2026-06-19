from .base import NewsFilter
from typing import Any


class KeywordFilter(NewsFilter):
    def __init__(self, keywords: list[str], match_source: bool = True):
        self.keywords = [k.lower() for k in keywords]
        self.match_source = match_source
    
    async def should_include(self, news: dict[str, Any]) -> bool:
        if not self.keywords:
            return True
        
        text_to_search = f"{news.get('title', '')} {news.get('content', '')}"
        if self.match_source:
            text_to_search += f" {news.get('source', '')}"
        
        text_to_search = text_to_search.lower()
        return any(kw in text_to_search for kw in self.keywords)
    
    @property
    def name(self) -> str:
        return "keyword_filter"
