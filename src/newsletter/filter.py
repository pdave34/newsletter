from datetime import datetime, timezone

from .models import Article

KEYWORDS = [
    "llm",
    "large language model",
    "transformer",
    "gpt",
    "claude",
    "gemini",
    "llama",
    "mistral",
    "phi",
    "qwen",
    "deepseek",
    "rag",
    "retrieval",
    "fine-tun",
    "finetuning",
    "embeddings",
    "vector",
    "inference",
    "quantization",
    "lora",
    "rlhf",
    "alignment",
    "anthropic",
    "openai",
    "hugging face",
    "huggingface",
    "snowflake",
    "databricks",
    "delta lake",
    "spark",
    "dbt",
    "dbt cloud",
    "aws",
    "sagemaker",
    "bedrock",
    "azure",
    "openai service",
    "gcp",
    "vertex",
    "data engineering",
    "data pipeline",
    "etl",
    "elt",
    "lakehouse",
    "data lake",
    "data warehouse",
    "data platform",
    "data mesh",
    "data fabric",
    "machine learning",
    "deep learning",
    "neural network",
    "diffusion",
    "multimodal",
    "vision",
    "speech",
    "nlp",
    "reinforcement learning",
    "mlops",
    "model deployment",
    "feature store",
    "experiment tracking",
    "data science",
    "statistics",
    "bayesian",
    "causal",
    "open source",
    "open-source",
    "benchmark",
    "eval",
    "agent",
    "agentic",
    "tool use",
    "function calling",
    "context window",
    "token",
]


def score_article(article: Article) -> int:
    text = (article.title + " " + article.summary).lower()
    keyword_score = sum(1 for kw in KEYWORDS if kw in text)
    age_days = (datetime.now(timezone.utc) - article.published).days
    if age_days <= 7:
        recency_bonus = 3
    elif age_days <= 30:
        recency_bonus = 1
    else:
        recency_bonus = 0
    return keyword_score + recency_bonus


def filter_recent(articles: list[Article], max_age_days: int = 30) -> list[Article]:
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    return [a for a in articles if a.published.timestamp() >= cutoff]


def deduplicate(articles: list[Article], seen_urls: set[str]) -> list[Article]:
    seen = set(seen_urls)
    result = []
    for a in articles:
        if a.url not in seen:
            seen.add(a.url)
            result.append(a)
    return result


def rank(articles: list[Article]) -> list[Article]:
    for a in articles:
        a.score = score_article(a)
    return sorted(articles, key=lambda a: (-a.score, -a.published.timestamp()))


def limit(articles: list[Article], n: int) -> list[Article]:
    return articles[:n]
