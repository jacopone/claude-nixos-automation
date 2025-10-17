---
status: active
created: 2025-10-10
updated: 2025-10-10
type: architecture
lifecycle: persistent
---

# Claude NixOS Automation: Project Constitution

**Version**: 1.0
**Status**: Foundational Document
**Purpose**: Define immutable principles that govern this project's architecture and evolution

---

## 🎯 Mission Statement

**Claude NixOS Automation** exists to maximize coding agent effectiveness by leveraging NixOS's declarative, text-based nature to provide intelligent, context-aware configuration that aligns with Anthropic's best practices.

---

## 📜 Core Principles

### Principle 1: Source/Artifact Separation

**Declaration**: There shall be a clear distinction between sources (editable) and artifacts (generated).

**Rationale**: Prevents accidental loss of manual content during regeneration. Ensures reproducibility.

**Rules**:
1. **Sources are sacred** - Never overwritten by automation
2. **Artifacts are ephemeral** - Always regenerable from sources
3. **Generators merge sources** - Manual content is preserved through merging, not editing artifacts
4. **Clear naming conventions** - Sources have specific names (CLAUDE-USER-POLICIES.md), artifacts use generic names (CLAUDE.md)

**Examples**:
```
✅ SOURCES (Manually Editable):
   - CLAUDE-USER-POLICIES.md
   - CLAUDE.local.md
   - packages.nix

❌ ARTIFACTS (Auto-Generated):
   - CLAUDE.md
   - settings.local.json
```

---

### Principle 2: Intelligence Over Inventory

**Declaration**: The system shall provide semantic understanding, not just lists.

**Rationale**: Static inventory is Level 1. Intelligence (understanding why, how, when) is Level 3-4.

**Rules**:
1. **Context must be actionable** - Don't just list tools, explain when to use them
2. **Usage informs recommendations** - Frequently-used tools are prioritized
3. **History reveals intent** - Git commits explain why packages were added
4. **Relationships matter** - Dependency graphs show how tools relate

**Examples**:
```
❌ BAD (Inventory):
   - ripgrep: Super fast grep

✅ GOOD (Intelligence):
   - ripgrep: Your preferred search tool (156 uses vs grep's 5)
     Added 6 months ago for "performance over grep"
     Commonly piped to bat for viewing results
```

---

### Principle 3: Dynamic Over Static

**Declaration**: Context shall adapt to project type and task, not be universal.

**Rationale**: Python projects don't need Kubernetes tools. Reduces noise, increases signal.

**Rules**:
1. **Project-aware filtering** - Only relevant tools for detected project type
2. **Task-specific loading** - Future: Load context based on task (testing vs debugging)
3. **Usage-based prioritization** - Most-used tools appear first
4. **Lazy loading** - Don't load what isn't needed

**Examples**:
```
Python Project CLAUDE.md:
- pytest, ruff, uv, mypy  ← Relevant
- NOT: k9s, pgcli, docker  ← Irrelevant for this context
```

---

### Principle 4: Validation Over Trust

**Declaration**: All generated content shall be validated before use.

**Rationale**: Prevents artifact pollution (commit messages in permissions), ensures correctness.

**Rules**:
1. **Schema validation** - Pydantic models enforce structure
2. **Content validation** - No multi-line strings in permissions, no temporal markers in docs
3. **Effectiveness tracking** - Measure if optimizations actually improve responses
4. **Fail loudly** - Invalid content should error, not silently corrupt

**Examples**:
```python
def validate_permission(perm: str) -> bool:
    if '\n' in perm or '<<' in perm or len(perm) > 200:
        raise ValueError(f"Invalid permission: {perm[:50]}")
    return True
```

---

### Principle 5: Declarative Truth

**Declaration**: System state shall be declared in text files, queryable and version-controlled.

**Rationale**: This is NixOS's superpower. Everything in .nix files is parseable, git-tracked.

**Rules**:
1. **Parse, don't poll** - Extract data from .nix files, not runtime state (when possible)
2. **Git as time machine** - Use git log to understand evolution
3. **Text as API** - All configuration is text, no binary formats
4. **Reproducibility** - Same inputs = same outputs, always

---

### Principle 6: Minimal Ceremony

