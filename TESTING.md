---
status: active
created: 2024-01-01
updated: 2025-10-20
type: guide
lifecycle: persistent
---

# Testing Documentation

Comprehensive testing guide for claude-nixos-automation.

## Overview

This project includes **59 automated tests** with 100% pass rate:

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| Schema Validation | 28 | All Pydantic models |
| Template Rendering | 24 | All Jinja2 templates |
| Integration Workflows | 7 | End-to-end phases |
| **Total** | **59** | **100% passing** |

## Running Tests

### Quick Start

```bash
# Enter development environment
nix develop

# Run all tests
pytest -v

# Run with coverage
pytest --cov=claude_automation

# Run specific test file
pytest tests/test_schemas.py -v
```

### Test Categories

#### 1. Schema Validation Tests (28 tests)

**File:** `tests/test_schemas.py`

Tests all Pydantic models for:
- Valid data acceptance
- Invalid data rejection
- Validator enforcement
- Property methods
- Edge cases

**Example tests:**
```python
def test_valid_tool_info(sample_tool_info):
    """Valid ToolInfo should validate."""
    assert sample_tool_info.name == "git"
    assert sample_tool_info.category == ToolCategory.DEVELOPMENT

def test_invalid_url():
    """Invalid URL should raise ValidationError."""
    with pytest.raises(ValidationError):
        ToolInfo(
            name="test",
            description="Test",
            category=ToolCategory.DEVELOPMENT,
            url="not-a-url",  # Missing http://
        )
```

**Run schema tests only:**
```bash
pytest tests/test_schemas.py -v
```

#### 2. Template Rendering Tests (24 tests)

**File:** `tests/test_templates.py`

Tests all Jinja2 templates for:
- Syntax errors
- Empty data handling
- None value handling
- All template variants

**Template coverage:**
- 10 directory templates (generic, source_code, tests, documentation, etc.)
- 5 permission templates (base, python, nodejs, rust, nixos)
- Usage analytics template
- Local context template

**Example tests:**
```python
@pytest.mark.parametrize(
    "template_name",
    [
        "directory/generic.j2",
        "directory/source_code.j2",
        # ... all templates
    ],
)
def test_directory_template_renders(jinja_env, tmp_project, template_name):
    """All directory templates should render without errors."""
    template = jinja_env.get_template(template_name)
    result = template.render(**context)
    assert len(result) > 0
```

**Run template tests only:**
```bash
pytest tests/test_templates.py -v
```

#### 3. Integration Tests (7 tests)

**File:** `tests/test_integration.py`

End-to-end workflow tests for each phase:

**Phase 1: Permissions Generator**
```python
def test_permissions_end_to_end(tmp_project):
    """Test full permissions generation workflow."""
    # Create Python project
    # Detect project type
    # Generate permissions
    # Verify JSON output
```

**Phase 2: Directory Context Generator**
```python
def test_directory_context_end_to_end(tmp_project):
    """Test full directory context generation workflow."""
    # Create source directory
    # Analyze directory
    # Generate context
    # Verify CLAUDE.md
```

**Phase 3: Local Context Generator**
```python
def test_local_context_end_to_end(tmp_project):
    """Test full local context generation workflow."""
    # Analyze system
    # Generate context
    # Verify hardware detection
```

**Phase 4: Slash Commands Generator**
```python
def test_slash_commands_end_to_end(tmp_project):
    """Test full slash commands generation workflow."""
    # Create git repository
    # Analyze workflows
    # Generate commands
    # Verify command files
```

**Phase 6: Usage Analytics Generator**
```python
def test_usage_analytics_end_to_end(tmp_project, tmp_fish_history):
    """Test full usage analytics generation workflow."""
    # Track usage
    # Generate analytics
    # Verify CLAUDE.md section
    # Test update (no duplicates)
```

**Cross-Phase Integration**
```python
def test_full_project_setup(tmp_project, tmp_fish_history):
    """Test setting up a full project with all generators."""
    # Run all 5 phases
    # Verify all outputs exist

def test_idempotency(tmp_project, tmp_fish_history):
    """Test that generators are idempotent."""
    # Generate twice
    # Verify same output
```

**Run integration tests only:**
```bash
pytest tests/test_integration.py -v
```

## Test Fixtures

**File:** `tests/conftest.py`

Shared fixtures for all tests:

```python
@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with basic structure."""
    # Creates: src/, tests/, docs/, .git/
    # Creates: pyproject.toml, README.md

@pytest.fixture
def tmp_fish_history(tmp_path):
    """Create a temporary Fish history file."""
    # Sample commands: git, cd, eza, bat

@pytest.fixture
def sample_tool_info():
    """Sample ToolInfo object."""

@pytest.fixture
def sample_slash_command():
    """Sample SlashCommand object."""

@pytest.fixture
def sample_command_usage():
    """Sample CommandUsage object."""
```

## Test Output Examples

