"""
Permission learning and approval tracking schemas.

Handles permission patterns, approvals, and suggestions for the adaptive learning system.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

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
        description="Pattern category type (e.g., Git_workflow, Github_cli, Nix_tools)",
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
        """Validate pattern type against known categories."""
        # All valid pattern categories from permission_pattern_detector.py
        # NOTE: Keys must start with uppercase to pass Claude Code validation
        # Claude Code error: "Tool names must start with uppercase"
        valid_types = {
            # Git operations
            "Git_read_only",
            "Git_workflow",  # renamed from git_all_safe
            "Git_destructive",
            # Development tools
            "Pytest",
            "Ruff",
            "Modern_cli",
            # File operations
            "File_operations",
            "File_write_operations",
            "Test_execution",
            "Project_full_access",
            # CLI tools (added 2025-12)
            "Github_cli",
            "Cloud_cli",
            "Package_managers",
            "Nix_tools",
            "Database_cli",
            "Network_tools",
            "Runtime_tools",
            # POSIX commands (added 2025-12)
            "Posix_filesystem",
            "Posix_search",
            "Posix_read",
            "Shell_utilities",
            "Dangerous_operations",
        }
        # Allow CrossFolder_* patterns for dynamic tool detection (Boris-style)
        if v.startswith("CrossFolder_"):
            return v
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
    tier: str = Field(
        "TIER_2_MODERATE",
        description="Tier classification: TIER_1_SAFE (global), TIER_2_MODERATE (project), TIER_3_RISKY (project)",
    )

    @validator("tier")
    def validate_tier(cls, v):
        """Validate tier classification."""
        valid_tiers = {"TIER_1_SAFE", "TIER_2_MODERATE", "TIER_3_RISKY", "CROSS_FOLDER"}
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier: {v}. Must be one of {valid_tiers}")
        return v

    @property
    def is_global(self) -> bool:
        """Check if this suggestion should be applied globally."""
        return self.tier in {"TIER_1_SAFE", "CROSS_FOLDER"}

    @property
    def confidence_percentage(self) -> int:
        """Get confidence as percentage."""
        return int(self.pattern.confidence * 100)


class SuggestionRejectionEntry(BaseModel):
    """Log entry for a rejected suggestion."""

    timestamp: datetime = Field(default_factory=datetime.now)
    suggestion_type: str = Field(
        ..., description="Type: workflow, permission, mcp, or context"
    )
    suggestion_fingerprint: str = Field(
        ..., description="Unique identifier for suggestion"
    )
    project_path: str = Field("", description="Project where rejection occurred")

    @validator("suggestion_type")
    def validate_type(cls, v):
        """Validate suggestion type."""
        if v not in {"workflow", "permission", "mcp", "context"}:
            raise ValueError(
                "suggestion_type must be 'workflow', 'permission', 'mcp', or 'context'"
            )
        return v
