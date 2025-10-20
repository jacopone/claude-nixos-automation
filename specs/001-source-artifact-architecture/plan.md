---
status: active
created: 2025-10-20
updated: 2025-10-20
type: planning
lifecycle: persistent
---

# Implementation Plan: Self-Improving Claude Code System

**Branch**: `001-source-artifact-architecture` | **Date**: 2025-10-17 | **Spec**: [spec.md](./spec.md)

## Summary

This feature implements a self-improving Claude Code automation system with explicit source/artifact separation and multi-tier adaptive learning. The system progressively learns from user behavior to reduce permission prompts, optimize MCP servers, improve context relevance, and transfer knowledge across projects.

**Core Components**:
- **Foundation**: Source/artifact protection, validation pipeline, NixOS integration
- **Tier 1 Learning**: Permission patterns, Global MCP optimization, Context optimization
- **Tier 2 Learning**: Workflow detection, Instruction effectiveness
- **Tier 3 Learning**: Cross-project transfer, Meta-learning calibration

**Technical Approach**: Extend existing Python automation with 8 new analyzers, unified AdaptiveSystemEngine coordinator, and integration with `./rebuild-nixos` workflow for zero-overhead learning.

## Technical Context

**Language/Version**: Python 3.13+ (from pyproject.toml)
**Development Environment**: devenv shell (fast activation <1s, declarative)
**Primary Dependencies**:
- Pydantic 2.5+ (existing - schema validation)
- Jinja2 3.1+ (existing - template rendering)
- pytest 7.4+ (existing - testing framework)

