from __future__ import annotations

import enum
import sqlite3
from datetime import datetime
from pathlib import Path


def _adapt_datetime(val: datetime) -> str:
    return val.isoformat()


sqlite3.register_adapter(datetime, _adapt_datetime)


class NewsStatus(str, enum.Enum):
    PENDING = "pending"
    POST_GENERATED = "generated"
    PUBLISHED = "published"
    GENERATION_FAILED = "generation_failed"
    PUBLISH_FAILED = "publish_failed"
    DISCARDED = "discarded"


class NewsDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS news (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    source TEXT,
                    url TEXT,
                    published_at TIMESTAMP,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (news_id) REFERENCES news(id)
                );

                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id TEXT NOT NULL UNIQUE,
                    base_asset TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (news_id) REFERENCES news(id)
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS technical_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self._migrate_add_column(conn, "news", "status", "TEXT DEFAULT 'pending'")
            self._migrate_add_column(conn, "news", "retry_count", "INTEGER DEFAULT 0")
            self._migrate_add_column(conn, "news", "error_message", "TEXT")
            self._migrate_add_column(conn, "news", "type", "TEXT DEFAULT 'fundamental'")
            self._migrate_add_column(conn, "news", "pattern_type", "TEXT")

    @staticmethod
    def _migrate_add_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass

    # ── 新闻 CRUD ──────────────────────────────────────────

    def news_exists(self, news_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM news WHERE id = ?", (news_id,))
            return cursor.fetchone() is not None

    def save_news(
        self,
        news_id: str,
        title: str,
        content: str,
        source: str,
        url: str,
        published_at: datetime | None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO news (id, title, content, source, url, published_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (news_id, title, content, source, url, published_at),
            )

    def save_technical_news(
        self,
        news_id: str,
        title: str,
        content: str,
        source: str,
        url: str,
        published_at: datetime | None,
        pattern_type: str = "",
    ) -> None:
        """保存技术面新闻。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO news (id, title, content, source, url, published_at, type, pattern_type) "
                "VALUES (?, ?, ?, ?, ?, ?, 'technical', ?)",
                (news_id, title, content, source, url, published_at, pattern_type),
            )

    def get_news_list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        keyword: str | None = None,
        source: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        news_type: str | None = None,
    ) -> tuple[list[dict], int]:
        conditions: list[str] = []
        params: list[str | int] = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if keyword:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if source:
            conditions.append("source = ?")
            params.append(source)
        if date_from:
            conditions.append("published_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("published_at <= ?")
            params.append(date_to)
        if news_type:
            conditions.append("type = ?")
            params.append(news_type)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT COUNT(*) FROM news {where_clause}", params)
            total: int = cursor.fetchone()[0]
            offset = (page - 1) * page_size
            cursor = conn.execute(
                f"SELECT * FROM news {where_clause} ORDER BY published_at DESC LIMIT ? OFFSET ?",
                [*params, page_size, offset],
            )
            items = [dict(row) for row in cursor.fetchall()]
        return items, total

    def get_news_by_id(self, news_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_news(self, news_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
            conn.execute("DELETE FROM images WHERE news_id = ?", (news_id,))
            conn.execute("DELETE FROM posts WHERE news_id = ?", (news_id,))
            return cursor.rowcount > 0

    def mark_processed(self, news_id: str) -> None:
        self.update_news_status(news_id, NewsStatus.PUBLISHED)

    def update_news_status(self, news_id: str, status: NewsStatus, error_message: str | None = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            if error_message:
                conn.execute(
                    "UPDATE news SET status = ?, retry_count = retry_count + 1, error_message = ? WHERE id = ?",
                    (status.value, error_message, news_id),
                )
            else:
                conn.execute("UPDATE news SET status = ?, error_message = NULL WHERE id = ?", (status.value, news_id))

    def get_unprocessed_news(self, limit: int = 5) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM news WHERE status = 'pending' ORDER BY published_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_failed_news(self, limit: int = 20) -> list[dict]:
        """获取所有失败状态的新闻。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM news WHERE status IN ('generation_failed', 'publish_failed') ORDER BY published_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ── 图片 ───────────────────────────────────────────────

    def save_image(self, news_id: str, image_url: str, local_path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO images (news_id, image_url, local_path) VALUES (?, ?, ?)",
                (news_id, image_url, local_path),
            )

    def get_images_by_news_id(self, news_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM images WHERE news_id = ? ORDER BY id", (news_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_first_image(self, news_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT local_path FROM images WHERE news_id = ? ORDER BY id LIMIT 1",
                (news_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    # ── 贴文 ───────────────────────────────────────────────

    def save_post(self, news_id: str, base_asset: str, content: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO posts (news_id, base_asset, content) VALUES (?, ?, ?)",
                (news_id, base_asset, content),
            )

    def get_post_by_news_id(self, news_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM posts WHERE news_id = ?", (news_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def mark_post_published(self, news_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE posts SET status = 'published', published_at = ? WHERE news_id = ?",
                (datetime.utcnow(), news_id),
            )

    # ── 统计 ───────────────────────────────────────────────

    def get_stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
            by_status: dict[str, int] = {}
            for row in conn.execute("SELECT status, COUNT(*) FROM news GROUP BY status"):
                by_status[row[0]] = row[1]
            total_images = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
            total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
            published_posts = conn.execute(
                "SELECT COUNT(*) FROM posts WHERE status = 'published'"
            ).fetchone()[0]
        return {
            "total_news": total,
            "news_by_status": by_status,
            "total_images": total_images,
            "total_posts": total_posts,
            "published_posts": published_posts,
        }

    # ── 设置 ───────────────────────────────────────────────

    def get_setting(self, key: str) -> str | None:
        """获取单条配置。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all_settings(self) -> dict[str, str]:
        """获取全部配置。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM settings")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def set_setting(self, key: str, value: str) -> None:
        """设置单条配置（INSERT OR REPLACE）。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.utcnow()),
            )

    def set_settings(self, settings: dict[str, str]) -> None:
        """批量设置配置。"""
        now = datetime.utcnow()
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                [(k, v, now) for k, v in settings.items()],
            )

    def delete_setting(self, key: str) -> None:
        """删除单条配置。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))
