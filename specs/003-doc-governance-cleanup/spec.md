# Feature Specification: Documentation Governance and Cleanup System

**Feature Branch**: `003-doc-governance-cleanup`
**Created**: 2025-10-20
**Status**: Draft
**Input**: Implement a documentation governance and cleanup system that extends the existing nixos-config and ai-project-orchestration YAML frontmatter approach to claude-nixos-automation

## User Scenarios & Testing

### User Story 1 - Add Missing Frontmatter to Existing Docs (Priority: P1)

As a developer returning to the project after 3 months, I need all markdown files to have standardized YAML frontmatter so I can quickly identify which docs are current (active/persistent) vs outdated session notes (ephemeral/archived), allowing me to find relevant documentation in under 30 seconds instead of reading through 15+ root-level files.

**Why this priority**: Foundation for all other features. Without frontmatter, automated lifecycle management is impossible.

**Independent Test**: Run the add-frontmatter.py script on the current repository. Verify that all markdown files receive proper frontmatter matching the nixos-config schema (status, created, updated, type, lifecycle fields). Test passes if 100% of .md files have frontmatter and the schema exactly matches ~/nixos-config/scripts/add-frontmatter.py structure.

**Acceptance Scenarios**:

1. **Given** repository with 15+ root-level markdown files without frontmatter, **When** developer runs `python3 scripts/add-frontmatter.py`, **Then** all files receive frontmatter with correct classification (PHASE*.md as ephemeral/archived, README.md as persistent/active)

2. **Given** file already has frontmatter, **When** script runs again, **Then** file is skipped with message "⏭️  Skipping (has frontmatter): [file]"

3. **Given** session note file like IMPLEMENTATION_COMPLETE.md, **When** frontmatter is added, **Then** it receives status=archived, type=session-note, lifecycle=ephemeral, created=2025-10

---

### User Story 2 - Clean Root Directory (Priority: P1)

As a first-time GitHub visitor evaluating this project for a star, I need a clean root directory with only essential files (README.md, CLAUDE.md, TESTING.md) so I can immediately understand the project value in under 10 seconds without being overwhelmed by 15+ markdown files.

**Why this priority**: Critical for GitHub star conversion. Messy root = immediate bounce.

**Independent Test**: Run the reorganization script. Verify root directory contains exactly 3-5 files (README.md, CLAUDE.md, TESTING.md, plus optionally LICENSE and CONTRIBUTING.md). Verify session notes moved to `.claude/sessions/2025-10-archive/` and architectural docs moved to `docs/architecture/`.

**Acceptance Scenarios**:

1. **Given** 15 markdown files in root, **When** reorganization runs, **Then** only README.md, CLAUDE.md, TESTING.md remain in root (3-5 files total)

2. **Given** PHASE*.md and IMPLEMENTATION*.md files, **When** reorganization runs, **Then** they move to `.claude/sessions/2025-10-archive/` with preserved filenames

3. **Given** CONSTITUTION.md or architectural docs, **When** reorganization runs, **Then** they move to `docs/architecture/` preserving content

---

### User Story 3 - Prevent Frontmatter-less Commits (Priority: P2)

As a developer creating new documentation, I need a pre-commit hook that blocks markdown files without frontmatter so I don't accidentally pollute the repository with untracked documentation, receiving a helpful error message showing exactly how to add frontmatter.

**Why this priority**: Enforcement mechanism. Prevents regression after initial cleanup.

**Independent Test**: Create a new markdown file without frontmatter and attempt to commit it. Verify the pre-commit hook blocks the commit with a clear error message containing the add-frontmatter.py command to run.

**Acceptance Scenarios**:

1. **Given** new file `docs/new-guide.md` without frontmatter, **When** developer runs `git commit`, **Then** commit is blocked with message "ERROR: Markdown files missing frontmatter: docs/new-guide.md. Run: python3 scripts/add-frontmatter.py"

2. **Given** markdown file with valid frontmatter, **When** developer commits, **Then** commit succeeds without blocking

3. **Given** non-markdown file (Python, shell script), **When** developer commits, **Then** frontmatter check is skipped

---

### User Story 4 - Automated Monthly Documentation Review (Priority: P3)

As a project maintainer, I need an automated monthly review script that identifies stale documentation (draft >30 days, ephemeral >90 days) so I can archive or update outdated docs, receiving a formatted report with recommendations.

**Why this priority**: Maintenance automation. Prevents long-term documentation debt accumulation.

**Independent Test**: Manually create test files with backdated frontmatter (draft from 60 days ago, ephemeral from 120 days ago) and run the review script. Verify it correctly identifies both files and outputs recommendations for archiving.

**Acceptance Scenarios**:

1. **Given** draft doc with created=2025-08-15 (>30 days), **When** review script runs on 2025-10-20, **Then** script outputs "⚠️  Draft older than 30 days: docs/planning/old-plan.md (created: 2025-08-15) - Recommend: Archive or update status"

2. **Given** ephemeral doc with created=2025-07-01 (>90 days), **When** review script runs, **Then** script outputs "🗄️  Ephemeral doc older than 90 days: .claude/sessions/old-notes.md - Recommend: Archive to .claude/sessions/archive/2025-07/"

