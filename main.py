"""Entry point for the TruthCheck desktop application."""

from __future__ import annotations

import argparse

from truthcheck.api_fetcher import APIFetcher
from truthcheck.config import load_config
from truthcheck.data_processor import DataProcessor
from truthcheck.dashboard import Dashboard
from truthcheck.scorer import CredibilityScorer


def run_cli(query: str) -> None:
    """Run a lightweight terminal demo without launching Tkinter."""

    config = load_config()
    fetcher = APIFetcher(config)
    processor = DataProcessor()
    scorer = CredibilityScorer()

    articles = processor.deduplicate(fetcher.fetch_articles(query, page_size=5))
    scored = scorer.score_articles(articles)
    for article in scored:
        print(f"{article.credibility_score:3d} | {article.verdict:16s} | {article.source:18s} | {article.title}")


def main() -> None:
    parser = argparse.ArgumentParser(description="TruthCheck Smart News Truth Checker")
    parser.add_argument("--cli", action="store_true", help="Run in terminal mode instead of GUI mode")
    parser.add_argument("--query", default="artificial intelligence", help="Topic or headline to analyse")
    args = parser.parse_args()

    if args.cli:
        run_cli(args.query)
    else:
        Dashboard().run()


if __name__ == "__main__":
    main()
