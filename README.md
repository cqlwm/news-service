# News Service

自动获取新闻、备份到 SQLite、下载图片、通过 LLM 生成贴文并发布到 Binance Square。

## 使用方法

1. 配置 `.env` 文件：
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
FETCH_INTERVAL=60
MAX_NEWS_PER_FETCH=5
```

2. 运行服务：
```shell
uv run python -m news_service.main
```

## 添加自定义过滤器

继承 `NewsFilter` 基类并实现 `should_include` 方法：

```python
from news_service.filters import NewsFilter
from typing import Any

class SourceFilter(NewsFilter):
    def __init__(self, allowed_sources: list[str]):
        self.allowed_sources = [s.lower() for s in allowed_sources]
    
    async def should_include(self, news: dict[str, Any]) -> bool:
        return news.get("source", "").lower() in self.allowed_sources
    
    @property
    def name(self) -> str:
        return "source_filter"
```

在 `main.py` 中注册：

```python
self.filters: list[NewsFilter] = [
    KeywordFilter(keywords=["BTC", "ETH"]),
    SourceFilter(allowed_sources=["CoinDesk", "Binance"]),
]
```

## 目录结构

```
news_service/
├── news_service/
│   ├── config.py              # 配置管理
│   ├── database.py            # SQLite 操作
│   ├── news_fetcher.py        # 新闻获取
│   ├── image_downloader.py    # 图片下载
│   ├── content_generator.py   # LLM 内容生成
│   ├── filters/
│   │   ├── base.py            # 抽象过滤器基类
│   │   └── keyword_filter.py  # 关键词过滤器示例
│   ├── publisher.py           # 发布器
│   └── main.py                # 主入口
├── images/                    # 图片存储目录
├── news.db                    # SQLite 数据库
└── .env                       # 环境变量
```
