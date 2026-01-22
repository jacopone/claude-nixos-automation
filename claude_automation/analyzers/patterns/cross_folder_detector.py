"""
Cross-folder tool pattern detection.

Detects tools used across multiple folders and generates tool:* wildcards.
Extracted from permission_pattern_detector.py to reduce complexity.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime

from ...data import CROSS_FOLDER_CONFIG, TOOL_BLOCKLIST
from ...schemas import (
    PatternSuggestion,
    PermissionApprovalEntry,
    PermissionPattern,
)
from .confidence import ConfidenceCalculator

logger = logging.getLogger(__name__)


class CrossFolderDetector:
    """
    Detect tools used across multiple folders and generate wildcards.

    Boris-style philosophy: If you approve `curl` in folder A, folder B, and
    folder C, you clearly trust curl - generalize to `Bash(curl:*)`.
    """

    def __init__(self, confidence_calculator: ConfidenceCalculator | None = None):
        """Initialize with optional custom confidence calculator."""
        self.confidence = confidence_calculator or ConfidenceCalculator()
        self.config = CROSS_FOLDER_CONFIG

    def detect(
        self,
        approvals: list[PermissionApprovalEntry],
        existing_patterns: set[str],
        days: int = 30,
    ) -> list[PatternSuggestion]:
        """
        Detect tools used across multiple folders.

        Args:
            approvals: Permission approval history
            existing_patterns: Already-approved patterns to skip
            days: Time window for pattern suggestions

        Returns:
            List of tool-level wildcard suggestions
        """
        if not approvals:
            return []

        logger.info("Detecting cross-folder tool patterns")

        # Extract tool usage from Bash permissions
        tool_usage = self._extract_tool_usage(approvals)

        # Find tools used across multiple folders
        cross_folder_patterns = self._find_cross_folder_tools(tool_usage, approvals, days)

        # Filter already-approved patterns
        filtered_patterns = [
            p
            for p in cross_folder_patterns
            if not self._is_tool_already_approved(
                p.pattern_type.replace("CrossFolder_", ""), existing_patterns
            )
        ]

        # Create suggestions
        return [self._create_suggestion(pattern) for pattern in filtered_patterns]

    def _extract_tool_usage(
        self, approvals: list[PermissionApprovalEntry]
    ) -> dict[str, list[PermissionApprovalEntry]]:
        """
        Extract tool names from Bash permissions.

        Pattern: Bash(toolname ...) - extract first word after Bash(
        """
        tool_usage: dict[str, list[PermissionApprovalEntry]] = defaultdict(list)

        for approval in approvals:
            perm = approval.permission
            match = re.match(r"Bash\(([a-zA-Z0-9_-]+)", perm)
            if match:
                tool_name = match.group(1).lower()

                # Skip blocklisted tools (shell invocations, control flow, etc.)
                if tool_name in TOOL_BLOCKLIST:
                    continue

                # Skip very short tool names (likely false positives)
                if len(tool_name) >= 2:
                    tool_usage[tool_name].append(approval)

        return tool_usage

    def _find_cross_folder_tools(
        self,
        tool_usage: dict[str, list[PermissionApprovalEntry]],
        all_approvals: list[PermissionApprovalEntry],
        days: int,
    ) -> list[PermissionPattern]:
        """Find tools meeting cross-folder criteria."""
        patterns = []

        for tool_name, tool_approvals in tool_usage.items():
            unique_folders = len({a.project_path for a in tool_approvals})
            total_approvals = len(tool_approvals)

            if (
                unique_folders >= self.config["min_unique_folders"]
                and total_approvals >= self.config["min_total_approvals"]
            ):
                # Calculate confidence with cross-folder boost
                base_confidence = self.confidence.calculate(tool_approvals, all_approvals)
                boosted_confidence = min(
                    1.0, base_confidence + self.config["confidence_boost"]
                )

                logger.info(
                    f"Cross-folder tool: {tool_name} "
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
                patterns.append(pattern)

        return patterns

    def _is_tool_already_approved(
        self, tool_name: str, existing_patterns: set[str]
    ) -> bool:
        """Check if a tool is already covered by existing wildcard patterns."""
        return (
            f"Bash({tool_name}:*)" in existing_patterns
            or f"Bash({tool_name} *)" in existing_patterns
        )

    def _create_suggestion(self, pattern: PermissionPattern) -> PatternSuggestion:
        """Create a suggestion from a cross-folder pattern."""
        tool_name = pattern.pattern_type.replace("CrossFolder_", "")

        return PatternSuggestion(
            description=f"Allow {tool_name} (cross-folder usage detected)",
            pattern=pattern,
            proposed_rule=f"Bash({tool_name}:*)",
            would_allow=[f"Bash({tool_name} any arguments)"],
            would_still_ask=[],
            approved_examples=pattern.examples,
            impact_estimate=f"Cross-folder: {pattern.occurrences} approvals across multiple projects",
            tier="CROSS_FOLDER",
        )
