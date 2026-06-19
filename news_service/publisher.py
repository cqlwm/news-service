import logging

logger = logging.getLogger(__name__)


class Publisher:
    def publish(self, base_asset: str, content: str, image_path: str | None = None) -> bool:
        return True