3. **Given** active persistent doc from 365 days ago, **When** review script runs, **Then** doc is not flagged (persistent docs don't expire)

---

### User Story 5 - Star-Optimized README (Priority: P2)

As a GitHub user discovering this project through search or trending, I need a README that communicates the project value in under 10 seconds with a hero section, clear value proposition, visual architecture diagram, and 2-minute quickstart so I can immediately understand if this project solves my problem and decide whether to star it.

**Why this priority**: High-impact for discoverability. Current README doesn't follow proven star-maximizing patterns.

**Independent Test**: Show the new README to 5 developers unfamiliar with the project. Measure time to comprehend value proposition (target: <10 seconds) and ask if they would star it (target: 4/5 yes).

**Acceptance Scenarios**:

1. **Given** developer lands on README, **When** they read first 200 words, **Then** they understand "Claude automation for NixOS that learns from your workflow and auto-configures permissions"

2. **Given** README with architecture diagram (Mermaid or ASCII), **When** developer views it, **Then** they understand the 3-tier learning system in under 30 seconds

3. **Given** quickstart section, **When** developer follows steps, **Then** they can run `./run-adaptive-learning.py` successfully in under 2 minutes

4. **Given** badges section, **When** developer views it, **Then** they see test coverage (100%), code quality (A+), and actively maintained status

---

### Edge Cases

- What happens when a markdown file is in a directory not covered by RULES patterns? (Should fail gracefully with message suggesting manual frontmatter)
- How does the system handle markdown files with malformed existing frontmatter? (Attempt to parse, warn user if invalid YAML)
- What if session notes directory `.claude/sessions/2025-10-archive/` doesn't exist? (Create it automatically with mkdir -p)
- How to handle merge conflicts in frontmatter `updated` field? (Accept newer timestamp, or use git conflict markers)
- What if user runs add-frontmatter.py on wrong repository (e.g., ~/nixos-config)? (Detect repo via git remote, warn if not claude-nixos-automation)

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a Python script `scripts/add-frontmatter.py` that processes all markdown files in the repository
- **FR-002**: Script MUST follow the exact pattern from `~/nixos-config/scripts/add-frontmatter.py` with RULES list for categorization
- **FR-003**: Frontmatter schema MUST exactly match nixos-config: `status`, `created`, `updated`, `type`, `lifecycle` fields (no additional fields, no missing fields)
- **FR-004**: Script MUST classify session notes (PHASE*.md, IMPLEMENTATION*.md, FINAL_STATUS.md, *_SUMMARY.md) as `status: archived`, `type: session-note`, `lifecycle: ephemeral`
- **FR-005**: Script MUST classify architectural docs (CONSTITUTION.md, CLAUDE_ORCHESTRATION.md-style) as `status: active`, `type: architecture`, `lifecycle: persistent`
- **FR-006**: Script MUST classify guides (TESTING.md, quickstarts) as `status: active`, `type: guide`, `lifecycle: persistent`
- **FR-007**: Script MUST skip files that already have frontmatter (check for `---` as first line)
- **FR-008**: Script MUST use current date for `updated` field and either provided or current date for `created` field
- **FR-009**: System MUST provide a reorganization script `scripts/reorganize-docs.sh` that moves files based on frontmatter classification
- **FR-010**: Reorganization script MUST move session notes to `.claude/sessions/2025-10-archive/` preserving filenames
- **FR-011**: Reorganization script MUST move architectural docs to `docs/architecture/` preserving filenames
- **FR-012**: Reorganization script MUST NOT move README.md, CLAUDE.md, or TESTING.md from root
- **FR-013**: System MUST add pre-commit hook to `.pre-commit-config.yaml` that validates frontmatter presence
- **FR-014**: Pre-commit hook MUST block commits containing markdown files without frontmatter
- **FR-015**: Pre-commit hook MUST provide helpful error message: "ERROR: Markdown files missing frontmatter: [files]. Run: python3 scripts/add-frontmatter.py"
- **FR-016**: System MUST provide monthly review script `scripts/review-docs-lifecycle.py` that scans all markdown files
- **FR-017**: Review script MUST flag draft docs with created date >30 days ago
- **FR-018**: Review script MUST flag ephemeral docs with created date >90 days ago
- **FR-019**: Review script MUST output recommendations in formatted text (emojis optional: ⚠️ for drafts, 🗄️ for ephemeral)
- **FR-020**: System MUST completely rewrite README.md following proven GitHub star optimization patterns
- **FR-021**: README.md MUST include hero section with value proposition comprehensible in <10 seconds (first 100-200 words)
- **FR-022**: README.md MUST include visual architecture diagram (Mermaid or ASCII art) showing 3-tier learning system
- **FR-023**: README.md MUST include badges for test coverage, code quality, license, and maintenance status
- **FR-024**: README.md MUST include 2-minute quickstart section with exact commands to run
- **FR-025**: README.md MUST include feature highlights section with benefits (not just features list)
- **FR-026**: README.md MUST include contribution guide section or link to CONTRIBUTING.md
- **FR-027**: System MUST provide migration plan document `specs/003-doc-governance-cleanup/MIGRATION_PLAN.md` with step-by-step execution order

### Key Entities

- **Markdown File**: Represents a .md file with attributes: path, current frontmatter status (has/missing), classification (session-note/guide/architecture/reference)
- **Frontmatter**: YAML metadata block with fields: status (draft/active/deprecated/archived), created (YYYY-MM-DD), updated (YYYY-MM-DD), type (guide/architecture/reference/session-note/planning), lifecycle (persistent/ephemeral)
- **Categorization Rule**: Tuple of (path_pattern, status, type, lifecycle, created_date) used to classify files
- **Documentation Debt Item**: Represents outdated doc with attributes: file_path, age_in_days, lifecycle_type, recommended_action (archive/update/delete)

## Success Criteria

### Measurable Outcomes

- **SC-001**: YAML frontmatter schema exactly matches nixos-config (verify by diff of field names: status, created, updated, type, lifecycle)
- **SC-002**: Root directory contains exactly 3-5 files after reorganization (README.md, CLAUDE.md, TESTING.md required; LICENSE, CONTRIBUTING.md optional)
- **SC-003**: Pre-commit hook successfully blocks 100% of markdown commits without frontmatter (test with 5 sample files)
- **SC-004**: README.md value proposition comprehensible in <10 seconds (measured via user testing with 5 developers, target: 5/5 understand)
- **SC-005**: Documentation debt reduction of 80%+ (baseline: 15 root files, target: ≤3-5 root files + organized subdirectories)
- **SC-006**: 100% of markdown files have frontmatter after running add-frontmatter.py (verify with: `fd -e md --exec head -1 {} \; | grep -c '^---$'`)
- **SC-007**: Monthly review script correctly identifies docs requiring action (test with backdated frontmatter: draft=60 days, ephemeral=120 days)
- **SC-008**: Zero manual intervention needed for future doc lifecycle management (after migration, all workflows automated)

## Assumptions

- **A-001**: Repository has git installed and `.git/` directory exists (required for pre-commit hooks)
- **A-002**: Python 3.6+ is available in system PATH (required for scripts)
- **A-003**: User has write permissions to repository directories (required for reorganization)
- **A-004**: Existing markdown files use UTF-8 encoding (required for Python file operations)
- **A-005**: User will manually run migration once (scripts are not automatically triggered on repo clone)
- **A-006**: Session notes from October 2025 are archived together (created date set to 2025-10 for all)
- **A-007**: GitHub repository uses standard README.md naming (not readme.md or README.MD)
- **A-008**: Pre-commit framework is already installed or user will install it (required for hooks)

## Out of Scope

- **OOS-001**: Automated README generation from code docstrings (README is manually written following template)
- **OOS-002**: Integration with external documentation platforms (ReadTheDocs, GitBook)
- **OOS-003**: Automatic git commits of frontmatter changes (user must manually commit after running scripts)
- **OOS-004**: Bi-directional sync between different documentation formats (Markdown only)
- **OOS-005**: Historical git analysis to infer created dates (uses current date if not specified in RULES)
- **OOS-006**: Interactive prompts for frontmatter values (RULES-based automated classification only)
- **OOS-007**: Linting or formatting of markdown content (only frontmatter validation)
- **OOS-008**: Translation of documentation to other languages

## Dependencies

- **D-001**: Python 3.6+ with standard library (pathlib, datetime, os, sys)
- **D-002**: Git repository initialized (required for pre-commit hooks)
- **D-003**: Pre-commit framework (install with: `pip install pre-commit`)
- **D-004**: Bash shell for reorganization script (standard on Linux/macOS)
- **D-005**: Existing `.pre-commit-config.yaml` file or willingness to create one
- **D-006**: Access to ~/nixos-config/scripts/add-frontmatter.py for reference (same machine)

## Security & Privacy

- **SEC-001**: Scripts must not transmit any repository data externally (all operations local)
- **SEC-002**: Frontmatter created/updated dates may reveal development timeline (acceptable for open-source)
- **SEC-003**: Pre-commit hooks run user-provided scripts (standard risk, mitigated by code review)
- **SEC-004**: Scripts must validate file paths to prevent directory traversal (use pathlib.resolve())

## Performance & Scalability

- **PERF-001**: add-frontmatter.py must process 100+ markdown files in <5 seconds
- **PERF-002**: Pre-commit hook must validate frontmatter in <1 second for typical commit (1-5 files)
- **PERF-003**: Monthly review script must scan entire repository in <10 seconds
- **PERF-004**: Reorganization script must move files without data loss (use `git mv` for tracked files)

## Constraints

- **CON-001**: Must maintain backward compatibility with existing nixos-config frontmatter approach (same fields, same values)
- **CON-002**: Cannot modify CLAUDE.md (auto-generated file, excluded from frontmatter script)
- **CON-003**: Must preserve git history when reorganizing files (use `git mv`, not `mv`)
- **CON-004**: README.md must remain in root (GitHub requirement for visibility)
- **CON-005**: Scripts must be idempotent (safe to run multiple times without side effects)
