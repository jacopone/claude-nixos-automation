---
status: draft
created: 2025-10-20
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# Schema Domain Boundaries Contract

**Version**: 1.0
**Date**: 2025-10-19
**Status**: Authoritative Domain Definition

## Purpose

This contract defines the domain boundaries for the schema refactoring. It specifies:
1. Which Pydantic models belong in which domain module
2. Allowed dependencies between domains
3. Validation rules to prevent domain coupling

## Domain Definitions

### Domain 1: Core (`schemas/core.py`)

**Purpose**: Foundational system-level schemas used across all domains.

**Schemas** (8 models):
- `ToolCategory` - Enum for tool categorization
- `ProjectType` - Enum for project type detection
- `ToolInfo` - System tool metadata
- `FishAbbreviation` - Fish shell abbreviation config
- `GitStatus` - Git repository status
- `SystemConfig` - System-wide configuration
- `ProjectConfig` - Project-specific configuration
- `ParsingResult` - Generic parsing result wrapper

**Dependencies**: None (foundational layer)

**Allowed Imports**:
- ✅ Standard library (pathlib, datetime, enum, etc.)
- ✅ Pydantic (BaseModel, Field, validator, etc.)
- ❌ Other claude_automation.schemas domains
- ❌ claude_automation.analyzers
- ❌ claude_automation.generators

**Rationale**: Core types are used everywhere. No business logic, pure data structures.

---

### Domain 2: Permissions (`schemas/permissions.py`)

**Purpose**: Permission learning and approval tracking (Tier 1 learning).

**Schemas** (3 models):
- `PermissionApprovalEntry` - Log entry for a permission approval
- `PermissionPattern` - Detected approval pattern
- `PatternSuggestion` - Suggested auto-approval rule

**Dependencies**: `core` only

**Allowed Imports**:
- ✅ Standard library
- ✅ Pydantic
- ✅ `from claude_automation.schemas.core import ...`
- ❌ Other schemas domains (mcp, learning, context, workflows, validation)

**Rationale**: Tightly coupled permission approval tracking. Tier 1 learning focused on reducing approval requests.

---

### Domain 3: MCP (`schemas/mcp.py`)

**Purpose**: MCP (Model Context Protocol) server management and analytics.

**Schemas** (9 models):
- `MCPServerType` - Enum for server types
- `MCPServerStatus` - Enum for server status
- `MCPServerInfo` - Server metadata
- `MCPToolUsage` - Tool usage tracking
- `MCPSessionStats` - Session-level statistics
- `MCPServerSessionUtilization` - Server utilization metrics
- `MCPUsageRecommendation` - Optimization suggestions
- `GlobalMCPReport` - System-wide MCP report
- `MCPUsageAnalyticsConfig` - Analytics configuration

**Dependencies**: `core` only

**Allowed Imports**:
- ✅ Standard library
- ✅ Pydantic
- ✅ `from claude_automation.schemas.core import ...`
- ❌ Other schemas domains

**Rationale**: Distinct external integration domain. MCP is Claude-specific protocol for tool usage.

---

### Domain 4: Learning (`schemas/learning.py`)

**Purpose**: Cross-project and meta-learning (Tier 3 learning).

**Schemas** (6 models):
- `LearningMetrics` - Learning effectiveness metrics
- `ThresholdAdjustment` - Meta-learning threshold tuning
- `LearningHealthReport` - System health report
- `CrossProjectPattern` - Patterns detected across projects
- `TransferSuggestion` - Cross-project knowledge transfer
- `ProjectArchetype` - Project type classification

**Dependencies**: `core` only

**Allowed Imports**:
- ✅ Standard library
- ✅ Pydantic
- ✅ `from claude_automation.schemas.core import ...`
- ❌ Other schemas domains

**Rationale**: Tier 3 learning operates at system level, distinct from Tier 1/2. Meta-learning adjusts other learning components.

---

### Domain 5: Context (`schemas/context.py`)

**Purpose**: CLAUDE.md context optimization and usage tracking (Tier 1 learning).

**Schemas** (3 models):
- `ContextAccessLog` - Section access logging
- `SectionUsage` - Usage statistics per section
- `ContextOptimization` - Suggested optimizations

**Dependencies**: `core` only

**Allowed Imports**:
- ✅ Standard library
- ✅ Pydantic
- ✅ `from claude_automation.schemas.core import ...`
- ❌ Other schemas domains

**Rationale**: Tier 1 learning focused on CLAUDE.md file optimization. Distinct from workflow/permission learning.

---

### Domain 6: Workflows (`schemas/workflows.py`)

**Purpose**: Workflow and slash command detection (Tier 2 learning).

**Schemas** (9 models):
- `SlashCommandLog` - Slash command execution log
- `WorkflowSequence` - Detected command sequence
- `WorkflowSuggestion` - Suggested slash command
- `CommandCategory` - Enum for command types
- `SlashCommand` - Slash command definition
- `SlashCommandsConfig` - Slash commands configuration
- `CommandUsage` - Command usage statistics
- `UsagePattern` - Usage pattern detection
- `UsageAnalyticsConfig` - Analytics configuration

**Dependencies**: `core` only

**Allowed Imports**:
- ✅ Standard library
- ✅ Pydantic
- ✅ `from claude_automation.schemas.core import ...`
- ❌ Other schemas domains

**Rationale**: Tier 2 learning, command-oriented. Distinct from Tier 1 (permissions/context) and Tier 3 (cross-project).

