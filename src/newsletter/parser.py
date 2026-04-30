import logging
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from .models import Article

logger = logging.getLogger(__name__)

SUMMARY_MAX = 280


def parse_entries(source_name: str, raw_entries: list[dict[str, Any]]) -> list[Article]:
    articles = []
    for entry in raw_entries:
        try:
            article = _parse_entry(source_name, entry)
            if article:
                articles.append(article)
        except Exception as exc:
            logger.debug("Skipping malformed entry from %s: %s", source_name, exc)
    return articles


def _parse_entry(source_name: str, entry: dict[str, Any]) -> Article | None:
    url = _get_url(entry)
    title = _get_text(entry, ["title"])
    if not url or not title:
        return None

    summary = _get_summary(entry)
    published = _get_date(entry)

    return Article(
        url=url,
        title=title.strip(),
        summary=summary,
        source=source_name,
        published=published,
        engagement=int(entry.get("engagement") or 0),
    )


def _get_url(entry: dict[str, Any]) -> str:
    for key in ("link", "url", "id"):
        val = entry.get(key, "")
        if val and val.startswith("http"):
            return val
    return ""


def _get_text(entry: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        val = entry.get(key)
        if val:
            if isinstance(val, dict):
                val = val.get("value", "")
            return str(val).strip()
    return ""


def _get_summary(entry: dict[str, Any]) -> str:
    raw = ""
    for key in ("summary", "description", "content", "story_text"):
        val = entry.get(key)
        if val:
            if isinstance(val, list) and val:
                val = val[0].get("value", "")
            raw = str(val)
            break

    text = BeautifulSoup(raw, "lxml").get_text(separator=" ", strip=True) if raw else ""
    return text[:SUMMARY_MAX]


def _get_date(entry: dict[str, Any]) -> datetime:
    # feedparser provides published_parsed as time.struct_time
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    # String date fallback
    for key in ("published", "updated", "created_at"):
        val = entry.get(key)
        if val and isinstance(val, str):
            for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%d"):
                try:
                    return datetime.strptime(val[:19], fmt[: len(val[:19])]).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

    return datetime.now(tz=timezone.utc)
