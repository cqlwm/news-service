from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..database import NewsDatabase
from ..service import NewsService
from .deps import get_db, get_service

router = APIRouter()


@router.post("/fetch")
async def trigger_fetch(
    service: NewsService = Depends(get_service),
) -> dict:
    """手动触发一轮新闻采集（仅入库，不处理）。"""
    new_ids = await service.fetch_news()
    return {"message": f"Fetched {len(new_ids)} new news", "new_news_ids": new_ids}


@router.post("/process/{news_id}")
async def process_single_news(
    news_id: str,
    service: NewsService = Depends(get_service),
) -> dict:
    """对单条新闻执行完整处理流程（过滤→入库→下载图片→生成贴文→发布）。"""
    success = await service.process_news(news_id)
    if not success:
        # 检查新闻是否存在（可能被过滤，也可能是根本不存在）
        news_detail = await service.fetcher.fetch_news_detail(news_id)
        if not news_detail:
            raise HTTPException(status_code=404, detail="News not found")
        return {"message": "News processed but not published (filtered or failed)", "news_id": news_id, "published": False}
    return {"message": "News processed and published", "news_id": news_id, "published": True}


@router.post("/process-pending")
async def process_pending_news(
    limit: int = 5,
    service: NewsService = Depends(get_service),
) -> dict:
    """批量处理待处理新闻。"""
    results = await service.process_pending_news(limit=limit)
    return {
        "message": f"Processed {len(results)} pending news",
        "results": results,
    }


@router.post("/news/{news_id}/generate")
async def generate_post(
    news_id: str,
    service: NewsService = Depends(get_service),
    db: NewsDatabase = Depends(get_db),
) -> dict:
    """仅为新闻生成贴文内容（不发布）。"""
    news = db.get_news_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    result = await service.generate_post_only(news_id)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="无法生成贴文：LLM 未配置。请在设置页面配置 API Key 和 Model。",
        )

    base_asset, content = result
    return {
        "message": "Post generated",
        "news_id": news_id,
        "base_asset": base_asset,
        "content": content,
    }


@router.post("/news/{news_id}/retry")
async def retry_news(
    news_id: str,
    service: NewsService = Depends(get_service),
) -> dict:
    """重试失败的新闻（仅限 GENERATION_FAILED / PUBLISH_FAILED）。"""
    success = await service.retry_news(news_id)
    if not success:
        raise HTTPException(status_code=400, detail="Retry failed")
    return {"message": "Retry successful", "news_id": news_id, "published": True}


@router.post("/news/{news_id}/discard")
async def discard_news(
    news_id: str,
    service: NewsService = Depends(get_service),
) -> dict:
    """废弃新闻（终态）。仅允许在失败状态下废弃。"""
    success = service.discard_news(news_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot discard news: not found or invalid status")
    return {"message": "News discarded", "news_id": news_id}


@router.post("/news/{news_id}/publish")
async def publish_post(
    news_id: str,
    service: NewsService = Depends(get_service),
    db: NewsDatabase = Depends(get_db),
) -> dict:
    """发布已生成的贴文。"""
    post = db.get_post_by_news_id(news_id)
    if not post:
        raise HTTPException(status_code=400, detail="No generated post found. Generate first.")

    success = await service.publish_post(news_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to publish post")

    return {"message": "Post published", "news_id": news_id}
