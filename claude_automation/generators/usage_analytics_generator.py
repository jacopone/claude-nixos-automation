"""
Usage analytics generator for CLAUDE.md.
Appends usage statistics section to project CLAUDE.md file.
"""

import logging
import re
from pathlib import Path

from ..schemas import GenerationResult, UsageAnalyticsConfig
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class UsageAnalyticsGenerator(BaseGenerator):
    """Generates usage analytics section for CLAUDE.md."""

    # Markers for the analytics section
    START_MARKER = "<!-- USAGE_ANALYTICS_START -->"
    END_MARKER = "<!-- USAGE_ANALYTICS_END -->"

    def __init__(self, template_dir: Path | None = None):
        """Initialize generator."""
        super().__init__(template_dir or self._get_default_template_dir())

    def generate(self, config: UsageAnalyticsConfig) -> GenerationResult:
        """
        Generate usage analytics section.

        Args:
            config: Usage analytics configuration

        Returns:
            GenerationResult with generation status and stats
        """
        try:
            # Render analytics content
            analytics_content = self._render_analytics(config)

            # Get CLAUDE.md path
            claude_file = config.claude_file

            # Read existing CLAUDE.md if it exists
            if claude_file.exists():
                existing_content = claude_file.read_text()

                # Check if analytics section already exists
                if self.START_MARKER in existing_content:
                    # Replace existing section
                    new_content = self._replace_analytics_section(
                        existing_content, analytics_content
                    )
                else:
                    # Append new section
                    new_content = self._append_analytics_section(
                        existing_content, analytics_content
                    )
            else:
                # Create new file with analytics section
                new_content = f"# CLAUDE.md\n\n{analytics_content}\n"

            # Write updated content
            claude_file.write_text(new_content)

            # Collect stats
            stats = {
                "output_path": str(claude_file),
                "total_commands": config.total_commands,
                "unique_commands": config.unique_commands,
                "top_commands_count": len(config.top_commands),
                "tools_tracked": len(config.tool_usage),
                "workflow_patterns": len(config.workflow_patterns),
            }

            return GenerationResult(
                success=True, output_path=str(claude_file), stats=stats
            )

        except Exception as e:
            logger.error(f"Failed to generate usage analytics: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                output_path=str(config.claude_file),
                errors=[str(e)],
            )

    def _render_analytics(self, config: UsageAnalyticsConfig) -> str:
        """
        Render analytics content from template.

        Args:
            config: Usage analytics configuration

        Returns:
            Rendered analytics markdown
        """
        template = self.env.get_template("usage_analytics.j2")

        return template.render(
            total_commands=config.total_commands,
            unique_commands=config.unique_commands,
            top_commands=config.top_commands,
            command_stats=config.command_stats,
            tool_usage=config.tool_usage,
            workflow_patterns=config.workflow_patterns,
            timestamp=config.timestamp,
            start_marker=self.START_MARKER,
            end_marker=self.END_MARKER,
        )

    def _replace_analytics_section(self, content: str, analytics_content: str) -> str:
        """
        Replace existing analytics section in CLAUDE.md.

        Args:
            content: Existing CLAUDE.md content
            analytics_content: New analytics content

        Returns:
            Updated content
        """
        # Pattern to match everything between markers
        pattern = re.compile(
            f"{re.escape(self.START_MARKER)}.*?{re.escape(self.END_MARKER)}",
            re.DOTALL,
        )

        # Replace with new content
        return pattern.sub(analytics_content.strip(), content)

    def _append_analytics_section(self, content: str, analytics_content: str) -> str:
        """
        Append analytics section to CLAUDE.md.

        Args:
            content: Existing CLAUDE.md content
            analytics_content: New analytics content

        Returns:
            Updated content with analytics appended
        """
        # Ensure content ends with newline
        if not content.endswith("\n"):
            content += "\n"

        # Add separator and analytics
        return f"{content}\n---\n\n{analytics_content}\n"

    @staticmethod
    def _get_default_template_dir() -> Path:
        """Get default template directory."""
        return Path(__file__).parent.parent / "templates"
