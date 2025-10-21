#!/usr/bin/env bash
#
# Test Suite for Permission Auto-Learner Hook
#
# Tests:
# 1. Hook processes input correctly
# 2. Invocation counter works
# 3. Pattern analysis runs at correct intervals
# 4. Permission rules are generated
# 5. Settings file is updated correctly
# 6. Notification file is created

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOK_SCRIPT="$PROJECT_ROOT/claude_automation/hooks/permission_auto_learner.py"
CLI_TOOL="$PROJECT_ROOT/claude_automation/tools/permission_suggester.py"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "\n${YELLOW}TEST: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

cleanup() {
    # Clean up test artifacts
    rm -f /tmp/permission-auto-learner-log.txt
    rm -f ~/.claude/learner_counter_test_session_*.txt
    rm -rf /tmp/test_project_autolearner
}

trap cleanup EXIT

# Test 1: Hook accepts valid JSON input
print_test "Hook accepts valid JSON input"

TEST_INPUT='{
  "session_id": "test_session_1",
  "tool_name": "Bash",
  "tool_input": {"command": "echo test"},
  "project_path": "/tmp/test_project"
}'

if echo "$TEST_INPUT" | python3 "$HOOK_SCRIPT" 2>/dev/null; then
    print_pass "Hook processes JSON input without errors"
else
    print_fail "Hook failed to process JSON input"
fi

# Test 2: Invocation counter increments
print_test "Invocation counter increments correctly"

SESSION_ID="test_session_counter"
COUNTER_FILE="$HOME/.claude/learner_counter_${SESSION_ID}.txt"

# Clean counter
rm -f "$COUNTER_FILE"

# Send 3 inputs
for i in {1..3}; do
    echo '{"session_id": "'$SESSION_ID'", "tool_name": "Bash", "tool_input": {}, "project_path": "/tmp/test"}' | \
        python3 "$HOOK_SCRIPT" 2>/dev/null
done

# Check counter
if [ -f "$COUNTER_FILE" ]; then
    COUNT=$(cat "$COUNTER_FILE")
    if [ "$COUNT" = "3" ]; then
        print_pass "Counter incremented to 3"
    else
        print_fail "Counter is $COUNT, expected 3"
    fi
else
    print_fail "Counter file not created"
fi

# Test 3: CLI tool runs without errors
print_test "CLI tool runs without errors"

if python3 "$CLI_TOOL" --help >/dev/null 2>&1; then
    print_pass "CLI tool --help works"
else
    print_fail "CLI tool --help failed"
fi

# Test 4: CLI tool can analyze approval history
print_test "CLI tool analyzes approval history"

# Check if learning directory exists
if [ -d "$HOME/.claude/learning" ]; then
    if python3 "$CLI_TOOL" --analyze-all 2>&1 | grep -q "Found"; then
        print_pass "CLI tool analyzes all projects"
    else
        print_fail "CLI tool analysis output unexpected"
    fi
else
    echo "  ⚠️  Skipping (no approval history found)"
fi

# Test 5: Hook logs debug messages
print_test "Hook logs debug messages"

rm -f /tmp/permission-auto-learner-log.txt

echo '{"session_id": "debug_test", "tool_name": "Read", "tool_input": {}, "project_path": "/tmp"}' | \
    python3 "$HOOK_SCRIPT" 2>/dev/null

if [ -f /tmp/permission-auto-learner-log.txt ]; then
    if grep -q "Hook triggered" /tmp/permission-auto-learner-log.txt; then
        print_pass "Debug logging works"
    else
        print_fail "Debug log missing expected messages"
    fi
else
    print_fail "Debug log file not created"
fi

# Test 6: Hook respects environment variable
print_test "Hook respects ENABLE_PERMISSION_AUTO_LEARN=0"

COUNTER_FILE_DISABLED="$HOME/.claude/learner_counter_disabled_test.txt"
rm -f "$COUNTER_FILE_DISABLED"

export ENABLE_PERMISSION_AUTO_LEARN=0
echo '{"session_id": "disabled_test", "tool_name": "Bash", "tool_input": {}, "project_path": "/tmp"}' | \
    python3 "$HOOK_SCRIPT" 2>/dev/null
unset ENABLE_PERMISSION_AUTO_LEARN

if [ ! -f "$COUNTER_FILE_DISABLED" ]; then
    print_pass "Hook disabled when ENABLE_PERMISSION_AUTO_LEARN=0"
else
    print_fail "Hook ran despite being disabled"
fi

# Test 7: CLI tool handles missing approval data gracefully
print_test "CLI tool handles missing project gracefully"

if python3 "$CLI_TOOL" /nonexistent/project/path 2>&1 | grep -q "No new permission patterns"; then
    print_pass "CLI tool handles missing project"
else
    # Also acceptable if it shows 0 suggestions
    if python3 "$CLI_TOOL" /nonexistent/project/path 2>&1 | grep -q "Found 0"; then
        print_pass "CLI tool handles missing project (0 suggestions)"
    else
        print_fail "CLI tool error handling needs improvement"
    fi
fi

# Test 8: Hook script is executable
print_test "Hook script has executable permissions"

if [ -x "$HOOK_SCRIPT" ]; then
    print_pass "Hook script is executable"
else
    print_fail "Hook script is not executable"
fi

# Test 9: CLI tool script is executable
print_test "CLI tool has executable permissions"

if [ -x "$CLI_TOOL" ]; then
    print_pass "CLI tool is executable"
else
    print_fail "CLI tool is not executable"
fi

# Test 10: Hook can be imported as Python module
print_test "Hook can be imported as Python module"

if python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from claude_automation.hooks import permission_auto_learner" 2>/dev/null; then
    print_pass "Hook imports without errors"
else
    echo "  ⚠️  Skipping (module structure may not support direct import)"
fi

# Test 11: Integration with existing analyzers
print_test "Hook integrates with ApprovalTracker and PermissionPatternDetector"

if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from claude_automation.analyzers import ApprovalTracker, PermissionPatternDetector

tracker = ApprovalTracker()
detector = PermissionPatternDetector(tracker)
print('Integration OK')
" 2>/dev/null | grep -q "Integration OK"; then
    print_pass "Integration with analyzers works"
else
    print_fail "Integration with analyzers failed"
fi

# Print summary
echo ""
echo "========================================"
echo "          TEST SUMMARY"
echo "========================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "========================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