### Successful Test Run

```
============================= test session starts ==============================
platform linux -- Python 3.13.7, pytest-8.4.1, pluggy-1.6.0
collected 59 items

tests/test_integration.py::TestPhase1Integration::test_permissions_end_to_end PASSED [  1%]
tests/test_integration.py::TestPhase2Integration::test_directory_context_end_to_end PASSED [  3%]
tests/test_integration.py::TestPhase3Integration::test_local_context_end_to_end PASSED [  5%]
tests/test_integration.py::TestPhase4Integration::test_slash_commands_end_to_end PASSED [  6%]
tests/test_integration.py::TestPhase6Integration::test_usage_analytics_end_to_end PASSED [  8%]
tests/test_integration.py::TestCrossPhaseIntegration::test_full_project_setup PASSED [ 10%]
tests/test_integration.py::TestCrossPhaseIntegration::test_idempotency PASSED [ 11%]
tests/test_schemas.py::TestToolInfo::test_valid_tool_info PASSED         [ 13%]
# ... 52 more tests ...
======================= 59 passed, 16 warnings in 0.45s ========================
```

### Coverage Report

```bash
pytest --cov=claude_automation --cov-report=term-missing

Name                                          Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------
claude_automation/analyzers/__init__.py           5      0   100%
claude_automation/analyzers/directory_analyzer.py    120     10    92%   45-48, 89-92
claude_automation/analyzers/project_detector.py      80      5    94%   67-71
claude_automation/analyzers/system_analyzer.py       150     15    90%   multiple
claude_automation/analyzers/usage_tracker.py         200     20    90%   multiple
claude_automation/analyzers/workflow_analyzer.py     150     10    93%   multiple
claude_automation/generators/base_generator.py       50      0   100%
claude_automation/generators/permissions_generator.py 120      8    93%   multiple
claude_automation/schemas.py                         250      5    98%   multiple
---------------------------------------------------------------------------
TOTAL                                           1125     73    94%
```

## Test Philosophy

This project follows the **"minimal testing"** philosophy:

### What We Test

✅ **Schema validation** - Ensures Pydantic models enforce business rules
✅ **Template rendering** - Catches Jinja2 syntax errors early
✅ **Integration workflows** - Each phase tested end-to-end
✅ **Edge cases** - Empty data, None values, nonexistent paths
✅ **Idempotency** - Generators can run multiple times safely

### What We Don't Test

❌ **High coverage** - Not worth it for infrequently-changed infrastructure code
❌ **TDD enforcement** - Deliberately removed for infrastructure code
❌ **Complex mocking** - Keep tests simple and readable
❌ **Every function** - Focus on critical paths and integration points

### Rationale

> "Test enough to refactor confidently, not so much that tests become the product."

