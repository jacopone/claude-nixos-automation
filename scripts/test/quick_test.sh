#!/usr/bin/env bash
set -e

echo "🧪 Quick Dependency & Import Test"
echo "=================================="

cd /home/guyfawkes/claude-nixos-automation

# Test 1: Dependencies
echo ""
echo "1. Testing Python dependencies..."
devenv shell -c "python -c 'import pydantic; import jinja2; print(\"✅ pydantic\", pydantic.__version__); print(\"✅ jinja2\", jinja2.__version__)'"

# Test 2: Basic imports
echo ""
echo "2. Testing core imports..."
devenv shell -c "python -c 'from claude_automation.core import AdaptiveSystemEngine; print(\"✅ AdaptiveSystemEngine imported\")'"

# Test 3: All analyzers
echo ""
echo "3. Testing all analyzers..."
devenv shell -c "python -c 'from claude_automation.analyzers import ApprovalTracker, PermissionPatternDetector, GlobalMCPAnalyzer, ContextOptimizer, WorkflowDetector, InstructionEffectivenessTracker, ProjectArchetypeDetector, MetaLearner; print(\"✅ All 8 analyzers imported\")'"

# Test 4: Generator
echo ""
echo "4. Testing intelligent generator..."
devenv shell -c "python -c 'from claude_automation.generators.intelligent_permissions_generator import IntelligentPermissionsGenerator; print(\"✅ IntelligentPermissionsGenerator imported\")'"

echo ""
echo "=================================="
echo "✅ ALL TESTS PASSED!"
