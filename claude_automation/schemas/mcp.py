"""
MCP (Model Context Protocol) server and usage tracking schemas.

Handles MCP server configuration, tool usage analytics, and optimization recommendations.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator


class MCPServerType(str, Enum):
    """MCP server type."""

    NPM = "npm"
    PYTHON = "python"
    BINARY = "binary"
    BUILTIN = "builtin"
    UNKNOWN = "unknown"


class MCPServerStatus(str, Enum):
    """MCP server connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"
    UNKNOWN = "unknown"


class MCPServerInfo(BaseModel):
    """Information about an MCP server."""

    name: str = Field(..., description="Server name")
    type: MCPServerType = Field(..., description="Server type")
    command: str = Field(..., description="Command to start server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    status: MCPServerStatus = Field(
        default=MCPServerStatus.UNKNOWN, description="Connection status"
    )
    description: str = Field("", description="Server description")
    is_configured: bool = Field(False, description="Whether server is configured")
    config_location: str = Field(
        "", description="Where server is configured (global/project)"
    )

    @validator("name")
    def validate_name(cls, v):
        """Validate server name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Server name cannot be empty")
        return v.strip()


class MCPToolUsage(BaseModel):
    """Usage statistics for an MCP tool."""

    server_name: str = Field(..., description="MCP server name")
    tool_name: str = Field(..., description="Tool name within server")
    invocation_count: int = Field(0, ge=0, description="Number of invocations")
    success_count: int = Field(0, ge=0, description="Number of successful invocations")
    error_count: int = Field(0, ge=0, description="Number of failed invocations")
    last_used: datetime | None = Field(None, description="Last usage timestamp")
    avg_duration_ms: float | None = Field(None, description="Average execution time")

    # Token usage tracking
    input_tokens: int = Field(0, ge=0, description="Total input tokens consumed")
    output_tokens: int = Field(0, ge=0, description="Total output tokens generated")
    cache_read_tokens: int = Field(0, ge=0, description="Total cache read tokens")
    cache_creation_tokens: int = Field(
        0, ge=0, description="Total cache creation tokens"
    )

    # Scope tracking
    scope: str = Field("unknown", description="Server scope: global, project, or both")

    @validator("server_name")
    def validate_server_name(cls, v):
        """Validate server name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Server name cannot be empty")
        return v.strip()

    @validator("tool_name")
    def validate_tool_name(cls, v):
        """Validate tool name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Tool name cannot be empty")
        return v.strip()

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100.0

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens consumed (input + output + cache)."""
        return self.input_tokens + self.output_tokens + self.cache_creation_tokens

    @property
    def avg_tokens_per_invocation(self) -> float:
        """Calculate average tokens per invocation."""
        if self.invocation_count == 0:
            return 0.0
        return self.total_tokens / self.invocation_count

    @property
    def estimated_cost_usd(self) -> float:
        """
        Estimate cost in USD based on Claude Sonnet 4.5 pricing.
        Input: $3 per 1M tokens
        Output: $15 per 1M tokens
        Cache read: $0.30 per 1M tokens
        Cache write: $3.75 per 1M tokens
        """
        input_cost = (self.input_tokens / 1_000_000) * 3.0
        output_cost = (self.output_tokens / 1_000_000) * 15.0
        cache_read_cost = (self.cache_read_tokens / 1_000_000) * 0.30
        cache_write_cost = (self.cache_creation_tokens / 1_000_000) * 3.75
        return input_cost + output_cost + cache_read_cost + cache_write_cost

    @property
    def roi_score(self) -> float:
        """
        Calculate ROI score: invocations per 1000 tokens.
        Higher score = better value (more invocations for fewer tokens).
        """
        if self.total_tokens == 0:
            return 0.0
        return (self.invocation_count / self.total_tokens) * 1000


class MCPSessionStats(BaseModel):
    """Statistics for a single MCP session."""

    session_id: str = Field(..., description="Session identifier (filename UUID)")
    project_path: str = Field("", description="Project path if detectable")
    start_time: datetime | None = Field(None, description="Session start timestamp")
    end_time: datetime | None = Field(None, description="Session end timestamp")
    servers_used: list[str] = Field(
        default_factory=list, description="MCP servers invoked in this session"
    )
    total_tokens: int = Field(0, ge=0, description="Total tokens in session")
    mcp_invocation_count: int = Field(
        0, ge=0, description="Number of MCP tool invocations"
    )

    @validator("session_id")
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Session ID cannot be empty")
        return v.strip()


