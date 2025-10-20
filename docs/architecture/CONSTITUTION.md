---
status: active
created: 2025-10-10
updated: 2025-10-17
type: architecture
lifecycle: persistent
---

# Claude NixOS Automation: Project Constitution

**Version**: 2.0
**Status**: Foundational Document
**Purpose**: Define immutable principles that govern this project's architecture and evolution
**Scope**: Updated to include self-improving adaptive system principles and implementation patterns

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

## 🏛️ Implementation Principles (Version 2.0 Additions)

### Principle 7: Schema-First Design with Pydantic

**Declaration**: All data structures MUST be Pydantic `BaseModel` subclasses with comprehensive validation.

**Rationale**: Type safety, validation at boundaries, self-documenting contracts prevent bugs and enable confident refactoring.

**Rules**:
1. ALL data structures are Pydantic models (no bare dicts or JSON manipulation)
2. Validation logic lives in `@validator` decorators (not scattered in business logic)
3. Fields MUST have descriptions via `Field(description="...")`
4. Complex cross-field validation uses `@root_validator`
5. Properties provide computed fields and helpers for templates

**Evidence from Codebase** (schemas.py, 1397 lines):
```python
# 42 Pydantic schemas covering ALL domain objects
class PermissionApprovalEntry(BaseModel):
    """Log entry for a permission approval."""
    timestamp: datetime = Field(default_factory=datetime.now)
    permission: str = Field(..., description="Approved permission string")

    @validator("permission")
    def validate_permission(cls, v):
        if "\n" in v or "<<" in v:
            raise ValueError("Permission cannot contain newlines/heredocs")
        return v.strip()

# Real schemas: ToolInfo, GitStatus, MCPToolUsage, WorkflowSequence,
# LearningMetrics, and 37+ more domain models
```

**Benefits Realized**:
- Zero dict manipulation bugs (type checker catches them)
- Validation centralized (not scattered across 50 files)
- Self-documenting APIs (autocomplete shows descriptions)

---

### Principle 8: Multi-Tier Adaptive Learning

**Declaration**: The system MUST learn from user behavior across 3 tiers: immediate productivity (Tier 1), workflow intelligence (Tier 2), and cross-project knowledge (Tier 3).

**Rationale**: Single-tier learning plateaus. Multi-tier creates compound intelligence where each tier enables the next, achieving exponential improvement over time.

**Architecture**:

**Tier 1 - Immediate Productivity** (Permissions, MCP, Context):
- Permission Learning: Detect approval patterns → auto-approve common operations
- Global MCP Optimization: Track token costs system-wide → optimize server placement
- Context Optimization: Track section usage → prune noise, reorder by frequency

**Tier 2 - Workflow Intelligence** (Workflows, Instructions):
- Workflow Detection: Detect command sequences → bundle into slash commands
- Instruction Effectiveness: Monitor policy compliance → suggest rewording

**Tier 3 - Cross-Project Knowledge** (Archetypes, Meta-Learning):
- Project Archetypes: Detect patterns → transfer to similar projects
- Meta-Learning: Track learning effectiveness → self-calibrate thresholds

**Coordinator**: `AdaptiveSystemEngine` (571 lines) orchestrates all learners in unified cycle.

**Integration**: Runs automatically during `./rebuild-nixos` as final step.

