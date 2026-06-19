from binance_service.binance_poster import create_post
import logging

logger = logging.getLogger(__name__)


class Publisher:
    def publish(self, base_asset: str, content: str, image_path: str | None = None) -> bool:
        try:
            logger.info(f"Publishing post: {base_asset} - {content[:50]}...")
            create_post(base_asset, content, image_path)
            return True
        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return False
