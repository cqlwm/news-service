# News Service

自动采集加密货币新闻、技术面分析信号，通过 LLM 生成社交媒体贴文并发布到 Binance Square。附带 Web 管理面板。

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    News Service                      │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  NewsFetcher  │  │  Technical   │  │  Publisher │  │
│  │  (TradingView │  │  Engine      │  │ (Binance   │  │
│  │   新闻API)    │  │  (CCXT+币安) │  │  Square)   │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                 │        │
│  ┌──────▼─────────────────▼─────────────────▼──────┐ │
│  │               NewsService (编排层)               │ │
│  │  过滤 → 入库 → 下载图片 → LLM生成 → 发布       │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │              NewsDatabase (SQLite)               │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  FastAPI REST API  ───  React Frontend          │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 职责 |
|------|------|
| `news_fetcher.py` | 从 TradingView News API 采集新闻列表和详情 |
| `filters/` | 可插拔的新闻过滤器（关键词过滤等） |
| `image_downloader.py` | 下载新闻配图到本地 |
| `content_generator.py` | 通过 OpenAI/兼容 API 将新闻改写为社交媒体贴文 |
| `publisher.py` | 发布贴文到 Binance Square（通过 Chrome CDP 自动化） |
| `technical/` | 技术面分析引擎（K线形态、RSI、MACD、成交量异动） |
| `database.py` | SQLite 持久化（新闻、图片、贴文、配置） |
| `service.py` | 核心编排层 + 后台定时调度器 |
| `api/` | FastAPI REST API 路由 |
| `app.py` | FastAPI 应用创建与启动 |

## 快速开始

### 1. 配置环境变量

```env
# OpenAI / 兼容 API
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 采集调度
FETCH_INTERVAL=60          # 新闻采集间隔（秒）
MAX_NEWS_PER_FETCH=5       # 每次采集最大条数

# API 服务
API_HOST=0.0.0.0
API_PORT=8000

# Chrome 自动化（用于发布到 Binance Square）
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR="/path/to/chrome/user-data"
DEBUG_ADDRESS=127.0.0.1
DEBUG_PORT=18800
```

### 2. 启动服务

```shell
# API 模式（默认，附带 Web 管理面板）
uv run python -m news_service.main

# CLI 模式（仅后台采集，无 API）
uv run python -m news_service.main --mode cli

# API 模式 + 热重载（开发）
uv run python -m news_service.main --reload
```

API 模式默认监听 `http://0.0.0.0:8000`，前端管理面板在 `http://localhost:8000`。

### 3. 启动前端（开发）

```shell
cd frontend
npm run dev
```

开发服务器默认在 `http://localhost:5173`，需配置 Vite 代理到后端 API。

## API 概览

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/stats` | 系统统计（新闻/图片/贴文数量） |
| GET | `/images/{filename}` | 获取本地图片 |

### 新闻

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/news` | 分页查询新闻列表（支持状态/关键词/来源/时间/类型过滤） |
| GET | `/api/news/{id}` | 获取单条新闻详情（含图片和贴文） |
| DELETE | `/api/news/{id}` | 删除新闻 |

### 流水线

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/pipeline/fetch` | 手动触发新闻采集（仅入库） |
| POST | `/api/pipeline/process/{id}` | 对单条新闻执行完整流程（过滤→入库→生成→发布） |
| POST | `/api/pipeline/process-pending` | 批量处理待处理新闻 |
| POST | `/api/pipeline/news/{id}/generate` | 仅为新闻生成贴文（不发布） |
| POST | `/api/pipeline/news/{id}/publish` | 发布已生成的贴文 |
| POST | `/api/pipeline/news/{id}/retry` | 重试失败的新闻 |
| POST | `/api/pipeline/news/{id}/discard` | 废弃新闻 |

### 调度器

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/scheduler/status` | 查看调度器状态 |
| POST | `/api/scheduler/start` | 启动后台定时采集 |
| POST | `/api/scheduler/stop` | 停止后台定时采集 |
| PUT | `/api/scheduler/interval` | 调整采集间隔 |

### 过滤器

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/filters` | 查看当前启用的过滤器 |
| POST | `/api/filters` | 动态添加过滤器（支持 `keyword` 类型） |
| DELETE | `/api/filters/{name}` | 移除过滤器 |

### 技术面分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/technical/run` | 手动触发一轮技术面检测 |
| GET | `/api/technical/detectors` | 查看启用的检测器 |
| GET | `/api/technical/config` | 查看技术模块配置 |
| PUT | `/api/technical/config` | 更新技术模块配置 |

### 设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings` | 获取所有运行时配置 |
| PUT | `/api/settings` | 批量更新配置 |
| POST | `/api/settings/reload` | 通知服务重新加载配置 |

## 技术面分析

技术面分析引擎从币安 U 本位永续合约市场动态排名交易对，按成交量 × 波动率综合评分选取 Top N 标的，然后运行以下检测器：

### 检测器

| 检测器 | 说明 |
|--------|------|
| **连续涨跌检测器** | 检测连续 N 根阳线/阴线（支持日线、4小时、1小时） |
| **RSI 信号检测器** | 检测 RSI 超买/超卖、MACD 金叉/死叉 |
| **成交量异动检测器** | 检测成交量相对于 N 周期均值的显著放大或缩小 |