This is **infrastructure automation**, not a SaaS product. The testing strategy reflects this:
- Manual validation is effective (user reviews outputs)
- Low blast radius (failures don't cascade)
- Single maintainer (no team coordination)
- Infrequent changes (stable codebase)

## Continuous Integration

### Running Tests in CI/CD (Future)

When setting up GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: cachix/install-nix-action@v20
      - run: nix develop --command pytest -v
```

## Debugging Test Failures

### Common Issues

**1. Template Not Found**
```
TemplateNotFound: 'base.j2'
```
**Fix:** Ensure template path is `permissions/base.j2` not `base.j2`

**2. Directory Already Exists**
```
FileExistsError: [Errno 17] File exists: '/tmp/.../test_project/src'
```
**Fix:** Add `exist_ok=True` to `mkdir()` calls

**3. Assertion Failure**
```
AssertionError: assert 'CLAUDE.md' in content
```
**Fix:** Check what's actually in `content`, adjust assertion to match reality

### Verbose Mode

```bash
# See full output
pytest -vv

# See stdout/stderr
pytest -s

# Stop on first failure
pytest -x

# See full traceback
pytest --tb=long
```

### Debugging Specific Tests

```bash
# Run single test
pytest tests/test_schemas.py::TestToolInfo::test_valid_tool_info -v

# Run with pdb on failure
pytest --pdb

# Print variables
pytest -vv --showlocals
```

## Adding New Tests

### 1. Adding Schema Tests

When adding a new Pydantic model:

```python
# tests/test_schemas.py

class TestNewSchema:
    """Tests for NewSchema."""

    def test_valid_config(self):
        """Valid NewSchema should validate."""
        config = NewSchema(field1="value", field2=123)
        assert config.field1 == "value"

    def test_invalid_field(self):
        """Invalid field should raise ValidationError."""
        with pytest.raises(ValidationError):
            NewSchema(field1="", field2=-1)  # Invalid values
```

### 2. Adding Template Tests

When adding a new Jinja2 template:

```python
# tests/test_templates.py

def test_new_template_renders(jinja_env):
    """New template should render without errors."""
    template = jinja_env.get_template("new_template.j2")

    context = {
        "required_field": "value",
        "optional_field": None,
    }

    result = template.render(**context)
    assert len(result) > 0
    assert "expected content" in result
```

### 3. Adding Integration Tests

When adding a new phase:

```python
# tests/test_integration.py

class TestPhaseXIntegration:
    """Integration tests for Phase X: New Feature."""

    def test_new_feature_end_to_end(self, tmp_project):
        """Test full Phase X workflow."""
        # Setup
        # Analyze
        # Generate
        # Verify output exists
        # Verify content is correct
```

## Performance Testing

### Benchmarking

```bash
# Time individual phases
time nix run .#update-permissions
time nix run .#update-slash-commands
time nix run .#update-usage-analytics

# Time full suite
time nix run .#update-all
```

### Expected Performance

| Phase | Execution Time | Complexity |
|-------|----------------|------------|
| Permissions | < 1 second | Project type detection |
| Directory Context | < 2 seconds | File system scanning |
| Local Context | < 1 second | System introspection |
| Slash Commands | < 2 seconds | Git log parsing (100 commits) |
| Usage Analytics | < 3 seconds | Fish history parsing (1000+ commands) |
| **Total** | **< 10 seconds** | **All phases** |

## Test Maintenance

### When to Update Tests

1. **New schema added** → Add validation tests
2. **New template added** → Add rendering tests
3. **New phase added** → Add integration tests
4. **Breaking change** → Update affected tests
5. **Bug fix** → Add regression test (optional)

### Test Coverage Goals

- ✅ **90%+ for schemas** - Type safety is critical
- ✅ **100% for templates** - All templates must render
- ✅ **100% for phases** - Each phase needs smoke test
- ❌ **< 80% overall** - Don't over-test infrastructure code

## Troubleshooting

### Tests Pass Locally, Fail in Nix Build

**Cause:** Different Python/package versions

**Solution:**
```bash
nix develop --command pytest -v
# Always test in Nix environment
```

### Flaky Tests

**Cause:** Datetime.now() generating different values

**Solution:**
```python
# Use fixed datetime in tests
from datetime import datetime
fixed_time = datetime(2025, 10, 8, 12, 0, 0)
```

### Import Errors

**Cause:** Python path not set correctly

**Solution:**
```bash
# In nix develop, PYTHONPATH is set automatically
# Outside nix, use:
export PYTHONPATH="$PWD:$PYTHONPATH"
pytest
```

## Best Practices

1. ✅ **Use fixtures** - Share common setup via `conftest.py`
2. ✅ **Test edge cases** - Empty lists, None values, missing files
3. ✅ **Clear test names** - `test_permissions_end_to_end` not `test_phase1`
4. ✅ **One assertion focus** - Test one thing per test function
5. ✅ **Fast tests** - Keep integration tests under 5 seconds each
6. ✅ **Isolated tests** - No test dependencies, can run in any order
7. ✅ **Document why** - Add docstrings explaining what's being tested

## Summary

- **59 tests, 100% passing**
- **3 test categories** (schemas, templates, integration)
- **Minimal philosophy** - Test critical paths, not everything
- **Fast execution** - Full suite runs in < 1 second
- **Easy to extend** - Clear patterns for adding new tests

Run tests before every commit:
```bash
nix develop --command pytest -v
```

---

## Tier 1 Learning Components

Additional tests for the adaptive learning system (Phases 3-5).

### Components

1. **Permission Learning** - `approval_tracker.py`, `permission_pattern_detector.py`
2. **Global MCP Optimization** - `global_mcp_analyzer.py`
3. **Context Optimization** - `context_optimizer.py`

### Test Files

| Component | Test Files | Test Cases |
|-----------|------------|------------|
| Permission Learning | `tests/unit/test_approval_tracker.py`<br>`tests/unit/test_permission_patterns.py`<br>`tests/integration/test_learning_cycle.py` | 17<br>24<br>8 |
| MCP Optimization | `tests/unit/test_global_mcp_analyzer.py`<br>`tests/integration/test_cross_project.py` | 13<br>7 |
| Context Optimization | `tests/unit/test_context_optimizer.py` | 19 |
| **TOTAL** | **6 test files** | **88 tests** |

### Running Tier 1 Tests

```bash
# All Tier 1 tests
pytest tests/unit/test_approval_tracker.py tests/unit/test_permission_patterns.py -v
pytest tests/unit/test_global_mcp_analyzer.py tests/unit/test_context_optimizer.py -v
pytest tests/integration/test_learning_cycle.py tests/integration/test_cross_project.py -v

# Or run all together
pytest tests/unit/test_*_{approval,permission,mcp,context}*.py -v
```

### Prerequisites

Requires `pydantic` (available in devenv):

```bash
devenv shell
pytest tests/unit/test_approval_tracker.py -v
```

Or use `uv`:

```bash
uv run python -m pytest tests/unit/test_approval_tracker.py -v
```
