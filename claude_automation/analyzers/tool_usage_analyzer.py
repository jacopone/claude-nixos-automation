"""
Tool Usage Analyzer - Analyzes system tool installation and usage patterns.

This analyzer:
1. Parses packages.nix to extract all installed tools
2. Analyzes Fish command history for tool usage (human, Claude, scripts)
3. Generates usage statistics and recommendations
4. Identifies dormant tools and policy violations
"""

import json
import logging
import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from claude_automation.schemas.tool_usage import (
    ToolCategory,
    ToolInfo,
    ToolUsageAnalyticsConfig,
    ToolUsageRecommendation,
    ToolUsageStats,
)
from claude_automation.tool_categories import (
    ALL_CATEGORIZED_TOOLS,
    DORMANCY_THRESHOLD_DAYS,
    MIN_USAGE_FOR_ADOPTION,
    MODERN_VS_TRADITIONAL,
    get_canonical_tool_name,
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
        Analyze Fish command logs for tool usage.

        Args:
            tool_inventory: List of installed tools
            days: Number of days to analyze

        Returns:
            Dict mapping tool name to usage stats
        """
        if not self.fish_log_path.exists():
            logger.warning(f"Fish command log not found: {self.fish_log_path}")
            return {}

        # Build set of tool names for fast lookup
        tool_names = {tool.name for tool in tool_inventory}

        # Initialize usage tracking
        usage_data = defaultdict(
            lambda: {
                "tool_name": "",
                "total": 0,
                "human": 0,
                "claude": 0,
                "script": 0,
                "first_used": None,
                "last_used": None,
            }
        )

        # Calculate cutoff date
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        cutoff_timestamp = int(cutoff_date.timestamp())

        # Parse JSONL log
        with open(self.fish_log_path) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    if not line.strip():
                        continue

                    data = json.loads(line)

                    # Extract fields
                    timestamp = data.get("ts", 0)
                    cmd = data.get("cmd", "")
                    source = data.get("src", "human")

                    # Skip if outside analysis period
                    if timestamp < cutoff_timestamp:
                        continue

                    # Extract tool name from command (first token)
                    if not cmd:
                        continue

                    # Get first token (command name)
                    first_token = cmd.split()[0] if cmd.split() else ""
                    if not first_token:
                        continue

                    # Handle path prefixes (e.g., /usr/bin/git → git)
                    command_name = Path(first_token).name

                    # Get canonical tool name
                    tool_name = get_canonical_tool_name(command_name)

                    # Skip if not an installed tool
                    if (
                        tool_name not in tool_names
                        and tool_name not in ALL_CATEGORIZED_TOOLS
                    ):
                        continue

                    # Initialize if first time seeing this tool
                    if usage_data[tool_name]["tool_name"] == "":
                        usage_data[tool_name]["tool_name"] = tool_name

                    # Update counts
                    usage_data[tool_name]["total"] += 1

                    if source == "human":
                        usage_data[tool_name]["human"] += 1
                    elif source == "claude-code":
                        usage_data[tool_name]["claude"] += 1
                    elif source in ("script", "bash-script", "python-script"):
                        usage_data[tool_name]["script"] += 1

                    # Update timestamps
                    ts_datetime = datetime.fromtimestamp(timestamp, tz=UTC)
                    if (
                        usage_data[tool_name]["first_used"] is None
                        or ts_datetime < usage_data[tool_name]["first_used"]
                    ):
                        usage_data[tool_name]["first_used"] = ts_datetime
                    if (
                        usage_data[tool_name]["last_used"] is None
                        or ts_datetime > usage_data[tool_name]["last_used"]
                    ):
                        usage_data[tool_name]["last_used"] = ts_datetime

                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON at line {line_num}: {e}")
                except Exception as e:
                    logger.debug(f"Error processing line {line_num}: {e}")

        # Convert to ToolUsageStats objects
        usage_stats = {}
        for tool_name, data in usage_data.items():
            if data["total"] > 0:
                usage_stats[tool_name] = ToolUsageStats(
                    tool_name=data["tool_name"],
                    total_invocations=data["total"],
                    human_invocations=data["human"],
                    claude_invocations=data["claude"],
                    script_invocations=data["script"],
                    first_used=data["first_used"],
                    last_used=data["last_used"],
                )

        logger.info(f"Found usage data for {len(usage_stats)} tools")
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
        """
        Generate actionable recommendations.

        Args:
            tool_inventory: All installed tools
            usage_stats: Usage statistics
            dormant_tools: Tools with no usage

        Returns:
            List of recommendations
        """
        recommendations = []

        # Recommendation 1: Dormant tools (candidates for removal)
        if len(dormant_tools) > 10:
            # Group by category
            dormant_by_category = defaultdict(list)
            for tool in dormant_tools:
                dormant_by_category[tool.category].append(tool.name)

            for category, tools in dormant_by_category.items():
                if len(tools) >= 3:
                    tools_str = ", ".join(tools[:5])
                    if len(tools) > 5:
                        tools_str += f", and {len(tools) - 5} more"

                    recommendations.append(
                        ToolUsageRecommendation(
                            tool_name=f"{category.value} tools",
                            recommendation_type="remove_dormant",
                            reason=f"{len(tools)} {category.value} tools unused in last {DORMANCY_THRESHOLD_DAYS} days",
                            action=f"Consider removing: {tools_str}",
                            priority=2 if len(tools) > 10 else 3,
                        )
                    )

        # Recommendation 2: High-value tools (frequently used)
        high_value_tools = [
            (name, stats)
            for name, stats in usage_stats.items()
            if stats.total_invocations >= MIN_USAGE_FOR_ADOPTION * 5
        ]
        high_value_tools.sort(key=lambda x: x[1].total_invocations, reverse=True)

        for tool_name, stats in high_value_tools[:5]:
            recommendations.append(
                ToolUsageRecommendation(
                    tool_name=tool_name,
                    recommendation_type="highlight_value",
                    reason=f"Highly used: {stats.total_invocations} invocations (human: {stats.human_invocations}, Claude: {stats.claude_invocations})",
                    action=f"Keep {tool_name} - provides excellent value",
                    priority=3,
                )
            )

        # Recommendation 3: Claude not using modern tools
        for modern_tool, traditional_tool in MODERN_VS_TRADITIONAL.items():
            if modern_tool in usage_stats:
                stats = usage_stats[modern_tool]
                if stats.claude_invocations == 0 and stats.human_invocations > 0:
                    recommendations.append(
                        ToolUsageRecommendation(
                            tool_name=modern_tool,
                            recommendation_type="policy_violation",
                            reason=f"Claude not using {modern_tool} (modern {traditional_tool}), but humans use it {stats.human_invocations} times",
                            action=f"Update CLAUDE.md policy to enforce {modern_tool} usage",
                            priority=1,
                        )
                    )

        # Recommendation 4: Human vs Claude gaps
        human_only_tools = [
            (name, stats)
            for name, stats in usage_stats.items()
            if stats.human_invocations >= 10 and stats.claude_invocations == 0
        ]
        if len(human_only_tools) > 5:
            tools_str = ", ".join([name for name, _ in human_only_tools[:10]])
            recommendations.append(
                ToolUsageRecommendation(
                    tool_name="multiple",
                    recommendation_type="human_vs_claude_gap",
                    reason=f"{len(human_only_tools)} tools used frequently by humans but never by Claude",
                    action=f"Consider documenting usage in CLAUDE.md for: {tools_str}",
                    priority=2,
                )
            )

        claude_only_tools = [
            (name, stats)
            for name, stats in usage_stats.items()
            if stats.claude_invocations >= 10 and stats.human_invocations == 0
        ]
        if len(claude_only_tools) > 3:
            tools_str = ", ".join([name for name, _ in claude_only_tools[:10]])
            recommendations.append(
                ToolUsageRecommendation(
                    tool_name="multiple",
                    recommendation_type="human_vs_claude_gap",
                    reason=f"{len(claude_only_tools)} tools used by Claude but never by humans",
                    action=f"AI-optimized tools working well: {tools_str}",
                    priority=3,
                )
            )

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority)

        return recommendations
