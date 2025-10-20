---
status: draft
created: 2025-10-20
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# Quickstart: Code Quality Refactoring Implementation

**Target Audience**: Developer implementing the refactoring
**Time to Complete**: 4-6 hours (estimated)
**Prerequisites**: Python 3.13, pytest, familiarity with Pydantic and Python modules

## Overview

This guide walks you through implementing the code quality refactoring in priority order:
1. **P1**: Schema split (1,455 lines → 8 modules)
2. **P1**: API alignment (24 failing tests → 100% pass rate)
3. **P2**: UI extraction (608-line engine → <500 lines)

## Before You Start

### Verify Environment

```bash
# Confirm Python version
python --version  # Should be 3.13+

# Confirm tests run
pytest tests/ -v  # Should show 479 tests (215 passing, 24 failing)

# Confirm schemas.py exists
wc -l claude_automation/schemas.py  # Should be 1455 lines
```

### Create Feature Branch

```bash
# Branch should already exist from /speckit.specify
git branch  # Confirm on 002-code-quality-refactoring

# If not, create it:
git checkout -b 002-code-quality-refactoring
```

---

## Phase 1: Schema Split (P1) - 2 hours

### Step 1.1: Create Schema Domain Modules (30 min)

```bash
# Create schemas/ subdirectory
mkdir -p claude_automation/schemas

# Create 8 domain module files
touch claude_automation/schemas/__init__.py
touch claude_automation/schemas/core.py
touch claude_automation/schemas/permissions.py
touch claude_automation/schemas/mcp.py
touch claude_automation/schemas/learning.py
touch claude_automation/schemas/context.py
touch claude_automation/schemas/workflows.py
touch claude_automation/schemas/validation.py
```

### Step 1.2: Copy Schemas to Domain Modules (60 min)

**Use the domain mapping from contracts/schema-domains.md:**

```bash
# Reference the current schemas.py
head -100 claude_automation/schemas.py  # Identify imports block

# For each domain, copy relevant schemas:
# 1. Copy imports (datetime, Field, BaseModel, etc.) to each domain file
# 2. Copy schema classes based on contract mapping
# 3. Preserve ALL validators, Field descriptions, @root_validator decorators
```

**Example for permissions.py**:

```python
# claude_automation/schemas/permissions.py
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Copy PermissionApprovalEntry from schemas.py (lines X-Y)
class PermissionApprovalEntry(BaseModel):
    """Log entry for a permission approval."""
    timestamp: datetime = Field(default_factory=datetime.now)
    permission: str = Field(..., description="Approved permission string")

    @validator("permission")
    def validate_permission(cls, v):
        if "\n" in v or "<<" in v:
            raise ValueError("Permission cannot contain newlines/heredocs")
        return v.strip()

# Copy PermissionPattern from schemas.py (lines A-B)
# Copy PatternSuggestion from schemas.py (lines C-D)
```

**Repeat for all 7 domain modules** (core, permissions, mcp, learning, context, workflows, validation).

### Step 1.3: Create __init__.py Re-exports (15 min)

```python
# claude_automation/schemas/__init__.py
"""Schema re-exports for backward compatibility.

This module preserves 100% backward compatibility by re-exporting all schemas
from domain-specific modules. External code continues to work without changes:

    from claude_automation.schemas import PermissionPattern  # Still works

New code can use domain-specific imports for clarity:

    from claude_automation.schemas.permissions import PermissionPattern  # Clearer
"""

# Import and re-export from core
from .core import (
    ToolCategory,
    ProjectType,
    ToolInfo,
    FishAbbreviation,
    GitStatus,
    SystemConfig,
    ProjectConfig,
    ParsingResult,
)

# Import and re-export from permissions
from .permissions import (
    PermissionApprovalEntry,
    PermissionPattern,
    PatternSuggestion,
)

# Import and re-export from mcp
from .mcp import (
    MCPServerType,
    MCPServerStatus,
    MCPServerInfo,
    MCPToolUsage,
    MCPSessionStats,
    MCPServerSessionUtilization,
    MCPUsageRecommendation,
    GlobalMCPReport,
    MCPUsageAnalyticsConfig,
)

# ... repeat for learning, context, workflows, validation
```

