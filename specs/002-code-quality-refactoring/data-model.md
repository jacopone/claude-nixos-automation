# Data Model: Code Quality Refactoring

**Phase**: 1 (Design & Contracts)
**Date**: 2025-10-19
**Status**: Complete

## Overview

This document defines the data model for the refactoring implementation. Since this is a code refactoring (not new feature development), the data model focuses on the **refactored structure** rather than new entities.

---

## 1. Schema Domain Organization

### Entity: SchemaDomain

Represents a logical grouping of related Pydantic models.

**Attributes**:
- `name`: str - Domain name (e.g., "permissions", "mcp", "learning")
- `module_path`: str - Python module path (e.g., "claude_automation.schemas.permissions")
- `file_path`: Path - Filesystem location (e.g., "claude_automation/schemas/permissions.py")
- `schemas`: list[str] - Names of Pydantic models in this domain
- `line_count_target`: int - Target LOC (<300 per domain)
- `dependencies`: list[str] - Other domains this depends on (should only be ["core"])

**Validation Rules**:
- `name` must match one of 8 defined domains: core, permissions, mcp, learning, context, workflows, validation
- `schemas` list must contain at least 1 model
- `dependencies` may only reference "core" (prevents cross-domain coupling)
- `line_count_target` must be <= 300

**State Transitions**: N/A (static structure)

**Example**:
```python
permissions_domain = SchemaDomain(
    name="permissions",
    module_path="claude_automation.schemas.permissions",
    file_path=Path("claude_automation/schemas/permissions.py"),
    schemas=["PermissionApprovalEntry", "PermissionPattern", "PatternSuggestion"],
    line_count_target=100,
    dependencies=["core"]  # May import from core.py only
)
```

---

## 2. BaseAnalyzer Interface

### Entity: BaseAnalyzer (Abstract Base Class)

Standardized interface for all analyzer components.

**Attributes** (Constructor Parameters):
- `storage_dir`: Path | None - Directory for analytics storage (default: ~/.claude)
- `days`: int - Number of days of history to analyze (default: 30)

**Methods** (Public API):
- `analyze() -> Any` - **Abstract method** subclasses must implement
- `_validate_parameters() -> None` - Common parameter validation

**Validation Rules**:
- `days` must be >= 1
- `storage_dir` must be created if it doesn't exist (mkdir with parents=True)
- Subclasses must implement `analyze()` (enforced by ABC)

**Relationships**:
- **Inherits from**: `abc.ABC`
- **Inherited by**: PermissionPatternDetector, GlobalMCPAnalyzer, ContextOptimizer, WorkflowDetector, InstructionTracker, ProjectArchetypeDetector, MetaLearner (all Tier 3 analyzers)

**Example**:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class BaseAnalyzer(ABC):
    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        self.storage_dir = storage_dir or Path.home() / ".claude"
        self.days = days
        self._validate_parameters()

    def _validate_parameters(self):
        if self.days < 1:
            raise ValueError(f"days must be >= 1, got {self.days}")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def analyze(self) -> Any:
        """Perform analysis. Subclasses MUST implement."""
        pass
```

---

## 3. InteractiveApprovalUI Component

### Entity: InteractiveApprovalUI

Handles interactive user approval workflow (extracted from AdaptiveSystemEngine).

**Attributes**: None (stateless)

**Methods** (Public API):
- `present_report(report: LearningReport) -> None` - Display learning report to user
- `collect_approvals(suggestions: list[Suggestion]) -> list[Suggestion]` - Collect user approvals

**Relationships**:
- **Used by**: AdaptiveSystemEngine (via dependency injection)
- **Depends on**: LearningReport schema (from learning.py), Suggestion types (from permissions/mcp/context/workflows domains)

**Behavior**:
- Exact replication of `_present_report()` and `_collect_approvals()` logic from engine
- Preserves all prompts, input handling, and approval workflow
- No state stored between calls (stateless component)

**Example Usage**:
```python
# In AdaptiveSystemEngine
class AdaptiveSystemEngine:
    def __init__(self, interactive: bool = True, ui: InteractiveApprovalUI | None = None):
        self.interactive = interactive
        self.ui = ui or InteractiveApprovalUI()

    def run_full_learning_cycle(self) -> LearningReport:
        # ... analysis logic ...
        if self.interactive:
            self.ui.present_report(report)
            approved_suggestions = self.ui.collect_approvals(report.suggestions)
        # ... apply approved suggestions ...
```

---

## 4. Import Migration Tracker

### Entity: ImportMigrationEntry

Tracks progress of import statement updates during refactoring.

**Attributes**:
- `file_path`: Path - File being updated
- `old_import`: str - Original import statement (e.g., "from claude_automation.schemas import PermissionPattern")
- `new_import`: str - New import statement (e.g., "from claude_automation.schemas.permissions import PermissionPattern")
- `status`: str - Migration status: "pending" | "reviewed" | "applied" | "validated"
- `requires_manual_review`: bool - Flagged for manual inspection (complex dynamic imports)

**Validation Rules**:
- `old_import` must start with "from claude_automation.schemas import" or "import claude_automation.schemas"
- `new_import` must reference one of the 8 domain modules
- `status` must be one of 4 valid states

**State Transitions**:
```
pending → reviewed → applied → validated
         ↓ (if complex)
         requires_manual_review
