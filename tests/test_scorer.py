import unittest

from truthcheck.models import Article, FactCheckResult
from truthcheck.scorer import CredibilityScorer


class TestCredibilityScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = CredibilityScorer()

    def test_reliable_source_gets_higher_score_than_unknown_blog(self):
        reliable = Article(title="Researchers publish careful climate analysis", url="", source="BBC News")
        risky = Article(title="Shocking leaked miracle cure exposed", url="", source="Unknown Blog")
        reliable = self.scorer.score_article(reliable)
        risky = self.scorer.score_article(risky)
        self.assertGreater(reliable.credibility_score, risky.credibility_score)

    def test_false_fact_check_reduces_score(self):
        article = Article(title="Viral claim says miracle cure is real", url="", source="Unknown Blog")
        fact_checks = [
            FactCheckResult(
                site="PolitiFact",
                title="Viral claim says miracle cure is real",
                url="https://example.com/fact-check",
                verdict="False",
            )
        ]
        scored = self.scorer.score_article(article, fact_checks)
        self.assertEqual(scored.verdict, "High risk")
        self.assertLess(scored.credibility_score, 50)

    def test_keyword_risk_detection(self):
        article = Article(title="Shocking secret leaked report exposed", url="", source="Unknown Source")
        scored = self.scorer.score_article(article)
        self.assertIn("shocking", scored.keyword_risks)
        self.assertIn("secret", scored.keyword_risks)


if __name__ == "__main__":
    unittest.main()
