"""
Context optimization and CLAUDE.md section usage tracking schemas.

Handles context access logging, section usage analytics, and optimization recommendations.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator

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
