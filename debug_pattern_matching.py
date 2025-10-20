#!/usr/bin/env python3
"""Debug pattern matching logic."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.analyzers.approval_tracker import ApprovalTracker

print("🔍 Debugging Pattern Matching\n")

# Get real data
tracker = ApprovalTracker()
approvals = tracker.get_recent_approvals(days=30)

print(f"📊 Sample of actual approval data:")
for a in approvals[:10]:
    print(f"   {a.permission}")

print(f"\n📋 Pattern regexes being tested:")
patterns = {
    "modern_cli": r"Bash\((fd|eza|bat|rg|dust|procs)",
    "git": r"Bash\(git (status|log|diff|show|branch)",
}

for name, pattern in patterns.items():
    print(f"   {name}: {pattern}")

print(f"\n🧪 Testing matches:")
test_permissions = [
    "Bash(fd:*)",
    "Bash(git:*)",
    "Bash(git status:*)",
    "Bash(fd --help)",
]

for perm in test_permissions:
    for name, pattern in patterns.items():
        match = re.search(pattern, perm, re.IGNORECASE)
        status = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"   {status}: '{perm}' vs {name}")
