# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the full pipeline (fetches, ranks, sends email)
uv run python -m newsletter.main

# Or via the script entry point
uv run newsletter
```

There are no tests or linter configs in this project.

## Architecture

Linear pipeline in `main.py`:

```
prune_old (SQLite) → fetch_all → parse_entries → deduplicate → rank → limit → render → send → mark_seen
```

**Stage responsibilities:**
- `sources.py` — static list of `Source(name, url, type)` objects; `type` is `"rss"`, `"api"`, or `"scrape"`
- `fetcher.py` — dispatches by source type; RSS via `feedparser`, JSON APIs via `httpx`, HTML via `BeautifulSoup`; returns `dict[source_name, list[raw_dict]]`
- `parser.py` — converts raw dicts to `Article` dataclasses; handles missing fields and date parsing
- `filter.py` — dedup by URL against SQLite seen set, keyword-score articles, sort by `(-score, -published)`, cap at `MAX_ARTICLES`
- `storage.py` — SQLite `seen_articles` table; `get_seen_urls`, `mark_seen`, `prune_old(days=180)`
- `renderer.py` — Jinja2 renders `templates/newsletter.html.j2`
- `sender.py` — `smtplib` STARTTLS to Gmail (or any SMTP)
- `config.py` — loads `.env` via `python-dotenv`; exposes `SMTP_*`, `RECIPIENT_EMAILS` (list), `SENDER_NAME`, `DB_PATH`, `MAX_ARTICLES`

**Data flow types:**
- `fetcher` output: `dict[str, list[dict[str, Any]]]`
- After `parser`: `list[Article]` — fields: `url`, `title`, `summary` (280 char max, HTML-stripped), `source`, `published: datetime`, `score: int`

## Key scraping details

Several sites have no working RSS; these use `"scrape"` type with custom per-site functions in `fetcher.py`:

- **Anthropic** (`/news`): finds `<a href=re("/news/[a-z0-9]")>`, extracts `h2/h3/h4` title, `<p>` summary, `<time>` date
- **DeepMind** (`/blog/`): reads `data-event-nav-name` attribute on `<a>` tags (format: `"Cat - Sub - Title"`), splits on ` - ` for title
- **Eugene Yan** (`/writing/`): finds `<a href>` containing `/writing/` (excluding the index path)

**API sources** (`"api"` type) parsed by URL in `_fetch_api()`:
- HuggingFace Daily Papers: `huggingface.co/api/daily_papers?limit=20`
- Hacker News: Algolia search API

## Adding sources

1. Add a `Source(...)` entry to `sources.py`
2. If `type="scrape"`, add a `_scrape_<site>()` function in `fetcher.py` and dispatch it in `_fetch_scrape()`
3. If `type="api"`, add a `_parse_<site>()` function and dispatch it in `_fetch_api()`
4. To tune relevance ranking, add keywords to `KEYWORDS` in `filter.py`

## Scheduling

GitHub Actions cron in `.github/workflows/newsletter.yml`. SQLite DB is persisted across runs via `actions/cache`. Secrets required: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `RECIPIENT_EMAILS`, `SENDER_NAME`.
