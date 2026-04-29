from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    url: str
    title: str
    summary: str
    source: str
    published: datetime
    score: int = field(default=0, compare=False)
