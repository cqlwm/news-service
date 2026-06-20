from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from ..config import IMAGES_DIR
from ..database import NewsDatabase
from .deps import get_db

router = APIRouter()


@router.get("/health")
@router.head("/health")
async def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok"}


@router.get("/stats")
async def stats(db: NewsDatabase = Depends(get_db)) -> dict:
    """系统统计信息。"""
    return db.get_stats()


@router.get("/images/{filename}")
async def serve_image(filename: str) -> FileResponse:
    """提供本地图片文件访问。"""
    image_path = IMAGES_DIR / filename
    if not image_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(image_path))
