# Research: Code Quality Refactoring

**Phase**: 0 (Outline & Research)
**Date**: 2025-10-19
**Status**: Complete

## Research Questions

This document resolves technical unknowns and documents best practices for the refactoring implementation.

---

## 1. Python Module Refactoring Best Practices

### Decision: Use Package-Level __init__.py for Backward Compatibility

**Rationale**:
- Python's import system supports transparent re-exports via `__init__.py`
- Allows gradual migration: external code continues using `from claude_automation.schemas import Model`
- Internal code can migrate to `from claude_automation.schemas.domain import Model` for clarity
- Standard pattern used by major libraries (Django, SQLAlchemy, Pydantic itself)

**Implementation Pattern**:
```python
# claude_automation/schemas/__init__.py
from .core import (
    ToolCategory,
    ProjectType,
    ToolInfo,
    # ... all core exports
)
from .permissions import (
    PermissionApprovalEntry,
    PermissionPattern,
    # ... all permission exports
)
# ... repeat for all domains
```

**Alternatives Considered**:
- **Breaking change with migration script**: Rejected - violates 100% backward compatibility constraint
- **Type stubs (.pyi) only**: Rejected - doesn't solve actual code organization problem
- **Monolithic file with internal organization**: Rejected - doesn't address merge conflicts or navigation time

**References**:
- PEP 420 (Implicit Namespace Packages)
- Python Packaging User Guide: https://packaging.python.org/guides/packaging-namespace-packages/

---

## 2. Abstract Base Class Design for Analyzers

### Decision: Use ABC with Template Method Pattern

**Rationale**:
- Enforces consistent interface across all Tier 3 analyzers
- Allows shared implementation (default parameters, common validation)
- Type checkers (mypy, pyright) enforce compliance at development time
- Aligns with existing BaseGenerator pattern in codebase

**Implementation Pattern**:
```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseAnalyzer(ABC):
    """Base class for all analyzer components.

    Provides standardized constructor interface and common utilities.
    Subclasses MUST implement analyze() method.
    """

    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        """Initialize analyzer with standard parameters.

        Args:
            storage_dir: Directory for analytics storage (defaults to ~/.claude)
            days: Number of days of history to analyze (default: 30)
        """
        self.storage_dir = storage_dir or Path.home() / ".claude"
        self.days = days
        self._validate_parameters()

    def _validate_parameters(self):
        """Common validation logic for all analyzers."""
        if self.days < 1:
            raise ValueError(f"days must be >= 1, got {self.days}")
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def analyze(self) -> Any:
        """Perform analysis. Subclasses MUST implement."""
        pass
```

**Alternatives Considered**:
- **Protocol/typing.Protocol**: Rejected - runtime enforcement weaker, doesn't provide shared implementation
- **Composition over inheritance**: Rejected - analyzers genuinely share IS-A relationship, not HAS-A
- **Mixin classes**: Rejected - adds complexity without solving constructor signature problem

**References**:
- PEP 3119 (Abstract Base Classes)
- Effective Python Item 37: "Compose Classes Instead of Nesting Many Levels of Built-in Types"
- Gang of Four: Template Method pattern

---

## 3. Circular Import Detection Strategy

### Decision: Static Analysis with importlib + AST Parsing

