"""
User policies generator for CLAUDE.md automation.
Manages user-defined policies that should never be auto-generated.
"""

import logging
from datetime import datetime
from pathlib import Path

from ..schemas import GenerationResult
from ..version_tracker import PolicyVersionTracker
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class UserPoliciesGenerator(BaseGenerator):
    """Generator for user-defined Claude Code policies."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize user policies generator."""
        super().__init__(template_dir)
        self.user_policies_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
        self.example_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md.example"
        self.version_tracker = PolicyVersionTracker()

    def generate_example_template(self) -> GenerationResult:
        """Generate/update the example template (ALWAYS updated)."""
        logger.info("Generating user policies example template...")

        # Fetch latest best practices from community/docs
        best_practices = self._fetch_community_best_practices()

        # Detect new policies since last update
        new_policies = self.version_tracker.detect_new_policies(best_practices)
        if new_policies:
            logger.info(f"Detected {len(new_policies)} new policies since last update")

        # Mark policies as new in the data structure
        best_practices_with_new = {}
        for category, policies in best_practices.items():
            best_practices_with_new[category] = [
                self.version_tracker.mark_policy_as_new(p, new_policies)
                for p in policies
            ]

        context = {
            "timestamp": datetime.now(),
            "best_practices": best_practices_with_new,
            "version": "2.0",
            "new_count": len(new_policies),
        }

        try:
            content = self.render_template("user-policies-example.j2", context)
            return self.write_file(self.example_file, content, create_backup=False)

        except Exception as e:
            logger.error(f"Failed to generate example template: {e}")
            return GenerationResult(
                success=False,
                output_path=str(self.example_file),
                errors=[str(e)],
                warnings=[],
                stats={},
            )

    def generate_initial_user_policies(self) -> GenerationResult:
        """Generate initial user policies file (ONLY if doesn't exist)."""
        if self.user_policies_file.exists():
            logger.info(f"User policies file already exists: {self.user_policies_file}")
            return GenerationResult(
                success=True,
                output_path=str(self.user_policies_file),
                errors=[],
                warnings=["File already exists - not overwriting"],
                stats={"skipped": True},
            )

        logger.info("Creating initial CLAUDE-USER-POLICIES.md from template...")

        context = {
            "timestamp": datetime.now(),
            "best_practices": self._fetch_community_best_practices(),
            "version": "2.0",
            "initial_setup": True,
        }

        try:
            content = self.render_template("user-policies.j2", context)
            return self.write_file(
                self.user_policies_file, content, create_backup=False
            )

        except Exception as e:
            logger.error(f"Failed to generate initial user policies: {e}")
            return GenerationResult(
                success=False,
                output_path=str(self.user_policies_file),
                errors=[str(e)],
                warnings=[],
                stats={},
            )

    def update_both_files(self) -> dict[str, GenerationResult]:
        """Update both example template and user policies (if needed)."""
        results = {}

        # ALWAYS update the example file
        results["example"] = self.generate_example_template()

        # ONLY create user file if it doesn't exist
        results["user_file"] = self.generate_initial_user_policies()

        return results

    def _fetch_community_best_practices(self) -> dict[str, list[dict]]:
        """
        Fetch latest best practices from community and official docs.

        Returns structured best practices organized by category.
        Combines curated policies with web-scraped content from multiple sources.
        """
        from ..scrapers import (
            AnthropicDocsScraper,
            ClaudeLogScraper,
            GitHubExamplesScraper,
        )

        # Start with curated best practices (always available)
        curated_practices = {
            "git_policies": [
                {
                    "name": "No --no-verify Without Permission",
                    "category": "Git Commit Policy",
                    "description": "Prevents bypassing quality gates without explicit user approval",
                    "recommended": True,
                    "source": "Security Best Practices 2025",
                },
            ],
            "system_limitations": [
                {
                    "name": "No Sudo Commands",
                    "category": "System Limitations",
                    "description": "Claude Code cannot run interactive sudo commands",
                    "recommended": True,
                    "platform": "NixOS",
                    "source": "Claude Code Documentation",
                },
            ],
            "documentation_standards": [
                {
                    "name": "No Temporal Markers",
                    "category": "Documentation Standards",
                    "description": "Avoid time-based references like 'NEW 2025', 'Week 1'",
                    "recommended": True,
                    "source": "Technical Writing Best Practices 2025",
                },
                {
                    "name": "No Hyperbolic Language",
                    "category": "Documentation Standards",
                    "description": "Avoid marketing speak in technical docs",
                    "recommended": True,
                    "source": "Technical Writing Best Practices 2025",
                },
                {
                    "name": "Documentation Creation Policy",
                    "category": "Documentation Standards",
                    "description": "Always ask before creating documentation files",
                    "recommended": True,
                    "source": "Anthropic Best Practices",
                },
            ],
            "code_quality": [
                {
                    "name": "Prefer Editing Over Creating",
                    "category": "Code Quality",
                    "description": "Edit existing files rather than creating new ones",
                    "recommended": True,
                    "source": "SWE Best Practices",
                },
                {
                    "name": "No Partial Implementations",
                    "category": "Code Quality",
                    "description": "Complete features fully, no stubs",
                    "recommended": False,
                    "source": "SWE Best Practices",
                },
                {
                    "name": "Cyclomatic Complexity < 10",
                    "category": "Code Quality",
                    "description": "Keep functions simple and focused",
                    "recommended": False,
                    "source": "Code Quality Standards",
                },
            ],
            "communication_style": [
                {
                    "name": "Concise Mode",
                    "category": "Communication",
                    "description": "Short, direct responses without preamble",
                    "recommended": False,
                    "source": "User Preferences",
                },
                {
                    "name": "Verbose Mode",
                    "category": "Communication",
                    "description": "Detailed explanations with reasoning",
                    "recommended": False,
                    "source": "User Preferences",
                },
            ],
            "project_management": [
                {
                    "name": "Todo List Usage",
                    "category": "Project Management",
                    "description": "Use TodoWrite for multi-step tasks",
                    "recommended": False,
                    "source": "Claude Code Best Practices",
                },
            ],
        }

        # Try to fetch from web sources (non-blocking)
        scraped_policies = []

        try:
            # Scrape Anthropic official docs
            anthropic_scraper = AnthropicDocsScraper(timeout=5)
            anthropic_result = anthropic_scraper.scrape_best_practices()
            if anthropic_result.success:
                scraped_policies.extend(anthropic_result.policies)
                logger.info(
                    f"Scraped {len(anthropic_result.policies)} policies from Anthropic docs"
                )
            else:
                logger.warning(
                    f"Anthropic scraping failed: {', '.join(anthropic_result.errors)}"
                )
        except Exception as e:
            logger.warning(f"Failed to scrape Anthropic docs: {e}")

        try:
            # Scrape GitHub examples (optional community feature)
            github_scraper = GitHubExamplesScraper(timeout=5)
            github_result = github_scraper.scrape_examples(max_repos=5)
            if github_result.success:
                scraped_policies.extend(github_result.policies)
                logger.info(
                    f"Scraped {len(github_result.policies)} examples from GitHub"
                )
            elif github_result.errors:
                # Only log if there are actual errors (not just missing token)
                logger.info(
                    f"GitHub scraping skipped: {', '.join(github_result.errors)}"
                )
        except Exception as e:
            logger.info(f"GitHub scraping unavailable: {e}")

        try:
            # Scrape ClaudeLog (optional community feature)
            claudelog_scraper = ClaudeLogScraper(timeout=5)
            claudelog_result = claudelog_scraper.scrape_best_practices()
            if claudelog_result.success:
                scraped_policies.extend(claudelog_result.policies)
                logger.info(
                    f"Scraped {len(claudelog_result.policies)} policies from ClaudeLog"
                )
            elif claudelog_result.errors:
                # Only log if there are actual errors
                logger.info(
                    f"ClaudeLog scraping skipped: {', '.join(claudelog_result.errors)}"
                )
        except Exception as e:
            logger.info(f"ClaudeLog scraping unavailable: {e}")

        # Merge scraped policies into curated ones
        if scraped_policies:
            logger.info(f"Total scraped policies: {len(scraped_policies)}")
            for policy in scraped_policies:
                # Convert ScrapedPolicy to dict format
                category_key = policy.category
                if category_key not in curated_practices:
                    curated_practices[category_key] = []

                curated_practices[category_key].append(
                    {
                        "name": policy.name,
                        "category": policy.category,
                        "description": policy.description,
                        "recommended": policy.confidence >= 0.7,
                        "source": policy.source_url,
                        "scraped": True,
                        "confidence": policy.confidence,
                    }
                )

        return curated_practices

    def should_generate_user_file(self) -> bool:
        """Check if user policies file needs to be generated."""
        return not self.user_policies_file.exists()

    def get_user_file_status(self) -> dict[str, any]:
        """Get status information about user policies files."""
        return {
            "user_file_exists": self.user_policies_file.exists(),
            "example_file_exists": self.example_file.exists(),
            "user_file_path": str(self.user_policies_file),
            "example_file_path": str(self.example_file),
            "should_generate": self.should_generate_user_file(),
        }
