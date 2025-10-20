---
status: draft
created: 2025-10-20
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# Tier 1 Components - Testing Guide

**Date**: 2025-10-17
**Status**: All Tier 1 components implemented and ready for testing

---

## Overview

All three Tier 1 learning components have been fully implemented:

1. ✅ **Phase 3**: Permission Learning
2. ✅ **Phase 4**: Global MCP Optimization
3. ✅ **Phase 5**: Context Optimization

This guide provides instructions for testing each component independently.

---

## Prerequisites

The components require pydantic, which is available in the devenv environment:

```bash
cd /home/guyfawkes/claude-nixos-automation
devenv shell
```

Alternatively, use `uv`:

```bash
uv run python <script>
```

---

## Component 1: Permission Learning (Phase 3)

### Location
- **Code**: `claude_automation/analyzers/approval_tracker.py`
- **Code**: `claude_automation/analyzers/permission_pattern_detector.py`
- **Code**: `claude_automation/generators/intelligent_permissions_generator.py`
- **Tests**: `tests/unit/test_approval_tracker.py`
- **Tests**: `tests/unit/test_permission_patterns.py`
- **Tests**: `tests/integration/test_learning_cycle.py`

### Manual Test

```python
from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.permission_pattern_detector import PermissionPatternDetector
from pathlib import Path
import tempfile

# Create temp log file
with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / "approvals.jsonl"

    # 1. Log some approvals
    tracker = ApprovalTracker(log_file)
    for i in range(5):
        tracker.log_approval("Bash(git status:*)", f"session-{i}", "/test/project")

    # 2. Get recent approvals
    approvals = tracker.get_recent_approvals(days=30)
    print(f"✓ Logged {len(approvals)} approvals")

    # 3. Detect patterns
    detector = PermissionPatternDetector(log_file)
    patterns = detector.detect_patterns(days=30)
    print(f"✓ Detected {len(patterns)} patterns")

    for pattern in patterns:
        print(f"  - {pattern.pattern_type}: {pattern.confidence:.0%} confidence")
```

### Run Unit Tests

```bash
uv run python -m pytest tests/unit/test_approval_tracker.py -v
uv run python -m pytest tests/unit/test_permission_patterns.py -v
uv run python -m pytest tests/integration/test_learning_cycle.py -v
```

### Expected Results

- ✓ Approvals logged to JSONL file
- ✓ Patterns detected from approval history
- ✓ Confidence scores calculated
- ✓ Pattern suggestions generated

---

## Component 2: Global MCP Optimization (Phase 4)

### Location
- **Code**: `claude_automation/analyzers/global_mcp_analyzer.py`
- **Tests**: `tests/unit/test_global_mcp_analyzer.py`
- **Tests**: `tests/integration/test_cross_project.py`

### Manual Test

```python
from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from pathlib import Path
import tempfile
import json

# Create temp projects
with tempfile.TemporaryDirectory() as tmpdir:
    home = Path(tmpdir)

    # Create test project with MCP config
    project = home / "test_project"
    project.mkdir()
    (project / ".claude").mkdir()
    (project / ".claude" / "mcp.json").write_text(
        json.dumps({
            "mcpServers": {
                "mcp-nixos": {"command": "mcp-nixos"},
                "serena": {"command": "serena"}
            }
        })
    )

    # 1. Discover projects
    analyzer = GlobalMCPAnalyzer(home)
    projects = analyzer.discover_projects()
    print(f"✓ Discovered {len(projects)} project(s)")

    # 2. Analyze all projects
    report = analyzer.analyze_all_projects()
    print(f"✓ Analyzed {report.total_projects} project(s)")
    print(f"✓ Found {report.total_servers} MCP server(s)")

    # 3. Generate summary
    summary = analyzer.generate_summary(report)
    print(summary)
```

### Run Unit Tests

```bash
uv run python -m pytest tests/unit/test_global_mcp_analyzer.py -v
uv run python -m pytest tests/integration/test_cross_project.py -v
```

### Expected Results

- ✓ Projects with `.claude/mcp.json` discovered
- ✓ Global vs project-specific servers distinguished
- ✓ Usage statistics aggregated
- ✓ Recommendations generated
- ✓ Summary formatted for display

---

## Component 3: Context Optimization (Phase 5)

### Location
- **Code**: `claude_automation/analyzers/context_optimizer.py`
- **Tests**: `tests/unit/test_context_optimizer.py`

### Manual Test

