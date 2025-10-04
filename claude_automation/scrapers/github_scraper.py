"""
Scraper for GitHub repositories with .claude/CLAUDE.md examples.
"""

import logging
from datetime import datetime

import requests

from ..schemas_policies import ScrapedPolicy, WebScrapingResult

logger = logging.getLogger(__name__)


class GitHubExamplesScraper:
    """Scrapes GitHub for .claude/CLAUDE.md examples."""

    GITHUB_API = "https://api.github.com"

    def __init__(self, timeout: int = 10):
        """Initialize scraper."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "User-Agent": "claude-nixos-automation/2.0",
        })

    def scrape_examples(self, max_repos: int = 10) -> WebScrapingResult:
        """
        Search GitHub for repositories with .claude/CLAUDE.md files.

        Args:
            max_repos: Maximum number of repositories to analyze

        Returns:
            WebScrapingResult with policies extracted from examples
        """
        policies = []
        errors = []

        try:
            # Search for files named CLAUDE.md in .claude directory
            search_query = "filename:CLAUDE.md path:.claude"
            logger.info(f"Searching GitHub for: {search_query}")

            response = self.session.get(
                f"{self.GITHUB_API}/search/code",
                params={"q": search_query, "per_page": max_repos},
                timeout=self.timeout,
            )

            if response.status_code == 403:
                # Rate limited
                error_msg = "GitHub API rate limit exceeded. Skipping GitHub scraping."
                logger.warning(error_msg)
                errors.append(error_msg)
                return WebScrapingResult(
                    success=False, policies=[], errors=errors, source="github"
                )

            response.raise_for_status()
            data = response.json()

            # Analyze each found file
            for item in data.get("items", [])[:max_repos]:
                repo_name = item.get("repository", {}).get("full_name", "unknown")
                file_url = item.get("html_url", "")

                logger.info(f"Found example in {repo_name}")

                # For now, just note the existence
                # In production, you'd fetch and parse the actual content
                policy = ScrapedPolicy(
                    name=f"Example from {repo_name}",
                    category="documentation_standards",
                    description=f"Community example from {repo_name}",
                    source_url=file_url,
                    confidence=0.6,  # Lower confidence for community examples
                )
                policies.append(policy)

            logger.info(f"Found {len(policies)} example repositories")

        except requests.RequestException as e:
            error_msg = f"Failed to search GitHub: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error searching GitHub: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return WebScrapingResult(
            success=len(policies) > 0,
            policies=policies,
            errors=errors,
            source="github",
        )
