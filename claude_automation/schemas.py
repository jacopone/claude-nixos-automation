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


class MCPUsageRecommendation(BaseModel):
    """Recommendation for MCP server usage."""

    server_name: str = Field(..., description="Server name")
    recommendation_type: str = Field(
        ..., description="Type: remove_unused, install_missing, fix_errors, optimize"
    )
    reason: str = Field(..., description="Reason for recommendation")
    action: str = Field(..., description="Suggested action")
    priority: int = Field(..., ge=1, le=3, description="Priority (1=high, 3=low)")


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
