---
description: "Implementation tasks for Documentation Governance and Cleanup System"
created: 2025-10-20
---

# Tasks: Documentation Governance and Cleanup System

**Input**: Design documents from `/specs/003-doc-governance-cleanup/`
**Prerequisites**: plan.md, spec.md, research.md

**Tests**: NO tests required - manual testing via script execution (utility scripts following nixos-config pattern)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Scripts: `scripts/` at repository root
- Documentation: Root and organized subdirectories (`.claude/sessions/`, `docs/architecture/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure for scripts

- [X] T001 Create scripts/ directory if not exists in repository root
- [X] T002 Create .claude/sessions/2025-10-archive/ directory structure
- [X] T003 Create docs/architecture/ directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational tasks needed - each user story is independent utility script

**⚠️ CRITICAL**: User stories can proceed independently after Setup

**Checkpoint**: Setup complete - user story implementation can begin in parallel

---

## Phase 3: User Story 1 - Add Missing Frontmatter to Existing Docs (Priority: P1) 🎯 MVP

**Goal**: Create a Python script that adds standardized YAML frontmatter to all markdown files following the nixos-config pattern

**Independent Test**: Run `python3 scripts/add-frontmatter.py` on the current repository. Verify all .md files receive proper frontmatter matching nixos-config schema (status, created, updated, type, lifecycle). Test passes if 100% of .md files have frontmatter and schema matches ~/nixos-config/scripts/add-frontmatter.py structure.

### Implementation for User Story 1

- [X] T004 [US1] Create scripts/add-frontmatter.py with YAML frontmatter schema (status, created, updated, type, lifecycle)
- [X] T005 [US1] Implement RULES list in scripts/add-frontmatter.py for file categorization patterns
- [X] T006 [US1] Add RULES entries for session notes: PHASE*.md → (archived, session-note, ephemeral, 2025-10)
- [X] T007 [US1] Add RULES entries for session notes: IMPLEMENTATION*.md → (archived, session-note, ephemeral, 2025-10)
- [X] T008 [US1] Add RULES entries for session notes: FINAL_STATUS.md, *_SUMMARY.md → (archived, session-note, ephemeral, 2025-10)
- [X] T009 [US1] Add RULES entries for architectural docs: CONSTITUTION.md → (active, architecture, persistent)
- [X] T010 [US1] Add RULES entries for guides: TESTING.md, README.md, CLAUDE.md → (active, guide/reference, persistent)
- [X] T011 [US1] Add RULES entries for root-level markdown files not matching patterns → default classification
- [X] T012 [US1] Implement frontmatter detection logic (check for '---' as first line)
- [X] T013 [US1] Implement frontmatter generation function with YAML formatting
- [X] T014 [US1] Implement file processing loop with skip logic for existing frontmatter
- [X] T015 [US1] Add color output using ANSI codes (✅ green for processed, ⏭️ yellow for skipped)
- [X] T016 [US1] Add summary statistics output (Processed: X, Skipped: Y)
- [X] T017 [US1] Add error handling with try/except for individual file failures
- [X] T018 [US1] Add UTF-8 encoding validation for markdown files
- [X] T019 [US1] Test script manually on repository, verify frontmatter added to all .md files

**Checkpoint**: At this point, User Story 1 should be fully functional - all markdown files should have standardized frontmatter

---

## Phase 4: User Story 2 - Clean Root Directory (Priority: P1)

**Goal**: Create a bash script that reorganizes documentation files from root into appropriate subdirectories based on frontmatter classification

**Independent Test**: Run the reorganization script. Verify root directory contains exactly 3-5 files (README.md, CLAUDE.md, TESTING.md, plus optionally LICENSE and CONTRIBUTING.md). Verify session notes moved to `.claude/sessions/2025-10-archive/` and architectural docs moved to `docs/architecture/`.

### Implementation for User Story 2

- [X] T020 [US2] Create scripts/reorganize-docs.sh with bash safety headers (set -euo pipefail)
- [X] T021 [US2] Add git repository validation check in scripts/reorganize-docs.sh
- [X] T022 [US2] Implement function to read frontmatter type and lifecycle from markdown files
- [X] T023 [US2] Add logic to move session notes (type=session-note) to .claude/sessions/2025-10-archive/ using git mv
- [X] T024 [US2] Add logic to move architectural docs (type=architecture) to docs/architecture/ using git mv
- [X] T025 [US2] Add exclusion list for files that must stay in root (README.md, CLAUDE.md, TESTING.md, LICENSE, CONTRIBUTING.md)
- [X] T026 [US2] Implement dry-run mode with --dry-run flag for testing moves
- [X] T027 [US2] Add verbose output showing each file being moved
- [X] T028 [US2] Add directory creation logic (mkdir -p) for destination directories
- [X] T029 [US2] Test script with --dry-run flag, verify correct file categorization
- [X] T030 [US2] Execute script to reorganize repository, verify root directory cleaned

**Checkpoint**: At this point, User Story 2 should be complete - root directory should contain only 3-5 essential files

---

## Phase 5: User Story 3 - Prevent Frontmatter-less Commits (Priority: P2)

**Goal**: Add pre-commit hook that blocks markdown files without frontmatter from being committed

**Independent Test**: Create a new markdown file without frontmatter and attempt to commit it. Verify the pre-commit hook blocks the commit with a clear error message containing the add-frontmatter.py command to run.

### Implementation for User Story 3

- [X] T031 [US3] Create scripts/check-frontmatter.py validation script
- [X] T032 [US3] Implement logic to read staged markdown files from git
- [X] T033 [US3] Add frontmatter detection for each staged .md file (check for '---' as first line)
- [X] T034 [US3] Add CLAUDE.md exclusion logic (auto-generated file)
- [X] T035 [US3] Implement error output with helpful message: "ERROR: Markdown files missing frontmatter: [files]. Run: python3 scripts/add-frontmatter.py"
- [X] T036 [US3] Add exit code logic (exit 1 if missing frontmatter, exit 0 if all valid)
- [X] T037 [US3] Add local hook entry to .pre-commit-config.yaml for check-markdown-frontmatter
- [X] T038 [US3] Configure hook to run on \.md$ files, exclude ^CLAUDE\.md$
- [X] T039 [US3] Set hook to use language: system and entry: python3 scripts/check-frontmatter.py
- [X] T040 [US3] Test hook by creating test .md file without frontmatter and attempting commit
- [X] T041 [US3] Test hook allows commit with valid frontmatter

**Checkpoint**: At this point, User Story 3 should be complete - pre-commit hook enforces frontmatter requirement

---

## Phase 6: User Story 4 - Automated Monthly Documentation Review (Priority: P3)

**Goal**: Create a review script that identifies stale documentation and outputs recommendations for archiving

**Independent Test**: Manually create test files with backdated frontmatter (draft from 60 days ago, ephemeral from 120 days ago) and run the review script. Verify it correctly identifies both files and outputs recommendations for archiving.

### Implementation for User Story 4

- [X] T042 [US4] Create scripts/review-docs-lifecycle.py scanner script
- [X] T043 [US4] Implement markdown file discovery using pathlib glob for all .md files
- [X] T044 [US4] Implement frontmatter parsing function to extract status, created, lifecycle fields
- [X] T045 [US4] Add date parsing logic to calculate age in days from created field
- [X] T046 [US4] Implement logic to flag draft docs with created date >30 days ago
- [X] T047 [US4] Implement logic to flag ephemeral docs with created date >90 days ago
- [X] T048 [US4] Skip persistent docs from age-based flagging (lifecycle=persistent)
- [X] T049 [US4] Implement formatted output with emojis (⚠️ for drafts >30 days, 🗄️ for ephemeral >90 days)
- [X] T050 [US4] Add recommendation text for each flagged file (Archive or update status for drafts, Move to archive for ephemeral)
- [X] T051 [US4] Add summary statistics (Total docs scanned, Drafts flagged, Ephemeral flagged)
- [X] T052 [US4] Test script with backdated frontmatter test files (draft=60 days, ephemeral=120 days)
- [X] T053 [US4] Verify script correctly identifies stale docs and outputs recommendations

**Checkpoint**: At this point, User Story 4 should be complete - monthly review automation ready

---

## Phase 7: User Story 5 - Star-Optimized README (Priority: P2)

**Goal**: Rewrite README.md following proven GitHub star-maximizing patterns to improve discoverability and conversion

**Independent Test**: Show the new README to 5 developers unfamiliar with the project. Measure time to comprehend value proposition (target: <10 seconds) and ask if they would star it (target: 4/5 yes).

### Implementation for User Story 5

- [X] T054 [US5] Review current README.md and extract essential content to preserve
- [X] T055 [US5] Create hero section (first 100-200 words) with value proposition: "Claude automation for NixOS that learns from your workflow and auto-configures permissions"
- [X] T056 [US5] Add badges section (test coverage 100%, code quality A+, license, actively maintained)
- [X] T057 [US5] Create visual architecture diagram showing 3-tier learning system (Permissions → Workflows → Archetypes) using Mermaid or ASCII art
- [X] T058 [US5] Write 2-minute quickstart section with exact commands (git clone → ./run-adaptive-learning.py)
- [X] T059 [US5] Create feature highlights section with benefits (not just feature list)
- [X] T060 [US5] Add contribution guide section or link to CONTRIBUTING.md
- [X] T061 [US5] Add "How It Works" section explaining the learning cycle
- [X] T062 [US5] Add "Use Cases" section with concrete examples
- [X] T063 [US5] Add "Why This Matters" section explaining problem solved
- [X] T064 [US5] Review README structure against high-star projects (nodebestpractices, home-manager)
- [X] T065 [US5] Verify value proposition comprehensible in <10 seconds (user testing with 5 developers)

**Checkpoint**: All user stories should now be independently functional - documentation governance system complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation updates

- [X] T066 [P] Update CLAUDE.md with documentation governance workflow instructions
- [X] T067 [P] Create MIGRATION_PLAN.md in specs/003-doc-governance-cleanup/ with execution order
- [X] T068 Verify all scripts are idempotent (safe to run multiple times)
- [X] T069 Verify all scripts have helpful error messages and color output
- [X] T070 Run complete workflow: add-frontmatter.py → reorganize-docs.sh → check-frontmatter.py → review-docs-lifecycle.py
- [X] T071 Validate success criteria: root contains 3-5 files, 100% frontmatter coverage, pre-commit hook blocks commits

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 (Phase 3)**: Depends on Setup completion - Foundation for all other stories
- **User Story 2 (Phase 4)**: Depends on User Story 1 (needs frontmatter to exist for reorganization)
- **User Story 3 (Phase 5)**: Can start after Setup - Independent of US1/US2 (validation script)
- **User Story 4 (Phase 6)**: Can start after Setup - Independent of other stories (read-only scanner)
- **User Story 5 (Phase 7)**: Can start after Setup - Independent of other stories (README rewrite)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories - 🎯 MVP
- **User Story 2 (P1)**: Depends on User Story 1 completion (reorganization needs frontmatter)
- **User Story 3 (P2)**: Independent - can run parallel with US1/US2 after Setup
- **User Story 4 (P3)**: Independent - can run parallel with all other stories after Setup
- **User Story 5 (P2)**: Independent - can run parallel with all other stories after Setup

### Within Each User Story

- User Story 1: Linear task sequence (create script → add RULES → implement logic → test)
- User Story 2: Depends on US1 frontmatter being in place
- User Story 3: Linear task sequence (create validator → add hook config → test)
- User Story 4: Linear task sequence (create scanner → add logic → test)
- User Story 5: Linear task sequence (extract content → write sections → validate)

### Parallel Opportunities

- **After Setup completes**: User Stories 3, 4, 5 can all start in parallel
- **After User Story 1 completes**: User Story 2 can start while 3, 4, 5 continue
- Within Phase 8 (Polish): Tasks T066 and T067 can run in parallel

---

## Parallel Example: Initial Work

```bash
# After Setup (Phase 1) completes, launch these user stories in parallel:
Task: "Create scripts/check-frontmatter.py validation script" (US3)
Task: "Create scripts/review-docs-lifecycle.py scanner script" (US4)
Task: "Review current README.md and extract essential content" (US5)

# User Story 1 must complete first for User Story 2 to proceed
# But US3, US4, US5 can all proceed independently
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (add-frontmatter.py)
3. **STOP and VALIDATE**: Run script, verify 100% frontmatter coverage
4. Complete Phase 4: User Story 2 (reorganize-docs.sh)
5. **STOP and VALIDATE**: Verify root directory cleaned to 3-5 files
6. This delivers core value: standardized frontmatter + clean repository

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add User Story 1 → Test independently → ✅ MVP Core (frontmatter standardization)
3. Add User Story 2 → Test independently → ✅ Clean repository structure
4. Add User Story 3 → Test independently → ✅ Enforcement via pre-commit
5. Add User Story 5 → Test independently → ✅ GitHub discoverability boost
6. Add User Story 4 → Test independently → ✅ Maintenance automation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
   - Developer A: User Story 1 (blocks US2, critical path)
   - Developer B: User Story 3 (independent)
   - Developer C: User Story 5 (independent)
3. Once US1 completes:
   - Developer A: User Story 2 (depends on US1)
   - Developer B: User Story 4 (independent)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests are manual (not automated pytest) - run scripts and verify output
- Scripts follow nixos-config pattern (idempotent, color output, summary stats)
- All file moves use `git mv` to preserve history
- CLAUDE.md explicitly excluded from all operations
- Verify each checkpoint independently before proceeding
- Avoid: modifying core adaptive learning code, breaking git history

---

## Task Summary

- **Total Tasks**: 71
- **User Story 1 (P1)**: 16 tasks - Foundation for frontmatter system
- **User Story 2 (P1)**: 11 tasks - Repository reorganization
- **User Story 3 (P2)**: 11 tasks - Pre-commit enforcement
- **User Story 4 (P3)**: 12 tasks - Monthly review automation
- **User Story 5 (P2)**: 12 tasks - README optimization
- **Setup**: 3 tasks
- **Polish**: 6 tasks
- **Parallel Opportunities**: High - US3, US4, US5 all independent after Setup
- **MVP Scope**: User Stories 1 + 2 (27 tasks) - delivers standardized frontmatter + clean repository
