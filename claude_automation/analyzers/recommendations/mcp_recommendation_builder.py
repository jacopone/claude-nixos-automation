"""
MCP Recommendation Builder - Focused recommendation generation.

Extracted from mcp_usage_analyzer._generate_recommendations (CCN 26)
to reduce complexity with single-responsibility methods (CCN ~2-3 each).
"""

from __future__ import annotations

from claude_automation.schemas import (
    MCPServerInfo,
    MCPServerSessionUtilization,
    MCPServerStatus,
    MCPToolUsage,
    MCPUsageRecommendation,
)


class MCPRecommendationBuilder:
    """
    Builder for MCP usage recommendations.

    Uses builder pattern for clear, composable recommendation generation.
    Each check_* method has CCN < 5 for maintainability.
    """

    def __init__(
        self,
        servers: list[MCPServerInfo],
        usage: list[MCPToolUsage],
        server_utilization: list[MCPServerSessionUtilization],
    ):
        self.servers = servers
        self.usage = usage
        self.server_utilization = server_utilization
        self._recommendations: list[MCPUsageRecommendation] = []

        # Pre-compute lookup for efficiency
        self._used_server_names = {
            u.server_name for u in usage if u.invocation_count > 0
        }

    def check_unused_servers(self) -> MCPRecommendationBuilder:
        """Flag connected servers with no recorded usage."""
        for server in self.servers:
            if (
                server.name not in self._used_server_names
                and server.status == MCPServerStatus.CONNECTED
            ):
                scope_info = server.config_location.split()[0].lower()
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="review_unused",
                        reason=f"Server '{server.name}' is connected but has no recorded usage",
                        action=f"Consider disabling '{server.name}' if not needed ({scope_info} scope)",
                        priority=3,
                    )
                )
        return self

    def check_low_roi_servers(self) -> MCPRecommendationBuilder:
        """Flag servers with high token cost relative to invocations."""
        for tool_usage in self.usage:
            if tool_usage.invocation_count > 0 and tool_usage.roi_score < 1.0:
                cost_str = f"${tool_usage.estimated_cost_usd:.4f}"
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=tool_usage.server_name,
                        recommendation_type="optimize",
                        reason=f"Server '{tool_usage.server_name}' has low ROI: {tool_usage.invocation_count} invocations for {tool_usage.total_tokens:,} tokens (est. {cost_str})",
                        action=f"Review usage patterns. Consider if '{tool_usage.server_name}' is cost-effective ({tool_usage.scope} scope)",
                        priority=2,
                    )
                )
        return self

    def check_high_value_servers(self) -> MCPRecommendationBuilder:
        """Highlight servers with excellent efficiency."""
        for tool_usage in self.usage:
            if tool_usage.invocation_count >= 5 and tool_usage.roi_score > 10.0:
                cost_str = f"${tool_usage.estimated_cost_usd:.4f}"
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=tool_usage.server_name,
                        recommendation_type="highlight_value",
                        reason=f"Server '{tool_usage.server_name}' provides excellent value: {tool_usage.invocation_count} invocations for only {tool_usage.total_tokens:,} tokens (est. {cost_str})",
                        action=f"Keep '{tool_usage.server_name}' enabled. High efficiency tool ({tool_usage.scope} scope)",
                        priority=3,
                    )
                )
        return self

    def check_high_token_consumers(self) -> MCPRecommendationBuilder:
        """Flag servers consuming significant tokens for awareness."""
        for tool_usage in self.usage:
            if tool_usage.total_tokens > 100_000:
                cost_str = f"${tool_usage.estimated_cost_usd:.2f}"
                avg_tokens = int(tool_usage.avg_tokens_per_invocation)
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=tool_usage.server_name,
                        recommendation_type="high_usage",
                        reason=f"Server '{tool_usage.server_name}' consumed {tool_usage.total_tokens:,} tokens (est. {cost_str})",
                        action=f"Frequent user: {tool_usage.invocation_count} calls, ~{avg_tokens:,} tokens/call ({tool_usage.scope} scope)",
                        priority=3,
                    )
                )
        return self

    def check_connection_errors(self) -> MCPRecommendationBuilder:
        """Flag servers with connection errors."""
        for server in self.servers:
            if server.status == MCPServerStatus.ERROR:
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="fix_errors",
                        reason=f"Server '{server.name}' has connection errors",
                        action=f"Check configuration and ensure '{server.command}' is available",
                        priority=1,
                    )
                )
        return self

    def check_disconnected_servers(self) -> MCPRecommendationBuilder:
        """Flag servers that are configured but not connected."""
        for server in self.servers:
            if server.status == MCPServerStatus.DISCONNECTED:
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="check_connection",
                        reason=f"Server '{server.name}' is configured but not connected",
                        action="Run 'claude mcp list' to diagnose connection issues",
                        priority=2,
                    )
                )
        return self

    def check_no_servers_configured(self) -> MCPRecommendationBuilder:
        """Suggest common servers if none are configured."""
        if len(self.servers) == 0:
            self._recommendations.append(
                MCPUsageRecommendation(
                    server_name="sequential-thinking",
                    recommendation_type="install_missing",
                    reason="No MCP servers configured",
                    action="Consider installing '@modelcontextprotocol/server-sequential-thinking' for improved reasoning",
                    priority=2,
                )
            )
        return self

    def check_poor_utilization(self) -> MCPRecommendationBuilder:
        """Flag global servers with poor session utilization."""
        for util in self.server_utilization:
            if (
                "global" in util.scope.lower()
                and util.utilization_rate < 20.0
                and util.loaded_sessions > 10
            ):
                wasted_tokens = util.total_wasted_overhead
                wasted_sessions = util.wasted_sessions
                utilization_pct = util.utilization_rate

                priority = 1 if wasted_tokens > 500_000 else 2
                self._recommendations.append(
                    MCPUsageRecommendation(
                        server_name=util.server_name,
                        recommendation_type="poor_utilization",
                        reason=f"Server '{util.server_name}' loads in all sessions but only used in {utilization_pct:.1f}% ({util.used_sessions}/{util.loaded_sessions} sessions)",
                        action=f"Consider moving '{util.server_name}' to project-level config. Wasted overhead: ~{wasted_tokens:,} tokens across {wasted_sessions} sessions",
                        priority=priority,
                    )
                )
        return self

    def build(self) -> list[MCPUsageRecommendation]:
        """Return all collected recommendations."""
        return self._recommendations

    def build_all(self) -> list[MCPUsageRecommendation]:
        """Run all checks and return recommendations."""
        return (
            self.check_unused_servers()
            .check_low_roi_servers()
            .check_high_value_servers()
            .check_high_token_consumers()
            .check_connection_errors()
            .check_disconnected_servers()
            .check_no_servers_configured()
            .check_poor_utilization()
            .build()
        )