---

### Domain 7: Validation (`schemas/validation.py`)

**Purpose**: Generation and validation result schemas (infrastructure).

**Schemas** (4 models):
- `ValidationResult` - Validation outcome
- `SourceArtifactDeclaration` - Source/artifact declaration
- `GenerationHeader` - Auto-generated file header
- `GenerationResult` - Generation outcome

**Dependencies**: `core` only

**Allowed Imports**:
- ✅ Standard library
- ✅ Pydantic
- ✅ `from claude_automation.schemas.core import ...`
- ❌ Other schemas domains

**Rationale**: Infrastructure schemas used by generators and validators. Not domain-specific.

---

### Domain 8: Package (`schemas/__init__.py`)

**Purpose**: Backward compatibility re-exports.

**Schemas**: All 42+ schemas from above domains

**Dependencies**: All 7 domain modules

**Allowed Imports**:
- ✅ `from .core import *`
- ✅ `from .permissions import *`
- ✅ `from .mcp import *`
- ✅ `from .learning import *`
- ✅ `from .context import *`
- ✅ `from .workflows import *`
- ✅ `from .validation import *`

**Rationale**: Maintains 100% backward compatibility. External code continues using `from claude_automation.schemas import Model`.

---

## Dependency Rules

### Rule 1: Core is Foundation
**ALL domain modules MAY import from `core.py`.**

Rationale: Core types (ToolCategory, ProjectType, etc.) are foundational and reused across domains.

### Rule 2: No Cross-Domain Imports
**Domain modules MUST NOT import from other domain modules (except core).**

Examples:
- ❌ `permissions.py` importing from `mcp.py`
- ❌ `learning.py` importing from `workflows.py`
- ✅ `permissions.py` importing from `core.py`

Rationale: Prevents tight coupling. Each domain should be independently testable.

### Rule 3: Analyzers/Generators MAY Import Multiple Domains
**Analyzers and generators MAY import from multiple domain modules.**

Examples:
- ✅ `adaptive_system_engine.py` importing from `permissions`, `mcp`, `learning`, `workflows`, `context`
- ✅ `permission_pattern_detector.py` importing from `permissions` and `validation`

Rationale: Analyzers/generators are cross-cutting concerns that orchestrate multiple domains.

### Rule 4: No Upward Imports
**Domain schemas MUST NOT import from analyzers, generators, or validators.**

Examples:
- ❌ `permissions.py` importing from `analyzers.permission_pattern_detector`
- ❌ `validation.py` importing from `generators.base_generator`

Rationale: Maintains unidirectional data flow (Sources → Analyzers → Generators → Artifacts).

---

## Validation Checklist

Use this checklist when creating or modifying domain modules:

### File Structure Validation
- [ ] Domain module exists at correct path (`claude_automation/schemas/{domain}.py`)
- [ ] Domain module is <300 lines
- [ ] Domain module contains only schemas (no business logic)
- [ ] __init__.py re-exports all schemas from this domain

### Import Validation
- [ ] Only imports from: standard library, pydantic, `schemas.core`
- [ ] Does NOT import from other schemas domains
- [ ] Does NOT import from analyzers/generators/validators

### Schema Validation
- [ ] All schemas are Pydantic BaseModel subclasses
- [ ] All fields have `Field(description="...")`
- [ ] All validators preserved from original schemas.py
- [ ] No functionality changes (behavior identical to original)

### Test Validation
- [ ] Backward compatibility test passes: `from claude_automation.schemas import {Model}`
- [ ] New import path works: `from claude_automation.schemas.{domain} import {Model}`
- [ ] No circular import errors when running pytest
- [ ] All existing tests pass without modification

---

## Circular Import Detection

### Automated Detection
Run this command before committing:

```bash
# AST-based circular import detector
python scripts/detect_circular_imports.py claude_automation/schemas/

# mypy also detects circular imports
mypy claude_automation/schemas/ --no-incremental
```

### Manual Detection (Code Review)
When reviewing schema changes:
1. Check import statements at top of file
2. Verify imports only reference `core.py` (not other domains)
3. Ensure no `from claude_automation.analyzers import ...`
4. Confirm no conditional imports inside functions

### Fail-Fast Behavior (from clarification #2)
If circular import detected:
- ✅ Halt the refactoring immediately
- ✅ Report clear error identifying the cycle path
- ✅ Require manual resolution before continuing
- ❌ Do NOT auto-resolve (prevents masking design issues)

Example error message:
```
CircularImportError: Circular import detected

Cycle path: permissions -> mcp -> permissions

This violates domain boundary rules. The 'permissions' domain cannot import
from the 'mcp' domain. Refactor to remove the dependency or move shared
types to the 'core' domain.

Files involved:
  - claude_automation/schemas/permissions.py (line 15)
  - claude_automation/schemas/mcp.py (line 42)
```

---

## Summary

**7 domain modules** + **1 package init** = **8 total files**

**42+ Pydantic models** organized by domain

**Dependency tree**:
```
core (8 models)
 ├── permissions (3 models) → depends on core
 ├── mcp (9 models) → depends on core
 ├── learning (6 models) → depends on core
 ├── context (3 models) → depends on core
 ├── workflows (9 models) → depends on core
 └── validation (4 models) → depends on core

__init__ → re-exports all 42+ models from above
```

**Validation**: Each domain <300 lines, no cross-domain imports, 100% backward compatibility.

