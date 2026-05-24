"""NewsAPI integration for TruthCheck."""

from __future__ import annotations

from typing import Any

import requests

from .config import AppConfig
from .models import Article


class APIFetcher:
    """Fetches live news articles from NewsAPI.

    The class deliberately supports a demo fallback so the project can still be
    demonstrated when no API key is available or the daily quota is exhausted.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def fetch_articles(self, query: str, page_size: int = 10) -> list[Article]:
        """Fetch articles for a topic or keyword.

        Args:
            query: Keyword typed by the user.
            page_size: Maximum number of results to request.

        Returns:
            A list of Article objects. Demo data is returned if the API key is
            missing or the request fails.
        """

        clean_query = (query or "technology").strip()
        if not self.config.news_api_key:
            return self._demo_articles(clean_query)

        params: dict[str, Any] = {
            "q": clean_query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max(1, min(page_size, 20)),
            "apiKey": self.config.news_api_key,
        }
        headers = {"User-Agent": self.config.user_agent}

        try:
            response = requests.get(
                self.config.news_api_url,
                params=params,
                headers=headers,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "ok":
                return self._demo_articles(clean_query)
            articles = [self._parse_article(item) for item in payload.get("articles", [])]
            return articles or self._demo_articles(clean_query)
        except requests.RequestException:
            return self._demo_articles(clean_query)
        except ValueError:
            return self._demo_articles(clean_query)

    @staticmethod
    def _parse_article(item: dict[str, Any]) -> Article:
        source = item.get("source") or {}
        return Article(
            title=item.get("title") or "Untitled article",
            url=item.get("url") or "",
            source=source.get("name") or "Unknown Source",
            published_at=item.get("publishedAt") or "",
            description=item.get("description") or "",
            content=item.get("content") or "",
        )

    @staticmethod
    def _demo_articles(query: str) -> list[Article]:
        """Return deterministic sample data for offline demonstration."""

        return [
            Article(
                title=f"Researchers warn that viral {query} claims need context before sharing",
                url="https://example.com/context-needed",
                source="BBC News",
                published_at="2026-05-19T08:00:00Z",
                description="A cautious report explains why context matters when evaluating fast-moving online claims.",
            ),
            Article(
                title=f"Shocking leaked {query} miracle cure exposed by anonymous insider",
                url="https://example.com/viral-claim",
                source="Unknown Blog",
                published_at="2026-05-19T09:30:00Z",
                description="A highly emotional headline uses several sensational terms without clear evidence.",
            ),
            Article(
                title=f"University team builds tool to help readers compare {query} sources",
                url="https://example.com/research-tool",
                source="The Guardian",
                published_at="2026-05-19T11:15:00Z",
                description="The project focuses on source comparison, attribution, and responsible interpretation.",
            ),
        ]
