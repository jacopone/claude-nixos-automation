"""
Global MCP analyzer for cross-project analysis.
Discovers and analyzes MCP usage across all projects system-wide.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from ..schemas import (
    GlobalMCPReport,
    MCPServerInfo,
    MCPServerStatus,
    MCPServerType,
    MCPToolUsage,
    MCPUsageRecommendation,
)

logger = logging.getLogger(__name__)


class GlobalMCPAnalyzer:
    """
    Analyzes MCP usage across ALL projects system-wide.

    Addresses limitation of project-scoped analysis by:
    1. Discovering all .claude/mcp.json configs in home directory
    2. Aggregating usage data across all projects
    3. Providing unified view of global vs project-specific servers
    4. Generating system-wide optimization recommendations
    """

    def __init__(self, home_dir: Path, analysis_period_days: int = 30):
        """
        Initialize global MCP analyzer.

        Args:
            home_dir: Home directory to scan (usually Path.home())
            analysis_period_days: Analysis window in days
        """
        self.home_dir = home_dir
        self.analysis_period_days = analysis_period_days
        self.projects: list[Path] = []
        self.global_servers: dict[str, MCPServerInfo] = {}
        self.project_servers: dict[str, MCPServerInfo] = {}
        self.aggregated_usage: dict[str, MCPToolUsage] = {}
        self.recommendations: list[MCPUsageRecommendation] = []

    def discover_projects(self) -> list[Path]:
        """
        Discover all projects with MCP configurations.

        Scans for .claude/mcp.json files system-wide,
        skipping hidden directories except .claude itself.

        Returns:
            List of project paths with MCP configs
        """
        projects = []

        logger.info(f"Scanning {self.home_dir} for MCP configurations...")

        # Find all .claude/mcp.json files
        for mcp_config in self.home_dir.rglob(".claude/mcp.json"):
            # Skip hidden directories in path (except .claude)
            if self._is_valid_project(mcp_config):
                project_path = mcp_config.parent.parent  # Go up from .claude/mcp.json
                projects.append(project_path)
                logger.debug(f"Found MCP config in: {project_path}")

        logger.info(f"Discovered {len(projects)} projects with MCP configurations")
        return projects

    def _is_valid_project(self, mcp_config_path: Path) -> bool:
        """
        Check if MCP config path is from a valid project.

        Args:
            mcp_config_path: Path to .claude/mcp.json

        Returns:
            True if valid project path
        """
        # Skip paths with hidden directories (except .claude itself)
        parts = mcp_config_path.parts
        for part in parts[:-2]:  # Exclude ".claude" and "mcp.json"
            if part.startswith(".") and part != ".claude":
                return False

        # Ensure file exists and is readable
        return mcp_config_path.exists() and mcp_config_path.is_file()

    def analyze_all_projects(self) -> GlobalMCPReport:
        """
        Run MCP analysis for all projects and aggregate.

        Returns unified report with:
        - Total projects scanned
        - Global servers (from ~/.claude.json)
        - Project-specific servers (from each project)
        - Aggregated usage statistics
        - System-wide utilization metrics
        - Prioritized recommendations

        Returns:
            GlobalMCPReport with aggregated analysis
        """
        logger.info("Starting global MCP analysis...")

        # Discover projects
        self.projects = self.discover_projects()

        # Analyze global config
        self._analyze_global_config()

        # Analyze each project
        for project_path in self.projects:
            self._analyze_project(project_path)

        # Generate recommendations
        self._generate_recommendations()

        # Build report
        report = self._build_report()

        logger.info(f"Global MCP analysis complete: {len(self.global_servers)} global, {len(self.project_servers)} project-specific servers")
        return report

    def _analyze_global_config(self):
        """Analyze global MCP configuration from ~/.claude.json."""
        global_config_path = self.home_dir / ".claude.json"

        if not global_config_path.exists():
            logger.debug("No global MCP config found")
            return

        try:
            with open(global_config_path, encoding="utf-8") as f:
                config = json.load(f)

            # Extract MCP servers
            mcp_servers = config.get("mcpServers", {})

            for server_name, server_config in mcp_servers.items():
                # Parse server info
                server_info = MCPServerInfo(
                    name=server_name,
                    type=self._detect_server_type(server_config),
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    status=MCPServerStatus.UNKNOWN,
                    description=f"Global MCP server: {server_name}",
                    is_configured=True,
                    config_location="global (~/.claude.json)",
                )

                self.global_servers[server_name] = server_info

            logger.info(f"Found {len(self.global_servers)} global MCP servers")

        except Exception as e:
            logger.warning(f"Failed to analyze global MCP config: {e}")

    def _analyze_project(self, project_path: Path):
        """
        Analyze single project and merge into global state.

        Args:
            project_path: Project root directory
        """
        mcp_config_path = project_path / ".claude" / "mcp.json"

        try:
            with open(mcp_config_path, encoding="utf-8") as f:
                config = json.load(f)

            # Extract MCP servers
            mcp_servers = config.get("mcpServers", {})

            for server_name, server_config in mcp_servers.items():
                # Parse server info
                server_info = MCPServerInfo(
                    name=server_name,
                    type=self._detect_server_type(server_config),
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    status=MCPServerStatus.UNKNOWN,
                    description=f"Project MCP server: {server_name}",
                    is_configured=True,
                    config_location=f"project ({project_path.name})",
                )

                # Track project-specific servers
                if server_name not in self.global_servers:
                    self.project_servers[server_name] = server_info
                else:
                    # Server is both global and project-specific
                    logger.debug(f"Server {server_name} configured both globally and in {project_path.name}")

            logger.debug(f"Analyzed project {project_path.name}: {len(mcp_servers)} servers")

        except Exception as e:
            logger.warning(f"Failed to analyze project {project_path}: {e}")

    def _detect_server_type(self, server_config: dict) -> MCPServerType:
        """
        Detect MCP server type from configuration.

        Args:
            server_config: Server configuration dict

        Returns:
            MCPServerType
        """
        command = server_config.get("command", "")

        if command.startswith("npx") or command.startswith("node"):
            return MCPServerType.NPM
        elif command.startswith("python") or command.startswith("uv"):
            return MCPServerType.PYTHON
        elif "/" in command or command.startswith("."):
            return MCPServerType.BINARY
        else:
            return MCPServerType.UNKNOWN

    def _generate_recommendations(self):
        """Generate system-wide optimization recommendations."""
        # TODO: Implement sophisticated recommendations based on:
        # - Underutilized servers
        # - High-value servers
        # - Servers with errors
        # - Duplicate configurations

        # For now, generate basic recommendations

        # Recommend removing unused project-specific servers
        for server_name, server_info in self.project_servers.items():
            if server_name not in self.aggregated_usage:
                self.recommendations.append(
                    MCPUsageRecommendation(
                        server_name=server_name,
                        recommendation_type="remove_unused",
                        reason=f"Server configured in project but never used",
                        action=f"Remove from {server_info.config_location}",
                        priority=2,  # Medium priority
                    )
                )

    def _build_report(self) -> GlobalMCPReport:
        """Build system-wide aggregated report."""
        all_servers = {**self.global_servers, **self.project_servers}

        return GlobalMCPReport(
            timestamp=datetime.now(),
            total_projects=len(self.projects),
            total_servers=len(all_servers),
            connected_servers=sum(
                1 for s in all_servers.values() if s.status == MCPServerStatus.CONNECTED
            ),
            global_servers=list(self.global_servers.values()),
            project_servers=list(self.project_servers.values()),
            aggregated_usage=self.aggregated_usage,
            recommendations=self.recommendations,
            projects_scanned=[str(p) for p in self.projects],
        )

    def generate_summary(self, report: GlobalMCPReport) -> str:
        """
        Generate human-readable summary for rebuild output.

        Args:
            report: GlobalMCPReport to summarize

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("🌐 Global MCP Analysis")
        lines.append(f"  Projects: {report.total_projects}")
        lines.append(
            f"  Servers: {report.connected_servers}/{report.total_servers} connected"
        )
        lines.append(
            f"  Global: {len(report.global_servers)} | Project-specific: {len(report.project_servers)}"
        )

        # High-priority recommendations
        high_priority = [r for r in report.recommendations if r.priority == 1]
        if high_priority:
            lines.append(f"  ⚠️  {len(high_priority)} high-priority action(s)")

        return "\n".join(lines)


