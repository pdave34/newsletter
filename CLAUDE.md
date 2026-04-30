# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Principles

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Commands

```bash
# Install dependencies
uv sync

# Run the full pipeline (fetches, ranks, sends email)
uv run python -m newsletter.main

# Or via the script entry point
uv run newsletter
```

```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

Ruff is configured in `pyproject.toml`: 100-char line limit, `E`/`F`/`I` rules (pycodestyle, pyflakes, isort).

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
- `config.py` — loads `.env` via `python-dotenv`; exposes `SMTP_*`, `RECIPIENT_EMAILS` (list), `SENDER_NAME`, `DB_PATH`, `MAX_ARTICLES` (default 3), `MAX_AGE_DAYS` (default 30)

**Data flow types:**
- `fetcher` output: `dict[str, list[dict[str, Any]]]`
- After `parser`: `list[Article]` — fields: `url`, `title`, `summary` (280 char max, HTML-stripped), `source`, `published: datetime`, `engagement: int`, `score: int`

**Scoring breakdown** (all additive):
| Signal | Range | Detail |
|---|---|---|
| Keywords | 0–N | +1 per keyword match in title+summary |
| Recency | 0, 1, 3 | +3 if ≤7 days old, +1 if ≤30 days |
| Source weight | 1–3 | defined in `SOURCE_WEIGHTS` in `filter.py`; default 1 |
| Engagement | 0–3 | `min(points+comments // 50, 3)`; HN and HF papers only |

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
