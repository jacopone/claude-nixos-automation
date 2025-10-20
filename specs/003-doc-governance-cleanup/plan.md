# Implementation Plan: Documentation Governance and Cleanup System

**Branch**: `003-doc-governance-cleanup` | **Date**: 2025-10-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-doc-governance-cleanup/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a documentation governance system that extends the existing nixos-config YAML frontmatter pattern to claude-nixos-automation, reducing root directory clutter from 15+ files to 3-5 files, enforcing frontmatter via pre-commit hooks, automating monthly documentation review, and rewriting README.md for GitHub star optimization. Technical approach: Python scripts following established patterns (add-frontmatter.py with RULES-based classification), bash reorganization script using git mv for history preservation, pre-commit hook integration, and lifecycle review automation.

## Technical Context

**Language/Version**: Python 3.6+ (standard library only), Bash 4.0+
**Primary Dependencies**: None (pure Python stdlib: pathlib, datetime, os, sys, re, yaml for frontmatter parsing)
**Storage**: File system (markdown files with YAML frontmatter), git for version control
**Testing**: Manual testing via script execution (no pytest - scripts are simple utilities)
**Target Platform**: NixOS/Linux (bash, git, python available)
**Project Type**: Utility scripts (not an application - standalone scripts in /scripts directory)
**Performance Goals**: <5 seconds to process 100+ markdown files, <1 second for pre-commit validation
**Constraints**: Must preserve git history (use git mv), must not modify CLAUDE.md (auto-generated), backward compatible with nixos-config frontmatter schema
**Scale/Scope**: ~50-100 markdown files initially, grows with project documentation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Source/Artifact Separation ✅ **PASS**

**Analysis**: This feature manages documentation files, not the core adaptive learning system. The scripts themselves (add-frontmatter.py, reorganize-docs.sh) are sources. Markdown files with frontmatter are also sources (manually editable, not auto-generated). CLAUDE.md is explicitly excluded from modification (CON-002).

**Verdict**: No violations. Scripts don't generate artifacts, they modify sources (markdown files) in a controlled, idempotent way.

### Principle II: Schema-First Design ❌ **NOT APPLICABLE**

**Analysis**: This feature creates utility scripts, not application code. No Pydantic models needed - frontmatter is simple YAML with fixed fields (status, created, updated, type, lifecycle).

**Verdict**: Not applicable. Scripts are too simple to justify Pydantic overhead.

### Principle III: Multi-Tier Adaptive Learning ❌ **NOT APPLICABLE**

**Analysis**: This feature is documentation tooling, not part of the adaptive learning system.

**Verdict**: Not applicable.

### Principle IV: Validation at Boundaries ✅ **PASS**

**Analysis**: Scripts validate at boundaries:
- add-frontmatter.py: Validates file exists, checks for existing frontmatter, validates UTF-8 encoding
- Pre-commit hook: Validates frontmatter presence before allowing commit
- reorganize-docs.sh: Validates git repo exists before using git mv

**Verdict**: PASS. Appropriate validation for utility scripts.

### Principle V: Idempotency ✅ **PASS**

**Analysis**: All scripts are designed to be idempotent:
- add-frontmatter.py: Skips files that already have frontmatter
- reorganize-docs.sh: Checks if files exist before moving
- review-docs-lifecycle.py: Read-only script, no modifications

**Verdict**: PASS. All scripts safe to run multiple times.

### Principle VI: Testing as Documentation ⚠️ **WAIVED**

**Analysis**: Feature spec explicitly states "Manual testing via script execution" (see Technical Context). These are simple utility scripts (similar to nixos-config/scripts/add-frontmatter.py which also has no tests).

**Justification**: Cost/benefit ratio doesn't justify pytest infrastructure for 3 simple scripts. Manual testing via acceptance scenarios in spec is sufficient.

**Verdict**: WAIVED. Manual testing acceptable for utility scripts.

###Summary: **✅ GATES PASSED**

- No constitution violations
- Principles II, III not applicable (documentation tooling, not core system)
- Principle VI waived (utility scripts, manual testing acceptable)
- Feature ready for Phase 0 research

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

