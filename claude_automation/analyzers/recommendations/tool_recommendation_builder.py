"""
Tool Recommendation Builder - Focused recommendation generation.

Extracted from tool_usage_analyzer._generate_recommendations (CCN 24)
to reduce complexity with single-responsibility methods (CCN ~3-4 each).
"""

from __future__ import annotations

from collections import defaultdict

from claude_automation.schemas.tool_usage import (
    ToolInfo,
    ToolUsageRecommendation,
    ToolUsageStats,
)
from claude_automation.tool_categories import (
    DORMANCY_THRESHOLD_DAYS,
    MIN_USAGE_FOR_ADOPTION,
    MODERN_VS_TRADITIONAL,
)


class ToolRecommendationBuilder:
    """
    Builder for tool usage recommendations.

    Uses builder pattern for clear, composable recommendation generation.
    Each check_* method has CCN < 5 for maintainability.
    """

    def __init__(
        self,
        tool_inventory: list[ToolInfo],
        usage_stats: dict[str, ToolUsageStats],
        dormant_tools: list[ToolInfo],
    ):
        self.tool_inventory = tool_inventory
        self.usage_stats = usage_stats
        self.dormant_tools = dormant_tools
        self._recommendations: list[ToolUsageRecommendation] = []

    def check_dormant_tools(self) -> ToolRecommendationBuilder:
        """Flag tools with no usage, grouped by category."""
        if len(self.dormant_tools) <= 10:
            return self

        # Group by category
        dormant_by_category = defaultdict(list)
        for tool in self.dormant_tools:
            dormant_by_category[tool.category].append(tool.name)

        for category, tools in dormant_by_category.items():
            if len(tools) >= 3:
                tools_str = ", ".join(tools[:5])
                if len(tools) > 5:
                    tools_str += f", and {len(tools) - 5} more"

                self._recommendations.append(
                    ToolUsageRecommendation(
                        tool_name=f"{category.value} tools",
                        recommendation_type="remove_dormant",
                        reason=f"{len(tools)} {category.value} tools unused in last {DORMANCY_THRESHOLD_DAYS} days",
                        action=f"Consider removing: {tools_str}",
                        priority=2 if len(tools) > 10 else 3,
                    )
                )
        return self

    def check_high_value_tools(self) -> ToolRecommendationBuilder:
        """Highlight frequently used tools."""
        high_value_tools = [
            (name, stats)
            for name, stats in self.usage_stats.items()
            if stats.total_invocations >= MIN_USAGE_FOR_ADOPTION * 5
        ]
        high_value_tools.sort(key=lambda x: x[1].total_invocations, reverse=True)

        for tool_name, stats in high_value_tools[:5]:
            self._recommendations.append(
                ToolUsageRecommendation(
                    tool_name=tool_name,
                    recommendation_type="highlight_value",
                    reason=f"Highly used: {stats.total_invocations} invocations (human: {stats.human_invocations}, Claude: {stats.claude_invocations})",
                    action=f"Keep {tool_name} - provides excellent value",
                    priority=3,
                )
            )
        return self

    def check_policy_violations(self) -> ToolRecommendationBuilder:
        """Flag when Claude isn't using modern tools that humans use."""
        for modern_tool, traditional_tool in MODERN_VS_TRADITIONAL.items():
            if modern_tool in self.usage_stats:
                stats = self.usage_stats[modern_tool]
                if stats.claude_invocations == 0 and stats.human_invocations > 0:
                    self._recommendations.append(
                        ToolUsageRecommendation(
                            tool_name=modern_tool,
                            recommendation_type="policy_violation",
                            reason=f"Claude not using {modern_tool} (modern {traditional_tool}), but humans use it {stats.human_invocations} times",
                            action=f"Update CLAUDE.md policy to enforce {modern_tool} usage",
                            priority=1,
                        )
                    )
        return self

    def check_usage_gaps(self) -> ToolRecommendationBuilder:
        """Flag tools with significant human/Claude usage disparity."""
        # Human-only tools
        human_only_tools = [
            (name, stats)
            for name, stats in self.usage_stats.items()
            if stats.human_invocations >= 10 and stats.claude_invocations == 0
        ]
        if len(human_only_tools) > 5:
            tools_str = ", ".join([name for name, _ in human_only_tools[:10]])
            self._recommendations.append(
                ToolUsageRecommendation(
                    tool_name="multiple",
                    recommendation_type="human_vs_claude_gap",
                    reason=f"{len(human_only_tools)} tools used frequently by humans but never by Claude",
                    action=f"Consider documenting usage in CLAUDE.md for: {tools_str}",
                    priority=2,
                )
            )

        # Claude-only tools
        claude_only_tools = [
            (name, stats)
            for name, stats in self.usage_stats.items()
            if stats.claude_invocations >= 10 and stats.human_invocations == 0
        ]
        if len(claude_only_tools) > 3:
            tools_str = ", ".join([name for name, _ in claude_only_tools[:10]])
            self._recommendations.append(
                ToolUsageRecommendation(
                    tool_name="multiple",
                    recommendation_type="human_vs_claude_gap",
                    reason=f"{len(claude_only_tools)} tools used by Claude but never by humans",
                    action=f"AI-optimized tools working well: {tools_str}",
                    priority=3,
                )
            )
        return self

    def build(self) -> list[ToolUsageRecommendation]:
        """Return all collected recommendations, sorted by priority."""
        self._recommendations.sort(key=lambda r: r.priority)
        return self._recommendations

    def build_all(self) -> list[ToolUsageRecommendation]:
        """Run all checks and return recommendations."""
        return (
            self.check_dormant_tools()
            .check_high_value_tools()
            .check_policy_violations()
            .check_usage_gaps()
            .build()
        )
