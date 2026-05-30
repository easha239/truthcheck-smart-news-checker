"""Tests for scraper utility functions and article detail extraction."""

from __future__ import annotations

import unittest

from bs4 import BeautifulSoup

from truthcheck.models import FactCheckResult
from truthcheck.scrapers import ArticleDetailScraper, WebScraper


class TestScraperUtilities(unittest.TestCase):
    """Tests for keyword extraction and fact-check filtering."""

    def test_extract_keywords_removes_stopwords(self) -> None:
        keywords = WebScraper.extract_keywords(
            "This is a climate change misinformation article"
        )

        self.assertIn("climate", keywords)
        self.assertIn("change", keywords)
        self.assertIn("misinformation", keywords)
        self.assertNotIn("this", keywords)
        self.assertNotIn("is", keywords)

    def test_filter_relevant_results_keeps_related_factcheck(self) -> None:
        scraper = WebScraper([])

        results = [
            FactCheckResult(
                site="PolitiFact",
                title="Climate change misinformation spreads online",
                verdict="Needs review",
                url="https://example.com/factcheck/climate-change",
                snippet="A fact-check about climate change misinformation.",
            ),
            FactCheckResult(
                site="PolitiFact",
                title="Facebook posts",
                verdict="Needs review",
                url="https://www.politifact.com/personalities/facebook-posts/",
                snippet="Generic category page.",
            ),
        ]

        filtered = scraper.filter_relevant_results(
            "climate change misinformation",
            results,
        )

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Climate change misinformation spreads online")

    def test_filter_relevant_results_removes_generic_pages(self) -> None:
        scraper = WebScraper([])

        results = [
            FactCheckResult(
                site="PolitiFact",
                title="Facebook posts",
                verdict="Needs review",
                url="https://www.politifact.com/personalities/facebook-posts/",
                snippet="Generic social media category page.",
            )
        ]

        filtered = scraper.filter_relevant_results(
            "artificial intelligence",
            results,
        )

        self.assertEqual(filtered, [])


class TestArticleDetailScraper(unittest.TestCase):
    """Tests for static article detail extraction helpers."""

    def test_extract_author_date_and_article_text(self) -> None:
        html = """
        <html>
            <head>
                <meta name="author" content="Jane Reporter">
                <meta property="article:published_time" content="2026-05-20T10:00:00Z">
            </head>
            <body>
                <article>
                    <p>This is a detailed news paragraph about artificial intelligence and public trust.</p>
                    <p>This second paragraph provides more context about the article and its evidence.</p>
                </article>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")

        author = ArticleDetailScraper._extract_author(soup)
        published_date = ArticleDetailScraper._extract_date(soup)
        article_text = ArticleDetailScraper._extract_article_text(soup)

        self.assertEqual(author, "Jane Reporter")
        self.assertEqual(published_date, "2026-05-20T10:00:00Z")
        self.assertIn("artificial intelligence", article_text)
        self.assertIn("second paragraph", article_text)


if __name__ == "__main__":
    unittest.main()