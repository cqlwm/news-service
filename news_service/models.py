from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Provider:
    """新闻来源方信息。"""
    id: str
    name: str
    logo_id: str
    url: str | None = None


@dataclass
class NewsListItem:
    """新闻列表中的单条新闻项。"""
    id: str
    title: str
    published: int
    urgency: int
    story_path: str
    provider: Provider
    link: str | None = None


@dataclass
class NewsListResponse:
    """新闻列表 API 完整响应。"""
    items: list[NewsListItem]
    streaming: dict[str, str] | None = None
    pagination: dict[str, str] | None = None


@dataclass
class AstNode:
    """AST 描述树的节点。"""
    type: str
    children: list[Any] = field(default_factory=list)


@dataclass
class TagArg:
    """标签参数。"""
    id: str
    value: str


@dataclass
class Tag:
    """新闻标签。"""
    title: str
    args: list[TagArg] = field(default_factory=list)


@dataclass
class RelatedSymbol:
    """相关交易品种。"""
    symbol: str
    logoid: str | None = None


@dataclass
class NewsDetailRaw:
    """新闻详情 API 原始响应结构。"""
    id: str
    title: str
    short_description: str
    ast_description: AstNode
    language: str
    tags: list[Tag]
    published: int
    urgency: int
    related_symbols: list[RelatedSymbol]
    story_path: str
    provider: Provider
    link: str | None = None
    is_flash: bool | None = None


@dataclass
class NewsDetail:
    """NewsFetcher 处理后返回的新闻详情。"""
    id: str
    title: str
    content: str
    source: str
    url: str
    published_at: str | None
    images: list[str] = field(default_factory=list)
