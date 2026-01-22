"""
Tool Usage Analyzer - Analyzes system tool installation and usage patterns.

This analyzer:
1. Parses packages.nix to extract all installed tools
2. Analyzes Fish command history for tool usage (human, Claude, scripts)
3. Generates usage statistics and recommendations
4. Identifies dormant tools and policy violations
"""

import logging
import re
from collections import defaultdict
from pathlib import Path

from claude_automation.analyzers.recommendations import ToolRecommendationBuilder
from claude_automation.analyzers.sessions import FishLogParser
from claude_automation.schemas.tool_usage import (
    ToolCategory,
    ToolInfo,
    ToolUsageAnalyticsConfig,
    ToolUsageRecommendation,
    ToolUsageStats,
)
from claude_automation.tool_categories import (
    get_tool_category,
)

logger = logging.getLogger(__name__)


class ToolUsageAnalyzer:
    """Analyze system tool installation and usage patterns."""

    def __init__(self, project_path: Path):
        """Initialize analyzer with project path."""
        self.project_path = project_path.resolve()
        self.packages_nix_path = self.project_path / "modules" / "core" / "packages.nix"
        self.fish_log_path = (
            Path.home() / ".local" / "share" / "fish" / "command-source.jsonl"
        )
        self.claude_projects_dir = Path.home() / ".claude" / "projects"

    def analyze(self, analysis_period_days: int = 30) -> ToolUsageAnalyticsConfig:
        """
        Analyze tool installation and usage.

        Args:
            analysis_period_days: Number of days to analyze usage for

        Returns:
            ToolUsageAnalyticsConfig with full analysis results
        """
        logger.info(f"Analyzing tool usage for: {self.project_path}")

        # Step 1: Parse tool inventory from packages.nix
        tool_inventory = self._parse_packages_nix()
        logger.info(f"Found {len(tool_inventory)} tools in packages.nix")

        # Step 2: Analyze usage from Fish command logs
        usage_stats = self._analyze_fish_logs(tool_inventory, analysis_period_days)
        logger.info(f"Analyzed usage for {len(usage_stats)} tools")

        # Step 3: Identify used vs dormant tools
        used_tools, dormant_tools = self._classify_tools(tool_inventory, usage_stats)

        # Step 4: Calculate aggregate metrics
        total_commands = sum(stat.total_invocations for stat in usage_stats.values())
        human_tools = {
            name for name, stat in usage_stats.items() if stat.human_invocations > 0
        }
        claude_tools = {
            name for name, stat in usage_stats.items() if stat.claude_invocations > 0
        }

        # Step 5: Calculate usage by category
        usage_by_category = self._calculate_category_usage(usage_stats)

        # Step 6: Generate recommendations
        recommendations = self._generate_recommendations(
            tool_inventory, usage_stats, dormant_tools
        )

        return ToolUsageAnalyticsConfig(
            project_path=self.project_path,
            analysis_period_days=analysis_period_days,
            total_tools=len(tool_inventory),
            tool_inventory=tool_inventory,
            used_tools=list(usage_stats.values()),
            dormant_tools=dormant_tools,
            total_commands_tracked=total_commands,
            human_tool_count=len(human_tools),
            claude_tool_count=len(claude_tools),
            recommendations=recommendations,
            usage_by_category=usage_by_category,
        )

    def _parse_packages_nix(self) -> list[ToolInfo]:
        """
        Parse packages.nix to extract tool inventory.

        Returns:
            List of ToolInfo objects
        """
        if not self.packages_nix_path.exists():
            logger.warning(f"packages.nix not found at: {self.packages_nix_path}")
            return []

        tools = []

        # Category detection patterns
        category_patterns = {
            "# AI Tools": ToolCategory.AI_TOOLS,
            "# dev tools": ToolCategory.DEV_TOOLS,
            "# Development Tools": ToolCategory.DEV_TOOLS,
            "# Modern CLI Tools": ToolCategory.MODERN_CLI,
            "# system tools": ToolCategory.SYSTEM_TOOLS,
            "# productivity tools": ToolCategory.PRODUCTIVITY,
            "# Network & Security": ToolCategory.NETWORK_SECURITY,
            "# File Management": ToolCategory.FILE_MANAGEMENT,
            "# Database Tools": ToolCategory.DATABASE_TOOLS,
            "# file searchers": ToolCategory.FILE_MANAGEMENT,
            "# fonts": ToolCategory.FONTS,
        }

        with open(self.packages_nix_path) as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Update category based on comments
            for pattern, _category in category_patterns.items():
                if pattern in line:
                    break

            # Match simple package: helix  # Description - URL
            match = re.match(
                r"\s+(\w+[\w.-]*)\s+#\s+(.+?)(?:\s+-\s+(https?://\S+))?$", line
            )
            if match:
                name, desc, url = match.groups()
                # Use hardcoded category from tool_categories.py
                category = get_tool_category(name)
                tools.append(
                    ToolInfo(
                        name=name,
                        description=desc.strip() if desc else "",
                        url=url or "",
                        category=category,
                        package_line=line_num,
                    )
                )
                continue

            # Match wrapper scripts: (pkgs.writeShellScriptBin "name" ...)
            match = re.search(r'writeShellScriptBin\s+"([^"]+)"', line)
            if match:
                name = match.group(1)
                # Look for comment on same or previous line
                desc = ""
                if "#" in line:
                    desc = line.split("#", 1)[1].strip()
                category = get_tool_category(name)
                tools.append(
                    ToolInfo(
                        name=name,
                        description=desc,
                        category=category,
                        package_line=line_num,
                    )
                )
                continue

            # Match direct package references: pkgs.something
            match = re.search(r"pkgs\.(\w+[\w.-]*)", line)
            if match and not line.strip().startswith("#"):
                name = match.group(1)
                # Skip if already found
                if any(t.name == name for t in tools):
                    continue
                category = get_tool_category(name)
                tools.append(
                    ToolInfo(
                        name=name,
                        description="",
                        category=category,
                        package_line=line_num,
                    )
                )

        logger.info(f"Parsed {len(tools)} tools from packages.nix")
        return tools

    def _analyze_fish_logs(
        self, tool_inventory: list[ToolInfo], days: int
    ) -> dict[str, ToolUsageStats]:
        """
        Analyze Fish command logs for tool usage using FishLogParser.

        Args:
            tool_inventory: List of installed tools
            days: Number of days to analyze

        Returns:
            Dict mapping tool name to usage stats
        """
        # Build set of tool names for fast lookup
        tool_names = {tool.name for tool in tool_inventory}

        # Parse logs using extracted FishLogParser
        parser = FishLogParser(self.fish_log_path)
        usage_data = parser.parse(tool_names, days)

        # Convert FishToolUsageData to ToolUsageStats schema objects
        usage_stats = {}
        for tool_name, data in usage_data.items():
            if data.total > 0:
                usage_stats[tool_name] = ToolUsageStats(
                    tool_name=data.tool_name,
                    total_invocations=data.total,
                    human_invocations=data.human,
                    claude_invocations=data.claude,
                    script_invocations=data.script,
                    first_used=data.first_used,
                    last_used=data.last_used,
                )

        return usage_stats

    def _classify_tools(
        self, tool_inventory: list[ToolInfo], usage_stats: dict[str, ToolUsageStats]
    ) -> tuple[list[ToolUsageStats], list[ToolInfo]]:
        """
        Classify tools as used or dormant.

        Args:
            tool_inventory: All installed tools
            usage_stats: Usage statistics

        Returns:
            (used_tools, dormant_tools) tuple
        """
        used_tool_names = set(usage_stats.keys())
        used_tools = list(usage_stats.values())

        dormant_tools = [
            tool for tool in tool_inventory if tool.name not in used_tool_names
        ]

        return used_tools, dormant_tools

    def _calculate_category_usage(
        self, usage_stats: dict[str, ToolUsageStats]
    ) -> dict[str, int]:
        """
        Calculate tool usage by category.

        Args:
            usage_stats: Usage statistics

        Returns:
            Dict mapping category name to usage count
        """
        category_usage = defaultdict(int)

        for tool_name, stats in usage_stats.items():
            category = get_tool_category(tool_name)
            category_usage[category.value] += stats.total_invocations

        return dict(category_usage)

    def _generate_recommendations(
        self,
        tool_inventory: list[ToolInfo],
        usage_stats: dict[str, ToolUsageStats],
        dormant_tools: list[ToolInfo],
    ) -> list[ToolUsageRecommendation]:
        """Generate actionable recommendations using ToolRecommendationBuilder."""
        return ToolRecommendationBuilder(
            tool_inventory=tool_inventory,
            usage_stats=usage_stats,
            dormant_tools=dormant_tools,
        ).build_all()
