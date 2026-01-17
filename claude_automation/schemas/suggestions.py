"""
CLAUDE.md Suggestion Engine schemas.

Handles suggestions for CLAUDE.md edits based on session conversation patterns.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SuggestionScope(str, Enum):
    """Where the suggestion should be applied."""

    GLOBAL = "global"  # ~/.claude/CLAUDE-USER-POLICIES.md
    PROJECT = "project"  # ./CLAUDE.md


class ClaudeMdSuggestion(BaseModel):
    """A suggested edit to CLAUDE.md based on session analysis."""

    instruction: str = Field(
        ...,
        description="The instruction text to add (e.g., 'Always use pytest for tests')",
    )
    scope: SuggestionScope = Field(
        ...,
        description="global (cross-project) or project (single project)",
    )
    target_file: str = Field(
        ...,
        description="Target file path (e.g., '~/.claude/CLAUDE-USER-POLICIES.md')",
    )
    suggested_section: str = Field(
        ...,
        description="Where to add it (e.g., '## Testing Conventions')",
    )
    occurrences: int = Field(
        ...,
        ge=1,
        description="How many times this instruction was seen",
    )
    projects: list[str] = Field(
        default_factory=list,
        description="Which projects this appeared in",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score based on frequency and consistency",
    )
    source_sessions: list[str] = Field(
        default_factory=list,
        description="Session IDs where this was detected",
    )
    pattern_type: str = Field(
        default="instruction",
        description="Pattern type: instruction, correction, preference",
    )
    detected_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_high_confidence(self) -> bool:
        """Check if suggestion is high confidence (>0.7)."""
        return self.confidence >= 0.7

    @property
    def is_cross_project(self) -> bool:
        """Check if suggestion appears in multiple projects."""
        return len(self.projects) >= 2


class InstructionPattern(BaseModel):
    """A detected instruction pattern from session analysis."""

    text: str = Field(..., description="The instruction text")
    pattern_type: Literal["always", "never", "remember", "correction", "preference"] = Field(
        ..., description="Type of instruction pattern"
    )
    session_id: str = Field(..., description="Session where detected")
    project_path: str = Field(..., description="Project path")
    message_index: int = Field(..., ge=0, description="Message index in session")
    detected_at: datetime = Field(default_factory=datetime.now)


class SuggestionReport(BaseModel):
    """Report of all CLAUDE.md suggestions."""

    timestamp: datetime = Field(default_factory=datetime.now)
    analysis_period_days: int = Field(..., ge=1, description="Days analyzed")
    sessions_analyzed: int = Field(..., ge=0, description="Number of sessions")
    global_suggestions: list[ClaudeMdSuggestion] = Field(
        default_factory=list,
        description="Suggestions for global CLAUDE.md",
    )
    project_suggestions: dict[str, list[ClaudeMdSuggestion]] = Field(
        default_factory=dict,
        description="Suggestions per project path",
    )
    total_suggestions: int = Field(0, ge=0, description="Total suggestions")

    @property
    def has_suggestions(self) -> bool:
        """Check if report has any suggestions."""
        return self.total_suggestions > 0

    def get_all_suggestions(self) -> list[ClaudeMdSuggestion]:
        """Get all suggestions as a flat list."""
        all_suggestions = list(self.global_suggestions)
        for project_list in self.project_suggestions.values():
            all_suggestions.extend(project_list)
        return all_suggestions


class SuggestionConfig(BaseModel):
    """Configuration for suggestion engine."""

    analysis_period_days: int = Field(30, ge=1, description="Days to analyze")
    min_occurrences: int = Field(
        3, ge=1, description="Minimum times an instruction must appear"
    )
    min_cross_project_count: int = Field(
        2, ge=2, description="Minimum projects for global suggestion"
    )
    confidence_threshold: float = Field(
        0.6, ge=0.0, le=1.0, description="Minimum confidence for suggestions"
    )
    max_suggestions: int = Field(
        10, ge=1, description="Maximum suggestions to return"
    )
    exclude_patterns: list[str] = Field(
        default_factory=lambda: [
            r"^(yes|no|ok|thanks|thank you)$",
            r"^(ultrathink|think|continue)",
        ],
        description="Regex patterns to exclude from detection",
    )
