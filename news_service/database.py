import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


class NewsDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
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
                    processed INTEGER DEFAULT 0,
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
            """)
    
    def news_exists(self, news_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM news WHERE id = ?", (news_id,))
            return cursor.fetchone() is not None
    
    def save_news(self, news_id: str, title: str, content: str, 
                  source: str, url: str, published_at: datetime | None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO news 
                (id, title, content, source, url, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (news_id, title, content, source, url, published_at))
    
    def save_image(self, news_id: str, image_url: str, local_path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO images (news_id, image_url, local_path)
                VALUES (?, ?, ?)
            """, (news_id, image_url, local_path))
    
    def get_first_image(self, news_id: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT local_path FROM images WHERE news_id = ? ORDER BY id LIMIT 1",
                (news_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_unprocessed_news(self, limit: int = 5) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM news WHERE processed = 0 ORDER BY published_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_processed(self, news_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE news SET processed = 1 WHERE id = ?",
                (news_id,)
            )
