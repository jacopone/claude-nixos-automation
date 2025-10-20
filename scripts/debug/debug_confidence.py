#!/usr/bin/env python3
"""Debug confidence calculation."""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.analyzers.approval_tracker import ApprovalTracker

print("🔍 Debugging Confidence Calculation\n")

# Get real data
tracker = ApprovalTracker()
approvals = tracker.get_recent_approvals(days=30)

print(f"📊 Total approvals: {len(approvals)}")

# Test modern_cli pattern
pattern_regex = r"Bash\((fd|eza|bat|rg|dust|procs)"
matching = []

for approval in approvals:
    if re.search(pattern_regex, approval.permission, re.IGNORECASE):
        matching.append(approval)

print(f"\n🔍 Modern CLI pattern matches: {len(matching)}")
print(f"   Pattern: {pattern_regex}")

if matching:
    print("\n   Sample matches:")
    counter = Counter(a.permission for a in matching)
    for perm, count in counter.most_common(10):
        print(f"      {count:3d}× {perm}")

    # Calculate confidence
    base_conf = len(matching) / len(approvals)
    print(f"\n   Base confidence: {base_conf:.3f} ({len(matching)}/{len(approvals)})")
    print(f"   Meets min_occurrences=3? {len(matching) >= 3}")
    print(f"   Meets confidence=0.7? {base_conf >= 0.7}")

# Test git pattern
print("\n\n🔍 Git read-only pattern:")
git_pattern = r"Bash\(git (status|log|diff|show|branch)"
git_matching = []

for approval in approvals:
    if re.search(git_pattern, approval.permission, re.IGNORECASE):
        git_matching.append(approval)

print(f"   Matches: {len(git_matching)}")
print(f"   Pattern: {git_pattern}")

if git_matching:
    counter = Counter(a.permission for a in git_matching)
    for perm, count in counter.most_common(10):
        print(f"      {count:3d}× {perm}")

    base_conf = len(git_matching) / len(approvals)
    print(f"\n   Base confidence: {base_conf:.3f} ({len(git_matching)}/{len(approvals)})")
    print(f"   Meets min_occurrences=3? {len(git_matching) >= 3}")
    print(f"   Meets confidence=0.7? {base_conf >= 0.7}")
