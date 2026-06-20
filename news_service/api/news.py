from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import NewsDatabase
from .deps import get_db

router = APIRouter()


@router.get("")
async def list_news(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: str | None = Query(None, description="按状态过滤 (pending/generated/published/generation_failed/publish_failed)"),
    keyword: str | None = Query(None, description="按关键词搜索标题和内容"),
    source: str | None = Query(None, description="按来源过滤"),
    date_from: str | None = Query(None, description="起始时间 (ISO 8601)"),
    date_to: str | None = Query(None, description="结束时间 (ISO 8601)"),
    news_type: str | None = Query(None, description="新闻类型 (fundamental/technical)"),
    db: NewsDatabase = Depends(get_db),
) -> dict:
    """分页查询新闻列表。"""
    items, total = db.get_news_list(
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
        source=source,
        date_from=date_from,
        date_to=date_to,
        news_type=news_type,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{news_id}")
async def get_news(
    news_id: str,
    db: NewsDatabase = Depends(get_db),
) -> dict:
    """获取单条新闻详情（含图片和贴文信息）。"""
    news = db.get_news_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    images = db.get_images_by_news_id(news_id)
    post = db.get_post_by_news_id(news_id)

    return {
        **news,
        "images": images,
        "post": post,
    }


@router.delete("/{news_id}")
async def delete_news(
    news_id: str,
    db: NewsDatabase = Depends(get_db),
) -> dict:
    """删除新闻及其关联的图片和贴文记录。"""
    if not db.delete_news(news_id):
        raise HTTPException(status_code=404, detail="News not found")
    return {"message": "News deleted", "news_id": news_id}
