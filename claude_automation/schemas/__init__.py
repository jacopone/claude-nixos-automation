"""
Schema package initialization.

Provides backward compatibility by re-exporting all schemas from domain modules.
Import from this package maintains existing code compatibility.
"""

# Core foundational schemas
# Configuration schemas
from claude_automation.schemas.config import (
    CommandCategory,
    CommandUsage,
    DirectoryContextConfig,
    DirectoryPurpose,
    GenerationResult,
    LocalContextConfig,
    PermissionsConfig,
    SlashCommand,
    SlashCommandsConfig,
    UsageAnalyticsConfig,
    UsagePattern,
)

# Context optimization schemas
from claude_automation.schemas.context import (
    ContextAccessLog,
    ContextOptimization,
    SectionUsage,
)
from claude_automation.schemas.core import (
    FishAbbreviation,
    GitStatus,
    ParsingResult,
    ProjectConfig,
    ProjectType,
    SystemConfig,
    ToolCategory,
    ToolInfo,
)

# Disk health monitoring schemas
from claude_automation.schemas.health import (
    LearningDataHealthReport,
    RiskLevel,
)

# Learning cycle schemas
from claude_automation.schemas.learning import (
    AdaptiveSystemConfig,
    CrossProjectPattern,
    InstructionEffectiveness,
    InstructionImprovement,
    LearningHealthReport,
    LearningMetrics,
    LearningReport,
    PolicyViolation,
    ProjectArchetype,
    ThresholdAdjustment,
    TransferSuggestion,
)

# MCP server schemas
from claude_automation.schemas.mcp import (
    GlobalMCPReport,
    MCPServerInfo,
    MCPServerSessionUtilization,
    MCPServerStatus,
    MCPServerType,
    MCPSessionStats,
    MCPToolUsage,
    MCPUsageAnalyticsConfig,
    MCPUsageRecommendation,
)

# Permission learning schemas
from claude_automation.schemas.permissions import (
    PatternSuggestion,
    PermissionApprovalEntry,
    PermissionPattern,
)

# Validation schemas
from claude_automation.schemas.validation import (
    GenerationHeader,
    SourceArtifactDeclaration,
    ValidationResult,
)

# Workflow detection schemas
from claude_automation.schemas.workflows import (
    SlashCommandLog,
    WorkflowSequence,
    WorkflowSuggestion,
)

__all__ = [
    # Core schemas
    "ToolCategory",
    "ProjectType",
    "ToolInfo",
    "FishAbbreviation",
    "GitStatus",
    "SystemConfig",
    "ProjectConfig",
    "ParsingResult",
    # Configuration schemas
    "CommandCategory",
    "CommandUsage",
    "DirectoryContextConfig",
    "DirectoryPurpose",
    "GenerationResult",
    "LocalContextConfig",
    "PermissionsConfig",
    "SlashCommand",
    "SlashCommandsConfig",
    "UsageAnalyticsConfig",
    "UsagePattern",
    # Permission schemas
    "PermissionApprovalEntry",
    "PermissionPattern",
    "PatternSuggestion",
    # MCP schemas
    "MCPServerType",
    "MCPServerStatus",
    "MCPServerInfo",
    "MCPToolUsage",
    "MCPSessionStats",
    "MCPServerSessionUtilization",
    "MCPUsageRecommendation",
    "GlobalMCPReport",
    "MCPUsageAnalyticsConfig",
    # Learning schemas
    "AdaptiveSystemConfig",
    "LearningReport",
    "ProjectArchetype",
    "CrossProjectPattern",
    "TransferSuggestion",
    "LearningMetrics",
    "ThresholdAdjustment",
    "LearningHealthReport",
    "PolicyViolation",
    "InstructionEffectiveness",
    "InstructionImprovement",
    # Context schemas
    "ContextAccessLog",
    "SectionUsage",
    "ContextOptimization",
    # Health schemas
    "RiskLevel",
    "LearningDataHealthReport",
    # Workflow schemas
    "SlashCommandLog",
    "WorkflowSequence",
    "WorkflowSuggestion",
    # Validation schemas
    "ValidationResult",
    "SourceArtifactDeclaration",
    "GenerationHeader",
]
