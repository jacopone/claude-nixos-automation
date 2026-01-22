"""
PermissionPatternDetector - Detects patterns in permission approvals.

Uses frequency analysis and categorization to identify generalizable patterns
that can reduce future permission prompts.

Refactored: Static data moved to data/, detection logic split into patterns/
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..data import (
    CATEGORY_TO_TOOLS,
    PATTERN_CATEGORIES,
    TIER_CONFIG,
)
from ..data.pattern_categories import EDGE_CASES, RULE_TEMPLATES
from ..schemas import (
    PatternSuggestion,
    PermissionApprovalEntry,
    PermissionPattern,
)
from .approval_tracker import ApprovalTracker
from .base_analyzer import BaseAnalyzer
from .patterns import ConfidenceCalculator, CrossFolderDetector

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

        # Initialize sub-detectors
        self._confidence = ConfidenceCalculator()
        self._cross_folder = CrossFolderDetector(self._confidence)

    def _get_analysis_method_name(self) -> str:
        """Return the name of the primary analysis method."""
        return "detect_patterns"

    def _get_existing_patterns(self) -> set[str]:
        """
        Load existing allowed patterns from both global and local settings.

        Checks:
        1. ~/.claude/settings.json (global TIER_1_SAFE and cross-folder patterns)
        2. .claude/settings.local.json (per-project patterns)

        Returns:
            Set of patterns already in the allow lists.
        """
        existing = set()

        # Check GLOBAL settings first (~/.claude/settings.json)
        global_settings_file = Path.home() / ".claude" / "settings.json"
        if global_settings_file.exists():
            try:
                with open(global_settings_file, encoding="utf-8") as f:
                    settings = json.load(f)
                allow_list = settings.get("permissions", {}).get("allow", [])
                existing.update(allow_list)
                logger.debug(
                    f"Loaded {len(allow_list)} existing patterns from global settings.json"
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load global patterns: {e}")

        # Check LOCAL settings (.claude/settings.local.json)
        local_settings_file = Path.cwd() / ".claude" / "settings.local.json"
        if local_settings_file.exists():
            try:
                with open(local_settings_file, encoding="utf-8") as f:
                    settings = json.load(f)
                allow_list = settings.get("permissions", {}).get("allow", [])
                existing.update(allow_list)
                logger.debug(
                    f"Loaded {len(allow_list)} existing patterns from settings.local.json"
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load local patterns: {e}")

        logger.debug(f"Total existing patterns: {len(existing)}")
        return existing

    def _pattern_already_approved(
        self, pattern: PermissionPattern, existing_patterns: set[str]
    ) -> bool:
        """Check if a detected pattern is already covered by existing patterns."""
        for example in pattern.examples:
            if example in existing_patterns:
                return True
            for existing in existing_patterns:
                if existing.endswith("**)") or existing.endswith(":*)"):
                    prefix = existing.replace("**)", "").replace(":*)", "")
                    if example.startswith(prefix):
                        return True
        return False

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

        existing_patterns = self._get_existing_patterns()
        skipped_categories = set()

        # Process each tier separately
        for tier_name, tier_config in TIER_CONFIG.items():
            tier_days = tier_config["time_window_days"]
            tier_min_occurrences = tier_config["min_occurrences"]
            tier_threshold = tier_config["confidence_threshold"]

            logger.debug(
                f"Processing {tier_name}: {tier_min_occurrences} occurrences in {tier_days} days"
            )

            approvals = self.tracker.get_recent_approvals(
                days=tier_days, project_path=project_path
            )

            if not approvals:
                logger.debug(f"No approvals in last {tier_days} days for {tier_name}")
                continue

            # Detect patterns for categories in this tier
            for category, rules in PATTERN_CATEGORIES.items():
                if rules.get("tier") != tier_name:
                    continue

                if self._is_category_covered_by_wildcards(category, existing_patterns):
                    if category not in skipped_categories:
                        logger.debug(f"Skipping {category} (already covered)")
                        skipped_categories.add(category)
                    continue

                pattern = self._detect_category_pattern(
                    category, rules, approvals, tier_days, tier_min_occurrences
                )
                if pattern and pattern.confidence >= tier_threshold:
                    detected_patterns.append(pattern)
                    logger.info(
                        f"Detected {category} pattern "
                        f"({pattern.occurrences} times, {pattern.confidence:.0%} confidence)"
                    )

        if skipped_categories:
            logger.info(f"Skipped {len(skipped_categories)} categories (already covered)")

        # Filter rejected patterns
        from .rejection_tracker import RejectionTracker

        tracker = RejectionTracker()
        rejections = tracker.get_recent_rejections(days=90, suggestion_type="permission")
        rejected_fingerprints = {r.suggestion_fingerprint for r in rejections}
        detected_patterns = [
            p for p in detected_patterns if p.pattern_type not in rejected_fingerprints
        ]

        # Filter already approved
        if existing_patterns:
            original_count = len(detected_patterns)
            detected_patterns = [
                p
                for p in detected_patterns
                if not self._pattern_already_approved(p, existing_patterns)
            ]
            filtered = original_count - len(detected_patterns)
            if filtered > 0:
                logger.info(f"Filtered {filtered} patterns (already approved)")

        # Create suggestions from category patterns
        approvals = self.tracker.get_recent_approvals(days=days, project_path=project_path)
        suggestions = [
            self._create_suggestion(pattern, approvals)
            for pattern in detected_patterns
            if pattern.confidence >= self.confidence_threshold
        ]

        # Add cross-folder tool suggestions
        cross_folder_suggestions = self._cross_folder.detect(
            approvals, existing_patterns, days
        )
        suggestions.extend(cross_folder_suggestions)

        if not suggestions:
            logger.info("All patterns were rejected or already approved")
            return []

        suggestions.sort(key=lambda s: s.pattern.confidence, reverse=True)
        return suggestions

    def _is_category_covered_by_wildcards(
        self, category: str, existing_patterns: set[str]
    ) -> bool:
        """Check if a category is already fully covered by existing wildcards."""
        tools = CATEGORY_TO_TOOLS.get(category, [])
        if not tools:
            return False

        for tool in tools:
            if not (
                f"Bash({tool}:*)" in existing_patterns
                or f"Bash({tool} *)" in existing_patterns
            ):
                return False
        return True

    def _detect_category_pattern(
        self,
        category: str,
        rules: dict[str, Any],
        approvals: list[PermissionApprovalEntry],
        days: int,
        min_occurrences: int | None = None,
    ) -> PermissionPattern | None:
        """Detect a specific category pattern."""
        min_occ = min_occurrences if min_occurrences is not None else self.min_occurrences

        matching_approvals = []
        patterns_regex = rules["patterns"]

        for approval in approvals:
            for pattern_regex in patterns_regex:
                if re.search(pattern_regex, approval.permission, re.IGNORECASE):
                    matching_approvals.append(approval)
                    break

        if len(matching_approvals) < min_occ:
            return None

        final_confidence = self._confidence.calculate(matching_approvals, approvals)
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
        """Create a pattern suggestion from detected pattern."""
        rules = PATTERN_CATEGORIES.get(pattern.pattern_type, {})
        description = rules.get("description", pattern.pattern_type)
        tier = rules.get("tier", "TIER_2_MODERATE")

        if pattern.pattern_type.startswith("CrossFolder_"):
            tier = "CROSS_FOLDER"

        proposed_rule = RULE_TEMPLATES.get(pattern.pattern_type, "")
        if not proposed_rule:
            logger.error(f"No rule template for: {pattern.pattern_type}")

        would_allow = pattern.examples[:3]
        would_still_ask = EDGE_CASES.get(pattern.pattern_type, [])
        impact = self._estimate_impact(pattern, all_approvals)

        return PatternSuggestion(
            description=f"Allow {description}",
            pattern=pattern,
            proposed_rule=proposed_rule,
            would_allow=would_allow,
            would_still_ask=would_still_ask,
            approved_examples=pattern.examples,
            impact_estimate=impact,
            tier=tier,
        )

    def _estimate_impact(
        self, pattern: PermissionPattern, all_approvals: list[PermissionApprovalEntry]
    ) -> str:
        """Estimate impact of applying this pattern."""
        if not all_approvals:
            return "Unknown impact"

        percentage = (pattern.occurrences / len(all_approvals)) * 100

        if percentage >= 50:
            return f"High impact: ~{percentage:.0f}% fewer prompts"
        elif percentage >= 25:
            return f"Medium impact: ~{percentage:.0f}% fewer prompts"
        else:
            return f"Low impact: ~{percentage:.0f}% fewer prompts"

    def get_pattern_stats(self, days: int = 30) -> dict[str, Any]:
        """Get statistics about detected patterns."""
        approvals = self.tracker.get_recent_approvals(days=days)
        suggestions = self.detect_patterns(days=days)

        from collections import defaultdict

        category_counts = defaultdict(int)
        for approval in approvals:
            for category, rules in PATTERN_CATEGORIES.items():
                for pattern_regex in rules["patterns"]:
                    if re.search(pattern_regex, approval.permission, re.IGNORECASE):
                        category_counts[category] += 1
                        break

        return {
            "total_approvals": len(approvals),
            "patterns_detected": len(suggestions),
            "patterns_above_threshold": sum(
                1
                for s in suggestions
                if s.pattern.confidence >= self.confidence_threshold
            ),
            "category_counts": dict(category_counts),
            "high_confidence_patterns": [
                s.pattern.pattern_type
                for s in suggestions
                if s.pattern.confidence >= 0.8
            ],
        }

    def categorize_by_tier(
        self, suggestions: list[PatternSuggestion]
    ) -> dict[str, list[PatternSuggestion]]:
        """Categorize pattern suggestions by their tier."""
        categorized: dict[str, list[PatternSuggestion]] = {
            "TIER_1_SAFE": [],
            "TIER_2_MODERATE": [],
            "TIER_3_RISKY": [],
            "CROSS_FOLDER": [],
        }

        for suggestion in suggestions:
            tier = suggestion.tier
            if tier in categorized:
                categorized[tier].append(suggestion)
            else:
                logger.warning(f"Unknown tier '{tier}', defaulting to TIER_2_MODERATE")
                categorized["TIER_2_MODERATE"].append(suggestion)

        for tier, items in categorized.items():
            if items:
                logger.info(f"  {tier}: {len(items)} suggestions")

        return categorized

    def get_global_suggestions(
        self, suggestions: list[PatternSuggestion] | None = None, days: int = 30
    ) -> list[PatternSuggestion]:
        """Get suggestions that should be applied globally."""
        if suggestions is None:
            suggestions = self.detect_patterns(days=days)

        categorized = self.categorize_by_tier(suggestions)
        return categorized["TIER_1_SAFE"] + categorized["CROSS_FOLDER"]

    def get_project_suggestions(
        self, suggestions: list[PatternSuggestion] | None = None, days: int = 30
    ) -> list[PatternSuggestion]:
        """Get suggestions that should be applied per-project."""
        if suggestions is None:
            suggestions = self.detect_patterns(days=days)

        categorized = self.categorize_by_tier(suggestions)
        return categorized["TIER_2_MODERATE"] + categorized["TIER_3_RISKY"]
