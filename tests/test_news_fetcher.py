from __future__ import annotations

import logging

import pytest

from news_service.config import NEWS_LIST_URL, NEWS_DETAIL_URL
from news_service.news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_fetch_news_list_returns_ids() -> None:
    """验证列表 API 能正常返回新闻列表，且每个 ID 非空。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) > 0, "列表 API 应返回至少一条新闻"
        for item in items:
            assert isinstance(item.id, str) and item.id, f"新闻 ID 应为非空字符串: {item.id!r}"
            assert isinstance(item.title, str) and item.title, f"标题应为非空字符串: {item.title!r}"
            assert isinstance(item.published, int) and item.published > 0
            assert isinstance(item.provider.id, str) and item.provider.id
            assert isinstance(item.provider.name, str) and item.provider.name
            if item.link is None:
                logger.warning(f"新闻 {item.id} 缺少可选字段 link")
    finally:
        await fetcher.close()


@pytest.mark.asyncio
async def test_fetch_news_list_response_structure() -> None:
    """验证列表 API 返回的 items 结构包含 README 中声明的核心字段。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) > 0

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(NEWS_LIST_URL, params={
                "filter": ["lang:zh-Hans", "market:crypto,stock"],
                "client": "screener",
                "streaming": "true",
                "user_prostatus": "non_pro",
            })
            resp.raise_for_status()
            data = resp.json()

        # 验证顶层结构
        assert "items" in data, "响应应包含 items 字段"
        assert isinstance(data["items"], list), "items 应为数组"
        assert len(data["items"]) > 0, "items 不应为空"

        # streaming 和 pagination 是稳定字段
        assert "streaming" in data, "响应应包含 streaming 字段"
        assert "pagination" in data, "响应应包含 pagination 字段"
        assert "cursor" in data["pagination"], "pagination 应包含 cursor"

        # 验证每项的核心字段
        raw_item = data["items"][0]
        assert "id" in raw_item, "item 应包含 id"
        assert "title" in raw_item, "item 应包含 title"
        assert "published" in raw_item, "item 应包含 published"
        assert "provider" in raw_item, "item 应包含 provider"

        # provider 结构验证
        provider = raw_item["provider"]
        assert isinstance(provider, dict), "provider 应为对象"
        assert "id" in provider, "provider 应包含 id"
        assert "name" in provider, "provider 应包含 name"

        # 可选字段检查
        if "link" not in raw_item:
            logger.warning(f"新闻 {raw_item['id']} 缺少可选字段 link")
        if "urgency" not in raw_item:
            logger.warning(f"新闻 {raw_item['id']} 缺少可选字段 urgency")
        if "storyPath" not in raw_item:
            logger.warning(f"新闻 {raw_item['id']} 缺少可选字段 storyPath")
    finally:
        await fetcher.close()


