import argparse
import logging

from . import config
from .fetcher import fetch_all
from .filter import deduplicate, filter_recent, limit, rank
from .models import Article
from .parser import parse_entries
from .renderer import render
from .sender import send
from .storage import get_seen_urls, mark_seen, prune_old

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prune",
        nargs="?",
        const=0,
        type=int,
        metavar="DAYS",
        help=(
            "Clear seen-articles DB. Omit DAYS to wipe all; "
            "pass N to remove entries older than N days."
        ),
    )
    args = parser.parse_args()

    if args.prune is not None:
        prune_old(config.DB_PATH, days=args.prune)
        logger.info("Pruning complete")
        return

    logger.info("Starting newsletter pipeline")

    # 1. Prune stale dedup state
    prune_old(config.DB_PATH)

    # 2. Fetch raw entries from all sources
    raw = fetch_all()

    # 3. Parse into Article objects
    all_articles: list[Article] = []
    for source_name, entries in raw.items():
        all_articles.extend(parse_entries(source_name, entries))
    logger.info("Parsed %d total articles", len(all_articles))

    # 4. Drop articles older than MAX_AGE_DAYS
    recent = filter_recent(all_articles, config.MAX_AGE_DAYS)
    logger.info("%d articles within 30 days", len(recent))

    # 5. Deduplicate against seen history
    seen_urls = get_seen_urls(config.DB_PATH)
    fresh = deduplicate(recent, seen_urls)
    logger.info("%d new articles after deduplication", len(fresh))

    if not fresh:
        logger.info("No new articles — skipping email send")
        return

    # 6. Rank and limit
    ranked = rank(fresh)
    top = limit(ranked, config.MAX_ARTICLES)
    logger.info("Selected top %d articles for newsletter", len(top))

    # 7. Render HTML
    html = render(top)

    # 7. Send email
    send(
        html=html,
        recipients=config.RECIPIENT_EMAILS,
        smtp_host=config.SMTP_HOST,
        smtp_port=config.SMTP_PORT,
        smtp_user=config.SMTP_USER,
        smtp_password=config.SMTP_PASSWORD,
        sender_name=config.SENDER_NAME,
    )

    # 8. Mark sent articles as seen
    mark_seen(config.DB_PATH, top)
    logger.info("Newsletter pipeline complete")


if __name__ == "__main__":
    main()
