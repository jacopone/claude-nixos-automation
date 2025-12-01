"""
Instruction effectiveness tracker for policy compliance monitoring.
Tracks adherence to CLAUDE.md policies and suggests improvements.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from ..schemas import (
    InstructionEffectiveness,
    InstructionImprovement,
    PolicyViolation,
)
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class InstructionEffectivenessTracker(BaseAnalyzer):
    """
    Tracks effectiveness of CLAUDE.md instructions.

    Monitors policy compliance, detects violations, and
    suggests improvements for low-effectiveness policies.
    """

    def __init__(self, log_file: Path | None = None):
        """
        Initialize instruction effectiveness tracker.

        Args:
            log_file: Path to JSONL log file (default: ~/.claude/learning/policy_violations.jsonl)
        """
        if log_file is None:
            log_file = Path.home() / ".claude" / "learning" / "policy_violations.jsonl"

        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_analysis_method_name(self) -> str:
        """Return the name of the primary analysis method."""
        return "suggest_improvements"

    def log_session(
        self,
        session_id: str,
        policy_name: str,
        compliant: bool,
        violation_type: str = "",
        details: str = "",
        severity: str = "medium",
    ):
        """
        Log a session's compliance with a policy.

        Args:
            session_id: Session identifier
            policy_name: Name of policy being checked
            compliant: Whether session was compliant
            violation_type: Type of violation if not compliant
            details: Additional violation details
            severity: Severity level (low, medium, high)
        """
        if not compliant:
            violation = PolicyViolation(
                timestamp=datetime.now(),
                policy_name=policy_name,
                violation_type=violation_type,
                session_id=session_id,
                details=details,
                severity=severity,
            )

            # Append to log file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(violation.model_dump_json() + "\n")

            logger.debug(f"Logged policy violation: {policy_name} ({violation_type})")

    def get_recent_violations(
        self, days: int = 30, policy_name: str | None = None
    ) -> list[PolicyViolation]:
        """
        Get recent policy violations within time window.

        Args:
            days: Number of days to look back
            policy_name: Filter by specific policy (None = all)

        Returns:
            List of PolicyViolation entries
        """
        if not self.log_file.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        violations = []

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    entry_dict = json.loads(line)
                    violation = PolicyViolation(**entry_dict)

                    if violation.timestamp > cutoff:
                        if policy_name is None or violation.policy_name == policy_name:
                            violations.append(violation)
                except Exception as e:
                    logger.warning(f"Failed to parse violation log entry: {e}")
                    continue

        return violations

    def get_effectiveness_score(
        self, policy_name: str, total_sessions: int, days: int = 30
    ) -> InstructionEffectiveness:
        """
        Calculate effectiveness score for a policy.

        Args:
            policy_name: Name of policy to evaluate
            total_sessions: Total number of sessions in period
            days: Analysis window in days

        Returns:
            InstructionEffectiveness with metrics
        """
        violations = self.get_recent_violations(days, policy_name)

        # Calculate compliant sessions (ensure non-negative)
        compliant_sessions = max(0, total_sessions - len(violations))

        # Calculate effectiveness score
        if total_sessions == 0:
            effectiveness_score = 1.0  # No sessions = no violations
        else:
            effectiveness_score = max(0.0, compliant_sessions / total_sessions)

        return InstructionEffectiveness(
            policy_name=policy_name,
            total_sessions=total_sessions,
            compliant_sessions=compliant_sessions,
            violations=violations,
            effectiveness_score=effectiveness_score,
            last_evaluated=datetime.now(),
        )

    def suggest_improvements(
        self,
        total_sessions: int,
        days: int = 30,
        min_violations: int = 3,
        effectiveness_threshold: float = 0.7,
    ) -> list[InstructionImprovement]:
        """
        Suggest improvements for low-effectiveness policies.

        Args:
            total_sessions: Total number of sessions in period
            days: Analysis window in days
            min_violations: Minimum violations to trigger suggestion
            effectiveness_threshold: Score below which to suggest improvement

        Returns:
            List of InstructionImprovement suggestions
        """
        violations = self.get_recent_violations(days)

        if not violations:
            logger.info("No policy violations detected - all policies effective")
            return []

        # Group violations by policy
        policy_violations: dict[str, list[PolicyViolation]] = {}
        for violation in violations:
            if violation.policy_name not in policy_violations:
                policy_violations[violation.policy_name] = []
            policy_violations[violation.policy_name].append(violation)

        # Identify low-effectiveness policies
        improvements = []

        for policy_name, policy_viols in policy_violations.items():
            # Skip if not enough violations to be meaningful
            if len(policy_viols) < min_violations:
                continue

            # Calculate effectiveness
            effectiveness = self.get_effectiveness_score(
                policy_name, total_sessions, days
            )

            # Skip if already effective
            if effectiveness.is_effective:
                continue

            # Generate improvement suggestion
            improvement = self._generate_improvement_suggestion(
                policy_name, effectiveness
            )
            improvements.append(improvement)

        # Sort by priority (low effectiveness = high priority)
        improvements.sort(key=lambda i: i.effectiveness_data.effectiveness_score)

        logger.info(
            f"Generated {len(improvements)} instruction improvement suggestions"
        )
        return improvements

    def _generate_improvement_suggestion(
        self, policy_name: str, effectiveness: InstructionEffectiveness
    ) -> InstructionImprovement:
        """
        Generate improvement suggestion for a policy.

        Args:
            policy_name: Policy name
            effectiveness: Effectiveness data

        Returns:
            InstructionImprovement suggestion
        """
        # Analyze violation types to suggest rewording
        violation_types = [v.violation_type for v in effectiveness.violations]
        most_common = max(set(violation_types), key=violation_types.count)

        # Generate reason
        reason = f"Policy violated {len(effectiveness.violations)} times ({effectiveness.effectiveness_score:.0%} compliance). Most common: {most_common}"

        # Generate suggested wording
        current_wording = f"Original policy: {policy_name}"
        suggested_wording = self._suggest_policy_rewording(policy_name, most_common)

        # Determine priority
        if effectiveness.effectiveness_score < 0.5:
            priority = 1  # High priority
        elif effectiveness.effectiveness_score < 0.7:
            priority = 2  # Medium priority
        else:
            priority = 3  # Low priority

        return InstructionImprovement(
            policy_name=policy_name,
            current_wording=current_wording,
            suggested_wording=suggested_wording,
            reason=reason,
            effectiveness_data=effectiveness,
            priority=priority,
        )

    def _suggest_policy_rewording(self, policy_name: str, violation_type: str) -> str:
        """
        Suggest improved wording for a policy.

        Args:
            policy_name: Policy name
            violation_type: Most common violation type

        Returns:
            Suggested improved wording
        """
        # Common rewording patterns
        if "documentation" in policy_name.lower():
            return "**CRITICAL:** ALWAYS ask before creating documentation files (.md, .txt, README). Only create documentation if explicitly requested or part of agreed plan."

        if "tool" in policy_name.lower():
            return "**IMPORTANT:** ALWAYS use modern tools (fd, rg, bat, eza) instead of traditional Unix commands (find, grep, cat, ls)."

        # Generic improvement
        return f"**IMPORTANT:** {policy_name} - Add clarity and emphasis"

    def get_stats(self, days: int = 30) -> dict:
        """
        Get aggregated statistics.

        Args:
            days: Analysis window in days

        Returns:
            Dict with statistics
        """
        violations = self.get_recent_violations(days)

        if not violations:
            return {
                "total_violations": 0,
                "unique_policies": 0,
                "severity_breakdown": {},
            }

        # Count by policy
        policy_counts: dict[str, int] = {}
        for v in violations:
            policy_counts[v.policy_name] = policy_counts.get(v.policy_name, 0) + 1

        # Count by severity
        severity_counts: dict[str, int] = {}
        for v in violations:
            severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

        return {
            "total_violations": len(violations),
            "unique_policies": len(policy_counts),
            "severity_breakdown": severity_counts,
            "most_violated": sorted(
                policy_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }
