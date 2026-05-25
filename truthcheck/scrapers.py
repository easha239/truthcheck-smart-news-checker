"""Web scraping, article detail extraction, and fact-check relevance filtering for TruthCheck."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .models import Article, FactCheckResult


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "did",
    "do", "does", "for", "from", "has", "have", "he", "her", "his", "how",
    "i", "in", "is", "it", "its", "may", "might", "new", "news", "of", "on",
    "or", "our", "she", "should", "that", "the", "their", "them", "they",
    "this", "to", "was", "we", "were", "what", "when", "where", "which",
    "who", "why", "will", "with", "you", "your", "after", "before", "about",
    "into", "over", "under", "more", "less", "than", "then", "also", "just",
    "said", "says", "say", "claim", "claims", "claimed", "post", "posts",
    "video", "image", "photo", "photos", "online", "social", "media"
}


class ArticleDetailScraper:
    """Attempts to scrape article-level metadata and readable text from article URLs."""

    def __init__(self, config) -> None:
        self.config = config
        self.headers = {
            "User-Agent": (
                "TruthCheck academic project bot "
                "(contact: student project, respectful scraping)"
            )
        }

    def enrich_articles(self, articles: list[Article], max_articles: int = 6) -> list[Article]:
        """Scrape extra article details for a limited number of articles.

        The scraper is intentionally conservative. If a website blocks scraping,
        uses JavaScript rendering, or has an unsupported layout, the article is
        returned unchanged.
        """
        enriched_articles: list[Article] = []

        for index, article in enumerate(articles):
            if index < max_articles:
                enriched_articles.append(self.enrich_article(article))
                time.sleep(0.7)
            else:
                enriched_articles.append(article)

        return enriched_articles

    def enrich_article(self, article: Article) -> Article:
        """Try to extract author, date, metadata, and readable article text."""
        if not article.url:
            return article

        try:
            response = requests.get(article.url, headers=self.headers, timeout=8)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                return article

            soup = BeautifulSoup(response.text, "html.parser")

            author = self._extract_author(soup)
            published_date = self._extract_date(soup)
            article_text = self._extract_article_text(soup)

            if author and not getattr(article, "author", ""):
                article.author = author

            if published_date and not getattr(article, "published_at", ""):
                article.published_at = published_date

            if article_text and len(article_text) > len(article.content or ""):
                article.content = article_text

        except Exception:
            return article

        return article

    @staticmethod
    def _extract_author(soup: BeautifulSoup) -> str:
        """Extract author from common metadata tags."""
        selectors = [
            {"name": "author"},
            {"property": "article:author"},
            {"name": "twitter:creator"},
            {"name": "parsely-author"},
            {"property": "og:author"},
        ]

        for attrs in selectors:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                return tag["content"].strip()

        author_tag = soup.find(attrs={"class": re.compile("author|byline", re.I)})
        if author_tag:
            return author_tag.get_text(" ", strip=True)[:120]

        return ""

    @staticmethod
    def _extract_date(soup: BeautifulSoup) -> str:
        """Extract publication date from common metadata tags."""
        selectors = [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"name": "publishdate"},
            {"name": "timestamp"},
            {"name": "date"},
            {"itemprop": "datePublished"},
        ]

        for attrs in selectors:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                return tag["content"].strip()

        time_tag = soup.find("time")
        if time_tag:
            if time_tag.get("datetime"):
                return time_tag["datetime"].strip()
            return time_tag.get_text(" ", strip=True)

        return ""

    @staticmethod
    def _extract_article_text(soup: BeautifulSoup) -> str:
        """Extract readable text from article body or paragraph tags."""
        for unwanted in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            unwanted.decompose()

        article_container = soup.find("article")

        if article_container:
            paragraphs = article_container.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        cleaned_paragraphs = []

        for paragraph in paragraphs:
            text = paragraph.get_text(" ", strip=True)
            if len(text) < 40:
                continue
            if ArticleDetailScraper._looks_like_noise(text):
                continue
            cleaned_paragraphs.append(text)

        article_text = " ".join(cleaned_paragraphs)
        article_text = re.sub(r"\s+", " ", article_text).strip()

        return article_text[:2500]

    @staticmethod
    def _looks_like_noise(text: str) -> bool:
        """Remove cookie notices, newsletter prompts, and navigation text."""
        lowered = text.lower()

        noisy_phrases = [
            "subscribe",
            "sign up",
            "cookie",
            "privacy policy",
            "terms of service",
            "advertisement",
            "all rights reserved",
            "follow us",
            "share this article",
            "newsletter",
            "enable javascript",
        ]

        return any(phrase in lowered for phrase in noisy_phrases)


class Scraper(ABC):
    """Abstract base scraper class."""

    def __init__(self, config) -> None:
        self.config = config
        self.headers = {
            "User-Agent": (
                "TruthCheck academic project bot "
                "(contact: student project, respectful scraping)"
            )
        }

    @abstractmethod
    def scrape(self, query: str, limit: int = 5) -> list[FactCheckResult]:
        """Scrape fact-check results for a query."""


class SnopesScraper(Scraper):
    """Scraper for Snopes search results."""

    def scrape(self, query: str, limit: int = 5) -> list[FactCheckResult]:
        results: list[FactCheckResult] = []

        try:
            url = f"https://www.snopes.com/?s={quote_plus(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.select(
                "article, .media-list-item, .card, .article_wrapper, .entry-content"
            )

            for card in cards[: limit * 4]:
                title_tag = card.find(["h1", "h2", "h3", "h4", "a"])
                if not title_tag:
                    continue

                title = title_tag.get_text(" ", strip=True)
                if not title or len(title) < 8:
                    continue

                link_tag = card.find("a", href=True)
                link = link_tag["href"] if link_tag else url

                if link.startswith("/"):
                    link = "https://www.snopes.com" + link

                snippet = card.get_text(" ", strip=True)
                verdict = self._infer_verdict(snippet)

                results.append(
                    FactCheckResult(
                        site="Snopes",
                        title=title,
                        verdict=verdict,
                        url=link,
                        snippet=snippet[:350],
                    )
                )

                if len(results) >= limit:
                    break

            time.sleep(1)

        except Exception:
            return []

        return results

    @staticmethod
    def _infer_verdict(text: str) -> str:
        lowered = text.lower()

        if "mostly false" in lowered:
            return "Mostly False"
        if "false" in lowered:
            return "False"
        if "mostly true" in lowered:
            return "Mostly True"
        if "true" in lowered:
            return "True"
        if "mixture" in lowered or "mixed" in lowered:
            return "Mixed"
        if "unproven" in lowered:
            return "Unproven"

        return "Needs review"


class PolitiFactScraper(Scraper):
    """Scraper for PolitiFact search results."""

    def scrape(self, query: str, limit: int = 5) -> list[FactCheckResult]:
        results: list[FactCheckResult] = []

        try:
            url = f"https://www.politifact.com/search/?q={quote_plus(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.select(
                "article, .m-statement, .o-listicle__item, .c-textgroup"
            )

            for card in cards[: limit * 4]:
                title_tag = card.find(["h1", "h2", "h3", "a"])
                if not title_tag:
                    continue

                title = title_tag.get_text(" ", strip=True)
                if not title or len(title) < 8:
                    continue

                link_tag = card.find("a", href=True)
                link = link_tag["href"] if link_tag else url

                if link.startswith("/"):
                    link = "https://www.politifact.com" + link

                snippet = card.get_text(" ", strip=True)
                verdict = self._infer_verdict(snippet)

                results.append(
                    FactCheckResult(
                        site="PolitiFact",
                        title=title,
                        verdict=verdict,
                        url=link,
                        snippet=snippet[:350],
                    )
                )

                if len(results) >= limit:
                    break

            time.sleep(1)

        except Exception:
            return []

        return results

    @staticmethod
    def _infer_verdict(text: str) -> str:
        lowered = text.lower()

        if "pants on fire" in lowered:
            return "Pants on Fire"
        if "mostly false" in lowered:
            return "Mostly False"
        if "false" in lowered:
            return "False"
        if "half true" in lowered:
            return "Half True"
        if "mostly true" in lowered:
            return "Mostly True"
        if "true" in lowered:
            return "True"

        return "Needs review"


class WebScraper:
    """Combines multiple fact-check scrapers and filters irrelevant results."""

    def __init__(self, scrapers: list[Scraper]) -> None:
        self.scrapers = scrapers

    def search_fact_checks(
        self,
        query: str,
        limit_per_site: int = 3
    ) -> list[FactCheckResult]:
        """Search fact-check websites and keep only relevant results."""
        all_results: list[FactCheckResult] = []

        for scraper in self.scrapers:
            site_results = scraper.scrape(query, limit=limit_per_site * 4)
            all_results.extend(site_results)

        filtered = self.filter_relevant_results(query, all_results)

        return filtered[: limit_per_site * len(self.scrapers)]

    def filter_relevant_results(
        self,
        query: str,
        results: list[FactCheckResult],
        min_score: float = 0.45,
    ) -> list[FactCheckResult]:
        """Filter fact-check results using stronger keyword overlap."""
        query_keywords = self.extract_keywords(query)

        if not query_keywords:
            return []

        scored_results: list[tuple[float, FactCheckResult]] = []

        for result in results:
            title_text = result.title or ""
            snippet_text = result.snippet or ""
            url_text = result.url or ""

            if self.is_generic_factcheck_page(title_text, url_text):
                continue

            title_keywords = self.extract_keywords(title_text)
            snippet_keywords = self.extract_keywords(snippet_text)

            title_overlap = query_keywords.intersection(title_keywords)
            snippet_overlap = query_keywords.intersection(snippet_keywords)

            combined_overlap = title_overlap.union(snippet_overlap)

            if len(query_keywords) >= 2 and len(combined_overlap) < 2:
                continue

            score = (
                (len(title_overlap) * 0.7)
                + (len(snippet_overlap) * 0.3)
            ) / len(query_keywords)

            if score >= min_score:
                scored_results.append((score, result))

        scored_results.sort(key=lambda item: item[0], reverse=True)

        return [result for _, result in scored_results]

    @staticmethod
    def is_generic_factcheck_page(title: str, url: str) -> bool:
        """Remove generic profile or category pages that are not fact-check articles."""
        title_clean = title.strip().lower()
        url_clean = url.lower()

        generic_titles = {
            "facebook posts",
            "instagram posts",
            "tiktok posts",
            "x posts",
            "twitter posts",
            "viral image",
            "viral images",
            "social media",
            "politicians",
            "celebrities",
            "elon musk",
            "donald trump",
            "joe biden",
            "climate power",
            "facebook",
            "instagram",
            "tiktok",
            "twitter",
            "truth-o-meter",
        }

        generic_url_parts = [
            "/personalities/",
            "/subjects/",
            "/truth-o-meter/",
            "/article/",
            "/facebook-posts/",
            "/instagram-posts/",
            "/tiktok-posts/",
            "/twitter-posts/",
            "/staff/",
            "/media/",
        ]

        if title_clean in generic_titles:
            return True

        return any(part in url_clean for part in generic_url_parts)

    @staticmethod
    def extract_keywords(text: str) -> set[str]:
        """Extract meaningful lowercase keywords from text."""
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())

        keywords = {
            word
            for word in words
            if word not in STOPWORDS and len(word) >= 3
        }

        return keywords

    @staticmethod
    def relevance_score(
        query_keywords: set[str],
        result_keywords: set[str]
    ) -> float:
        """Calculate keyword overlap score between query and result."""
        if not query_keywords or not result_keywords:
            return 0.0

        overlap = query_keywords.intersection(result_keywords)
        return len(overlap) / len(query_keywords)