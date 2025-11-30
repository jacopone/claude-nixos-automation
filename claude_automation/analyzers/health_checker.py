"""
Analyzer Health Checker - Validates analyzer prerequisites and tracks failures.

Solves Silent Analyzer Degradation issue:
- Pre-flight validation before running analyzers
- Tracks which analyzers failed and why
- Provides actionable diagnostics
- Warns user when learning system is partially broken
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerHealthStatus:
    """Health status for a single analyzer."""

    analyzer_name: str
    is_healthy: bool
    status_message: str
    missing_prerequisites: list[str] = field(default_factory=list)
    last_error: str | None = None
    last_success_at: datetime | None = None
    consecutive_failures: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "analyzer": self.analyzer_name,
            "healthy": self.is_healthy,
            "status": self.status_message,
            "missing": self.missing_prerequisites,
            "error": self.last_error,
            "failures": self.consecutive_failures,
        }


@dataclass
class SystemHealthReport:
    """Overall health report for adaptive learning system."""

    timestamp: datetime = field(default_factory=datetime.now)
    total_analyzers: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    failed_count: int = 0
    analyzer_statuses: list[AnalyzerHealthStatus] = field(default_factory=list)

    @property
    def health_percentage(self) -> float:
        """Calculate overall health percentage."""
        if self.total_analyzers == 0:
            return 100.0
        return (self.healthy_count / self.total_analyzers) * 100

    @property
    def is_critical(self) -> bool:
        """Check if system health is critical (>50% failures)."""
        return self.failed_count > (self.total_analyzers / 2)

    @property
    def health_level(self) -> str:
        """Get human-readable health level."""
        if self.health_percentage >= 90:
            return "EXCELLENT"
        elif self.health_percentage >= 70:
            return "GOOD"
        elif self.health_percentage >= 50:
            return "FAIR"
        else:
            return "CRITICAL"

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "health_level": self.health_level,
            "health_percentage": self.health_percentage,
            "total_analyzers": self.total_analyzers,
            "healthy": self.healthy_count,
            "degraded": self.degraded_count,
            "failed": self.failed_count,
            "analyzers": [status.to_dict() for status in self.analyzer_statuses],
        }


class AnalyzerHealthChecker:
    """
    Health checker for adaptive learning analyzers.

    Usage:
        checker = AnalyzerHealthChecker()

        # Register analyzers with their validation functions
        checker.register_analyzer("permission_learning", validate_permission_prereqs)

        # Run health check
        report = checker.check_all_analyzers()

        if report.failed_count > 0:
            print(f"Warning: {report.failed_count} analyzers unhealthy")
            checker.print_health_report(report)
    """

    def __init__(self):
        """Initialize health checker."""
        self.validators: dict[str, Callable[[], tuple[bool, str, list[str]]]] = {}
        self.last_report: SystemHealthReport | None = None

    def register_analyzer(
        self,
        analyzer_name: str,
        validator: Callable[[], tuple[bool, str, list[str]]],
    ):
        """
        Register an analyzer with its validation function.

        Args:
            analyzer_name: Name of the analyzer
            validator: Function that returns (is_healthy, message, missing_prereqs)
        """
        self.validators[analyzer_name] = validator

    def check_all_analyzers(self) -> SystemHealthReport:
        """
        Check health of all registered analyzers.

        Returns:
            SystemHealthReport with detailed status
        """
        report = SystemHealthReport(
            total_analyzers=len(self.validators),
        )

        for analyzer_name, validator in self.validators.items():
            try:
                is_healthy, message, missing = validator()

                status = AnalyzerHealthStatus(
                    analyzer_name=analyzer_name,
                    is_healthy=is_healthy,
                    status_message=message,
                    missing_prerequisites=missing,
                )

                if is_healthy:
                    report.healthy_count += 1
                    status.last_success_at = datetime.now()
                elif missing:
                    report.degraded_count += 1
                else:
                    report.failed_count += 1

                report.analyzer_statuses.append(status)

            except Exception as e:
                logger.error(f"Health check failed for {analyzer_name}: {e}")

                status = AnalyzerHealthStatus(
                    analyzer_name=analyzer_name,
                    is_healthy=False,
                    status_message="Health check error",
                    last_error=str(e),
                )
                report.failed_count += 1
                report.analyzer_statuses.append(status)

        self.last_report = report
        return report

    def print_health_report(self, report: SystemHealthReport | None = None):
        """
        Print human-readable health report.

        Args:
            report: Health report to print (default: last report)
        """
        if report is None:
            report = self.last_report

        if report is None:
            print("❌ No health report available")
            return

        print("\n" + "=" * 70)
        print("🏥 ANALYZER HEALTH REPORT")
        print("=" * 70)

        print(f"\n📊 Overall Health: {report.health_level} ({report.health_percentage:.0f}%)")
        print(f"   • Healthy: {report.healthy_count}/{report.total_analyzers}")
        print(f"   • Degraded: {report.degraded_count}")
        print(f"   • Failed: {report.failed_count}")

        # Group by health status
        healthy = [s for s in report.analyzer_statuses if s.is_healthy]
        degraded = [
            s for s in report.analyzer_statuses if not s.is_healthy and s.missing_prerequisites
        ]
        failed = [
            s for s in report.analyzer_statuses if not s.is_healthy and not s.missing_prerequisites
        ]

        # Show healthy analyzers (brief)
        if healthy:
            print("\n✅ Healthy Analyzers:")
            for status in healthy:
                print(f"   • {status.analyzer_name}: {status.status_message}")

        # Show degraded analyzers (detailed)
        if degraded:
            print("\n⚠️  Degraded Analyzers:")
            for status in degraded:
                print(f"   • {status.analyzer_name}: {status.status_message}")
                if status.missing_prerequisites:
                    print(f"     Missing: {', '.join(status.missing_prerequisites)}")

        # Show failed analyzers (detailed)
        if failed:
            print("\n❌ Failed Analyzers:")
            for status in failed:
                print(f"   • {status.analyzer_name}: {status.status_message}")
                if status.last_error:
                    # Truncate long errors
                    error_msg = status.last_error[:100] + "..." if len(status.last_error) > 100 else status.last_error
                    print(f"     Error: {error_msg}")

        print("\n" + "=" * 70 + "\n")


# === Validator Functions ===


def validate_permission_learning() -> tuple[bool, str, list[str]]:
    """
    Validate permission learning analyzer prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    missing = []

    # Check for approval tracker data (matches ApprovalTracker path)
    approval_db = Path.home() / ".claude" / "learning" / "permission_approvals.jsonl"
    if not approval_db.exists():
        missing.append("permission_approvals.jsonl")

    if missing:
        return False, "Missing approval history data", missing

    # Check if file is readable and non-empty
    if approval_db.stat().st_size == 0:
        return False, "Approval history is empty", ["permission_approvals.jsonl (empty)"]

    return True, "Ready", []


