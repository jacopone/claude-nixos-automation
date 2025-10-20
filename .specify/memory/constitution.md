---
status: draft
created: 2025-10-20
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# Claude NixOS Automation Constitution

## Core Principles

### I. Source/Artifact Separation (NON-NEGOTIABLE)

There shall be a clear distinction between sources (editable) and artifacts (generated).

**MUST**:
- Sources are sacred - Never overwritten by automation
- Artifacts are ephemeral - Always regenerable from sources
- Generators merge sources - Manual content is preserved through merging
- Clear naming conventions - Sources have specific names, artifacts use generic names

**Examples**:
- ✅ SOURCES: CLAUDE-USER-POLICIES.md, packages.nix (manually editable)
- ❌ ARTIFACTS: CLAUDE.md, settings.local.json (auto-generated)

### II. Schema-First Design with Pydantic (NON-NEGOTIABLE)

All data structures MUST be Pydantic BaseModel subclasses with comprehensive validation.

**MUST**:
- ALL data structures are Pydantic models (no bare dicts or JSON manipulation)
- Validation logic lives in @validator decorators (not scattered in business logic)
- Fields MUST have descriptions via Field(description="...")
- Complex cross-field validation uses @root_validator
- Properties provide computed fields and helpers for templates

**Rationale**: Type safety at boundaries prevents bugs, enables confident refactoring, self-documenting contracts.

### III. Multi-Tier Adaptive Learning (CORE ARCHITECTURE)

The system MUST learn from user behavior across 3 tiers:
- **Tier 1**: Immediate productivity (Permissions, MCP, Context)
- **Tier 2**: Workflow intelligence (Workflows, Instructions)
- **Tier 3**: Cross-project knowledge (Archetypes, Meta-learning)

**MUST**:
- Permission learning: Detect approval patterns → auto-approve common operations
- Global MCP optimization: Track token costs system-wide → optimize server placement
- Context optimization: Track section usage → prune noise, reorder by frequency
- Workflow detection: Detect command sequences → bundle into slash commands
- Instruction effectiveness: Monitor policy compliance → suggest rewording
- Project archetypes: Detect patterns → transfer to similar projects
- Meta-learning: Track learning effectiveness → self-calibrate thresholds

**Coordinator**: AdaptiveSystemEngine orchestrates all learners in unified cycle

### IV. Validation at Boundaries (Tiered Strictness)

Validation MUST occur at all data boundaries with tiered strictness.

**MUST FAIL immediately**:
- Source protection violations (cannot write to MANUAL_SOURCES)
- Permission injection (newlines, heredocs, excessive length >200 chars)
- Schema validation failures
- Template rendering errors

**SHOULD WARN initially**:
- Temporal markers in docs (NEW, Week 1, Phase 2)
- Formatting inconsistencies
- Style guideline violations

**Rationale**: Security issues must halt; style issues can warn with gradual enforcement.

### V. Idempotency and Graceful Degradation

All generators MUST be idempotent. Learning components MUST degrade gracefully.

**MUST**:
- Running generator 2x produces same result as 1x
- Learning components catch exceptions, continue with remaining components
- Analytics parsing handles corrupt/incomplete log files
- File operations create backups before overwrite
- Migration scripts are safely re-runnable

**Rationale**: Partial failure ≠ total failure. User gets 4/5 suggestions instead of 0/5.

### VI. Testing as Documentation

Tests MUST define behavior contract, with 90%+ coverage for critical paths and 100% for schemas/templates.

**MUST**:
- Unit tests: 100% of validators
- Schema tests: 100% of Pydantic models
- Template tests: 100% of Jinja2 templates
- Integration tests: All critical workflows
- Test names describe behavior (not implementation)
- Each test is independent (no shared state)
- Fast (<30s for full suite)

**Rationale**: Tests are source of truth for behavior. When tests pass, behavior is correct.

### VII. Intelligence Over Inventory

The system shall provide semantic understanding, not just lists.

**MUST**:
- Context must be actionable - Don't just list tools, explain when to use them
- Usage informs recommendations - Frequently-used tools are prioritized
- History reveals intent - Git commits explain why packages were added
- Relationships matter - Dependency graphs show how tools relate

**Example**:
- ❌ BAD: "ripgrep: Super fast grep"
- ✅ GOOD: "ripgrep: Your preferred search tool (156 uses vs grep's 5)"

### VIII. Dynamic Over Static

Context shall adapt to project type and task, not be universal.

**MUST**:
- Project-aware filtering - Only relevant tools for detected project type
- Task-specific loading - Load context based on task (testing vs debugging)
- Usage-based prioritization - Most-used tools appear first
- Lazy loading - Don't load what isn't needed

**Rationale**: Python projects don't need Kubernetes tools. Reduces noise, increases signal.

## Architectural Constraints

### Pure Function Generators

```
generator(sources, system_state) → artifacts
```

