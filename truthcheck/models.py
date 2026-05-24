"""Data models used across TruthCheck."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Article:
    """Represents one news article or search result."""

    title: str
    url: str
    source: str
    published_at: str = ""
    description: str = ""
    content: str = ""
    sentiment_compound: float = 0.0
    source_trust: int = 50
    credibility_score: int = 0
    verdict: str = "Unscored"
    keyword_risks: dict[str, int] = field(default_factory=dict)
    fact_matches: list[dict[str, Any]] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)

    @property
    def display_date(self) -> str:
        """Return a readable publication date where possible."""

        if not self.published_at:
            return "Unknown date"
        try:
            parsed = datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return self.published_at


@dataclass
class FactCheckResult:
    """Represents a scraped fact-check search result."""

    site: str
    title: str
    url: str
    verdict: str = "Unknown"
    snippet: str = ""