class MCPServerSessionUtilization(BaseModel):
    """Session utilization metrics for an MCP server."""

    server_name: str = Field(..., description="MCP server name")
    scope: str = Field(..., description="Server scope (global/project)")
    total_sessions: int = Field(0, ge=0, description="Total sessions analyzed")
    loaded_sessions: int = Field(
        0, ge=0, description="Sessions where server was loaded"
    )
    used_sessions: int = Field(0, ge=0, description="Sessions where server was invoked")
    estimated_overhead_tokens: int = Field(
        0, ge=0, description="Estimated overhead tokens per session"
    )

    @validator("server_name")
    def validate_server_name(cls, v):
        """Validate server name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Server name cannot be empty")
        return v.strip()

    @property
    def utilization_rate(self) -> float:
        """Calculate utilization rate percentage (used / loaded)."""
        if self.loaded_sessions == 0:
            return 0.0
        return (self.used_sessions / self.loaded_sessions) * 100.0

    @property
    def wasted_sessions(self) -> int:
        """Calculate number of sessions where server was loaded but not used."""
        return self.loaded_sessions - self.used_sessions

    @property
    def total_wasted_overhead(self) -> int:
        """Calculate total wasted overhead tokens."""
        return self.wasted_sessions * self.estimated_overhead_tokens

    @property
    def efficiency_score(self) -> str:
        """Get human-readable efficiency score."""
        rate = self.utilization_rate
        if rate >= 80:
            return "excellent"
        elif rate >= 50:
            return "good"
        elif rate >= 20:
            return "fair"
        else:
            return "poor"


class MCPUsageRecommendation(BaseModel):
    """Recommendation for MCP server usage."""

    server_name: str = Field(..., description="Server name")
    recommendation_type: str = Field(
        ..., description="Type: remove_unused, install_missing, fix_errors, optimize"
    )
    reason: str = Field(..., description="Reason for recommendation")
    action: str = Field(..., description="Suggested action")
    priority: int = Field(..., ge=1, le=3, description="Priority (1=high, 3=low)")


class GlobalMCPReport(BaseModel):
    """Aggregated MCP analysis across all projects."""

    timestamp: datetime = Field(default_factory=datetime.now)
    total_projects: int = Field(0, ge=0, description="Number of projects scanned")
    total_servers: int = Field(0, ge=0, description="Total unique MCP servers")
    connected_servers: int = Field(
        0, ge=0, description="Successfully connected servers"
    )
    global_servers: list[MCPServerInfo] = Field(
        default_factory=list, description="Servers from global config"
    )
    project_servers: list[MCPServerInfo] = Field(
        default_factory=list, description="Servers from project configs"
    )
    aggregated_usage: dict[str, MCPToolUsage] = Field(
        default_factory=dict, description="Usage aggregated by server"
    )
    recommendations: list[MCPUsageRecommendation] = Field(
        default_factory=list, description="Prioritized recommendations"
    )
    projects_scanned: list[str] = Field(
        default_factory=list, description="Paths of scanned projects"
    )

    @property
    def total_invocations(self) -> int:
        """Total invocations across all servers."""
        return sum(usage.invocation_count for usage in self.aggregated_usage.values())

    @property
    def total_tokens(self) -> int:
        """Total tokens across all servers."""
        return sum(usage.total_tokens for usage in self.aggregated_usage.values())


class MCPUsageAnalyticsConfig(BaseModel):
    """Configuration for MCP usage analytics generation."""

    project_path: Path = Field(..., description="Project root directory")
    global_mcp_config: Path | None = Field(
        None, description="Global MCP config path (~/.claude.json)"
    )
    project_mcp_config: Path | None = Field(
        None, description="Project MCP config path (.claude/mcp.json)"
    )
    configured_servers: list[MCPServerInfo] = Field(
        default_factory=list, description="All configured MCP servers"
    )
    tool_usage: list[MCPToolUsage] = Field(
        default_factory=list, description="Tool usage statistics"
    )
    recommendations: list[MCPUsageRecommendation] = Field(
        default_factory=list, description="Usage recommendations"
    )
    analysis_period_days: int = Field(30, ge=1, description="Analysis period in days")
    timestamp: datetime = Field(default_factory=datetime.now)

    # Session-level analytics
    session_stats: list[MCPSessionStats] = Field(
        default_factory=list, description="Per-session statistics"
    )
    server_utilization: list[MCPServerSessionUtilization] = Field(
        default_factory=list, description="Per-server session utilization metrics"
    )

    @validator("project_path")
    def validate_project_path(cls, v):
        """Validate project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

    @property
    def claude_file(self) -> Path:
        """Get CLAUDE.md path for analytics output."""
        return self.project_path / "CLAUDE.md"

    @property
    def total_configured_servers(self) -> int:
        """Get count of configured servers."""
        return len(self.configured_servers)

    @property
    def total_invocations(self) -> int:
        """Get total MCP tool invocations."""
        return sum(usage.invocation_count for usage in self.tool_usage)

    @property
    def connected_servers(self) -> list[MCPServerInfo]:
        """Get list of successfully connected servers."""
        return [
            s for s in self.configured_servers if s.status == MCPServerStatus.CONNECTED
        ]

    @property
    def unused_servers(self) -> list[MCPServerInfo]:
        """Get servers that are configured but never used."""
        used_servers = {
            usage.server_name for usage in self.tool_usage if usage.invocation_count > 0
        }
        return [s for s in self.configured_servers if s.name not in used_servers]