**MUST be**:
- Deterministic: Same inputs → Same outputs
- Side-effect free: Only reads sources, only writes artifacts
- Composable: Can chain generators
- Testable: Easy to unit test

### Unidirectional Data Flow

```
Sources → Analyzers → Generators → Artifacts
```

**NOT allowed**:
- Artifacts influencing sources ❌
- Circular dependencies ❌
- Implicit state ❌

**MUST follow**:
- Sources → Analyzers (read) ✅
- Analyzers → Generators (data) ✅
- Generators → Artifacts (write) ✅

### Three-Layer Architecture

```
┌─────────────────────────────────────┐
│   ANALYZERS (Extract Intelligence)  │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│   GENERATORS (Merge & Render)       │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│   VALIDATORS (Ensure Quality)       │
└─────────────────────────────────────┘
```

**MUST maintain**:
- Clear separation of concerns
- Analyzers extract, Generators transform, Validators ensure quality
- No layer skipping

## Design Patterns (Required)

### 1. Base Class with Abstract Methods

**Use for**: Common functionality across multiple generator implementations

**MUST include**:
- Abstract methods enforced by ABC
- MANUAL_SOURCES and GENERATED_ARTIFACTS class attributes
- Shared implementation (write_artifact with protection, headers, backups)
- Compile-time contract validation

### 2. Result Objects (Not Exceptions for Business Logic)

**Use for**: Operations that can fail for expected reasons

**MUST return**: Structured result objects (GenerationResult, ValidationResult) with:
- success: bool
- errors: list[str]
- warnings: list[str]
- Additional context (output_path, backup_path, stats)

**Rationale**: Exceptions for control flow are antipattern. Result objects make failure explicit.

### 3. Jinja2 Templates with Type-Safe Context

**MUST**:
- Schema defines contract (Pydantic model)
- Template receives validated context
- Properties provide computed fields for templates
- Data/presentation separation

### 4. Append-Only JSONL Logging

**Use for**: Analytics, audit trails, learning datasets

**MUST**:
- JSONL format (one JSON object per line)
- Atomic append operations
- Corruption-tolerant parsing (skip bad lines)
- Human-readable and grep-able

### 5. Tiered Confidence Scoring

**Use for**: Pattern detection, suggestions, recommendations

**MUST include**:
- Multi-factor scoring (frequency, consistency, recency)
- Weighted average (tunable by meta-learner)
- Filtering and prioritization based on confidence
- Meta-learning calibration

## Anti-Patterns (MUST AVOID)

### 1. Editing Artifacts Directly
- ❌ **NEVER**: Edit CLAUDE.md directly
- ✅ **INSTEAD**: Edit CLAUDE-USER-POLICIES.md, regenerate

### 2. Universal Context
- ❌ **NEVER**: Load all 123 tools for every project
- ✅ **INSTEAD**: Filter by project type, prioritize by usage

### 3. Artifact Pollution
- ❌ **NEVER**: Capture random strings from git log into permissions
- ✅ **INSTEAD**: Validate and filter before including

### 4. Silent Failures
- ❌ **NEVER**: Continue if validation fails
- ✅ **INSTEAD**: Fail loudly, provide clear error messages

### 5. Implicit Magic
- ❌ **NEVER**: Auto-detect without logging what was detected
- ✅ **INSTEAD**: Explicit output showing what was found and why

## Success Metrics

### Performance Targets (MUST achieve)
- Execution time: <10 seconds for full learning cycle
- Memory usage: <100MB for all analyzers
- Project scanning: >5 projects/second
- Test suite: <30 seconds

### Quality Targets (MUST achieve)
- Test coverage: 90%+ for critical paths, 100% for schemas/templates
- Schema compliance: 100% of generated content validates
- Idempotency: Running twice produces identical output
- Approval reduction: 50%+ fewer user approvals over 30 days

### User Experience (MUST deliver)
- Response relevance: Claude Code suggests correct tools
- Setup time: New projects configured in <5 minutes
- Maintenance burden: Zero manual updates needed

## Governance

### Constitution Authority

This constitution is **NON-NEGOTIABLE** within analysis and implementation scope. Constitution conflicts are automatically CRITICAL and require:
1. Adjustment of spec, plan, or tasks (not the constitution)
2. OR explicit constitution amendment via separate process

### Amendment Process

Constitution can be amended when:
1. **Principle conflicts** - Two principles contradict in practice
2. **Technology changes** - New tools/APIs make principles obsolete
3. **User needs shift** - Original mission no longer serves users

**Amendment requires**:
1. Document the problem with current principle
2. Propose amendment with rationale
3. Show impact analysis (what breaks, what improves)
4. Explicit approval before changing

### Immutable Core (CANNOT CHANGE)
- Source/Artifact separation (Principle I)
- Schema-First Design (Principle II)
- Validation at boundaries (Principle IV)

These are **foundational** - abandoning them requires a new project.

**Version**: 2.0 | **Ratified**: 2025-10-10 | **Last Amended**: 2025-10-17