### Step 1.4: Validate Schema Split (15 min)

```bash
# Test imports work
python3 -c "from claude_automation.schemas import PermissionPattern; print('✅ Old import works')"
python3 -c "from claude_automation.schemas.permissions import PermissionPattern; print('✅ New import works')"

# Run schema tests
pytest tests/test_schemas.py -v  # Should pass

# Check for circular imports
mypy claude_automation/schemas/ --no-incremental  # Should pass
```

**If circular import detected**: STOP. Review contracts/schema-domains.md and remove the cross-domain import.

---

## Phase 2: API Alignment (P1) - 1.5 hours

### Step 2.1: Create BaseAnalyzer Abstract Class (30 min)

```python
# claude_automation/analyzers/base_analyzer.py
"""Base class for all analyzer components.

See contracts/base-analyzer.py for the complete interface contract.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzer components."""

    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        """Initialize analyzer with standard parameters.

        Args:
            storage_dir: Directory for analytics storage (default: ~/.claude)
            days: Number of days of history to analyze (default: 30)
        """
        self.storage_dir = storage_dir or Path.home() / ".claude"
        self.days = days
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate constructor parameters."""
        if self.days < 1:
            raise ValueError(f"days must be >= 1, got {self.days}")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def analyze(self) -> Any:
        """Perform analysis. Subclasses MUST implement."""
        pass
```

### Step 2.2: Update Tier 3 Analyzers (45 min)

**For each Tier 3 analyzer, update constructor to match BaseAnalyzer:**

```python
# Example: claude_automation/analyzers/permission_pattern_detector.py

# BEFORE:
class PermissionPatternDetector:
    def __init__(self, history_file: Path):
        self.history_file = history_file

# AFTER:
from claude_automation.analyzers.base_analyzer import BaseAnalyzer

class PermissionPatternDetector(BaseAnalyzer):
    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        super().__init__(storage_dir, days)
        self.history_file = self.storage_dir / "approval-history.jsonl"

    def analyze(self) -> list[PermissionPattern]:
        # Existing logic unchanged
        ...
```

**Update these analyzers**:
1. `permission_pattern_detector.py` ✅
2. `global_mcp_analyzer.py` ✅
3. `context_optimizer.py` ✅
4. `workflow_detector.py` ✅
5. `instruction_tracker.py` ✅
6. `project_archetype_detector.py` ✅
7. `meta_learner.py` ✅

### Step 2.3: Validate API Alignment (15 min)

```bash
# Run failing tests - should now pass
pytest tests/unit/test_permission_patterns.py -v  # Should pass
pytest tests/unit/test_approval_tracker.py -v  # Should pass
pytest tests/integration/test_learning_cycle.py -v  # Should pass
pytest tests/contract/test_analyzer_contracts.py -v  # Should pass

# Check test pass rate
pytest tests/ -v --tb=no | tail -20  # Should be 239/280 (86%+)
```

---

## Phase 3: UI Extraction (P2) - 1 hour

### Step 3.1: Create InteractiveApprovalUI Class (30 min)

```python
# claude_automation/core/interactive_ui.py
"""Interactive user approval workflow for learning suggestions."""

from claude_automation.schemas.learning import LearningReport
# Import other schemas as needed


class InteractiveApprovalUI:
    """Handles interactive user approval for learning suggestions.

    Extracted from AdaptiveSystemEngine to improve separation of concerns
    and testability. Preserves exact user-facing behavior.
    """

    def present_report(self, report: LearningReport) -> None:
        """Display learning report to user.

        Extracted from AdaptiveSystemEngine._present_report()
        """
        # Copy exact logic from engine._present_report() method
        print("\n" + "="*80)
        print("LEARNING CYCLE REPORT")
        print("="*80)
        # ... rest of presentation logic

    def collect_approvals(self, suggestions: list) -> list:
        """Collect user approvals for suggestions.

        Extracted from AdaptiveSystemEngine._collect_approvals()
        """
        # Copy exact logic from engine._collect_approvals() method
        approved = []
        for suggestion in suggestions:
            response = input(f"Approve {suggestion}? (y/n): ")
            if response.lower() == 'y':
                approved.append(suggestion)
        return approved
```