```

**Example**:
```python
migration_entry = ImportMigrationEntry(
    file_path=Path("claude_automation/analyzers/permission_pattern_detector.py"),
    old_import="from claude_automation.schemas import PermissionPattern",
    new_import="from claude_automation.schemas.permissions import PermissionPattern",
    status="reviewed",
    requires_manual_review=False
)
```

---

## 5. Circular Import Detection

### Entity: CircularImportError (Exception)

Raised when circular import dependency detected during schema split.

**Attributes**:
- `cycle_path`: list[str] - Module names forming the circular dependency
- `message`: str - Human-readable error description

**Validation Rules**:
- `cycle_path` must contain at least 2 modules
- First and last elements of `cycle_path` must be identical (forming cycle)

**Example**:
```python
class CircularImportError(Exception):
    def __init__(self, cycle_path: list[str]):
        self.cycle_path = cycle_path
        self.message = (
            f"Circular import detected: {' -> '.join(cycle_path)}\n\n"
            f"This violates domain boundary rules. Schemas in {cycle_path[0]} "
            f"cannot import from {cycle_path[1]}. Refactor to remove dependency."
        )
        super().__init__(self.message)

# Usage example:
if circular_dependency_found:
    raise CircularImportError(["permissions", "mcp", "permissions"])
    # Output: "Circular import detected: permissions -> mcp -> permissions"
```

---

## Domain-Specific Schema Mappings

### Mapping: Schema → Domain

This mapping defines which Pydantic models belong in which domain module (from FR-004).

| Domain | Module | Schemas (Count) | Dependencies |
|--------|--------|-----------------|--------------|
| **core** | `schemas/core.py` | ToolCategory, ProjectType, ToolInfo, FishAbbreviation, GitStatus, SystemConfig, ProjectConfig, ParsingResult (8) | None |
| **permissions** | `schemas/permissions.py` | PermissionApprovalEntry, PermissionPattern, PatternSuggestion (3) | core |
| **mcp** | `schemas/mcp.py` | MCPServerType, MCPServerStatus, MCPServerInfo, MCPToolUsage, MCPSessionStats, MCPServerSessionUtilization, MCPUsageRecommendation, GlobalMCPReport, MCPUsageAnalyticsConfig (9) | core |
| **learning** | `schemas/learning.py` | LearningMetrics, ThresholdAdjustment, LearningHealthReport, CrossProjectPattern, TransferSuggestion, ProjectArchetype (6) | core |
| **context** | `schemas/context.py` | ContextAccessLog, SectionUsage, ContextOptimization (3) | core |
| **workflows** | `schemas/workflows.py` | SlashCommandLog, WorkflowSequence, WorkflowSuggestion, CommandCategory, SlashCommand, SlashCommandsConfig, CommandUsage, UsagePattern, UsageAnalyticsConfig (9) | core |
| **validation** | `schemas/validation.py` | ValidationResult, SourceArtifactDeclaration, GenerationHeader, GenerationResult (4) | core |
| **__init__** | `schemas/__init__.py` | Re-exports all 42 schemas from above domains | All domains |

**Total**: 42+ Pydantic models organized across 7 domain modules + 1 init module

**Validation**: Each domain file must be <300 lines (target: 100-200 lines each)

---

## Refactoring Impact Analysis

### Files to Create:
1. `claude_automation/schemas/__init__.py` (NEW)
2. `claude_automation/schemas/core.py` (NEW)
3. `claude_automation/schemas/permissions.py` (NEW)
4. `claude_automation/schemas/mcp.py` (NEW)
5. `claude_automation/schemas/learning.py` (NEW)
6. `claude_automation/schemas/context.py` (NEW)
7. `claude_automation/schemas/workflows.py` (NEW)
8. `claude_automation/schemas/validation.py` (NEW)
9. `claude_automation/analyzers/base_analyzer.py` (NEW)
10. `claude_automation/core/interactive_ui.py` (NEW)
11. `tests/unit/test_base_analyzer.py` (NEW)
12. `tests/integration/test_schema_imports.py` (NEW)

### Files to Update (Imports Only):
- ~15 analyzer files (inherit from BaseAnalyzer, update imports)
- ~10 generator files (update imports)
- ~5 validator files (update imports)
- ~30 test files (update imports, validate backward compatibility)

### Files to Remove (After Migration):
- `claude_automation/schemas.py` (REMOVE after validation complete)

---

## Summary

This data model defines:
1. **8 schema domains** with clear boundaries and dependencies
2. **BaseAnalyzer interface** standardizing all Tier 3 analyzers
3. **InteractiveApprovalUI component** extracted from engine
4. **Import migration tracking** for semi-automated updates
5. **Circular import detection** with fail-fast error handling

**Total Refactoring Scope**:
- 12 new files
- ~60 files updated
- 1 file removed
- 42+ schemas reorganized
- 24 tests fixed
- 100% backward compatibility maintained

