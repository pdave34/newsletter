import logging
import os
import sqlite3
from datetime import datetime, timezone, timedelta

from .models import Article

logger = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS seen_articles (
    url TEXT PRIMARY KEY,
    title TEXT,
    source TEXT,
    seen_at TEXT
)
"""


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE)
    conn.commit()
    return conn


def get_seen_urls(db_path: str) -> set[str]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT url FROM seen_articles").fetchall()
    return {row[0] for row in rows}


def mark_seen(db_path: str, articles: list[Article]) -> None:
    now = datetime.now(tz=timezone.utc).isoformat()
    rows = [(a.url, a.title, a.source, now) for a in articles]
    with _connect(db_path) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO seen_articles (url, title, source, seen_at) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    logger.info("Marked %d articles as seen", len(rows))


def prune_old(db_path: str, days: int = 180) -> None:
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()
    with _connect(db_path) as conn:
        deleted = conn.execute(
            "DELETE FROM seen_articles WHERE seen_at < ?", (cutoff,)
        ).rowcount
        conn.commit()
    if deleted:
        logger.info("Pruned %d old articles from seen_articles", deleted)
