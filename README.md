# AI & Data Newsletter

Weekly email digest of AI/Data engineering news. Scrapes 15 sources, deduplicates, ranks by relevance, and sends an HTML email every Monday.

**Topics:** OpenAI, Anthropic, Snowflake, Databricks, AWS, Azure, LLMs, open-source models, data engineering, MLOps, applied ML, statistics.

## Setup

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
uv sync
cp .env.example .env
```

Edit `.env` with your credentials:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password   # Gmail: myaccount.google.com/apppasswords
RECIPIENT_EMAILS=you@example.com  # comma-separated for multiple
```

## Run

```bash
uv run python -m newsletter.main
```

## Scheduling (GitHub Actions)

Runs automatically every Monday at 12:00 PM UTC via `.github/workflows/newsletter.yml`.

Add these secrets in your repo under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password |
| `RECIPIENT_EMAILS` | comma-separated recipient list |

Trigger manually anytime via **Actions → Newsletter → Run workflow**.

## Development

```bash
uv run ruff check src/   # lint
uv run ruff format src/  # format
```

100-char line limit, import sorting enforced.

## Customization

- **Add/remove sources:** edit `src/newsletter/sources.py`
- **Add keywords:** edit the `KEYWORDS` list in `src/newsletter/filter.py`
- **Change article limit:** set `MAX_ARTICLES` in `.env` (default: 20)
- **Change schedule:** edit the `cron` expression in `.github/workflows/newsletter.yml`
