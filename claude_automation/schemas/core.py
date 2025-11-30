"""
Core foundational schemas used across all domains.

This module contains system-level types and enums that are referenced
by multiple domains. No business logic - pure data structures only.

Domain: Core (Foundation)
Dependencies: None (foundational layer)
"""

from datetime import datetime
from enum import Enum

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


class ClaudeRelevance(str, Enum):
    """Relevance level for tool documentation in CLAUDE.md.

    Used to filter which tools are included in generated documentation.
    Claude doesn't need to know about standard tools it already understands.
    """

    ESSENTIAL = "essential"  # Tool substitutions (fd, eza, bat, rg) - must document
    HIGH = "high"  # Non-obvious tools with unique syntax (jless, miller, choose)
    MEDIUM = "medium"  # Useful but Claude likely knows (devenv, lazygit)
    LOW = "low"  # Standard tools Claude knows (git, gcc, docker, npm)
    NONE = "none"  # System packages, fonts, libraries - skip entirely


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
    relevance: ClaudeRelevance = Field(
        default=ClaudeRelevance.MEDIUM,
        description="Relevance for CLAUDE.md documentation",
    )

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
        if v < 1:
            raise ValueError("Package count must be at least 1")
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