**Declaration**: Automation shall be invisible until needed.

**Rationale**: Don't force process on users. Provide value, not overhead.

**Rules**:
1. **Zero-config by default** - Works out of the box with sane defaults
2. **Progressive disclosure** - Advanced features opt-in, not mandatory
3. **Fast execution** - All phases complete in <10 seconds
4. **Idempotent operations** - Safe to run multiple times

---

## 🏗️ Architectural Tenets

### Tenet 1: Generators Are Pure Functions

```
generator(sources, system_state) → artifacts
```

**Properties**:
- Deterministic: Same inputs → Same outputs
- Side-effect free: Only reads sources, only writes artifacts
- Composable: Can chain generators
- Testable: Easy to unit test

---

### Tenet 2: Data Flows Unidirectionally

```
Sources → Analyzers → Generators → Artifacts
```

**Not allowed**:
- Artifacts influencing sources ❌
- Circular dependencies ❌
- Implicit state ❌

**Allowed**:
- Sources → Analyzers (read) ✅
- Analyzers → Generators (data) ✅
- Generators → Artifacts (write) ✅

---

### Tenet 3: Three-Layer Architecture

```
┌─────────────────────────────────────┐
│   ANALYZERS (Extract Intelligence)  │
│   - project_detector.py             │
│   - usage_tracker.py                │
│   - git_history_analyzer.py         │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│   GENERATORS (Merge & Render)       │
│   - system_generator.py             │
│   - permissions_generator.py        │
│   - dynamic_context_generator.py    │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│   VALIDATORS (Ensure Quality)       │
│   - schema validation               │
│   - content validation              │
│   - effectiveness tracking          │
└─────────────────────────────────────┘
```

---

## 🚫 Anti-Patterns (Things We Must Avoid)

### Anti-Pattern 1: Editing Artifacts Directly

**Never**: Edit CLAUDE.md directly
**Instead**: Edit CLAUDE-USER-POLICIES.md, regenerate

### Anti-Pattern 2: Universal Context

**Never**: Load all 123 tools for every project
**Instead**: Filter by project type, prioritize by usage

### Anti-Pattern 3: Artifact Pollution

**Never**: Capture random strings from git log into permissions
**Instead**: Validate and filter before including

### Anti-Pattern 4: Silent Failures

**Never**: Continue if validation fails
**Instead**: Fail loudly, provide clear error messages

### Anti-Pattern 5: Implicit Magic

**Never**: Auto-detect without logging what was detected
**Instead**: Explicit output showing what was found and why

---

## 📊 Success Metrics

### For Users:
1. **Approval request reduction** - Fewer "Ask" prompts from Claude Code
2. **Response relevance** - Claude Code suggests correct tools
3. **Setup time reduction** - New projects configured in <5 minutes
4. **Maintenance burden** - Zero manual updates needed

### For System:
1. **Regeneration speed** - All phases complete in <10 seconds
2. **Test coverage** - 90%+ for generators and analyzers
3. **Schema compliance** - 100% of generated content validates
4. **Idempotency** - Running twice produces identical output

---

## 🔄 Evolution Policy

### This Constitution Can Be Amended When:
1. **Principle conflicts** - Two principles contradict in practice
2. **Technology changes** - New tools/APIs make principles obsolete
3. **User needs shift** - Original mission no longer serves users

### Amendment Process:
1. Document the problem with current principle
2. Propose amendment with rationale
3. Show impact analysis (what breaks, what improves)
4. Require explicit approval before changing

### What Cannot Change:
- ✅ Source/Artifact separation (Principle 1)
- ✅ Validation before use (Principle 4)
- ✅ Declarative truth (Principle 5)

These are **foundational** and abandoning them would require a new project.

---

## 📝 Version History

- **v1.0** (2025-10-10): Initial constitution
  - Defined 6 core principles
  - Established 3 architectural tenets
  - Documented anti-patterns
  - Set success metrics

---

## 🤝 Governance

**Maintainer**: User (guyfawkes)
**Authority**: Single-user project, user has final say
**Consultation**: Claude Code (AI assistant) provides recommendations
**Decision Process**: User approves all breaking changes

---

*This constitution governs all decisions in claude-nixos-automation.*
*When in doubt, refer to these principles.*
