---
status: draft
created: 2025-10-10
updated: 2025-10-17
type: planning
lifecycle: ephemeral
speckit_phase: clarify
scope_expanded: true
self_improvement_tiers: all  # Tier 1, 2, 3 components added
---

# Specification: Explicit Source/Artifact Architecture + Self-Improving System

**Spec ID**: SAA-001
**Priority**: High
**Estimated Effort**: 40-60 hours (includes all self-improvement tiers)
**Dependencies**: None (foundational)

**Scope**:
- Core: Source/artifact separation, validation, NixOS integration (10-15h)
- Tier 1: Permission learning, MCP optimization, context optimization (15-20h)
- Tier 2: Workflow detection, instruction tracking (10-12h)
- Tier 3: Cross-project transfer, meta-learning (5-8h)
- Integration: Unified AdaptiveSystemEngine, testing, documentation (5-10h)

---

## Clarifications

### Session 2025-10-16

- Q: Should validation be strict (fail) or lenient (warn) initially? → A: Tiered strictness - Critical rules (source protection, permission injection) fail; Content rules (temporal markers, formatting) warn initially
- Q: Should git hook block commits or just warn? → A: Interactive prompt - Ask user "Are you sure? (y/n)" before allowing commit
- Q: Should headers be visible in rendered markdown or hidden? → A: Hidden - Use HTML comments so headers are invisible when rendered
- Q: How to handle migration of existing deployments? → A: Migration script provided - Optional script adds headers to existing artifacts, plus automatic on next generation
- Q: What should happen if user manually deletes generation header? → A: Regenerate adds header back - Next generation run detects missing header and adds it automatically

---

## `/speckit.specify` - Capture Requirements

### Problem Statement

**Current State**:
- CLAUDE.md files are auto-generated but include manually-maintained content
- The separation between "sources" (editable) and "artifacts" (generated) is **implicit**
- Risk of accidental data loss if generators overwrite manual content
- No validation prevents writing to source files
- Users can't easily tell which files are editable vs generated
- **NixOS system state not accurately reflected** - Auto-generated CLAUDE.md content doesn't sync with actual system state from `./rebuild-nixos`
- **Permission generation needs verification** - Dynamic permission creation system status uncertain, requires investigation

**Pain Points**:
1. **Fragile architecture** - Manual/auto split works but only by convention
2. **No enforcement** - Nothing prevents generator from overwriting sources
3. **User confusion** - Which files should I edit? CLAUDE.md or CLAUDE-USER-POLICIES.md?
4. **Artifact pollution** - Line 19 of settings.local.json contains entire commit message
5. **No validation** - Invalid permissions (multi-line strings, heredocs) not caught
6. **Stale system context** - Claude Code receives outdated/inaccurate NixOS system information
7. **Permission system unclear** - Dynamic permission creation system needs investigation and possible repair

**Impact**:
- Users might edit CLAUDE.md directly, changes get overwritten
- Generators could accidentally corrupt source files
- No feedback when violations occur
- Permission system has garbage data
- **Claude Code operates with inaccurate system context** - Recommendations and tool usage don't match actual NixOS configuration
- **Permission workflow uncertain** - Unknown whether dynamic permission generation works as intended

---

### Proposed Solution

**Implement explicit source/artifact separation architecture following Constitution Principle 1, with accurate NixOS system state reflection and working permission generation.**

**Key Components**:

1. **Explicit Declarations**
   - Every generator declares MANUAL_SOURCES and GENERATED_ARTIFACTS
   - Compile-time validation ensures no overlap

2. **Protective API**
   - `read_source(path)` - Read manual content
   - `write_artifact(path, content)` - Write generated content with validation
   - Raises error if trying to write to source

3. **Generation Headers**
   - All artifacts include HTML comment headers:
     ```html
     <!-- AUTO-GENERATED: Do not edit directly -->
     <!-- Source: ~/.claude/CLAUDE-USER-POLICIES.md -->
     <!-- Generated: 2025-10-10 18:27:31 -->
     ```

4. **Validation Pipeline** (Tiered Strictness)
   - **Critical validation (FAIL)**: Source protection, permission injection, schema compliance
   - **Content validation (WARN initially)**: Temporal markers, formatting, style guidelines
   - All validation uses Pydantic models for consistency

5. **NixOS System State Integration** (NEW)
   - Query actual NixOS configuration from `nixos-config` flake
   - Extract accurate installed packages, services, and system capabilities
   - Generate concise, accurate system context for CLAUDE.md
   - Trigger regeneration automatically on `./rebuild-nixos` completion
   - Ensure Claude Code always receives current system state

6. **Permission Generation Assessment & Fix** (NEW - Verified Working + Enhanced)
   - ✅ Current system verified as working (template-based, smart merging)
   - ✅ Enhancement: Add stricter validation (newlines, heredocs, length limits)
   - Validate permission syntax before writing to settings
   - Support project-specific permission patterns
   - Enable incremental permission additions without full regeneration

7. **Intelligent Permission Learning System** (NEW - Tier 1 Self-Improvement)
   - Log all permission approvals to history file during Claude Code sessions
   - Detect approval patterns using statistical analysis (min 3 occurrences, 30-day window)
   - Categorize patterns: git read-only, test execution, file operations, project access
   - Calculate confidence scores based on consistency and frequency
   - **Integrate with `./rebuild-nixos` workflow** as final interactive step
   - Present pattern suggestions with examples and impact preview
   - Apply accepted patterns automatically to project permissions
   - Track learned patterns with metadata for audit trail
   - Create feedback loop: **each system rebuild = smarter Claude Code**

8. **MCP Server Optimization System** (NEW - Tier 1 Self-Improvement)
   - Track MCP server token consumption and utilization rates per session
   - Calculate ROI scores: utility value / token cost for each server
   - Detect underutilized servers (loaded but rarely invoked)
   - Identify high-value servers for priority recommendations
   - Generate optimization suggestions during rebuild
   - Propose server removal/addition based on usage patterns
   - Update MCP configuration automatically on user approval

9. **CLAUDE.md Context Optimization** (NEW - Tier 1 Self-Improvement)
   - Track which tools/sections Claude Code actually references during sessions
   - Log tool mentions, section access patterns, and query relevance
   - Calculate "effective context" vs "loaded context" ratio
   - Identify noise: sections loaded but never referenced
   - Detect missing context: frequent queries for unavailable information
   - Reorder sections by access frequency (most-used at top)
   - Suggest pruning rarely-used content to reduce token overhead
   - Generate personalized "Quick Reference" section from hot paths

10. **Slash Command Workflow Detection** (NEW - Tier 2 Self-Improvement)
   - Log slash command sequences and timing patterns
   - Detect common workflows (e.g., `/speckit.specify` → `/speckit.clarify` → `/speckit.plan`)
   - Identify repetitive multi-command patterns
   - Calculate workflow completion rates and success indicators
   - Suggest workflow shortcuts or bundled commands
   - Generate project-specific slash command recommendations
   - Create workflow templates from observed patterns

11. **Instruction Effectiveness Tracking** (NEW - Tier 2 Self-Improvement)
   - Monitor adherence to CLAUDE.md policies during sessions
   - Detect instruction violations (e.g., unwanted doc creation, wrong tool selection)
   - Track which instructions are frequently ignored or misunderstood
   - Calculate effectiveness scores per instruction section
   - Identify ambiguous or conflicting guidance
   - Suggest instruction rewording for clarity
   - Add emphasis markers to frequently violated rules
   - Generate "learning report" showing policy adherence trends

12. **Cross-Project Knowledge Transfer** (NEW - Tier 3 Self-Improvement)
   - Learn patterns from one project and apply to others
   - Detect common project archetypes (Python/pytest, TypeScript/vitest, etc.)
   - Build knowledge base of effective configurations per project type
   - Transfer proven permission patterns across similar projects
   - Propagate successful CLAUDE.md customizations
   - Share learned workflows between projects with similar structures
   - Create "project profile templates" from successful configurations

