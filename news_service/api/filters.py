from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..filters import NewsFilter, KeywordFilter
from .deps import get_service
from ..service import NewsService

router = APIRouter()


@router.get("")
async def list_filters(
    service: NewsService = Depends(get_service),
) -> list[dict]:
    """查看当前启用的过滤器列表。"""
    return [
        {
            "name": f.name,
            "type": f.__class__.__name__,
        }
        for f in service.filters
    ]


@router.post("")
async def add_filter(
    filter_type: str,
    config: dict,
    service: NewsService = Depends(get_service),
) -> dict:
    """动态添加过滤器。

    支持类型：
    - keyword: {"keywords": ["BTC", "ETH"], "match_source": true}
    """
    if filter_type == "keyword":
        new_filter: NewsFilter = KeywordFilter(
            keywords=config.get("keywords", []),
            match_source=config.get("match_source", True),
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported filter type: {filter_type}. Supported: keyword",
        )

    service.filters.append(new_filter)
    return {"message": f"Filter '{new_filter.name}' added", "filter": filter_type}


@router.delete("/{filter_name}")
async def remove_filter(
    filter_name: str,
    service: NewsService = Depends(get_service),
) -> dict:
    """移除指定名称的过滤器。"""
    for i, f in enumerate(service.filters):
        if f.name == filter_name:
            service.filters.pop(i)
            return {"message": f"Filter '{filter_name}' removed"}
    raise HTTPException(status_code=404, detail=f"Filter '{filter_name}' not found")
