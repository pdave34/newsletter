import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER: str = _require("SMTP_USER")
SMTP_PASSWORD: str = _require("SMTP_PASSWORD")
RECIPIENT_EMAILS: list[str] = [
    e.strip() for e in _require("RECIPIENT_EMAILS").split(",") if e.strip()
]
SENDER_NAME: str = os.getenv("SENDER_NAME", "AI & Data Newsletter")
DB_PATH: str = os.getenv("DB_PATH", "data/seen_articles.db")
MAX_ARTICLES: int = int(os.getenv("MAX_ARTICLES") or "3")
MAX_AGE_DAYS: int = int(os.getenv("MAX_AGE_DAYS") or "30")