13. **Meta-Learning Layer** (NEW - Tier 3 Self-Improvement)
   - Track effectiveness of the learning system itself
   - Monitor: suggestion acceptance rates, false positive patterns, user corrections
   - Adjust pattern detection thresholds based on acceptance feedback
   - Tune confidence scoring algorithms from actual outcomes
   - Learn which types of suggestions users find valuable
   - Optimize prompt timing and presentation format
   - Self-calibrate: system learns its own learning parameters
   - Generate "learning health" metrics and diagnostics

14. **User Guidance**
   - Git pre-commit hook warns when committing artifacts
   - Error messages point to correct source files
   - Documentation clearly separates sources vs artifacts

---

### Requirements

#### Functional Requirements

**FR-1: Source Protection**
- System MUST NOT allow generators to write to source files
- Attempting to write to source MUST raise exception
- Exception message MUST indicate which source was violated

**FR-2: Artifact Identification**
- All generated files MUST include generation header
- Header MUST indicate: DO NOT EDIT, source file, timestamp
- Header MUST use HTML comments for markdown files (invisible when rendered, visible in source)
- If header is manually deleted, next generation run MUST restore it automatically

**FR-3: Explicit Contracts**
- Each generator MUST declare MANUAL_SOURCES list
- Each generator MUST declare GENERATED_ARTIFACTS list
- System MUST validate no overlap at initialization

**FR-4: Permission Validation** (Critical - FAIL on violation)
- Permission strings MUST NOT contain newlines
- Permission strings MUST NOT contain heredoc markers (<<, EOF)
- Permission strings MUST be ≤200 characters
- Invalid permissions MUST be rejected with clear error and generation halted

**FR-5: Content Validation** (Style - WARN initially, promote to FAIL later)
- Generated docs SHOULD NOT contain temporal markers (NEW, Week 1, Phase 2) - warns if present
- Generated docs MUST have proper section markers - fails if missing
- Templates MUST render without errors - fails on template errors

**FR-6: User Guidance**
- Git hook MUST detect when committing generated artifacts (e.g., CLAUDE.md)
- Hook MUST show warning with correct source file suggestion
- Hook MUST prompt user interactively: "Are you sure? (y/n)"
- Answer "n" MUST abort commit; "y" MUST allow commit to proceed
- Error messages MUST be actionable

**FR-7: NixOS System State Synchronization** (NEW)
- System MUST query actual NixOS configuration from `nixos-config` flake
- System MUST extract installed packages, services, and enabled features
- Generated CLAUDE.md MUST reflect current system state accurately
- System MUST trigger regeneration hook on `./rebuild-nixos` completion
- System context MUST be concise (prioritize active/relevant tools)
- Stale data MUST be detected and flagged (timestamp-based freshness check)

**FR-8: Permission Generation** (NEW - Verified Working, Enhanced)
- System MUST validate permission syntax before persisting to settings
- System MUST support dynamic permission creation for new project patterns
- System MUST prevent injection of malformed permissions (newlines, heredocs, excessive length)
- System MUST support incremental permission additions
- System MUST provide clear error messages when permission validation fails
- System MUST include enhanced validation for newlines, heredocs, and length limits

**FR-9: Intelligent Permission Learning** (NEW - Tier 1 Self-Improvement)
- System MUST log all permission approvals to history file (~/.claude/approval-history.jsonl)
- System MUST detect patterns in approval history (minimum 3 occurrences within 30 days)
- System MUST categorize patterns: git commands, test runners, file operations, project directories
- System MUST suggest generalizations interactively during `./rebuild-nixos`
- System MUST show: approved examples, what would be allowed, what would still ask
- System MUST calculate confidence scores for each pattern suggestion
- System MUST allow user to accept/reject suggestions with [Y/n] prompts
- System MUST apply accepted patterns to project settings.local.json
- System MUST track learned patterns separately with metadata (_learned_patterns)
- System MUST integrate with rebuild-nixos workflow as final step
- System MUST create progressive intelligence: each rebuild improves Claude Code behavior

**FR-10: MCP Server Optimization** (NEW - Tier 1 Self-Improvement)
- System MUST track token consumption per MCP server per session
- System MUST calculate utilization metrics: invocations, success rate, average response time
- System MUST compute ROI scores: (utility_value / token_cost) for each server
- System MUST detect underutilized servers (loaded >5 sessions but invoked <5% of time)
- System MUST identify high-value servers (high invocation rate, low token overhead)
- System MUST log metrics to ~/.claude/mcp-analytics.jsonl
- System MUST scan ALL projects system-wide during rebuild (not just nixos-config)
- System MUST aggregate MCP usage across all projects for global view
- System MUST distinguish between global servers (~/.claude.json) and project-specific servers
- System MUST generate optimization report during rebuild: servers to remove/add/prioritize
- System MUST update .claude/mcp.json on user approval with learned configuration
- System MUST preserve manual MCP customizations (_user_mcp_override marker)

**FR-11: CLAUDE.md Context Optimization** (NEW - Tier 1 Self-Improvement)
- System MUST log which CLAUDE.md sections Claude references during sessions
- System MUST track tool mentions, command usage, and section access patterns
- System MUST calculate "effective context ratio": referenced_tokens / total_loaded_tokens
- System MUST identify noise sections: loaded but never referenced in 30+ days
- System MUST detect context gaps: Claude queries for info not in CLAUDE.md
- System MUST reorder sections by access frequency (hot paths first)
- System MUST generate "Quick Reference" section from top 20% most-accessed content
- System MUST suggest pruning low-value sections to reduce token overhead
- System MUST propose adding missing frequently-queried information
- System MUST log analytics to ~/.claude/context-analytics.jsonl

**FR-12: Slash Command Workflow Detection** (NEW - Tier 2 Self-Improvement)
- System MUST log slash command invocations with timestamps
- System MUST detect multi-command sequences (e.g., `/speckit.specify` → `/speckit.clarify`)
- System MUST identify repetitive patterns (≥3 occurrences of same sequence)
- System MUST calculate workflow success rates and completion metrics
- System MUST suggest workflow bundling when sequences occur frequently
- System MUST generate project-specific slash command suggestions
- System MUST create workflow templates from observed successful patterns
- System MUST log workflow analytics to ~/.claude/workflow-analytics.jsonl

**FR-13: Instruction Effectiveness Tracking** (NEW - Tier 2 Self-Improvement)
- System MUST monitor Claude Code adherence to CLAUDE.md policies
- System MUST detect policy violations: unwanted doc creation, wrong tool usage, ignored warnings
- System MUST track violation frequency per instruction section
- System MUST calculate effectiveness score per policy: (compliant_sessions / total_sessions)
- System MUST identify ambiguous instructions (frequently violated or misunderstood)
- System MUST suggest instruction rewording for low-effectiveness policies (<70%)
- System MUST add emphasis to frequently violated rules (e.g., **CRITICAL:** markers)
- System MUST generate "Policy Adherence Report" during rebuild
- System MUST log instruction analytics to ~/.claude/instruction-analytics.jsonl

**FR-14: Cross-Project Knowledge Transfer** (NEW - Tier 3 Self-Improvement)
- System MUST detect project archetypes: Python/pytest, TypeScript/vitest, Rust/cargo, etc.
- System MUST build knowledge base of effective configurations per archetype
- System MUST transfer proven permission patterns to new projects of same type
- System MUST propagate successful CLAUDE.md customizations across similar projects
- System MUST share learned workflows between projects with matching structure
- System MUST create "project profile templates" from successful configurations
- System MUST log cross-project patterns to ~/.claude/project-patterns.jsonl
- System MUST prompt: "Apply Python/pytest patterns from project X to project Y? [Y/n]"

