"""
Tool Usage Analytics Generator - Generates tool usage reports.

Generates two outputs:
1. Minimal status section for CLAUDE.md (Claude's operational context)
2. Detailed analytics report in .claude/tool-analytics.md (human decision support)

Philosophy:
- CLAUDE.md: What Claude needs to know (adoption rate, top tools, basic stats)
- tool-analytics.md: What humans need to see (detailed usage, categories, recommendations)
"""

import logging
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from claude_automation.schemas import GenerationResult
from claude_automation.schemas.tool_usage import ToolUsageAnalyticsConfig

logger = logging.getLogger(__name__)


class ToolUsageAnalyticsGenerator:
    """Generate tool usage analytics with separate outputs for AI and human."""

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
        Generate tool usage analytics with dual outputs.

        Writes:
        1. Minimal status to CLAUDE.md (for Claude's context)
        2. Full analytics to .claude/tool-analytics.md (for human review)

        Args:
            config: Tool usage analytics configuration

        Returns:
            GenerationResult with success status and output paths
        """
        errors = []
        warnings = []
        timestamp = config.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # === 1. Generate minimal status for CLAUDE.md ===
            minimal_template = self.env.get_template("tool_usage_status_minimal.j2")
            minimal_content = minimal_template.render(
                config=config,
                timestamp=timestamp,
            )

            # Update CLAUDE.md with minimal section
            claude_md_path = config.claude_file
            if claude_md_path.exists():
                self._update_claude_md_section(
                    claude_md_path, minimal_content, "## 📦 System Tool Usage"
                )
                logger.info(f"Updated minimal tool usage status in {claude_md_path}")
            else:
                warnings.append(
                    f"CLAUDE.md does not exist at {claude_md_path}, skipping minimal status"
                )
                logger.warning(warnings[-1])

            # === 2. Generate full analytics for separate file ===
            analytics_template = self.env.get_template("tool_usage_analytics.j2")
            analytics_content = analytics_template.render(
                config=config,
                timestamp=timestamp,
            )

            # Write full analytics to .claude/tool-analytics.md
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

    def _update_claude_md_section(
        self, claude_md_path: Path, new_content: str, section_marker: str
    ) -> None:
        """
        Update a specific section in CLAUDE.md, replacing old content.

        Args:
            claude_md_path: Path to CLAUDE.md
            new_content: New section content to insert
            section_marker: Section heading to replace (e.g., "## 📦 System Tool Usage")
        """
        with open(claude_md_path) as f:
            existing_content = f.read()

        # List of possible markers (for backwards compatibility)
        markers = [section_marker, "## 📦 System Tools", "## 📦 Tool Usage"]

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
    def _priority_label_filter(priority: int) -> str:
        """Convert priority number to label."""
        labels = {
            1: "HIGH",
            2: "MEDIUM",
            3: "LOW",
        }
        return labels.get(priority, "UNKNOWN")
