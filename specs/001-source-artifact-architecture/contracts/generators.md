---
status: active
created: 2025-10-17
updated: 2025-10-17
type: reference
lifecycle: persistent
---

# Generator Contracts

Interface contracts for all generators using the Source-Artifact Architecture.

**Purpose**: Define the contract that all generators MUST follow to maintain source-artifact separation and prevent accidental edits to user-managed files.

---

## BaseGenerator Contract

**Module**: `claude_automation/generators/base_generator.py`

All generators MUST inherit from `BaseGenerator` and follow this contract:

```python
class BaseGenerator(ABC):
    """Base class for all generators.

    Enforces source-artifact architecture:
    - Manual sources: User-editable files (MUST NOT be written by generator)
    - Generated artifacts: Auto-generated files (CAN write, MUST have header)
    """

    # REQUIRED: Subclasses MUST declare these
    MANUAL_SOURCES: list[Path] = []
    GENERATED_ARTIFACTS: list[Path] = []

    def __init__(self):
        """Initialize generator and validate declarations."""
        self._validate_declarations()

    @abstractmethod
    def generate(self) -> GenerationResult:
        """Generate artifacts from sources.

        Returns:
            GenerationResult with success status, warnings, errors

        MUST:
        - Read from MANUAL_SOURCES using read_source()
        - Write to GENERATED_ARTIFACTS using write_artifact()
        - NEVER write to MANUAL_SOURCES
        """
        ...

    # Protected API for subclasses

    def read_source(self, path: Path) -> str:
        """Read a source file.

        Warns if path not in MANUAL_SOURCES (but doesn't fail).

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        ...

    def write_artifact(
        self,
        path: Path,
        content: str,
        sources_used: list[Path]
    ) -> None:
        """Write an artifact file with auto-generated header.

        Args:
            path: File to write (must be in GENERATED_ARTIFACTS)
            content: Content to write
            sources_used: Source files used to generate this artifact

        Side effects:
            - Writes file with HTML comment header
            - Creates parent directories if needed

        Raises:
            ValueError: If path is in MANUAL_SOURCES
            ValueError: If path not in GENERATED_ARTIFACTS (warning mode)
        """
        ...

    # Private implementation

    def _validate_declarations(self) -> None:
        """Validate MANUAL_SOURCES and GENERATED_ARTIFACTS don't overlap."""
        ...

    def _generate_header(
        self,
        sources_used: list[Path]
    ) -> str:
        """Generate HTML comment header for artifact.

        Format:
        <!--
        ============================================================
          AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY

          Generated: {timestamp}
          Generator: {class_name}
          Sources: {source_files}

          To modify, edit source files and regenerate.
        ============================================================
        -->
        """
        ...
```

---

## Generator Implementations

### 1. SystemGenerator

**Purpose**: Generate system-level CLAUDE.md from system configuration.

**Module**: `claude_automation/generators/system_generator.py`

**Contract**:

```python
class SystemGenerator(BaseGenerator):
    """Generates ~/.claude/CLAUDE.md from system configuration."""

    # Source-artifact declaration
    MANUAL_SOURCES = [
        Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md",
        Path.home() / ".config" / "fish" / "config.fish",
        Path.home() / ".config" / "fish" / "conf.d" / "abbreviations.fish",
        # ... other system files
    ]

    GENERATED_ARTIFACTS = [
        Path.home() / ".claude" / "CLAUDE.md"
    ]

    def __init__(
        self,
        config: SystemConfig,
        scrapers: Optional[list[BaseScraper]] = None
    ):
        """Initialize with system config and scrapers."""
        super().__init__()
        self.config = config
        self.scrapers = scrapers or self._default_scrapers()

    def generate(self) -> GenerationResult:
        """Generate ~/.claude/CLAUDE.md.

        Steps:
        1. Run scrapers to collect system data
        2. Read user policies (if exists)
        3. Render template with all data
        4. Write artifact with header

        Returns:
            GenerationResult
        """
        ...
```

**Template**: `claude_automation/templates/system-claude.j2`

**Output**: `~/.claude/CLAUDE.md` (HTML header + Markdown content)

---

### 2. PermissionsGenerator

**Purpose**: Generate `settings.local.json` from base settings and learned patterns.

**Module**: `claude_automation/generators/permissions_generator.py`

**Contract**:

```python
class PermissionsGenerator(BaseGenerator):
    """Generates settings.local.json with auto-approval permissions."""

    # Source-artifact declaration
    MANUAL_SOURCES = [
        Path(".claude") / "settings.base.json"  # User-editable base settings
    ]

    GENERATED_ARTIFACTS = [
        Path(".claude") / "settings.local.json"  # Auto-generated
    ]

    def __init__(self, config: PermissionsConfig):
        """Initialize with permissions config."""
        super().__init__()
        self.config = config

    def generate(self) -> GenerationResult:
        """Generate settings.local.json.

        Steps:
        1. Read base settings (if exists)
        2. Merge with config.patterns
        3. Validate all permissions
        4. Write artifact

        Returns:
            GenerationResult
        """
        ...

    def add_patterns(self, patterns: list[str]) -> None:
        """Add permission patterns to config."""
        self.config.patterns.extend(patterns)
```

**Validation**: Uses `PermissionValidator` to check all permissions

**Output**: `.claude/settings.local.json` (JSON with header comment)

---

### 3. IntelligentPermissionsGenerator

**Purpose**: Generate permissions with learning from approval history.

**Module**: `claude_automation/generators/intelligent_permissions_generator.py`

**Contract**:

