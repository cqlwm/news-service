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
news-service/
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


## API details

新闻列表
```shell
curl "https://news-mediator.tradingview.com/news-flow/v2/news?filter=lang%3Azh-Hans&filter=market%3Acrypto%2Cstock&client=screener&streaming=true&user_prostatus=non_pro"
```

响应
```json
{
    "items": [
        {
            "id": "panews:e14bedcd1e3f9:0",
            "title": "韩国拟允许交易所及金融科技公司参与虚拟资产海外汇款系统",
            "published": 1781857920,
            "urgency": 2,
            "link": "https://www.panewslab.com/zh/articles/019edf02-41ae-7522-8e8f-f181f17fee50",
            "storyPath": "/news/panews:e14bedcd1e3f9:0/",
            "provider": {
                "id": "panews",
                "name": "PANews",
                "logo_id": "panews",
                "url": "https://www.panewslab.com/"
            }
        }
    ],
    "streaming": {
        "channel": "a63015f27273a81fc514cce225d6"
    },
    "pagination": {
        "cursor": "eyJfaWQiOiJwYW5ld3M6OTNiN2U5ZTZhZTNmOSIsInB1YmRhdGUiOjE3ODE3ODk0MjgwMDB9"
    }
}
```

新闻信息
```shell
curl "https://news-mediator.tradingview.com/public/news/v1/story?id=gelonghui%3Ab72a2c0b8e3f9%3A0&lang=zh-Hans&user_prostatus=non_pro"
```

响应
```json
{
    "short_description": "格隆汇6月19日｜英特尔CEO陈立武表示，他对英特尔的回报目标是\"5至10年内实现10倍\"，并正在围绕先进封装、新型半导体材料与下一代基板技术，系统性地重构英特尔的技术路线图。在近期一档播客节目中，陈立武详细阐述了其改造英特尔的路径：在稳固资产负债表、聚焦产品线之后，他正将投注重心转向先进封装技术EMIB、玻璃基板、以及氮化镓(GaN)、碳化硅(SiC)、磷化铟(InP)和人工合成钻石等新材料领域，以应对传统工艺节点微缩趋近物理极限的挑战。他同时透露，智能体AI和推理场景的爆发正在带动CPU需求强劲回升，数据中心服务器中CPU与GPU的配比已从过去的一比八向一比四乃至更低演变。陈立武表示，过…",
    "ast_description": {
        "type": "root",
        "children": [
            {
                "type": "p",
                "children": [
                    "格隆汇6月19日｜英特尔CEO陈立武表示，他对英特尔的回报目标是\"5至10年内实现10倍\"，并正在围绕先进封装、新型半导体材料与下一代基板技术，系统性地重构英特尔的技术路线图。"
                ]
            },
            {
                "type": "p",
                "children": [
                    "在近期一档播客节目中，陈立武详细阐述了其改造英特尔的路径：在稳固资产负债表、聚焦产品线之后，他正将投注重心转向先进封装技术EMIB、玻璃基板、以及氮化镓(GaN)、碳化硅(SiC)、磷化铟(InP)和人工合成钻石等新材料领域，以应对传统工艺节点微缩趋近物理极限的挑战。他同时透露，智能体AI和推理场景的爆发正在带动CPU需求强劲回升，数据中心服务器中CPU与GPU的配比已从过去的一比八向一比四乃至更低演变。"
                ]
            },
            {
                "type": "p",
                "children": [
                    "陈立武表示，过去14个月已为英特尔股东创造了约6倍回报，但\"这只是开始\"。他预计到2030至2032年，外界将开始真正认识到英特尔的潜力——不仅限于PC客户端的传统基本盘，更将延伸至边缘计算、物理AI与智能体AI等新兴市场。在他看来，英特尔的XPU、先进封装与代工能力若能有效整合，将为不同工作负载提供定制化芯片解决方案，这是他为公司锚定的长期战略方向。"
                ]
            }
        ]
    },
    "language": "zh-Hans",
    "tags": [
        {
            "title": "Gelonghui",
            "args": [
                {
                    "id": "provider",
                    "value": "gelonghui"
                }
            ]
        },
        {
            "title": "美国股票",
            "args": [
                {
                    "id": "market",
                    "value": "stock"
                },
                {
                    "id": "market_country",
                    "value": "US"
                }
            ]
        }
    ],
    "id": "gelonghui:b72a2c0b8e3f9:0",
    "title": "英特尔CEO：我们的目标是“5-10年10倍” 押注先进封装、玻璃基板和人工钻石",
    "published": 1781859013,
    "urgency": 1,
    "link": "https://www.gelonghui.com/live/2511472",
    "related_symbols": [
        {
            "symbol": "NASDAQ:INTC",
            "logoid": "intel"
        }
    ],
    "story_path": "/news/gelonghui:b72a2c0b8e3f9:0/",
    "is_flash": true,
    "provider": {
        "id": "gelonghui",
        "name": "Gelonghui",
        "logo_id": "gelonghui",
        "url": "https://www.gelonghui.com"
    }
}
```
