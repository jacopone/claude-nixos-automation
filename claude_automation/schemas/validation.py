"""
Validation and artifact generation tracking schemas.

Handles validation results, source/artifact declarations, and generation headers.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator

# ============================================================================
# Validation Schemas
# ============================================================================


class ValidationResult(BaseModel):
    """Result of validation check."""

    valid: bool = Field(..., description="Whether validation passed")
    severity: str = Field(..., description="Severity: fail, warn, info")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    info: list[str] = Field(default_factory=list, description="Info messages")
    validated_at: datetime = Field(default_factory=datetime.now)

    @validator("severity")
    def validate_severity(cls, v):
        """Validate severity."""
        if v not in {"fail", "warn", "info"}:
            raise ValueError("Severity must be: fail, warn, or info")
        return v

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


class SourceArtifactDeclaration(BaseModel):
    """Declaration of manual sources and generated artifacts."""

    manual_sources: list[str] = Field(
        default_factory=list, description="Files that are manually edited"
    )
    generated_artifacts: list[str] = Field(
        default_factory=list, description="Files that are auto-generated"
    )
    validated_at: datetime = Field(default_factory=datetime.now)

    @validator("manual_sources", "generated_artifacts")
    def validate_no_duplicates(cls, v):
        """Ensure no duplicate filenames."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate filenames in list")
        return v

    @property
    def has_overlap(self) -> bool:
        """Check if sources and artifacts overlap."""
        return bool(set(self.manual_sources) & set(self.generated_artifacts))


class GenerationHeader(BaseModel):
    """Generation header for artifacts."""

    generator_name: str = Field(..., description="Name of generator class")
    generated_at: datetime = Field(default_factory=datetime.now)
    source_files: list[str] = Field(
        default_factory=list, description="Source files used"
    )
    warning_message: str = Field(
        "AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY", description="Warning message"
    )

    def to_html_comment(self) -> str:
        """Generate HTML comment format for markdown files."""
        sources = ", ".join(self.source_files) if self.source_files else "N/A"
        return f"""<!--
{'=' * 60}
  {self.warning_message}

  Generated: {self.generated_at.isoformat()}
  Generator: {self.generator_name}
  Sources: {sources}

  To modify, edit source files and regenerate.
{'=' * 60}
-->"""