**FR-15: Meta-Learning Layer** (NEW - Tier 3 Self-Improvement)
- System MUST track learning system effectiveness metrics
- System MUST monitor: suggestion acceptance rate, false positive rate, user corrections
- System MUST adjust pattern detection thresholds based on acceptance feedback
- System MUST tune confidence scoring algorithms from actual outcomes
- System MUST learn which suggestion types users find valuable vs annoying
- System MUST optimize prompt timing (not too early, not too late)
- System MUST self-calibrate: adapt min_occurrences, time windows, confidence thresholds
- System MUST generate "Learning Health Report" with diagnostics
- System MUST log meta-learning metrics to ~/.claude/meta-learning.jsonl

#### Non-Functional Requirements

**NFR-1: Performance**
- Validation overhead MUST be <1 second per generator
- Full rebuild MUST complete in <10 seconds

**NFR-2: Backward Compatibility**
- Existing source files (CLAUDE-USER-POLICIES.md) MUST continue working without modification
- Existing templates MUST work with new headers
- System MUST handle artifacts both with and without headers gracefully
- Migration script MUST be provided to add headers to existing artifacts
- Next generation run MUST automatically add headers to any artifacts lacking them

**NFR-3: Testability**
- Each validation rule MUST have unit test
- Generator contracts MUST be testable
- Integration tests MUST verify end-to-end

**NFR-4: Maintainability**
- Adding new generator MUST be straightforward
- Declarations MUST be self-documenting
- Violations MUST be caught at development time

---

### Acceptance Criteria

**AC-1: Source Protection Works**
```python
# Test case
def test_cannot_write_to_source():
    gen = SystemGenerator()
    with pytest.raises(ValueError, match="overwrite source"):
        gen.write_artifact(
            Path("CLAUDE-USER-POLICIES.md"),
            "content"
        )
```

**AC-2: Artifacts Have Headers**
```python
# Test case
def test_artifact_has_header():
    gen = SystemGenerator()
    gen.generate()

    artifact = Path("~/.claude/CLAUDE.md").read_text()
    assert "<!-- AUTO-GENERATED:" in artifact
    assert "DO NOT EDIT" in artifact
```

**AC-3: Permission Validation**
```python
# Test case
def test_permission_validation():
    validator = PermissionValidator()

    # Valid
    assert validator.validate("Bash(git status:*)")

    # Invalid - multi-line
    with pytest.raises(ValueError):
        validator.validate("Bash(git commit -m 'line1\nline2')")

    # Invalid - too long
    with pytest.raises(ValueError):
        validator.validate("Bash(" + "x" * 201 + ")")
```

**AC-4: Git Hook Interactive Prompt**
```bash
# Test case 1: User aborts
echo "test" >> CLAUDE.md
git add CLAUDE.md
git commit -m "test"

# Expected output:
# ⚠️  WARNING: Committing CLAUDE.md (artifact)
# Did you mean to edit:
#   ✏️  ~/.claude/CLAUDE-USER-POLICIES.md
# Are you sure? (y/n): n
# Commit aborted.

# Test case 2: User confirms
git commit -m "test"
# Are you sure? (y/n): y
# [Commit proceeds normally]
```

**AC-5: Dynamic Context Preserves Manual Content**
```python
# Test case
def test_dynamic_context_preserves_policies():
    # Setup: User policies exist
    policies = Path("~/.claude/CLAUDE-USER-POLICIES.md")
    policies.write_text("# My Custom Policy\n...")

    # Generate dynamic context
    gen = DynamicContextGenerator()
    gen.generate(project_path=Path("~/project"))

    # Verify: Policies included in artifact
    artifact = Path("~/project/CLAUDE.md").read_text()
    assert "# My Custom Policy" in artifact
```

**AC-6: Migration Script Works**
```bash
# Test case 1: Add headers to existing artifacts
./scripts/migrate-add-headers.sh

# Verify headers added
grep -q "AUTO-GENERATED" ~/.claude/CLAUDE.md

# Test case 2: Idempotency - run twice
./scripts/migrate-add-headers.sh
./scripts/migrate-add-headers.sh

# Verify only one header (not duplicated)
[ $(grep -c "AUTO-GENERATED" ~/.claude/CLAUDE.md) -eq 1 ]
```

**AC-7: Intelligent Permission Learning**
```python
# Test case 1: Pattern detection
def test_pattern_detection():
    tracker = ApprovalTracker()

    # Simulate 3 git approvals
    tracker.log_approval("Bash(git status:*)")
    tracker.log_approval("Bash(git diff:*)")
    tracker.log_approval("Bash(git log:*)")

    # Detect pattern
    detector = PermissionPatternDetector(tracker)
    patterns = detector.detect_patterns(min_occurrences=3)

    assert len(patterns) >= 1
    assert patterns[0].pattern_type == "git_read_only"
    assert patterns[0].confidence > 0.8

# Test case 2: Integration with rebuild
# User runs: cd ~/nixos-config && ./rebuild-nixos
# Expected at end of rebuild:
#
# 🤖 Updating Claude Code system context...
# ✅ System CLAUDE.md regenerated (127 packages)
#
# 🧠 Analyzing permission patterns...
# ============================================================
# 🧠 Pattern Detected: Git read-only commands
# ============================================================
# [Interactive prompt appears]
# Add this permission pattern? [Y/n]: y
# ✅ Applied 1 learned permission pattern
#
# ✅ Claude Code context refreshed
```

**AC-8: Rebuild Integration**
```bash
# Test case: Verify rebuild workflow integration
cd ~/nixos-config
./rebuild-nixos

# Expected workflow:
# 1. NixOS rebuild happens
# 2. System CLAUDE.md regenerated automatically
# 3. Permission learning triggered
# 4. User prompted for pattern approvals
# 5. Accepted patterns applied
# 6. Summary printed

# Verify CLAUDE.md updated
stat -c %Y ~/.claude/CLAUDE.md  # Should be recent timestamp

# Verify learning happened
cat ~/.claude/approval-history.jsonl | tail -5  # Should show recent activity

# Verify patterns applied (if any accepted)
jq '.permissions.allow' .claude/settings.local.json | grep -q "git"
```

**AC-9: MCP Server Optimization Works**
```python
# Test case 1: Global multi-project discovery
def test_global_mcp_discovery():
    analyzer = GlobalMCPAnalyzer(Path.home())
    projects = analyzer.discover_projects()

    # Should find all projects with .claude/mcp.json
    assert len(projects) >= 3  # nixos-config, whatsapp-mcp, sunsama-mcp
    assert any("whatsapp" in str(p) for p in projects)
    assert any("sunsama" in str(p) for p in projects)

# Test case 2: Aggregate usage across projects
def test_global_usage_aggregation():
    analyzer = GlobalMCPAnalyzer(Path.home())
    report = analyzer.analyze_all_projects()

    # Should aggregate servers from all projects
    assert report['total_projects'] > 1
    assert len(report['servers']) > 0

    # Should distinguish global vs project-specific
    global_servers = [s for s in report['servers'] if 'global' in s.config_location.lower()]
    project_servers = [s for s in report['servers'] if 'project' in s.config_location.lower()]

    assert len(global_servers) > 0  # sequential-thinking from ~/.claude.json
    assert len(project_servers) > 0  # serena from various projects

# Test case 3: Detect underutilized servers
def test_underutilized_detection():
    analyzer = GlobalMCPAnalyzer(Path.home())
    report = analyzer.analyze_all_projects()

    # Find poor utilization recommendations
    poor_util = [
        r for r in report['recommendations']
        if r.recommendation_type == "poor_utilization"
    ]

    # Each should identify project context
    for rec in poor_util:
        assert "[" in rec.action  # Project name in brackets

# Test case 4: Rebuild integration output
# Expected during rebuild:
#
# 🧠 Running adaptive learning cycle...
#
# 🌐 Global MCP Analysis
#   Projects: 6 scanned
#   Servers: 3/4 connected
#   Global: 1 | Project-specific: 3
#
# 📊 MCP Optimizations (2):
#   • serena: High value - 45 calls, 8K tokens, ROI: 5.6
#   • sequential-thinking: Poor utilization - 15% (3/20 sessions)
#     [whatsapp-mcp] Consider moving to project-level config
#
# Apply MCP optimization? [Y/n]:
```