检测结果会合并为技术面新闻入库，可与其他新闻一同处理。

### 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_n` | 20 | 监控的交易对数量 |
| `timeframes` | `["1d", "4h"]` | 分析的时间周期 |
| `min_consecutive` | 3 | 连续涨跌的最小根数 |
| `rsi_period` | 14 | RSI 计算周期 |
| `rsi_overbought` | 70 | RSI 超买阈值 |
| `rsi_oversold` | 30 | RSI 超卖阈值 |
| `volume_period` | 20 | 成交量均值计算周期 |
| `volume_multiplier` | 2.0 | 成交量异动倍数阈值 |
| `min_volume_usdt` | 1,000,000 | 最低 24h 成交量（USDT） |
| `min_price_change_pct` | 1.0 | 最低 24h 涨跌幅（%） |
| `interval_seconds` | 300 | 技术面检测间隔 |

## 自定义过滤器

继承 `NewsFilter` 基类并实现 `should_include` 方法：

```python
from news_service.filters import NewsFilter
from news_service.models import NewsDetail

class SourceFilter(NewsFilter):
    def __init__(self, allowed_sources: list[str]):
        self.allowed_sources = [s.lower() for s in allowed_sources]

    async def should_include(self, news: NewsDetail) -> bool:
        return news.source.lower() in self.allowed_sources

    @property
    def name(self) -> str:
        return "source_filter"
```

在 `service.py` 的 `__init__` 中注册，或通过 API 动态添加：

```shell
curl -X POST "http://localhost:8000/api/filters?filter_type=keyword" \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["BTC", "ETH"], "match_source": true}'
```

## 目录结构

```
news-service/
├── news_service/
│   ├── __init__.py
│   ├── main.py                  # 入口（API/CLI 双模式）
│   ├── app.py                   # FastAPI 应用
│   ├── config.py                # 配置管理
│   ├── database.py              # SQLite 操作
│   ├── models.py                # 数据模型（dataclass）
│   ├── news_fetcher.py          # TradingView 新闻采集
│   ├── news.py                  # CLI 入口包装
│   ├── image_downloader.py      # 图片下载
│   ├── content_generator.py     # LLM 内容生成
│   ├── publisher.py             # Binance Square 发布
│   ├── service.py               # 核心编排 + 调度器
│   ├── filters/
│   │   ├── base.py              # 抽象过滤器基类
│   │   └── keyword_filter.py    # 关键词过滤器
│   ├── technical/
│   │   ├── engine.py            # 技术面检测引擎
│   │   ├── models.py            # 技术面数据模型
│   │   ├── market_data.py       # 行情数据（CCXT）
│   │   ├── symbol_ranker.py     # 动态币种排名
│   │   └── detectors/
│   │       ├── base.py          # 检测器基类
│   │       ├── consecutive_candle.py  # 连续涨跌检测
│   │       ├── indicator_signal.py    # RSI/MACD 检测
│   │       └── volume_spike.py        # 成交量异动检测
│   ├── api/
│   │   ├── router.py            # 路由注册
│   │   ├── deps.py              # 依赖注入（单例）
│   │   ├── system.py            # 系统/健康检查
│   │   ├── news.py              # 新闻 CRUD
│   │   ├── pipeline.py          # 采集/处理/发布流水线
│   │   ├── filters.py           # 过滤器管理
│   │   ├── scheduler.py         # 调度器控制
│   │   ├── settings.py          # 运行时配置
│   │   └── technical.py         # 技术面分析
│   └── type_wrapper/
│       ├── __init__.py
│       └── ccxt_wrapper.py      # CCXT 类型安全封装
├── frontend/                    # React + TypeScript + Vite 管理面板
│   ├── src/
│   │   ├── pages/               # 仪表盘、新闻列表、详情、技术面、过滤器、设置
│   │   ├── components/          # 通用组件、布局、新闻、仪表盘、过滤器
│   │   ├── hooks/               # 数据获取 hooks
│   │   ├── services/api.ts      # API 客户端
│   │   └── types/index.ts       # TypeScript 类型定义
│   └── dist/                    # 构建产物
├── images/                      # 下载的新闻图片
├── news.db                      # SQLite 数据库
├── tests/                       # pytest 测试
├── pyproject.toml               # 项目配置
└── uv.lock                      # 依赖锁定
```

## 开发

```shell
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 代码格式化
uv run ruff format

# 类型检查
uv run mypy news_service
```

## 数据流

```
TradingView News API  ──→  NewsFetcher  ──→  Filters  ──→  NewsDatabase
                                                              │
币安 U本位永续合约  ──→  SymbolRanker  ──→  Detectors  ────┘
                                                              │
                                                              ▼
                                                      ContentGenerator
                                                      (LLM 生成贴文)
                                                              │
                                                              ▼
                                                      Publisher
                                                      (Binance Square)
```

## 依赖

- **Python ≥ 3.13**
- **FastAPI + Uvicorn** — REST API 服务
- **httpx** — HTTP 客户端（新闻采集、图片下载）
- **OpenAI SDK** — LLM 贴文生成
- **CCXT** — 行情数据获取
- **binance-service** — Chrome 自动化发布（本地依赖）
- **SQLite** — 数据持久化
- **React 19 + Vite + Tailwind CSS** — 前端管理面板
