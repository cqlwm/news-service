from __future__ import annotations

from datetime import datetime, timezone

import pytest

from news_service.database import NewsDatabase


class TestNewsDatabase:
    """测试 NewsDatabase 的 CRUD 操作。"""

    def test_save_and_check_news_exists(self, news_database: NewsDatabase) -> None:
        news_database.save_news(
            news_id="test_001",
            title="Test Title",
            content="Test content",
            source="TestSource",
            url="https://example.com/test",
            published_at=datetime.now(timezone.utc),
        )
        assert news_database.news_exists("test_001") is True
        assert news_database.news_exists("nonexistent") is False

    def test_save_news_duplicate_id(self, news_database: NewsDatabase) -> None:
        """重复 ID 的新闻不应覆盖已有记录（INSERT OR IGNORE）。"""
        published_at = datetime.now(timezone.utc)
        news_database.save_news(
            news_id="dup_001",
            title="Original Title",
            content="Original content",
            source="SourceA",
            url="https://example.com/a",
            published_at=published_at,
        )
        news_database.save_news(
            news_id="dup_001",
            title="Duplicate Title",
            content="Duplicate content",
            source="SourceB",
            url="https://example.com/b",
            published_at=published_at,
        )
        unprocessed = news_database.get_unprocessed_news(limit=10)
        matches = [n for n in unprocessed if n["id"] == "dup_001"]
        assert len(matches) == 1
        assert matches[0]["title"] == "Original Title"

    def test_mark_processed(self, news_database: NewsDatabase) -> None:
        news_database.save_news(
            news_id="proc_001",
            title="To Process",
            content="Content",
            source="Src",
            url="https://example.com/proc",
            published_at=datetime.now(timezone.utc),
        )
        unprocessed_before = news_database.get_unprocessed_news()
        assert any(n["id"] == "proc_001" for n in unprocessed_before)

        news_database.mark_processed("proc_001")
        unprocessed_after = news_database.get_unprocessed_news()
        assert not any(n["id"] == "proc_001" for n in unprocessed_after)

    def test_get_unprocessed_news_returns_only_unprocessed(
        self, news_database: NewsDatabase,
    ) -> None:
        now = datetime.now(timezone.utc)
        news_database.save_news("a", "A", "A", "Src", "url", now)
        news_database.save_news("b", "B", "B", "Src", "url", now)
        news_database.save_news("c", "C", "C", "Src", "url", now)
        news_database.mark_processed("b")

        results = news_database.get_unprocessed_news(limit=10)
        ids = {n["id"] for n in results}
        assert ids == {"a", "c"}

    def test_get_unprocessed_news_respects_limit(
        self, news_database: NewsDatabase,
    ) -> None:
        now = datetime.now(timezone.utc)
        for i in range(10):
            news_database.save_news(
                f"limit_{i}", f"Title {i}", "Content", "Src", "url", now,
            )
        results = news_database.get_unprocessed_news(limit=3)
        assert len(results) == 3

    def test_save_and_get_image(self, news_database: NewsDatabase) -> None:
        news_database.save_news(
            news_id="img_001",
            title="Image Test",
            content="Content",
            source="Src",
            url="https://example.com/img",
            published_at=datetime.now(timezone.utc),
        )
        news_database.save_image("img_001", "https://example.com/img.jpg", "/tmp/img.jpg")
        path = news_database.get_first_image("img_001")
        assert path == "/tmp/img.jpg"

    def test_get_first_image_no_images(self, news_database: NewsDatabase) -> None:
        assert news_database.get_first_image("nonexistent") is None

    def test_news_exists_empty_db(self, news_database: NewsDatabase) -> None:
        assert news_database.news_exists("anything") is False

    def test_published_at_none(self, news_database: NewsDatabase) -> None:
        """published_at 为 None 时应能正常保存。"""
        news_database.save_news(
            news_id="null_date",
            title="No Date",
            content="Content",
            source="Src",
            url="https://example.com/null",
            published_at=None,
        )
        assert news_database.news_exists("null_date") is True
