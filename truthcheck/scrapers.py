"""Fact-check site scraping utilities."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import Iterable
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from .config import AppConfig
from .models import FactCheckResult


class Scraper(ABC):
    """Abstract scraper interface.

    Subclasses implement the same scrape() method, which demonstrates
    polymorphism in the project.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    @abstractmethod
    def scrape(self, query: str, limit: int = 3) -> list[FactCheckResult]:
        """Search a fact-checking site and return possible matches."""

    def _get_soup(self, url: str) -> BeautifulSoup | None:
        headers = {"User-Agent": self.config.user_agent}
        try:
            time.sleep(self.config.polite_delay_seconds)
            response = requests.get(url, headers=headers, timeout=self.config.request_timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException:
            return None


class SnopesScraper(Scraper):
    """Scrapes Snopes search results for matching fact checks."""

    site_name = "Snopes"
    base_url = "https://www.snopes.com"

    def scrape(self, query: str, limit: int = 3) -> list[FactCheckResult]:
        url = f"{self.base_url}/?s={quote_plus(query)}"
        soup = self._get_soup(url)
        if soup is None:
            return []
        results: list[FactCheckResult] = []
        for anchor in self._candidate_links(soup):
            title = self._clean(anchor.get_text(" "))
            href = anchor.get("href") or ""
            if not title or len(title) < 20 or "/fact-check/" not in href:
                continue
            result_url = urljoin(self.base_url, href)
            results.append(
                FactCheckResult(
                    site=self.site_name,
                    title=title,
                    url=result_url,
                    verdict=self._infer_verdict(title),
                )
            )
            if len(results) >= limit:
                break
        return self._unique(results)

    @staticmethod
    def _candidate_links(soup: BeautifulSoup) -> Iterable:
        return soup.find_all("a", href=True)

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _infer_verdict(text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in ["false", "fake", "scam", "hoax"]):
            return "Likely false"
        if any(word in lowered for word in ["true", "correct", "real"]):
            return "Likely true"
        return "Needs review"

    @staticmethod
    def _unique(results: list[FactCheckResult]) -> list[FactCheckResult]:
        seen: set[str] = set()
        unique: list[FactCheckResult] = []
        for item in results:
            if item.url in seen:
                continue
            seen.add(item.url)
            unique.append(item)
        return unique


class PolitiFactScraper(Scraper):
    """Scrapes PolitiFact search results for matching fact checks."""

    site_name = "PolitiFact"
    base_url = "https://www.politifact.com"

    def scrape(self, query: str, limit: int = 3) -> list[FactCheckResult]:
        url = f"{self.base_url}/search/?q={quote_plus(query)}"
        soup = self._get_soup(url)
        if soup is None:
            return []
        results: list[FactCheckResult] = []
        for anchor in soup.find_all("a", href=True):
            title = self._clean(anchor.get_text(" "))
            href = anchor.get("href") or ""
            if not title or len(title) < 20 or "/factchecks/" not in href:
                continue
            result_url = urljoin(self.base_url, href)
            verdict = self._infer_verdict(anchor, title)
            results.append(
                FactCheckResult(
                    site=self.site_name,
                    title=title,
                    url=result_url,
                    verdict=verdict,
                )
            )
            if len(results) >= limit:
                break
        return self._unique(results)

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _infer_verdict(anchor, title: str) -> str:
        nearby_text = " ".join([
            title,
            anchor.parent.get_text(" ") if anchor.parent else "",
        ]).lower()
        verdicts = [
            "pants on fire",
            "false",
            "mostly false",
            "half true",
            "mostly true",
            "true",
        ]
        for verdict in verdicts:
            if verdict in nearby_text:
                return verdict.title()
        return "Needs review"

    @staticmethod
    def _unique(results: list[FactCheckResult]) -> list[FactCheckResult]:
        seen: set[str] = set()
        unique: list[FactCheckResult] = []
        for item in results:
            if item.url in seen:
                continue
            seen.add(item.url)
            unique.append(item)
        return unique


class WebScraper:
    """Coordinates multiple fact-check scrapers."""

    def __init__(self, scrapers: list[Scraper]) -> None:
        self.scrapers = scrapers

    def search_fact_checks(self, query: str, limit_per_site: int = 2) -> list[FactCheckResult]:
        results: list[FactCheckResult] = []
        for scraper in self.scrapers:
            results.extend(scraper.scrape(query, limit=limit_per_site))
        return results
