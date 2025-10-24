"""
Learning cycle and meta-learning schemas.

Handles project archetype detection, cross-project pattern transfer, and meta-learning metrics.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

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

    @property
    def name(self) -> str:
        """Alias for archetype to match test expectations."""
        return self.archetype.replace("/", "-").lower()

    @property
    def test_framework(self) -> str:
        """Extract test framework from archetype name."""
        # Parse format: "Language/TestFramework" or "Language/BuildSystem"
        parts = self.archetype.split("/")
        if len(parts) == 2:
            # Return the second part which is usually test framework or build system
            return parts[1]
        return self.archetype

    @property
    def build_system(self) -> str:
        """Extract build system from archetype name."""
        # For certain archetypes, the second part is the build system
        parts = self.archetype.split("/")
        if len(parts) == 2:
            framework = parts[1].lower()
            # Known build systems
            if framework in ["cargo", "npm", "yarn", "pnpm", "poetry", "pip"]:
                return framework
            # For test frameworks, infer build system from language
            if "rust" in self.archetype.lower():
                return "cargo"
            elif "python" in self.archetype.lower():
                return "pip"
            elif "typescript" in self.archetype.lower() or "javascript" in self.archetype.lower():
                return "npm"
            return parts[1]
        return self.archetype

    @property
    def common_tools(self) -> list[str]:
        """Extract common tools based on archetype."""
        tools = []
        arch_lower = self.archetype.lower()

        if "pytest" in arch_lower:
            tools.extend(["pytest", "python"])
        if "vitest" in arch_lower:
            tools.extend(["vitest", "typescript", "node"])
        if "jest" in arch_lower:
            tools.extend(["jest", "typescript", "node"])
        if "cargo" in arch_lower:
            tools.extend(["cargo", "rustc"])
        if "nix" in arch_lower:
            tools.extend(["nix", "nixos-rebuild"])

        return tools

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
            "Generic",
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

    @property
    def recommended_threshold(self) -> float:
        """Alias for new_value to match test expectations."""
        return self.new_value


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
# Unified Engine Schemas
# ============================================================================


class LearningReport(BaseModel):
    """Consolidated report from all learners."""

    timestamp: datetime = Field(default_factory=datetime.now)
    permission_patterns: list[Any] = Field(
        default_factory=list, description="Permission learning suggestions"
    )
    mcp_optimizations: list[dict[str, Any]] = Field(
        default_factory=list, description="MCP optimization suggestions"
    )
    context_suggestions: list[Any] = Field(
        default_factory=list, description="Context optimization suggestions"
    )
    workflow_patterns: list[Any] = Field(
        default_factory=list, description="Workflow bundling suggestions"
    )
    instruction_improvements: list[Any] = Field(
        default_factory=list, description="Instruction effectiveness improvements"
    )
    cross_project_transfers: list[Any] = Field(
        default_factory=list, description="Cross-project pattern transfers"
    )
    meta_insights: dict[str, Any] = Field(
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
