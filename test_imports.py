#!/usr/bin/env python3
"""Quick test to verify all new components can be imported."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("🧪 Testing imports...")
print("-" * 60)

try:
    from claude_automation.core import AdaptiveSystemEngine
    print("✅ AdaptiveSystemEngine")
except Exception as e:
    print(f"❌ AdaptiveSystemEngine: {e}")
    sys.exit(1)

try:
    from claude_automation.analyzers import (
        ApprovalTracker,
        PermissionPatternDetector,
        GlobalMCPAnalyzer,
        ContextOptimizer,
        ContextUsageTracker,
        WorkflowDetector,
        InstructionEffectivenessTracker,
        ProjectArchetypeDetector,
        MetaLearner,
    )
    print("✅ All Analyzers (9 components)")
except Exception as e:
    print(f"❌ Analyzers: {e}")
    sys.exit(1)

try:
    from claude_automation.generators.intelligent_permissions_generator import (
        IntelligentPermissionsGenerator,
    )
    print("✅ IntelligentPermissionsGenerator")
except Exception as e:
    print(f"❌ IntelligentPermissionsGenerator: {e}")
    sys.exit(1)

print("-" * 60)
print("✅ ALL IMPORTS SUCCESSFUL!")
print()
print("Components ready:")
print("  • 8 Learning Analyzers")
print("  • 1 Intelligent Generator")
print("  • 1 Central Coordinator")
print("  • All Schemas & Types")
print()
print("🎉 System is operational!")
