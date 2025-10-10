"""
MCP Usage Analytics Generator - Generates MCP usage reports.

Generates two outputs:
1. Minimal status section for CLAUDE.md (Claude's operational context)
2. Detailed analytics report in .claude/mcp-analytics.md (human decision support)

Philosophy:
- CLAUDE.md: What Claude needs to know (server availability, basic status)
- mcp-analytics.md: What humans need to see (usage stats, costs, recommendations)
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from claude_automation.schemas import GenerationResult, MCPUsageAnalyticsConfig

logger = logging.getLogger(__name__)


class MCPUsageAnalyticsGenerator:
    """Generate MCP usage analytics with separate outputs for AI and human."""

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
        Generate MCP usage analytics with dual outputs.

        Writes:
        1. Minimal status to CLAUDE.md (for Claude's context)
        2. Full analytics to .claude/mcp-analytics.md (for human review)

        Args:
            config: MCP usage analytics configuration

        Returns:
            GenerationResult with success status and output paths
        """
        errors = []
        warnings = []
        timestamp = config.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # === 1. Generate minimal status for CLAUDE.md ===
            minimal_template = self.env.get_template("mcp_usage_status_minimal.j2")
            minimal_content = minimal_template.render(
                config=config,
                timestamp=timestamp,
            )

            # Update CLAUDE.md with minimal section
            claude_md_path = config.claude_file
            if claude_md_path.exists():
                self._update_claude_md_section(
                    claude_md_path, minimal_content, "## 🔌 MCP Servers"
                )
                logger.info(f"Updated minimal MCP status in {claude_md_path}")
            else:
                warnings.append(
                    f"CLAUDE.md does not exist at {claude_md_path}, skipping minimal status"
                )
                logger.warning(warnings[-1])

            # === 2. Generate full analytics for separate file ===
            analytics_template = self.env.get_template("mcp_usage_analytics.j2")
            analytics_content = analytics_template.render(
                config=config,
                timestamp=timestamp,
            )

            # Write full analytics to .claude/mcp-analytics.md
            analytics_path = claude_md_path.parent / ".claude" / "mcp-analytics.md"
            analytics_path.parent.mkdir(parents=True, exist_ok=True)

            with open(analytics_path, "w") as f:
                f.write(analytics_content)

            logger.info(f"Wrote detailed analytics to {analytics_path}")

            # Build stats
            stats = {
                "configured_servers": config.total_configured_servers,
                "connected_servers": len(config.connected_servers),
                "unused_servers": len(config.unused_servers),
                "recommendations": len(config.recommendations),
                "total_invocations": config.total_invocations,
                "minimal_section_lines": minimal_content.count("\n"),
                "detailed_report_lines": analytics_content.count("\n"),
            }

            return GenerationResult(
                success=True,
                output_path=str(claude_md_path),
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

    def _update_claude_md_section(
        self, claude_md_path: Path, new_content: str, section_marker: str
    ) -> None:
        """
        Update a specific section in CLAUDE.md, replacing old content.

        Handles both old and new section markers for backwards compatibility:
        - Old: "## 🔌 MCP Server Status"
        - New: "## 🔌 MCP Servers"

        Args:
            claude_md_path: Path to CLAUDE.md
            new_content: New section content to insert
            section_marker: Section heading to replace (e.g., "## 🔌 MCP Servers")
        """
        with open(claude_md_path) as f:
            existing_content = f.read()

        # List of possible markers (for backwards compatibility)
        markers = [section_marker, "## 🔌 MCP Server Status"]

        # Remove all matching sections
        for marker in markers:
            if marker in existing_content:
                # Remove old section
                parts = existing_content.split(marker)
                # Keep everything before the marker
                existing_content = parts[0].rstrip()

                # Find next ## heading if exists
                if len(parts) > 1:
                    remaining = parts[1]
                    next_section_idx = remaining.find("\n## ")
                    if next_section_idx != -1:
                        # Append everything after the old section
                        existing_content += "\n\n" + remaining[next_section_idx + 1 :]

        # Append new section
        final_content = existing_content.rstrip() + "\n\n" + new_content + "\n"

        # Write back
        with open(claude_md_path, "w") as f:
            f.write(final_content)

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