```python
class IntelligentPermissionsGenerator(PermissionsGenerator):
    """Permissions generator with learning from approval history."""

    def __init__(
        self,
        config: PermissionsConfig,
        pattern_detector: PermissionPatternDetector
    ):
        """Initialize with config and pattern detector."""
        super().__init__(config)
        self.pattern_detector = pattern_detector

    def generate_with_learning(
        self,
        interactive: bool = True
    ) -> GenerationResult:
        """Generate permissions with learned patterns.

        Steps:
        1. Detect patterns from approval history
        2. If interactive: prompt user for approval
        3. Apply approved patterns
        4. Generate settings.local.json

        Args:
            interactive: Whether to prompt user for approval

        Returns:
            GenerationResult with applied patterns
        """
        ...

    def _prompt_for_pattern(
        self,
        suggestion: PatternSuggestion
    ) -> bool:
        """Prompt user to approve a pattern suggestion.

        Returns:
            True if user approved, False otherwise
        """
        ...

    def _apply_patterns(
        self,
        patterns: list[PermissionPattern]
    ) -> None:
        """Add patterns to config and regenerate."""
        ...
```

**Integration**: Called by `AdaptiveSystemEngine` during learning cycle

---

### 4. ProjectGenerator (Future)

**Purpose**: Generate project-level CLAUDE.md from project configuration.

**Contract**:

```python
class ProjectGenerator(BaseGenerator):
    """Generates project-level CLAUDE.md."""

    MANUAL_SOURCES = [
        Path("CLAUDE-PROJECT-POLICIES.md"),  # User-editable project policies
        Path(".claude") / "config.yaml"       # User-editable project config
    ]

    GENERATED_ARTIFACTS = [
        Path("CLAUDE.md")  # Auto-generated
    ]

    def __init__(self, config: ProjectConfig):
        """Initialize with project config."""
        super().__init__()
        self.config = config

    def generate(self) -> GenerationResult:
        """Generate project CLAUDE.md."""
        ...
```

---

## Generator Testing Contract

All generators MUST have these tests:

### 1. Source Protection Test

```python
def test_cannot_write_to_source():
    """Verify generator cannot write to MANUAL_SOURCES."""
    generator = SystemGenerator(config)

    source_file = generator.MANUAL_SOURCES[0]

    with pytest.raises(ValueError, match="Cannot write to manual source"):
        generator.write_artifact(source_file, "content", [])
```

### 2. Artifact Header Test

```python
def test_artifact_has_header():
    """Verify generated artifacts have AUTO-GENERATED header."""
    generator = SystemGenerator(config)
    result = generator.generate()

    assert result.success
    artifact_path = generator.GENERATED_ARTIFACTS[0]
    content = artifact_path.read_text()

    assert "AUTO-GENERATED" in content
    assert "DO NOT EDIT DIRECTLY" in content
    assert generator.__class__.__name__ in content  # Generator name
```

### 3. Declaration Validation Test

```python
def test_declarations_dont_overlap():
    """Verify MANUAL_SOURCES and GENERATED_ARTIFACTS don't overlap."""
    generator = SystemGenerator(config)

    sources = set(generator.MANUAL_SOURCES)
    artifacts = set(generator.GENERATED_ARTIFACTS)

    overlap = sources & artifacts
    assert len(overlap) == 0, f"Overlap found: {overlap}"
```

### 4. Idempotency Test

```python
def test_generation_is_idempotent():
    """Verify generating twice produces identical output."""
    generator = SystemGenerator(config)

    result1 = generator.generate()
    content1 = generator.GENERATED_ARTIFACTS[0].read_text()

    result2 = generator.generate()
    content2 = generator.GENERATED_ARTIFACTS[0].read_text()

    # Ignore timestamp differences
    content1_normalized = re.sub(r'Generated: .*', 'Generated: <TIMESTAMP>', content1)
    content2_normalized = re.sub(r'Generated: .*', 'Generated: <TIMESTAMP>', content2)

    assert content1_normalized == content2_normalized
```

---

## Migration from Legacy Generators

Existing generators MUST be updated to follow this contract:

**Before** (legacy):
```python
class SystemGenerator:
    def generate(self):
        config = self.scrape_system()
        content = self.render_template(config)
        Path("~/.claude/CLAUDE.md").write_text(content)  # Direct write
```

**After** (contract-compliant):
```python
class SystemGenerator(BaseGenerator):
    MANUAL_SOURCES = [
        Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
    ]
    GENERATED_ARTIFACTS = [
        Path.home() / ".claude" / "CLAUDE.md"
    ]

    def generate(self) -> GenerationResult:
        config = self.scrape_system()
        user_policies = self.read_source(self.MANUAL_SOURCES[0])  # Safe read
        content = self.render_template(config, user_policies)
        self.write_artifact(                                        # Safe write with header
            self.GENERATED_ARTIFACTS[0],
            content,
            sources_used=self.MANUAL_SOURCES
        )
        return GenerationResult(success=True)
```

---

## Best Practices

1. **Always declare sources and artifacts** in class attributes
2. **Use read_source() and write_artifact()** instead of direct file I/O
3. **List all sources** used in `sources_used` parameter for traceability
4. **Validate inputs** before generating (use validators)
5. **Return detailed GenerationResult** with warnings and errors
6. **Make generation idempotent** (same inputs → same outputs, ignoring timestamps)
7. **Test source protection** to prevent accidental source file modification

---

## Pre-commit Hook Integration

The pre-commit hook detects `AUTO-GENERATED` markers and warns users:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: artifact-check
        name: Artifact Protection
        entry: bash -c 'check for AUTO-GENERATED markers'
        language: system
```

If user attempts to commit an artifact:
1. Hook detects `AUTO-GENERATED` marker
2. Warns user: "This file is auto-generated"
3. Prompts: "Continue anyway? (y/N)"
4. If user says no: abort commit
5. If user says yes: allow commit (with warning)

---

*Last updated: 2025-10-17 (Phase 2 completion)*
