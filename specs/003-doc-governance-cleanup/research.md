---
status: active
created: 2025-10-20
updated: 2025-10-20
type: planning
lifecycle: persistent
---

# Research: Documentation Governance and Cleanup System

**Feature**: Documentation Governance and Cleanup
**Date**: 2025-10-20
**Status**: Complete

## Decision Summary

All technical unknowns resolved. No research needed - this feature extends existing, proven patterns from nixos-config and ai-project-orchestration repositories.

## Key Decisions

### Decision 1: Frontmatter Schema

**Decision**: Use exact schema from ~/nixos-config/scripts/add-frontmatter.py

**Fields**:
```yaml
---
status: draft | active | deprecated | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: guide | architecture | reference | session-note | planning
lifecycle: persistent | ephemeral
---
```

**Rationale**: Proven pattern already in use across 2 repositories. Backward compatibility critical. No improvements needed - schema serves its purpose well.

**Alternatives Considered**:
- Adding `author` field → Rejected: git history provides authorship
- Adding `priority` field → Rejected: Out of scope, adds complexity
- Adding `tags` field → Rejected: Filesystem organization sufficient

**Implementation**: Direct copy-paste from nixos-config with repository-specific RULES

---

### Decision 2: File Categorization Rules

**Decision**: Use RULES list pattern (list of tuples) from nixos-config

**Pattern**:
```python
RULES = [
    # (path_pattern, status, type, lifecycle, created_date)
    ("PHASE*.md", "archived", "session-note", "ephemeral", "2025-10"),
    ("IMPLEMENTATION*.md", "archived", "session-note", "ephemeral", "2025-10"),
    ("README.md", "active", "reference", "persistent", "2024-01-01"),
    # ... more rules
]
```

**Rationale**: Pattern matching with glob is simple, readable, maintainable. Already proven in production.

**Alternatives Considered**:
- YAML config file → Rejected: Overkill for ~20 rules
- Hardcoded logic → Rejected: Less maintainable
- Machine learning classification → Rejected: Absurd overkill

**Implementation**: Create RULES list specific to claude-nixos-automation file structure

---

### Decision 3: Pre-Commit Hook Implementation

**Decision**: Add custom local hook to .pre-commit-config.yaml

**Pattern**:
```yaml
- repo: local
  hooks:
    - id: check-markdown-frontmatter
      name: Check Markdown Frontmatter
      entry: python3 scripts/check-frontmatter.py
      language: system
      files: \.md$
      exclude: ^CLAUDE\.md$
```

**Rationale**: Local hooks run without network access, fast validation, already using pre-commit framework in project.

**Alternatives Considered**:
- Git pre-commit hook directly → Rejected: .pre-commit-config.yaml is project standard
- GitHub Actions only → Rejected: Too slow, want local validation
- No enforcement → Rejected: Defeats purpose of governance

**Implementation**: Create check-frontmatter.py that reads files and validates YAML

---

### Decision 4: Git History Preservation

**Decision**: Use `git mv` instead of `mv` for file reorganization

**Rationale**: Preserves git blame, maintains commit history, essential for audit trail.

**Alternatives Considered**:
- Regular `mv` → Rejected: Loses git history
- Copy then delete → Rejected: Creates duplicate history

**Implementation**: Bash script wraps git mv commands:
```bash
git mv PHASE1_COMPLETE.md .claude/sessions/2025-10-archive/
```

---

### Decision 5: README Optimization Strategy

**Decision**: Follow proven GitHub star-maximizing template from successful projects

**Template Elements** (based on research of 1000+ star projects):
1. Hero section (1-2 sentences, value prop in 10 seconds)
2. Visual architecture diagram (Mermaid or ASCII)
3. Badges (test coverage, code quality, license, maintenance)
4. 2-minute quickstart (exact commands, no fluff)
5. Feature highlights (benefits, not feature lists)
6. Clear contribution guide

**Examples Studied**:
- github.com/goldbergyoni/nodebestpractices (88k stars)
- github.com/papers-we-love/papers-we-love (85k stars)
- github.com/nix-community/home-manager (6.8k stars - NixOS specific)

**Rationale**: These patterns are proven. First 10 seconds determine star/bounce decision.

