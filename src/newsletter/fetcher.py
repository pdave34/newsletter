import logging
import time
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup

from .sources import SOURCES, Source

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0; +https://github.com/newsletter)"
}
TIMEOUT = 15.0


def fetch_all() -> dict[str, list[dict[str, Any]]]:
    """Fetch raw entries from all sources. Returns {source_name: [raw_entries]}."""
    results: dict[str, list[dict[str, Any]]] = {}
    for source in SOURCES:
        try:
            if source.type == "rss":
                entries = _fetch_rss(source)
            elif source.type == "api":
                entries = _fetch_api(source)
            elif source.type == "scrape":
                entries = _fetch_scrape(source)
            else:
                entries = []
            results[source.name] = entries
            logger.info("Fetched %d entries from %s", len(entries), source.name)
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", source.name, exc)
            results[source.name] = []
        time.sleep(0.5)
    return results


def _fetch_rss(source: Source) -> list[dict[str, Any]]:
    feed = feedparser.parse(source.url)
    return [dict(entry) for entry in feed.entries]


def _fetch_api(source: Source) -> list[dict[str, Any]]:
    with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        resp = client.get(source.url)
        resp.raise_for_status()
        data = resp.json()

    if "hn.algolia" in source.url:
        return _parse_hn(data)
    if "huggingface.co/api/daily_papers" in source.url:
        return _parse_hf_papers(data)
    return []


def _parse_hn(data: dict[str, Any]) -> list[dict[str, Any]]:
    hits = data.get("hits", [])
    return [
        {
            "title": h.get("title", ""),
            "link": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "summary": h.get("story_text") or "",
            "published": h.get("created_at", ""),
            "engagement": (h.get("points") or 0) + (h.get("num_comments") or 0),
        }
        for h in hits
        if h.get("title")
    ]


def _parse_hf_papers(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for item in data:
        paper = item.get("paper", {})
        title = paper.get("title", "")
        arxiv_id = paper.get("id", "")
        if not title or not arxiv_id:
            continue
        entries.append(
            {
                "title": title,
                "link": f"https://huggingface.co/papers/{arxiv_id}",
                "summary": paper.get("summary", ""),
                "published": item.get("publishedAt", ""),
                "engagement": paper.get("upvotes") or 0,
            }
        )
    return entries


def _fetch_scrape(source: Source) -> list[dict[str, Any]]:
    with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        resp = client.get(source.url)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "lxml")
    entries: list[dict[str, Any]] = []

    if "anthropic.com" in source.url:
        entries = _scrape_anthropic(soup)
    elif "deepmind" in source.url:
        entries = _scrape_deepmind(soup)
    elif "eugeneyan.com" in source.url:
        entries = _scrape_eugeneyan(soup)

    return entries


def _scrape_anthropic(soup: BeautifulSoup) -> list[dict[str, Any]]:
    entries = []
    import re as _re

    for a in soup.find_all("a", href=_re.compile(r"^/news/[a-z0-9]")):
        href = "https://www.anthropic.com" + a["href"]
        title_tag = a.find(["h2", "h3", "h4"])
        title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)[:100]
        summary_tag = a.find("p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        time_tag = a.find("time")
        published = time_tag.get_text(strip=True) if time_tag else ""
        if title:
            entries.append(
                {"title": title, "link": href, "summary": summary, "published": published}
            )
    return entries


def _scrape_deepmind(soup: BeautifulSoup) -> list[dict[str, Any]]:
    seen: set[str] = set()
    entries = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        nav_name = a.get("data-event-nav-name", "")
        if "/blog/" not in href or href == "/blog/" or not nav_name or href in seen:
            continue
        seen.add(href)
        # nav_name is like "Category - Subcategory - Title", take the last part
        title = nav_name.split(" - ")[-1].strip()
        full_href = "https://deepmind.google" + href if not href.startswith("http") else href
        entries.append({"title": title, "link": full_href, "summary": ""})
        if len(entries) >= 20:
            break
    return entries


def _scrape_eugeneyan(soup: BeautifulSoup) -> list[dict[str, Any]]:
    entries = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/writing/" not in href or href in ("/writing/", "/tag/writing/"):
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        full_href = "https://eugeneyan.com" + href if not href.startswith("http") else href
        entries.append({"title": title, "link": full_href, "summary": ""})
        if len(entries) >= 20:
            break
    return entries