**Storage**:
- JSONL files for append-only learning logs (~/.claude/*.jsonl)
- JSON for configurations (.claude/mcp.json, settings.local.json)
- Markdown for generated artifacts (CLAUDE.md)

**Testing**: pytest with fixtures, parametrization, integration tests
**Target Platform**: Linux (NixOS) - integrates with existing rebuild-nixos workflow
**Project Type**: Single Python library/CLI tool with update scripts

**Performance Goals**:
- <1 second validation overhead per generator
- <10 seconds full learning cycle execution
- <100MB memory for global MCP analysis across all projects

**Constraints**:
- No new external dependencies (use existing: Pydantic, Jinja2, pathlib)
- Backward compatibility required (existing workflows must continue working)
- Idempotent operations (safe to run multiple times)

**Scale/Scope**:
- 30+ new Pydantic schemas
- 8 new analyzer modules
- 6 projects scanned for MCP configs
- 30-day rolling window for pattern detection
- 100+ permission patterns to detect

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: Source/Artifact Separation
**Status**: ✅ PERFECT ALIGNMENT (This IS the spec)
- FR-1, FR-2, FR-3 enforce explicit source/artifact declarations
- BaseGenerator validates no overlap, prevents source overwrites
- Generation headers clearly mark artifacts
- **Gate: PASS** - Principle 1 is the foundation of this feature

### Principle 2: Intelligence Over Inventory
**Status**: ✅ ENHANCED
- Permission learning detects patterns (not just lists commands)
- MCP optimization calculates ROI (not just connection status)
- Context optimization tracks effectiveness (not just presence)
- **Gate: PASS** - Adds Tier 1-3 intelligence layers

### Principle 3: Dynamic Over Static
**Status**: ✅ ENHANCED
- Global MCP analyzer filters by project type
- Context optimizer reorders by usage frequency
- Cross-project transfer detects archetypes
- **Gate: PASS** - Implements adaptive, context-aware system

### Principle 4: Validation Over Trust
**Status**: ✅ ALIGNED
- FR-4: Critical validation fails immediately
- FR-5: Content validation with tiered strictness
- Permission syntax validated (no newlines, heredocs, length limits)
- **Gate: PASS** - Comprehensive validation pipeline

### Principle 5: Declarative Truth
**Status**: ✅ ALIGNED
- Uses NixOS .nix files as source of truth
- Git history for pattern detection
- All learning data in text files (JSONL, JSON, Markdown)
- **Gate: PASS** - Maintains declarative approach

### Principle 6: Minimal Ceremony
**Status**: ✅ ALIGNED
- Zero user configuration required (auto-discovery)
- Integrates with existing rebuild-nixos workflow
- Interactive prompts only when needed
- <10 second execution budget
- **Gate: PASS** - Invisible until needed

**Overall Constitution Check: ✅ PASSES ALL GATES**
- Zero violations requiring justification
- Feature perfectly aligns with all 6 core principles
- No complexity tracking needed

## Project Structure

### Documentation (this feature)

```
specs/001-source-artifact-architecture/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file - implementation plan
├── research.md          # Phase 0 output (pattern detection algorithms, ROI methods)
├── data-model.md        # Phase 1 output (all Pydantic schemas)
├── quickstart.md        # Phase 1 output (user & dev guide)
├── contracts/           # Phase 1 output (API contracts)
│   ├── analyzers.md     # Analyzer interfaces
│   ├── generators.md    # Generator interfaces
│   └── engine.md        # AdaptiveSystemEngine contract
└── tasks.md             # Phase 2 output (from /speckit.tasks - NOT created yet)
```

### Source Code (repository root)

```
# Root configuration
devenv.nix                           # NEW - Development environment config
pyproject.toml                       # EXISTS - Python dependencies
flake.nix                            # EXISTS - Nix flake

claude_automation/
├── analyzers/                       # Extract intelligence layer
│   ├── __init__.py
│   ├── approval_tracker.py          # NEW - Logs permission approvals
│   ├── permission_pattern_detector.py  # NEW - Detects approval patterns
│   ├── global_mcp_analyzer.py       # NEW - Multi-project MCP analysis
│   ├── mcp_usage_analyzer.py        # MODIFY - Add token tracking
│   ├── context_optimizer.py         # NEW - CLAUDE.md effectiveness
│   ├── workflow_detector.py         # NEW - Slash command patterns
│   ├── instruction_tracker.py       # NEW - Policy compliance
│   ├── project_archetype_detector.py  # NEW - Cross-project patterns
│   └── meta_learner.py              # NEW - System self-calibration
│
├── core/
│   ├── __init__.py
│   └── adaptive_system_engine.py    # NEW - Central coordinator
│
├── generators/
│   ├── __init__.py
│   ├── base_generator.py            # MODIFY - Add source/artifact protection
│   ├── permissions_generator.py     # EXISTS - Keep as-is
│   ├── intelligent_permissions_generator.py  # NEW - With learning
│   ├── system_generator.py          # MODIFY - Add validation headers
│   └── mcp_usage_analytics_generator.py  # EXISTS - Keep as-is
│
├── validators/
│   ├── __init__.py
│   ├── permission_validator.py      # NEW - Syntax validation
│   └── content_validator.py         # MODIFY - Add tiered strictness
│
├── schemas.py                       # MODIFY - Add 30+ learning schemas
├── templates/                       # Jinja2 templates (existing)
└── utils.py                         # Utility functions

tests/
├── unit/
│   ├── test_approval_tracker.py
│   ├── test_permission_patterns.py
│   ├── test_global_mcp_analyzer.py
│   ├── test_context_optimizer.py
│   ├── test_workflow_detector.py
│   ├── test_meta_learner.py
│   ├── test_base_generator.py
│   └── test_validators.py
│
├── integration/
│   ├── test_learning_cycle.py
│   ├── test_rebuild_integration.py
│   └── test_cross_project.py
│
└── contract/
    ├── test_analyzer_contracts.py
    ├── test_generator_contracts.py
    └── test_engine_contract.py

scripts/
├── analyze-all-projects-mcp.py      # NEW - Global MCP CLI
├── run-adaptive-learning.py         # NEW - Unified learning entry
├── update-permissions-with-learning.py  # NEW - Smart permissions
└── migrate-add-headers.sh           # NEW - Add headers to existing artifacts

.git/hooks/
└── pre-commit                       # MODIFY - Add artifact warning

~/nixos-config/
└── rebuild-nixos                    # MODIFY - Add learning integration
```

**Structure Decision**: Single Python library/CLI tool (Option 1). This is not a web or mobile app, so the backend/frontend split is not needed. The three-layer architecture (Analyzers → Generators → Validators) aligns with Constitution Tenet 3.

## Phase 0: Research

*Deliverable: research.md documenting all findings*

### Research Topics

1. **Permission Pattern Detection Algorithms**
   - **Question**: What's the optimal algorithm for detecting generalizable patterns from approval history?
   - **Approach**: Research frequent itemset mining (FP-Growth), sequence mining, statistical significance tests
   - **Output**: Algorithm choice with rationale, minimum occurrence thresholds, confidence scoring

2. **Token-Based MCP ROI Calculation**
   - **Question**: How to accurately calculate ROI for MCP servers given token consumption?
   - **Approach**: Research cost models (invocations/1000 tokens), session overhead estimation, utilization rate formulas
   - **Output**: ROI formula, overhead token estimates per server type, utilization thresholds

3. **Context Effectiveness Measurement**
   - **Question**: How to track which CLAUDE.md sections Claude actually uses?
   - **Approach**: Research session log analysis, section reference detection, "effective context ratio" metrics
   - **Output**: Measurement methodology, noise detection criteria, reordering algorithms

4. **Meta-Learning Threshold Calibration**
   - **Question**: How should the system adjust detection thresholds based on user feedback?
   - **Approach**: Research adaptive threshold algorithms, acceptance rate feedback loops, calibration strategies
   - **Output**: Calibration algorithm, initial thresholds, adjustment rules

**Research Output**: Consolidated in `research.md` with:
- Decision made for each topic
- Rationale (why chosen over alternatives)
- Implementation implications
- References to papers/docs consulted

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

### 1.1 Data Model (data-model.md)

Extract entities from spec and define all Pydantic schemas:

**Learning Schemas** (30+ new models):
```python
# Permission Learning
class PermissionApprovalEntry(BaseModel)
class PermissionPattern(BaseModel)
class PatternSuggestion(BaseModel)

# MCP Optimization (extend existing)
class GlobalMCPReport(BaseModel)
class MCPServerRecommendation(BaseModel)

# Context Optimization
class ContextAccessLog(BaseModel)
class SectionUsage(BaseModel)
class ContextOptimization(BaseModel)

# Workflow Detection
class SlashCommandLog(BaseModel)
class WorkflowSequence(BaseModel)
class WorkflowSuggestion(BaseModel)

# Instruction Tracking
class PolicyViolation(BaseModel)
class InstructionEffectiveness(BaseModel)
class InstructionImprovement(BaseModel)

# Cross-Project
class ProjectArchetype(BaseModel)
class CrossProjectPattern(BaseModel)
class TransferSuggestion(BaseModel)

# Meta-Learning
class LearningMetrics(BaseModel)
class ThresholdAdjustment(BaseModel)
class LearningHealthReport(BaseModel)

# Unified Engine
class LearningReport(BaseModel)
class AdaptiveSystemConfig(BaseModel)
```

**Validation Models**:
```python
class ValidationResult(BaseModel)
class SourceArtifactDeclaration(BaseModel)
class GenerationHeader(BaseModel)
```

### 1.2 API Contracts (contracts/ directory)

**analyzers.md**: Interface contracts for all 8 analyzers
```python
class ApprovalTracker:
    def log_approval(permission: str, context: dict) -> None
    def get_recent_approvals(days: int) -> list[ApprovalEntry]

class PermissionPatternDetector:
    def detect_patterns(min_occurrences: int) -> list[PatternSuggestion]

class GlobalMCPAnalyzer:
    def discover_projects() -> list[Path]
    def analyze_all_projects() -> GlobalMCPReport

# ... all 8 analyzers
```

**generators.md**: Generator contracts
```python
class BaseGenerator(ABC):
    MANUAL_SOURCES: List[str] = []
    GENERATED_ARTIFACTS: List[str] = []

    def read_source(path: Path) -> str
    def write_artifact(path: Path, content: str) -> None
    def _validate_declarations() -> None
    def _generate_header(path: Path) -> str
```

**engine.md**: AdaptiveSystemEngine contract
```python
class AdaptiveSystemEngine:
    def run_full_learning_cycle() -> LearningReport
    def _collect_approvals(report: LearningReport) -> list[dict]
    def _apply_improvements(approved: list[dict]) -> None
    def _update_meta_learning(report: LearningReport) -> None
```

### 1.3 Quickstart Guide (quickstart.md)

**User Guide**:
- How the self-improving system works
- What happens during `./rebuild-nixos`
- How to approve/reject suggestions
- Where learning data is stored
- How to reset learning state

**Developer Guide**:
- Development environment setup with devenv
  - `devenv shell` - Fast activation (<1s)
  - Available scripts: `test`, `lint`, `format`, `quality`
  - Pre-commit hooks automatically configured
- How to add new analyzers
- How to extend learning patterns
- How to test learning components
- Architecture overview with diagrams

**Output**: quickstart.md with both user and developer sections

### 1.4 Agent Context Update

Run update script to add new technologies to agent context:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This adds:
- Pattern detection algorithms (from research)
- Meta-learning concepts
- Adaptive threshold calibration
- Statistical analysis techniques

## Phase 2: Implementation Build Sequence

*Prerequisites: Phase 1 complete, all designs approved*

### Stage 0: Development Environment Setup (1-2h)

**0.1 devenv Configuration** (1-2h)
- [ ] Create devenv.nix with Python 3.13 configuration
- [ ] Configure poetry integration with auto-install
- [ ] Add development packages (ruff, mypy)
- [ ] Define scripts: test, test-fast, lint, format, quality
- [ ] Configure pre-commit hooks (ruff, mypy, artifact detection)
- [ ] Set environment variables (PYTHONPATH, CLAUDE_AUTOMATION_DEV)
- [ ] Test devenv shell activation (<1s performance)
- [ ] Document devenv usage in quickstart.md
- [ ] Verify poetry install works on shell entry

### Stage 1: Core Architecture (10-15h)

**1.1 Base Generator Enhancement** (3-4h)
- [ ] Add MANUAL_SOURCES/GENERATED_ARTIFACTS to BaseGenerator
- [ ] Implement _validate_declarations() with overlap check
- [ ] Implement read_source() with warning for undeclared sources
- [ ] Implement write_artifact() with source protection
- [ ] Implement _generate_header() for HTML comment headers
- [ ] Unit tests: test_cannot_write_to_source, test_artifact_has_header
- [ ] Update existing generators (SystemGenerator, PermissionsGenerator)

**1.2 Validation Pipeline** (3-4h)
- [ ] Create PermissionValidator with syntax checking
- [ ] Implement tiered validation (FAIL vs WARN)
- [ ] Add validation for: newlines, heredocs, length >200
- [ ] Add content validation for temporal markers
- [ ] Unit tests: test_permission_validation, test_content_validation
- [ ] Integration with generators

**1.3 Migration & Headers** (2-3h)
- [ ] Create migrate-add-headers.sh script
- [ ] Implement idempotent header addition
- [ ] Test on existing CLAUDE.md files
- [ ] Update git pre-commit hook with artifact warnings
- [ ] Interactive prompt: "Are you sure? (y/n)"

**1.4 NixOS Integration** (2-4h)
- [ ] Verify NixConfigParser works with global MCP analyzer
- [ ] Add freshness detection (timestamp-based)
- [ ] Test automatic regeneration trigger
- [ ] Verify no breaking changes to rebuild-nixos

### Stage 2: Tier 1 Learning (15-20h)

**2.1 Permission Learning** (5-7h)
- [ ] Implement ApprovalTracker with JSONL logging
- [ ] Implement PermissionPatternDetector with algorithms from research
- [ ] Pattern categorization: git, pytest, file ops, project access
- [ ] Confidence scoring implementation
- [ ] IntelligentPermissionsGenerator with interactive prompts
- [ ] Unit tests: test_pattern_detection, test_confidence_scoring
- [ ] Integration test: end-to-end approval → pattern → suggestion

**2.2 Global MCP Optimization** (5-7h)
- [ ] Implement GlobalMCPAnalyzer.discover_projects()
- [ ] Implement project aggregation logic
- [ ] Add token consumption tracking to existing analyzer
- [ ] Implement ROI calculation (invocations / tokens * 1000)
- [ ] Utilization metrics: loaded vs used sessions
- [ ] Recommendations: poor_utilization, high_value, fix_errors
- [ ] Unit tests: test_global_discovery, test_usage_aggregation
- [ ] Test with user's whatsapp-mcp and sunsama-mcp projects

**2.3 Context Optimization** (5-6h)
- [ ] Implement ContextUsageTracker for section access logging
- [ ] Calculate effective context ratio
- [ ] Identify noise sections (loaded but never referenced)
- [ ] Detect context gaps (queries for missing info)
- [ ] Reordering algorithm by access frequency
- [ ] Generate "Quick Reference" from hot paths
- [ ] Unit tests: test_section_tracking, test_noise_detection

### Stage 3: Tier 2 Learning (10-12h)

**3.1 Workflow Detection** (5-6h)
- [ ] Implement WorkflowDetector for slash command logging
- [ ] Sequence detection (multi-command patterns)
- [ ] Completion rate and success metrics
- [ ] Workflow bundling suggestions
- [ ] Unit tests: test_workflow_detection, test_sequence_patterns

**3.2 Instruction Effectiveness** (5-6h)
- [ ] Implement InstructionEffectivenessTracker
- [ ] Policy violation detection
- [ ] Effectiveness scoring per instruction
- [ ] Ambiguity identification (<70% compliance)
- [ ] Rewording suggestions
- [ ] Unit tests: test_violation_detection, test_effectiveness_score

### Stage 4: Tier 3 Learning (5-8h)

**4.1 Cross-Project Transfer** (3-4h)
- [ ] Implement ProjectArchetypeDetector
- [ ] Archetype detection (Python/pytest, TypeScript/vitest, etc.)
- [ ] Knowledge base building per archetype
- [ ] Pattern transfer logic
- [ ] Unit tests: test_archetype_detection, test_pattern_transfer

**4.2 Meta-Learning** (2-4h)
- [ ] Implement MetaLearner for effectiveness tracking
- [ ] Acceptance rate monitoring
- [ ] Threshold adjustment algorithms (from research)
- [ ] Confidence scoring calibration
- [ ] Learning health metrics
- [ ] Unit tests: test_meta_learning, test_threshold_adjustment

### Stage 5: Integration & Polish (5-10h)

**5.1 Adaptive System Engine** (3-5h)
- [ ] Implement AdaptiveSystemEngine central coordinator
- [ ] _analyze_* methods for all 8 learners
- [ ] _build_report() with prioritization
- [ ] _present_report() formatting
- [ ] _collect_approvals() interactive flow
- [ ] _apply_improvements() dispatcher
- [ ] _update_meta_learning() feedback loop

**5.2 CLI Entry Points** (1-2h)
- [ ] Create run-adaptive-learning.py
- [ ] Add --interactive, --all-components, --dry-run flags
- [ ] Error handling and logging
- [ ] Help text and examples

**5.3 Rebuild Integration** (1-2h)
- [ ] Update ~/nixos-config/rebuild-nixos
- [ ] Add learning cycle after system context update
- [ ] Test full workflow: rebuild → learn → approve → apply
- [ ] Verify backward compatibility

**5.4 Testing & Documentation** (2-3h)
- [ ] Integration test: full learning cycle
- [ ] Contract tests: all API boundaries
- [ ] Performance test: <10s budget verification
- [ ] Update README with self-improvement features
- [ ] Generate API documentation

## Success Criteria

### Acceptance Criteria (from spec)
- ✅ AC-1: Cannot write to sources (pytest validates)
- ✅ AC-2: Artifacts have headers (pytest validates)
- ✅ AC-3: Permission validation works (pytest validates)
- ✅ AC-4: Git hook prompts interactively (manual test)
- ✅ AC-5: Manual content preserved (pytest validates)
- ✅ AC-6: Migration script idempotent (bash test)
- ✅ AC-7: Permission pattern detection (pytest validates)
- ✅ AC-8: Rebuild integration works (manual test)
- ✅ AC-9: Global MCP discovery (pytest validates)
- ✅ AC-10: Context optimization (pytest validates)
- ✅ AC-11: Workflow detection (pytest validates)
- ✅ AC-12: Instruction tracking (pytest validates)
- ✅ AC-13: Cross-project transfer (pytest validates)
- ✅ AC-14: Meta-learning (pytest validates)

### Performance Metrics
- [ ] Validation overhead <1s per generator
- [ ] Full learning cycle <10s
- [ ] Global MCP scan <5s for 10 projects
- [ ] Test suite <30s
- [ ] Memory usage <100MB for learning cycle

### Quality Metrics
- [ ] 90%+ test coverage for new code
- [ ] 100% schema compliance (Pydantic validation)
- [ ] 0 source overwrites (enforced by BaseGenerator)
- [ ] 100% of artifacts have generation headers
- [ ] 70%+ suggestion acceptance rate (after 30 days)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing workflows | HIGH | Extensive backward compatibility tests, migration script, phased rollout |
| Performance degradation | MEDIUM | <10s budget enforced, caching, profiling, optimization |
| False positive patterns | MEDIUM | Confidence thresholds, meta-learning, user approval required |
| Pattern detection inaccuracy | MEDIUM | Research-backed algorithms, statistical validation, min occurrences=3 |
| User confusion about headers | LOW | Clear documentation, hidden HTML comments, helpful error messages |
| Migration script failures | LOW | Idempotent design, dry-run mode, backup recommendation |

## Dependencies

### Development Dependencies
- devenv (existing - already installed on system)
- Python 3.13+ (from devenv)
- poetry (from devenv, auto-install dependencies)

### External Dependencies (No New Ones)
- Pydantic 2.5+ (existing)
- Jinja2 3.1+ (existing)
- pytest 7.4+ (existing)

### Internal Dependencies
- Existing MCPUsageAnalyzer (extend, don't replace)
- Existing PermissionsGenerator (keep as fallback)
- Existing schemas.py (add to, don't break)
- Existing templates/ (add new, keep existing)

### System Dependencies
- ~/nixos-config/rebuild-nixos (modify minimally)
- ~/.claude.json (read global MCP config)
- ~/.claude/projects/*/\*.jsonl (read session logs)
- NixOS flake (parse packages.nix)

## Next Steps After Plan Approval

1. **User Review**: Review and approve this implementation plan
2. **Run `/speckit.tasks`**: Generate detailed tasks.md from this plan
3. **Phase 0 Execution**: Create research.md with algorithm decisions
4. **Phase 1 Execution**: Generate data-model.md, contracts/, quickstart.md
5. **Phase 2 Execution**: Implement in 5 stages following build sequence
6. **Testing**: Run full test suite, verify all acceptance criteria
7. **Documentation**: Update README, generate API docs
8. **Deployment**: Merge to main, tag release, announce features

---

**Implementation Time Estimate**: 46-67 hours total
- Stage 0 (Dev Environment): 1-2h
- Stage 1 (Core): 10-15h
- Stage 2 (Tier 1): 15-20h
- Stage 3 (Tier 2): 10-12h
- Stage 4 (Tier 3): 5-8h
- Stage 5 (Integration): 5-10h

**Development Workflow**:
```bash
# Setup (once)
devenv shell  # <1s activation

# Development cycle
format  # Auto-format code
lint    # Check for issues
test    # Run test suite
quality # All checks + tests

# Implementation
# Pre-commit hooks run automatically on git commit
```

**Ready for `/speckit.tasks` command to generate granular task checklist.**
