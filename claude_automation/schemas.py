"""
Pydantic schemas for CLAUDE.md automation system.
Provides type safety and validation for all data structures.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, validator


class ToolCategory(str, Enum):
    """Standard tool categories."""

    AI_MCP_TOOLS = "AI & MCP Tools"
    CLI_TOOLS = "Modern CLI Tools"
    DEVELOPMENT = "Development Tools"
    FILE_MANAGEMENT = "File Management & Search Tools"
    SYSTEM_MONITORING = "System Monitoring & Process Management"
    NETWORK_SECURITY = "Network & Security Tools"
    SYSTEM_PACKAGES = "System Support Packages"
    OTHER = "Other Tools"


class ProjectType(str, Enum):
    """Detected project types for permissions optimization."""

    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    NIXOS = "nixos"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ToolInfo(BaseModel):
    """Information about a CLI tool."""

    name: str = Field(..., description="Tool command name")
    description: str = Field(..., description="Tool description")
    category: ToolCategory = Field(..., description="Tool category")
    url: str | None = Field(None, description="Tool homepage URL")

    @validator("name")
    def validate_name(cls, v):
        """Validate tool name format."""
        if not v:
            raise ValueError("Tool name cannot be empty")
        # Allow alphanumeric, hyphens, dots, underscores
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._"
        )
        if not all(c in allowed_chars for c in v):
            raise ValueError(f"Invalid tool name format: {v}")
        return v

    @validator("description")
    def validate_description(cls, v):
        """Validate description."""
        if not v or len(v.strip()) < 3:
            raise ValueError("Description must be at least 3 characters")
        return v.strip()

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format."""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class FishAbbreviation(BaseModel):
    """Fish shell abbreviation."""

    abbr: str = Field(..., description="Abbreviation")
    command: str = Field(..., description="Full command")

    @validator("abbr")
    def validate_abbr(cls, v):
        """Validate abbreviation format."""
        if not v or not v.replace("_", "").isalnum():
            raise ValueError("Abbreviation must be alphanumeric (underscore allowed)")
        return v


class GitStatus(BaseModel):
    """Git repository status."""

    modified: int = Field(0, ge=0, description="Number of modified files")
    added: int = Field(0, ge=0, description="Number of added files")
    untracked: int = Field(0, ge=0, description="Number of untracked files")

    @property
    def status_string(self) -> str:
        """Generate status string like '2M 1A 3U'."""
        if self.modified == 0 and self.added == 0 and self.untracked == 0:
            return "clean"
        return f"{self.modified}M {self.added}A {self.untracked}U"

    @classmethod
    def from_string(cls, status_str: str) -> "GitStatus":
        """Parse status string like '2M 1A 3U' into GitStatus."""
        if status_str == "clean":
            return cls()

        parts = status_str.split()
        modified = added = untracked = 0

        for part in parts:
            if part.endswith("M"):
                modified = int(part[:-1])
            elif part.endswith("A"):
                added = int(part[:-1])
            elif part.endswith("U"):
                untracked = int(part[:-1])

        return cls(modified=modified, added=added, untracked=untracked)


class SystemConfig(BaseModel):
    """System-level CLAUDE.md configuration."""

    timestamp: datetime = Field(default_factory=datetime.now)
    package_count: int = Field(
        ..., ge=1, le=1000, description="Total number of packages"
    )
    fish_abbreviations: list[FishAbbreviation] = Field(default_factory=list)
    tool_categories: dict[ToolCategory, list[ToolInfo]] = Field(default_factory=dict)
    git_status: GitStatus = Field(default_factory=GitStatus)
    user_policies: str = Field(default="", description="User-defined policies content")
    has_user_policies: bool = Field(
        default=False, description="Whether user policies exist"
    )

    @validator("package_count")
    def validate_package_count(cls, v):
        """Validate package count is reasonable."""
        if v < 10:
            raise ValueError("Package count seems too low (less than 10)")
        if v > 500:
            raise ValueError("Package count seems too high (more than 500)")
        return v

    @property
    def total_tools(self) -> int:
        """Calculate total number of tools across all categories."""
        return sum(len(tools) for tools in self.tool_categories.values())

    @property
    def abbreviation_count(self) -> int:
        """Get count of fish abbreviations."""
        return len(self.fish_abbreviations)