@pytest.mark.asyncio
async def test_fetch_news_detail_returns_full_structure() -> None:
    """验证详情 API 能正常返回新闻详情，且包含必要字段。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) > 0

        detail = await fetcher.fetch_news_detail(items[0].id)
        assert detail is not None, f"详情 API 应返回数据 (id={items[0].id})"

        # 必选字段
        assert isinstance(detail.id, str) and detail.id, "id 应为非空字符串"
        assert isinstance(detail.title, str) and detail.title, "title 应为非空字符串"
        assert isinstance(detail.content, str), "content 应为字符串"
        assert isinstance(detail.source, str), "source 应为字符串"
        assert isinstance(detail.url, str), "url 应为字符串"
        assert isinstance(detail.images, list), "images 应为数组"

        # 可选字段提示
        if not detail.source:
            logger.warning(f"新闻 {detail.id} 的 source 为空")
        if not detail.url:
            logger.warning(f"新闻 {detail.id} 的 url 为空")
        if detail.published_at is None:
            logger.warning(f"新闻 {detail.id} 的 published_at 为 None")
    finally:
        await fetcher.close()


@pytest.mark.asyncio
async def test_fetch_news_detail_raw_response_matches_readme() -> None:
    """直接请求详情 API，验证原始响应结构与 README 中声明的字段一致。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) > 0

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(NEWS_DETAIL_URL, params={
                "id": items[0].id,
                "lang": "zh-Hans",
                "user_prostatus": "non_pro",
            })
            resp.raise_for_status()
            raw = resp.json()

        # 必选字段
        required_fields = {
            "short_description", "ast_description", "language", "tags",
            "id", "title", "published", "urgency",
            "related_symbols", "story_path", "provider",
        }
        missing = required_fields - set(raw.keys())
        assert not missing, f"详情响应缺少必选字段: {missing}"

        # 可选字段提示
        optional_fields = {"is_flash", "link"}
        for field in optional_fields:
            if field not in raw:
                logger.warning(f"新闻 {items[0].id} 的详情响应缺少可选字段 {field}")

        # 验证 provider 结构
        provider = raw["provider"]
        assert isinstance(provider, dict), "provider 应为对象"
        assert "id" in provider, "provider 应包含 id"
        assert "name" in provider, "provider 应包含 name"
        assert "logo_id" in provider, "provider 应包含 logo_id"
        if "url" not in provider:
            logger.warning(f"新闻 {items[0].id} 的 provider 缺少可选字段 url")

        # 验证 ast_description 结构
        ast = raw["ast_description"]
        assert isinstance(ast, dict), "ast_description 应为对象"
        assert ast.get("type") == "root", "ast_description.type 应为 root"
        assert "children" in ast, "ast_description 应包含 children"
        assert isinstance(ast["children"], list), "ast_description.children 应为数组"

        # 验证 tags 结构
        assert isinstance(raw["tags"], list), "tags 应为数组"
        if raw["tags"]:
            tag = raw["tags"][0]
            assert "title" in tag, "tag 应包含 title"
            assert "args" in tag, "tag 应包含 args"

        # 验证 published 为 Unix 时间戳
        assert isinstance(raw["published"], int), "published 应为整数 (Unix 时间戳)"
        assert raw["published"] > 0, "published 应为正数"

        # 验证 related_symbols 结构
        assert isinstance(raw["related_symbols"], list), "related_symbols 应为数组"
    finally:
        await fetcher.close()


@pytest.mark.asyncio
async def test_fetch_news_detail_ast_description_extraction() -> None:
    """验证从 ast_description 树中能正确提取纯文本内容。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) > 0

        detail = await fetcher.fetch_news_detail(items[0].id)
        assert detail is not None

        assert len(detail.content) > 0, "content 不应为空"
        # 不应包含 HTML 标签
        assert "<" not in detail.content or ">" not in detail.content, \
            "content 不应包含 HTML 标签"
    finally:
        await fetcher.close()


@pytest.mark.asyncio
async def test_fetch_news_detail_published_at_format() -> None:
    """验证 published_at 被正确转换为 ISO 8601 格式。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) > 0

        detail = await fetcher.fetch_news_detail(items[0].id)
        assert detail is not None
        assert detail.published_at is not None, "published_at 不应为 None"

        published = detail.published_at
        assert "T" in published, f"published_at 应包含 T 分隔符: {published}"
        assert published.endswith("+00:00"), f"published_at 应为 UTC 时区: {published}"
    finally:
        await fetcher.close()


@pytest.mark.asyncio
async def test_fetch_multiple_news_details() -> None:
    """验证批量获取多条新闻详情均能成功。"""
    fetcher = NewsFetcher(NEWS_LIST_URL, NEWS_DETAIL_URL)
    try:
        items = await fetcher.fetch_news_list()
        assert len(items) >= 3, "至少需要 3 条新闻用于批量测试"

        for item in items[:3]:
            detail = await fetcher.fetch_news_detail(item.id)
            assert detail is not None, f"详情获取失败: {item.id}"
            assert detail.id == item.id, f"返回的 id 不匹配: {detail.id} != {item.id}"
            assert detail.title, f"标题为空: {item.id}"
            assert detail.source, f"来源为空: {item.id}"
    finally:
        await fetcher.close()
