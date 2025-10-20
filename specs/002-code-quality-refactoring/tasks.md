---
status: active
created: 2025-10-20
updated: 2025-10-20
type: planning
lifecycle: persistent
---

# Implementation Tasks: Code Quality Refactoring

**Feature**: Code Quality Refactoring
**Branch**: `002-code-quality-refactoring`
**Generated**: 2025-10-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This document provides a dependency-ordered task breakdown for refactoring the monolithic 1,455-line schemas.py, fixing 24 test failures through API alignment, and extracting UI logic from the 608-line AdaptiveSystemEngine.

**Total Tasks**: 34
**Estimated Time**: 6 hours

---

## Phase 1: Setup & Prerequisites (Foundation)

**Goal**: Prepare the codebase for refactoring by creating necessary directory structure and validation tooling.

**Tasks** (2 tasks, ~15 minutes):

- [ ] T001 Create schemas/ subdirectory in claude_automation/
- [ ] T002 [P] Create contracts validation script for circular import detection

**Completion Criteria**:
- Directory `claude_automation/schemas/` exists
- Script `scripts/detect_circular_imports.py` can be run without errors

---

## Phase 2: User Story 1 - Navigate and Maintain Schema Code (P1)

**Story Goal**: Split the monolithic 1,455-line schemas.py into 8 domain-specific modules so developers can navigate to specific schema definitions in <10 seconds (vs current ~30 seconds).

**Independent Test**: Import any schema from the new modular structure. All existing imports still work via backward-compatible re-exports, new domain-specific imports work, and test suite passes without test modifications.

**Tasks** (14 tasks, ~2 hours):

### Schema Domain Module Creation

- [ ] T003 [P] [US1] Create core.py with 8 foundational schemas in claude_automation/schemas/core.py
- [ ] T004 [P] [US1] Create permissions.py with 3 permission learning schemas in claude_automation/schemas/permissions.py
- [ ] T005 [P] [US1] Create mcp.py with 9 MCP server/tool schemas in claude_automation/schemas/mcp.py
- [ ] T006 [P] [US1] Create learning.py with 6 meta-learning schemas in claude_automation/schemas/learning.py
- [ ] T007 [P] [US1] Create context.py with 3 context optimization schemas in claude_automation/schemas/context.py
- [ ] T008 [P] [US1] Create workflows.py with 9 workflow/slash command schemas in claude_automation/schemas/workflows.py
- [ ] T009 [P] [US1] Create validation.py with 4 validation/generation result schemas in claude_automation/schemas/validation.py

### Backward Compatibility & Validation

- [ ] T010 [US1] Create __init__.py with re-exports of all 42+ schemas in claude_automation/schemas/__init__.py
- [ ] T011 [US1] Run circular import detection script on claude_automation/schemas/ directory
- [ ] T012 [US1] Verify backward compatibility by running: python -c "from claude_automation.schemas import *"
- [ ] T013 [US1] Verify new imports work by testing: from claude_automation.schemas.permissions import PermissionPattern
- [ ] T014 [US1] Run schema validation tests: pytest tests/test_schemas.py -v

### Import Migration (Semi-Automated)

- [ ] T015 [US1] Discover all import statements using: rg "from claude_automation.schemas import" -l > /tmp/imports_to_update.txt
- [ ] T016 [US1] Update internal imports in analyzers/ generators/ validators/ to use new domain-specific imports

**Story Completion Test**:
```bash
# All three import styles work
python -c "from claude_automation.schemas import PermissionPattern"
python -c "from claude_automation.schemas.permissions import PermissionPattern"

# Schema tests pass
pytest tests/test_schemas.py -v

# No circular imports
mypy claude_automation/schemas/ --no-incremental

# File sizes <300 lines each
wc -l claude_automation/schemas/*.py | grep -v total
```

**Success Criteria**: SC-001 (navigate in <10s), SC-003 (zero import errors), SC-004 (100% backward compatibility), SC-005 (reduced merge conflicts)

**Parallel Execution Opportunities**:
- Tasks T003-T009 (7 domain modules) can be created in parallel - each works on a different file
- All run after circular import check (T011)

---

## Phase 3: User Story 2 - Run Tests Successfully (P1)

**Story Goal**: Fix 24 failing tests by standardizing Tier 3 analyzer constructor signatures, bringing test pass rate from 77% (215/280) to at least 86% (239/280).

**Independent Test**: Run the test suite. All Tier 3 analyzer tests pass, bringing pass rate to 86%+.

**Tasks** (10 tasks, ~1.5 hours):

### BaseAnalyzer Creation

- [ ] T017 [US2] Create BaseAnalyzer abstract base class with standardized constructor in claude_automation/analyzers/base_analyzer.py
- [ ] T018 [US2] Create test for BaseAnalyzer contract in tests/unit/test_base_analyzer.py

