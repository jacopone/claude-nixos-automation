"""
Pydantic schemas for user policies system.
Provides type safety and validation for policy management.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PolicyCategory(str, Enum):
    """Policy category types."""

    GIT = "git_policies"
    SYSTEM = "system_limitations"
    DOCUMENTATION = "documentation_standards"
    CODE_QUALITY = "code_quality"
    COMMUNICATION = "communication_style"
    PROJECT_MANAGEMENT = "project_management"


class PolicyMetadata(BaseModel):
    """Metadata for a single policy."""

    name: str = Field(..., description="Policy name")
    category: str = Field(..., description="Policy category")
    description: str = Field(..., description="Policy description")
    recommended: bool = Field(default=False, description="Is this recommended for most users")
    source: str = Field(..., description="Source of this policy")
    platform: str | None = Field(None, description="Platform-specific (e.g., NixOS)")
    added_date: datetime = Field(default_factory=datetime.now, description="When policy was added")
    version: str = Field(default="2.0", description="Version when policy was introduced")


class ScrapedPolicy(BaseModel):
    """Policy scraped from external source."""

    name: str
    category: str
    description: str
    source_url: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    scraped_at: datetime = Field(default_factory=datetime.now)


class PolicyVersionInfo(BaseModel):
    """Version information for policy tracking."""

    last_updated: datetime = Field(default_factory=datetime.now)
    policies_count: int = Field(default=0, description="Total number of policies")
    new_since_last: list[str] = Field(default_factory=list, description="New policy names")
    version: str = Field(default="2.0")


class WebScrapingResult(BaseModel):
    """Result of web scraping for best practices."""

    success: bool
    policies: list[ScrapedPolicy] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    source: str = Field(..., description="Source URL or identifier")
    scraped_at: datetime = Field(default_factory=datetime.now)


class UserPolicyPreferences(BaseModel):
    """User's policy preferences from interactive setup."""

    enable_git_policy: bool = Field(default=True)
    enable_system_limitations: bool = Field(default=True)
    enable_doc_standards: bool = Field(default=True)
    enable_code_quality: bool = Field(default=False)
    enable_communication: bool = Field(default=False)
    enable_project_mgmt: bool = Field(default=False)
    custom_preferences: dict[str, Any] = Field(default_factory=dict)
