"""
MCP Usage Analytics Generator - Generates MCP usage reports.

Generates analytics section for CLAUDE.md showing:
- Configured MCP servers and their status
- Usage recommendations
- Connection health
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from claude_automation.schemas import GenerationResult, MCPUsageAnalyticsConfig

logger = logging.getLogger(__name__)


class MCPUsageAnalyticsGenerator:
    """Generate MCP usage analytics section for CLAUDE.md."""

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
        Generate MCP usage analytics section.

        Args:
            config: MCP usage analytics configuration

        Returns:
            GenerationResult with success status and output path
        """
        errors = []
        warnings = []

        try:
            # Load template
            template = self.env.get_template("mcp_usage_analytics.j2")

            # Render content
            content = template.render(
                config=config,
                timestamp=config.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            )

            # Determine output path
            output_path = config.claude_file

            # Append to CLAUDE.md if it exists, otherwise warn
            if output_path.exists():
                # Read existing content
                with open(output_path) as f:
                    existing_content = f.read()

                # Check if MCP analytics section already exists
                mcp_section_marker = "## 🔌 MCP Server Status"
                if mcp_section_marker in existing_content:
                    # Remove old section
                    parts = existing_content.split(mcp_section_marker)
                    # Keep everything before the marker
                    existing_content = parts[0].rstrip()

                    # Find next ## heading if exists
                    if len(parts) > 1:
                        remaining = parts[1]
                        next_section_idx = remaining.find("\n## ")
                        if next_section_idx != -1:
                            # Append everything after the old MCP section
                            existing_content += (
                                "\n\n" + remaining[next_section_idx + 1 :]
                            )

                # Append new MCP section
                final_content = existing_content.rstrip() + "\n\n" + content + "\n"

                # Write back
                with open(output_path, "w") as f:
                    f.write(final_content)

                logger.info(f"Appended MCP analytics to {output_path}")
            else:
                warnings.append(
                    f"CLAUDE.md does not exist at {output_path}, cannot append MCP analytics"
                )
                logger.warning(warnings[-1])

                return GenerationResult(
                    success=False,
                    output_path=str(output_path),
                    errors=errors,
                    warnings=warnings,
                    stats={},
                )

            # Build stats
            stats = {
                "configured_servers": config.total_configured_servers,
                "connected_servers": len(config.connected_servers),
                "unused_servers": len(config.unused_servers),
                "recommendations": len(config.recommendations),
                "total_invocations": config.total_invocations,
            }

            return GenerationResult(
                success=True,
                output_path=str(output_path),
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
