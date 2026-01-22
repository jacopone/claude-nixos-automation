"""
Confidence calculation for permission patterns.

Extracted from permission_pattern_detector.py to reduce complexity.
"""

from collections import Counter

from ...schemas import PermissionApprovalEntry


class ConfidenceCalculator:
    """
    Calculate confidence scores for permission patterns.

    Uses Boris-style weighting where cross-folder usage is the strongest signal.
    """

    # Confidence calculation weights
    BASE_CONFIDENCE = 0.4
    MAX_SESSION_BONUS = 0.15
    MAX_PROJECT_BONUS = 0.35
    MAX_CONSISTENCY_BONUS = 0.05
    RECENCY_BONUS = 0.05

    def calculate(
        self,
        matching_approvals: list[PermissionApprovalEntry],
        all_approvals: list[PermissionApprovalEntry],
    ) -> float:
        """
        Calculate confidence based on pattern RELIABILITY.

        Philosophy: Cross-folder/cross-project usage is the strongest signal.
        If you approve curl in 3 different folders, you trust curl - period.

        Factors:
        - Base: 0.4 (lower base, let bonuses drive confidence)
        - Session spread: +0.15 (appears across sessions)
        - Folder/Project spread: +0.35 (KEY SIGNAL - cross-folder = trust)
        - Consistency: +0.05 (same strings = predictable)
        - Recency: +0.05 (used recently = relevant)

        Args:
            matching_approvals: Approvals matching this pattern
            all_approvals: All approvals for context

        Returns:
            Confidence score (0.0-1.0)
        """
        if not matching_approvals:
            return 0.0

        confidence = self.BASE_CONFIDENCE
        confidence += self._session_spread_bonus(matching_approvals)
        confidence += self._project_spread_bonus(matching_approvals)
        confidence += self._consistency_bonus(matching_approvals)
        confidence += self._recency_bonus(matching_approvals, all_approvals)

        return min(1.0, confidence)

    def _session_spread_bonus(
        self, matching_approvals: list[PermissionApprovalEntry]
    ) -> float:
        """Calculate bonus for patterns appearing across multiple sessions."""
        unique_sessions = len({a.session_id for a in matching_approvals})
        return min(self.MAX_SESSION_BONUS, (unique_sessions / 5) * self.MAX_SESSION_BONUS)

    def _project_spread_bonus(
        self, matching_approvals: list[PermissionApprovalEntry]
    ) -> float:
        """
        Calculate bonus for patterns appearing across multiple projects/folders.

        This is the KEY SIGNAL - cross-folder usage indicates trust.
        """
        unique_projects = len({a.project_path for a in matching_approvals})

        if unique_projects >= 3:
            return self.MAX_PROJECT_BONUS  # Full bonus
        elif unique_projects == 2:
            return 0.25  # Partial bonus
        else:
            return 0.10  # Small bonus for single project

    def _consistency_bonus(
        self, matching_approvals: list[PermissionApprovalEntry]
    ) -> float:
        """Calculate bonus for consistent permission strings."""
        n = len(matching_approvals)
        permission_counts = Counter(a.permission for a in matching_approvals)
        most_common_count = max(permission_counts.values())
        consistency_ratio = most_common_count / n
        return consistency_ratio * self.MAX_CONSISTENCY_BONUS

    def _recency_bonus(
        self,
        matching_approvals: list[PermissionApprovalEntry],
        all_approvals: list[PermissionApprovalEntry],
    ) -> float:
        """Calculate bonus if pattern was used recently."""
        recent_permissions = {a.permission for a in all_approvals[:20]}
        matching_permissions = {a.permission for a in matching_approvals}
        return self.RECENCY_BONUS if recent_permissions & matching_permissions else 0.0