class ProjectConfig(BaseModel):
    """Project-level CLAUDE.md configuration."""

    timestamp: datetime = Field(default_factory=datetime.now)
    package_count: int = Field(..., ge=1, le=1000)
    fish_abbreviation_count: int = Field(..., ge=0, le=200)
    git_status: GitStatus = Field(default_factory=GitStatus)
    working_features: list[str] = Field(default_factory=list)

    @validator("working_features")
    def validate_features(cls, v):
        """Validate working features list."""
        if len(v) < 3:
            raise ValueError("Should have at least 3 working features")
        return v


class ParsingResult(BaseModel):
    """Result of parsing a Nix configuration file."""

    success: bool = Field(..., description="Whether parsing succeeded")
    packages: dict[str, ToolInfo] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    parser_used: str = Field(..., description="Which parser was used")

    @property
    def package_count(self) -> int:
        """Get number of packages parsed."""
        return len(self.packages)

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there were any warnings."""
        return len(self.warnings) > 0


class GenerationResult(BaseModel):
    """Result of generating a CLAUDE.md file."""

    success: bool = Field(..., description="Whether generation succeeded")
    output_path: str = Field(..., description="Path to generated file")
    backup_path: str | None = Field(None, description="Path to backup file")
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there were any warnings."""
        return len(self.warnings) > 0


# Example configurations for testing
class CommandCategory(str, Enum):
    """Slash command categories."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    BUILD = "build"
    GIT = "git"
    DOCUMENTATION = "documentation"
    SYSTEM = "system"
    CUSTOM = "custom"


class DirectoryPurpose(str, Enum):
    """Standard directory purposes."""

    SOURCE_CODE = "source_code"
    TESTS = "tests"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    MODULES = "modules"
    SCRIPTS = "scripts"
    TEMPLATES = "templates"
    DATA = "data"
    BUILD = "build"
    UNKNOWN = "unknown"


class DirectoryContextConfig(BaseModel):
    """Configuration for directory-level CLAUDE.md generation."""

    directory_path: Path = Field(..., description="Directory path")
    directory_name: str = Field(..., description="Directory name")
    purpose: DirectoryPurpose = Field(..., description="Detected directory purpose")
    file_count: int = Field(0, ge=0, description="Number of files in directory")
    subdirectory_count: int = Field(0, ge=0, description="Number of subdirectories")
    primary_file_types: list[str] = Field(
        default_factory=list, description="Primary file extensions found"
    )
    do_not_touch: list[str] = Field(
        default_factory=list, description="Files/patterns to never modify"
    )
    key_files: list[str] = Field(
        default_factory=list, description="Important files in this directory"
    )
    description: str = Field(
        default="", description="Auto-generated directory description"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("directory_path")
    def validate_directory_path(cls, v):
        """Validate directory exists."""
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

    @property
    def claude_file(self) -> Path:
        """Get CLAUDE.md path for this directory."""
        return self.directory_path / "CLAUDE.md"


EXAMPLE_SYSTEM_CONFIG = SystemConfig(
    package_count=109,
    fish_abbreviations=[
        FishAbbreviation(abbr="l1", command="eza -1"),
        FishAbbreviation(abbr="lg", command="eza -la --git --group-directories-first"),
    ],
    tool_categories={
        ToolCategory.DEVELOPMENT: [
            ToolInfo(
                name="git",
                description="A free and open source distributed version control system",
                category=ToolCategory.DEVELOPMENT,
                url="https://git-scm.com/",
            )
        ]
    },
    git_status=GitStatus.from_string("2M 1A 0U"),
)

EXAMPLE_PROJECT_CONFIG = ProjectConfig(
    package_count=109,
    fish_abbreviation_count=55,
    git_status=GitStatus.from_string("clean"),
    working_features=[
        "Fish shell with 55 smart abbreviations",
        "Yazi file manager with rich previews",
        "Starship prompt with visual git status",
    ],
)


class UsagePattern(BaseModel):
    """Command usage pattern from git history."""

    command: str = Field(..., description="Command name")
    frequency: int = Field(..., ge=0, description="Usage count in git history")
    last_used: datetime = Field(..., description="Last usage timestamp")

    @validator("command")
    def validate_command(cls, v):
        """Validate command format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Command cannot be empty")
        return v.strip()