**AC-10: CLAUDE.md Context Optimization Works**
```python
# Test case 1: Track section access
def test_section_tracking():
    tracker = ContextUsageTracker()

    # Simulate Claude referencing tools section
    tracker.log_access(
        section="Modern CLI Tools",
        tokens_in_section=2500,
        relevance_score=0.9
    )

    # Calculate effective context ratio
    ratio = tracker.get_effective_ratio(days=30)
    assert 0 < ratio <= 1.0

# Test case 2: Identify noise sections
def test_noise_detection():
    optimizer = ContextOptimizer()

    suggestions = optimizer.analyze()

    # Find sections loaded but never referenced
    noise = [s for s in suggestions if s.type == "PRUNE_SECTION"]
    assert len(noise) >= 0  # May be empty if all sections used

# Test case 3: Rebuild integration
# Expected output during rebuild:
#
# 🧹 CLAUDE.md Context Analysis:
#
# Effective Context Ratio: 67% (10K used / 15K loaded)
#
# ✂️  Suggested Pruning (save 3K tokens):
#   • Fish abbreviations (loaded 15x, referenced 0x)
#   • Legacy tool docs (loaded 15x, referenced 1x)
#
# Prune low-value sections? [Y/n]:
```

**AC-11: Workflow Detection Works**
```python
# Test case 1: Detect command sequences
def test_workflow_detection():
    detector = WorkflowDetector()

    # Log sequence 3 times
    for _ in range(3):
        detector.log_command("/speckit.specify")
        detector.log_command("/speckit.clarify")
        detector.log_command("/speckit.plan")

    # Detect pattern
    workflows = detector.detect_patterns(min_occurrences=3)

    assert len(workflows) >= 1
    assert workflows[0].commands == [
        "/speckit.specify",
        "/speckit.clarify",
        "/speckit.plan"
    ]

# Test case 2: Suggest workflow bundling
# Expected output during rebuild:
#
# 🔄 Workflow Pattern Detected:
#
# You frequently run:
#   1. /speckit.specify
#   2. /speckit.clarify
#   3. /speckit.plan
#
# (3 times in last 30 days, 100% completion rate)
#
# Create bundled command '/speckit.full-plan'? [Y/n]:
```

**AC-12: Instruction Effectiveness Tracking Works**
```python
# Test case 1: Detect policy violations
def test_violation_detection():
    tracker = InstructionEffectivenessTracker()

    # Simulate session with unwanted doc creation (violates policy)
    tracker.log_session(
        policy="documentation-creation",
        compliant=False,
        violation_type="created_md_without_approval"
    )

    # Calculate effectiveness
    score = tracker.get_effectiveness_score("documentation-creation")
    assert 0 <= score <= 1.0

# Test case 2: Suggest instruction rewording
# Expected output during rebuild:
#
# 📋 Instruction Effectiveness Report:
#
# ⚠️  Low-Effectiveness Policies (<70%):
#
# • "Documentation Creation Policy" - 45% compliance
#   Violations: Created .md files without asking (8 times)
#   Suggestion: Add **CRITICAL:** prefix and rephrase
#
# Apply suggested emphasis? [Y/n]:
```

**AC-13: Cross-Project Knowledge Transfer Works**
```python
# Test case 1: Detect project archetype
def test_archetype_detection():
    detector = ProjectArchetypeDetector()

    archetype = detector.detect(Path("~/new-python-project"))

    assert archetype == "Python/pytest"

# Test case 2: Transfer patterns
# Expected when creating new Python project:
#
# 🎯 Project Archetype Detected: Python/pytest
#
# Apply patterns learned from 'claude-nixos-automation'?
#   ✓ Pytest permissions (--cov, --verbose)
#   ✓ Ruff permissions (check, format)
#   ✓ Python file access patterns
#
# Transfer these patterns? [Y/n]:
```

**AC-14: Meta-Learning Works**
```python
# Test case 1: Track suggestion acceptance
def test_meta_learning():
    meta = MetaLearner()

    # Log suggestion outcomes
    meta.log_suggestion(
        type="permission_pattern",
        accepted=True,
        confidence=0.85
    )

    meta.log_suggestion(
        type="permission_pattern",
        accepted=False,  # User rejected
        confidence=0.60
    )

    # Adjust thresholds based on feedback
    new_threshold = meta.get_adjusted_threshold("permission_pattern")

    # Should increase threshold since low-confidence was rejected
    assert new_threshold > 0.60

# Test case 2: Learning health report
# Expected output during rebuild:
#
# 🔬 Learning System Health Report:
#
# Suggestion Acceptance Rates:
#   • Permission patterns: 85% (17/20)
#   • MCP optimizations: 100% (3/3)
#   • Context pruning: 60% (3/5)
#
# Adjustments Made:
#   • Increased min_occurrences: 3 → 4 (reduce false positives)
#   • Lowered confidence threshold: 0.8 → 0.75 (user trusts suggestions)
#
# System is learning effectively ✅
```

---

### Constraints

**C-1: No Breaking Changes**
- Existing CLAUDE-USER-POLICIES.md files MUST continue working
- Existing workflow (rebuild-nixos) MUST not break
- Users MUST NOT need to modify their source files

**C-2: Minimal Dependencies**
- No new external dependencies
- Use existing Pydantic for validation
- Use existing Jinja2 for templates

**C-3: Clear Migration Path**
- Provide migration script: `scripts/migrate-add-headers.sh`
- Script MUST be idempotent (safe to run multiple times)
- Script MUST detect existing headers and skip those files
- Automatic migration on next generation run (headers added if missing)
- Document migration process with before/after examples

**C-4: Performance Budget**
- Validation: <1 second
- Full generation: <10 seconds
- Tests: <30 seconds

---

### Out of Scope

**OS-1: Dynamic Context Filtering** (Separate spec)
- Project-aware tool filtering
- Usage-based prioritization
- Task-specific loading

**OS-2: Intelligence Layer** (Separate spec)
- Git history mining
- Dependency analysis
- Cross-project patterns

**OS-3: Permission Analytics** (Separate spec)
- Effectiveness tracking
- Usage logging
- Recommendation engine

---

### Technical Design (High-Level)

#### Component Architecture

```python
# claude_automation/generators/base_generator.py

class BaseGenerator(ABC):
    """Base class enforcing source/artifact separation."""

    # Subclasses MUST override these
    MANUAL_SOURCES: List[str] = []
    GENERATED_ARTIFACTS: List[str] = []

    def __init__(self):
        self._validate_declarations()

    def _validate_declarations(self):
        """Ensure no overlap between sources and artifacts."""
        overlap = set(self.MANUAL_SOURCES) & set(self.GENERATED_ARTIFACTS)
        if overlap:
            raise ValueError(f"Source/artifact overlap: {overlap}")

    def read_source(self, path: Path) -> str:
        """Read manual source content."""
        if path.name not in self.MANUAL_SOURCES:
            logger.warning(f"Reading undeclared source: {path}")
        return path.read_text()

    def write_artifact(self, path: Path, content: str):
        """Write generated artifact with validation.

        Always adds generation header, even if manually deleted previously.
        This ensures artifacts are always identifiable as generated.
        """
        # 1. Validate not a source
        if path.name in self.MANUAL_SOURCES:
            raise ValueError(f"Cannot overwrite source: {path}")

        # 2. Validate is a declared artifact
        if path.name not in self.GENERATED_ARTIFACTS:
            raise ValueError(f"Undeclared artifact: {path}")

        # 3. Add generation header (always, even if previously deleted)
        header = self._generate_header(path)
        final_content = f"{header}\n\n{content}"

        # 4. Write
        path.write_text(final_content)

    def _generate_header(self, path: Path) -> str:
        """Generate header for artifact."""
        return f"""<!--
{'=' * 60}
  AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY

  Generated: {datetime.now().isoformat()}
  Generator: {self.__class__.__name__}

  To modify, edit source files and regenerate.
{'=' * 60}
-->"""

    @abstractmethod
    def generate(self):
        """Generate artifact by merging sources."""
        pass
```

