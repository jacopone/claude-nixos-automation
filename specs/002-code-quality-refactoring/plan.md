---
status: active
created: 2025-10-20
updated: 2025-10-20
type: planning
lifecycle: persistent
---

# Implementation Plan: Code Quality Refactoring

**Branch**: `002-code-quality-refactoring` | **Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-code-quality-refactoring/spec.md`

## Summary

Refactor the monolithic 1,455-line schemas.py into 8 domain-specific modules, standardize analyzer API interfaces by creating a BaseAnalyzer abstract class, and extract interactive UI logic from the 608-line AdaptiveSystemEngine. This refactoring addresses technical debt that blocks scalability, causes merge conflicts, and creates false test failures (24 tests failing due to API misalignment). The work is broken into three priority tiers (P1: schema split, P1: API alignment, P2: UI extraction) with clear success criteria: test pass rate increasing from 77% to 86%+, schema file sizes <300 lines, and engine complexity reducing to <500 lines.

## Technical Context

**Language/Version**: Python 3.13 (confirmed in pyproject.toml)
**Primary Dependencies**:
- Pydantic 2.5.0+ (schema validation, all data structures are BaseModel subclasses)
- Jinja2 3.1.2+ (template rendering)
- pytest 7.4.0+ (testing framework)

**Storage**: JSONL append-only files for analytics (~/.claude/*-analytics.jsonl)
**Testing**: pytest with 479 total tests across unit/, integration/, and contract/ directories
**Target Platform**: NixOS Linux development environment
**Project Type**: Single Python project (internal tooling for Claude Code automation)

**Performance Goals**:
- Full learning cycle: <10 seconds (currently 1.38s - well within target)
- Test suite: <30 seconds (refactoring must maintain)
- Import operations: <100ms (new modular structure should improve)

**Constraints**:
- 100% backward compatibility for schema imports (re-exports in __init__.py)
- Cannot modify test expectations, only implementations to match tests
- Must preserve all 45+ existing Pydantic validators and model behavior
- Zero new dependencies allowed
- Must not affect runtime performance

**Scale/Scope**:
- 1,455 lines → 8 files (<300 lines each)
- 45+ Pydantic models to organize across domains
- ~50 files importing from schemas.py need analysis
- 24 failing tests to fix (Tier 3 analyzer constructor signatures)
- 608-line engine → <500 lines after UI extraction

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Source/Artifact Separation (NON-NEGOTIABLE)
**Status**: PASS - This refactoring touches only source files (schemas.py → domain modules, analyzers, engine). No artifacts are edited directly.

### ✅ Principle II: Schema-First Design with Pydantic (NON-NEGOTIABLE)
**Status**: PASS - All 45+ models remain Pydantic BaseModel subclasses. Refactoring preserves validators, Field descriptions, and @root_validator decorators. No dict manipulation introduced.

### ✅ Principle III: Multi-Tier Adaptive Learning (CORE ARCHITECTURE)
**Status**: PASS - Refactoring does not alter learning tier architecture. Schema organization by domain (permissions, MCP, learning, workflows) aligns with tier boundaries. UI extraction improves engine testability.

### ✅ Principle IV: Validation at Boundaries (Tiered Strictness)
**Status**: PASS - Circular import detection during schema split will fail-fast (per clarification #2). Import validation tests ensure correctness. No boundary validation logic modified.

### ✅ Principle V: Idempotency and Graceful Degradation
**Status**: PASS - Refactoring does not affect generator idempotency or analyzer exception handling. Test suite verifies behavior preservation.

### ✅ Principle VI: Testing as Documentation
**Status**: PASS - Fixes 24 failing tests (API alignment). Maintains 100% test pass rate for schemas/templates. All refactored code covered by existing tests.

### ✅ Principle VII: Intelligence Over Inventory
**Status**: N/A - No impact on intelligence/context generation logic.

### ✅ Principle VIII: Dynamic Over Static
**Status**: N/A - No impact on project-aware filtering or dynamic context loading.

### ✅ Architectural Constraints
**Pure Function Generators**: PASS - BaseGenerator pattern unchanged
**Unidirectional Data Flow**: PASS - Sources → Analyzers → Generators → Artifacts flow maintained
**Three-Layer Architecture**: PASS - Analyzer layer refactored (BaseAnalyzer), generator/validator layers unchanged

### ✅ Design Patterns (Required)
**Base Class with Abstract Methods**: PASS - Creating BaseAnalyzer follows this pattern (FR-007)
**Result Objects**: PASS - No modification to GenerationResult/ValidationResult patterns
**Jinja2 Templates with Type-Safe Context**: PASS - Schema refactoring preserves Pydantic context
**Append-Only JSONL Logging**: PASS - No modification to analytics logging
**Tiered Confidence Scoring**: PASS - No modification to pattern detection

### ✅ Anti-Patterns (MUST AVOID)
**Editing Artifacts Directly**: PASS - Only source files modified
**Universal Context**: N/A
**Artifact Pollution**: N/A
**Silent Failures**: PASS - Fail-fast circular import detection (clarification #2)
**Implicit Magic**: PASS - Explicit import validation tests (clarification #1)

### 🎯 Constitution Gate: PASSED
No violations detected. All principles and architectural constraints satisfied.

## Project Structure

### Documentation (this feature)

```
specs/002-code-quality-refactoring/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (already exists)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
│   ├── base-analyzer.py # BaseAnalyzer abstract interface contract
│   └── schema-domains.md # Domain boundary definitions
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
claude_automation/
├── schemas/                      # NEW: Domain-specific schema modules
│   ├── __init__.py              # Re-exports for backward compatibility (FR-002)
│   ├── core.py                  # Core system schemas (~150 lines)
│   ├── permissions.py           # Permission learning schemas (~100 lines)
│   ├── mcp.py                   # MCP server/tool schemas (~200 lines)
│   ├── learning.py              # Meta-learning schemas (~150 lines)
│   ├── context.py               # Context optimization schemas (~100 lines)
│   ├── workflows.py             # Workflow/slash command schemas (~200 lines)
│   └── validation.py            # Validation/generation result schemas (~100 lines)
│
├── schemas.py                    # OLD: Monolithic file (TO BE REMOVED after migration)
│
├── analyzers/
│   ├── base_analyzer.py         # NEW: Abstract base class (FR-007)
│   ├── permission_pattern_detector.py  # UPDATED: Inherit from BaseAnalyzer
│   ├── global_mcp_analyzer.py   # UPDATED: Inherit from BaseAnalyzer
│   ├── context_optimizer.py     # UPDATED: Inherit from BaseAnalyzer
│   ├── workflow_detector.py     # UPDATED: Inherit from BaseAnalyzer
│   ├── instruction_tracker.py   # UPDATED: Inherit from BaseAnalyzer
│   ├── project_archetype_detector.py  # UPDATED: Fix constructor (FR-009)
│   ├── meta_learner.py          # UPDATED: Fix constructor (FR-009)
│   └── [other analyzers]        # UPDATED: Import from new schema modules
│
├── core/
│   ├── adaptive_system_engine.py  # UPDATED: Use InteractiveApprovalUI (FR-014)
│   └── interactive_ui.py        # NEW: Extracted UI logic (FR-012, FR-013)
│
├── generators/
│   └── [all generators]         # UPDATED: Import from new schema modules
│
└── validators/
    └── [all validators]         # UPDATED: Import from new schema modules

tests/
├── unit/
│   ├── test_base_analyzer.py    # NEW: Test abstract base class
│   ├── test_permission_patterns.py  # UPDATED: Pass with BaseAnalyzer
│   ├── test_approval_tracker.py # UPDATED: Pass with BaseAnalyzer
│   └── [other unit tests]       # UPDATED: Use new schema imports
│
├── integration/
│   ├── test_learning_cycle.py   # UPDATED: Pass with BaseAnalyzer
│   └── test_schema_imports.py   # NEW: Validate backward compatibility
│
└── contract/
    └── test_analyzer_contracts.py  # UPDATED: Test BaseAnalyzer contract
```

**Structure Decision**: Single project structure (Option 1). This is an internal Python tooling project with clear separation between analyzers/, generators/, validators/, and core/ modules. The schemas/ subdirectory represents a new organizational layer within the existing claude_automation package. Tests remain organized by type (unit/integration/contract) and will be updated to test the new modular structure while maintaining backward compatibility assertions.

## Complexity Tracking

*No constitutional violations - this section left empty per template guidance.*