class PermissionsConfig(BaseModel):
    """Configuration for permissions generation."""

    project_path: Path = Field(..., description="Project root directory")
    project_type: ProjectType = Field(..., description="Detected project type")
    usage_patterns: list[UsagePattern] = Field(default_factory=list)
    existing_hooks: dict[str, Any] | None = Field(None)
    quality_tools: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    sensitive_paths: list[str] = Field(default_factory=list)
    modern_cli_tools: list[str] = Field(default_factory=list)
    username: str = Field(..., description="System username")
    timestamp: datetime = Field(default_factory=datetime.now)
    has_tests: bool = Field(False, description="Whether project has test directory")
    template_name: str = Field(
        "permissions/base.j2", description="Template file name to use"
    )

    @validator("project_path")
    def validate_project_path(cls, v):
        """Validate project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Username cannot be empty")
        return v.strip()

    @property
    def claude_dir(self) -> Path:
        """Get .claude directory path."""
        return self.project_path / ".claude"

    @property
    def settings_file(self) -> Path:
        """Get settings.local.json path."""
        return self.claude_dir / "settings.local.json"


class LocalContextConfig(BaseModel):
    """Configuration for local/machine-specific context generation."""

    project_path: Path = Field(..., description="Project root directory")
    hostname: str = Field(..., description="Machine hostname")
    cpu_info: str = Field("", description="CPU information")
    memory_total: str = Field("", description="Total system memory")
    disk_usage: str = Field("", description="Disk usage information")
    running_services: list[str] = Field(
        default_factory=list, description="Detected running services"
    )
    current_branches: list[str] = Field(
        default_factory=list, description="Active git branches"
    )
    wip_notes: list[str] = Field(
        default_factory=list, description="Work in progress notes"
    )
    experiments: list[str] = Field(
        default_factory=list, description="Experimental features"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("project_path")
    def validate_project_path(cls, v):
        """Validate project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

    @property
    def local_claude_file(self) -> Path:
        """Get .claude/CLAUDE.local.md path."""
        return self.project_path / ".claude" / "CLAUDE.local.md"


class SlashCommand(BaseModel):
    """A slash command definition."""

    name: str = Field(..., description="Command name (without /)")
    description: str = Field(..., description="Short description")
    category: CommandCategory = Field(..., description="Command category")
    prompt: str = Field(..., description="Command prompt/action")
    requires_args: bool = Field(False, description="Whether command requires arguments")
    example_usage: str = Field("", description="Example usage")

    @validator("name")
    def validate_name(cls, v):
        """Validate command name format."""
        if not v or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid command name format: {v}")
        return v.lower()


