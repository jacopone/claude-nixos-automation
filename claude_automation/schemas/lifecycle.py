"""
Session lifecycle tracking schemas.

Tracks the lifecycle stages of Claude Code session logs to enable value-based
cleanup decisions. Sessions progress through stages as insights are extracted
and implemented.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SessionLifecycle(str, Enum):
    """
    Lifecycle stage of a Claude Code session.

    Stages represent value extraction progress:
    - RAW: Session just created, not yet analyzed
    - ANALYZED: Session analyzed by MCP/usage analytics
    - INSIGHTS_GENERATED: Insights extracted and documented
    - IMPLEMENTED: Insights applied to system configuration

    Safe cleanup rule: Only delete sessions marked as IMPLEMENTED.
    """

    RAW = "raw"
    ANALYZED = "analyzed"
    INSIGHTS_GENERATED = "insights_generated"
    IMPLEMENTED = "implemented"


class SessionMetadata(BaseModel):
    """
    Lifecycle metadata for a Claude Code session.

    Stored as sidecar file: session.jsonl → session.jsonl.lifecycle.json
    """

    session_file: str = Field(..., description="Path to session .jsonl file")
    lifecycle_stage: SessionLifecycle = Field(
        default=SessionLifecycle.RAW,
        description="Current lifecycle stage"
    )

    # Timestamps for lifecycle transitions
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When session was created"
    )
    analyzed_at: datetime | None = Field(
        None,
        description="When session was analyzed"
    )
    insights_generated_at: datetime | None = Field(
        None,
        description="When insights were extracted"
    )
    implemented_at: datetime | None = Field(
        None,
        description="When insights were implemented"
    )

    # Optional metadata
    project_name: str | None = Field(None, description="Project this session belongs to")
    insights_summary: str | None = Field(
        None,
        description="Brief summary of insights extracted"
    )
    implementation_notes: str | None = Field(
        None,
        description="Notes about how insights were implemented"
    )

    @property
    def is_safe_to_cleanup(self) -> bool:
        """Check if session can be safely deleted."""
        return self.lifecycle_stage == SessionLifecycle.IMPLEMENTED

    @property
    def has_value(self) -> bool:
        """Check if session still has unextracted value."""
        return self.lifecycle_stage in (
            SessionLifecycle.RAW,
            SessionLifecycle.ANALYZED,
            SessionLifecycle.INSIGHTS_GENERATED
        )

    @property
    def age_days(self) -> float:
        """Calculate age of session in days."""
        return (datetime.now() - self.created_at).total_seconds() / 86400


class LifecycleStats(BaseModel):
    """
    Statistics about session lifecycle distribution.

    Used to understand how much unprocessed data exists.
    """

    total_sessions: int = Field(..., ge=0, description="Total number of sessions")
    raw_count: int = Field(0, ge=0, description="Sessions not yet analyzed")
    analyzed_count: int = Field(0, ge=0, description="Sessions analyzed but no insights")
    insights_generated_count: int = Field(
        0,
        ge=0,
        description="Sessions with documented insights"
    )
    implemented_count: int = Field(
        0,
        ge=0,
        description="Sessions with insights implemented (safe to cleanup)"
    )

    @property
    def has_unprocessed(self) -> bool:
        """Check if there are sessions that haven't been analyzed."""
        return self.raw_count > 0

    @property
    def has_pending_insights(self) -> bool:
        """Check if there are analyzed sessions without insights extracted."""
        return self.analyzed_count > 0 or self.insights_generated_count > 0

    @property
    def safe_to_cleanup_count(self) -> int:
        """Number of sessions safe to cleanup."""
        return self.implemented_count

    @property
    def valuable_data_count(self) -> int:
        """Number of sessions with potential value still to extract."""
        return self.raw_count + self.analyzed_count + self.insights_generated_count
