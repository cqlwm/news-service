from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
IMAGES_DIR = PROJECT_ROOT / "images"
DB_PATH = PROJECT_ROOT / "news.db"

# TradingView API
NEWS_LIST_URL = "https://news-mediator.tradingview.com/news-flow/v2/news"
NEWS_DETAIL_URL = "https://news-mediator.tradingview.com/public/news/v1/story"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# 采集调度
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))
MAX_NEWS_PER_FETCH = int(os.getenv("MAX_NEWS_PER_FETCH", "5"))

# API 服务
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
