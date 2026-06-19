import httpx
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ImageDownloader:
    def __init__(self, images_dir: Path):
        self.images_dir = images_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def download_image(self, image_url: str, news_id: str, index: int = 0) -> str | None:
        try:
            ext = self._get_extension(image_url)
            filename = f"{news_id.replace(':', '_')}_{index}{ext}"
            local_path = self.images_dir / filename
            
            response = await self.client.get(image_url)
            response.raise_for_status()
            
            local_path.write_bytes(response.content)
            logger.info(f"Downloaded image: {local_path}")
            return str(local_path)
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
            return None
    
    def _get_extension(self, url: str) -> str:
        url_lower = url.lower()
        if ".png" in url_lower:
            return ".png"
        elif ".gif" in url_lower:
            return ".gif"
        else:
            return ".jpg"
    
    async def close(self):
        await self.client.aclose()
