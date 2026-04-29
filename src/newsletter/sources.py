from dataclasses import dataclass
from typing import Literal

SourceType = Literal["rss", "api", "scrape"]


@dataclass
class Source:
    name: str
    url: str
    type: SourceType


SOURCES: list[Source] = [
    # RSS feeds
    Source("OpenAI Blog", "https://openai.com/blog/rss.xml", "rss"),
    Source("HuggingFace Blog", "https://huggingface.co/blog/feed.xml", "rss"),
    Source("Last Week in AI", "https://lastweekin.ai/feed", "rss"),
    Source("AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed/", "rss"),
    Source("Azure Blog", "https://azure.microsoft.com/en-us/blog/feed/", "rss"),
    Source("Microsoft AI Blog", "https://blogs.microsoft.com/ai/feed/", "rss"),
    Source("Databricks Blog", "https://www.databricks.com/feed", "rss"),
    Source("Snowflake Blog", "https://medium.com/feed/snowflake", "rss"),
    Source("Towards Data Science", "https://towardsdatascience.com/feed", "rss"),
    Source("Ahead of AI", "https://magazine.sebastianraschka.com/feed", "rss"),
    Source("Simon Willison", "https://simonwillison.net/atom/everything/", "rss"),
    Source("Chip Huyen", "https://huyenchip.com/feed.xml", "rss"),
    Source("Eugene Yan", "https://eugeneyan.com/writing/", "scrape"),
    # JSON API
    Source(
        "Hacker News AI",
        "https://hn.algolia.com/api/v1/search?tags=story&query=AI+LLM+machine+learning&hitsPerPage=30",
        "api",
    ),
    Source(
        "HuggingFace Daily Papers",
        "https://huggingface.co/api/daily_papers?limit=20",
        "api",
    ),
    # HTML scrape (JS-rendered, no working RSS)
    Source("Anthropic News", "https://www.anthropic.com/news", "scrape"),
    Source("Google DeepMind", "https://deepmind.google/blog/", "scrape"),
]
