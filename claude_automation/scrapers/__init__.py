"""Web scrapers for collecting best practices from various sources."""

from .anthropic_scraper import AnthropicDocsScraper
from .claudelog_scraper import ClaudeLogScraper
from .github_scraper import GitHubExamplesScraper

__all__ = ["AnthropicDocsScraper", "GitHubExamplesScraper", "ClaudeLogScraper"]
