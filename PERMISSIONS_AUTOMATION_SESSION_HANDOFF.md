---
status: draft
created: 2025-10-20
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# 🔐 Permissions Automation Implementation - Session Handoff

**Date**: 2025-10-06
**Status**: Ready to implement - Plan approved, blocked by TDD Guard
**Next Session**: Start fresh Claude Code session without TDD enforcement

---

## 🎯 What We're Building

An **automated permissions optimizer** for `claude-nixos-automation` that:
- Runs on every `./rebuild-nixos`
- Scans all projects with `.claude/` directories
- Generates optimized `.claude/settings.local.json` for each project
- Uses project-specific templates (Python, Node.js, Rust, NixOS)
- Preserves user customizations
- Follows security best practices

**Pattern**: Extends existing `claude-nixos-automation` architecture (same as SystemGenerator, UserPoliciesGenerator)

---

## 📋 Complete Approved Plan

The full implementation plan is in **THIS FILE** starting at line 60.

**Key decisions made**:
1. ✅ Follow existing generator pattern (BaseGenerator, Jinja2 templates, Pydantic schemas)
2. ✅ **NO TDD/testing enforcement** - only preserve if already exists
3. ✅ **NO unit tests** for claude-nixos-automation (infrastructure code, no tests currently)
4. ✅ Analyze git history for usage patterns
5. ✅ Detect project types automatically
6. ✅ User opt-out via `_user_customized: true` marker

---

## 🚧 Why We Stopped

**Current blocker**: TDD Guard is active in current session, enforcing test-first development.

**The problem**:
- `claude-nixos-automation` has NO existing tests (infrastructure project)
- User wants to reserve strict SWE/TDD standards for `ai-orchestrator` once completed
- We agreed to exclude TDD for projects without existing test infrastructure
- But TDD Guard is still active from previous `ai-project-orchestration` context

**The solution**: Start fresh session, work in `claude-nixos-automation` directory where TDD Guard hooks aren't configured.

---

## 🎬 How to Resume (Copy This Message)

Start your next Claude Code session with this exact message:

```
I want to implement the Automated Permissions Optimization System for claude-nixos-automation.

Context:
- Full plan approved in: /home/guyfawkes/ai-project-orchestration/PERMISSIONS_AUTOMATION_SESSION_HANDOFF.md
- Working directory: /home/guyfawkes/claude-nixos-automation
- This project has NO TDD Guard hooks configured (infrastructure code)
- We're extending existing architecture (BaseGenerator pattern)
- NO unit tests needed (following existing project style)

Phase 1 tasks:
1. Add PermissionsConfig schema to claude_automation/schemas.py
2. Create claude_automation/generators/permissions_generator.py
3. Create claude_automation/analyzers/ directory with project_detector.py
4. Create claude_automation/templates/permissions/ with base.j2, python.j2, nodejs.j2, rust.j2, nixos.j2
5. Create update-permissions-v2.py script
6. Update flake.nix with new app

Start with Phase 1.1: adding schemas to schemas.py (lines to add are in the handoff file)
```

---

## 📐 Architecture Overview

### Files to Create

```
claude-nixos-automation/
├── claude_automation/
│   ├── generators/
│   │   └── permissions_generator.py          # NEW (extends BaseGenerator)
│   ├── analyzers/                             # NEW (parallel to parsers/)
│   │   ├── __init__.py
│   │   ├── project_detector.py
│   │   ├── usage_analyzer.py
│   │   └── security_analyzer.py
│   ├── templates/
│   │   └── permissions/                       # NEW
│   │       ├── base.j2
│   │       ├── python.j2
│   │       ├── nodejs.j2
│   │       ├── rust.j2
│   │       └── nixos.j2
│   └── schemas.py                             # EXTEND (add 3 new classes)
├── update-permissions-v2.py                   # NEW
└── flake.nix                                  # UPDATE (add permissions app)
```

### Files to Modify

1. **`claude_automation/schemas.py`** - Add 3 new classes at end
2. **`flake.nix`** - Add `update-permissions` app + update `update-all` script
3. **`~/nixos-config/rebuild-nixos`** - Add permissions optimization step (later)

---

## 📝 Phase 1.1: Schema Code to Add

Add to end of `claude_automation/schemas.py` (before example configs):

```python
class ProjectType(str, Enum):
    """Detected project types for permissions optimization."""

    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    NIXOS = "nixos"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class UsagePattern(BaseModel):
    """Command usage pattern from git history."""

    command: str = Field(..., description="Command name")
    frequency: int = Field(..., ge=0, description="Usage count in git history")
    last_used: datetime = Field(..., description="Last usage timestamp")

    @validator("command")
    def validate_command(cls, v):
        """Validate command format."""
        if not v or len(v.strip()) < 2:
            raise ValueError("Command must be at least 2 characters")
        return v.strip()


class PermissionsConfig(BaseModel):
    """Configuration for permissions generation."""

    project_path: Path = Field(..., description="Project root directory")
    project_type: ProjectType = Field(..., description="Detected project type")
    usage_patterns: list[UsagePattern] = Field(
        default_factory=list, description="Command patterns from git history"
    )
    existing_hooks: Optional[dict[str, Any]] = Field(
        None, description="Existing hooks configuration to preserve"
    )
    quality_tools: list[str] = Field(
        default_factory=list, description="Detected quality tools (ruff, black, etc.)"
    )
    package_managers: list[str] = Field(
        default_factory=list, description="Detected package managers (uv, npm, cargo)"
    )
    sensitive_paths: list[str] = Field(
        default_factory=list, description="Sensitive paths for deny rules"
    )
    modern_cli_tools: list[str] = Field(
        default_factory=list, description="Modern CLI tools (fd, eza, bat, rg)"
    )
    username: str = Field(..., description="System username")
    timestamp: datetime = Field(default_factory=datetime.now)
    has_tests: bool = Field(False, description="Whether project has test directory")
    template_name: str = Field(
        "base.j2", description="Template file name to use for generation"
    )

    @validator("project_path")
    def validate_project_path(cls, v):
        """Validate project path exists."""
        if not v.exists():
            raise ValueError(f"Project path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Project path is not a directory: {v}")
        return v

    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if not v or len(v.strip()) < 2:
            raise ValueError("Username must be at least 2 characters")
        return v.strip()
```

