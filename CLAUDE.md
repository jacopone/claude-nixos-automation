# CLAUDE.md

## 📋 Documentation Governance Workflow

This repository uses an automated documentation governance system to maintain clean, well-organized documentation.

### Quick Reference

**Daily workflow:**
1. Create markdown files as needed
2. Commit your changes - the pre-commit hook will validate frontmatter
3. If blocked: run `python3 scripts/add-frontmatter.py` to add frontmatter automatically

**Monthly maintenance:**
```bash
python3 scripts/review-docs-lifecycle.py
```
This identifies stale documents that need attention.

### Scripts Available

**scripts/add-frontmatter.py** - Add YAML frontmatter to markdown files
- Automatically classifies files by pattern (session notes, architecture docs, guides)
- Idempotent: safe to run multiple times
- Usage: `python3 scripts/add-frontmatter.py`

**scripts/reorganize-docs.sh** - Move files based on frontmatter classification
- Moves session notes to `.claude/sessions/2025-10-archive/`
- Moves architecture docs to `docs/architecture/`
- Uses `git mv` to preserve history
- Usage: `bash scripts/reorganize-docs.sh [--dry-run]`

**scripts/check-frontmatter.py** - Pre-commit hook validation
- Blocks commits of markdown files without frontmatter
- Automatically runs on `git commit`
- To bypass (emergencies only): `git commit --no-verify`

**scripts/review-docs-lifecycle.py** - Stale document detection
- Flags draft docs >30 days old
- Flags ephemeral docs >90 days old
- Provides recommendations for archiving
- Usage: `python3 scripts/review-docs-lifecycle.py`

### Frontmatter Schema

All markdown files (except CLAUDE.md) must include:

```yaml
---
status: draft | active | deprecated | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: guide | architecture | reference | session-note | planning
lifecycle: persistent | ephemeral
---
```

**Status field:**
- `draft` - Work in progress
- `active` - Current and maintained
- `deprecated` - Outdated but kept for reference
- `archived` - Historical record

**Type field:**
- `guide` - How-to documentation
- `architecture` - System design documentation
- `reference` - API/specification documentation
- `session-note` - Development session notes
- `planning` - Feature planning documents

**Lifecycle field:**
- `persistent` - Long-term documentation (guides, architecture, reference)
- `ephemeral` - Temporary documentation (session notes, planning docs)

### Directory Structure