### Step 3.2: Update AdaptiveSystemEngine (20 min)

```python
# claude_automation/core/adaptive_system_engine.py

# Add import at top
from claude_automation.core.interactive_ui import InteractiveApprovalUI

class AdaptiveSystemEngine:
    def __init__(self, interactive: bool = True, ui: InteractiveApprovalUI | None = None):
        self.interactive = interactive
        self.ui = ui or InteractiveApprovalUI()  # Dependency injection
        # ... existing initialization

    def run_full_learning_cycle(self) -> LearningReport:
        # ... existing analysis logic ...

        # REPLACE:
        # if self.interactive:
        #     self._present_report(report)
        #     approved = self._collect_approvals(report.suggestions)

        # WITH:
        if self.interactive:
            self.ui.present_report(report)
            approved = self.ui.collect_approvals(report.suggestions)

        # ... rest of method unchanged

    # REMOVE these methods (moved to InteractiveApprovalUI):
    # def _present_report(self, report): ...
    # def _collect_approvals(self, suggestions): ...
```

### Step 3.3: Validate UI Extraction (10 min)

```bash
# Check engine file size
wc -l claude_automation/core/adaptive_system_engine.py  # Should be <500 lines

# Run integration tests
pytest tests/integration/test_learning_cycle.py -v  # Should pass

# Manual smoke test
python3 -c "
from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine
engine = AdaptiveSystemEngine(interactive=False)
print('✅ Engine instantiates without errors')
"
```

---

## Phase 4: Import Migration (Semi-Automated)

### Step 4.1: Discover Import Statements (10 min)

```bash
# Find all files importing from schemas
rg "from claude_automation.schemas import" -l > /tmp/files_to_update.txt

# Count files to update
wc -l /tmp/files_to_update.txt  # Should be ~60 files
```

### Step 4.2: Update Internal Imports (30 min)

**For internal code (analyzers, generators, validators), use domain-specific imports:**

```python
# BEFORE:
from claude_automation.schemas import (
    PermissionPattern,
    MCPServerInfo,
    ValidationResult
)

# AFTER:
from claude_automation.schemas.permissions import PermissionPattern
from claude_automation.schemas.mcp import MCPServerInfo
from claude_automation.schemas.validation import ValidationResult
```

**Use tool-assisted discovery**:
```bash
# For each file in /tmp/files_to_update.txt
for file in $(cat /tmp/files_to_update.txt); do
    echo "Reviewing: $file"
    # Manual review: identify which schemas are imported
    # Update to domain-specific imports
    # Run tests after each file
done
```

### Step 4.3: Update Test Imports (15 min)

**Test files can use backward-compatible imports** (no change needed):

```python
# tests/unit/test_permission_patterns.py
from claude_automation.schemas import PermissionPattern  # Still works!
```

### Step 4.4: Validate Imports (15 min)

```bash
# Create import validation test
# tests/integration/test_schema_imports.py

def test_backward_compatibility():
    """All old-style imports still work."""
    from claude_automation.schemas import (
        PermissionPattern,
        MCPServerInfo,
        ValidationResult,
        # ... all 42+ models
    )
    assert PermissionPattern is not None

def test_new_domain_imports():
    """New domain-specific imports work."""
    from claude_automation.schemas.permissions import PermissionPattern
    from claude_automation.schemas.mcp import MCPServerInfo
    assert PermissionPattern is not None
```

```bash
# Run validation
pytest tests/integration/test_schema_imports.py -v  # Should pass
```

---

## Phase 5: Final Validation & Cleanup

### Step 5.1: Run Full Test Suite (10 min)

```bash
# Run all tests
pytest tests/ -v

# Verify test pass rate
pytest tests/ --tb=no | grep -E "passed|failed"
# Should show: 239+ passed (86%+ pass rate)
```

### Step 5.2: Remove Old schemas.py (5 min)

```bash
# ONLY after all tests pass
git mv claude_automation/schemas.py claude_automation/schemas.py.backup

# Run tests again to confirm
pytest tests/ -v  # Should still pass

# If pass, delete backup
rm claude_automation/schemas.py.backup
```

