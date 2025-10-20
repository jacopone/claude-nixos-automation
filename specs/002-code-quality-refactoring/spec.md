---
status: active
created: 2025-10-20
updated: 2025-10-20
type: planning
lifecycle: persistent
---

# Feature Specification: Code Quality Refactoring

**Feature Branch**: `002-code-quality-refactoring`
**Created**: 2025-10-19
**Status**: Draft
**Input**: User description: "Implement high-priority code quality refactoring recommendations from comprehensive analysis: 1) Split monolithic schemas.py (1,455 lines) into domain modules, 2) Fix API alignment issues (24 test failures), 3) Extract interactive UI logic from AdaptiveSystemEngine"

## Clarifications

### Session 2025-10-19

- Q: What approach should be used to update internal imports after schema split (FR-005)? → A: Semi-automated with validation (tool-assisted discovery + manual review + import validation tests)
- Q: How should the system handle circular import detection during schema split? → A: Fail fast with clear error (halt split, report circular dependency, require manual resolution)

## User Scenarios & Testing

### User Story 1 - Navigate and Maintain Schema Code (Priority: P1)

Developers need to quickly find and modify schema definitions without navigating a massive 1,455-line file. When making changes to permission-related schemas, they should only need to work with permission schemas, not scroll through MCP, learning, and validation schemas.

**Why this priority**: This is the highest priority because it's blocking future scalability and causing merge conflicts. The monolithic schemas.py file impacts daily developer productivity and code maintainability.

**Independent Test**: Can be fully tested by attempting to import any schema from the new modular structure. Success means all existing imports still work, new imports are cleaner (e.g., `from claude_automation.schemas.permissions import PermissionPattern`), and the test suite passes without modifications.

**Acceptance Scenarios**:

1. **Given** a developer needs to modify a permission schema, **When** they open the codebase, **Then** they can directly navigate to `claude_automation/schemas/permissions.py` containing only permission-related models
2. **Given** existing code imports schemas from `claude_automation.schemas`, **When** the schema split is complete, **Then** all existing imports continue to work without modification via re-exports in `__init__.py`
3. **Given** multiple developers working on different schema domains, **When** they make changes simultaneously, **Then** merge conflicts are reduced because each domain has its own file

---

### User Story 2 - Run Tests Successfully (Priority: P1)

Developers need the test suite to pass reliably. Currently, 24 tests fail due to API misalignment (constructor signature mismatches), which creates confusion about whether code changes broke something or if it's a known issue.

**Why this priority**: This is equally critical because failing tests undermine confidence in the test suite and make it harder to detect real regressions. A 77% pass rate should be 100% for non-optional tests.

**Independent Test**: Can be fully tested by running the test suite. Success means all Tier 3 analyzer tests pass, bringing the pass rate from 77% (215/280) to at least 86% (239/280).

**Acceptance Scenarios**:

1. **Given** the test suite with 24 failing tests, **When** API alignment is fixed, **Then** all 24 previously failing tests now pass
2. **Given** a developer runs `pytest tests/unit/`, **When** tests complete, **Then** they see 100% pass rate for all unit tests
3. **Given** standardized analyzer interfaces, **When** a new analyzer is created, **Then** it follows the same constructor pattern (`storage_dir`, `days` parameters)

---

### User Story 3 - Understand Engine Code Flow (Priority: P2)

Developers need to understand and modify the AdaptiveSystemEngine without getting lost in mixed concerns. Currently, orchestration logic and interactive UI code are intertwined, making it hard to follow the learning cycle workflow.

**Why this priority**: This is secondary priority because while it impacts code clarity and testability, it doesn't block scalability like the schema split or create false failures like the API misalignment. It's technical debt that should be addressed after the higher-priority issues.

**Independent Test**: Can be fully tested by verifying the engine still orchestrates learning cycles correctly after UI extraction. Success means the same interactive approval workflow functions, but the code is now in a dedicated `InteractiveApprovalUI` class.

**Acceptance Scenarios**:

1. **Given** a developer needs to modify the approval UI, **When** they locate the code, **Then** they find it in a dedicated `InteractiveApprovalUI` class, not embedded in the engine
2. **Given** the refactored engine, **When** running in interactive mode, **Then** the user still sees the same prompts and can approve/reject suggestions
3. **Given** the extracted UI logic, **When** writing tests for the engine, **Then** tests can mock the UI class instead of dealing with deep nesting

---

### Edge Cases

- What happens when an existing import statement uses a specific schema that's been moved to a domain module? (Answered: Backward compatibility via `__init__.py` re-exports ensures no import breaks)
- How does the system handle partial refactoring where some analyzers are updated but others aren't? (Design for incremental rollout: add default parameters to base class, update subclasses gradually)
- What if new tests are added during the refactoring process? (Tests should continue to use the same fixture patterns; only constructor signatures change)
- How do we ensure no functionality is lost during the UI extraction? (Preserve exact behavior: extract methods as-is, then refactor if needed)
- What happens if circular import is detected during schema split? (System halts split immediately, reports clear error message identifying the circular dependency chain, requires manual resolution before continuing)

## Requirements

### Functional Requirements

#### Schema Split (Priority P1)

- **FR-001**: System MUST split `claude_automation/schemas.py` into 8 domain-specific modules: `core.py`, `permissions.py`, `mcp.py`, `learning.py`, `context.py`, `workflows.py`, `validation.py`, plus `__init__.py`
- **FR-002**: System MUST maintain backward compatibility by re-exporting all schemas from `claude_automation/schemas/__init__.py`
- **FR-003**: System MUST preserve all 51 existing Pydantic models without modification to their structure, validators, or behavior
- **FR-004**: System MUST organize schemas by domain:
  - `core.py`: ToolCategory, ProjectType, ToolInfo, FishAbbreviation, GitStatus, SystemConfig, ProjectConfig, ParsingResult
  - `permissions.py`: PermissionApprovalEntry, PermissionPattern, PatternSuggestion
  - `mcp.py`: MCPServerType, MCPServerStatus, MCPServerInfo, MCPToolUsage, MCPSessionStats, MCPServerSessionUtilization, MCPUsageRecommendation, GlobalMCPReport, MCPUsageAnalyticsConfig
  - `learning.py`: LearningMetrics, ThresholdAdjustment, LearningHealthReport, CrossProjectPattern, TransferSuggestion, ProjectArchetype
  - `context.py`: ContextAccessLog, SectionUsage, ContextOptimization
  - `workflows.py`: SlashCommandLog, WorkflowSequence, WorkflowSuggestion, CommandCategory, SlashCommand, SlashCommandsConfig, CommandUsage, UsagePattern, UsageAnalyticsConfig
  - `validation.py`: ValidationResult, SourceArtifactDeclaration, GenerationHeader, GenerationResult
- **FR-005**: System MUST update all internal imports within `claude_automation/` to use the new module structure using a semi-automated approach: tool-assisted discovery (AST parsing/grep) + manual review + import validation tests to ensure correctness
- **FR-006**: System MUST ensure the test suite passes without test modifications (tests should continue using backward-compatible imports)

#### API Alignment (Priority P1)

- **FR-007**: System MUST create a `BaseAnalyzer` abstract base class with standardized constructor: `def __init__(self, storage_dir: Path = None, days: int = 30)`
- **FR-008**: System MUST update all Tier 3 analyzers to inherit from `BaseAnalyzer` and implement the standard constructor
- **FR-009**: System MUST fix constructor signatures in:
  - `analyzers/project_archetype_detector.py`
  - `analyzers/meta_learner.py`
  - All other Tier 3 analyzers that currently fail constructor tests
- **FR-010**: System MUST ensure all 24 previously failing tests pass after API alignment
- **FR-011**: System MUST maintain analyzer functionality - only constructor signatures change, not behavior

#### UI Extraction (Priority P2)

- **FR-012**: System MUST create a new `InteractiveApprovalUI` class in `claude_automation/core/interactive_ui.py`
- **FR-013**: System MUST extract these methods from `AdaptiveSystemEngine` to `InteractiveApprovalUI`:
  - `_present_report(report)` → `present_report(report)`
  - `_collect_approvals(report)` → `collect_approvals(suggestions)`
  - Logic for showing suggestion details (currently inline)
