from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .models import Article

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def render(articles: list[Article]) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("newsletter.html.j2")
    return template.render(
        title="AI & Data Engineering Newsletter",
        articles=articles,
        article_count=len(articles),
        generated_at=datetime.now(tz=timezone.utc).strftime("%B %d, %Y"),
    )