**Also update imports at top**:
```python
from pathlib import Path
from typing import Any, Optional
```

---

## 🎯 Implementation Checklist

- [ ] Phase 1.1: Add schemas to `schemas.py`
- [ ] Phase 1.2: Create `generators/permissions_generator.py`
- [ ] Phase 1.3: Create `templates/permissions/base.j2`
- [ ] Phase 1.4: Create `analyzers/project_detector.py`
- [ ] Phase 1.5: Create `update-permissions-v2.py`
- [ ] Phase 1.6: Update `flake.nix`
- [ ] Phase 1.7: Test with `ai-project-orchestration`

---

## 🔑 Key Design Decisions

### 1. **No TDD Enforcement**
- Infrastructure code, follows existing project style
- `claude-nixos-automation` has no tests currently
- Only for projects that already have test infrastructure

### 2. **Follows Existing Pattern**
- Extends `BaseGenerator` (same as `SystemGenerator`)
- Uses Jinja2 templates in `templates/` directory
- Returns `GenerationResult`
- Same backup system (`.backups/`)

### 3. **User Customization Preservation**
Marker-based approach:
```json
{
  "_user_customized": true,
  "permissions": { "..." }
}
```
If this marker exists, skip auto-generation.

### 4. **Project Type Detection**
- Python: `pyproject.toml`, `requirements.txt`
- Node.js: `package.json`
- Rust: `Cargo.toml`
- NixOS: `flake.nix` + `configuration.nix`

### 5. **Security First**
Always deny:
- `.env`, `.env.*`
- `.ssh/`, `.gnupg/`
- `Bash(rm -rf:*)`
- `Bash(sudo:*)`
- `Bash(curl:*)`, `Bash(wget:*)`

---

## 📊 Templates Overview

### Base Template (All Projects)
- Git operations (status, diff, log, add, commit)
- Modern CLI tools (fd, eza, bat, rg)
- Read project files
- WebFetch/WebSearch
- Deny sensitive paths
- Ask for git push

### Python Template
Adds:
- ruff, black, pytest (if detected)
- uv/pip package managers
- Write/Edit src/, tests/
- Ask for package installs

### Node.js Template
Adds:
- npm/pnpm/yarn
- Write/Edit src/, lib/
- Ask for npm install

### Rust Template
Adds:
- cargo commands
- Write/Edit src/
- Deny target/ writes

### NixOS Template
Adds:
- fd, eza, fish
- Edit modules/, docs/
- Deny sudo, rebuild-nixos
- Ask for nix flake update

---

## 🧪 Testing Plan

Since no unit tests for infrastructure:

**Manual testing checklist**:
1. Run on `ai-project-orchestration` (Python + TDD)
2. Run on `nixos-config` (NixOS)
3. Run on `whisper-dictation` (Rust)
4. Run on `birthday-manager` (Python)
5. Verify user customization preservation
6. Check backup system works

---

## 📚 Reference Files

**Key files to understand existing pattern**:
- `/home/guyfawkes/claude-nixos-automation/claude_automation/generators/base_generator.py`
- `/home/guyfawkes/claude-nixos-automation/claude_automation/generators/system_generator.py`
- `/home/guyfawkes/claude-nixos-automation/claude_automation/generators/user_policies_generator.py`
- `/home/guyfawkes/claude-nixos-automation/claude_automation/schemas.py`
- `/home/guyfawkes/claude-nixos-automation/flake.nix`

**Applied example**:
- `/home/guyfawkes/ai-project-orchestration/docs/PERMISSIONS_OPTIMIZATION_GUIDE.md` (already created)

---

## ⏭️ After Implementation

1. Test with real projects
2. Update `/home/guyfawkes/nixos-config/rebuild-nixos` to call `update-permissions`
3. Run `./rebuild-nixos` and verify all projects get optimized permissions
4. Document in `claude-nixos-automation/README.md`

---

## 💡 Tips for Next Session

1. **Start in correct directory**: `cd /home/guyfawkes/claude-nixos-automation`
2. **Check TDD Guard status**: Should NOT be active in this project
3. **Follow existing patterns**: Look at `SystemGenerator` as reference
4. **Work incrementally**: One file at a time, test as you go
5. **Use existing utilities**: `BaseGenerator.render_template()`, `BaseGenerator.write_file()`

---

**Good luck! This is a clean, well-architected addition to an existing system. Follow the pattern and it will integrate seamlessly.** 🚀
