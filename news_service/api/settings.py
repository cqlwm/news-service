from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..database import NewsDatabase
from .deps import get_db, get_service_instance

router = APIRouter()

ALLOWED_SETTINGS = {
    "openai_api_key",
    "openai_base_url",
    "openai_model",
    "fetch_interval",
    "max_news_per_fetch",
    "prompt_system",
    "prompt_user_template",
}


@router.get("")
async def get_settings(db: NewsDatabase = Depends(get_db)) -> dict:
    """获取所有运行时配置。"""
    return db.get_all_settings()


@router.put("")
async def update_settings(
    settings: dict[str, str],
    db: NewsDatabase = Depends(get_db),
) -> dict:
    """批量更新运行时配置。"""
    invalid = [k for k in settings if k not in ALLOWED_SETTINGS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid keys: {invalid}. Allowed: {sorted(ALLOWED_SETTINGS)}",
        )
    db.set_settings(settings)
    return {"message": "Settings updated", "updated": list(settings.keys())}


@router.post("/reload")
async def reload_settings() -> dict:
    """通知服务重新加载配置。"""
    service = get_service_instance()
    if service:
        service.reload_config()
        return {"message": "Configuration reloaded"}
    return {"message": "Service not initialized"}