#### Example Usage

```python
# claude_automation/generators/system_generator.py

class SystemGenerator(BaseGenerator):
    # Explicit declarations
    MANUAL_SOURCES = ["CLAUDE-USER-POLICIES.md"]
    GENERATED_ARTIFACTS = ["CLAUDE.md"]

    def generate(self):
        # Read manual source
        policies = self.read_source(
            Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
        )

        # Generate auto content
        tools = self._generate_tools()

        # Merge via template
        content = self.template.render(
            user_policies=policies,
            tools=tools
        )

        # Write artifact (validated)
        self.write_artifact(
            Path.home() / ".claude" / "CLAUDE.md",
            content
        )
```

---

### Intelligent Permission Learning Architecture

#### Workflow Integration with `./rebuild-nixos`

```bash
#!/usr/bin/env bash
# ~/nixos-config/rebuild-nixos

set -e

echo "🔧 Rebuilding NixOS configuration..."

# 1. Standard NixOS rebuild
sudo nixos-rebuild switch --flake .

# 2. Update home-manager if needed
home-manager switch --flake .

# 3. INTEGRATION: Update Claude Code context automatically
if [[ -d ~/claude-nixos-automation ]]; then
    echo ""
    echo "🤖 Updating Claude Code system context..."

    # Run system context update
    python3 ~/claude-nixos-automation/update-system-claude-v2.py

    # Run intelligent permission learning
    echo ""
    echo "🧠 Analyzing permission patterns..."
    python3 ~/claude-nixos-automation/update-permissions-with-learning.py \
        --interactive \
        --global  # Apply to all projects globally

    echo ""
    echo "✅ Claude Code context refreshed"
fi

echo "✅ System rebuild complete!"
```

#### Permission Learning Components

```python
# claude_automation/analyzers/approval_tracker.py

class ApprovalTracker:
    """Logs permission approvals across Claude Code sessions."""

    def __init__(self):
        self.history_file = Path.home() / ".claude" / "approval-history.jsonl"
        self.history_file.parent.mkdir(exist_ok=True)

    def log_approval(self, permission: str, context: dict = None):
        """Log a permission approval (called by Claude Code hook)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "permission": permission,
            "session_id": os.getenv("CLAUDE_SESSION_ID", "unknown"),
            "project_path": str(Path.cwd()),
            "context": context or {}
        }

        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def get_recent_approvals(self, days: int = 30) -> list[dict]:
        """Get approvals from last N days."""
        if not self.history_file.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        approvals = []

        with open(self.history_file) as f:
            for line in f:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry['timestamp'])
                if ts > cutoff:
                    approvals.append(entry)

        return approvals


# claude_automation/analyzers/permission_pattern_detector.py

class PermissionPatternDetector:
    """Detects patterns in permission approvals."""

    PATTERN_DETECTORS = {
        'git_read_only': lambda cmds: _detect_git_readonly(cmds),
        'git_all_safe': lambda cmds: _detect_git_all_safe(cmds),
        'pytest': lambda cmds: _detect_pytest(cmds),
        'ruff': lambda cmds: _detect_ruff(cmds),
        'modern_cli': lambda cmds: _detect_modern_cli(cmds),
        'project_full_access': lambda approvals: _detect_project_access(approvals)
    }

    def detect_patterns(self, min_occurrences: int = 3) -> list[PatternSuggestion]:
        """Detect patterns worth suggesting."""
        tracker = ApprovalTracker()
        approvals = tracker.get_recent_approvals(days=30)

        patterns = []
        for pattern_type, detector_func in self.PATTERN_DETECTORS.items():
            suggestion = detector_func(approvals)
            if suggestion and self._meets_threshold(suggestion, min_occurrences):
                patterns.append(suggestion)

        # Sort by confidence (highest first)
        return sorted(patterns, key=lambda p: p.confidence, reverse=True)


# claude_automation/generators/intelligent_permissions_generator.py

class IntelligentPermissionsGenerator(PermissionsGenerator):
    """Permission generator with learning."""

    def generate_with_learning(
        self,
        global_mode: bool = False,
        interactive: bool = True
    ) -> GenerationResult:
        """
        Generate permissions with pattern learning.

        Args:
            global_mode: If True, apply to ~/.claude.json (all projects)
                        If False, apply to current project .claude/settings.local.json
            interactive: If True, prompt user for approval
        """
        # Detect patterns
        detector = PermissionPatternDetector()
        patterns = detector.detect_patterns(min_occurrences=3)

        if not patterns:
            print("No new patterns detected. Keep using Claude Code!")
            return GenerationResult(success=True, output_path="", stats={})

        # Filter already-applied patterns
        if global_mode:
            settings_file = Path.home() / ".claude.json"
        else:
            settings_file = Path.cwd() / ".claude" / "settings.local.json"

        new_patterns = self._filter_new_patterns(patterns, settings_file)

        if not new_patterns:
            print("All detected patterns already configured!")
            return GenerationResult(success=True, output_path="", stats={})

        # Interactive approval
        accepted = []
        if interactive:
            for pattern in new_patterns[:5]:  # Max 5 per session
                if self._prompt_for_pattern(pattern):
                    accepted.append(pattern)
        else:
            accepted = new_patterns

        # Apply accepted patterns
        if accepted:
            self._apply_patterns(settings_file, accepted)
            print(f"✅ Applied {len(accepted)} learned permission pattern(s)")

        return GenerationResult(
            success=True,
            output_path=str(settings_file),
            stats={'learned_patterns': len(accepted)}
        )

    def _prompt_for_pattern(self, pattern: PatternSuggestion) -> bool:
        """Prompt user interactively."""
        print("\n" + "="*60)
        print(f"🧠 Pattern Detected: {pattern.description}")
        print("="*60)

        print(f"\n📊 Based on your recent approvals:")
        for ex in pattern.approved_examples[:5]:
            print(f"  ✓ {ex}")

        print(f"\n✅ This would automatically allow:")
        for item in pattern.would_allow[:5]:
            print(f"  • {item}")

        if pattern.would_still_ask:
            print(f"\n❓ Would still ask for:")
            for item in pattern.would_still_ask[:3]:
                print(f"  • {item}")

        print(f"\n🎯 Proposed rule: {pattern.proposed_rule}")
        print(f"📈 Confidence: {pattern.confidence*100:.0f}%")

        try:
            response = input("\nAdd this permission pattern? [Y/n]: ").strip().lower()
            return response in ['', 'y', 'yes']
        except (KeyboardInterrupt, EOFError):
            print("\nSkipped.")
            return False
```

#### Update Script Integration

```python
#!/usr/bin/env python3
# update-permissions-with-learning.py

"""
Intelligent permission learning and application.
Analyzes approval history, detects patterns, suggests generalizations.
Designed to run at end of ./rebuild-nixos workflow.
"""

import argparse
from pathlib import Path
from claude_automation.generators.intelligent_permissions_generator import (
    IntelligentPermissionsGenerator
)

def main():
    parser = argparse.ArgumentParser(
        description="Learn and apply permission patterns from approval history"
    )
    parser.add_argument(
        '--global',
        dest='global_mode',
        action='store_true',
        help='Apply to global ~/.claude.json (all projects)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Prompt for approval (default: True)'
    )
    parser.add_argument(
        '--min-occurrences',
        type=int,
        default=3,
        help='Minimum approval count to suggest pattern (default: 3)'
    )

    args = parser.parse_args()

    generator = IntelligentPermissionsGenerator()
    result = generator.generate_with_learning(
        global_mode=args.global_mode,
        interactive=args.interactive
    )

    if result.success:
        if result.stats.get('learned_patterns', 0) > 0:
            print(f"\n🧠 Learned {result.stats['learned_patterns']} new pattern(s)")
        return 0
    else:
        print("❌ Learning failed")
        return 1

if __name__ == '__main__':
    exit(main())
```