**Rationale**:
- Catch circular imports before execution (fail-fast per clarification #2)
- Python's importlib.util can detect cycles without actually importing
- AST parsing identifies import statements without side effects
- Tooling available: pylint, mypy both detect circular imports

**Implementation Approach**:
```python
import ast
from pathlib import Path

def detect_circular_imports(schema_dir: Path) -> list[tuple[str, str]]:
    """Detect circular import dependencies in schema modules.

    Returns:
        List of (module_a, module_b) tuples representing circular dependencies

    Raises:
        CircularImportError: If circular dependency detected (fail-fast)
    """
    # Build dependency graph from import statements
    dependencies = {}
    for py_file in schema_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file) as f:
            tree = ast.parse(f.read())

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("claude_automation.schemas"):
                    imports.append(node.module.split(".")[-1])

        dependencies[py_file.stem] = imports

    # Detect cycles using depth-first search
    cycles = find_cycles(dependencies)
    if cycles:
        raise CircularImportError(f"Circular imports detected: {cycles}")

    return cycles
```

**Alternatives Considered**:
- **Runtime detection only**: Rejected - fails too late, harder to debug
- **Manual code review only**: Rejected - error-prone, doesn't scale
- **Defer to Python's import system**: Rejected - provides poor error messages, doesn't fail fast

**Tools to Use**:
- mypy --no-incremental (detects import cycles during type checking)
- pytest with import validation test (test_schema_imports.py)
- Custom AST-based validator (for clearer error messages)

---

## 4. Semi-Automated Import Update Strategy

### Decision: AST-Based Discovery + Manual Review + Validation Tests

**Rationale** (from clarification #1):
- Balances safety with efficiency
- Automated tools catch obvious cases quickly (regex/AST parsing)
- Manual review catches edge cases (dynamic imports, string-based imports)
- Explicit validation prevents silent failures

**Implementation Workflow**:

1. **Discovery Phase** (Automated):
   ```bash
   # Find all files importing from schemas
   rg "from claude_automation.schemas import" -l > imports_to_update.txt
   rg "import claude_automation.schemas" -l >> imports_to_update.txt

   # AST-based analysis for complex imports
   python scripts/analyze_imports.py --source schemas.py --output import_report.json
   ```

2. **Update Phase** (Semi-Automated):
   ```python
   # Tool-assisted but reviewed before applying
   import_rewriter.py:
     - Parse AST to find import statements
     - Suggest new import based on schema → domain mapping
     - Show diff for manual approval
     - Apply changes only after confirmation
   ```

3. **Validation Phase** (Automated):
   ```python
   # test_schema_imports.py
   def test_backward_compatibility():
       """Verify all old-style imports still work."""
       from claude_automation.schemas import PermissionPattern
       from claude_automation.schemas import MCPServerInfo
       # ... test all 45+ models

   def test_new_imports():
       """Verify new domain-specific imports work."""
       from claude_automation.schemas.permissions import PermissionPattern
       from claude_automation.schemas.mcp import MCPServerInfo
       # ... test domain organization

   def test_no_unused_imports():
       """Verify no schema imports left in old file."""
       # Run after migration complete
   ```

**Tools**:
- ripgrep (rg) for fast text search
- ast.parse() for accurate import detection
- libcst for code transformation (preserves formatting)
- pytest for validation

**Alternatives Considered**:
- **Fully automated (Option A)**: Rejected - risky for complex codebase, might miss edge cases
- **Fully manual (Option C)**: Rejected - error-prone, time-consuming
- **Incremental (Option D)**: Rejected - leaves codebase in inconsistent state during migration

---

## 5. UI Extraction Pattern

### Decision: Dependency Injection via Constructor

**Rationale**:
- Engine remains testable (inject mock UI for unit tests)
- UI logic cleanly separated (single responsibility principle)
- Preserves exact user-facing behavior (same prompts, same flow)
- Follows existing patterns in codebase (BaseGenerator injecting templates)

**Implementation Pattern**:
```python
# claude_automation/core/interactive_ui.py
class InteractiveApprovalUI:
    """Handles interactive user approval for learning suggestions."""

    def present_report(self, report: LearningReport) -> None:
        """Display learning report to user (extracted from engine)."""
        # Exact logic from _present_report() method
        ...

    def collect_approvals(self, suggestions: list[Suggestion]) -> list[Suggestion]:
        """Collect user approvals for suggestions (extracted from engine)."""
        # Exact logic from _collect_approvals() method
        ...

# claude_automation/core/adaptive_system_engine.py
class AdaptiveSystemEngine:
    def __init__(self, interactive: bool = True, ui: InteractiveApprovalUI | None = None):
        self.interactive = interactive
        self.ui = ui or InteractiveApprovalUI()  # Default instance

    def run_full_learning_cycle(self) -> LearningReport:
        ...
        if self.interactive:
            self.ui.present_report(report)
            approved = self.ui.collect_approvals(report.suggestions)
        ...
```

**Testing Benefits**:
```python
# tests/unit/test_adaptive_system_engine.py
def test_non_interactive_mode():
    """Engine runs without UI in non-interactive mode."""
    engine = AdaptiveSystemEngine(interactive=False)
    report = engine.run_full_learning_cycle()
    # No UI prompts, all suggestions auto-approved or rejected

def test_with_mock_ui():
    """Engine uses injected UI for approval."""
    mock_ui = MockInteractiveUI(approve_all=True)
    engine = AdaptiveSystemEngine(interactive=True, ui=mock_ui)
    report = engine.run_full_learning_cycle()
    assert mock_ui.present_report_called
```

**Alternatives Considered**:
- **Functional approach (pass callbacks)**: Rejected - less OOP-friendly, harder to test
- **Global UI singleton**: Rejected - makes testing harder, violates dependency inversion
- **Keep UI in engine**: Rejected - violates single responsibility, doesn't solve complexity

---

## 6. Domain Boundary Validation

### Decision: Explicit Domain Contracts in contracts/

**Rationale**:
- Documents which schemas belong in which domain (prevents drift)
- Provides reference for future schema additions
- Enforceable via tests (schema in correct file, no cross-domain dependencies)

**Domain Definitions** (from FR-004):

1. **core.py**: System-level foundational schemas
   - ToolCategory, ProjectType, ToolInfo, FishAbbreviation
   - GitStatus, SystemConfig, ProjectConfig, ParsingResult
   - *Rationale*: Used across all domains, no business logic

2. **permissions.py**: Permission learning and approval
   - PermissionApprovalEntry, PermissionPattern, PatternSuggestion
   - *Rationale*: Tier 1 learning, tightly coupled approval tracking

3. **mcp.py**: MCP server management and analytics
   - MCPServerType, MCPServerStatus, MCPServerInfo, MCPToolUsage
   - MCPSessionStats, MCPServerSessionUtilization
   - MCPUsageRecommendation, GlobalMCPReport, MCPUsageAnalyticsConfig
   - *Rationale*: Distinct external integration domain

4. **learning.py**: Cross-project and meta-learning
   - LearningMetrics, ThresholdAdjustment, LearningHealthReport
   - CrossProjectPattern, TransferSuggestion, ProjectArchetype
   - *Rationale*: Tier 3 learning, distinct from Tier 1/2

5. **context.py**: Context optimization and usage tracking
   - ContextAccessLog, SectionUsage, ContextOptimization
   - *Rationale*: Tier 1 learning, focused on CLAUDE.md optimization

6. **workflows.py**: Workflow and slash command detection
   - SlashCommandLog, WorkflowSequence, WorkflowSuggestion
   - CommandCategory, SlashCommand, SlashCommandsConfig
   - CommandUsage, UsagePattern, UsageAnalyticsConfig
   - *Rationale*: Tier 2 learning, command-oriented

7. **validation.py**: Generation and validation results
   - ValidationResult, SourceArtifactDeclaration
   - GenerationHeader, GenerationResult
   - *Rationale*: Infrastructure schemas used by generators/validators

**Boundary Rules**:
- ✅ Schemas may import from core.py (foundational types)
- ✅ Generators/analyzers may import from multiple domains (cross-cutting)
- ❌ Domain schemas MUST NOT import from other domain schemas (prevents coupling)
- ❌ Domain schemas MUST NOT import from validators/ or generators/ (layer violation)

---

## Summary

All research questions resolved. Key decisions:

1. **Backward Compatibility**: Package-level __init__.py with re-exports
2. **BaseAnalyzer**: ABC with template method pattern, standardized constructor
3. **Circular Imports**: AST-based detection with fail-fast error
4. **Import Updates**: Semi-automated workflow (discovery → review → validation)
5. **UI Extraction**: Dependency injection for testability
6. **Domain Boundaries**: Explicit contracts with validation rules

**Ready for Phase 1**: Design & Contracts