def validate_mcp_optimization() -> tuple[bool, str, list[str]]:
    """
    Validate MCP analyzer prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    missing = []

    # Check for session logs
    session_dir = Path.home() / ".claude" / "projects"
    if not session_dir.exists():
        missing.append("~/.claude/projects")
        return False, "No Claude session logs found", missing

    # Check for MCP configuration
    mcp_config_global = Path.home() / ".claude.json"
    mcp_config_user = Path.home() / ".claude" / "mcp.json"

    if not mcp_config_global.exists() and not mcp_config_user.exists():
        missing.append("MCP server configuration")

    if missing:
        return False, "MCP configuration not found", missing

    return True, "Ready", []


def validate_context_optimization() -> tuple[bool, str, list[str]]:
    """
    Validate context optimizer prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    missing = []

    # Check for session logs (context usage tracking)
    session_dir = Path.home() / ".claude" / "projects"
    if not session_dir.exists():
        missing.append("~/.claude/projects")

    if missing:
        return False, "No session logs for context analysis", missing

    return True, "Ready", []


def validate_workflow_detection() -> tuple[bool, str, list[str]]:
    """
    Validate workflow detector prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    missing = []

    # Check for session logs (workflow tracking)
    session_dir = Path.home() / ".claude" / "projects"
    if not session_dir.exists():
        missing.append("~/.claude/projects")

    if missing:
        return False, "No session logs for workflow detection", missing

    return True, "Ready", []


def validate_instruction_tracking() -> tuple[bool, str, list[str]]:
    """
    Validate instruction tracker prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    missing = []

    # Check for policy violation tracking (matches InstructionEffectivenessTracker path)
    violation_db = Path.home() / ".claude" / "learning" / "policy_violations.jsonl"
    if not violation_db.exists():
        missing.append("policy_violations.jsonl")

    if missing:
        return False, "No policy violation data", missing

    return True, "Ready", []


def validate_cross_project() -> tuple[bool, str, list[str]]:
    """
    Validate cross-project analyzer prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    # Cross-project detection requires multiple projects
    # This is always available (scans filesystem)
    return True, "Ready", []


def validate_meta_learning() -> tuple[bool, str, list[str]]:
    """
    Validate meta-learner prerequisites.

    Returns:
        (is_healthy, message, missing_prerequisites)
    """
    missing = []

    # Check for learning metrics database (matches MetaLearner path)
    metrics_db = Path.home() / ".claude" / "learning" / "meta_metrics.jsonl"
    if not metrics_db.exists():
        missing.append("meta_metrics.jsonl")

    if missing:
        return False, "No learning metrics data", missing

    return True, "Ready", []


# === Convenience function ===


def create_default_health_checker() -> AnalyzerHealthChecker:
    """
    Create health checker with all default analyzers registered.

    Returns:
        AnalyzerHealthChecker with 7 analyzers registered
    """
    checker = AnalyzerHealthChecker()

    checker.register_analyzer("permission_learning", validate_permission_learning)
    checker.register_analyzer("mcp_optimization", validate_mcp_optimization)
    checker.register_analyzer("context_optimization", validate_context_optimization)
    checker.register_analyzer("workflow_detection", validate_workflow_detection)
    checker.register_analyzer("instruction_tracking", validate_instruction_tracking)
    checker.register_analyzer("cross_project", validate_cross_project)
    checker.register_analyzer("meta_learning", validate_meta_learning)

    return checker
