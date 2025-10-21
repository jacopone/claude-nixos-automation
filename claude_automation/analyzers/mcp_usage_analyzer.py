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
from datetime import UTC, datetime
from pathlib import Path

from claude_automation.schemas import (
    MCPServerInfo,
    MCPServerSessionUtilization,
    MCPServerStatus,
    MCPServerType,
    MCPSessionStats,
    MCPToolUsage,
    MCPUsageAnalyticsConfig,
    MCPUsageRecommendation,
)

logger = logging.getLogger(__name__)

# Estimated overhead tokens per session for common MCP servers
# Based on typical tool definition sizes (~500 tokens per tool)
MCP_OVERHEAD_ESTIMATES = {
    "sequential-thinking": 500,  # 1 tool
    "serena": 10_000,  # ~20 tools (list_dir, find_symbol, search, etc.)
    "chrome-devtools": 5_000,  # ~10 tools
    "whatsapp": 3_000,  # ~6 tools
    "mcp-nixos": 2_000,  # ~4 tools
    "filesystem": 3_000,  # ~6 tools
    "git": 2_000,  # ~4 tools
    "github": 4_000,  # ~8 tools
    "playwright": 4_000,  # ~8 tools
    "_default": 2_000,  # Unknown servers
}


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

        # Step 3: Analyze usage from session logs
        tool_usage, session_stats, server_utilization = self._analyze_usage(
            configured_servers, analysis_period_days
        )

        # Step 4: Generate recommendations (including session utilization insights)
        recommendations = self._generate_recommendations(
            configured_servers, tool_usage, server_utilization
        )

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
            session_stats=session_stats,
            server_utilization=server_utilization,
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
    ) -> tuple[
        list[MCPToolUsage], list[MCPSessionStats], list[MCPServerSessionUtilization]
    ]:
        """
        Analyze MCP tool usage from Claude Code session logs.

        Parses .jsonl session logs to extract:
        - Tool-level usage statistics
        - Per-session statistics
        - Server utilization metrics

        Returns:
            Tuple of (tool_usage, session_stats, server_utilization)
        """
        from collections import defaultdict
        from datetime import timedelta

        usage_data = defaultdict(
            lambda: {
                "server_name": "",
                "tool_name": "",
                "invocation_count": 0,
                "success_count": 0,
                "error_count": 0,
                "last_used": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_creation_tokens": 0,
                "scope": "unknown",
            }
        )

        # Find Claude Code session logs
        claude_projects_dir = Path.home() / ".claude" / "projects"
        if not claude_projects_dir.exists():
            logger.debug(f"Claude projects directory not found: {claude_projects_dir}")
            return []

        # Calculate cutoff date for analysis period (timezone-aware)

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        # Scan all project directories for session logs
        log_files = []
        for project_dir in claude_projects_dir.iterdir():
            if project_dir.is_dir():
                for log_file in project_dir.glob("*.jsonl"):
                    log_files.append(log_file)

        if not log_files:
            logger.debug("No Claude Code session logs found")
            return [], [], []

        logger.info(f"Found {len(log_files)} session log files to analyze")

        # Track session-level stats
        session_data = {}  # session_id -> {servers_used, total_tokens, start/end}

        # Parse session logs
        for log_file in log_files:
            try:
                self._parse_session_log(log_file, cutoff_date, usage_data, session_data)
            except Exception as e:
                logger.warning(f"Failed to parse log file {log_file}: {e}")

        # Determine scope for each server
        global_servers = {
            s.name for s in servers if "global" in s.config_location.lower()
        }
        project_servers = {
            s.name for s in servers if "project" in s.config_location.lower()
        }

        # Convert to MCPToolUsage objects
        usage_list = []
        for _key, data in usage_data.items():
            server_name = data["server_name"]

            # Determine scope
            scope = "unknown"
            if server_name in global_servers and server_name in project_servers:
                scope = "both"
            elif server_name in global_servers:
                scope = "global"
            elif server_name in project_servers:
                scope = "project"

            usage_list.append(
                MCPToolUsage(
                    server_name=data["server_name"],
                    tool_name=data["tool_name"],
                    invocation_count=data["invocation_count"],
                    success_count=data["success_count"],
                    error_count=data["error_count"],
                    last_used=data["last_used"],
                    input_tokens=data["input_tokens"],
                    output_tokens=data["output_tokens"],
                    cache_read_tokens=data["cache_read_tokens"],
                    cache_creation_tokens=data["cache_creation_tokens"],
                    scope=scope,
                )
            )

        logger.info(f"Analyzed {len(usage_list)} unique MCP tool invocations")

        # Build session stats
        session_stats = []
        for session_id, data in session_data.items():
            session_stats.append(
                MCPSessionStats(
                    session_id=session_id,
                    project_path=data.get("project_path", ""),
                    start_time=data.get("start_time"),
                    end_time=data.get("end_time"),
                    servers_used=list(data.get("servers_used", set())),
                    total_tokens=data.get("total_tokens", 0),
                    mcp_invocation_count=data.get("mcp_invocation_count", 0),
                )
            )

        # Calculate server utilization metrics
        server_utilization = self._calculate_server_utilization(
            servers, session_stats, global_servers, project_servers
        )

        logger.info(f"Analyzed {len(session_stats)} sessions")
        logger.info(f"Calculated utilization for {len(server_utilization)} servers")

        # Mark analyzed sessions with lifecycle tracker (Phase 2)
        self._mark_sessions_analyzed(log_files)

        return usage_list, session_stats, server_utilization

    def _parse_session_log(
        self,
        log_file: Path,
        cutoff_date: datetime,
        usage_data: dict,
        session_data: dict,
    ) -> None:
        """Parse a single session log file for MCP invocations and session stats."""
        session_id = log_file.stem  # UUID from filename
        project_path = log_file.parent.name  # Project directory name

        # Initialize session tracking
        if session_id not in session_data:
            session_data[session_id] = {
                "project_path": project_path,
                "start_time": None,
                "end_time": None,
                "servers_used": set(),
                "total_tokens": 0,
                "mcp_invocation_count": 0,
            }

        with open(log_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    if not line.strip():
                        continue

                    data = json.loads(line)

                    # Extract timestamp
                    timestamp_str = data.get("timestamp")
                    if not timestamp_str:
                        continue

                    # Parse timestamp (ISO 8601 format)
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )

                    # Skip if outside analysis period
                    if timestamp < cutoff_date:
                        continue

                    # Track session timestamps
                    if (
                        session_data[session_id]["start_time"] is None
                        or timestamp < session_data[session_id]["start_time"]
                    ):
                        session_data[session_id]["start_time"] = timestamp
                    if (
                        session_data[session_id]["end_time"] is None
                        or timestamp > session_data[session_id]["end_time"]
                    ):
                        session_data[session_id]["end_time"] = timestamp

                    # Extract message content
                    message = data.get("message", {})
                    content = message.get("content", [])

                    if not isinstance(content, list):
                        continue

                    # Track token usage for this session
                    usage = message.get("usage", {})
                    if usage and isinstance(usage, dict):
                        session_data[session_id]["total_tokens"] += usage.get(
                            "input_tokens", 0
                        )
                        session_data[session_id]["total_tokens"] += usage.get(
                            "output_tokens", 0
                        )

                    # Look for MCP tool invocations
                    for item in content:
                        if not isinstance(item, dict):
                            continue

                        tool_name = item.get("name", "")
                        if not tool_name.startswith("mcp__"):
                            continue

                        # Parse MCP tool name: mcp__server__tool
                        parts = tool_name.split("__")
                        if len(parts) < 3:
                            continue

                        server_name = parts[1]
                        tool_only = "__".join(parts[2:])

                        # Track server usage in this session
                        session_data[session_id]["servers_used"].add(server_name)
                        session_data[session_id]["mcp_invocation_count"] += 1

                        # Create unique key for this server+tool
                        key = f"{server_name}__{tool_only}"

                        # Initialize if first time seeing this tool
                        if (
                            key not in usage_data
                            or usage_data[key]["invocation_count"] == 0
                        ):
                            usage_data[key]["server_name"] = server_name
                            usage_data[key]["tool_name"] = tool_only

                        # Update invocation count
                        usage_data[key]["invocation_count"] += 1

                        # Update last used
                        if (
                            usage_data[key]["last_used"] is None
                            or timestamp > usage_data[key]["last_used"]
                        ):
                            usage_data[key]["last_used"] = timestamp

                        # Determine success/failure
                        item_type = item.get("type", "")
                        if item_type == "tool_result":
                            is_error = item.get("isError", False)
                            if is_error:
                                usage_data[key]["error_count"] += 1
                            else:
                                usage_data[key]["success_count"] += 1

                    # Extract token usage from message
                    usage = message.get("usage", {})
                    if usage and isinstance(usage, dict):
                        # Check if this message contains MCP tool invocations
                        has_mcp_tools = any(
                            isinstance(item, dict)
                            and item.get("name", "").startswith("mcp__")
                            for item in content
                        )

                        if has_mcp_tools:
                            # Attribute tokens to all MCP tools in this message
                            mcp_tools_in_message = [
                                item.get("name", "")
                                for item in content
                                if isinstance(item, dict)
                                and item.get("name", "").startswith("mcp__")
                            ]

                            for tool_name in mcp_tools_in_message:
                                parts = tool_name.split("__")
                                if len(parts) < 3:
                                    continue

                                server_name = parts[1]
                                tool_only = "__".join(parts[2:])
                                key = f"{server_name}__{tool_only}"

                                # Add token usage
                                usage_data[key]["input_tokens"] += usage.get(
                                    "input_tokens", 0
                                )
                                usage_data[key]["output_tokens"] += usage.get(
                                    "output_tokens", 0
                                )
                                usage_data[key]["cache_read_tokens"] += usage.get(
                                    "cache_read_input_tokens", 0
                                )
                                usage_data[key]["cache_creation_tokens"] += usage.get(
                                    "cache_creation_input_tokens", 0
                                )

                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON in {log_file}:{line_num}: {e}")
                except Exception as e:
                    logger.debug(f"Error processing line {line_num} in {log_file}: {e}")

    def _calculate_server_utilization(
        self,
        servers: list[MCPServerInfo],
        session_stats: list[MCPSessionStats],
        global_servers: set[str],
        project_servers: set[str],
    ) -> list[MCPServerSessionUtilization]:
        """
        Calculate session utilization metrics for each configured MCP server.

        For each server, determines:
        - How many sessions loaded it (all sessions for global, project sessions for project-level)
        - How many sessions actually used it (invoked at least one tool)
        - Estimated overhead tokens per session
        - Utilization rate and efficiency score

        Args:
            servers: List of configured MCP servers
            session_stats: Per-session statistics
            global_servers: Set of globally-configured server names
            project_servers: Set of project-configured server names

        Returns:
            List of server utilization metrics
        """
        total_sessions = len(session_stats)
        if total_sessions == 0:
            logger.debug("No sessions to analyze for utilization")
            return []

        utilization_metrics = []

        for server in servers:
            # Determine scope
            scope = "unknown"
            if server.name in global_servers and server.name in project_servers:
                scope = "both"
            elif server.name in global_servers:
                scope = "global"
            elif server.name in project_servers:
                scope = "project"

            # Calculate loaded sessions
            # Global servers load in ALL sessions
            # Project servers only load in sessions for that project
            if "global" in scope.lower():
                loaded_sessions = total_sessions
            else:
                # Project-level server - only loaded in sessions from this project
                # For now, assume all sessions are from this project
                # TODO: Filter by project_path when available
                loaded_sessions = total_sessions

            # Calculate used sessions (sessions where this server was actually invoked)
            used_sessions = sum(
                1 for session in session_stats if server.name in session.servers_used
            )

            # Get estimated overhead tokens
            estimated_overhead = MCP_OVERHEAD_ESTIMATES.get(
                server.name, MCP_OVERHEAD_ESTIMATES["_default"]
            )

            utilization_metrics.append(
                MCPServerSessionUtilization(
                    server_name=server.name,
                    scope=scope,
                    total_sessions=total_sessions,
                    loaded_sessions=loaded_sessions,
                    used_sessions=used_sessions,
                    estimated_overhead_tokens=estimated_overhead,
                )
            )

        return utilization_metrics

    def _generate_recommendations(
        self,
        servers: list[MCPServerInfo],
        usage: list[MCPToolUsage],
        server_utilization: list[MCPServerSessionUtilization],
    ) -> list[MCPUsageRecommendation]:
        """Generate recommendations based on configuration, usage, session utilization, and token costs."""
        recommendations = []

        # Build usage lookup by server name
        usage_by_server = {}
        for tool_usage in usage:
            server_name = tool_usage.server_name
            if server_name not in usage_by_server:
                usage_by_server[server_name] = []
            usage_by_server[server_name].append(tool_usage)

        # Recommendation 1: Unused servers (no usage data)
        used_server_names = {u.server_name for u in usage if u.invocation_count > 0}
        for server in servers:
            if (
                server.name not in used_server_names
                and server.status == MCPServerStatus.CONNECTED
            ):
                scope_info = server.config_location.split()[
                    0
                ].lower()  # 'global' or 'project'
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="review_unused",
                        reason=f"Server '{server.name}' is connected but has no recorded usage",
                        action=f"Consider disabling '{server.name}' if not needed ({scope_info} scope)",
                        priority=3,  # Low priority - just informational
                    )
                )

        # Recommendation 2: Low ROI servers (high token cost, low invocations)
        for tool_usage in usage:
            if tool_usage.invocation_count > 0 and tool_usage.roi_score < 1.0:
                # ROI < 1.0 means less than 1 invocation per 1000 tokens
                cost_str = f"${tool_usage.estimated_cost_usd:.4f}"
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=tool_usage.server_name,
                        recommendation_type="optimize",
                        reason=f"Server '{tool_usage.server_name}' has low ROI: {tool_usage.invocation_count} invocations for {tool_usage.total_tokens:,} tokens (est. {cost_str})",
                        action=f"Review usage patterns. Consider if '{tool_usage.server_name}' is cost-effective ({tool_usage.scope} scope)",
                        priority=2,  # Medium priority
                    )
                )

        # Recommendation 3: High-value servers (highlight efficient tools)
        for tool_usage in usage:
            if tool_usage.invocation_count >= 5 and tool_usage.roi_score > 10.0:
                # ROI > 10.0 means more than 10 invocations per 1000 tokens
                cost_str = f"${tool_usage.estimated_cost_usd:.4f}"
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=tool_usage.server_name,
                        recommendation_type="highlight_value",
                        reason=f"Server '{tool_usage.server_name}' provides excellent value: {tool_usage.invocation_count} invocations for only {tool_usage.total_tokens:,} tokens (est. {cost_str})",
                        action=f"Keep '{tool_usage.server_name}' enabled. High efficiency tool ({tool_usage.scope} scope)",
                        priority=3,  # Low priority - positive feedback
                    )
                )

        # Recommendation 4: High token consumers (awareness)
        for tool_usage in usage:
            if tool_usage.total_tokens > 100_000:
                cost_str = f"${tool_usage.estimated_cost_usd:.2f}"
                avg_tokens = int(tool_usage.avg_tokens_per_invocation)
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=tool_usage.server_name,
                        recommendation_type="high_usage",
                        reason=f"Server '{tool_usage.server_name}' consumed {tool_usage.total_tokens:,} tokens (est. {cost_str})",
                        action=f"Frequent user: {tool_usage.invocation_count} calls, ~{avg_tokens:,} tokens/call ({tool_usage.scope} scope)",
                        priority=3,  # Low priority - informational
                    )
                )

        # Recommendation 5: Fix connection errors
        for server in servers:
            if server.status == MCPServerStatus.ERROR:
                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server.name,
                        recommendation_type="fix_errors",
                        reason=f"Server '{server.name}' has connection errors",
                        action=f"Check configuration and ensure '{server.command}' is available",
                        priority=1,  # High priority
                    )
                )

        # Recommendation 6: Report disconnected servers
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

        # Recommendation 7: Suggest common servers if none configured
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

        # Recommendation 8: Low session utilization (global servers with poor utilization)
        for util in server_utilization:
            # Focus on global servers with poor utilization (< 20%)
            if (
                "global" in util.scope.lower()
                and util.utilization_rate < 20.0
                and util.loaded_sessions > 10
            ):
                wasted_tokens = util.total_wasted_overhead
                wasted_sessions = util.wasted_sessions
                utilization_pct = util.utilization_rate

                recommendations.append(
                    MCPUsageRecommendation(
                        server_name=util.server_name,
                        recommendation_type="poor_utilization",
                        reason=f"Server '{util.server_name}' loads in all sessions but only used in {utilization_pct:.1f}% ({util.used_sessions}/{util.loaded_sessions} sessions)",
                        action=f"Consider moving '{util.server_name}' to project-level config. Wasted overhead: ~{wasted_tokens:,} tokens across {wasted_sessions} sessions",
                        priority=(
                            1 if wasted_tokens > 500_000 else 2
                        ),  # High priority if >500K wasted tokens
                    )
                )

        return recommendations

    def _mark_sessions_analyzed(self, log_files: list[Path]) -> None:
        """
        Mark analyzed session files with ANALYZED lifecycle stage.

        Phase 2: Integrates lifecycle tracking to enable value-based cleanup.

        Args:
            log_files: List of session .jsonl files that were analyzed
        """
        try:
            from claude_automation.analyzers.session_lifecycle_tracker import (
                SessionLifecycleTracker,
            )
            from claude_automation.schemas.lifecycle import SessionLifecycle

            tracker = SessionLifecycleTracker()

            # Mark each analyzed session
            for log_file in log_files:
                try:
                    tracker.mark_session(
                        log_file,
                        SessionLifecycle.ANALYZED,
                        notes="Processed by MCP usage analyzer"
                    )
                except Exception as e:
                    logger.debug(f"Could not mark session {log_file.name}: {e}")

            logger.info(f"Marked {len(log_files)} sessions as ANALYZED")

        except Exception as e:
            # Don't fail analysis if lifecycle tracking fails
            logger.warning(f"Could not update session lifecycle: {e}")
