from __future__ import annotations

from abc import ABC, abstractmethod

from news_service.models import NewsDetail


class NewsFilter(ABC):
    @abstractmethod
    async def should_include(self, news: NewsDetail) -> bool:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
