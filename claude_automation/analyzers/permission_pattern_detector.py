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

    Uses tiered detection approach:
    - TIER 1 (SAFE): Fast learning for read-only tools (2 occurrences, 7 days)
    - TIER 2 (MODERATE): Normal learning for dev tools (3 occurrences, 14 days)
    - TIER 3 (RISKY): Conservative learning for write operations (5 occurrences, 30 days)

    Algorithms:
    1. Frequency counting (occurrences >= threshold per tier)
    2. Pattern categorization (git, pytest, file ops, etc.)
    3. Confidence scoring (occurrences / total * context_bonus)
    """

    # Pattern categories and their detection rules
    PATTERN_CATEGORIES = {
        "git_read_only": {
            "patterns": [r"Bash\(git (status|log|diff|show|branch)"],
            "description": "Read-only git commands",
            "tier": "TIER_1_SAFE",
        },
        "git_all_safe": {
            "patterns": [
                r"Bash\(git (status|log|diff|show|branch|add|commit|push|pull)"
            ],
            "description": "All safe git commands (no force operations)",
            "tier": "TIER_3_RISKY",
        },
        "pytest": {
            "patterns": [r"Bash\(pytest", r"Bash\(python -m pytest"],
            "description": "Pytest test execution",
            "tier": "TIER_1_SAFE",
        },
        "ruff": {
            "patterns": [r"Bash\(ruff"],
            "description": "Ruff linter/formatter",
            "tier": "TIER_1_SAFE",
        },
        "modern_cli": {
            "patterns": [
                r"Bash\((fd|eza|bat|rg|dust|procs|btm|cat|tree|ls)",
            ],
            "description": "Modern CLI tools (fd, eza, bat, cat, etc.)",
            "tier": "TIER_1_SAFE",
        },
        "file_operations": {
            "patterns": [
                r"Read\([^)]+\)",
                r"Glob\([^)]+\)",
            ],
            "description": "File read operations",
            "tier": "TIER_1_SAFE",
        },
        "file_write_operations": {
            "patterns": [
                r"Write\([^)]+\)",
                r"Edit\([^)]+\)",
            ],
            "description": "File write/edit operations",
            "tier": "TIER_2_MODERATE",
        },
        "test_execution": {
            "patterns": [
                r"Bash\(.*test",
                r"Bash\(npm test",
                r"Bash\(cargo test",
            ],
            "description": "Test execution commands",
            "tier": "TIER_2_MODERATE",
        },
        "project_full_access": {
            "patterns": [
                r"Read\(/home/[^/]+/[^/]+/\*\*\)",
            ],
            "description": "Full project directory access",
            "tier": "TIER_3_RISKY",
        },
    }

    # Tiered detection configuration
    TIER_CONFIG = {
        "TIER_1_SAFE": {
            "min_occurrences": 2,
            "time_window_days": 7,
            "confidence_threshold": 0.5,
            "description": "Safe read-only tools",
        },
        "TIER_2_MODERATE": {
            "min_occurrences": 3,
            "time_window_days": 14,
            "confidence_threshold": 0.7,
            "description": "Development and testing tools",
        },
        "TIER_3_RISKY": {
            "min_occurrences": 5,
            "time_window_days": 30,
            "confidence_threshold": 0.8,
            "description": "Write operations and risky commands",
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
        Detect patterns in approval history using tiered approach.

        Args:
            days: Maximum days of history to analyze (overridden by tier configs)
            project_path: Optional project filter

        Returns:
            List of pattern suggestions, sorted by confidence (high to low)
        """
        logger.info("Starting tiered pattern detection")
        detected_patterns = []

        # Process each tier separately
        for tier_name, tier_config in self.TIER_CONFIG.items():
            tier_days = tier_config["time_window_days"]
            tier_min_occurrences = tier_config["min_occurrences"]
            tier_threshold = tier_config["confidence_threshold"]

            logger.debug(
                f"Processing {tier_name}: {tier_min_occurrences} occurrences in {tier_days} days"
            )

            # Get approvals for this tier's time window
            approvals = self.tracker.get_recent_approvals(
                days=tier_days, project_path=project_path
            )

            if not approvals:
                logger.debug(f"No approvals in last {tier_days} days for {tier_name}")
                continue

            # Detect patterns for categories in this tier
            for category, rules in self.PATTERN_CATEGORIES.items():
                if rules.get("tier") != tier_name:
                    continue  # Skip categories not in this tier

                pattern = self._detect_category_pattern(
                    category, rules, approvals, tier_days, tier_min_occurrences
                )
                if pattern and pattern.confidence >= tier_threshold:
                    detected_patterns.append(pattern)
                    logger.info(
                        f"✓ Detected {category} pattern "
                        f"({pattern.occurrences} times, {pattern.confidence:.0%} confidence)"
                    )

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
        min_occurrences: int | None = None,
    ) -> PermissionPattern | None:
        """
        Detect a specific category pattern.

        Args:
            category: Pattern category name
            rules: Category detection rules
            approvals: Approval history
            days: Time window
            min_occurrences: Minimum occurrences (uses self.min_occurrences if None)

        Returns:
            PermissionPattern if detected, None otherwise
        """
        # Use tier-specific min_occurrences or fall back to default
        min_occ = min_occurrences if min_occurrences is not None else self.min_occurrences

        # Find matching approvals
        matching_approvals = []
        patterns_regex = rules["patterns"]

        for approval in approvals:
            for pattern_regex in patterns_regex:
                if re.search(pattern_regex, approval.permission, re.IGNORECASE):
                    matching_approvals.append(approval)
                    break

        # Check if meets minimum occurrences
        if len(matching_approvals) < min_occ:
            return None

        # Calculate confidence based on pattern RELIABILITY, not category share
        # The old formula (occurrences/total) was broken - a pattern used 100 times
        # out of 800 total would only get 12.5% confidence, failing 50% threshold.
        # New formula measures: Is this pattern consistently approved across
        # sessions and projects? If so, it's reliable and should be auto-approved.
        final_confidence = self._calculate_pattern_confidence(
            matching_approvals, approvals
        )

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

    def _calculate_pattern_confidence(
        self,
        matching_approvals: list[PermissionApprovalEntry],
        all_approvals: list[PermissionApprovalEntry],
    ) -> float:
        """
        Calculate confidence based on pattern RELIABILITY, not category share.

        The key insight: once minimum_occurrences threshold is met, confidence
        should measure "how reliable is this pattern as a predictor of user
        approval", not "what percentage of all activity is this category".

        Factors:
        - Base: 0.5 (pattern exists with enough occurrences - already gated)
        - Session spread: +0.25 (appears across multiple sessions = not a fluke)
        - Project spread: +0.15 (appears across projects = generalizable)
        - Consistency: +0.05 (same permission strings = predictable)
        - Recency: +0.05 (used recently = still relevant)

        Max possible: 1.0
        Typical well-established pattern: 0.7-0.95

        Args:
            matching_approvals: Approvals matching this pattern
            all_approvals: All approvals for context

        Returns:
            Confidence score (0.0-1.0)
        """
        if not matching_approvals:
            return 0.0

        n = len(matching_approvals)

        # Base confidence: pattern exists with enough occurrences
        # The min_occurrences threshold already ensures we have enough data
        base = 0.5

        # Session spread bonus (up to +0.25)
        # More sessions = more confident this is a real pattern, not a fluke
        unique_sessions = len({a.session_id for a in matching_approvals})
        # Cap at 10 sessions for max bonus
        session_bonus = min(0.25, (unique_sessions / 10) * 0.25)

        # Project spread bonus (up to +0.15)
        # Cross-project patterns are more generalizable and reliable
        unique_projects = len({a.project_path for a in matching_approvals})
        # Cap at 5 projects for max bonus
        project_bonus = min(0.15, (unique_projects / 5) * 0.15)

        # Consistency bonus (up to +0.05)
        # Same exact permission string appearing multiple times = predictable
        permission_counts = Counter(a.permission for a in matching_approvals)
        most_common_count = max(permission_counts.values())
        # Higher ratio of most common permission = more consistent
        consistency_ratio = most_common_count / n
        consistency_bonus = consistency_ratio * 0.05

        # Recency bonus (+0.05 if pattern was used recently)
        # Check if any matching permission appears in the 20 most recent approvals
        recent_permissions = {a.permission for a in all_approvals[:20]}
        matching_permissions = {a.permission for a in matching_approvals}
        recency_bonus = 0.05 if recent_permissions & matching_permissions else 0.0

        confidence = base + session_bonus + project_bonus + consistency_bonus + recency_bonus
        return min(1.0, confidence)

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