class SlashCommandsConfig(BaseModel):
    """Configuration for slash commands generation."""

    commands_dir: Path = Field(
        ..., description="Commands directory (~/.claude/commands)"
    )
    project_type: ProjectType = Field(..., description="Project type")
    commands: list[SlashCommand] = Field(
        default_factory=list, description="Commands to generate"
    )
    common_workflows: list[str] = Field(
        default_factory=list, description="Common workflows from git history"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("commands_dir")
    def validate_commands_dir(cls, v):
        """Ensure commands directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class CommandUsage(BaseModel):
    """Usage statistics for a single command."""

    command: str = Field(..., description="Command name")
    count: int = Field(..., ge=1, description="Number of times used")
    last_used: datetime = Field(..., description="Last usage timestamp")
    category: str = Field("unknown", description="Command category (if detected)")

    @validator("command")
    def validate_command(cls, v):
        """Validate command format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Command cannot be empty")
        return v.strip()


class UsageAnalyticsConfig(BaseModel):
    """Configuration for usage analytics generation."""

    project_path: Path = Field(..., description="Project root directory")
    fish_history_path: Path = Field(..., description="Path to Fish shell history file")
    command_stats: dict[str, CommandUsage] = Field(
        default_factory=dict, description="Command usage statistics"
    )
    top_commands: list[str] = Field(
        default_factory=list, description="Top N most used commands"
    )
    tool_usage: dict[str, int] = Field(
        default_factory=dict, description="Tool usage counts"
    )
    workflow_patterns: list[str] = Field(
        default_factory=list, description="Detected workflow patterns"
    )
    total_commands: int = Field(0, ge=0, description="Total commands parsed")
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("project_path")
    def validate_project_path(cls, v):
        """Validate project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

    @validator("fish_history_path")
    def validate_fish_history_path(cls, v):
        """Validate Fish history file exists."""
        if not v.exists():
            raise ValueError(f"Fish history file does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return v

    @property
    def claude_file(self) -> Path:
        """Get CLAUDE.md path for analytics output."""
        return self.project_path / "CLAUDE.md"

    @property
    def unique_commands(self) -> int:
        """Get count of unique commands."""
        return len(self.command_stats)


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


# ============================================================================
# Permission Learning Schemas
# ============================================================================


class PermissionApprovalEntry(BaseModel):
    """Log entry for a permission approval."""

    timestamp: datetime = Field(default_factory=datetime.now)
    permission: str = Field(..., description="Approved permission string")
    session_id: str = Field(..., description="Claude Code session identifier")
    project_path: str = Field(..., description="Project where approval occurred")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context metadata"
    )

    @validator("permission")
    def validate_permission(cls, v):
        """Validate permission format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Permission cannot be empty")
        if len(v) > 200:
            raise ValueError("Permission too long (max 200 chars)")
        if "\n" in v:
            raise ValueError("Permission cannot contain newlines")
        if "<<" in v or "EOF" in v:
            raise ValueError("Permission cannot contain heredoc markers")
        return v.strip()


class PermissionPattern(BaseModel):
    """Detected pattern in permission approvals."""

    pattern_type: str = Field(
        ...,
        description="Type: git_read_only, git_all_safe, pytest, ruff, modern_cli, project_full_access",
    )
    occurrences: int = Field(..., ge=1, description="Number of times pattern observed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    examples: list[str] = Field(
        default_factory=list, description="Example approvals matching pattern"
    )
    detected_at: datetime = Field(default_factory=datetime.now)
    time_window_days: int = Field(30, ge=1, description="Detection window in days")

    @validator("pattern_type")
    def validate_pattern_type(cls, v):
        """Validate pattern type."""
        valid_types = {
            "git_read_only",
            "git_all_safe",
            "pytest",
            "ruff",
            "modern_cli",
            "project_full_access",
            "file_operations",
            "test_execution",
        }
        if v not in valid_types:
            raise ValueError(f"Invalid pattern type: {v}")
        return v


class PatternSuggestion(BaseModel):
    """Suggestion to apply a detected pattern."""

    description: str = Field(..., description="Human-readable description")
    pattern: PermissionPattern = Field(..., description="Underlying pattern")
    proposed_rule: str = Field(..., description="Proposed permission rule")
    would_allow: list[str] = Field(
        default_factory=list, description="Examples of what would be auto-allowed"
    )
    would_still_ask: list[str] = Field(
        default_factory=list, description="Examples that would still require approval"
    )
    approved_examples: list[str] = Field(
        default_factory=list, description="User's actual approvals that led to this"
    )
    impact_estimate: str = Field(
        "", description="Estimated impact (e.g., '50% fewer prompts')"
    )

    @property
    def confidence_percentage(self) -> int:
        """Get confidence as percentage."""
        return int(self.pattern.confidence * 100)


# ============================================================================
# Context Optimization Schemas
# ============================================================================


class ContextAccessLog(BaseModel):
    """Log entry for CLAUDE.md section access."""

    timestamp: datetime = Field(default_factory=datetime.now)
    section_name: str = Field(
        ..., description="Section accessed (e.g., 'Modern CLI Tools')"
    )
    tokens_in_section: int = Field(0, ge=0, description="Estimated tokens in section")
    relevance_score: float = Field(
        0.0, ge=0.0, le=1.0, description="How relevant was this section (0-1)"
    )
    session_id: str = Field(..., description="Session identifier")
    query_context: str = Field("", description="What was Claude trying to do")

    @validator("section_name")
    def validate_section_name(cls, v):
        """Validate section name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Section name cannot be empty")
        return v.strip()


class SectionUsage(BaseModel):
    """Usage statistics for a CLAUDE.md section."""

    section_name: str = Field(..., description="Section name")
    total_loads: int = Field(0, ge=0, description="Times section was loaded")
    total_references: int = Field(0, ge=0, description="Times actually referenced")
    total_tokens: int = Field(0, ge=0, description="Total tokens in section")
    avg_relevance: float = Field(
        0.0, ge=0.0, le=1.0, description="Average relevance when used"
    )
    last_used: datetime | None = Field(None, description="Last usage timestamp")

    @property
    def utilization_rate(self) -> float:
        """Calculate utilization rate (references / loads)."""
        if self.total_loads == 0:
            return 0.0
        return self.total_references / self.total_loads

    @property
    def is_noise(self) -> bool:
        """Check if section is noise (loaded but rarely used)."""
        return self.total_loads > 5 and self.utilization_rate < 0.1


class ContextOptimization(BaseModel):
    """Optimization suggestion for CLAUDE.md."""

    optimization_type: str = Field(
        ..., description="Type: prune_section, reorder, add_quick_ref, add_missing"
    )
    section_name: str = Field(..., description="Section to optimize")
    reason: str = Field(..., description="Why this optimization is suggested")
    impact: str = Field(..., description="Expected impact")
    token_savings: int = Field(0, ge=0, description="Estimated token savings")
    priority: int = Field(..., ge=1, le=3, description="Priority (1=high, 3=low)")

    @validator("optimization_type")
    def validate_optimization_type(cls, v):
        """Validate optimization type."""
        valid_types = {"prune_section", "reorder", "add_quick_ref", "add_missing"}
        if v not in valid_types:
            raise ValueError(f"Invalid optimization type: {v}")
        return v


# ============================================================================
# Workflow Detection Schemas
# ============================================================================


class SlashCommandLog(BaseModel):
    """Log entry for slash command invocation."""

    timestamp: datetime = Field(default_factory=datetime.now)
    command: str = Field(..., description="Command invoked (e.g., '/speckit.specify')")
    session_id: str = Field(..., description="Session identifier")
    success: bool = Field(True, description="Whether command succeeded")
    duration_ms: int | None = Field(None, description="Execution duration")
    project_path: str = Field("", description="Project path if applicable")

    @validator("command")
    def validate_command(cls, v):
        """Validate command format."""
        if not v.startswith("/"):
            raise ValueError("Command must start with /")
        return v


class WorkflowSequence(BaseModel):
    """Detected sequence of slash commands."""

    commands: list[str] = Field(..., description="Ordered list of commands")
    occurrences: int = Field(..., ge=1, description="Times this sequence occurred")
    completion_rate: float = Field(
        0.0, ge=0.0, le=1.0, description="How often sequence completes"
    )
    avg_duration_ms: int | None = Field(None, description="Average total duration")
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)

    @validator("commands")
    def validate_commands(cls, v):
        """Validate command sequence."""
        if len(v) < 2:
            raise ValueError("Sequence must have at least 2 commands")
        if not all(cmd.startswith("/") for cmd in v):
            raise ValueError("All commands must start with /")
        return v


class WorkflowSuggestion(BaseModel):
    """Suggestion to bundle workflow commands."""

    description: str = Field(..., description="Workflow description")
    sequence: WorkflowSequence = Field(..., description="Underlying sequence")
    proposed_command: str = Field(..., description="Proposed bundled command name")
    script_content: str = Field(..., description="Script implementation")
    impact_estimate: str = Field("", description="Estimated time savings")

    @validator("proposed_command")
    def validate_proposed_command(cls, v):
        """Validate proposed command."""
        if not v.startswith("/"):
            raise ValueError("Proposed command must start with /")
        return v


# ============================================================================
# Instruction Tracking Schemas
# ============================================================================


class PolicyViolation(BaseModel):
    """Record of a policy violation."""

    timestamp: datetime = Field(default_factory=datetime.now)
    policy_name: str = Field(..., description="Name of violated policy")
    violation_type: str = Field(..., description="Type of violation")
    session_id: str = Field(..., description="Session identifier")
    details: str = Field("", description="Violation details")
    severity: str = Field(..., description="Severity: low, medium, high")

    @validator("severity")
    def validate_severity(cls, v):
        """Validate severity."""
        if v not in {"low", "medium", "high"}:
            raise ValueError("Severity must be: low, medium, or high")
        return v


class InstructionEffectiveness(BaseModel):
    """Effectiveness metrics for an instruction/policy."""

    policy_name: str = Field(..., description="Policy name")
    total_sessions: int = Field(0, ge=0, description="Total sessions observed")
    compliant_sessions: int = Field(0, ge=0, description="Compliant sessions")
    violations: list[PolicyViolation] = Field(
        default_factory=list, description="Recent violations"
    )
    effectiveness_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Compliance rate"
    )
    last_evaluated: datetime = Field(default_factory=datetime.now)

    @property
    def is_effective(self) -> bool:
        """Check if policy is effective (>70% compliance)."""
        return self.effectiveness_score >= 0.7

    @property
    def needs_improvement(self) -> bool:
        """Check if policy needs rewording (<70% compliance)."""
        return self.effectiveness_score < 0.7


class InstructionImprovement(BaseModel):
    """Suggested improvement for an instruction."""

    policy_name: str = Field(..., description="Policy to improve")
    current_wording: str = Field(..., description="Current instruction text")
    suggested_wording: str = Field(..., description="Improved instruction text")
    reason: str = Field(..., description="Why this improvement is needed")
    effectiveness_data: InstructionEffectiveness = Field(
        ..., description="Underlying effectiveness data"
    )
    priority: int = Field(..., ge=1, le=3, description="Priority (1=high, 3=low)")


# ============================================================================
# Cross-Project Schemas
# ============================================================================


class ProjectArchetype(BaseModel):
    """Detected project archetype."""

    archetype: str = Field(
        ...,
        description="Type: Python/pytest, TypeScript/vitest, Rust/cargo, NixOS, etc.",
    )
    indicators: list[str] = Field(
        default_factory=list, description="Files/patterns that indicate this type"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    detected_at: datetime = Field(default_factory=datetime.now)

    @validator("archetype")
    def validate_archetype(cls, v):
        """Validate archetype."""
        valid_archetypes = {
            "Python/pytest",
            "Python/unittest",
            "TypeScript/vitest",
            "TypeScript/jest",
            "Rust/cargo",
            "NixOS",
            "Go/testing",
            "Unknown",
        }
        if v not in valid_archetypes:
            raise ValueError(f"Invalid archetype: {v}")
        return v


class CrossProjectPattern(BaseModel):
    """Pattern learned from one project, applicable to others."""

    pattern_type: str = Field(
        ..., description="Type: permission, workflow, context, configuration"
    )
    source_project: str = Field(..., description="Project where pattern originated")
    source_archetype: str = Field(..., description="Source project archetype")
    pattern_data: dict[str, Any] = Field(
        default_factory=dict, description="Pattern details"
    )
    applicability_score: float = Field(
        ..., ge=0.0, le=1.0, description="How applicable to other projects"
    )
    learned_at: datetime = Field(default_factory=datetime.now)


class TransferSuggestion(BaseModel):
    """Suggestion to transfer pattern to another project."""

    description: str = Field(..., description="Transfer description")
    pattern: CrossProjectPattern = Field(..., description="Pattern to transfer")
    target_project: str = Field(..., description="Target project path")
    target_archetype: str = Field(..., description="Target project archetype")
    compatibility_score: float = Field(
        ..., ge=0.0, le=1.0, description="Compatibility with target"
    )
    action: str = Field(..., description="What would be applied")
    examples: list[str] = Field(
        default_factory=list, description="Examples from source project"
    )


# ============================================================================
# Meta-Learning Schemas
# ============================================================================


class LearningMetrics(BaseModel):
    """Metrics for learning system effectiveness."""

    component: str = Field(
        ...,
        description="Component: permissions, mcp, context, workflows, instructions",
    )
    total_suggestions: int = Field(0, ge=0, description="Total suggestions made")
    accepted: int = Field(0, ge=0, description="Suggestions accepted")
    rejected: int = Field(0, ge=0, description="Suggestions rejected")
    false_positives: int = Field(0, ge=0, description="Incorrect suggestions")
    acceptance_rate: float = Field(0.0, ge=0.0, le=1.0, description="Acceptance rate")
    false_positive_rate: float = Field(
        0.0, ge=0.0, le=1.0, description="False positive rate"
    )
    last_updated: datetime = Field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Check if learning is healthy (>50% acceptance, <20% false positives)."""
        return self.acceptance_rate > 0.5 and self.false_positive_rate < 0.2


class ThresholdAdjustment(BaseModel):
    """Adjustment to detection thresholds."""

    component: str = Field(..., description="Component being adjusted")
    threshold_name: str = Field(..., description="Threshold parameter name")
    old_value: float = Field(..., description="Previous value")
    new_value: float = Field(..., description="New value")
    reason: str = Field(..., description="Why adjustment was made")
    adjusted_at: datetime = Field(default_factory=datetime.now)


class LearningHealthReport(BaseModel):
    """Health report for the learning system."""

    overall_health: str = Field(..., description="Overall: excellent, good, fair, poor")
    component_metrics: list[LearningMetrics] = Field(
        default_factory=list, description="Metrics per component"
    )
    recent_adjustments: list[ThresholdAdjustment] = Field(
        default_factory=list, description="Recent threshold adjustments"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="System recommendations"
    )
    generated_at: datetime = Field(default_factory=datetime.now)

    @validator("overall_health")
    def validate_overall_health(cls, v):
        """Validate overall health."""
        if v not in {"excellent", "good", "fair", "poor"}:
            raise ValueError("Health must be: excellent, good, fair, or poor")
        return v


# ============================================================================
# Unified Engine Schemas
# ============================================================================


class LearningReport(BaseModel):
    """Consolidated report from all learners."""

    timestamp: datetime = Field(default_factory=datetime.now)
    permission_patterns: list[PatternSuggestion] = Field(
        default_factory=list, description="Permission learning suggestions"
    )
    mcp_optimizations: list[dict[str, Any]] = Field(
        default_factory=list, description="MCP optimization suggestions"
    )
    context_suggestions: list[ContextOptimization] = Field(
        default_factory=list, description="Context optimization suggestions"
    )
    workflow_patterns: list[WorkflowSuggestion] = Field(
        default_factory=list, description="Workflow bundling suggestions"
    )
    instruction_improvements: list[InstructionImprovement] = Field(
        default_factory=list, description="Instruction effectiveness improvements"
    )
    cross_project_transfers: list[TransferSuggestion] = Field(
        default_factory=list, description="Cross-project pattern transfers"
    )
    meta_insights: dict[str, float] = Field(
        default_factory=dict, description="Meta-learning health metrics"
    )
    total_suggestions: int = Field(
        0, ge=0, description="Total suggestions across all components"
    )
    estimated_improvements: str = Field(
        "", description="Human-readable impact estimate"
    )

    @property
    def has_suggestions(self) -> bool:
        """Check if report has any suggestions."""
        return self.total_suggestions > 0


class AdaptiveSystemConfig(BaseModel):
    """Configuration for adaptive system engine."""

    interactive: bool = Field(True, description="Whether to prompt user interactively")
    min_occurrences: int = Field(
        3, ge=1, description="Minimum occurrences for pattern detection"
    )
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence for suggestions"
    )
    analysis_period_days: int = Field(30, ge=1, description="Analysis window in days")
    max_suggestions_per_component: int = Field(
        5, ge=1, description="Max suggestions per component"
    )
    enable_meta_learning: bool = Field(
        True, description="Whether to enable meta-learning calibration"
    )