### Tier 3 Analyzer Updates

- [ ] T019 [P] [US2] Update PermissionPatternDetector to inherit from BaseAnalyzer in claude_automation/analyzers/permission_pattern_detector.py
- [ ] T020 [P] [US2] Update GlobalMCPAnalyzer to inherit from BaseAnalyzer in claude_automation/analyzers/global_mcp_analyzer.py
- [ ] T021 [P] [US2] Update ContextOptimizer to inherit from BaseAnalyzer in claude_automation/analyzers/context_optimizer.py
- [ ] T022 [P] [US2] Update WorkflowDetector to inherit from BaseAnalyzer in claude_automation/analyzers/workflow_detector.py
- [ ] T023 [P] [US2] Update InstructionTracker to inherit from BaseAnalyzer in claude_automation/analyzers/instruction_tracker.py
- [ ] T024 [P] [US2] Update ProjectArchetypeDetector to inherit from BaseAnalyzer in claude_automation/analyzers/project_archetype_detector.py
- [ ] T025 [P] [US2] Update MetaLearner to inherit from BaseAnalyzer in claude_automation/analyzers/meta_learner.py

### Validation

- [ ] T026 [US2] Run full test suite and verify 86%+ pass rate: pytest tests/ -v --tb=no

**Story Completion Test**:
```bash
# All previously failing tests now pass
pytest tests/unit/test_permission_patterns.py -v
pytest tests/unit/test_approval_tracker.py -v
pytest tests/integration/test_learning_cycle.py -v
pytest tests/contract/test_analyzer_contracts.py -v

# Overall pass rate is 86%+
pytest tests/ --tb=no | grep "passed"
```

**Success Criteria**: SC-002 (test pass rate >= 86%), SC-007 (new analyzers align in <5 min)

**Parallel Execution Opportunities**:
- Task T017 (BaseAnalyzer) must complete first
- Tasks T019-T025 (7 analyzer updates) can be done in parallel - each updates a different analyzer file
- Task T026 (full test suite) runs after all analyzer updates

**Dependencies**: Requires Phase 2 (User Story 1) to be complete for schema imports to work correctly in analyzers.

---

## Phase 4: User Story 3 - Understand Engine Code Flow (P2)

**Story Goal**: Extract interactive UI logic from the 608-line AdaptiveSystemEngine into a dedicated InteractiveApprovalUI class, reducing engine complexity to <500 lines while preserving exact user-facing behavior.

**Independent Test**: Verify the engine still orchestrates learning cycles correctly after UI extraction. Same interactive approval workflow functions, but code is now in a dedicated InteractiveApprovalUI class.

**Tasks** (5 tasks, ~1 hour):

### UI Component Creation

- [ ] T027 [US3] Create InteractiveApprovalUI class with present_report() and collect_approvals() methods in claude_automation/core/interactive_ui.py
- [ ] T028 [US3] Extract _present_report() logic from AdaptiveSystemEngine to InteractiveApprovalUI.present_report()
- [ ] T029 [US3] Extract _collect_approvals() logic from AdaptiveSystemEngine to InteractiveApprovalUI.collect_approvals()

### Engine Integration

- [ ] T030 [US3] Update AdaptiveSystemEngine to use InteractiveApprovalUI via dependency injection in claude_automation/core/adaptive_system_engine.py
- [ ] T031 [US3] Remove _present_report() and _collect_approvals() methods from AdaptiveSystemEngine

### Validation

- [ ] T032 [US3] Run integration tests to verify behavior preserved: pytest tests/integration/test_learning_cycle.py -v
- [ ] T033 [US3] Verify engine file size <500 lines: wc -l claude_automation/core/adaptive_system_engine.py

**Story Completion Test**:
```bash
# Engine file size reduced
wc -l claude_automation/core/adaptive_system_engine.py  # Should be <500

# Interactive workflow still works
python3 -c "
from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine
from claude_automation.core.interactive_ui import InteractiveApprovalUI
engine = AdaptiveSystemEngine(interactive=False)
print('✅ Engine instantiates without errors')
"

# Integration tests pass
pytest tests/integration/test_learning_cycle.py -v
```

**Success Criteria**: SC-006 (engine <500 lines)

**Parallel Execution Opportunities**:
- Tasks T027-T029 can be done together (extracting to new class)
- Tasks T030-T031 must run after T027-T029 complete
- Tasks T032-T033 run after all code changes

**Dependencies**: Requires Phase 2 (User Story 1) for schema imports, but independent of Phase 3 (User Story 2).

---

## Phase 4 Extended: ImprovementApplicator Extraction

**Goal**: Further reduce engine complexity by extracting improvement application logic, reaching <500 line target (from 519 → 379 lines).

