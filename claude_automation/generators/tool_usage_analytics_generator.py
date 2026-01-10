"""
Tool Usage Analytics Generator - Generates tool usage reports.

Generates detailed analytics report in .claude/tool-analytics.md.
No longer embeds into CLAUDE.md - full report is linked from Dynamic Context section.

Philosophy:
- CLAUDE.md: Links to analytics (slim, policies-only)
- tool-analytics.md: Full detailed usage stats (human decision support)
"""

import logging
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from claude_automation.schemas import GenerationResult
from claude_automation.schemas.tool_usage import ToolUsageAnalyticsConfig

logger = logging.getLogger(__name__)


class ToolUsageAnalyticsGenerator:
    """Generate tool usage analytics to separate report file."""

    def __init__(self):
        """Initialize generator with templates."""
        # Template directory
        template_dir = Path(__file__).parent.parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["priority_label"] = self._priority_label_filter

        # Add timedelta to globals for template access
        self.env.globals["timedelta"] = timedelta

    def generate(self, config: ToolUsageAnalyticsConfig) -> GenerationResult:
        """
        Generate tool usage analytics to separate report file.

        Writes full analytics to .claude/tool-analytics.md only.
        CLAUDE.md is no longer modified (it links to the report).

        Args:
            config: Tool usage analytics configuration

        Returns:
            GenerationResult with success status and output paths
        """
        errors = []
        warnings = []
        timestamp = config.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Generate full analytics for separate file
            analytics_template = self.env.get_template("tool_usage_analytics.j2")
            analytics_content = analytics_template.render(
                config=config,
                timestamp=timestamp,
            )

            # Write full analytics to .claude/tool-analytics.md
            claude_md_path = config.claude_file
            analytics_path = claude_md_path.parent / ".claude" / "tool-analytics.md"
            analytics_path.parent.mkdir(parents=True, exist_ok=True)

            with open(analytics_path, "w") as f:
                f.write(analytics_content)

            logger.info(f"Wrote detailed tool analytics to {analytics_path}")

            # Build stats
            stats = {
                "total_tools": config.total_tools,
                "used_tools": len(config.used_tools),
                "dormant_tools": config.unused_tool_count,
                "adoption_rate": config.adoption_rate,
                "human_tools": config.human_tool_count,
                "claude_tools": config.claude_tool_count,
                "recommendations": len(config.recommendations),
                "detailed_report_lines": analytics_content.count("\n"),
            }

            return GenerationResult(
                success=True,
                output_path=str(analytics_path),
                errors=errors,
                warnings=warnings,
                stats=stats,
            )

        except Exception as e:
            error_msg = f"Failed to generate tool usage analytics: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

            return GenerationResult(
                success=False,
                output_path=str(config.claude_file),
                errors=errors,
                warnings=warnings,
                stats={},
            )

    @staticmethod
    def _priority_label_filter(priority: int) -> str:
        """Convert priority number to label."""
        labels = {
            1: "HIGH",
            2: "MEDIUM",
            3: "LOW",
        }
        return labels.get(priority, "UNKNOWN")
