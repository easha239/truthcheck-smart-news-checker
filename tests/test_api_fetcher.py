import unittest

from truthcheck.api_fetcher import APIFetcher
from truthcheck.config import AppConfig


class TestAPIFetcher(unittest.TestCase):
    def test_demo_mode_returns_articles_without_api_key(self):
        fetcher = APIFetcher(AppConfig(news_api_key=None))
        articles = fetcher.fetch_articles("ai")
        self.assertGreaterEqual(len(articles), 1)
        self.assertTrue(all(article.title for article in articles))


if __name__ == "__main__":
    unittest.main()
