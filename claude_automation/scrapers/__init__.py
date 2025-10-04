"""Web scrapers for collecting best practices from various sources."""

from .anthropic_scraper import AnthropicDocsScraper
from .github_scraper import GitHubExamplesScraper
from .claudelog_scraper import ClaudeLogScraper

__all__ = ["AnthropicDocsScraper", "GitHubExamplesScraper", "ClaudeLogScraper"]
