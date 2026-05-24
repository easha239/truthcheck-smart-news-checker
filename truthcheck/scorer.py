"""Credibility scoring logic for TruthCheck."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import Article, FactCheckResult

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:  # pragma: no cover
    SentimentIntensityAnalyzer = None


class _FallbackSentimentAnalyzer:
    """Tiny fallback so tests and demos still run without VADER installed."""

    NEGATIVE = {"shocking", "fake", "scam", "hoax", "danger", "exposed", "leaked"}
    POSITIVE = {"safe", "verified", "true", "confirmed", "research"}

    def polarity_scores(self, text: str) -> dict[str, float]:
        tokens = set(re.findall(r"[a-zA-Z]+", text.lower()))
        neg = len(tokens & self.NEGATIVE)
        pos = len(tokens & self.POSITIVE)
        total = max(1, neg + pos)
        compound = (pos - neg) / total if (pos or neg) else 0.0
        return {"compound": compound}


class CredibilityScorer:
    """Calculates a 0 to 100 credibility score for an article."""

    SOURCE_TRUST = {
        "associated press": 92,
        "reuters": 92,
        "bbc news": 88,
        "abc news": 82,
        "the guardian": 82,
        "cnn": 75,
        "the new york times": 86,
        "washington post": 84,
        "al jazeera english": 76,
        "unknown source": 45,
        "unknown blog": 25,
        "blog": 35,
    }

    SENSATIONAL_KEYWORDS = {
        "shocking": 15,
        "leaked": 12,
        "secret": 10,
        "miracle": 14,
        "exposed": 13,
        "banned": 8,
        "scam": 18,
        "hoax": 20,
        "fake": 18,
        "conspiracy": 18,
        "you won't believe": 15,
        "doctors hate": 15,
        "anonymous insider": 12,
        "urgent": 8,
    }

    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else _FallbackSentimentAnalyzer()

    def score_article(self, article: Article, fact_checks: list[FactCheckResult] | None = None) -> Article:
        """Score an article and return the same Article with score fields filled."""

        fact_checks = fact_checks or []
        text = " ".join([article.title, article.description, article.content]).strip()
        article.sentiment_compound = self.analyzer.polarity_scores(text).get("compound", 0.0)
        article.source_trust = self._source_trust(article.source)
        article.keyword_risks = self._keyword_risks(text)
        article.fact_matches = self._match_fact_checks(article.title, fact_checks)

        keyword_penalty = min(60, sum(article.keyword_risks.values()))
        keyword_score = max(0, 100 - keyword_penalty)
        sentiment_score = max(0, 100 - int(abs(article.sentiment_compound) * 35))
        fact_score = self._fact_score(article.fact_matches)

        raw_score = (
            article.source_trust * 0.35
            + keyword_score * 0.20
            + sentiment_score * 0.15
            + fact_score * 0.30
        )
        article.credibility_score = int(round(max(0, min(100, raw_score))))
        article.verdict = self._verdict(article.credibility_score)
        article.explanation = self._explain(article, keyword_score, sentiment_score, fact_score)
        return article

    def score_articles(self, articles: list[Article], fact_checks: list[FactCheckResult] | None = None) -> list[Article]:
        """Score a list of articles."""

        return [self.score_article(article, fact_checks) for article in articles]

    def _source_trust(self, source_name: str) -> int:
        key = (source_name or "unknown source").strip().lower()
        if key in self.SOURCE_TRUST:
            return self.SOURCE_TRUST[key]
        for known, score in self.SOURCE_TRUST.items():
            if known in key or key in known:
                return score
        return 50

    def _keyword_risks(self, text: str) -> dict[str, int]:
        lowered = text.lower()
        risks: dict[str, int] = {}
        for keyword, weight in self.SENSATIONAL_KEYWORDS.items():
            if keyword in lowered:
                risks[keyword] = weight
        return risks

    @staticmethod
    def _match_fact_checks(title: str, fact_checks: list[FactCheckResult]) -> list[dict[str, str | float]]:
        matches: list[dict[str, str | float]] = []
        for fact in fact_checks:
            similarity = SequenceMatcher(None, title.lower(), fact.title.lower()).ratio()
            if similarity >= 0.25:
                matches.append(
                    {
                        "site": fact.site,
                        "title": fact.title,
                        "url": fact.url,
                        "verdict": fact.verdict,
                        "similarity": round(similarity, 2),
                    }
                )
        return sorted(matches, key=lambda item: item["similarity"], reverse=True)[:3]

    @staticmethod
    def _fact_score(matches: list[dict[str, str | float]]) -> int:
        if not matches:
            return 60
        verdict_text = " ".join(str(match.get("verdict", "")).lower() for match in matches)
        if any(word in verdict_text for word in ["false", "pants on fire", "hoax", "fake"]):
            return 15
        if any(word in verdict_text for word in ["true", "correct", "real"]):
            return 90
        return 55

    @staticmethod
    def _verdict(score: int) -> str:
        if score >= 75:
            return "Likely credible"
        if score >= 50:
            return "Needs review"
        return "High risk"

    @staticmethod
    def _explain(article: Article, keyword_score: int, sentiment_score: int, fact_score: int) -> list[str]:
        notes = [
            f"Source trust contribution: {article.source_trust}/100 based on the source label.",
            f"Keyword signal: {keyword_score}/100 after checking sensational terms.",
            f"Sentiment signal: {sentiment_score}/100 using headline and description polarity.",
            f"Fact-check signal: {fact_score}/100 based on scraped matches.",
        ]
        if article.keyword_risks:
            words = ", ".join(article.keyword_risks.keys())
            notes.append(f"Risk keywords detected: {words}.")
        if not article.fact_matches:
            notes.append("No close fact-check match was found, so the result is not a final verdict.")
        return notes