- **FR-014**: System MUST update `AdaptiveSystemEngine.run_full_learning_cycle()` to instantiate and use `InteractiveApprovalUI` when in interactive mode
- **FR-015**: System MUST preserve exact user-facing behavior: same prompts, same input handling, same approval workflow

### Key Entities

- **Schema Module**: A Python file containing domain-specific Pydantic models (e.g., `permissions.py` contains all permission-related schemas)
- **BaseAnalyzer**: Abstract base class defining the standard interface for all analyzer components
- **InteractiveApprovalUI**: Extracted class responsible for presenting learning reports and collecting user approvals
- **Domain Boundary**: Logical grouping of related schemas (core, permissions, MCP, learning, context, workflows, validation)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Developers can navigate to any schema definition in under 10 seconds (vs. current ~30 seconds scrolling through 1,455 lines)
- **SC-002**: Test pass rate increases from 77% (215/280) to at least 86% (239/280) by fixing the 24 API alignment failures
- **SC-003**: Zero import errors occur after schema split when running `python -c "from claude_automation.schemas import *"`
- **SC-004**: All existing code continues to function without modification (100% backward compatibility)
- **SC-005**: Merge conflicts in schema files decrease by at least 60% when multiple developers work on different domains
- **SC-006**: The AdaptiveSystemEngine class reduces from 608 lines to under 500 lines after UI extraction
- **SC-007**: New analyzer implementations require under 5 minutes to align with BaseAnalyzer interface (vs current ~15 minutes figuring out inconsistent patterns)

## Scope

### In Scope

- Splitting schemas.py into 8 domain modules with backward-compatible re-exports
- Creating BaseAnalyzer abstract base class
- Standardizing all Tier 3 analyzer constructor signatures
- Extracting interactive UI logic from AdaptiveSystemEngine
- Updating internal imports to use new modular structure
- Ensuring test suite passes after changes

### Out of Scope

- Modifying test code beyond what's necessary for API alignment
- Refactoring analyzer logic beyond constructor signatures
- UI/UX improvements to the interactive approval workflow
- Performance optimizations
- Adding new features or capabilities
- Addressing other code quality issues from the analysis (pytest.approx, config files, etc.) - these are future work

## Assumptions

- The current test suite accurately reflects expected behavior (failing tests are due to API misalignment, not bugs)
- Developers are familiar with Python imports and module structure
- The existing schema organization follows clear domain boundaries
- No external code outside the repository depends on direct imports from `schemas.py` internals
- The interactive approval workflow is functioning correctly and should be preserved as-is

## Dependencies

- Existing test suite must be runnable
- No changes to Pydantic version or validation behavior
- Python 3.13 compatibility maintained
- All current imports in the codebase must be discoverable for update

## Constraints

- Must maintain 100% backward compatibility for schema imports
- Cannot modify test expectations, only implementation to match tests
- Must preserve all existing Pydantic validators and model behavior
- Refactoring must not introduce new dependencies
- Changes must not affect runtime performance

## Risks

- **Risk**: Breaking imports in external code not covered by tests
  - **Mitigation**: Comprehensive re-exports in `__init__.py`, manual review of all imports

- **Risk**: Test failures due to circular imports after split
  - **Mitigation**: Fail-fast validation during schema split (halt split and report circular dependency with clear error message requiring manual resolution before proceeding), careful domain boundary design, import order testing

- **Risk**: Behavioral changes when extracting UI logic
  - **Mitigation**: Exact method extraction, integration testing before/after

## Success Metrics

- Lines of code in largest schema file: Target <300 lines including docstrings and comments (from 1,455)
- Test pass rate: Target 86%+ (from 77%)
- Import statement length: Target <60 chars (from potential >80 with deep paths)
- AdaptiveSystemEngine complexity: Target <500 lines including docstrings and comments (from 608)
- Time to locate a schema: Target <10 seconds (from ~30 seconds)