---

### Unified Self-Improvement Architecture

#### AdaptiveSystemEngine (Central Coordinator)

The AdaptiveSystemEngine orchestrates all self-improving components as a unified system, coordinating learning across permissions, MCP servers, context, workflows, instructions, cross-project patterns, and meta-learning.

```python
# claude_automation/core/adaptive_system_engine.py

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import logging

from ..analyzers.approval_tracker import ApprovalTracker
from ..analyzers.permission_pattern_detector import PermissionPatternDetector
from ..analyzers.mcp_optimizer import MCPOptimizer
from ..analyzers.context_optimizer import ContextOptimizer
from ..analyzers.workflow_detector import WorkflowDetector
from ..analyzers.instruction_tracker import InstructionEffectivenessTracker
from ..analyzers.project_archetype_detector import ProjectArchetypeDetector
from ..analyzers.meta_learner import MetaLearner

logger = logging.getLogger(__name__)


@dataclass
class LearningReport:
    """Consolidated report from all learners."""
    permission_patterns: List[dict]
    mcp_optimizations: List[dict]
    context_suggestions: List[dict]
    workflow_patterns: List[dict]
    instruction_improvements: List[dict]
    cross_project_transfers: List[dict]
    meta_insights: Dict[str, float]
    total_suggestions: int
    estimated_improvements: str


class AdaptiveSystemEngine:
    """
    Central coordinator for all self-improving components.

    Runs during ./rebuild-nixos to:
    1. Collect insights from all learners
    2. Prioritize suggestions by impact
    3. Present consolidated report
    4. Apply user-approved improvements
    5. Update meta-learning parameters
    """

    def __init__(self, interactive: bool = True):
        self.interactive = interactive

        # Initialize all learners
        self.permission_learner = PermissionPatternDetector()
        self.mcp_optimizer = MCPOptimizer()
        self.context_optimizer = ContextOptimizer()
        self.workflow_detector = WorkflowDetector()
        self.instruction_tracker = InstructionEffectivenessTracker()
        self.archetype_detector = ProjectArchetypeDetector()
        self.meta_learner = MetaLearner()

    def run_full_learning_cycle(self) -> LearningReport:
        """
        Run complete learning cycle across all components.

        Called by ./rebuild-nixos as final step.
        """
        logger.info("🧠 Starting adaptive learning cycle...")

        # Phase 1: Collect insights
        permission_patterns = self._analyze_permissions()
        mcp_suggestions = self._analyze_mcp_servers()
        context_suggestions = self._analyze_context()
        workflow_patterns = self._analyze_workflows()
        instruction_improvements = self._analyze_instructions()
        cross_project_patterns = self._analyze_cross_project()
        meta_insights = self._analyze_meta_learning()

        # Phase 2: Prioritize suggestions
        report = self._build_report(
            permission_patterns,
            mcp_suggestions,
            context_suggestions,
            workflow_patterns,
            instruction_improvements,
            cross_project_patterns,
            meta_insights
        )

        # Phase 3: Interactive approval (if enabled)
        if self.interactive and report.total_suggestions > 0:
            self._present_report(report)
            approved = self._collect_approvals(report)
            self._apply_improvements(approved)

        # Phase 4: Update meta-learning
        self._update_meta_learning(report, approved if self.interactive else [])

        logger.info("✅ Learning cycle complete")
        return report

    def _analyze_permissions(self) -> List[dict]:
        """Detect permission patterns from approval history."""
        patterns = self.permission_learner.detect_patterns(min_occurrences=3)
        return [p.to_dict() for p in patterns[:5]]  # Top 5

    def _analyze_mcp_servers(self) -> List[dict]:
        """Analyze MCP server utilization and ROI across ALL projects."""
        # Use global analyzer instead of project-scoped
        from ..analyzers.global_mcp_analyzer import GlobalMCPAnalyzer

        global_analyzer = GlobalMCPAnalyzer(Path.home())
        report = global_analyzer.analyze_all_projects()

        # Convert to suggestions format
        suggestions = []
        for rec in report['recommendations'][:3]:  # Top 3
            suggestions.append({
                'description': rec.reason,
                'impact': rec.action,
                'priority': rec.priority,
            })
        return suggestions

    def _analyze_context(self) -> List[dict]:
        """Identify CLAUDE.md optimization opportunities."""
        suggestions = self.context_optimizer.analyze()
        return [s.to_dict() for s in suggestions[:3]]  # Top 3

    def _analyze_workflows(self) -> List[dict]:
        """Detect repeated slash command patterns."""
        workflows = self.workflow_detector.detect_patterns(min_occurrences=3)
        return [w.to_dict() for w in workflows[:3]]  # Top 3

    def _analyze_instructions(self) -> List[dict]:
        """Find low-effectiveness instructions needing improvement."""
        improvements = self.instruction_tracker.suggest_improvements()
        return [i.to_dict() for i in improvements[:3]]  # Top 3

    def _analyze_cross_project(self) -> List[dict]:
        """Identify cross-project pattern transfer opportunities."""
        transfers = self.archetype_detector.find_transfer_opportunities()
        return [t.to_dict() for t in transfers[:2]]  # Top 2

    def _analyze_meta_learning(self) -> Dict[str, float]:
        """Analyze learning system effectiveness."""
        return self.meta_learner.get_health_metrics()

    def _build_report(
        self,
        permissions: List[dict],
        mcp: List[dict],
        context: List[dict],
        workflows: List[dict],
        instructions: List[dict],
        cross_project: List[dict],
        meta: Dict[str, float]
    ) -> LearningReport:
        """Build consolidated learning report."""
        total = (
            len(permissions) +
            len(mcp) +
            len(context) +
            len(workflows) +
            len(instructions) +
            len(cross_project)
        )

        # Estimate improvements
        estimated = self._estimate_improvements(
            permissions, mcp, context, workflows, instructions
        )

        return LearningReport(
            permission_patterns=permissions,
            mcp_optimizations=mcp,
            context_suggestions=context,
            workflow_patterns=workflows,
            instruction_improvements=instructions,
            cross_project_transfers=cross_project,
            meta_insights=meta,
            total_suggestions=total,
            estimated_improvements=estimated
        )

    def _present_report(self, report: LearningReport):
        """Present consolidated report to user."""
        print("\n" + "="*70)
        print("🧠 ADAPTIVE SYSTEM LEARNING REPORT")
        print("="*70)

        if report.permission_patterns:
            print(f"\n📋 Permission Patterns ({len(report.permission_patterns)}):")
            for p in report.permission_patterns:
                print(f"  • {p['description']} (confidence: {p['confidence']:.0%})")

        if report.mcp_optimizations:
            print(f"\n📊 MCP Optimizations ({len(report.mcp_optimizations)}):")
            for m in report.mcp_optimizations:
                print(f"  • {m['description']} ({m['impact']})")

        if report.context_suggestions:
            print(f"\n🧹 Context Optimizations ({len(report.context_suggestions)}):")
            for c in report.context_suggestions:
                print(f"  • {c['description']} (save {c['tokens']} tokens)")

        if report.workflow_patterns:
            print(f"\n🔄 Workflow Patterns ({len(report.workflow_patterns)}):")
            for w in report.workflow_patterns:
                print(f"  • {w['description']} ({w['occurrences']}x)")

        if report.instruction_improvements:
            print(f"\n📝 Instruction Improvements ({len(report.instruction_improvements)}):")
            for i in report.instruction_improvements:
                print(f"  • {i['policy']} - {i['compliance']}% compliance")

        if report.cross_project_transfers:
            print(f"\n🔗 Cross-Project Transfers ({len(report.cross_project_transfers)}):")
            for t in report.cross_project_transfers:
                print(f"  • {t['description']}")

        print(f"\n📈 Estimated Improvements: {report.estimated_improvements}")

        print("\n" + "="*70)

    def _collect_approvals(self, report: LearningReport) -> List[dict]:
        """Interactively collect user approvals."""
        approved = []

        # Present each suggestion category
        categories = [
            ("Permissions", report.permission_patterns),
            ("MCP", report.mcp_optimizations),
            ("Context", report.context_suggestions),
            ("Workflows", report.workflow_patterns),
            ("Instructions", report.instruction_improvements),
            ("Cross-Project", report.cross_project_transfers)
        ]

        for category_name, suggestions in categories:
            if not suggestions:
                continue

            print(f"\n{'─'*70}")
            print(f"Review {category_name} Suggestions:")

            for idx, suggestion in enumerate(suggestions, 1):
                self._present_suggestion(category_name, idx, suggestion)

                try:
                    response = input(f"\nApply this? [Y/n]: ").strip().lower()
                    if response in ['', 'y', 'yes']:
                        approved.append({
                            'category': category_name,
                            'suggestion': suggestion
                        })
                        print("✅ Approved")
                    else:
                        print("⏭️  Skipped")
                except (KeyboardInterrupt, EOFError):
                    print("\n⏭️  Skipped remaining")
                    break

        return approved

    def _present_suggestion(self, category: str, idx: int, suggestion: dict):
        """Present individual suggestion with details."""
        print(f"\n[{idx}] {suggestion.get('description', 'Suggestion')}")

        if 'examples' in suggestion:
            print(f"    Examples:")
            for ex in suggestion['examples'][:3]:
                print(f"      • {ex}")

        if 'impact' in suggestion:
            print(f"    Impact: {suggestion['impact']}")

        if 'confidence' in suggestion:
            print(f"    Confidence: {suggestion['confidence']:.0%}")

    def _apply_improvements(self, approved: List[dict]):
        """Apply approved improvements across all components."""
        for item in approved:
            category = item['category']
            suggestion = item['suggestion']

            try:
                if category == "Permissions":
                    self.permission_learner.apply_pattern(suggestion)
                elif category == "MCP":
                    self.mcp_optimizer.apply_optimization(suggestion)
                elif category == "Context":
                    self.context_optimizer.apply_optimization(suggestion)
                elif category == "Workflows":
                    self.workflow_detector.create_workflow(suggestion)
                elif category == "Instructions":
                    self.instruction_tracker.apply_improvement(suggestion)
                elif category == "Cross-Project":
                    self.archetype_detector.transfer_pattern(suggestion)

                logger.info(f"Applied {category} improvement: {suggestion.get('description')}")
            except Exception as e:
                logger.error(f"Failed to apply {category} improvement: {e}")

    def _update_meta_learning(self, report: LearningReport, approved: List[dict]):
        """Update meta-learning based on user feedback."""
        acceptance_rate = len(approved) / report.total_suggestions if report.total_suggestions > 0 else 0

        self.meta_learner.record_session(
            total_suggestions=report.total_suggestions,
            accepted=len(approved),
            acceptance_rate=acceptance_rate
        )

        # Adjust thresholds if needed
        if acceptance_rate < 0.5:
            logger.info("Low acceptance rate - tightening thresholds")
            self.meta_learner.increase_thresholds()
        elif acceptance_rate > 0.9:
            logger.info("High acceptance rate - relaxing thresholds")
            self.meta_learner.decrease_thresholds()

    def _estimate_improvements(
        self,
        permissions: List[dict],
        mcp: List[dict],
        context: List[dict],
        workflows: List[dict],
        instructions: List[dict]
    ) -> str:
        """Estimate impact of all improvements."""
        benefits = []

        if permissions:
            benefits.append(f"{len(permissions)*10}% fewer permission prompts")
        if mcp:
            token_savings = sum(m.get('token_savings', 0) for m in mcp)
            benefits.append(f"{token_savings}K tokens saved on MCP")
        if context:
            token_savings = sum(c.get('tokens', 0) for c in context)
            benefits.append(f"{token_savings}K tokens saved on context")
        if workflows:
            benefits.append(f"{len(workflows)} workflow shortcuts")
        if instructions:
            benefits.append(f"{len(instructions)} policy improvements")

        return ", ".join(benefits) if benefits else "No improvements detected"
```

