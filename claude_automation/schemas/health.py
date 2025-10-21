"""
Learning data disk health tracking schemas.

Handles monitoring of disk usage for adaptive learning data (session logs,
learning cache, archives) with risk assessment and growth projections.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level for disk space usage."""

    GREEN = "green"  # <1% disk usage, >5 years until full
    YELLOW = "yellow"  # 1-5% disk usage, 1-5 years until full
    ORANGE = "orange"  # 5-20% disk usage, 6mo-1yr until full
    RED = "red"  # >20% disk usage or <6 months until full


class DiskHealthSnapshot(BaseModel):
    """
    Single snapshot of disk health metrics for historical tracking.

    Stored in ~/.claude/learning/disk_health_history.jsonl for growth analysis.
    """

    timestamp: datetime = Field(..., description="When this snapshot was taken")
    total_mb: int = Field(..., ge=0, description="Total learning data size")
    session_logs_mb: int = Field(..., ge=0, description="Size of session logs")
    learning_data_mb: int = Field(..., ge=0, description="Size of learning cache")
    archives_mb: int = Field(0, ge=0, description="Size of archives")
    available_gb: int = Field(..., ge=0, description="Available disk space")
    session_count: int = Field(0, ge=0, description="Number of sessions")


class LearningDataHealthReport(BaseModel):
    """
    Health report for learning data disk usage.

    Tracks current disk usage of learning data (session logs, learning cache)
    and provides risk assessment with actionable recommendations.

    Phase 1: Snapshot-based monitoring (no history tracking yet).
    Phase 1.5: Adds growth rate tracking via DiskHealthTracker.
    """

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When this report was generated",
    )

    # Sizes (in MB for human readability)
    session_logs_mb: int = Field(..., ge=0, description="Size of session logs")
    learning_data_mb: int = Field(..., ge=0, description="Size of learning cache")
    archives_mb: int = Field(
        0, ge=0, description="Size of compressed archives (if any)"
    )
    total_mb: int = Field(..., ge=0, description="Total learning data size")

    # Session statistics
    session_count: int = Field(
        0, ge=0, description="Number of Claude Code session files"
    )

    # Disk space
    available_gb: int = Field(..., ge=0, description="Available disk space in GB")
    usage_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of disk used by learning data"
    )

    # Risk assessment
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    risk_message: str = Field(..., description="Human-readable risk assessment")

    # Growth tracking (Phase 2 - optional for now)
    growth_mb_per_month: float | None = Field(
        None, description="Monthly growth rate (requires history)"
    )
    months_until_full: float | None = Field(
        None, description="Estimated months until disk full (requires growth rate)"
    )

    @property
    def is_healthy(self) -> bool:
        """Check if disk health is acceptable (GREEN or YELLOW)."""
        return self.risk_level in (RiskLevel.GREEN, RiskLevel.YELLOW)

    @property
    def needs_attention(self) -> bool:
        """Check if disk health requires user attention (ORANGE or RED)."""
        return self.risk_level in (RiskLevel.ORANGE, RiskLevel.RED)

    @property
    def exit_code(self) -> int:
        """
        Get appropriate exit code for CLI tool.

        Returns:
            0 = GREEN (no action needed)
            1 = YELLOW/ORANGE (optional/planned cleanup)
            2 = RED (urgent cleanup needed)
        """
        if self.risk_level == RiskLevel.GREEN:
            return 0
        elif self.risk_level in (RiskLevel.YELLOW, RiskLevel.ORANGE):
            return 1
        else:  # RED
            return 2

    @property
    def total_gb(self) -> float:
        """Total learning data size in GB."""
        return self.total_mb / 1024

    @property
    def projected_years(self) -> float | None:
        """Projected years until disk full (for display)."""
        if self.months_until_full is None:
            return None
        return self.months_until_full / 12
