---
status: active
created: 2025-10-17
updated: 2025-10-17
type: reference
lifecycle: persistent
---

# Data Model Reference

Complete reference for all Pydantic schemas in the Self-Improving Claude Code System.

**Total schemas**: 45 (as of implementation)

**Purpose**: This document provides comprehensive documentation of all data structures used across the system, enabling developers to understand the shape and validation rules for data flowing through analyzers, generators, and the adaptive system engine.

---

## Table of Contents

1. [Core System Models](#core-system-models)
2. [Configuration Models](#configuration-models)
3. [Permission Learning Models](#permission-learning-models)
4. [MCP Analytics Models](#mcp-analytics-models)
5. [Context Optimization Models](#context-optimization-models)
6. [Workflow Detection Models](#workflow-detection-models)
7. [Instruction Effectiveness Models](#instruction-effectiveness-models)
8. [Cross-Project Transfer Models](#cross-project-transfer-models)
9. [Meta-Learning Models](#meta-learning-models)
10. [Source-Artifact Architecture Models](#source-artifact-architecture-models)

---

## Core System Models

### ToolInfo
**Purpose**: Represents a command-line tool available on the system.

**Fields**:
- `name: str` - Tool name (e.g., "bat", "eza")
- `description: str` - What the tool does
- `url: Optional[str]` - Documentation URL
- `package: str` - Nix package name

**Usage**: Used by SystemGenerator to populate tool listings in CLAUDE.md

---

### FishAbbreviation
**Purpose**: Fish shell command abbreviation.

**Fields**:
- `abbr: str` - Abbreviation (e.g., "lg")
- `expansion: str` - Full command (e.g., "eza -la --git")

**Usage**: Generated from Fish shell config, documented in CLAUDE.md

---

### GitStatus
**Purpose**: Captures git repository state.

**Fields**:
- `is_repo: bool` - Whether directory is a git repo
- `current_branch: Optional[str]` - Active branch name
- `main_branch: Optional[str]` - Main/master branch name
- `status: Optional[str]` - Output of `git status`
- `recent_commits: Optional[str]` - Recent commit messages

**Usage**: Included in CLAUDE.md context for git-aware workflows

---

### GenerationResult
**Purpose**: Result of a generator run.

**Fields**:
- `success: bool` - Whether generation succeeded
- `output_file: Optional[Path]` - Path to generated artifact
- `warnings: list[str]` - Non-fatal issues
- `errors: list[str]` - Fatal errors
- `metadata: dict` - Additional generation info

**Usage**: Returned by all generators, consumed by AdaptiveSystemEngine

---

### ParsingResult
**Purpose**: Result of parsing source files.

**Fields**:
- `success: bool` - Whether parsing succeeded
- `data: Optional[dict]` - Parsed data structure
- `warnings: list[str]` - Non-fatal parsing issues
- `errors: list[str]` - Fatal parsing errors

**Usage**: Returned by scrapers, consumed by generators

---

## Configuration Models

### SystemConfig
**Purpose**: System-level configuration from `~/.claude/config.yaml`.

**Fields**:
- `tools: list[ToolInfo]` - Available CLI tools
- `fish_abbreviations: list[FishAbbreviation]` - Shell abbreviations
- `git_status: Optional[GitStatus]` - Git repository context
- `platform: str` - OS platform (linux, darwin, etc.)
- `os_version: str` - OS version string
- `user_policies: Optional[str]` - Content from CLAUDE-USER-POLICIES.md
- `has_user_policies: bool` - Whether user policies file exists

**Usage**: Primary config for SystemGenerator

---

### ProjectConfig
**Purpose**: Project-level configuration from `CLAUDE.md` or `.claude/config.yaml`.

**Fields**:
- `project_name: str` - Project name
- `project_root: Path` - Absolute path to project root
- `description: Optional[str]` - Project description
- `directory_context: Optional[DirectoryContextConfig]` - Directory context settings
- `permissions: Optional[PermissionsConfig]` - Auto-approval permissions
- `local_context: Optional[LocalContextConfig]` - Local context configuration
- `slash_commands: Optional[SlashCommandsConfig]` - Custom slash commands
- `usage_analytics: Optional[UsageAnalyticsConfig]` - Usage tracking settings
- `mcp_usage_analytics: Optional[MCPUsageAnalyticsConfig]` - MCP server analytics

**Usage**: Primary config for ProjectGenerator

---

### DirectoryContextConfig
**Purpose**: Configuration for additional working directories.

**Fields**:
- `additional_dirs: list[Path]` - Directories to include in context
- `max_depth: int = 2` - Maximum directory traversal depth

**Usage**: Enables multi-directory project support

---

### PermissionsConfig
**Purpose**: Auto-approval permission patterns.

**Fields**:
- `patterns: list[str]` - Permission patterns (e.g., "Read(//home/user/project/**)")
- `enabled: bool = True` - Whether auto-approval is enabled

**Usage**: Consumed by PermissionsGenerator, stored in `settings.local.json`

---

### LocalContextConfig
**Purpose**: Local project context snippets.

**Fields**:
- `snippets: dict[str, str]` - Named context snippets
- `enabled: bool = True` - Whether local context is enabled

**Usage**: Injected into project CLAUDE.md

---

### SlashCommandsConfig
**Purpose**: Custom slash command definitions.

**Fields**:
- `commands: list[SlashCommand]` - Defined slash commands

**Usage**: Generated into `.claude/commands/` directory

---

### SlashCommand
**Purpose**: A single slash command definition.

**Fields**:
- `name: str` - Command name (without leading /)
- `description: str` - What the command does
- `prompt: str` - Prompt template to execute
- `scope: str` - "global" or "project"

**Usage**: Used by SlashCommandsGenerator

---

### UsageAnalyticsConfig
**Purpose**: Configuration for usage analytics tracking.

**Fields**:
- `enabled: bool = True` - Whether analytics are enabled
- `retention_days: int = 90` - How long to keep analytics data
- `track_commands: bool = True` - Track shell command usage
- `track_approvals: bool = True` - Track permission approvals

**Usage**: Controls ApprovalTracker and usage analytics behavior

---

### MCPUsageAnalyticsConfig
**Purpose**: Configuration for MCP server usage analytics.

**Fields**:
- `enabled: bool = True` - Whether MCP analytics are enabled
- `track_sessions: bool = True` - Track session-level data
- `track_tools: bool = True` - Track individual tool usage

**Usage**: Controls MCPUsageAnalyzer behavior

---

### AdaptiveSystemConfig
**Purpose**: Master configuration for adaptive learning system.

**Fields**:
- `enabled: bool = True` - Master switch for adaptive learning
- `permission_learning_enabled: bool = True` - Permission pattern learning
- `mcp_optimization_enabled: bool = True` - MCP server optimization
- `context_optimization_enabled: bool = True` - Context pruning/reordering
- `workflow_detection_enabled: bool = True` - Workflow pattern detection
- `instruction_tracking_enabled: bool = True` - Instruction effectiveness tracking
- `cross_project_learning_enabled: bool = True` - Cross-project pattern transfer
- `meta_learning_enabled: bool = True` - Self-calibration
- `confidence_threshold: float = 0.7` - Minimum confidence for suggestions
- `min_pattern_occurrences: int = 3` - Minimum occurrences to detect pattern
- `analysis_window_days: int = 30` - Rolling window for analysis

**Usage**: Controls AdaptiveSystemEngine behavior

---

## Permission Learning Models

### PermissionApprovalEntry
**Purpose**: A single permission approval event.

**Fields**:
- `timestamp: datetime` - When approval happened
- `session_id: str` - Claude Code session ID
- `permission_pattern: str` - Exact permission string approved (e.g., "Read(//home/user/project/**)")
- `tool_name: str` - Tool that required approval (e.g., "Read")
- `path_pattern: str` - Path portion of permission
- `project_root: Optional[Path]` - Project context (if any)
- `approved: bool` - Whether user approved (always True if logged)

**Usage**: Logged by ApprovalTracker, consumed by PermissionPatternDetector

**Storage**: `~/.claude/approval-history.jsonl` (JSONL format, one entry per line)

---

### PermissionPattern
**Purpose**: A detected permission pattern with statistics.

**Fields**:
- `pattern_type: str` - Pattern category (e.g., "git_read_only", "pytest", "project_full_access")
- `permission_template: str` - Generalized permission string
- `occurrences: int` - How many times this pattern was approved
- `confidence: float` - Statistical confidence (0.0-1.0)
- `last_seen: datetime` - Most recent approval timestamp
- `projects: list[str]` - Projects where pattern was used
- `suggested_permission: str` - Final permission string to add to settings.local.json

**Usage**: Output of PermissionPatternDetector, shown to user for approval

**Confidence Calculation**:
```python
confidence = (occurrences / total_approvals) * recency_weight
recency_weight = 1.0 if last_seen within 7 days else 0.8
```

---

### PatternSuggestion
**Purpose**: A suggestion to add a permission pattern.

**Fields**:
- `pattern: PermissionPattern` - The detected pattern
- `justification: str` - Why this pattern was suggested
- `risk_level: str` - "low", "medium", "high" (based on path scope)
- `auto_approvable: bool` - Whether safe to auto-approve

**Usage**: Presented to user by IntelligentPermissionsGenerator

---

## MCP Analytics Models

### MCPServerInfo
**Purpose**: Information about an MCP server.

**Fields**:
- `server_id: str` - Unique server identifier
- `name: str` - Human-readable server name
- `command: str` - Command to start the server
- `args: list[str]` - Command arguments
- `env: dict[str, str]` - Environment variables
- `scope: str` - "global" (system-wide) or "project" (project-specific)
- `project_path: Optional[Path]` - Project root if project-scoped

**Usage**: Parsed from `.claude/mcp.json` files

---

### MCPToolUsage
**Purpose**: Usage statistics for a single MCP tool.

**Fields**:
- `tool_name: str` - Tool name (e.g., "list_dir", "read_file")
- `invocations: int` - Number of times invoked
- `last_used: datetime` - Most recent invocation
- `token_consumption: int` - Estimated tokens consumed by this tool

**Usage**: Tracked by MCPUsageAnalyzer

---

### MCPSessionStats
**Purpose**: MCP server statistics for a single session.

**Fields**:
- `session_id: str` - Claude Code session ID
- `server_id: str` - MCP server ID
- `loaded: bool` - Whether server was loaded in session
- `used: bool` - Whether server was actually invoked
- `tool_usages: list[MCPToolUsage]` - Per-tool usage stats
- `total_invocations: int` - Total tool invocations
- `session_start: datetime` - Session start time
- `session_end: Optional[datetime]` - Session end time (if finished)

**Usage**: Logged by MCPUsageAnalyzer per session

**Storage**: `~/.claude/mcp-analytics.jsonl`

---

### MCPServerSessionUtilization
**Purpose**: Utilization metrics for an MCP server across all sessions.

**Fields**:
- `server_id: str` - MCP server ID
- `total_sessions: int` - Total sessions where server was loaded
- `sessions_used: int` - Sessions where server was actually invoked
- `utilization_rate: float` - sessions_used / total_sessions (0.0-1.0)
- `total_invocations: int` - Total tool invocations across all sessions
- `tokens_consumed: int` - Total tokens consumed
- `roi_score: float` - invocations / tokens * 1000 (higher is better)
- `underutilized: bool` - Whether server is underutilized (utilization < 0.3)

**Usage**: Calculated by GlobalMCPAnalyzer

---

### MCPUsageRecommendation
**Purpose**: A recommendation about MCP server configuration.

**Fields**:
- `server_id: str` - MCP server ID
- `recommendation_type: str` - "remove_global" | "move_to_project" | "keep" | "promote_to_global"
- `reason: str` - Justification for recommendation
- `utilization_rate: float` - Current utilization rate
- `affected_projects: list[str]` - Projects that use this server

**Usage**: Generated by GlobalMCPAnalyzer, shown in rebuild output

---

### GlobalMCPReport
**Purpose**: Aggregated MCP analytics across all projects.

**Fields**:
- `total_servers: int` - Total MCP servers discovered
- `global_servers: int` - System-wide servers
- `project_servers: int` - Project-specific servers
- `servers: list[MCPServerInfo]` - All discovered servers
- `utilization: dict[str, MCPServerSessionUtilization]` - Per-server utilization
- `recommendations: list[MCPUsageRecommendation]` - Optimization suggestions
- `generated_at: datetime` - Report generation timestamp

**Usage**: Full report from GlobalMCPAnalyzer, summarized in rebuild output

---

## Context Optimization Models

### ContextAccessLog
**Purpose**: A single context section access event.

**Fields**:
- `timestamp: datetime` - When section was accessed
- `session_id: str` - Claude Code session ID
- `section_name: str` - Section identifier (e.g., "## Available Tools", "## Fish Shell Abbreviations")
- `access_type: str` - "load" | "reference" (loaded vs actually used)
- `file_path: Path` - Path to CLAUDE.md file
- `token_count: int` - Estimated tokens for this section

**Usage**: Logged by ContextOptimizer (future: requires Claude Code API integration)

**Storage**: `~/.claude/context-access.jsonl`

---

### SectionUsage
**Purpose**: Aggregated usage statistics for a CLAUDE.md section.

**Fields**:
- `section_name: str` - Section identifier
- `total_loads: int` - Times section was loaded
- `total_references: int` - Times section was actually referenced
- `reference_rate: float` - total_references / total_loads (0.0-1.0)
- `avg_token_count: int` - Average tokens per load
- `last_referenced: Optional[datetime]` - Most recent reference
- `noise_score: float` - 1.0 - reference_rate (higher = more noise)

**Usage**: Calculated by ContextOptimizer

---

### ContextOptimization
**Purpose**: A suggestion to optimize CLAUDE.md context.

**Fields**:
- `optimization_type: str` - "prune" | "reorder" | "summarize" | "extract_quick_ref"
- `section_name: str` - Affected section
- `reason: str` - Justification
- `estimated_token_savings: int` - Expected token reduction
- `risk_level: str` - "low" | "medium" | "high"

**Usage**: Generated by ContextOptimizer, shown to user for approval

---

## Workflow Detection Models

### SlashCommandLog
**Purpose**: A single slash command execution event.

**Fields**:
- `timestamp: datetime` - When command was executed
- `session_id: str` - Claude Code session ID
- `command_name: str` - Slash command name (e.g., "/commit", "/test")
- `success: bool` - Whether command succeeded
- `duration_seconds: float` - Execution time
- `project_root: Optional[Path]` - Project context

**Usage**: Logged by WorkflowDetector

**Storage**: `~/.claude/workflow-analytics.jsonl`

---

### WorkflowSequence
**Purpose**: A detected sequence of slash commands.

**Fields**:
- `commands: list[str]` - Slash command sequence (e.g., ["/test", "/commit", "/push"])
- `occurrences: int` - How many times this sequence was executed
- `completion_rate: float` - Fraction of sequences that completed successfully (0.0-1.0)
- `avg_duration_seconds: float` - Average time to complete full sequence
- `last_seen: datetime` - Most recent occurrence
- `projects: list[str]` - Projects where sequence was used

**Usage**: Detected by WorkflowDetector

---

### WorkflowSuggestion
**Purpose**: A suggestion to bundle slash commands into a workflow.

**Fields**:
- `sequence: WorkflowSequence` - The detected sequence
- `suggested_name: str` - Proposed workflow name (e.g., "/test-commit-push")
- `suggested_description: str` - What the workflow does
- `confidence: float` - Statistical confidence (0.0-1.0)

**Usage**: Presented to user by WorkflowDetector

---

## Instruction Effectiveness Models

### PolicyViolation
**Purpose**: A detected violation of a CLAUDE.md instruction.

**Fields**:
- `timestamp: datetime` - When violation occurred
- `session_id: str` - Claude Code session ID
- `policy_name: str` - Instruction that was violated (e.g., "Git Commit Policy")
- `violation_description: str` - What happened
- `policy_text: str` - Original instruction text
- `severity: str` - "low" | "medium" | "high"

**Usage**: Logged by InstructionTracker (requires Claude Code API integration)

**Storage**: `~/.claude/policy-violations.jsonl`

---

### InstructionEffectiveness
**Purpose**: Effectiveness metrics for a CLAUDE.md instruction.

**Fields**:
- `policy_name: str` - Instruction identifier
- `total_sessions: int` - Sessions where policy was applicable
- `compliant_sessions: int` - Sessions where policy was followed
- `effectiveness_score: float` - compliant_sessions / total_sessions (0.0-1.0)
- `violations: list[PolicyViolation]` - Recent violations
- `ambiguous: bool` - Whether policy is ambiguous (effectiveness < 0.7)

**Usage**: Calculated by InstructionTracker

---

### InstructionImprovement
**Purpose**: A suggestion to improve a CLAUDE.md instruction.

**Fields**:
- `policy_name: str` - Instruction to improve
- `current_text: str` - Current instruction text
- `suggested_text: str` - Improved instruction text
- `reason: str` - Why improvement is needed
- `effectiveness_score: float` - Current effectiveness

**Usage**: Generated by InstructionTracker, shown to user for approval

---

## Cross-Project Transfer Models

### ProjectArchetype
**Purpose**: Classification of a project by technology stack and patterns.

**Fields**:
- `archetype_type: str` - "python_pytest" | "typescript_vitest" | "rust_cargo" | "nixos_flake" | etc.
- `project_paths: list[Path]` - Projects matching this archetype
- `common_permissions: list[str]` - Permissions shared across all projects
- `common_tools: list[str]` - Tools shared across all projects
- `common_workflows: list[str]` - Slash command workflows shared across projects

**Usage**: Detected by ProjectArchetypeDetector

---

### CrossProjectPattern
**Purpose**: A pattern transferable between projects.

**Fields**:
- `pattern_type: str` - "permission" | "tool" | "workflow" | "instruction"
- `pattern_content: str` - Actual pattern (permission string, tool name, etc.)
- `source_projects: list[Path]` - Projects where pattern exists
- `archetype: str` - Archetype this pattern belongs to
- `confidence: float` - Strength of pattern (0.0-1.0)

**Usage**: Identified by ProjectArchetypeDetector

---

### TransferSuggestion
**Purpose**: A suggestion to transfer a pattern to a new project.

**Fields**:
- `target_project: Path` - Project to add pattern to
- `pattern: CrossProjectPattern` - Pattern to transfer
- `justification: str` - Why this pattern should be transferred
- `auto_approvable: bool` - Whether safe to auto-apply

**Usage**: Generated by ProjectArchetypeDetector for new projects

---

## Meta-Learning Models

### LearningMetrics
**Purpose**: Effectiveness metrics for the learning system itself.

**Fields**:
- `component: str` - Learning component name (e.g., "PermissionLearning", "MCPOptimization")
- `total_suggestions: int` - Total suggestions made
- `accepted_suggestions: int` - Suggestions user accepted
- `acceptance_rate: float` - accepted / total (0.0-1.0)
- `false_positives: int` - Suggestions user rejected
- `false_positive_rate: float` - false_positives / total (0.0-1.0)
- `last_updated: datetime` - Last metric update

**Usage**: Tracked by MetaLearner

**Storage**: `~/.claude/meta-learning.json`

---

### ThresholdAdjustment
**Purpose**: A recommended adjustment to learning system thresholds.

**Fields**:
- `component: str` - Learning component to adjust
- `parameter: str` - Parameter name (e.g., "confidence_threshold", "min_pattern_occurrences")
- `current_value: float` - Current parameter value
- `suggested_value: float` - Recommended new value
- `reason: str` - Justification for adjustment

**Usage**: Generated by MetaLearner based on acceptance rates

---

### LearningHealthReport
**Purpose**: Overall health report for the learning system.

**Fields**:
- `overall_health: str` - "healthy" | "needs_tuning" | "malfunctioning"
- `component_metrics: dict[str, LearningMetrics]` - Per-component metrics
- `threshold_adjustments: list[ThresholdAdjustment]` - Recommended adjustments
- `recommendations: list[str]` - High-level recommendations
- `generated_at: datetime` - Report timestamp

**Usage**: Full diagnostic from MetaLearner

---

### LearningReport
**Purpose**: Consolidated learning report from all components.

**Fields**:
- `permission_suggestions: list[PatternSuggestion]` - Permission patterns
- `mcp_recommendations: list[MCPUsageRecommendation]` - MCP optimizations
- `context_optimizations: list[ContextOptimization]` - Context improvements
- `workflow_suggestions: list[WorkflowSuggestion]` - Workflow bundles
- `instruction_improvements: list[InstructionImprovement]` - Instruction rewrites
- `transfer_suggestions: list[TransferSuggestion]` - Cross-project transfers
- `learning_health: LearningHealthReport` - Meta-learning health
- `generated_at: datetime` - Report timestamp

**Usage**: Master report from AdaptiveSystemEngine, shown during rebuild

---

## Source-Artifact Architecture Models

### ValidationResult
**Purpose**: Result of validating content (permissions, CLAUDE.md, etc.).

**Fields**:
- `valid: bool` - Whether content passed validation
- `errors: list[str]` - Fatal validation errors (FAIL)
- `warnings: list[str]` - Non-fatal issues (WARN)
- `info: list[str]` - Informational messages

**Usage**: Returned by PermissionValidator and ContentValidator

---

### SourceArtifactDeclaration
**Purpose**: Declaration of sources and artifacts for a generator.

**Fields**:
- `generator_name: str` - Generator class name
- `manual_sources: list[Path]` - User-editable source files (MUST NOT be written)
- `generated_artifacts: list[Path]` - Auto-generated files (CAN write, MUST have header)
- `declared_at: datetime` - When declaration was made

**Usage**: Defined in each generator's `MANUAL_SOURCES` and `GENERATED_ARTIFACTS` class attributes

**Validation Rules**:
1. `manual_sources` and `generated_artifacts` MUST NOT overlap
2. Generators MUST NOT call `write_artifact()` with paths in `manual_sources`
3. All files in `generated_artifacts` MUST have auto-generated headers

---

### GenerationHeader
**Purpose**: Metadata header added to auto-generated files.

**Fields**:
- `generated_at: datetime` - When file was generated
- `generator_name: str` - Generator class name
- `sources: list[Path]` - Source files used to generate this artifact
- `header_text: str` - Full HTML comment header

**Usage**: Embedded in generated CLAUDE.md files

**Format**:
```html
<!--
============================================================
  AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY

  Generated: 2025-10-17T12:00:00+00:00
  Generator: SystemGenerator
  Sources: ~/.claude/config.yaml, ~/.bashrc

  To modify, edit source files and regenerate.
============================================================
-->
```

---

## Usage Examples

### Permission Learning Flow

```python
from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.permission_pattern_detector import PermissionPatternDetector

# Log approval
tracker = ApprovalTracker()
tracker.log_approval(
    session_id="abc123",
    permission_pattern="Read(//home/user/project/tests/**)",
    project_root="/home/user/project"
)

# Detect patterns
detector = PermissionPatternDetector(tracker)
patterns = detector.detect_patterns()

for pattern in patterns:
    print(f"{pattern.pattern_type}: {pattern.confidence:.2f} confidence")
    print(f"  Suggested: {pattern.suggested_permission}")
```

### MCP Analytics Flow

```python
from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer

analyzer = GlobalMCPAnalyzer()
report = analyzer.analyze_all_projects()

print(f"Total servers: {report.total_servers}")
print(f"Global servers: {report.global_servers}")
print(f"Project servers: {report.project_servers}")

for rec in report.recommendations:
    print(f"{rec.server_id}: {rec.recommendation_type}")
    print(f"  Reason: {rec.reason}")
```

### Context Optimization Flow

```python
from claude_automation.analyzers.context_optimizer import ContextOptimizer

optimizer = ContextOptimizer()
optimizations = optimizer.analyze()

for opt in optimizations:
    print(f"{opt.optimization_type} - {opt.section_name}")
    print(f"  Reason: {opt.reason}")
    print(f"  Token savings: {opt.estimated_token_savings}")
```

---

## Schema Evolution

**Adding new fields**:
- Add with `Optional[...]` or default value to maintain backward compatibility
- Update this documentation

**Removing fields**:
- Mark as deprecated for 2 releases
- Remove only after migration path exists

**Breaking changes**:
- Bump major version in pyproject.toml
- Provide migration script

---

## Validation Rules

**All schemas** use Pydantic validation:
- Type checking automatic
- Custom validators via `@field_validator`
- See `claude_automation/validators/` for additional validation logic

**Common patterns**:
- Paths validated to exist when read
- Datetimes use timezone-aware format
- Confidence scores clamped to [0.0, 1.0]
- Token counts must be non-negative

---

*Last updated: 2025-10-17 (Phase 2 completion)*