#### Global Multi-Project MCP Analyzer

```python
# claude_automation/analyzers/global_mcp_analyzer.py

class GlobalMCPAnalyzer:
    """
    Analyzes MCP usage across ALL projects system-wide.

    Addresses limitation of project-scoped analysis by:
    1. Discovering all .claude/mcp.json configs in home directory
    2. Aggregating usage data across all projects
    3. Providing unified view of global vs project-specific servers
    4. Generating system-wide optimization recommendations
    """

    def __init__(self, home_dir: Path, analysis_period_days: int = 30):
        self.home_dir = home_dir
        self.analysis_period_days = analysis_period_days
        self.projects = []
        self.global_servers = {}  # Aggregated server info
        self.global_tool_usage = []  # All usage across projects
        self.global_utilization = {}  # Aggregated utilization
        self.global_recommendations = []

    def discover_projects(self) -> list[Path]:
        """
        Discover all projects with MCP configurations.

        Scans for .claude/mcp.json files system-wide,
        skipping hidden directories except .claude itself.
        """
        projects = []
        for mcp_config in self.home_dir.rglob(".claude/mcp.json"):
            # Skip hidden directories (except .claude)
            if self._is_valid_project(mcp_config):
                project_path = mcp_config.parent.parent
                projects.append(project_path)

        return projects

    def analyze_all_projects(self) -> dict:
        """
        Run MCP analysis for all projects and aggregate.

        Returns unified report with:
        - Total projects scanned
        - Global servers (from ~/.claude.json)
        - Project-specific servers (from each project)
        - Aggregated usage statistics
        - System-wide utilization metrics
        - Prioritized recommendations
        """
        self.projects = self.discover_projects()

        # Analyze each project
        for project_path in self.projects:
            self._analyze_project(project_path)

        # Analyze global config
        self._analyze_global_config()

        return self._build_report()

    def _analyze_project(self, project_path: Path):
        """Analyze single project and merge into global state."""
        analyzer = MCPUsageAnalyzer(project_path)
        config = analyzer.analyze(self.analysis_period_days)

        # Merge servers (global state)
        for server in config.configured_servers:
            if server.name not in self.global_servers:
                self.global_servers[server.name] = server
            else:
                # Update status if connected
                if server.status == MCPServerStatus.CONNECTED:
                    self.global_servers[server.name].status = MCPServerStatus.CONNECTED

        # Aggregate usage
        self.global_tool_usage.extend(config.tool_usage)

        # Aggregate utilization
        for util in config.server_utilization:
            if util.server_name not in self.global_utilization:
                self.global_utilization[util.server_name] = util
            else:
                # Sum across projects
                existing = self.global_utilization[util.server_name]
                existing.total_sessions += util.total_sessions
                existing.loaded_sessions += util.loaded_sessions
                existing.used_sessions += util.used_sessions

        # Aggregate recommendations with project context
        for rec in config.recommendations:
            rec.action = f"[{project_path.name}] {rec.action}"
            self.global_recommendations.append(rec)

    def _build_report(self) -> dict:
        """Build system-wide aggregated report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_projects": len(self.projects),
            "total_servers": len(self.global_servers),
            "connected_servers": sum(
                1 for s in self.global_servers.values()
                if s.status == MCPServerStatus.CONNECTED
            ),
            "servers": list(self.global_servers.values()),
            "usage_aggregated": self._aggregate_usage_by_server(),
            "utilization": list(self.global_utilization.values()),
            "recommendations": self.global_recommendations,
            "projects_scanned": [str(p) for p in self.projects],
        }

    def generate_summary(self, report: dict) -> str:
        """Generate human-readable summary for rebuild output."""
        summary = []
        summary.append("🌐 Global MCP Analysis")
        summary.append(f"  Projects: {report['total_projects']}")
        summary.append(f"  Servers: {report['connected_servers']}/{report['total_servers']} connected")

        # Show global vs project breakdown
        global_servers = [s for s in report['servers'] if 'global' in s.config_location.lower()]
        project_servers = [s for s in report['servers'] if 'project' in s.config_location.lower()]

        summary.append(f"  Global: {len(global_servers)} | Project-specific: {len(project_servers)}")

        # High-priority recommendations
        high_priority = [r for r in report['recommendations'] if r.priority == 1]
        if high_priority:
            summary.append(f"  ⚠️  {len(high_priority)} high-priority action(s)")

        return "\n".join(summary)
```

