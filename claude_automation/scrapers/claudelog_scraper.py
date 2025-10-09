"""
Scraper for ClaudeLog best practices database.
"""

import logging

import requests
from bs4 import BeautifulSoup

from ..schemas_policies import ScrapedPolicy, WebScrapingResult

logger = logging.getLogger(__name__)


class ClaudeLogScraper:
    """Scrapes ClaudeLog for best practices."""

    BASE_URL = "https://claudelog.com"

    def __init__(self, timeout: int = 10):
        """Initialize scraper."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "claude-nixos-automation/2.0",
                "Accept": "text/html,application/xhtml+xml",
            }
        )

    def scrape_best_practices(self) -> WebScrapingResult:
        """
        Scrape best practices from ClaudeLog.

        Focuses on the Mechanics section which contains foundational
        best practices for Claude Code usage.
        """
        policies = []
        errors = []

        try:
            logger.info("Scraping ClaudeLog best practices...")

            # Fetch main page
            response = self.session.get(self.BASE_URL, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Find all article links (best practices are typically in articles)
            articles = soup.find_all("a", href=True)

            for article in articles:
                href = article.get("href", "")
                title = article.get_text(strip=True)

                # Focus on mechanics/best practices articles
                if not title or len(title) < 3:
                    continue

                # Skip navigation/footer links
                if title.lower() in [
                    "home",
                    "about",
                    "contact",
                    "inventions",
                    "mechanics",
                ]:
                    continue

                # Build full URL
                if href.startswith("/"):
                    url = f"{self.BASE_URL}{href}"
                elif href.startswith("http"):
                    url = href
                else:
                    continue

                # Only process claudelog.com URLs
                if "claudelog.com" not in url:
                    continue

                # Categorize based on article title/URL
                category = self._categorize_practice(title, href)

                # Create policy entry
                policy = ScrapedPolicy(
                    name=title,
                    category=category,
                    description=f"ClaudeLog best practice: {title}",
                    source_url=url,
                    confidence=0.8,  # High confidence - curated community resource
                )
                policies.append(policy)
                logger.debug(f"Found practice: {title}")

            logger.info(f"Scraped {len(policies)} best practices from ClaudeLog")

        except requests.Timeout:
            error_msg = "ClaudeLog request timed out"
            logger.warning(error_msg)
            errors.append(error_msg)

        except requests.RequestException as e:
            error_msg = f"Failed to fetch ClaudeLog: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error scraping ClaudeLog: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return WebScrapingResult(
            success=len(policies) > 0,
            policies=policies,
            errors=errors,
            source="claudelog",
        )

    def _categorize_practice(self, title: str, url: str) -> str:
        """Categorize a best practice based on title/URL."""
        title_lower = title.lower()

        # Workflow and planning
        if any(kw in title_lower for kw in ["plan", "workflow", "process", "agent"]):
            return "workflow_optimization"

        # Performance and efficiency
        if any(
            kw in title_lower
            for kw in ["performance", "speed", "efficient", "optimize"]
        ):
            return "performance"

        # Documentation and context
        if any(
            kw in title_lower
            for kw in ["claude.md", "documentation", "context", "memory"]
        ):
            return "documentation_standards"

        # Development practices
        if any(kw in title_lower for kw in ["development", "code", "testing", "git"]):
            return "development_practices"

        # Default to general best practices
        return "best_practices"
