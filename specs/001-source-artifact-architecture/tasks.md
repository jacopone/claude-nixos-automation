---
description: "Task list for Self-Improving Claude Code System implementation"
---

# Tasks: Self-Improving Claude Code System

**Input**: Design documents from `/specs/001-source-artifact-architecture/`
**Prerequisites**: plan.md ✅, spec.md ✅

**Tests**: Included - Test-driven approach specified in Constitution Principle III

**Organization**: Tasks are grouped by major components (stages) to enable independent implementation and testing.

## Format: `[ID] [P?] [Component] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Component]**: Which major component this task belongs to (Core, PermLearn, MCP, Context, etc.)
- Include exact file paths in descriptions

## Path Conventions
- Repository root: `/home/guyfawkes/claude-nixos-automation/`
- Source code: `claude_automation/`
- Tests: `tests/`
- Scripts: `scripts/`
- Docs: `specs/001-source-artifact-architecture/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Development environment and project foundation

- [X] T001 Create devenv.nix with Python 3.13 configuration
- [X] T002 Configure poetry integration with auto-install in devenv.nix
- [X] T003 [P] Add development packages (ruff, mypy) to devenv.nix
- [X] T004 [P] Define devenv scripts: test, test-fast, lint, format, quality
- [X] T005 Configure pre-commit hooks in devenv.nix (ruff, mypy, artifact detection)
- [X] T006 [P] Set environment variables in devenv.nix (PYTHONPATH, CLAUDE_AUTOMATION_DEV)
- [X] T007 Test devenv shell activation (<1s performance requirement)
- [X] T008 Create .specify/memory/research.md with algorithm decisions (Phase 0 research output)

**Checkpoint**: Development environment ready - can begin implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core architecture that MUST be complete before ANY learning components can be implemented

**⚠️ CRITICAL**: No Tier 1/2/3 learning work can begin until this phase is complete

### Core Architecture Tasks

- [X] T009 [P] [Core] Add 30+ new Pydantic schemas to claude_automation/schemas.py (PermissionApprovalEntry, PermissionPattern, MCPServerRecommendation, ContextAccessLog, etc.)
- [X] T010 [P] [Core] Create claude_automation/validators/permission_validator.py with syntax checking (newlines, heredocs, length ≤200)
- [X] T011 [P] [Core] Implement tiered validation in claude_automation/validators/content_validator.py (FAIL vs WARN)
- [X] T012 [Core] Add MANUAL_SOURCES and GENERATED_ARTIFACTS declarations to claude_automation/generators/base_generator.py
- [X] T013 [Core] Implement _validate_declarations() in base_generator.py with overlap check
- [X] T014 [Core] Implement read_source() in base_generator.py with warning for undeclared sources
- [X] T015 [Core] Implement write_artifact() in base_generator.py with source protection and header generation
- [X] T016 [Core] Implement _generate_header() in base_generator.py for HTML comment headers
- [X] T017 [Core] Update claude_automation/generators/system_generator.py to use new BaseGenerator API
- [X] T018 [Core] Update claude_automation/generators/permissions_generator.py to declare sources/artifacts

### Core Tests (TDD - Write and Verify Fail FIRST)

- [X] T019 [P] [Core] Unit test: test_cannot_write_to_source in tests/unit/test_base_generator.py
- [X] T020 [P] [Core] Unit test: test_artifact_has_header in tests/unit/test_base_generator.py
- [X] T021 [P] [Core] Unit test: test_permission_validation in tests/unit/test_validators.py
- [X] T022 [P] [Core] Unit test: test_content_validation in tests/unit/test_validators.py
- [X] T023 [P] [Core] Integration test: test_dynamic_context_preserves_policies in tests/integration/test_generation.py

### Migration & Git Hooks

- [X] T024 [Core] Create scripts/migrate-add-headers.sh with idempotent header addition
- [X] T025 [Core] Test migration script on existing CLAUDE.md files
- [X] T026 [Core] Update .git/hooks/pre-commit with artifact warnings and interactive prompt

### Documentation (Foundational)

- [X] T027 [P] Create specs/001-source-artifact-architecture/data-model.md documenting all 45 Pydantic schemas
- [X] T028 [P] Create specs/001-source-artifact-architecture/contracts/analyzers.md with interfaces for 8 analyzers
- [X] T029 [P] Create specs/001-source-artifact-architecture/contracts/generators.md with BaseGenerator contract
- [X] T030 [P] Create specs/001-source-artifact-architecture/contracts/engine.md with AdaptiveSystemEngine contract
- [X] T031 Create specs/001-source-artifact-architecture/quickstart.md (user guide and developer guide)

**Checkpoint**: Core architecture ready - learning components can now be implemented in parallel

---

## Phase 3: Tier 1 Self-Improvement - Permission Learning (Priority: P1) 🎯

**Goal**: Learn permission patterns from approval history and suggest generalizations

**Independent Test**: Run approval tracker → detect patterns → suggest → apply → verify in settings.local.json

### Tests for Permission Learning (TDD - Write FIRST)

- [X] T032 [P] [PermLearn] Unit test: test_approval_logging in tests/unit/test_approval_tracker.py
- [X] T033 [P] [PermLearn] Unit test: test_pattern_detection in tests/unit/test_permission_patterns.py
- [X] T034 [P] [PermLearn] Unit test: test_confidence_scoring in tests/unit/test_permission_patterns.py
- [X] T035 [P] [PermLearn] Integration test: test_approval_to_pattern_to_suggestion in tests/integration/test_learning_cycle.py

### Implementation for Permission Learning

- [X] T036 [P] [PermLearn] Create claude_automation/analyzers/approval_tracker.py with JSONL logging
- [X] T037 [P] [PermLearn] Implement log_approval() and get_recent_approvals() in approval_tracker.py
- [X] T038 [PermLearn] Create claude_automation/analyzers/permission_pattern_detector.py
- [X] T039 [PermLearn] Implement PATTERN_DETECTORS in permission_pattern_detector.py (git_read_only, pytest, ruff, modern_cli, project_full_access)
- [X] T040 [PermLearn] Implement detect_patterns() with statistical analysis (min 3 occurrences, 30-day window)
- [X] T041 [PermLearn] Implement confidence scoring in permission_pattern_detector.py
- [X] T042 [PermLearn] Create claude_automation/generators/intelligent_permissions_generator.py
- [X] T043 [PermLearn] Implement generate_with_learning() with interactive prompts
- [X] T044 [PermLearn] Implement _prompt_for_pattern() for user approval flow
- [X] T045 [PermLearn] Implement _apply_patterns() to update settings.local.json
- [X] T046 [PermLearn] Create scripts/update-permissions-with-learning.py CLI entry point

**Checkpoint**: Permission learning functional and independently testable

---

## Phase 4: Tier 1 Self-Improvement - Global MCP Optimization (Priority: P1) 🎯

**Goal**: Analyze MCP servers across ALL projects and optimize utilization

**Independent Test**: Run global discovery → aggregate usage → calculate ROI → generate recommendations

### Tests for Global MCP Optimization (TDD - Write FIRST)

- [X] T047 [P] [MCP] Unit test: test_global_mcp_discovery in tests/unit/test_global_mcp_analyzer.py
- [X] T048 [P] [MCP] Unit test: test_global_usage_aggregation in tests/unit/test_global_mcp_analyzer.py
- [X] T049 [P] [MCP] Unit test: test_underutilized_detection in tests/unit/test_global_mcp_analyzer.py
- [X] T050 [P] [MCP] Integration test: test_cross_project_analysis in tests/integration/test_cross_project.py

### Implementation for Global MCP Optimization

- [X] T051 [P] [MCP] Create claude_automation/analyzers/global_mcp_analyzer.py
- [X] T052 [MCP] Implement discover_projects() to scan for .claude/mcp.json files system-wide
- [X] T053 [MCP] Implement _analyze_project() to run MCPUsageAnalyzer per project
- [X] T054 [MCP] Implement project aggregation logic in analyze_all_projects()
- [X] T055 [MCP] Add token consumption tracking to MCPUsageAnalyzer (session log parsing)
- [X] T056 [MCP] Implement ROI calculation: (invocations / tokens * 1000)
- [X] T057 [MCP] Implement utilization metrics: loaded vs used sessions
- [X] T058 [MCP] Implement _build_report() with global vs project-specific server distinction
- [X] T059 [MCP] Implement generate_summary() for rebuild output
- [X] T060 [MCP] Test with user's whatsapp-mcp and sunsama-mcp projects (integration test simulates this)

**Checkpoint**: Global MCP analysis functional and independently testable

---

## Phase 5: Tier 1 Self-Improvement - Context Optimization (Priority: P1) 🎯

**Goal**: Track CLAUDE.md section usage and optimize context relevance

**Independent Test**: Run context tracker → identify noise → calculate effective ratio → suggest pruning

### Tests for Context Optimization (TDD - Write FIRST)

- [X] T061 [P] [Context] Unit test: test_section_tracking in tests/unit/test_context_optimizer.py
- [X] T062 [P] [Context] Unit test: test_noise_detection in tests/unit/test_context_optimizer.py
- [X] T063 [P] [Context] Unit test: test_effective_ratio_calculation in tests/unit/test_context_optimizer.py

### Implementation for Context Optimization

- [X] T064 [P] [Context] Create claude_automation/analyzers/context_optimizer.py
- [X] T065 [Context] Implement ContextUsageTracker for section access logging
- [X] T066 [Context] Implement calculate_effective_context_ratio()
- [X] T067 [Context] Implement identify_noise_sections() for loaded but never referenced content
- [X] T068 [Context] Implement detect_context_gaps() for frequently-queried missing info
- [X] T069 [Context] Implement reordering algorithm by access frequency
- [X] T070 [Context] Implement generate_quick_reference() from hot paths
- [X] T071 [Context] Implement analyze() to generate optimization suggestions

**Checkpoint**: Context optimization functional and independently testable

---

## Phase 6: Tier 2 Self-Improvement - Workflow Detection (Priority: P2)

**Goal**: Detect repeated slash command patterns and suggest workflow bundling

**Independent Test**: Run workflow detector → log sequences → detect patterns → suggest bundling

### Tests for Workflow Detection (TDD - Write FIRST)

- [ ] T072 [P] [Workflow] Unit test: test_workflow_detection in tests/unit/test_workflow_detector.py
- [ ] T073 [P] [Workflow] Unit test: test_sequence_patterns in tests/unit/test_workflow_detector.py
- [ ] T074 [P] [Workflow] Unit test: test_completion_rate_calculation in tests/unit/test_workflow_detector.py

### Implementation for Workflow Detection

- [ ] T075 [P] [Workflow] Create claude_automation/analyzers/workflow_detector.py
- [ ] T076 [Workflow] Implement slash command logging to ~/.claude/workflow-analytics.jsonl
- [ ] T077 [Workflow] Implement sequence detection for multi-command patterns
- [ ] T078 [Workflow] Implement completion rate and success metrics calculation
- [ ] T079 [Workflow] Implement detect_patterns() with min 3 occurrences threshold
- [ ] T080 [Workflow] Implement workflow bundling suggestions

**Checkpoint**: Workflow detection functional and independently testable

---

## Phase 7: Tier 2 Self-Improvement - Instruction Effectiveness (Priority: P2)

**Goal**: Track policy adherence and suggest instruction improvements

**Independent Test**: Run effectiveness tracker → detect violations → calculate scores → suggest rewording

### Tests for Instruction Effectiveness (TDD - Write FIRST)

- [ ] T081 [P] [Instruction] Unit test: test_violation_detection in tests/unit/test_instruction_tracker.py
- [ ] T082 [P] [Instruction] Unit test: test_effectiveness_score in tests/unit/test_instruction_tracker.py
- [ ] T083 [P] [Instruction] Unit test: test_ambiguity_identification in tests/unit/test_instruction_tracker.py

### Implementation for Instruction Effectiveness

- [ ] T084 [P] [Instruction] Create claude_automation/analyzers/instruction_tracker.py
- [ ] T085 [Instruction] Implement InstructionEffectivenessTracker for policy monitoring
- [ ] T086 [Instruction] Implement policy violation detection
- [ ] T087 [Instruction] Implement effectiveness scoring per instruction (compliant_sessions / total_sessions)
- [ ] T088 [Instruction] Implement ambiguity identification (<70% compliance threshold)
- [ ] T089 [Instruction] Implement suggest_improvements() with rewording suggestions

**Checkpoint**: Instruction effectiveness tracking functional and independently testable

---

## Phase 8: Tier 3 Self-Improvement - Cross-Project Transfer (Priority: P3)

**Goal**: Detect project archetypes and transfer knowledge between similar projects

**Independent Test**: Run archetype detector → classify project → find transfer opportunities → apply patterns

### Tests for Cross-Project Transfer (TDD - Write FIRST)

- [ ] T090 [P] [CrossProject] Unit test: test_archetype_detection in tests/unit/test_project_archetype_detector.py
- [ ] T091 [P] [CrossProject] Unit test: test_pattern_transfer in tests/unit/test_project_archetype_detector.py
- [ ] T092 [P] [CrossProject] Integration test: test_new_project_pattern_application in tests/integration/test_cross_project.py

### Implementation for Cross-Project Transfer

- [ ] T093 [P] [CrossProject] Create claude_automation/analyzers/project_archetype_detector.py
- [ ] T094 [CrossProject] Implement archetype detection (Python/pytest, TypeScript/vitest, Rust/cargo, etc.)
- [ ] T095 [CrossProject] Implement knowledge base building per archetype
- [ ] T096 [CrossProject] Implement find_transfer_opportunities()
- [ ] T097 [CrossProject] Implement transfer_pattern() to apply patterns to new projects

**Checkpoint**: Cross-project transfer functional and independently testable

---

## Phase 9: Tier 3 Self-Improvement - Meta-Learning (Priority: P3)

**Goal**: Track learning system effectiveness and self-calibrate thresholds

**Independent Test**: Run meta-learner → track acceptance rates → adjust thresholds → generate health report

### Tests for Meta-Learning (TDD - Write FIRST)

- [ ] T098 [P] [MetaLearn] Unit test: test_meta_learning in tests/unit/test_meta_learner.py
- [ ] T099 [P] [MetaLearn] Unit test: test_threshold_adjustment in tests/unit/test_meta_learner.py
- [ ] T100 [P] [MetaLearn] Unit test: test_learning_health_metrics in tests/unit/test_meta_learner.py

### Implementation for Meta-Learning

- [ ] T101 [P] [MetaLearn] Create claude_automation/analyzers/meta_learner.py
- [ ] T102 [MetaLearn] Implement effectiveness tracking (suggestion acceptance rate, false positive rate)
- [ ] T103 [MetaLearn] Implement acceptance rate monitoring
- [ ] T104 [MetaLearn] Implement threshold adjustment algorithms from research.md
- [ ] T105 [MetaLearn] Implement confidence scoring calibration
- [ ] T106 [MetaLearn] Implement get_health_metrics() for diagnostics

**Checkpoint**: Meta-learning functional and independently testable

---

## Phase 10: Integration - Adaptive System Engine (Priority: P1) 🎯 CRITICAL

**Goal**: Unified coordinator for all 8 learners with consolidated reporting

**Independent Test**: Run full learning cycle → collect from all learners → present report → apply improvements

### Tests for Adaptive System Engine (TDD - Write FIRST)

- [ ] T107 [P] [Engine] Contract test: test_analyzer_contracts in tests/contract/test_analyzer_contracts.py
- [ ] T108 [P] [Engine] Contract test: test_generator_contracts in tests/contract/test_generator_contracts.py
- [ ] T109 [P] [Engine] Contract test: test_engine_contract in tests/contract/test_engine_contract.py
- [X] T110 [P] [Engine] Integration test: test_full_learning_cycle in tests/integration/test_learning_cycle.py
- [ ] T111 [P] [Engine] Integration test: test_rebuild_integration in tests/integration/test_rebuild_integration.py

### Implementation for Adaptive System Engine

- [X] T112 [Engine] Create claude_automation/core/adaptive_system_engine.py
- [X] T113 [Engine] Implement AdaptiveSystemEngine class with 8 learner initialization
- [X] T114 [P] [Engine] Implement _analyze_permissions() method
- [X] T115 [P] [Engine] Implement _analyze_mcp_servers() method (using GlobalMCPAnalyzer)
- [X] T116 [P] [Engine] Implement _analyze_context() method
- [X] T117 [P] [Engine] Implement _analyze_workflows() method
- [X] T118 [P] [Engine] Implement _analyze_instructions() method
- [X] T119 [P] [Engine] Implement _analyze_cross_project() method
- [X] T120 [P] [Engine] Implement _analyze_meta_learning() method
- [X] T121 [Engine] Implement _build_report() with prioritization
- [X] T122 [Engine] Implement _present_report() formatting
- [X] T123 [Engine] Implement _collect_approvals() interactive flow ✅ **FIXED 2025-10-17** - Now fully interactive
- [X] T124 [Engine] Implement _apply_improvements() dispatcher ⚠️ **PARTIAL** - Framework done, file modifications TODO
- [X] T125 [Engine] Implement _update_meta_learning() feedback loop
- [X] T126 [Engine] Implement run_full_learning_cycle() orchestration

### CLI Entry Points

- [X] T127 [P] [Engine] Create scripts/run-adaptive-learning.py with argparse (--interactive, --all-components, --dry-run)
- [X] T128 [P] [Engine] Add error handling and logging to run-adaptive-learning.py
- [X] T129 [P] [Engine] Create help text and usage examples for run-adaptive-learning.py

### Rebuild Integration

- [ ] T130 [Engine] Update ~/nixos-config/rebuild-nixos with learning cycle integration
- [ ] T131 [Engine] Test full workflow: rebuild → learn → approve → apply
- [ ] T132 [Engine] Verify backward compatibility (rebuild still works without learning)

**Checkpoint**: All learning components integrated and orchestrated

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, documentation, and validation

### Performance & Quality

- [ ] T133 [P] Performance test: verify validation overhead <1s per generator
- [ ] T134 [P] Performance test: verify full learning cycle <10s
- [ ] T135 [P] Performance test: verify global MCP scan <5s for 10 projects
- [ ] T136 [P] Performance test: verify test suite <30s
- [ ] T137 [P] Performance test: verify memory usage <100MB for learning cycle
- [ ] T138 [P] Code coverage: verify 90%+ test coverage for new code

### Documentation

- [ ] T139 [P] Update README.md with self-improvement features overview
- [ ] T140 [P] Generate API documentation for all 8 analyzers
- [ ] T141 [P] Document devenv usage in quickstart.md
- [ ] T142 [P] Create migration guide for existing deployments

### Final Validation

- [ ] T143 Run AC-1 through AC-14 validation from spec.md
- [ ] T144 Run quickstart.md validation (user guide steps)
- [ ] T145 Code cleanup and refactoring
- [ ] T146 Security review: permission validation, injection prevention
- [ ] T147 Final integration test: complete rebuild with all learners

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all learning components
- **Tier 1 Learning (Phases 3-5)**: All depend on Foundational phase completion
  - Phase 3 (Permission Learning), Phase 4 (MCP), Phase 5 (Context) can run in parallel
- **Tier 2 Learning (Phases 6-7)**: Depend on Foundational phase completion
  - Phase 6 (Workflow), Phase 7 (Instruction) can run in parallel
- **Tier 3 Learning (Phases 8-9)**: Depend on Foundational phase completion
  - Phase 8 (Cross-Project), Phase 9 (Meta-Learning) can run in parallel
- **Integration (Phase 10)**: Depends on ALL learning components (Phases 3-9) being complete
- **Polish (Phase 11)**: Depends on Integration completion

### Component Dependencies

- **Core Architecture**: BLOCKS all other components - must complete first
- **Permission Learning**: Independent after Core - can start immediately
- **Global MCP Optimization**: Independent after Core - can start immediately
- **Context Optimization**: Independent after Core - can start immediately
- **Workflow Detection**: Independent after Core - can start immediately
- **Instruction Effectiveness**: Independent after Core - can start immediately
- **Cross-Project Transfer**: Independent after Core - can start immediately
- **Meta-Learning**: Independent after Core - can start immediately
- **Adaptive System Engine**: Depends on ALL 8 learners being complete

### Within Each Component

- Tests MUST be written and FAIL before implementation (TDD)
- Schemas before analyzers
- Analyzers before generators
- Generators before CLI scripts
- Core implementation before integration
- Component complete before moving to Integration phase

### Parallel Opportunities

- **Phase 1 (Setup)**: Tasks T001-T008 can run in parallel (marked [P])
- **Phase 2 (Foundational)**:
  - Tasks T009-T011 (schemas, validators) can run in parallel
  - Tasks T019-T023 (tests) can run in parallel after schemas defined
  - Tasks T027-T031 (documentation) can run in parallel
- **Phases 3-9 (All Learning Components)**: Can ALL run in parallel once Phase 2 completes
  - 8 independent developers could work on 8 components simultaneously
- **Within each component**: Tests marked [P] can run in parallel
- **Phase 11 (Polish)**: Tasks T133-T142 can run in parallel (marked [P])

---

## Parallel Example: Tier 1 Learning Components

Once Foundational phase (Phase 2) completes, these can start simultaneously:

```bash
# Developer A: Permission Learning
Tasks: T032-T046 (Phase 3)