#### Integration Script

```bash
#!/usr/bin/env bash
# ~/nixos-config/rebuild-nixos (UPDATED)

set -e

echo "🔧 Rebuilding NixOS configuration..."

# 1. Standard NixOS rebuild
sudo nixos-rebuild switch --flake .

# 2. Update home-manager if needed
home-manager switch --flake .

# 3. UNIFIED LEARNING INTEGRATION
if [[ -d ~/claude-nixos-automation ]]; then
    echo ""
    echo "🤖 Updating Claude Code system context..."
    python3 ~/claude-nixos-automation/update-system-claude-v2.py

    echo ""
    echo "🧠 Running adaptive learning cycle..."
    python3 ~/claude-nixos-automation/run-adaptive-learning.py \
        --interactive \
        --all-components  # Run all learners: permissions, MCP, context, workflows, etc.

    echo ""
    echo "✅ Claude Code context and learning complete"
fi

echo "✅ System rebuild complete!"
```

**Note on MCP Global Analysis**: The `run-adaptive-learning.py` script internally uses `GlobalMCPAnalyzer` to scan all projects system-wide, replacing the previous project-scoped approach that only analyzed ~/nixos-config.

#### Entry Point Script

```python
#!/usr/bin/env python3
# run-adaptive-learning.py

"""
Unified entry point for all adaptive learning components.
Coordinates permissions, MCP, context, workflows, instructions, cross-project, and meta-learning.
"""

import argparse
import sys
from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine

def main():
    parser = argparse.ArgumentParser(
        description="Run Claude Code adaptive learning system"
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Present suggestions interactively (default: True)'
    )
    parser.add_argument(
        '--all-components',
        action='store_true',
        help='Run all learning components (permissions, MCP, context, workflows, etc.)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show suggestions without applying'
    )

    args = parser.parse_args()

    # Initialize engine
    engine = AdaptiveSystemEngine(interactive=args.interactive)

    # Run learning cycle
    try:
        report = engine.run_full_learning_cycle()

        if args.dry_run:
            print("\n[DRY RUN] No changes applied")

        if report.total_suggestions == 0:
            print("\n✅ No improvements detected - system is optimized!")
            return 0
        else:
            print(f"\n✅ Processed {report.total_suggestions} suggestions")
            return 0

    except Exception as e:
        print(f"\n❌ Learning cycle failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

---

### Testing Strategy

**Unit Tests**:
- BaseGenerator validation logic
- read_source() behavior
- write_artifact() validation
- Header generation
- Each validation rule

**Integration Tests**:
- Full generation workflow
- Manual content preservation
- Error handling
- Idempotency

**Validation Tests**:
- Permission format checking
- Content validation
- Schema compliance

---

### Risks & Mitigations

**Risk 1: Breaking existing workflows**
- *Mitigation*: Backward compatibility guaranteed, migration script provided

**Risk 2: Performance degradation**
- *Mitigation*: Validation is lightweight, budget enforced

**Risk 3: False positives in validation**
- *Mitigation*: Tiered validation - critical rules fail immediately, style rules warn initially allowing feedback-based refinement

**Risk 4: User confusion about new headers**
- *Mitigation*: Clear documentation, helpful error messages

---

### Success Metrics

**Quantitative - Core Architecture**:
- ✅ 100% of generators declare sources/artifacts
- ✅ 0 source files overwritten (prevented)
- ✅ 100% of artifacts have headers
- ✅ <1s validation overhead
- ✅ 90%+ test coverage

**Quantitative - Tier 1 Self-Improvement (Permissions, MCP, Context)**:
- ✅ Permission approvals logged 100% of time
- ✅ Patterns detected with ≥3 occurrences in 30 days
- ✅ Pattern suggestions presented during every `./rebuild-nixos`
- ⬆️ 50%+ reduction in permission prompts after 30 days
- ✅ MCP server usage tracked per session
- ⬆️ 20%+ token savings from MCP optimization after 30 days
- ✅ CLAUDE.md section access logged per session
- ⬆️ 30%+ improvement in effective context ratio after 30 days
- ⬆️ 15%+ reduction in total CLAUDE.md token overhead

**Quantitative - Tier 2 Self-Improvement (Workflows, Instructions)**:
- ✅ Slash command sequences logged 100% of time
- ✅ Workflow patterns detected with ≥3 occurrences
- ⬆️ 3+ workflow shortcuts created from observed patterns
- ✅ Instruction effectiveness tracked per policy
- ⬆️ 20%+ improvement in policy compliance scores after 30 days
- ⬆️ 5+ low-effectiveness policies identified and improved

**Quantitative - Tier 3 Self-Improvement (Cross-Project, Meta-Learning)**:
- ✅ Project archetypes detected automatically
- ⬆️ 2+ cross-project pattern transfers per new project
- ✅ Learning system effectiveness metrics tracked
- ⬆️ Suggestion acceptance rate maintained >70%
- ✅ Meta-learning thresholds self-adjust based on feedback
- ⬆️ False positive rate reduced by 30% through self-calibration

**Qualitative - Core Experience**:
- ✅ Users understand which files to edit
- ✅ Clear error messages when violations occur
- ✅ No manual content lost during regeneration

**Qualitative - Self-Improvement Experience**:
- ✅ System "learns" user's workflow preferences automatically
- ✅ Each rebuild makes Claude Code progressively smarter
- ✅ Permission management becomes invisible over time
- ✅ MCP servers optimize themselves based on actual usage
- ✅ CLAUDE.md stays relevant and lean
- ✅ Workflows emerge naturally from repeated patterns
- ✅ Instructions self-improve based on adherence data
- ✅ Knowledge transfers seamlessly between projects
- ✅ Learning system self-calibrates to user preferences
- ✅ "Invisible intelligence" - system improves without user effort

---

### Next Steps (After Specification)

1. **`/speckit.clarify`** - Q&A to resolve ambiguities
2. **`/speckit.plan`** - Detailed implementation plan
3. **User approval** - Review and approve plan
4. **`/speckit.implement`** - Execute implementation

---

## Open Questions (For Clarification Phase)

1. ~~Should git hook block commits or just warn?~~ ✅ RESOLVED: Interactive prompt
2. ~~What should happen if user manually deletes generation header?~~ ✅ RESOLVED: Regenerate restores header
3. ~~Should validation be strict (fail) or lenient (warn) initially?~~ ✅ RESOLVED: Tiered strictness
4. ~~How to handle migration of existing deployments?~~ ✅ RESOLVED: Migration script + automatic on next generation
5. ~~Should headers be visible in rendered markdown or hidden?~~ ✅ RESOLVED: Hidden (HTML comments)

---

*This specification follows Constitution Principle 1 (Source/Artifact Separation).*
*Approval required before proceeding to `/speckit.clarify`.*
