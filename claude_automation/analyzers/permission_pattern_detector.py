"""
PermissionPatternDetector - Detects patterns in permission approvals.

Uses frequency analysis and categorization to identify generalizable patterns
that can reduce future permission prompts.
"""

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
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
    # Updated 2025-12: Added 12 new categories based on approval data analysis
    # NOTE: Pattern category keys MUST start with uppercase to pass Claude Code validation
    # Claude Code error: "Tool names must start with uppercase"
    PATTERN_CATEGORIES = {
        # === Git Operations ===
        "Git_read_only": {
            "patterns": [r"Bash\(git (status|log|diff|show|branch)"],
            "description": "Read-only git commands",
            "tier": "TIER_1_SAFE",
        },
        "Git_workflow": {
            "patterns": [
                r"Bash\(git (status|log|diff|show|branch|add|commit|push|pull|fetch|stash|checkout|merge|rebase|restore|reset(?! --hard))"
            ],
            "description": "Standard git workflow commands (excludes force/hard operations)",
            "tier": "TIER_2_MODERATE",  # Changed from TIER_3_RISKY - these are routine
        },
        "Git_destructive": {
            "patterns": [
                r"Bash\(git.*(--force|--hard|push -f|push --force|reset --hard)",
            ],
            "description": "Destructive git operations (force push, hard reset)",
            "tier": "TIER_3_RISKY",
        },
        # === Development Tools ===
        "Pytest": {
            "patterns": [r"Bash\(pytest", r"Bash\(python -m pytest"],
            "description": "Pytest test execution",
            "tier": "TIER_1_SAFE",
        },
        "Ruff": {
            "patterns": [r"Bash\(ruff"],
            "description": "Ruff linter/formatter",
            "tier": "TIER_1_SAFE",
        },
        "Modern_cli": {
            "patterns": [
                r"Bash\((fd|eza|bat|rg|dust|procs|btm|tree)",
            ],
            "description": "Modern CLI tools (fd, eza, bat, rg, etc.)",
            "tier": "TIER_1_SAFE",
        },
        # === File Operations ===
        "File_operations": {
            "patterns": [
                r"Read\([^)]+\)",
                r"Glob\([^)]+\)",
            ],
            "description": "File read operations",
            "tier": "TIER_1_SAFE",
        },
        "File_write_operations": {
            "patterns": [
                r"Write\([^)]+\)",
                r"Edit\([^)]+\)",
            ],
            "description": "File write/edit operations",
            "tier": "TIER_2_MODERATE",
        },
        "Test_execution": {
            "patterns": [
                r"Bash\(.*test",
                r"Bash\(npm test",
                r"Bash\(cargo test",
            ],
            "description": "Test execution commands",
            "tier": "TIER_2_MODERATE",
        },
        "Project_full_access": {
            "patterns": [
                r"Read\(/home/[^/]+/[^/]+/\*\*\)",
            ],
            "description": "Full project directory access",
            "tier": "TIER_3_RISKY",
        },
        # === GitHub CLI (gh) ===
        "Github_cli": {
            "patterns": [r"Bash\(gh[\s:]"],
            "description": "GitHub CLI commands (gh pr, gh issue, gh api, etc.)",
            "tier": "TIER_2_MODERATE",
        },
        # === Cloud CLIs ===
        "Cloud_cli": {
            "patterns": [r"Bash\((gcloud|aws|az)[\s:]"],
            "description": "Cloud provider CLIs (GCP, AWS, Azure)",
            "tier": "TIER_3_RISKY",  # Can modify cloud resources
        },
        # === Package Managers ===
        "Package_managers": {
            "patterns": [r"Bash\((npm|npx|yarn|pnpm|pip|uv|cargo|poetry)[\s:]"],
            "description": "Package manager commands",
            "tier": "TIER_2_MODERATE",
        },
        # === Nix Ecosystem ===
        "Nix_tools": {
            "patterns": [r"Bash\((nix|devenv|nix-shell|nix-build|nix-env)[\s:]"],
            "description": "Nix/NixOS ecosystem tools",
            "tier": "TIER_2_MODERATE",
        },
        # === Database CLIs ===
        "Database_cli": {
            "patterns": [r"Bash\((sqlite3|psql|mysql|mycli|pgcli|usql)[\s:]"],
            "description": "Database CLI tools",
            "tier": "TIER_2_MODERATE",
        },
        # === Network/HTTP Tools ===
        "Network_tools": {
            "patterns": [r"Bash\((curl|wget|xh|httpie)[\s:]"],
            "description": "Network/HTTP client tools",
            "tier": "TIER_2_MODERATE",
        },
        # === Runtime Interpreters ===
        "Runtime_tools": {
            "patterns": [r"Bash\((python3?|node|ruby|go run)[\s:]"],
            "description": "Language runtime interpreters",
            "tier": "TIER_2_MODERATE",
        },
        # === POSIX Filesystem ===
        "Posix_filesystem": {
            "patterns": [r"Bash\((find|ls|mkdir|rmdir|touch|mv|cp|rm(?! -rf))[\s:]"],
            "description": "POSIX filesystem commands (find, ls, mkdir, etc.)",
            "tier": "TIER_2_MODERATE",
        },
        # === POSIX Search/Transform ===
        "Posix_search": {
            "patterns": [r"Bash\((grep|awk|sed|cut|sort|uniq)[\s:]"],
            "description": "POSIX search/transform commands",
            "tier": "TIER_2_MODERATE",
        },
        # === POSIX Read ===
        "Posix_read": {
            "patterns": [r"Bash\((cat|head|tail|less|more|wc)[\s:]"],
            "description": "POSIX file reading/stats commands",
            "tier": "TIER_1_SAFE",
        },
        # === Shell Utilities ===
        "Shell_utilities": {
            "patterns": [r"Bash\((echo|printf|sleep|true|false|which|type|cd|pwd)[\s:]"],
            "description": "Shell built-ins and utilities",
            "tier": "TIER_1_SAFE",
        },
        # === Dangerous Operations ===
        "Dangerous_operations": {
            "patterns": [r"Bash\((rm -rf|sudo|chmod 777)[\s:]"],
            "description": "Potentially dangerous operations",
            "tier": "TIER_3_RISKY",
        },
    }

    # Tiered detection configuration
    # NOTE: Boris-style permissive thresholds (2026-01 tuning)
    # Philosophy: If you approve a tool multiple times across different contexts,
    # it means you trust that tool - generalize to tool:* pattern
    # - TIER_1: 1 approval (safe read-only tools - just prove it's used)
    # - TIER_2: 2 approvals (dev tools - light validation)
    # - TIER_3: 3 approvals (risky operations - still reasonable)
    TIER_CONFIG = {
        "TIER_1_SAFE": {
            "min_occurrences": 1,  # Single use proves utility
            "time_window_days": 14,  # Extended window
            "confidence_threshold": 0.3,  # Low bar for safe tools
            "description": "Safe read-only tools",
        },
        "TIER_2_MODERATE": {
            "min_occurrences": 2,  # Just 2 approvals needed
            "time_window_days": 21,  # 3 weeks
            "confidence_threshold": 0.4,  # Lowered from 0.6
            "description": "Development and testing tools",
        },
        "TIER_3_RISKY": {
            "min_occurrences": 3,  # 3 approvals (was 5)
            "time_window_days": 30,
            "confidence_threshold": 0.5,  # Lowered from 0.7
            "description": "Write operations and risky commands",
        },
    }

    # Cross-folder generalization config
    # If a tool is approved in N different folders, generalize to tool:*
    CROSS_FOLDER_CONFIG = {
        "min_unique_folders": 2,  # 2+ folders triggers generalization
        "min_total_approvals": 3,  # At least 3 total approvals
        "confidence_boost": 0.3,  # Extra confidence for cross-folder patterns
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

    def _get_existing_patterns(self) -> set[str]:
        """
        Load existing allowed patterns from settings.local.json.

        Returns:
            Set of patterns already in the allow list.
        """
        existing = set()
        settings_file = Path.cwd() / ".claude" / "settings.local.json"

        if settings_file.exists():
            try:
                with open(settings_file, encoding="utf-8") as f:
                    settings = json.load(f)
                allow_list = settings.get("permissions", {}).get("allow", [])
                existing = set(allow_list)
                logger.debug(
                    f"Loaded {len(existing)} existing patterns from settings.local.json"
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load existing patterns: {e}")

        return existing

    def _pattern_already_approved(
        self, pattern: "PermissionPattern", existing_patterns: set[str]
    ) -> bool:
        """
        Check if a detected pattern is already covered by existing patterns.

        Args:
            pattern: The detected pattern to check
            existing_patterns: Set of patterns from settings.local.json

        Returns:
            True if pattern is already approved (should be skipped)
        """
        # Check if any example from this pattern matches existing patterns
        # Note: PermissionPattern has 'examples', not 'approved_examples'
        for example in pattern.examples:
            # Direct match
            if example in existing_patterns:
                return True
            # Check if covered by wildcard patterns
            for existing in existing_patterns:
                if existing.endswith("**)") or existing.endswith(":*)"):
                    # Wildcard pattern - check if it covers our example
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

        # BORIS-STYLE: Load existing patterns ONCE and skip covered categories
        existing_patterns = self._get_existing_patterns()
        skipped_categories = set()

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

                # BORIS-STYLE: Skip categories already covered by wildcards
                if self._is_category_covered_by_wildcards(category, existing_patterns):
                    if category not in skipped_categories:
                        logger.debug(f"⏭ Skipping {category} (already covered by wildcards)")
                        skipped_categories.add(category)
                    continue

                pattern = self._detect_category_pattern(
                    category, rules, approvals, tier_days, tier_min_occurrences
                )
                if pattern and pattern.confidence >= tier_threshold:
                    detected_patterns.append(pattern)
                    logger.info(
                        f"✓ Detected {category} pattern "
                        f"({pattern.occurrences} times, {pattern.confidence:.0%} confidence)"
                    )

        if skipped_categories:
            logger.info(f"Skipped {len(skipped_categories)} categories (already covered by wildcards)")

        # Filter out previously rejected permission patterns
        from .rejection_tracker import RejectionTracker

        tracker = RejectionTracker()
        rejections = tracker.get_recent_rejections(
            days=90, suggestion_type="permission"
        )
        rejected_fingerprints = {r.suggestion_fingerprint for r in rejections}

        # Filter detected patterns (rejected)
        detected_patterns = [
            p for p in detected_patterns if p.pattern_type not in rejected_fingerprints
        ]

        # Filter out patterns already approved in settings.local.json
        existing_patterns = self._get_existing_patterns()
        if existing_patterns:
            original_count = len(detected_patterns)
            detected_patterns = [
                p
                for p in detected_patterns
                if not self._pattern_already_approved(p, existing_patterns)
            ]
            filtered_count = original_count - len(detected_patterns)
            if filtered_count > 0:
                logger.info(
                    f"Filtered {filtered_count} patterns (already in settings.local.json)"
                )

        # Create suggestions from category patterns
        suggestions = []
        for pattern in detected_patterns:
            if pattern.confidence >= self.confidence_threshold:
                suggestion = self._create_suggestion(pattern, approvals)
                suggestions.append(suggestion)

        # BORIS-STYLE: Also detect cross-folder tool patterns
        # This catches tools that don't fit predefined categories but are
        # clearly trusted (used across multiple projects/folders)
        cross_folder_suggestions = self.detect_cross_folder_tools(days=days)
        suggestions.extend(cross_folder_suggestions)

        if not suggestions:
            logger.info(
                "All permission patterns were previously rejected or already approved"
            )
            return []

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda s: s.pattern.confidence, reverse=True)

        return suggestions

    def detect_cross_folder_tools(
        self, days: int = 30
    ) -> list[PatternSuggestion]:
        """
        Detect tools used across multiple folders and generate tool:* wildcards.

        Boris-style philosophy: If you approve `curl` in folder A, folder B, and
        folder C, you clearly trust curl - generalize to `Bash(curl:*)`.

        This is SEPARATE from category-based detection and catches tools that
        don't fit neatly into predefined categories.

        Args:
            days: Days of history to analyze

        Returns:
            List of tool-level wildcard suggestions
        """
        logger.info("Detecting cross-folder tool patterns")
        approvals = self.tracker.get_recent_approvals(days=days)

        if not approvals:
            return []

        # Extract tool names from Bash permissions
        # Pattern: Bash(toolname ...) or Bash(toolname:*)
        tool_usage: dict[str, list[PermissionApprovalEntry]] = defaultdict(list)

        for approval in approvals:
            perm = approval.permission
            # Match Bash(toolname ...) - extract first word after Bash(
            match = re.match(r"Bash\(([a-zA-Z0-9_-]+)", perm)
            if match:
                tool_name = match.group(1)
                # Skip very short tool names (likely false positives)
                if len(tool_name) >= 2:
                    tool_usage[tool_name].append(approval)

        # Find tools used across multiple folders
        cross_folder_tools = []
        config = self.CROSS_FOLDER_CONFIG

        for tool_name, tool_approvals in tool_usage.items():
            unique_folders = len({a.project_path for a in tool_approvals})
            total_approvals = len(tool_approvals)

            if (
                unique_folders >= config["min_unique_folders"]
                and total_approvals >= config["min_total_approvals"]
            ):
                # Calculate confidence with cross-folder boost
                base_confidence = self._calculate_pattern_confidence(
                    tool_approvals, approvals
                )
                boosted_confidence = min(
                    1.0, base_confidence + config["confidence_boost"]
                )

                logger.info(
                    f"✓ Cross-folder tool: {tool_name} "
                    f"({total_approvals} uses in {unique_folders} folders, "
                    f"{boosted_confidence:.0%} confidence)"
                )

                pattern = PermissionPattern(
                    pattern_type=f"CrossFolder_{tool_name}",
                    occurrences=total_approvals,
                    confidence=boosted_confidence,
                    examples=[a.permission for a in tool_approvals[:5]],
                    detected_at=datetime.now(),
                    time_window_days=days,
                )
                cross_folder_tools.append(pattern)

        # Filter already-approved patterns
        existing_patterns = self._get_existing_patterns()
        cross_folder_tools = [
            p for p in cross_folder_tools
            if not self._is_tool_already_approved(
                p.pattern_type.replace("CrossFolder_", ""),
                existing_patterns
            )
        ]

        # Create suggestions
        suggestions = []
        for pattern in cross_folder_tools:
            tool_name = pattern.pattern_type.replace("CrossFolder_", "")
            suggestion = PatternSuggestion(
                description=f"Allow {tool_name} (cross-folder usage detected)",
                pattern=pattern,
                proposed_rule=f"Bash({tool_name}:*)",
                would_allow=[f"Bash({tool_name} any arguments)"],
                would_still_ask=[],
                approved_examples=pattern.examples,
                impact_estimate=f"Cross-folder: {pattern.occurrences} approvals across multiple projects",
            )
            suggestions.append(suggestion)

        return suggestions

    def _is_tool_already_approved(
        self, tool_name: str, existing_patterns: set[str]
    ) -> bool:
        """Check if a tool is already covered by existing wildcard patterns."""
        # Check for exact Bash(tool:*) pattern
        if f"Bash({tool_name}:*)" in existing_patterns:
            return True
        # Check for Bash(tool *) pattern (older format)
        if f"Bash({tool_name} *)" in existing_patterns:
            return True
        return False

    # Mapping from category to primary tool names (for wildcard coverage check)
    # Boris-style: If git:* exists, skip Git_workflow detection entirely
    CATEGORY_TO_TOOLS = {
        "Git_read_only": ["git"],
        "Git_workflow": ["git"],
        "Git_destructive": ["git"],
        "Pytest": ["pytest", "python"],
        "Ruff": ["ruff"],
        "Modern_cli": ["fd", "eza", "bat", "rg", "dust", "procs", "btm", "tree"],
        "File_operations": [],  # These use Read/Glob, not Bash
        "File_write_operations": [],  # These use Write/Edit, not Bash
        "Test_execution": ["npm", "pytest", "cargo", "go"],
        "Project_full_access": [],
        "Github_cli": ["gh"],
        "Cloud_cli": ["gcloud", "aws", "az"],
        "Package_managers": ["npm", "pnpm", "pip", "uv", "cargo", "yarn"],
        "Nix_tools": ["nix", "devenv", "nix-shell", "nix-build"],
        "Database_cli": ["sqlite3", "psql", "mysql", "mycli", "pgcli"],
        "Network_tools": ["curl", "wget", "xh", "httpie"],
        "Runtime_tools": ["python", "python3", "node", "ruby", "go"],
        "Posix_filesystem": ["find", "ls", "mkdir", "rmdir", "touch", "mv", "cp"],
        "Posix_search": ["grep", "awk", "sed", "cut", "sort", "uniq"],
        "Posix_read": ["cat", "head", "tail", "less", "more", "wc"],
        "Shell_utilities": ["echo", "printf", "sleep", "which", "type", "cd", "pwd"],
        "Dangerous_operations": [],  # Never auto-skip dangerous ops
    }

    def _is_category_covered_by_wildcards(
        self, category: str, existing_patterns: set[str]
    ) -> bool:
        """
        Check if a category is already fully covered by existing wildcard patterns.

        Boris-style optimization: If settings.local.json already has Bash(git:*),
        don't waste time detecting Git_workflow patterns.

        Args:
            category: Pattern category name
            existing_patterns: Set of patterns from settings.local.json

        Returns:
            True if ALL tools in the category are already covered
        """
        tools = self.CATEGORY_TO_TOOLS.get(category, [])

        if not tools:
            return False  # Categories without tool mappings need detection

        # Check if ALL tools in the category are covered
        for tool in tools:
            if not self._is_tool_already_approved(tool, existing_patterns):
                return False  # At least one tool not covered

        return True  # All tools covered - skip this category

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
        min_occ = (
            min_occurrences if min_occurrences is not None else self.min_occurrences
        )

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
        Calculate confidence based on pattern RELIABILITY with Boris-style weighting.

        Philosophy: Cross-folder/cross-project usage is the strongest signal.
        If you approve curl in 3 different folders, you trust curl - period.

        Factors (rebalanced for permissive learning):
        - Base: 0.4 (lower base, let bonuses drive confidence)
        - Session spread: +0.15 (appears across sessions)
        - Folder/Project spread: +0.35 (KEY SIGNAL - cross-folder = trust)
        - Consistency: +0.05 (same strings = predictable)
        - Recency: +0.05 (used recently = relevant)

        Max possible: 1.0
        Cross-folder patterns easily hit 0.7+ confidence

        Args:
            matching_approvals: Approvals matching this pattern
            all_approvals: All approvals for context

        Returns:
            Confidence score (0.0-1.0)
        """
        if not matching_approvals:
            return 0.0

        n = len(matching_approvals)

        # Base confidence: pattern exists (lowered to let cross-folder drive)
        base = 0.4

        # Session spread bonus (up to +0.15)
        unique_sessions = len({a.session_id for a in matching_approvals})
        session_bonus = min(0.15, (unique_sessions / 5) * 0.15)

        # CROSS-FOLDER/PROJECT SPREAD BONUS (up to +0.35) - THE KEY SIGNAL
        # Boris philosophy: if you approve a tool across different contexts,
        # you trust that tool. 2 folders = 0.175, 3+ folders = max bonus
        unique_projects = len({a.project_path for a in matching_approvals})
        # Aggressive scaling: 2 folders gets half bonus, 3+ gets full
        if unique_projects >= 3:
            project_bonus = 0.35
        elif unique_projects == 2:
            project_bonus = 0.25
        else:
            project_bonus = 0.10  # Single project still gets small bonus

        # Consistency bonus (up to +0.05)
        permission_counts = Counter(a.permission for a in matching_approvals)
        most_common_count = max(permission_counts.values())
        consistency_ratio = most_common_count / n
        consistency_bonus = consistency_ratio * 0.05

        # Recency bonus (+0.05 if pattern was used recently)
        recent_permissions = {a.permission for a in all_approvals[:20]}
        matching_permissions = {a.permission for a in matching_approvals}
        recency_bonus = 0.05 if recent_permissions & matching_permissions else 0.0

        confidence = (
            base + session_bonus + project_bonus + consistency_bonus + recency_bonus
        )
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
        # NOTE: Pattern names must start with uppercase for Claude Code validation
        rule_templates = {
            "Git_read_only": "Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git branch:*)",
            "Git_workflow": "Bash(git:*)",  # Standard git workflow
            "Git_destructive": "Bash(git --force:*), Bash(git reset --hard:*)",
            "Pytest": "Bash(pytest:*), Bash(python -m pytest:*)",
            "Ruff": "Bash(ruff:*)",
            "Modern_cli": "Bash(fd:*), Bash(eza:*), Bash(bat:*), Bash(rg:*), Bash(dust:*), Bash(procs:*)",
            "File_operations": "Read(/**), Glob(**)",
            "File_write_operations": "Write(/**), Edit(/**)",
            "Test_execution": "Bash(npm test:*), Bash(pytest:*), Bash(cargo test:*), Bash(go test:*)",
            "Project_full_access": "Read(/home/*/project/**), Write(/home/*/project/**)",
            "Github_cli": "Bash(gh:*)",
            "Cloud_cli": "Bash(gcloud:*), Bash(aws:*), Bash(az:*)",
            "Package_managers": "Bash(npm:*), Bash(pnpm:*), Bash(pip:*), Bash(uv:*)",
            "Nix_tools": "Bash(nix:*), Bash(devenv:*)",
            "Database_cli": "Bash(sqlite3:*), Bash(psql:*), Bash(mycli:*)",
            "Network_tools": "Bash(curl:*), Bash(xh:*)",
            "Runtime_tools": "Bash(python:*), Bash(node:*)",
            "Posix_filesystem": "Bash(find:*), Bash(ls:*), Bash(mkdir:*)",
            "Posix_search": "Bash(grep:*), Bash(awk:*), Bash(sed:*)",
            "Posix_read": "Bash(cat:*), Bash(head:*), Bash(tail:*)",
            "Shell_utilities": "Bash(echo:*), Bash(which:*)",
            "Dangerous_operations": "Bash(rm -rf:*), Bash(sudo:*)",
        }

        rule = rule_templates.get(pattern.pattern_type)
        if not rule:
            # CRITICAL: Never return raw pattern_type as a permission rule
            # This was the root cause of the recurring "file_write_operations" bug
            logger.error(
                f"No rule template found for pattern type: {pattern.pattern_type}. "
                "Returning empty string to prevent invalid permission."
            )
            return ""
        return rule

    def _get_edge_cases(self, pattern: PermissionPattern) -> list[str]:
        """
        Get edge cases that would still require approval.

        Args:
            pattern: Detected pattern

        Returns:
            List of edge case examples
        """
        edge_cases = {
            "Git_workflow": ["Bash(git push --force)", "Bash(git reset --hard)"],
            "File_operations": ["Write(/etc/passwd)", "Read(/home/other_user/.ssh)"],
            "Project_full_access": ["Write(/home/user/.ssh/)", "Read(/etc/shadow)"],
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
