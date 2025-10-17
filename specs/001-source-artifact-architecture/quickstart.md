---
status: active
created: 2025-10-17
updated: 2025-10-17
type: guide
lifecycle: persistent
---

# Quickstart Guide

Get started with the Self-Improving Claude Code System in 5 minutes.

**Audience**: Both end-users (using the system) and developers (extending the system).

---

## Table of Contents

1. [For End Users](#for-end-users)
2. [For Developers](#for-developers)
3. [Common Tasks](#common-tasks)
4. [Troubleshooting](#troubleshooting)

---

## For End Users

### Prerequisites

- NixOS system with flakes enabled
- Claude Code CLI installed
- `~/nixos-config` repository (or similar)

### Initial Setup

**1. Clone the repository:**

```bash
cd ~
git clone https://github.com/yourusername/claude-nixos-automation.git
cd claude-nixos-automation
```

**2. Activate development environment:**

```bash
devenv shell
```

*Expected output*: Shell activates in <1s with Python 3.13, pytest, ruff, mypy.

**3. Verify installation:**

```bash
# Check Python version
python --version  # Should be 3.13.x

# Check devenv scripts
devenv info  # Should show scripts: test, lint, format, quality

# Run tests
devenv test  # Should pass all tests
```

**4. Run initial system generation:**

```bash
python scripts/generate-system-claude.py
```

*Expected output*: `~/.claude/CLAUDE.md` created with AUTO-GENERATED header.

**5. Verify generated file:**

```bash
head -20 ~/.claude/CLAUDE.md
```

*Expected output*: HTML comment header with "AUTO-GENERATED" marker.

---

### Daily Usage

#### Scenario 1: Regenerate CLAUDE.md after system changes

```bash
cd ~/claude-nixos-automation
devenv shell

# Regenerate system CLAUDE.md
python scripts/generate-system-claude.py

# Check for warnings/errors
echo $?  # Should be 0 for success
```

#### Scenario 2: Run adaptive learning cycle

```bash
cd ~/claude-nixos-automation
devenv shell

# Run full learning cycle (interactive)
python scripts/run-adaptive-learning.py --interactive
```

*Expected output*:
- Permission pattern suggestions
- MCP server optimization recommendations
- Context optimization suggestions
- Interactive prompts for approval

#### Scenario 3: Check system health

```bash
python scripts/run-adaptive-learning.py --health
```

*Expected output*: Health report showing:
- Overall system health (healthy/needs-tuning/malfunctioning)
- Per-component metrics (acceptance rates, suggestion counts)
- Threshold adjustment suggestions

#### Scenario 4: Run specific learning component

```bash
# Only analyze permissions
python scripts/run-adaptive-learning.py --components permission_learning

# Only optimize MCP servers
python scripts/run-adaptive-learning.py --components mcp_optimization

# Multiple components
python scripts/run-adaptive-learning.py --components permission_learning mcp_optimization
```

---

### Integration with NixOS Rebuild

**Option 1: Manual trigger after rebuild**

```bash
cd ~/nixos-config
./rebuild-nixos

# After successful rebuild
cd ~/claude-nixos-automation
python scripts/run-adaptive-learning.py --interactive
```

**Option 2: Automatic trigger (recommended)**

Add to `~/nixos-config/rebuild-nixos`:

```bash
# At end of rebuild script
if [ $? -eq 0 ]; then  # If rebuild succeeded
    echo ""
    echo "Running adaptive learning cycle..."
    if [ -f ~/claude-nixos-automation/scripts/run-adaptive-learning.py ]; then
        python3 ~/claude-nixos-automation/scripts/run-adaptive-learning.py --interactive
    fi
fi
```

---

## For Developers

### Development Environment Setup

**1. Clone and activate:**

```bash
git clone https://github.com/yourusername/claude-nixos-automation.git
cd claude-nixos-automation
devenv shell
```

**2. Install pre-commit hooks:**

```bash
devenv shell -c "pre-commit install"
```

*What this does*:
- Installs git pre-commit hooks
- Hooks run on `git commit`:
  - Ruff linting
  - Mypy type checking
  - Artifact protection (warns if committing auto-generated files)

**3. Verify development tools:**

```bash
# Type checking
mypy claude_automation/

# Linting
ruff check claude_automation/

# Format checking
ruff format --check claude_automation/

# Run all quality checks
devenv quality
```

---

### Running Tests

**Full test suite:**

```bash
devenv test
```

*Expected output*: All tests pass in <30s.

**Fast unit tests only:**

```bash
devenv test-fast
```

*Expected output*: Unit tests pass in <5s.

**With coverage:**

```bash
pytest --cov=claude_automation --cov-report=html
```

*Expected output*: Coverage report in `htmlcov/index.html`.

**TDD workflow:**

```bash
# 1. Write failing test
echo "def test_new_feature(): assert False" >> tests/unit/test_new_feature.py

# 2. Run test (should fail)
pytest tests/unit/test_new_feature.py -xvs

# 3. Implement feature
# ... edit code ...

# 4. Run test (should pass)
pytest tests/unit/test_new_feature.py -xvs

# 5. Run full suite
devenv test
```

---

### Creating a New Analyzer

**Step 1: Define data models**

Add to `claude_automation/schemas.py`:

```python
class MyAnalyzerEntry(BaseModel):
    """Entry for my analyzer log."""
    timestamp: datetime
    data: str
    # ... other fields

class MyAnalyzerSuggestion(BaseModel):
    """Suggestion from my analyzer."""
    suggestion_type: str
    reason: str
    confidence: float
```

**Step 2: Create analyzer module**

Create `claude_automation/analyzers/my_analyzer.py`:

```python
from claude_automation.schemas import MyAnalyzerSuggestion, AdaptiveSystemConfig

class MyAnalyzer:
    """Analyzer for X feature."""

    def __init__(self, config: AdaptiveSystemConfig):
        self.config = config

    def analyze(self) -> list[MyAnalyzerSuggestion]:
        """Run analysis and return suggestions."""
        # Implementation
        return []

    def get_health_metrics(self) -> dict:
        """Return health metrics."""
        return {
            'healthy': True,
            'last_run': datetime.now(),
            'total_suggestions': 0
        }
```

**Step 3: Write tests (TDD)**

Create `tests/unit/test_my_analyzer.py`:

```python
import pytest
from claude_automation.analyzers.my_analyzer import MyAnalyzer
from claude_automation.schemas import AdaptiveSystemConfig

def test_analyzer_interface():
    """Verify analyzer implements required interface."""
    config = AdaptiveSystemConfig()
    analyzer = MyAnalyzer(config)

    # Has analyze method
    assert hasattr(analyzer, 'analyze')
    result = analyzer.analyze()
    assert isinstance(result, list)

    # Has get_health_metrics method
    assert hasattr(analyzer, 'get_health_metrics')
    metrics = analyzer.get_health_metrics()
    assert isinstance(metrics, dict)
    assert 'healthy' in metrics
```

**Step 4: Integrate with engine**

Edit `claude_automation/core/adaptive_system_engine.py`:

```python
from claude_automation.analyzers.my_analyzer import MyAnalyzer

class AdaptiveSystemEngine:
    def __init__(self, config):
        # ... existing analyzers ...
        self.my_analyzer = MyAnalyzer(config)

    def _analyze_my_component(self):
        """Run my analyzer."""
        return self.my_analyzer.analyze()

    def _build_report(self, components):
        # ... existing code ...
        if self._should_run("my_component", components):
            report.my_suggestions = self._analyze_my_component()
```

**Step 5: Add CLI option**

Edit `scripts/run-adaptive-learning.py`:

```python
parser.add_argument(
    "--components",
    choices=[
        # ... existing choices ...
        "my_component"
    ]
)
```

**Step 6: Test end-to-end**

```bash
# Test analyzer standalone
pytest tests/unit/test_my_analyzer.py -xvs

# Test integration
python scripts/run-adaptive-learning.py --components my_component --no-interactive

# Test with engine
pytest tests/integration/test_learning_cycle.py -xvs
```

---

### Creating a New Generator

**Step 1: Define source-artifact declaration**

Create `claude_automation/generators/my_generator.py`:

```python
from claude_automation.generators.base_generator import BaseGenerator
from pathlib import Path

class MyGenerator(BaseGenerator):
    """Generates my-artifact.md from my-source.yaml."""

    MANUAL_SOURCES = [
        Path.home() / ".claude" / "my-source.yaml"
    ]

    GENERATED_ARTIFACTS = [
        Path.home() / ".claude" / "my-artifact.md"
    ]

    def generate(self) -> GenerationResult:
        """Generate artifact from source."""
        # Read source
        source_content = self.read_source(self.MANUAL_SOURCES[0])

        # Process
        output = self._process(source_content)

        # Write artifact with header
        self.write_artifact(
            self.GENERATED_ARTIFACTS[0],
            output,
            sources_used=self.MANUAL_SOURCES
        )

        return GenerationResult(success=True)
```

**Step 2: Write source protection test**

Create `tests/unit/test_my_generator.py`:

```python
import pytest
from claude_automation.generators.my_generator import MyGenerator

def test_cannot_write_to_source():
    """Verify cannot write to manual source."""
    generator = MyGenerator()

    with pytest.raises(ValueError, match="Cannot write to manual source"):
        generator.write_artifact(
            generator.MANUAL_SOURCES[0],
            "content",
            []
        )

def test_artifact_has_header():
    """Verify artifact has AUTO-GENERATED header."""
    generator = MyGenerator()
    result = generator.generate()

    assert result.success
    content = generator.GENERATED_ARTIFACTS[0].read_text()
    assert "AUTO-GENERATED" in content
```

**Step 3: Test and deploy**

```bash
# Run tests
pytest tests/unit/test_my_generator.py -xvs

# Test generation
python -c "from claude_automation.generators.my_generator import MyGenerator; MyGenerator().generate()"

# Verify artifact
cat ~/.claude/my-artifact.md | head -20
```

---

## Common Tasks

### Migrate Existing CLAUDE.md Files to Include Headers

```bash
# Dry-run mode (see what would change)
./scripts/migrate-add-headers.sh --dry-run

# Apply migration
./scripts/migrate-add-headers.sh
```

*Expected output*:
- Backups created in `.backups/` directory
- Headers added to CLAUDE.md files
- Summary: "Processed: 2, Skipped: 0, Failed: 0"

### Update Permission Patterns

```bash
# Interactive mode (prompts for approval)
python scripts/update-permissions-with-learning.py --interactive

# Dry-run mode (show suggestions without applying)
python scripts/update-permissions-with-learning.py --dry-run

# Apply specific patterns
python scripts/update-permissions-with-learning.py --pattern git_read_only
```

### Analyze MCP Usage Across All Projects

```bash
# Run global MCP analysis
python scripts/analyze-all-projects-mcp.py

# View report
cat ~/.claude/mcp-global-report.json | jq .
```

*Expected output*:
- Total servers discovered
- Utilization metrics per server
- Optimization recommendations

### Check Data Model Documentation

```bash
# View all schemas
cat specs/001-source-artifact-architecture/data-model.md | glow

# Count schemas
grep "^### " specs/001-source-artifact-architecture/data-model.md | wc -l
```

---

## Troubleshooting

### Issue: `devenv shell` takes too long (>5s)

**Diagnosis**:
```bash
time devenv shell -c "python --version"
```

**Fix**:
- Check network connectivity (Nix fetches from cache)
- Run `nix-collect-garbage` to clean old generations
- Verify cachix is configured

### Issue: Tests failing with import errors

**Diagnosis**:
```bash
python -c "import claude_automation; print(claude_automation.__file__)"
```

**Fix**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/home/guyfawkes/claude-nixos-automation:$PYTHONPATH

# Or run through devenv
devenv shell -c "pytest"
```

### Issue: Pre-commit hook blocking commit

**Diagnosis**:
```bash
# Check which hook is failing
git commit -m "test" --no-verify
```

**Fix**:
```bash
# Fix linting issues
ruff check --fix claude_automation/

# Fix formatting issues
ruff format claude_automation/

# Fix type errors
mypy claude_automation/

# Or commit with --no-verify (not recommended)
git commit -m "test" --no-verify
```

### Issue: Learning cycle returning empty suggestions

**Diagnosis**:
```bash
# Check approval history
cat ~/.claude/approval-history.jsonl | wc -l

# Check if configured correctly
python -c "from claude_automation.schemas import AdaptiveSystemConfig; print(AdaptiveSystemConfig())"
```

**Fix**:
- Ensure approval history exists (requires using Claude Code and approving permissions)
- Check config: `~/.claude/config.yaml`
- Lower `confidence_threshold` in config

### Issue: Generator failed with "Cannot write to manual source"

**Diagnosis**:
```bash
# Check generator declarations
python -c "from claude_automation.generators.system_generator import SystemGenerator; print(SystemGenerator.MANUAL_SOURCES)"
```

**Fix**:
- This is expected behavior (protection working!)
- Edit the correct file: modify source, not artifact
- If you need to write to that file, add it to `GENERATED_ARTIFACTS` instead

---

## Next Steps

**For end users:**
- Read `specs/001-source-artifact-architecture/spec.md` for architecture overview
- Explore `data-model.md` to understand data structures
- Check `CLAUDE.md` files to see generated documentation

**For developers:**
- Read `contracts/analyzers.md` for analyzer interface details
- Read `contracts/generators.md` for generator interface details
- Read `contracts/engine.md` for orchestration details
- Explore `tests/` directory for testing patterns
- Check `CONSTITUTION.md` for project principles

---

## Help & Support

**Documentation**:
- Architecture: `specs/001-source-artifact-architecture/spec.md`
- Planning: `specs/001-source-artifact-architecture/plan.md`
- Tasks: `specs/001-source-artifact-architecture/tasks.md`
- Contracts: `specs/001-source-artifact-architecture/contracts/`

**Community**:
- GitHub Issues: https://github.com/yourusername/claude-nixos-automation/issues
- Discussions: https://github.com/yourusername/claude-nixos-automation/discussions

**Development**:
- Run tests: `devenv test`
- Run quality checks: `devenv quality`
- View coverage: `pytest --cov=claude_automation --cov-report=html`

---

*Last updated: 2025-10-17 (Phase 2 completion)*
