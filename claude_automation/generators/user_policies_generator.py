"""
User policies generator for CLAUDE.md automation.
Manages user-defined policies that should never be auto-generated.
"""

import logging
from datetime import datetime
from pathlib import Path

from ..schemas import GenerationResult
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class UserPoliciesGenerator(BaseGenerator):
    """Generator for user-defined Claude Code policies."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize user policies generator."""
        super().__init__(template_dir)
        self.user_policies_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
        self.example_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md.example"

    def generate_example_template(self) -> GenerationResult:
        """Generate/update the example template (ALWAYS updated)."""
        logger.info("Generating user policies example template...")

        # Fetch latest best practices from community/docs
        best_practices = self._fetch_community_best_practices()

        context = {
            "timestamp": datetime.now(),
            "best_practices": best_practices,
            "version": "2.0",
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
        In future versions, this could scrape actual URLs for latest practices.
        """
        # For now, return curated best practices
        # TODO: Add web scraping for live updates from:
        # - https://docs.anthropic.com/claude-code/best-practices
        # - https://claudelog.com/mechanics/custom-agents/
        # - Community GitHub repos with .claude/CLAUDE.md examples

        return {
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
