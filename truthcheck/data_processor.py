"""Data cleaning and aggregation utilities."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from .models import Article


class DataProcessor:
    """Prepares article data for display, charts, and export."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove HTML fragments and repeated whitespace."""

        no_html = re.sub(r"<[^>]+>", " ", text or "")
        return re.sub(r"\s+", " ", no_html).strip()

    def deduplicate(self, articles: list[Article]) -> list[Article]:
        """Remove duplicate articles by URL or normalized title."""

        seen: set[str] = set()
        unique: list[Article] = []
        for article in articles:
            key = article.url or article.title.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            article.title = self.clean_text(article.title)
            article.description = self.clean_text(article.description)
            unique.append(article)
        return unique

    @staticmethod
    def to_dataframe(articles: list[Article]) -> pd.DataFrame:
        """Convert scored articles into a pandas DataFrame."""

        return pd.DataFrame(
            [
                {
                    "title": article.title,
                    "source": article.source,
                    "published_at": article.display_date,
                    "score": article.credibility_score,
                    "verdict": article.verdict,
                    "url": article.url,
                }
                for article in articles
            ]
        )

    @staticmethod
    def source_distribution(articles: list[Article]) -> dict[str, int]:
        """Count verdict categories for charting."""

        if not articles:
            return {"No results": 1}
        return dict(Counter(article.verdict for article in articles))