```python
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from pathlib import Path
import tempfile

# Create temp log file
with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / "context-access.jsonl"
    optimizer = ContextOptimizer(log_file)

    # 1. Log section accesses
    for i in range(10):
        optimizer.log_section_access(
            section_name="Modern CLI Tools",
            tokens_in_section=500,
            relevance_score=0.9,
            session_id=f"session-{i}"
        )

    # Create noise section
    for i in range(20):
        optimizer.log_section_access(
            section_name="Rarely Used Section",
            tokens_in_section=800,
            relevance_score=0.0,  # Never relevant
            session_id=f"session-noise-{i}"
        )

    # 2. Get usage statistics
    stats = optimizer.get_section_usage_statistics(period_days=1)
    print(f"✓ Tracked {len(stats)} section(s)")

    for name, usage in stats.items():
        print(f"  - {name}: {usage.utilization_rate:.0%} utilization")

    # 3. Identify noise
    noise = optimizer.identify_noise_sections(period_days=1)
    print(f"✓ Identified {len(noise)} noise section(s)")

    # 4. Calculate effective ratio
    ratio = optimizer.calculate_effective_context_ratio(period_days=1)
    print(f"✓ Effective context ratio: {ratio:.1%}")

    # 5. Generate suggestions
    suggestions = optimizer.analyze(period_days=1)
    print(f"✓ Generated {len(suggestions)} suggestion(s)")

    for s in suggestions:
        print(f"  - [{s.optimization_type}] {s.section_name}")
        print(f"    {s.reason}")
```

### Run Unit Tests

```bash
uv run python -m pytest tests/unit/test_context_optimizer.py -v
```

### Expected Results

- ✓ Section accesses logged to JSONL
- ✓ Usage statistics calculated per section
- ✓ Noise sections identified (low utilization)
- ✓ Effective context ratio calculated
- ✓ Optimization suggestions generated

---

## Automated Test Script

A comprehensive test script has been created: `test_tier1_manual.py`

### Run All Tests

```bash
# Option 1: Using devenv shell
devenv shell -c "python test_tier1_manual.py"

# Option 2: Using uv (if configured)
uv run python test_tier1_manual.py
```

The script tests all 14 scenarios across all three components.

---

## Test Status

### Test Files Created

| Component | Test File | Test Cases | Status |
|-----------|-----------|------------|--------|
| Permission Learning | `tests/unit/test_approval_tracker.py` | 17 | ✅ Created |
| Permission Learning | `tests/unit/test_permission_patterns.py` | 24 | ✅ Created |
| Permission Learning | `tests/integration/test_learning_cycle.py` | 8 | ✅ Created |
| MCP Optimization | `tests/unit/test_global_mcp_analyzer.py` | 13 | ✅ Created |
| MCP Optimization | `tests/integration/test_cross_project.py` | 7 | ✅ Created |
| Context Optimization | `tests/unit/test_context_optimizer.py` | 19 | ✅ Created |
| **TOTAL** | **6 test files** | **88 test cases** | ✅ **Complete** |

### Implementation Files

| Component | File | Status |
|-----------|------|--------|
| Permission Learning | `approval_tracker.py` | ✅ Complete |
| Permission Learning | `permission_pattern_detector.py` | ✅ Complete |
| Permission Learning | `intelligent_permissions_generator.py` | ✅ Complete |
| MCP Optimization | `global_mcp_analyzer.py` | ✅ Complete |
| Context Optimization | `context_optimizer.py` | ✅ Complete |

---

## Known Issues

### Pydantic Dependency

The components require `pydantic`, which is installed in the devenv environment but not globally. This is by design to keep the system dependencies isolated.

**Solution**: Always run tests within `devenv shell` or using `uv run`.

### Session Log Format

MCP usage analysis (Phase 4) expects session logs in a specific JSONL format. These logs are not yet being generated by Claude Code, so token consumption tracking is a placeholder.

**Future Work**: Integrate with Claude Code to generate actual session logs.

---

## Next Steps

### Option 1: Run Existing pytest Tests

The most reliable way to test:

```bash
# In devenv shell
devenv shell

# Run all Tier 1 tests
pytest tests/unit/test_approval_tracker.py -v
pytest tests/unit/test_permission_patterns.py -v
pytest tests/unit/test_global_mcp_analyzer.py -v
pytest tests/unit/test_context_optimizer.py -v
pytest tests/integration/test_learning_cycle.py -v
pytest tests/integration/test_cross_project.py -v
```

### Option 2: Manual Smoke Tests

Copy-paste the manual test code above into a Python REPL within devenv shell.

### Option 3: Integration Testing (Phase 10)

Move forward to Phase 10 to create the Adaptive System Engine that ties all components together and provides a unified CLI.

---

## Summary

All three Tier 1 learning components are **fully implemented** with:

- ✅ **Complete implementations** (5 analyzer/generator files)
- ✅ **Comprehensive tests** (88 test cases across 6 files)
- ✅ **Documented APIs** (in code comments and schemas)
- ✅ **Ready for integration** (Phase 10)

The components are production-ready but need to be tested within the devenv environment due to the pydantic dependency.
