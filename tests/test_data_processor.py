import unittest

from truthcheck.data_processor import DataProcessor
from truthcheck.models import Article


class TestDataProcessor(unittest.TestCase):
    def test_deduplicate_removes_duplicate_urls(self):
        processor = DataProcessor()
        articles = [
            Article(title="A", url="https://example.com/a", source="BBC News"),
            Article(title="A duplicate", url="https://example.com/a", source="BBC News"),
        ]
        result = processor.deduplicate(articles)
        self.assertEqual(len(result), 1)

    def test_source_distribution_counts_verdicts(self):
        articles = [
            Article(title="A", url="", source="BBC", verdict="Likely credible"),
            Article(title="B", url="", source="Blog", verdict="High risk"),
            Article(title="C", url="", source="Blog", verdict="High risk"),
        ]
        distribution = DataProcessor.source_distribution(articles)
        self.assertEqual(distribution["High risk"], 2)
        self.assertEqual(distribution["Likely credible"], 1)


if __name__ == "__main__":
    unittest.main()
