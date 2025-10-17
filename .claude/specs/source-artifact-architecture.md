---
status: draft
created: 2025-10-10
updated: 2025-10-10
type: planning
lifecycle: ephemeral
speckit_phase: specify
---

# Specification: Explicit Source/Artifact Architecture

**Spec ID**: SAA-001
**Priority**: High
**Estimated Effort**: 10 hours
**Dependencies**: None (foundational)

---

## `/speckit.specify` - Capture Requirements

### Problem Statement

**Current State**:
- CLAUDE.md files are auto-generated but include manually-maintained content
- The separation between "sources" (editable) and "artifacts" (generated) is **implicit**
- Risk of accidental data loss if generators overwrite manual content
- No validation prevents writing to source files
- Users can't easily tell which files are editable vs generated

**Pain Points**:
1. **Fragile architecture** - Manual/auto split works but only by convention
2. **No enforcement** - Nothing prevents generator from overwriting sources
3. **User confusion** - Which files should I edit? CLAUDE.md or CLAUDE-USER-POLICIES.md?
4. **Artifact pollution** - Line 19 of settings.local.json contains entire commit message
5. **No validation** - Invalid permissions (multi-line strings, heredocs) not caught

**Impact**:
- Users might edit CLAUDE.md directly, changes get overwritten
- Generators could accidentally corrupt source files
- No feedback when violations occur
- Permission system has garbage data

---

### Proposed Solution

**Implement explicit source/artifact separation architecture following Constitution Principle 1.**

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

4. **Validation Pipeline**
   - Permission validation (no multi-line, no heredocs, length limits)
   - Content validation (no temporal markers, proper sections)
   - Schema validation (Pydantic models)

5. **User Guidance**
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
- Header MUST use HTML comments for markdown files

**FR-3: Explicit Contracts**
- Each generator MUST declare MANUAL_SOURCES list
- Each generator MUST declare GENERATED_ARTIFACTS list
- System MUST validate no overlap at initialization

**FR-4: Permission Validation**
- Permission strings MUST NOT contain newlines
- Permission strings MUST NOT contain heredoc markers (<<, EOF)
- Permission strings MUST be ≤200 characters
- Invalid permissions MUST be rejected with clear error

**FR-5: Content Validation**
- Generated docs MUST NOT contain temporal markers (NEW, Week 1, Phase 2)
- Generated docs MUST have proper section markers
- Templates MUST render without errors

**FR-6: User Guidance**
- Git hook MUST warn when committing CLAUDE.md
- Warning MUST suggest correct source file
- Error messages MUST be actionable

#### Non-Functional Requirements

**NFR-1: Performance**
- Validation overhead MUST be <1 second per generator
- Full rebuild MUST complete in <10 seconds

**NFR-2: Backward Compatibility**
- Existing source files (CLAUDE-USER-POLICIES.md) MUST continue working
- Existing templates MUST work with new headers
- Migration path MUST be documented

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

**AC-4: Git Hook Warns**
```bash
# Test case
echo "test" >> CLAUDE.md
git add CLAUDE.md
git commit -m "test"

# Expected output:
# ⚠️  WARNING: Committing CLAUDE.md (artifact)
# Did you mean to edit:
#   ✏️  ~/.claude/CLAUDE-USER-POLICIES.md
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
- If changes are needed, provide automated migration
- Document changes clearly
- Provide before/after examples

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
        """Write generated artifact with validation."""
        # 1. Validate not a source
        if path.name in self.MANUAL_SOURCES:
            raise ValueError(f"Cannot overwrite source: {path}")

        # 2. Validate is a declared artifact
        if path.name not in self.GENERATED_ARTIFACTS:
            raise ValueError(f"Undeclared artifact: {path}")

        # 3. Add generation header
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
- *Mitigation*: Start lenient, tighten based on feedback

**Risk 4: User confusion about new headers**
- *Mitigation*: Clear documentation, helpful error messages

---

### Success Metrics

**Quantitative**:
- ✅ 100% of generators declare sources/artifacts
- ✅ 0 source files overwritten (prevented)
- ✅ 100% of artifacts have headers
- ✅ <1s validation overhead
- ✅ 90%+ test coverage

**Qualitative**:
- ✅ Users understand which files to edit
- ✅ Clear error messages when violations occur
- ✅ No manual content lost during regeneration

---

### Next Steps (After Specification)

1. **`/speckit.clarify`** - Q&A to resolve ambiguities
2. **`/speckit.plan`** - Detailed implementation plan
3. **User approval** - Review and approve plan
4. **`/speckit.implement`** - Execute implementation

---

## Open Questions (For Clarification Phase)

1. Should git hook block commits or just warn?
2. What should happen if user manually deletes generation header?
3. Should validation be strict (fail) or lenient (warn) initially?
4. How to handle migration of existing deployments?
5. Should headers be visible in rendered markdown or hidden?

---

*This specification follows Constitution Principle 1 (Source/Artifact Separation).*
*Approval required before proceeding to `/speckit.clarify`.*
