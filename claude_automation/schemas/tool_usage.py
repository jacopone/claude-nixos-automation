"""
Tool usage tracking schemas.

Handles system tool inventory, usage statistics, and analytics reporting.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class ToolCategory(str, Enum):
    """Tool categories from packages.nix structure."""

    AI_TOOLS = "ai-tools"
    DEV_TOOLS = "dev-tools"
    MODERN_CLI = "modern-cli"
    SYSTEM_TOOLS = "system-tools"
    PRODUCTIVITY = "productivity"
    NETWORK_SECURITY = "network-security"
    FILE_MANAGEMENT = "file-management"
    DATABASE_TOOLS = "database-tools"
    FONTS = "fonts"
    OTHER = "other"


class UsageSource(str, Enum):
    """Source of tool usage."""

    HUMAN = "human"
    CLAUDE_CODE = "claude-code"
    SCRIPT = "script"
    LIKELY_AI = "likely-ai"
    OTHER = "other"


class ToolInfo(BaseModel):
    """Information about an installed tool."""

    name: str = Field(..., description="Tool name (package name)")
    description: str = Field("", description="Tool description from packages.nix")
    url: str = Field("", description="Tool homepage URL")
    category: ToolCategory = Field(
        default=ToolCategory.OTHER, description="Tool category"
    )
    package_line: int = Field(0, ge=0, description="Line number in packages.nix")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Tool name cannot be empty")
        return v.strip()


class ToolUsageStats(BaseModel):
    """Usage statistics for a single tool."""

    tool_name: str = Field(..., description="Tool name")
    total_invocations: int = Field(0, ge=0, description="Total times invoked")
    human_invocations: int = Field(0, ge=0, description="Human invocations")
    claude_invocations: int = Field(0, ge=0, description="Claude Code invocations")
    script_invocations: int = Field(0, ge=0, description="Script invocations")
    first_used: datetime | None = Field(None, description="First usage timestamp")
    last_used: datetime | None = Field(None, description="Last usage timestamp")

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Tool name cannot be empty")
        return v.strip()

    @property
    def adoption_score(self) -> float:
        """Normalized usage score (invocations per day)."""
        if not self.first_used or not self.last_used:
            return 0.0
        days = (self.last_used - self.first_used).days or 1
        return self.total_invocations / days

    @property
    def human_percentage(self) -> float:
        """Percentage of usage from humans."""
        if self.total_invocations == 0:
            return 0.0
        return (self.human_invocations / self.total_invocations) * 100.0

    @property
    def claude_percentage(self) -> float:
        """Percentage of usage from Claude."""
        if self.total_invocations == 0:
            return 0.0
        return (self.claude_invocations / self.total_invocations) * 100.0

    @property
    def days_since_last_use(self) -> int | None:
        """Days since last use."""
        if not self.last_used:
            return None
        return (datetime.now() - self.last_used).days


class ToolUsageRecommendation(BaseModel):
    """Actionable recommendation for tool management."""

    tool_name: str = Field(..., description="Tool name")
    recommendation_type: str = Field(
        ...,
        description="Type: remove_dormant, highlight_value, policy_violation, human_vs_claude_gap",
    )
    reason: str = Field(..., description="Reason for recommendation")
    action: str = Field(..., description="Suggested action")
    priority: int = Field(..., ge=1, le=3, description="Priority (1=high, 3=low)")


class ToolUsageAnalyticsConfig(BaseModel):
    """Configuration for tool usage analytics generation."""

    project_path: Path = Field(..., description="Project root directory")
    analysis_period_days: int = Field(30, ge=1, description="Analysis period in days")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="Analysis timestamp"
    )

    # Tool inventory
    total_tools: int = Field(0, ge=0, description="Total installed tools")
    tool_inventory: list[ToolInfo] = Field(
        default_factory=list, description="All installed tools"
    )

    # Usage stats
    used_tools: list[ToolUsageStats] = Field(
        default_factory=list, description="Tools with usage"
    )
    dormant_tools: list[ToolInfo] = Field(
        default_factory=list, description="Tools never used in period"
    )

    # Aggregate metrics
    total_commands_tracked: int = Field(0, ge=0, description="Total commands in logs")
    human_tool_count: int = Field(0, ge=0, description="Unique tools used by humans")
    claude_tool_count: int = Field(0, ge=0, description="Unique tools used by Claude")

    # Recommendations
    recommendations: list[ToolUsageRecommendation] = Field(
        default_factory=list, description="Usage recommendations"
    )

    # Category breakdown
    usage_by_category: dict[str, int] = Field(
        default_factory=dict, description="Tool usage by category"
    )

    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, v: Path) -> Path:
        """Validate project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v

    @property
    def adoption_rate(self) -> float:
        """Percentage of tools actually used."""
        if self.total_tools == 0:
            return 0.0
        return (len(self.used_tools) / self.total_tools) * 100.0

    @property
    def unused_tool_count(self) -> int:
        """Count of dormant tools."""
        return len(self.dormant_tools)

    @property
    def claude_file(self) -> Path:
        """Get CLAUDE.md path for analytics output."""
        return self.project_path / "CLAUDE.md"