- **Root**: Essential files only (README.md, TESTING.md, plus 2-3 high-level guides)
- **.claude/sessions/YYYY-MM-archive/**: Archived session notes
- **docs/architecture/**: Architectural documentation
- **specs/NNN-feature-name/**: Feature specifications (spec.md, plan.md, tasks.md)

### Enforcement

**Pre-commit hook:**
- Configured in `.pre-commit-config.yaml`
- Validates all staged `.md` files (except CLAUDE.md)
- Blocks commits without proper frontmatter
- Exit code 1 = missing frontmatter, 0 = valid

**Monthly review automation:**
- Run `python3 scripts/review-docs-lifecycle.py` monthly
- Reviews all docs for staleness
- Outputs recommendations for archiving or updating

### Common Tasks

**Creating a new markdown file:**
1. Create the file
2. Either:
   - Add frontmatter manually following the schema above
   - Run `python3 scripts/add-frontmatter.py` to add it automatically
3. Commit normally - pre-commit hook will validate

**Moving stale documents:**
1. Run `python3 scripts/review-docs-lifecycle.py` to identify stale docs
2. Review recommendations
3. Update status or move to archive as suggested

**Reorganizing the repository:**
1. Run `bash scripts/reorganize-docs.sh --dry-run` to preview moves
2. Review the output
3. Run `bash scripts/reorganize-docs.sh` to execute moves

### For More Details

- **Full specification**: `specs/003-doc-governance-cleanup/spec.md`
- **Implementation plan**: `specs/003-doc-governance-cleanup/plan.md`
- **Migration guide**: `specs/003-doc-governance-cleanup/MIGRATION_PLAN.md`
- **Task breakdown**: `specs/003-doc-governance-cleanup/tasks.md`

---

<!-- USAGE_ANALYTICS_START -->
## 📊 Usage Analytics

> **Auto-generated from Fish shell history** - Last updated: 2025-10-08 11:27:49

### Command Usage Statistics

- **Total commands analyzed**: 883
- **Unique commands**: 223
- **Analysis period**: All Fish shell history

### Top 20 Most Used Commands

1. **`cd`** - Used 111 times (file_operations)
   - Last used: 2025-10-07 11:49
2. **`git`** - Used 97 times (git)
   - Last used: 2025-10-07 12:34
3. **`rm`** - Used 44 times (file_operations)
   - Last used: 2025-10-05 10:24
4. **`cat`** - Used 32 times (file_operations)
   - Last used: 2025-10-06 14:50
5. **`nix-shell`** - Used 32 times (nix)
   - Last used: 2025-08-22 15:36
6. **`glow`** - Used 32 times (unknown)
   - Last used: 2025-10-05 18:44
7. **`cp`** - Used 27 times (file_operations)
   - Last used: 2025-09-02 14:57
8. **`mv`** - Used 26 times (file_operations)
   - Last used: 2025-09-30 16:43
9. **`hx`** - Used 23 times (unknown)
   - Last used: 2025-10-06 01:56
10. **`eza`** - Used 19 times (file_operations)
   - Last used: 2025-10-01 23:54
11. **`plandex`** - Used 18 times (unknown)
   - Last used: 2025-04-22 20:09
12. **`ls`** - Used 16 times (file_operations)
   - Last used: 2025-10-01 12:18
13. **`gh`** - Used 14 times (git)
   - Last used: 2025-08-23 19:00
14. **`nix`** - Used 13 times (nix)
   - Last used: 2025-10-01 04:27
15. **`nix-channel`** - Used 13 times (unknown)
   - Last used: 2025-08-18 10:10
16. **`z`** - Used 13 times (unknown)
   - Last used: 2025-10-08 11:17
17. **`nix-env`** - Used 12 times (nix)
   - Last used: 2025-09-05 11:11
18. **`python`** - Used 9 times (development)
   - Last used: 2025-06-10 22:35
19. **`nixos-rebuild`** - Used 9 times (nix)
   - Last used: 2025-09-18 12:53
20. **`flox`** - Used 8 times (unknown)
   - Last used: 2025-05-06 23:05

### Modern CLI Tools Usage

Tools you actively use (tracked from history):

- **git**: 97 times
- **glow**: 32 times
- **eza**: 19 times
- **gh**: 14 times
- **nix**: 13 times
- **nixos-rebuild**: 9 times
- **devenv**: 8 times
- **bat**: 6 times
- **fd**: 2 times
- **gitui**: 1 times
- **dust**: 1 times
- **bottom**: 1 times
- **procs**: 1 times
- **btm**: 1 times
- **lazygit**: 1 times
- **aider**: 1 times
- **rg**: 1 times

### Workflow Patterns Detected

- ✓ Heavy git user
- ✓ Modern CLI tools adoption
- ✓ AI-assisted development

### Insights for Claude Code

Based on your command usage:

- **Git-heavy workflow**: You use git frequently. Claude Code can help with commit messages, code reviews, and git workflows.
- **Modern CLI adoption**: You prefer modern tools over traditional Unix commands. Claude Code should recommend eza, bat, rg, etc.
- **AI-assisted development**: You're already using AI coding tools. Claude Code is a natural fit for your workflow.
- **Diverse command usage**: You use 223 unique commands, indicating broad CLI proficiency.

---

*This section auto-updates to help Claude Code understand your actual tool usage patterns.*
<!-- USAGE_ANALYTICS_END -->
