"""
Workflow detection and slash command bundling schemas.

Handles slash command logging, workflow sequence detection, and bundling suggestions.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator

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