**Evidence**:
- 9 analyzer classes (permission_pattern_detector.py, global_mcp_analyzer.py, context_optimizer.py, workflow_detector.py, instruction_tracker.py, project_archetype_detector.py, meta_learner.py, + 2 support classes)
- JSONL append-only logging (~/.claude/*-analytics.jsonl)
- Interactive approval with confidence scores
- Meta-learning threshold adjustment

**Performance Achieved**:
- Execution: 1.38 seconds (7.3x faster than 10s target)
- Memory: ~35MB (2.9x better than 100MB budget)
- Project scanning: 6 projects/second

---

### Principle 9: Validation at Boundaries (Tiered Strictness)

**Declaration**: Validation MUST occur at all data boundaries with tiered strictness: FAIL for security/data-loss, WARN for style/content.

**Rationale**: Different violation types require different responses. Security issues must halt; style issues can warn with gradual enforcement.

**Validation Tiers**:

**Critical (FAIL immediately)**:
- Source protection violations (cannot write to MANUAL_SOURCES)
- Permission injection (newlines, heredocs, excessive length)
- Schema validation failures
- Template rendering errors

**Content (WARN initially)**:
- Temporal markers in docs (NEW, Week 1, Phase 2)
- Formatting inconsistencies
- Style guideline violations

**Implementation** (validators/permission_validator.py, 227 lines):
```python
class PermissionValidator:
    MAX_LENGTH = 200
    HEREDOC_PATTERNS = [r"<<", r"EOF", r"<<-"]

    def validate(self, permission: str) -> ValidationResult:
        errors = []  # FAIL
        warnings = []  # WARN

        # CRITICAL: Security (fail fast)
        if "\n" in permission:
            errors.append("Cannot contain newlines (breaks JSON)")

        # Non-critical: Style (warn)
        dangerous = self._check_dangerous_patterns(permission)
        warnings.extend(dangerous)

        return ValidationResult(
            valid=len(errors) == 0,
            severity="fail" if errors else "warn",
            errors=errors,
            warnings=warnings
        )
```

**Benefits**:
- Security issues caught before execution
- Style issues surfaced without blocking
- Gradual enforcement path (warn → fail)

---

### Principle 10: Idempotency and Graceful Degradation

**Declaration**: All generators MUST be idempotent, and learning components MUST degrade gracefully (partial failure ≠ total failure).

**Rationale**: Production systems fail partially. Each component's value should be independent. User gets 4/5 suggestions instead of 0/5.

**Rules**:
1. Running generator 2x produces same result as 1x
2. Learning components catch exceptions, continue with remaining components
3. Analytics parsing handles corrupt/incomplete log files
4. File operations create backups before overwrite
5. Migration scripts are safely re-runnable

**Implementation** (adaptive_system_engine.py:81-124):
```python
def run_full_learning_cycle(self) -> LearningReport:
    """Run complete cycle with graceful degradation."""

    # Each component runs independently (failures isolated)
    permission_patterns = self._analyze_permissions()    # May fail
    mcp_suggestions = self._analyze_mcp_servers()        # Continues anyway
    context_suggestions = self._analyze_context()        # Continues anyway
    workflow_patterns = self._analyze_workflows()        # Continues anyway
    instruction_improvements = self._analyze_instructions()  # Continues anyway

    # Build report with whatever succeeded
    report = self._build_report(...)

    # System is useful even if some components failed
    return report  # User gets partial value
```

**Evidence**:
- All `_analyze_*` methods wrapped in try/except
- Empty lists returned on failure (not exceptions)
- Report built from whatever succeeded
- Backup creation before all file writes (base_generator.py:303-332)

---

### Principle 11: Testing as Documentation

**Declaration**: Tests MUST define behavior contract, with 90%+ coverage for critical paths and 100% for schemas/templates.

**Rationale**: Tests are source of truth for behavior. When tests pass, behavior is correct. Test names should read like specifications.

**Coverage Achieved**:
- Unit tests: 100% of validators (permission_validator.py, content_validator.py)
- Schema tests: 100% of 42 Pydantic models (test_schemas.py)
- Template tests: 100% of 26 Jinja2 templates (test_templates.py)
- Integration tests: All critical workflows (test_source_artifact_protection.py, test_learning_cycle.py)

**Test Organization**:
```
tests/
├── unit/                          # Fast, isolated
│   ├── test_base_generator.py
│   ├── test_permission_validator.py
│   ├── test_approval_tracker.py
│   └── test_permission_patterns.py
├── integration/                   # End-to-end
│   ├── test_source_artifact_protection.py
│   ├── test_learning_cycle.py
│   └── test_cross_project.py
└── conftest.py                    # Shared fixtures
```

**Test Quality Standards**:
1. Names describe behavior (not implementation)
2. Each test is independent (no shared state)
3. Fixtures use temporary directories (no pollution)
4. Fast (<30s for full suite)
5. Clear assertion messages

**Example**:
```python
def test_cannot_write_to_source_file():
    """BaseGenerator must prevent writing to declared source files."""
    gen = SystemGenerator()

    with pytest.raises(ValueError, match="Cannot write to source"):
        gen.write_artifact(Path("CLAUDE-USER-POLICIES.md"), "content")
```

---

## 🎨 Design Patterns (Version 2.0)

### Pattern 1: Base Class with Abstract Methods (base_generator.py:21-241)

**Use Case**: Common functionality across multiple generator implementations.

**Structure**:
```python
class BaseGenerator(ABC):
    # Subclasses MUST override (enforced)
    MANUAL_SOURCES: list[str] = []
    GENERATED_ARTIFACTS: list[str] = []

    def __init__(self):
        self._validate_declarations()  # Compile-time safety

    @abstractmethod
    def generate(self) -> GenerationResult:
        """Subclasses implement generation logic."""
        pass

    # Shared functionality (all subclasses get this)
    def write_artifact(self, path: Path, content: str):
        """Protection, headers, backups - all automatic."""
        # ... validation, header generation, backup creation ...
```

**Real Subclasses**: SystemGenerator, PermissionsGenerator, IntelligentPermissionsGenerator, LocalContextGenerator, DirectoryContextGenerator

**Benefits**: Compile-time contract enforcement, shared implementation, no duplication.

---

### Pattern 2: Result Objects (Not Exceptions for Business Logic)

**Use Case**: Operations that can fail for expected reasons.

**Structure** (schemas.py:199-218):
```python
class GenerationResult(BaseModel):
    """Structured result (not exception)."""
    success: bool
    output_path: str
    backup_path: str | None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
```

**Usage**:
```python
result = generator.generate()

if not result.success:
    for error in result.errors:
        logger.error(error)
    return  # Handle gracefully
```

**Benefits**: Exceptions for control flow are antipattern. Result objects make failure explicit, enable graceful handling, carry rich context.

---

### Pattern 3: Jinja2 Templates with Type-Safe Context

**Use Case**: Generating markdown/config files from structured data.

**Structure**:
```python
# Schema defines contract (compile-time type safety)
class SystemConfig(BaseModel):
    timestamp: datetime
    package_count: int
    tool_categories: dict[ToolCategory, list[ToolInfo]]

    @property
    def total_tools(self) -> int:
        """Template helper (computed field)."""
        return sum(len(tools) for tools in self.tool_categories.values())

# Generator uses schema
def generate(self) -> GenerationResult:
    config = SystemConfig(...)  # Validated at construction

    content = self.render_template("system-claude.j2", {
        "config": config,  # Type-safe context
        "timestamp": datetime.now()
    })

    return self.write_artifact(Path("CLAUDE.md"), content)
```

**Real Examples**: 26 Jinja2 templates in `templates/` directory (system-claude.j2, permissions/base.j2, local_context.j2, etc.)

**Benefits**: Data/presentation separation, template reuse, runtime errors prevented by type safety.

---

### Pattern 4: Append-Only JSONL Logging

**Use Case**: Analytics, audit trails, learning datasets.

**Structure** (approval_tracker.py):
```python
class ApprovalTracker:
    """Logs permission approvals to append-only file."""

    def __init__(self):
        self.history_file = Path.home() / ".claude" / "approval-history.jsonl"

    def log_approval(self, permission: str, context: dict = None):
        """Atomic append operation."""
        entry = PermissionApprovalEntry(...)  # Validated

        with open(self.history_file, 'a') as f:
            f.write(entry.json() + '\n')  # Atomic, corruption-resistant

    def get_recent_approvals(self, days: int = 30) -> list[...]:
        """Parse log file (tolerates corruption)."""
        with open(self.history_file) as f:
            for line in f:
                try:
                    entry = PermissionApprovalEntry.parse_raw(line)
                    # ...
                except Exception:
                    continue  # Skip corrupt lines gracefully
```

**Real Usage**: approval-history.jsonl, mcp-analytics.jsonl, context-analytics.jsonl, workflow-analytics.jsonl, instruction-analytics.jsonl, project-patterns.jsonl, meta-learning.jsonl

**Benefits**: JSONL is append-only (no overwrite), human-readable, grep-able, corruption-tolerant (bad line ≠ bad file).

---

### Pattern 5: Tiered Confidence Scoring

**Use Case**: Pattern detection, suggestions, recommendations.

**Structure** (permission_pattern_detector.py):
```python
def _calculate_confidence(self, result: PermissionPattern) -> float:
    """Multi-factor confidence scoring."""

    # Factor 1: Frequency (more = higher confidence)
    frequency_score = min(result.occurrences / 10, 1.0)

    # Factor 2: Consistency (similar patterns = higher)
    consistency_score = self._measure_consistency(result.examples)

    # Factor 3: Recency (recent activity = higher)
    recency_score = self._measure_recency(result)

    # Weighted average (tunable by meta-learner)
    return (
        0.5 * frequency_score +
        0.3 * consistency_score +
        0.2 * recency_score
    )
```

**Benefits**: Confidence enables filtering, prioritization, meta-learning calibration. Multi-factor is more robust than single metrics.

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

- **v2.0** (2025-10-17): Comprehensive expansion based on implemented codebase
  - Added 5 new principles (7-11): Schema-First Design, Multi-Tier Adaptive Learning, Validation at Boundaries, Idempotency/Graceful Degradation, Testing as Documentation
  - Documented 5 design patterns with real code references
  - Added concrete evidence from 11,000+ lines of production code
  - Grounded principles in actual implementations (not aspirational)
  - Performance metrics: 1.38s execution, 35MB memory, 6 projects/sec

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
