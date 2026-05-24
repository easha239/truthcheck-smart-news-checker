"""Configuration helpers for TruthCheck."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration values."""

    news_api_key: str | None
    news_api_url: str = "https://newsapi.org/v2/everything"
    request_timeout: int = 10
    user_agent: str = "TruthCheckAcademicProject/0.1 (+https://github.com/)"
    polite_delay_seconds: float = 1.0


def load_config() -> AppConfig:
    """Load configuration from environment variables and optional .env file."""

    if load_dotenv is not None:
        load_dotenv()

    api_key = os.getenv("NEWS_API_KEY")
    if api_key:
        api_key = api_key.strip()
    if not api_key or api_key == "your_newsapi_key_here":
        api_key = None

    return AppConfig(news_api_key=api_key)
