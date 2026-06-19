from abc import ABC, abstractmethod
from typing import Any


class NewsFilter(ABC):
    @abstractmethod
    async def should_include(self, news: dict[str, Any]) -> bool:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
