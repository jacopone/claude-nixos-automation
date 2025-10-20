#!/usr/bin/env bash
# Test all Tier 1 learning components end-to-end
# This validates that Phase 3, 4, and 5 are fully functional

echo "========================================="
echo "Testing Tier 1 Learning Components"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_passed=0
test_failed=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${YELLOW}Testing: ${test_name}${NC}"

    # Run in devenv shell for access to pydantic
    if bash -c "source /etc/profiles/per-user/guyfawkes/etc/profile.d/hm-session-vars.sh 2>/dev/null && eval \"\$(direnv export bash)\" 2>/dev/null && $test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((test_passed++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Error output:"
        cat /tmp/test_output.log | tail -20
        ((test_failed++))
        return 1
    fi
}

echo "========================================="
echo "Phase 3: Permission Learning"
echo "========================================="
echo ""

# Test 1: Import ApprovalTracker
run_test "Import ApprovalTracker" \
    "python -c 'from claude_automation.analyzers.approval_tracker import ApprovalTracker; print(\"✓ Import successful\")'"

# Test 2: Log approval
run_test "Log permission approval" \
    "python -c '
from claude_automation.analyzers.approval_tracker import ApprovalTracker
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"approvals.jsonl\"
    tracker = ApprovalTracker(log_file)
    tracker.log_approval(\"Bash(git status:*)\", \"test-session\", \"/test/project\")
    approvals = tracker.get_recent_approvals(days=1)
    assert len(approvals) == 1, f\"Expected 1 approval, got {len(approvals)}\"
    print(\"✓ Logged and retrieved approval\")
'"

# Test 3: Pattern detection
run_test "Detect permission patterns" \
    "python -c '
from claude_automation.analyzers.permission_pattern_detector import PermissionPatternDetector
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"approvals.jsonl\"
    detector = PermissionPatternDetector(log_file)

    # Simulate approvals
    from claude_automation.analyzers.approval_tracker import ApprovalTracker
    tracker = ApprovalTracker(log_file)
    for i in range(5):
        tracker.log_approval(\"Bash(git status:*)\", f\"session-{i}\", \"/test/project\")

    # Detect patterns
    patterns = detector.detect_patterns(days=1)
    assert len(patterns) > 0, \"Expected to detect at least one pattern\"
    print(f\"✓ Detected {len(patterns)} pattern(s)\")
'"

# Test 4: Intelligent permissions generator
run_test "Generate permissions with learning" \
    "python -c '
from claude_automation.generators.intelligent_permissions_generator import IntelligentPermissionsGenerator
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"approvals.jsonl\"

    # Simulate approvals
    from claude_automation.analyzers.approval_tracker import ApprovalTracker
    tracker = ApprovalTracker(log_file)
    for i in range(5):
        tracker.log_approval(\"Bash(git status:*)\", f\"session-{i}\", \"/test/project\")

    # Generate suggestions
    generator = IntelligentPermissionsGenerator(log_file)
    suggestions = generator.get_pattern_suggestions(days=1)
    print(f\"✓ Generated {len(suggestions)} suggestion(s)\")
'"

echo ""
echo "========================================="
echo "Phase 4: Global MCP Optimization"
echo "========================================="
echo ""

# Test 5: Import GlobalMCPAnalyzer
run_test "Import GlobalMCPAnalyzer" \
    "python -c 'from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer; print(\"✓ Import successful\")'"

# Test 6: Discover projects
run_test "Discover MCP projects" \
    "python -c '
from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from pathlib import Path
import tempfile
import json

with tempfile.TemporaryDirectory() as tmpdir:
    home = Path(tmpdir)

    # Create test project
    project = home / \"test_project\"
    project.mkdir()
    (project / \".claude\").mkdir()
    (project / \".claude\" / \"mcp.json\").write_text(
        json.dumps({\"mcpServers\": {\"test-server\": {\"command\": \"node\"}}})
    )

    analyzer = GlobalMCPAnalyzer(home)
    projects = analyzer.discover_projects()
    assert len(projects) == 1, f\"Expected 1 project, got {len(projects)}\"
    print(f\"✓ Discovered {len(projects)} project(s)\")
'"

# Test 7: Analyze all projects
run_test "Analyze all MCP projects" \
    "python -c '
from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from pathlib import Path
import tempfile
import json

with tempfile.TemporaryDirectory() as tmpdir:
    home = Path(tmpdir)

    # Create test project
    project = home / \"test_project\"
    project.mkdir()
    (project / \".claude\").mkdir()
    (project / \".claude\" / \"mcp.json\").write_text(
        json.dumps({\"mcpServers\": {\"test-server\": {\"command\": \"node\"}}})
    )

    analyzer = GlobalMCPAnalyzer(home)
    report = analyzer.analyze_all_projects()
    assert report.total_projects == 1, f\"Expected 1 project, got {report.total_projects}\"
    assert report.total_servers == 1, f\"Expected 1 server, got {report.total_servers}\"
    print(f\"✓ Analyzed {report.total_projects} project(s), {report.total_servers} server(s)\")
'"

# Test 8: Generate summary
run_test "Generate MCP summary" \
    "python -c '
from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from pathlib import Path
import tempfile
import json

with tempfile.TemporaryDirectory() as tmpdir:
    home = Path(tmpdir)

    # Create test project
    project = home / \"test_project\"
    project.mkdir()
    (project / \".claude\").mkdir()
    (project / \".claude\" / \"mcp.json\").write_text(
        json.dumps({\"mcpServers\": {\"test-server\": {\"command\": \"node\"}}})
    )

    analyzer = GlobalMCPAnalyzer(home)
    report = analyzer.analyze_all_projects()
    summary = analyzer.generate_summary(report)
    assert \"Global MCP Analysis\" in summary, \"Expected summary to contain title\"
    print(\"✓ Generated summary\")
    print(summary)
'"

echo ""
echo "========================================="
echo "Phase 5: Context Optimization"
echo "========================================="
echo ""

# Test 9: Import ContextOptimizer
run_test "Import ContextOptimizer" \
    "python -c 'from claude_automation.analyzers.context_optimizer import ContextOptimizer; print(\"✓ Import successful\")'"

# Test 10: Log section access
run_test "Log section access" \
    "python -c '
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"context-access.jsonl\"
    optimizer = ContextOptimizer(log_file)

    optimizer.log_section_access(
        section_name=\"Modern CLI Tools\",
        tokens_in_section=500,
        relevance_score=0.9,
        session_id=\"test-session\",
        query_context=\"User asked about eza\"
    )

    assert log_file.exists(), \"Log file should exist\"
    print(\"✓ Logged section access\")
'"

# Test 11: Calculate usage statistics
run_test "Calculate section usage statistics" \
    "python -c '
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"context-access.jsonl\"
    optimizer = ContextOptimizer(log_file)

    # Log multiple accesses
    for i in range(10):
        optimizer.log_section_access(
            section_name=\"Test Section\",
            tokens_in_section=500,
            relevance_score=0.8,
            session_id=f\"session-{i}\"
        )

    stats = optimizer.get_section_usage_statistics(period_days=1)
    assert \"Test Section\" in stats, \"Expected to find Test Section in stats\"
    assert stats[\"Test Section\"].total_loads == 10, f\"Expected 10 loads, got {stats['Test Section'].total_loads}\"
    print(f\"✓ Calculated usage statistics: {stats['Test Section'].total_loads} loads\")
'"

# Test 12: Identify noise sections
run_test "Identify noise sections" \
    "python -c '
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"context-access.jsonl\"
    optimizer = ContextOptimizer(log_file)

    # Create noise section (loaded many times, low relevance)
    for i in range(20):
        optimizer.log_section_access(
            section_name=\"Noise Section\",
            tokens_in_section=500,
            relevance_score=0.0,  # Never relevant
            session_id=f\"session-{i}\"
        )

    noise = optimizer.identify_noise_sections(period_days=1)
    assert len(noise) == 1, f\"Expected 1 noise section, got {len(noise)}\"
    print(f\"✓ Identified {len(noise)} noise section(s)\")
'"

# Test 13: Calculate effective ratio
run_test "Calculate effective context ratio" \
    "python -c '
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"context-access.jsonl\"
    optimizer = ContextOptimizer(log_file)

    # Good section (high relevance)
    for i in range(10):
        optimizer.log_section_access(
            section_name=\"Good Section\",
            tokens_in_section=500,
            relevance_score=0.9,
            session_id=f\"session-{i}\"
        )

    ratio = optimizer.calculate_effective_context_ratio(period_days=1)
    assert ratio > 0.7, f\"Expected ratio > 0.7, got {ratio:.2f}\"
    print(f\"✓ Calculated effective ratio: {ratio:.2%}\")
'"

# Test 14: Generate optimization suggestions
run_test "Generate optimization suggestions" \
    "python -c '
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / \"context-access.jsonl\"
    optimizer = ContextOptimizer(log_file)

    # Create noise section
    for i in range(20):
        optimizer.log_section_access(
            section_name=\"Noise Section\",
            tokens_in_section=800,
            relevance_score=0.0,
            session_id=f\"session-{i}\"
        )

    suggestions = optimizer.analyze(period_days=1)
    assert len(suggestions) > 0, \"Expected at least one suggestion\"
    prune_suggestions = [s for s in suggestions if s.optimization_type == \"prune_section\"]
    assert len(prune_suggestions) > 0, \"Expected at least one prune suggestion\"
    print(f\"✓ Generated {len(suggestions)} suggestion(s)\")
'"

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""
echo -e "${GREEN}Passed: ${test_passed}${NC}"
echo -e "${RED}Failed: ${test_failed}${NC}"
echo ""

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}========================================="
    echo "All Tier 1 Components Working! ✓"
    echo "=========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================="
    echo "Some tests failed"
    echo "=========================================${NC}"
    exit 1
fi
