"""
PermissionPatternDetector - Detects patterns in permission approvals.

Uses frequency analysis and categorization to identify generalizable patterns
that can reduce future permission prompts.
"""

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from ..schemas import (
    PatternSuggestion,
    PermissionApprovalEntry,
    PermissionPattern,
)
from .approval_tracker import ApprovalTracker
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class PermissionPatternDetector(BaseAnalyzer):
    """
    Detects patterns in permission approval history.

    Uses algorithms:
    1. Frequency counting (occurrences >= threshold)
    2. Pattern categorization (git, pytest, file ops, etc.)
    3. Confidence scoring (occurrences / total * context_bonus)
    """

    # Pattern categories and their detection rules
    PATTERN_CATEGORIES = {
        "git_read_only": {
            "patterns": [r"Bash\(git (status|log|diff|show|branch)"],
            "description": "Read-only git commands",
        },
        "git_all_safe": {
            "patterns": [
                r"Bash\(git (status|log|diff|show|branch|add|commit|push|pull)"
            ],
            "description": "All safe git commands (no force operations)",
        },
        "pytest": {
            "patterns": [r"Bash\(pytest", r"Bash\(python -m pytest"],
            "description": "Pytest test execution",
        },
        "ruff": {
            "patterns": [r"Bash\(ruff"],
            "description": "Ruff linter/formatter",
        },
        "modern_cli": {
            "patterns": [
                r"Bash\((fd|eza|bat|rg|dust|procs|btm)",
            ],
            "description": "Modern CLI tools (fd, eza, bat, etc.)",
        },
        "file_operations": {
            "patterns": [
                r"Read\([^)]+\)",
                r"Write\([^)]+\)",
                r"Edit\([^)]+\)",
                r"Glob\([^)]+\)",
            ],
            "description": "File read/write/edit operations",
        },
        "test_execution": {
            "patterns": [
                r"Bash\(.*test",
                r"Bash\(npm test",
                r"Bash\(cargo test",
            ],
            "description": "Test execution commands",
        },
        "project_full_access": {
            "patterns": [
                r"Read\(/home/[^/]+/[^/]+/\*\*\)",
            ],
            "description": "Full project directory access",
        },
    }

    def __init__(
        self,
        approval_tracker: ApprovalTracker | None = None,
        min_occurrences: int = 3,
        confidence_threshold: float = 0.7,
    ):
        """
        Initialize pattern detector.

        Args:
            approval_tracker: ApprovalTracker instance (creates new if None)
            min_occurrences: Minimum occurrences for pattern detection
            confidence_threshold: Minimum confidence for suggestions (0-1)
        """
        super().__init__()
        self.tracker = approval_tracker or ApprovalTracker()
        self.min_occurrences = min_occurrences
        self.confidence_threshold = confidence_threshold

    def _get_analysis_method_name(self) -> str:
        """Return the name of the primary analysis method."""
        return "detect_patterns"

    def detect_patterns(
        self, days: int = 30, project_path: str | None = None
    ) -> list[PatternSuggestion]:
        """
        Detect patterns in approval history.

        Args:
            days: Days of history to analyze
            project_path: Optional project filter

        Returns:
            List of pattern suggestions, sorted by confidence (high to low)
        """
        # Get recent approvals
        approvals = self.tracker.get_recent_approvals(days=days, project_path=project_path)

        if not approvals:
            logger.info("No approvals found for pattern detection")
            return []

        # Detect patterns by category
        detected_patterns = []

        for category, rules in self.PATTERN_CATEGORIES.items():
            pattern = self._detect_category_pattern(
                category, rules, approvals, days
            )
            if pattern:
                detected_patterns.append(pattern)

        # Filter out previously rejected permission patterns
        from .rejection_tracker import RejectionTracker
        tracker = RejectionTracker()
        rejections = tracker.get_recent_rejections(days=90, suggestion_type='permission')
        rejected_fingerprints = {r.suggestion_fingerprint for r in rejections}

        # Filter detected patterns
        detected_patterns = [
            p for p in detected_patterns
            if p.pattern_type not in rejected_fingerprints
        ]

        if not detected_patterns:
            logger.info("All permission patterns were previously rejected")
            return []

        # Create suggestions from patterns
        suggestions = []
        for pattern in detected_patterns:
            if pattern.confidence >= self.confidence_threshold:
                suggestion = self._create_suggestion(pattern, approvals)
                suggestions.append(suggestion)

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda s: s.pattern.confidence, reverse=True)

        return suggestions

    def _detect_category_pattern(
        self,
        category: str,
        rules: dict[str, Any],
        approvals: list[PermissionApprovalEntry],
        days: int,
    ) -> PermissionPattern | None:
        """
        Detect a specific category pattern.

        Args:
            category: Pattern category name
            rules: Category detection rules
            approvals: Approval history
            days: Time window

        Returns:
            PermissionPattern if detected, None otherwise
        """
        # Find matching approvals
        matching_approvals = []
        patterns_regex = rules["patterns"]

        for approval in approvals:
            for pattern_regex in patterns_regex:
                if re.search(pattern_regex, approval.permission, re.IGNORECASE):
                    matching_approvals.append(approval)
                    break

        # Check if meets minimum occurrences
        if len(matching_approvals) < self.min_occurrences:
            return None

        # Calculate confidence
        # Base confidence: occurrences / total approvals
        base_confidence = len(matching_approvals) / len(approvals)

        # Boost for consistency (same permission string repeated)
        permission_counts = Counter(a.permission for a in matching_approvals)
        max_repeats = max(permission_counts.values())
        consistency_bonus = min(0.2, max_repeats / len(matching_approvals) * 0.2)

        # Boost for recency (more recent = higher confidence)
        recency_bonus = 0.1 if matching_approvals[0] in approvals[:5] else 0.0

        final_confidence = min(1.0, base_confidence + consistency_bonus + recency_bonus)

        # Collect examples
        examples = list({a.permission for a in matching_approvals[:5]})

        return PermissionPattern(
            pattern_type=category,
            occurrences=len(matching_approvals),
            confidence=final_confidence,
            examples=examples,
            detected_at=datetime.now(),
            time_window_days=days,
        )

    def _create_suggestion(
        self, pattern: PermissionPattern, all_approvals: list[PermissionApprovalEntry]
    ) -> PatternSuggestion:
        """
        Create a pattern suggestion from detected pattern.

        Args:
            pattern: Detected pattern
            all_approvals: All approvals for context

        Returns:
            PatternSuggestion with details
        """
        # Get category rules
        rules = self.PATTERN_CATEGORIES.get(pattern.pattern_type, {})
        description = rules.get("description", pattern.pattern_type)

        # Create proposed rule (wildcard pattern)
        proposed_rule = self._generate_proposed_rule(pattern)

        # Examples of what would be allowed
        would_allow = pattern.examples[:3]

        # Examples that would still ask (edge cases)
        would_still_ask = self._get_edge_cases(pattern)

        # User's actual approvals
        approved_examples = pattern.examples

        # Impact estimate
        impact = self._estimate_impact(pattern, all_approvals)

        return PatternSuggestion(
            description=f"Allow {description}",
            pattern=pattern,
            proposed_rule=proposed_rule,
            would_allow=would_allow,
            would_still_ask=would_still_ask,
            approved_examples=approved_examples,
            impact_estimate=impact,
        )

    def _generate_proposed_rule(self, pattern: PermissionPattern) -> str:
        """
        Generate a proposed permission rule from pattern.

        Args:
            pattern: Detected pattern

        Returns:
            Wildcard permission rule string
        """
        # Map pattern types to permission rules
        rule_templates = {
            "git_read_only": "Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git branch:*)",
            "git_all_safe": "Bash(git *:*)",  # Excludes --force operations
            "pytest": "Bash(pytest:*), Bash(python -m pytest:*)",
            "ruff": "Bash(ruff:*)",
            "modern_cli": "Bash(fd:*), Bash(eza:*), Bash(bat:*), Bash(rg:*), Bash(dust:*), Bash(procs:*)",
            "file_operations": "Read(/**), Write(/**), Edit(/**), Glob(**)",
            "test_execution": "Bash(*test:*)",
            "project_full_access": "Read(/home/*/project/**), Write(/home/*/project/**)",
        }

        return rule_templates.get(pattern.pattern_type, pattern.pattern_type)

    def _get_edge_cases(self, pattern: PermissionPattern) -> list[str]:
        """
        Get edge cases that would still require approval.

        Args:
            pattern: Detected pattern

        Returns:
            List of edge case examples
        """
        edge_cases = {
            "git_all_safe": ["Bash(git push --force)", "Bash(git reset --hard)"],
            "file_operations": ["Write(/etc/passwd)", "Read(/home/other_user/.ssh)"],
            "project_full_access": ["Write(/home/user/.ssh/)", "Read(/etc/shadow)"],
        }

        return edge_cases.get(pattern.pattern_type, [])

    def _estimate_impact(
        self, pattern: PermissionPattern, all_approvals: list[PermissionApprovalEntry]
    ) -> str:
        """
        Estimate impact of applying this pattern.

        Args:
            pattern: Detected pattern
            all_approvals: All approvals for comparison

        Returns:
            Human-readable impact estimate
        """
        if not all_approvals:
            return "Unknown impact"

        # Calculate percentage of approvals this would auto-allow
        percentage = (pattern.occurrences / len(all_approvals)) * 100

        # Format impact message
        if percentage >= 50:
            return f"High impact: ~{percentage:.0f}% fewer prompts"
        elif percentage >= 25:
            return f"Medium impact: ~{percentage:.0f}% fewer prompts"
        else:
            return f"Low impact: ~{percentage:.0f}% fewer prompts"

    def get_pattern_stats(self, days: int = 30) -> dict[str, Any]:
        """
        Get statistics about detected patterns.

        Args:
            days: Days of history to analyze

        Returns:
            Dictionary with pattern statistics
        """
        approvals = self.tracker.get_recent_approvals(days=days)
        suggestions = self.detect_patterns(days=days)

        # Count approvals by category
        category_counts = defaultdict(int)
        for approval in approvals:
            for category, rules in self.PATTERN_CATEGORIES.items():
                for pattern_regex in rules["patterns"]:
                    if re.search(pattern_regex, approval.permission, re.IGNORECASE):
                        category_counts[category] += 1
                        break

        return {
            "total_approvals": len(approvals),
            "patterns_detected": len(suggestions),
            "patterns_above_threshold": sum(
                1 for s in suggestions if s.pattern.confidence >= self.confidence_threshold
            ),
            "category_counts": dict(category_counts),
            "high_confidence_patterns": [
                s.pattern.pattern_type
                for s in suggestions
                if s.pattern.confidence >= 0.8
            ],
        }