# Developer B: Global MCP Optimization
Tasks: T047-T060 (Phase 4)

# Developer C: Context Optimization
Tasks: T061-T071 (Phase 5)
```

Each component is independently testable and deliverable.

---

## Implementation Strategy

### MVP First (Core + Permission Learning)

1. Complete Phase 1: Setup (devenv environment)
2. Complete Phase 2: Foundational (CRITICAL - blocks all components)
3. Complete Phase 3: Permission Learning (first Tier 1 component)
4. Complete Phase 10: Integration (minimal - just permission learning)
5. **STOP and VALIDATE**: Test permission learning end-to-end
6. Deploy/demo if ready

### Incremental Delivery (Add Learning Components)

1. Complete Setup + Foundational → Core ready
2. Add Permission Learning → Test independently → Deploy/Demo (MVP!)
3. Add Global MCP Optimization → Test independently → Deploy/Demo
4. Add Context Optimization → Test independently → Deploy/Demo
5. Add Workflow Detection → Test independently → Deploy/Demo
6. Add Instruction Effectiveness → Test independently → Deploy/Demo
7. Add Cross-Project Transfer → Test independently → Deploy/Demo
8. Add Meta-Learning → Test independently → Deploy/Demo
9. Full Integration → Test all components together → Deploy/Demo

### Parallel Team Strategy (8 developers)

With full team:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Once Foundational is done:
   - Developer 1: Permission Learning (Phase 3)
   - Developer 2: Global MCP Optimization (Phase 4)
   - Developer 3: Context Optimization (Phase 5)
   - Developer 4: Workflow Detection (Phase 6)
   - Developer 5: Instruction Effectiveness (Phase 7)
   - Developer 6: Cross-Project Transfer (Phase 8)
   - Developer 7: Meta-Learning (Phase 9)
   - Developer 8: Integration prep (Phase 10 setup)
3. Components complete independently, then integrate in Phase 10

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe to parallelize
- **[Component] label**: Maps task to specific component for traceability
- Each component should be independently completable and testable
- **TDD approach**: Verify tests fail before implementing (Constitution Principle III)
- Commit after each task or logical group
- Stop at any checkpoint to validate component independently
- **Performance budgets**: <1s validation, <10s full cycle, <100MB memory
- **Constitution compliance**: All 6 principles verified in plan.md
- **Backward compatibility**: Existing workflows must continue working

---

## Estimated Effort

**Total**: 46-67 hours

- **Phase 1 (Setup)**: 1-2h
- **Phase 2 (Foundational)**: 10-15h (CRITICAL PATH)
- **Phase 3 (Permission Learning)**: 5-7h
- **Phase 4 (MCP Optimization)**: 5-7h
- **Phase 5 (Context Optimization)**: 5-6h
- **Phase 6 (Workflow Detection)**: 5-6h
- **Phase 7 (Instruction Effectiveness)**: 5-6h
- **Phase 8 (Cross-Project Transfer)**: 3-4h
- **Phase 9 (Meta-Learning)**: 2-4h
- **Phase 10 (Integration)**: 5-10h
- **Phase 11 (Polish)**: 2-3h

**Critical Path**: Setup → Foundational → Integration → Polish (minimum 19-30h)

**Parallel Potential**: With 8 developers, Tier 1/2/3 components can run simultaneously after Foundational completes, reducing wall-clock time significantly.
