"""
MCP Usage Analyzer - Analyzes configured and used MCP servers.

This analyzer:
1. Discovers configured MCP servers (global and project-level)
2. Checks connection status via 'claude mcp list'
3. Analyzes usage patterns (if logs available)
4. Generates recommendations for optimization
"""

import json
import logging
import subprocess
from pathlib import Path

from claude_automation.schemas import (
    MCPServerInfo,
    MCPServerStatus,
    MCPServerType,
    MCPToolUsage,
    MCPUsageAnalyticsConfig,
    MCPUsageRecommendation,
)

logger = logging.getLogger(__name__)


class MCPUsageAnalyzer:
    """Analyze MCP server configuration and usage."""

    def __init__(self, project_path: Path):
        """Initialize analyzer with project path."""
        self.project_path = project_path.resolve()
        self.global_config_path = Path.home() / ".claude.json"
        self.project_config_path = self.project_path / ".claude" / "mcp.json"

    def analyze(self, analysis_period_days: int = 30) -> MCPUsageAnalyticsConfig:
        """
        Analyze MCP configuration and usage.

        Args:
            analysis_period_days: Number of days to analyze usage for

        Returns:
            MCPUsageAnalyticsConfig with full analysis results
        """
        logger.info(f"Analyzing MCP usage for: {self.project_path}")

        # Step 1: Discover configured servers
        configured_servers = self._discover_configured_servers()
        logger.info(f"Found {len(configured_servers)} configured MCP servers")

        # Step 2: Check connection status
        self._check_server_status(configured_servers)

        # Step 3: Analyze usage (currently placeholder - would parse logs)
        tool_usage = self._analyze_usage(configured_servers, analysis_period_days)

        # Step 4: Generate recommendations
        recommendations = self._generate_recommendations(configured_servers, tool_usage)

        return MCPUsageAnalyticsConfig(
            project_path=self.project_path,
            global_mcp_config=(
                self.global_config_path if self.global_config_path.exists() else None
            ),
            project_mcp_config=(
                self.project_config_path if self.project_config_path.exists() else None
            ),
            configured_servers=configured_servers,
            tool_usage=tool_usage,
            recommendations=recommendations,
            analysis_period_days=analysis_period_days,
        )

    def _discover_configured_servers(self) -> list[MCPServerInfo]:
        """Discover all configured MCP servers from config files."""
        servers = []

        # Check global config
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path) as f:
                    global_config = json.load(f)
                    mcp_servers = global_config.get("mcpServers", {})
                    for name, config in mcp_servers.items():
                        servers.append(
                            self._parse_server_config(
                                name, config, "global (~/.claude.json)"
                            )
                        )
                logger.debug(f"Found {len(mcp_servers)} servers in global config")
            except Exception as e:
                logger.warning(f"Failed to parse global MCP config: {e}")

        # Check project config
        if self.project_config_path.exists():
            try:
                with open(self.project_config_path) as f:
                    project_config = json.load(f)
                    mcp_servers = project_config.get("mcpServers", {})
                    for name, config in mcp_servers.items():
                        servers.append(
                            self._parse_server_config(
                                name, config, "project (.claude/mcp.json)"
                            )
                        )
                logger.debug(f"Found {len(mcp_servers)} servers in project config")
            except Exception as e:
                logger.warning(f"Failed to parse project MCP config: {e}")

        return servers

    def _parse_server_config(
        self, name: str, config: dict, location: str
    ) -> MCPServerInfo:
        """Parse MCP server configuration."""
        command = config.get("command", "")
        args = config.get("args", [])

        # Detect server type
        server_type = MCPServerType.UNKNOWN
        if command == "npx" or "npm" in command:
            server_type = MCPServerType.NPM
        elif command == "python" or command == "python3" or command.endswith(".py"):
            server_type = MCPServerType.PYTHON
        elif command in ["serena", "mcp-nixos"]:
            server_type = MCPServerType.BINARY

        # Get description from common servers
        descriptions = {
            "sequential-thinking": "Step-by-step reasoning for complex problems",
            "serena": "Semantic code analysis toolkit",
            "mcp-nixos": "NixOS package and option information",
            "filesystem": "File operations with access controls",
            "git": "Git repository operations",
            "github": "GitHub API operations",
            "google-drive": "Google Drive file operations",
            "postgres": "PostgreSQL database queries",
        }

        description = descriptions.get(name, "")

        return MCPServerInfo(
            name=name,
            type=server_type,
            command=command,
            args=args,
            status=MCPServerStatus.UNKNOWN,
            description=description,
            is_configured=True,
            config_location=location,
        )

    def _check_server_status(self, servers: list[MCPServerInfo]) -> None:
        """Check connection status of configured servers."""
        try:
            # Run 'claude mcp list' to get connection status
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_path,
            )

            if result.returncode == 0:
                output = result.stdout
                # Parse output to determine which servers are connected
                for server in servers:
                    if f"{server.name}:" in output and "✓ Connected" in output:
                        server.status = MCPServerStatus.CONNECTED
                        logger.debug(f"Server {server.name} is connected")
                    elif f"{server.name}:" in output and "✗" in output:
                        server.status = MCPServerStatus.ERROR
                        logger.debug(f"Server {server.name} has connection errors")
                    else:
                        server.status = MCPServerStatus.DISCONNECTED
            else:
                logger.warning(f"Failed to run 'claude mcp list': {result.stderr}")

        except FileNotFoundError:
            logger.warning("'claude' command not found, cannot check MCP status")
        except subprocess.TimeoutExpired:
            logger.warning("'claude mcp list' command timed out")
        except Exception as e:
            logger.warning(f"Failed to check MCP status: {e}")

    def _analyze_usage(
        self, servers: list[MCPServerInfo], days: int
    ) -> list[MCPToolUsage]:
        """
        Analyze MCP tool usage from logs.

        NOTE: This is currently a placeholder that returns empty usage data.
        Future enhancement: Parse Claude Code logs to extract actual MCP invocations.
        """
        usage = []

        # Placeholder: In a full implementation, we would:
        # 1. Find Claude Code session logs
        # 2. Parse logs for MCP tool invocations
        # 3. Extract: server name, tool name, timestamp, success/failure
        # 4. Aggregate statistics

        logger.debug(
            f"Usage analysis not yet implemented (would analyze last {days} days)"
        )

        # Return empty usage for now
        return usage

    def _generate_recommendations(
        self,
        servers: list[MCPServerInfo],
        usage: list[MCPToolUsage],
    ) -> list[MCPUsageRecommendation]:
        """Generate recommendations based on configuration and usage."""
        recommendations = []

        # Recommendation 1: Remove unused servers
        used_server_names = {u.server_name for u in usage if u.invocation_count > 0}
        for server in servers:
            if (
                server.name not in used_server_names
                and server.status == MCPServerStatus.CONNECTED
            ):
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="review_unused",
                        reason=f"Server '{server.name}' is configured and connected but usage data unavailable",
                        action=f"Review if '{server.name}' is needed. Connection status: ✓ Connected",
                        priority=3,  # Low priority - just informational
                    )
                )

        # Recommendation 2: Fix connection errors
        for server in servers:
            if server.status == MCPServerStatus.ERROR:
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="fix_errors",
                        reason=f"Server '{server.name}' has connection errors",
                        action=f"Check server configuration and ensure '{server.command}' is available",
                        priority=1,  # High priority
                    )
                )

        # Recommendation 3: Report disconnected servers
        for server in servers:
            if server.status == MCPServerStatus.DISCONNECTED:
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="check_connection",
                        reason=f"Server '{server.name}' is configured but not connected",
                        action="Run 'claude mcp list' to diagnose connection issues",
                        priority=2,  # Medium priority
                    )
                )

        # Recommendation 4: Suggest common servers if none configured
        if len(servers) == 0:
            recommendations.append(
                MCPUsageRecommendation(
                    server_name="sequential-thinking",
                    recommendation_type="install_missing",
                    reason="No MCP servers configured",
                    action="Consider installing '@modelcontextprotocol/server-sequential-thinking' for improved reasoning",
                    priority=2,
                )
            )

        return recommendations
