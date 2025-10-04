"""
Scraper for Anthropic's official Claude Code best practices documentation.
"""

import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from ..schemas_policies import ScrapedPolicy, WebScrapingResult

logger = logging.getLogger(__name__)


class AnthropicDocsScraper:
    """Scrapes Anthropic's Claude Code documentation for best practices."""

    BASE_URL = "https://docs.anthropic.com/en/docs/claude-code"

    def __init__(self, timeout: int = 10):
        """Initialize scraper with timeout."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "claude-nixos-automation/2.0 (best-practices-aggregator)"
        })

    def scrape_best_practices(self) -> WebScrapingResult:
        """
        Scrape best practices from Anthropic documentation.

        Returns WebScrapingResult with scraped policies.
        """
        policies = []
        errors = []

        try:
            # Try to fetch the best practices page
            url = f"{self.BASE_URL}/best-practices"
            logger.info(f"Scraping Anthropic docs: {url}")

            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for policy patterns in the documentation
            # This is a simplified parser - adjust based on actual page structure
            policies.extend(self._parse_documentation_policies(soup, url))

            logger.info(f"Scraped {len(policies)} policies from Anthropic docs")

        except requests.RequestException as e:
            error_msg = f"Failed to scrape Anthropic docs: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error scraping Anthropic docs: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return WebScrapingResult(
            success=len(policies) > 0,
            policies=policies,
            errors=errors,
            source="anthropic_docs",
        )

    def _parse_documentation_policies(
        self, soup: BeautifulSoup, source_url: str
    ) -> list[ScrapedPolicy]:
        """
        Parse policies from documentation HTML.

        Looks for common patterns like:
        - Headings with policy names
        - Description paragraphs
        - Code examples
        """
        policies = []

        # Look for sections with best practices
        # Adjust selectors based on actual page structure
        for section in soup.find_all(["h2", "h3", "h4"]):
            heading_text = section.get_text().strip()

            # Skip non-policy headings
            if not self._is_policy_heading(heading_text):
                continue

            # Get description from next paragraph
            description = ""
            next_elem = section.find_next_sibling()
            if next_elem and next_elem.name == "p":
                description = next_elem.get_text().strip()

            if description:
                policy = ScrapedPolicy(
                    name=heading_text,
                    category=self._categorize_policy(heading_text, description),
                    description=description[:200],  # Truncate long descriptions
                    source_url=source_url,
                    confidence=0.8,  # Medium confidence for auto-scraped content
                )
                policies.append(policy)

        return policies

    def _is_policy_heading(self, text: str) -> bool:
        """Check if heading looks like a policy."""
        policy_keywords = [
            "always",
            "never",
            "avoid",
            "prefer",
            "recommended",
            "best practice",
            "guideline",
            "policy",
            "standard",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in policy_keywords)

    def _categorize_policy(self, heading: str, description: str) -> str:
        """Categorize policy based on content."""
        text = (heading + " " + description).lower()

        if any(kw in text for kw in ["git", "commit", "version control"]):
            return "git_policies"
        elif any(kw in text for kw in ["document", "comment", "markdown"]):
            return "documentation_standards"
        elif any(kw in text for kw in ["code quality", "complexity", "test"]):
            return "code_quality"
        elif any(kw in text for kw in ["communication", "style", "response"]):
            return "communication_style"
        else:
            return "documentation_standards"  # Default