**Background**: After completing T027-T033, the engine was at 519 lines - close to but not quite meeting the <500 line target. Additional extraction was needed.

**Tasks** (8 tasks, ~1 hour):

### Applicator Component Creation

- [x] T034 [US3-EXT] Create ImprovementApplicator class skeleton in claude_automation/core/improvement_applicator.py
- [x] T035 [US3-EXT] Extract _apply_improvements() method to ImprovementApplicator.apply_improvements()
- [x] T036 [US3-EXT] Extract _apply_mcp_optimizations() helper method
- [x] T037 [US3-EXT] Extract _apply_permission_patterns() helper method
- [x] T038 [US3-EXT] Extract _apply_context_optimizations() helper method
- [x] T039 [US3-EXT] Extract _apply_workflow_patterns() helper method
- [x] T040 [US3-EXT] Extract _update_meta_learning() method to ImprovementApplicator.update_meta_learning()

### Engine Integration & Validation

- [x] T041 [US3-EXT] Update AdaptiveSystemEngine to use ImprovementApplicator, remove old methods, run tests, verify <500 lines

**Story Completion Test**:
```bash
# Engine file size reduced to <500
wc -l claude_automation/core/adaptive_system_engine.py  # Should be 379 lines

# New applicator class created
test -f claude_automation/core/improvement_applicator.py && echo "✅ ImprovementApplicator exists"

# Integration tests pass
pytest tests/integration/test_learning_cycle.py -v  # All 8 tests passing
```

**Results Achieved**:
- Engine reduced: 519 → 379 lines (140 line reduction, 27%)
- Total reduction from start: 732 → 379 lines (353 lines, 48%)
- Target exceeded: 379 < 500 ✅ (121 line buffer)
- All 8 integration tests passing
- Clean architecture with three focused classes

**Success Criteria**: SC-006 exceeded (engine now 379 lines, 24% under target)

---

## Phase 5: Final Validation & Cleanup

**Goal**: Validate all refactoring is complete, remove old files, and verify all success criteria met.

**Tasks** (3 tasks, ~30 minutes):

- [ ] T042 Run full test suite and verify all tests pass (verify 239+ tests pass at 86%+ rate, excluding optional tests): pytest tests/ -v
- [ ] T043 [P] Create import validation test in tests/integration/test_schema_imports.py
- [ ] T044 Remove old monolithic schemas.py file: git rm claude_automation/schemas.py

**Completion Test**:
```bash
# All tests pass (239+ passing, 86%+ rate)
pytest tests/ -v --tb=short | grep -E "(passed|failed)"

# Import validation test confirms backward compatibility
pytest tests/integration/test_schema_imports.py -v

# Old file removed
test ! -f claude_automation/schemas.py && echo "✅ Old schemas.py removed"
```

---

## Task Dependencies & Execution Order

### Dependency Graph

```
Phase 1 (Setup)
  T001, T002 → Can run in parallel
  ↓
Phase 2 (User Story 1 - Schema Split - P1)
  T003-T009 → Can run in parallel after T001
  ↓
  T010 → Depends on T003-T009 (needs all domains)
  ↓
  T011 → Depends on T010 (check circular imports)
  ↓
  T012-T014 → Can run in parallel after T011 (validation tests)
  ↓
  T015-T016 → Sequential (discover, then update imports)
  ↓
Phase 3 (User Story 2 - API Alignment - P1)
  T017 → Create BaseAnalyzer (must complete first)
  T018 → Depends on T017
  ↓
  T019-T025 → Can run in parallel after T017 (update analyzers)
  ↓
  T026 → Depends on T019-T025 (run full test suite)
  ↓
Phase 4 (User Story 3 - UI Extraction - P2)
  (Can run in parallel with Phase 3 if desired)
  T027-T029 → Can run together (extract UI)
  ↓
  T030-T031 → Sequential after T027-T029 (update engine)
  ↓
  T032-T033 → Can run in parallel after T030-T031 (validation)
  ↓
Phase 5 (Final Validation)
  T042, T043 → Can run in parallel after all phases
  ↓
  T044 → Depends on T042-T043 (remove old file only after validation)
```

### Critical Path

The fastest execution path to completion:

1. **Setup** (T001-T002): 15 min
2. **Schema Split** (T003-T016): 2 hours
3. **API Alignment** (T017-T026): 1.5 hours
4. **UI Extraction** (T027-T033): 1 hour (can overlap with API alignment)
5. **ImprovementApplicator** (T034-T041): 1 hour
6. **Final Validation** (T042-T044): 30 min

**Total Critical Path**: ~5-6 hours (with parallel execution)

### Parallel Execution Examples

**Maximum Parallelization**:

```bash
# Phase 2: Create 7 domain modules simultaneously
# T003-T009 (each developer takes 1 domain)
Developer A: T003 (core.py)
Developer B: T004 (permissions.py)
Developer C: T005 (mcp.py)
Developer D: T006 (learning.py)
Developer E: T007 (context.py)
Developer F: T008 (workflows.py)
Developer G: T009 (validation.py)

# Phase 3: Update 7 analyzers simultaneously
# T019-T025 (each developer takes 1 analyzer)
Developer A: T019 (PermissionPatternDetector)
Developer B: T020 (GlobalMCPAnalyzer)
Developer C: T021 (ContextOptimizer)
Developer D: T022 (WorkflowDetector)
Developer E: T023 (InstructionTracker)
Developer F: T024 (ProjectArchetypeDetector)
Developer G: T025 (MetaLearner)
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended MVP**: Complete Phase 2 (User Story 1) + Phase 3 (User Story 2) only.

This delivers:
- ✅ Modular schema organization (P1 - highest impact)
- ✅ All tests passing (P1 - highest confidence)
- ⏸️ UI extraction (P2 - lower priority, can be deferred)

**MVP Benefits**:
- Unblocks future scalability (no more 1,455-line file)
- Restores test suite confidence (86%+ pass rate)
- ~4 hours of work vs. 6 hours for full scope

### Incremental Delivery Milestones

1. **Milestone 1** (After T016): Schema split complete, all imports working
2. **Milestone 2** (After T026): All tests passing (86%+)
3. **Milestone 3** (After T033): Engine complexity reduced
4. **Milestone 4** (After T036): Old code removed, refactoring complete

Each milestone is shippable and provides independent value.

---

## Validation Checklist

After all tasks complete, verify these success criteria:

### SC-001: Schema Navigation (<10 seconds)
- [ ] Open `claude_automation/schemas/permissions.py` in editor
- [ ] Verify only permission-related schemas present
- [ ] Time to locate: <10 seconds

### SC-002: Test Pass Rate (86%+)
- [ ] Run: `pytest tests/ --tb=no | grep "passed"`
- [ ] Verify: 239+ tests passing (86%+ of 280 total)

### SC-003: Zero Import Errors
- [ ] Run: `python -c "from claude_automation.schemas import *"`
- [ ] Verify: No ImportError

### SC-004: 100% Backward Compatibility
- [ ] Run: `pytest tests/integration/test_schema_imports.py -v`
- [ ] Verify: All old-style imports still work

### SC-005: Reduced Merge Conflicts
- [ ] Manual verification over time (60% reduction)

### SC-006: Engine Complexity (<500 lines)
- [ ] Run: `wc -l claude_automation/core/adaptive_system_engine.py`
- [ ] Verify: <500 lines

### SC-007: New Analyzer Alignment (<5 minutes)
- [ ] Create test analyzer inheriting from BaseAnalyzer
- [ ] Verify: Constructor signature matches automatically

---

## Notes for Implementer

### Semi-Automated Import Updates (T016)

Use this workflow for updating imports:

```bash
# 1. Discovery (automated)
rg "from claude_automation.schemas import" -l > /tmp/files_to_update.txt

# 2. Update (semi-automated with manual review)
for file in $(cat /tmp/files_to_update.txt); do
    echo "Reviewing: $file"
    # Identify which schemas are imported
    # Update to domain-specific imports based on contracts/schema-domains.md
    # Run tests after each file
done

# 3. Validation (automated)
pytest tests/ -v
```

### Circular Import Detection (T011)

If circular import detected:
- ❌ HALT immediately (fail-fast per clarification #2)
- ✅ Review contracts/schema-domains.md for boundary rules
- ✅ Move shared types to core.py if needed
- ✅ Re-run detection script

### UI Extraction Preservation (T028-T029)

When extracting methods:
- ✅ Copy logic exactly as-is (no refactoring yet)
- ✅ Preserve all prompts, input handling, approval workflow
- ✅ Run integration tests immediately after extraction
- ❌ Do NOT improve UX or add features (out of scope)

---

## Task Completion Tracking

**Progress**: 33/41 tasks complete (80%)

**Phase Status**:
- [x] Phase 1: Setup (2/2 tasks) ✅ COMPLETE
- [x] Phase 2: User Story 1 - Schema Split (14/14 tasks) ✅ COMPLETE
- [x] Phase 3: User Story 2 - API Alignment (10/10 tasks) ✅ COMPLETE
- [x] Phase 4: User Story 3 - UI Extraction (7/7 tasks) ✅ COMPLETE
- [x] Phase 4 Extended: ImprovementApplicator (8/8 tasks) ✅ COMPLETE
- [ ] Phase 5: Final Validation (0/3 tasks) ⏸️ PENDING

**Actual Completion**: 5.5 hours

---

**Generated by**: /speckit.tasks command
**Last Updated**: 2025-10-20 (Updated after Phase 4 Extended completion, task IDs renumbered)