class MCPUsageAnalyzer:
    """
    Analyzes MCP usage for a single project.

    Parses session logs to track:
    - Token consumption (input, output, cache)
    - Tool invocation counts
    - Session utilization (loaded vs used)
    - ROI metrics (invocations per token)
    """

    def __init__(self, project_path: Path):
        """
        Initialize MCP usage analyzer for a project.

        Args:
            project_path: Project root directory
        """
        self.project_path = project_path
        self.sessions_dir = Path.home() / ".claude" / "sessions"

    def analyze(self, period_days: int = 30) -> dict:
        """
        Analyze MCP usage for this project.

        Args:
            period_days: Analysis window in days

        Returns:
            Dict with usage statistics including:
            - tool_usage: List of MCPToolUsage objects
            - server_utilization: List of MCPServerSessionUtilization objects
            - roi_metrics: Dict mapping server -> ROI score
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=period_days)

        # Collect usage data
        tool_usage = {}  # server:tool -> MCPToolUsage
        server_sessions = {}  # server -> {loaded_sessions, used_sessions}

        # Parse session logs
        if self.sessions_dir.exists():
            for session_file in self.sessions_dir.glob("*.jsonl"):
                try:
                    session_data = self._parse_session_file(session_file, cutoff_date)
                    if session_data:
                        self._aggregate_session_data(
                            session_data, tool_usage, server_sessions
                        )
                except Exception as e:
                    logger.debug(f"Failed to parse session {session_file}: {e}")

        # Calculate ROI metrics
        roi_metrics = self._calculate_roi_metrics(tool_usage)

        # Build utilization metrics
        utilization_metrics = self._build_utilization_metrics(server_sessions)

        return {
            "tool_usage": list(tool_usage.values()),
            "server_utilization": utilization_metrics,
            "roi_metrics": roi_metrics,
        }

    def _parse_session_file(self, session_file: Path, cutoff_date) -> dict | None:
        """
        Parse a single session JSONL file.

        Args:
            session_file: Path to session JSONL file
            cutoff_date: Only include sessions after this date

        Returns:
            Dict with session data or None if too old
        """
        # Check if session is recent enough based on file modification time
        if datetime.fromtimestamp(session_file.stat().st_mtime) < cutoff_date:
            return None

        # Parse JSONL - each line is a JSON object
        # Format: {"type": "mcp_tool_call", "server": "...", "tool": "...", "tokens": {...}}
        tool_calls = []
        servers_loaded = set()
        servers_used = set()

        try:
            with open(session_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)

                        # Track server loading
                        if entry.get("type") == "mcp_server_init":
                            servers_loaded.add(entry.get("server"))

                        # Track tool usage
                        elif entry.get("type") == "mcp_tool_call":
                            server = entry.get("server")
                            tool = entry.get("tool")
                            tokens = entry.get("tokens", {})
                            success = entry.get("success", True)

                            if server and tool:
                                servers_used.add(server)
                                tool_calls.append(
                                    {
                                        "server": server,
                                        "tool": tool,
                                        "tokens": tokens,
                                        "success": success,
                                    }
                                )
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.debug(f"Error reading session file {session_file}: {e}")
            return None

        if not tool_calls and not servers_loaded:
            return None

        return {
            "tool_calls": tool_calls,
            "servers_loaded": servers_loaded,
            "servers_used": servers_used,
        }

    def _aggregate_session_data(
        self, session_data: dict, tool_usage: dict, server_sessions: dict
    ):
        """
        Aggregate session data into usage statistics.

        Args:
            session_data: Parsed session data
            tool_usage: Dict to accumulate tool usage stats
            server_sessions: Dict to accumulate server session stats
        """
        from ..schemas import MCPToolUsage

        # Aggregate tool usage
        for call in session_data["tool_calls"]:
            key = f"{call['server']}:{call['tool']}"

            if key not in tool_usage:
                tool_usage[key] = MCPToolUsage(
                    server_name=call["server"], tool_name=call["tool"]
                )

            usage = tool_usage[key]
            usage.invocation_count += 1

            if call["success"]:
                usage.success_count += 1
            else:
                usage.error_count += 1

            # Accumulate tokens
            tokens = call.get("tokens", {})
            usage.input_tokens += tokens.get("input_tokens", 0)
            usage.output_tokens += tokens.get("output_tokens", 0)
            usage.cache_read_tokens += tokens.get("cache_read_tokens", 0)
            usage.cache_creation_tokens += tokens.get("cache_creation_tokens", 0)

        # Aggregate server session utilization
        for server in session_data["servers_loaded"]:
            if server not in server_sessions:
                server_sessions[server] = {"loaded": 0, "used": 0}

            server_sessions[server]["loaded"] += 1

            if server in session_data["servers_used"]:
                server_sessions[server]["used"] += 1

    def _calculate_roi_metrics(self, tool_usage: dict) -> dict[str, float]:
        """
        Calculate ROI score for each server.

        ROI = (invocations / tokens) * 1000
        Higher score = better value (more invocations per token)

        Args:
            tool_usage: Dict of MCPToolUsage objects

        Returns:
            Dict mapping server name -> ROI score
        """
        server_roi = {}

        # Aggregate by server
        server_totals = {}
        for usage in tool_usage.values():
            server = usage.server_name
            if server not in server_totals:
                server_totals[server] = {"invocations": 0, "tokens": 0}

            server_totals[server]["invocations"] += usage.invocation_count
            server_totals[server]["tokens"] += usage.total_tokens

        # Calculate ROI
        for server, totals in server_totals.items():
            if totals["tokens"] > 0:
                roi = (totals["invocations"] / totals["tokens"]) * 1000
                server_roi[server] = round(roi, 3)
            else:
                server_roi[server] = 0.0

        return server_roi

    def _build_utilization_metrics(
        self, server_sessions: dict
    ) -> list:
        """
        Build session utilization metrics.

        Args:
            server_sessions: Dict of server -> {loaded, used} counts

        Returns:
            List of MCPServerSessionUtilization objects
        """
        from ..schemas import MCPServerSessionUtilization

        metrics = []

        for server, counts in server_sessions.items():
            # Estimate overhead tokens (rough estimate: 500 tokens per server load)
            estimated_overhead = 500

            metric = MCPServerSessionUtilization(
                server_name=server,
                scope="unknown",  # Will be set by GlobalMCPAnalyzer
                total_sessions=counts["loaded"],  # All sessions where loaded
                loaded_sessions=counts["loaded"],
                used_sessions=counts["used"],
                estimated_overhead_tokens=estimated_overhead,
            )

            metrics.append(metric)

        return metrics