**Alternatives Considered**:
- Auto-generate from code → Rejected: Out of scope
- Keep current README → Rejected: Doesn't follow best practices

**Implementation**: Manual rewrite following template, will include:
- **Hero**: "Claude automation for NixOS that learns from your workflow and auto-configures itself"
- **Diagram**: 3-tier learning system (Permissions → Workflows → Archetypes)
- **Quickstart**: `git clone` → `./run-adaptive-learning.py` → profit

---

### Decision 6: Monthly Review Script Approach

**Decision**: Read-only Python script that scans and reports, does NOT auto-archive

**Rationale**: Safe, transparent, user maintains control over archival decisions.

**Output Format**:
```
⚠️  Draft docs older than 30 days:
  - docs/planning/old-plan.md (created: 2025-08-15, 66 days old)
  - Recommendation: Archive or update status to 'active'

🗄️  Ephemeral docs older than 90 days:
  - .claude/sessions/old-notes.md (created: 2025-07-01, 112 days old)
  - Recommendation: Move to .claude/sessions/archive/2025-07/
```

**Alternatives Considered**:
- Auto-archive → Rejected: Too aggressive, risks data loss
- Email reports → Rejected: Out of scope
- Cron integration → Rejected: User can set up if desired

**Implementation**: Iterate all .md files, parse frontmatter, calculate age, output recommendations

---

## Best Practices

### Python Script Best Practices (from nixos-config reference)

1. **Idempotency**: Check state before modifying (e.g., "skip if frontmatter exists")
2. **Color output**: Use ANSI codes for visibility (✅ green, ⏭️ yellow, ❌ red)
3. **Summary stats**: Print "Processed: X, Skipped: Y" at end
4. **Absolute paths**: Use `Path(__file__).parent.parent` for repo root
5. **Error handling**: Try/except with helpful messages, continue on single file errors

### Bash Script Best Practices

1. **Safety**: `set -euo pipefail` at top
2. **Validation**: Check git repo exists before git commands
3. **Dry-run mode**: Optional `--dry-run` flag for testing
4. **Verbose output**: Show each file being moved

### Pre-Commit Hook Best Practices

1. **Fast**: <1 second for typical commit (1-5 files)
2. **Helpful errors**: Show exact command to fix issue
3. **Exclude auto-generated**: Don't check CLAUDE.md

---

## Technology Choices

No new technologies needed. All tools already in use:

- **Python 3.6+**: Already used in project (claude_automation/)
- **Bash**: Standard on NixOS
- **Git**: Already in use
- **Pre-commit**: Already configured (.pre-commit-config.yaml exists)
- **YAML**: Standard for frontmatter

---

## Integration Patterns

### With Existing System

This feature is **independent** of the core adaptive learning system. It:
- Does NOT modify any claude_automation/ code
- Does NOT interact with Pydantic schemas
- Does NOT use generators/analyzers/validators
- Lives entirely in /scripts/ directory

### With Existing Documentation

Respects existing patterns:
- CLAUDE.md remains auto-generated (excluded from scripts)
- .claude/ directory structure preserved
- specs/ directory untouched
- Git history maintained

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accidental file deletion during reorganization | HIGH | Use git mv, test with --dry-run first, create backup branch |
| Frontmatter parsing errors on malformed YAML | MEDIUM | Try/except parsing, warn user, skip file |
| Pre-commit hook blocks legitimate commits | MEDIUM | Clear error messages, easy to bypass with --no-verify if needed |
| README rewrite loses important info | MEDIUM | Review current README, preserve all essential content in new structure |
| Scripts run on wrong repository | LOW | Validate git remote matches claude-nixos-automation |

---

## Implementation Sequence

1. **Phase A**: Create add-frontmatter.py (copy from nixos-config, adapt RULES)
2. **Phase B**: Create reorganize-docs.sh (git mv based on frontmatter)
3. **Phase C**: Add pre-commit hook (check-frontmatter.py + .pre-commit-config.yaml)
4. **Phase D**: Create review-docs-lifecycle.py (read-only scanner)
5. **Phase E**: Rewrite README.md (manual, following template)

Total estimated time: 4-6 hours

---

## Open Questions

None. All unknowns resolved.

---

**Research Complete**: 2025-10-20
**Ready for**: Phase 1 (Data Model & Contracts)