### Step 5.3: Verify Success Criteria (5 min)

Check each success criterion from spec.md:

- [ ] **SC-001**: Navigate to any schema in <10 seconds
  - Test: Open `claude_automation/schemas/permissions.py` in editor

- [ ] **SC-002**: Test pass rate >= 86% (239/280)
  - Run: `pytest tests/ --tb=no | grep passed`

- [ ] **SC-003**: Zero import errors
  - Run: `python -c "from claude_automation.schemas import *"`

- [ ] **SC-004**: 100% backward compatibility
  - Run: `pytest tests/integration/test_schema_imports.py`

- [ ] **SC-005**: Reduced merge conflicts (measure over time)

- [ ] **SC-006**: Engine <500 lines
  - Run: `wc -l claude_automation/core/adaptive_system_engine.py`

- [ ] **SC-007**: New analyzers align in <5 min
  - Manual verification: Create test analyzer inheriting BaseAnalyzer

---

## Troubleshooting

### Circular Import Error

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Solution**:
1. Run: `mypy claude_automation/schemas/ --no-incremental`
2. Identify the cycle (e.g., `permissions -> mcp -> permissions`)
3. Move shared type to `core.py`
4. Update imports to reference `core.py`

### Test Failures After Schema Split

**Symptom**: Tests import schemas but get `AttributeError`

**Solution**:
1. Verify `__init__.py` re-exports all schemas
2. Check for typos in import statements
3. Run: `python -c "from claude_automation.schemas import ModelName; print(ModelName)"`

### Engine Still >500 Lines

**Symptom**: `wc -l` shows engine >500 lines after UI extraction

**Solution**:
1. Verify `_present_report()` and `_collect_approvals()` methods removed
2. Check for lingering commented-out code
3. Remove debug print statements
4. Run: `ruff format claude_automation/core/adaptive_system_engine.py` (may remove extra whitespace)

---

## Commit Strategy

```bash
# Commit after each phase
git add claude_automation/schemas/
git commit -m "refactor: split schemas.py into 8 domain modules (P1)"

git add claude_automation/analyzers/base_analyzer.py
git add claude_automation/analyzers/*.py
git commit -m "refactor: create BaseAnalyzer and align API (P1)"

git add claude_automation/core/interactive_ui.py
git add claude_automation/core/adaptive_system_engine.py
git commit -m "refactor: extract UI logic from engine (P2)"

git add claude_automation/ tests/
git commit -m "refactor: update imports to use domain modules"

git rm claude_automation/schemas.py
git commit -m "refactor: remove old monolithic schemas.py"
```

---

## Next Steps

After completing this refactoring:

1. **Run `/speckit.tasks`** to generate the task breakdown (if using spec-kit workflow)
2. **Create PR** with branch `002-code-quality-refactoring`
3. **Document lessons learned** for future refactorings
4. **Address remaining code quality issues** from the analysis (pytest.approx, config files, etc.)

---

## Estimated Time Breakdown

| Phase | Task | Time |
|-------|------|------|
| 1.1 | Create schema modules | 30 min |
| 1.2 | Copy schemas to domains | 60 min |
| 1.3 | Create __init__.py | 15 min |
| 1.4 | Validate schema split | 15 min |
| 2.1 | Create BaseAnalyzer | 30 min |
| 2.2 | Update Tier 3 analyzers | 45 min |
| 2.3 | Validate API alignment | 15 min |
| 3.1 | Create InteractiveApprovalUI | 30 min |
| 3.2 | Update engine | 20 min |
| 3.3 | Validate UI extraction | 10 min |
| 4.1 | Discover imports | 10 min |
| 4.2 | Update internal imports | 30 min |
| 4.3 | Update test imports | 15 min |
| 4.4 | Validate imports | 15 min |
| 5.1 | Run full test suite | 10 min |
| 5.2 | Remove old schemas.py | 5 min |
| 5.3 | Verify success criteria | 5 min |
| **TOTAL** | | **5 hours 15 min** |

**Buffer for troubleshooting**: +45 min
**Total estimated time**: 6 hours

