#!/usr/bin/env python3
"""Direct test of permission pattern detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.permission_pattern_detector import PermissionPatternDetector

print("🔍 Testing Permission Pattern Detection\n")

# Initialize
tracker = ApprovalTracker()
detector = PermissionPatternDetector(
    approval_tracker=tracker,
    min_occurrences=3,
    confidence_threshold=0.7
)

# Get approval stats
approvals = tracker.get_recent_approvals(days=30)
print(f"📊 Found {len(approvals)} approvals in last 30 days")

# Get unique permissions
unique = tracker.get_all_unique_permissions(days=30)
print(f"🔑 {len(unique)} unique permission patterns\n")

# Top 10
from collections import Counter
counter = Counter(a.permission for a in approvals)
print("📈 Top 10 permissions:")
for perm, count in counter.most_common(10):
    print(f"   {count:3d}× {perm}")

# Detect patterns
print("\n🧠 Detecting patterns (min_occurrences=3, confidence=0.7)...")
patterns = detector.detect_patterns(days=30)

if patterns:
    print(f"\n✅ Found {len(patterns)} auto-approval candidates:\n")
    for p in patterns[:5]:
        print(f"   • {p.description}")
        print(f"     Confidence: {p.pattern.confidence:.1%}")
        print(f"     Examples: {p.approved_examples[:2]}")
        print()
else:
    print("\n❌ No patterns detected - checking thresholds...")
    print(f"   Current thresholds: min={detector.min_occurrences}, conf={detector.confidence_threshold}")
