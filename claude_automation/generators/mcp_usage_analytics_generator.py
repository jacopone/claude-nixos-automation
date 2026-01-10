"""
MCP Usage Analytics Generator - Generates MCP usage reports.

Generates detailed analytics report in .claude/mcp-analytics.md.
No longer embeds into CLAUDE.md - full report is linked from Dynamic Context section.

Philosophy:
- CLAUDE.md: Links to analytics (slim, policies-only)
- mcp-analytics.md: Full detailed usage stats (human decision support)
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from claude_automation.schemas import GenerationResult, MCPUsageAnalyticsConfig

logger = logging.getLogger(__name__)


class MCPUsageAnalyticsGenerator:
    """Generate MCP usage analytics to separate report file."""

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
        self.env.filters["status_icon"] = self._status_icon_filter
        self.env.filters["priority_label"] = self._priority_label_filter

    def generate(self, config: MCPUsageAnalyticsConfig) -> GenerationResult:
        """
        Generate MCP usage analytics to separate report file.

        Writes full analytics to .claude/mcp-analytics.md only.
        CLAUDE.md is no longer modified (it links to the report).

        Args:
            config: MCP usage analytics configuration

        Returns:
            GenerationResult with success status and output paths
        """
        errors = []
        warnings = []
        timestamp = config.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Generate full analytics for separate file
            analytics_template = self.env.get_template("mcp_usage_analytics.j2")
            analytics_content = analytics_template.render(
                config=config,
                timestamp=timestamp,
            )

            # Write full analytics to .claude/mcp-analytics.md
            claude_md_path = config.claude_file
            analytics_path = claude_md_path.parent / ".claude" / "mcp-analytics.md"
            analytics_path.parent.mkdir(parents=True, exist_ok=True)

            with open(analytics_path, "w") as f:
                f.write(analytics_content)

            logger.info(f"Wrote detailed MCP analytics to {analytics_path}")

            # Build stats
            stats = {
                "configured_servers": config.total_configured_servers,
                "connected_servers": len(config.connected_servers),
                "unused_servers": len(config.unused_servers),
                "recommendations": len(config.recommendations),
                "total_invocations": config.total_invocations,
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
            error_msg = f"Failed to generate MCP analytics: {e}"
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
    def _status_icon_filter(status: str) -> str:
        """Convert status enum to icon."""
        status_icons = {
            "connected": "✓",
            "disconnected": "○",
            "error": "✗",
            "not_installed": "⚠",
            "unknown": "?",
        }
        return status_icons.get(status, "?")

    @staticmethod
    def _priority_label_filter(priority: int) -> str:
        """Convert priority number to label."""
        labels = {
            1: "HIGH",
            2: "MEDIUM",
            3: "LOW",
        }
        return labels.get(priority, "UNKNOWN")