# ============================================================================
# Validation Schemas
# ============================================================================


class ValidationResult(BaseModel):
    """Result of validation check."""

    valid: bool = Field(..., description="Whether validation passed")
    severity: str = Field(..., description="Severity: fail, warn, info")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    info: list[str] = Field(default_factory=list, description="Info messages")
    validated_at: datetime = Field(default_factory=datetime.now)

    @validator("severity")
    def validate_severity(cls, v):
        """Validate severity."""
        if v not in {"fail", "warn", "info"}:
            raise ValueError("Severity must be: fail, warn, or info")
        return v

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


class SourceArtifactDeclaration(BaseModel):
    """Declaration of manual sources and generated artifacts."""

    manual_sources: list[str] = Field(
        default_factory=list, description="Files that are manually edited"
    )
    generated_artifacts: list[str] = Field(
        default_factory=list, description="Files that are auto-generated"
    )
    validated_at: datetime = Field(default_factory=datetime.now)

    @validator("manual_sources", "generated_artifacts")
    def validate_no_duplicates(cls, v):
        """Ensure no duplicate filenames."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate filenames in list")
        return v

    @property
    def has_overlap(self) -> bool:
        """Check if sources and artifacts overlap."""
        return bool(set(self.manual_sources) & set(self.generated_artifacts))


class GenerationHeader(BaseModel):
    """Generation header for artifacts."""

    generator_name: str = Field(..., description="Name of generator class")
    generated_at: datetime = Field(default_factory=datetime.now)
    source_files: list[str] = Field(
        default_factory=list, description="Source files used"
    )
    warning_message: str = Field(
        "AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY", description="Warning message"
    )

    def to_html_comment(self) -> str:
        """Generate HTML comment format for markdown files."""
        sources = ", ".join(self.source_files) if self.source_files else "N/A"
        return f"""<!--
{'=' * 60}
  {self.warning_message}

  Generated: {self.generated_at.isoformat()}
  Generator: {self.generator_name}
  Sources: {sources}

  To modify, edit source files and regenerate.
{'=' * 60}
-->"""
