#!/bin/bash
cd /home/guyfawkes/claude-nixos-automation
devenv shell python3 << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.permission_pattern_detector import PermissionPatternDetector

tracker = ApprovalTracker()
detector = PermissionPatternDetector(tracker, min_occurrences=3, confidence_threshold=0.03)

patterns = detector.detect_patterns(days=30)
print(f'\n🎉 Found {len(patterns)} patterns with confidence >= 3%!\n')

for p in patterns[:5]:
    print(f'   • {p.description}')
    print(f'     Confidence: {p.pattern.confidence:.1%}, Occurrences: {p.pattern.occurrences}')
    print()
PYEOF
