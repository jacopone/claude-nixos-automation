"""
Disk Health Monitor - Analyzes learning data disk usage and assesses risk.

This is a Tier 1 analyzer that tracks disk metrics for adaptive learning data.
Phase 1: Snapshot-based monitoring with risk assessment.
Phase 1.5: Historical tracking for growth rate analysis.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from claude_automation.analyzers.base_analyzer import BaseAnalyzer
from claude_automation.analyzers.disk_health_tracker import DiskHealthTracker
from claude_automation.schemas.health import (
    DiskHealthSnapshot,
    LearningDataHealthReport,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class DiskHealthMonitor(BaseAnalyzer):
    """
    Monitor disk health for adaptive learning data.

    Analyzes:
    - Session logs (~/.claude/projects/**/*.jsonl)
    - Learning cache (~/.claude/learning/*.jsonl)
    - Archives (~/.claude/archives/**/*.tar.gz) if present
    - Available disk space
    - Risk level assessment

    Phase 1: Snapshot-based monitoring.
    Phase 1.5: Historical tracking with growth projections.
    """

    def __init__(self, **kwargs):
        """
        Initialize disk health monitor.

        Args:
            **kwargs: Optional parameters (for future extension)
        """
        super().__init__(**kwargs)

        # Data directories
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.learning_dir = Path.home() / ".claude" / "learning"
        self.archives_dir = Path.home() / ".claude" / "archives"

        # History tracker for growth analysis
        self.tracker = DiskHealthTracker()

    def _get_analysis_method_name(self) -> str:
        """Return the primary analysis method name."""
        return "analyze"

    def analyze(self) -> LearningDataHealthReport:
        """
        Analyze learning data disk usage and assess risk.

        Returns:
            LearningDataHealthReport with current health status
        """
        logger.info("Analyzing learning data disk health...")

        # Step 1: Calculate sizes
        session_logs_bytes, session_count = self._get_session_logs_size()
        learning_data_bytes = self._get_directory_size(self.learning_dir)
        archives_bytes = (
            self._get_directory_size(self.archives_dir)
            if self.archives_dir.exists()
            else 0
        )

        total_bytes = session_logs_bytes + learning_data_bytes + archives_bytes

        # Step 2: Get disk space info
        disk_stat = self._get_disk_stats()
        total_disk_bytes = disk_stat.total
        available_bytes = disk_stat.free

        # Step 3: Calculate percentages
        usage_percentage = (
            (total_bytes / total_disk_bytes) * 100 if total_disk_bytes > 0 else 0.0
        )

        # Step 4: Assess risk
        risk_level, risk_message = self._assess_risk(total_bytes, total_disk_bytes)

        # Step 5: Calculate growth metrics (Phase 1.5)
        growth_mb_per_month = self.tracker.calculate_growth_rate(days=90)
        months_until_full = None

        if growth_mb_per_month is not None and growth_mb_per_month > 0:
            months_until_full = self.tracker.calculate_months_until_full(
                current_mb=total_bytes // (1024**2),
                available_gb=available_bytes // (1024**3),
                growth_mb_per_month=growth_mb_per_month
            )

        # Step 6: Build report
        report = LearningDataHealthReport(
            session_logs_mb=session_logs_bytes // (1024**2),
            learning_data_mb=learning_data_bytes // (1024**2),
            archives_mb=archives_bytes // (1024**2),
            total_mb=total_bytes // (1024**2),
            session_count=session_count,
            available_gb=available_bytes // (1024**3),
            usage_percentage=round(usage_percentage, 2),
            risk_level=risk_level,
            risk_message=risk_message,
            # Phase 1.5: Growth tracking
            growth_mb_per_month=growth_mb_per_month,
            months_until_full=months_until_full,
        )

        # Step 7: Record snapshot for future growth analysis
        snapshot = DiskHealthSnapshot(
            timestamp=datetime.now(),
            total_mb=report.total_mb,
            session_logs_mb=report.session_logs_mb,
            learning_data_mb=report.learning_data_mb,
            archives_mb=report.archives_mb,
            available_gb=report.available_gb,
            session_count=report.session_count,
        )
        self.tracker.record_snapshot(snapshot)

        logger.info(
            f"Health check complete: {report.total_mb}MB used, "
            f"{report.available_gb}GB available, risk={risk_level.value}"
        )

        if growth_mb_per_month is not None:
            if months_until_full is not None:
                logger.info(
                    f"Growth: {growth_mb_per_month:.1f}MB/month, "
                    f"projected {months_until_full:.1f} months until full"
                )
            else:
                logger.info(f"Growth: {growth_mb_per_month:.1f}MB/month")

        return report

    def _get_session_logs_size(self) -> tuple[int, int]:
        """
        Calculate total size of session logs and count files.

        Returns:
            Tuple of (total_bytes, file_count)
        """
        return self._get_directory_size(
            self.projects_dir,
            pattern="*.jsonl",
            count_files=True
        )

    def _get_directory_size(
        self,
        directory: Path,
        pattern: str = "*",
        count_files: bool = False
    ) -> int | tuple[int, int]:
        """
        Calculate total size of files in a directory recursively.

        Args:
            directory: Directory to measure
            pattern: Glob pattern for files (default: "*" for all files)
            count_files: Whether to return file count as well

        Returns:
            If count_files=True: Tuple of (total_bytes, file_count)
            If count_files=False: Total size in bytes
        """
        if not directory.exists():
            logger.debug(f"Directory not found: {directory}")
            return (0, 0) if count_files else 0

        total_bytes = 0
        file_count = 0

        try:
            # Scan directory for matching files
            for item in directory.rglob(pattern):
                if item.is_file():
                    try:
                        total_bytes += item.stat().st_size
                        if count_files:
                            file_count += 1
                    except (OSError, PermissionError) as e:
                        logger.debug(f"Could not stat file {item}: {e}")
                        continue

            # Log results
            if count_files:
                logger.debug(
                    f"{directory.name}: {file_count} files, "
                    f"{total_bytes / (1024**2):.1f}MB"
                )
            else:
                logger.debug(f"{directory.name}: {total_bytes / (1024**2):.1f}MB")

        except Exception as e:
            logger.warning(f"Error scanning directory {directory}: {e}")
            return (0, 0) if count_files else 0

        return (total_bytes, file_count) if count_files else total_bytes

    def _get_disk_stats(self):
        """
        Get disk usage statistics for home directory.

        Returns:
            os.statvfs_result with .total, .free, .used attributes
        """
        try:
            stat = shutil.disk_usage(Path.home())

            logger.debug(
                f"Disk space: {stat.total / (1024**3):.1f}GB total, "
                f"{stat.free / (1024**3):.1f}GB free"
            )

            return stat

        except Exception as e:
            logger.error(f"Could not get disk space: {e}")
            # Return zero values to trigger RED alert
            from collections import namedtuple
            DiskStat = namedtuple('DiskStat', ['total', 'used', 'free'])
            return DiskStat(total=0, used=0, free=0)

    def _assess_risk(self, total_bytes: int, total_disk_bytes: int) -> tuple[RiskLevel, str]:
        """
        Assess disk usage risk level.

        Risk levels:
        - GREEN: <1% disk usage (no action needed)
        - YELLOW: 1-5% disk usage (monitor, cleanup optional)
        - ORANGE: 5-20% disk usage (plan cleanup after insights extracted)
        - RED: >20% disk usage (urgent cleanup needed)

        Args:
            total_bytes: Total learning data size
            total_disk_bytes: Total disk capacity

        Returns:
            Tuple of (risk_level, risk_message)
        """
        if total_disk_bytes == 0:
            return RiskLevel.RED, "Unable to determine disk space"

        percentage = (total_bytes / total_disk_bytes) * 100
        total_mb = total_bytes / (1024**2)

        # Assess risk based on percentage thresholds
        if percentage < 1.0:
            return (
                RiskLevel.GREEN,
                f"No action needed - data size is healthy ({percentage:.2f}% of disk)",
            )
        elif percentage < 5.0:
            return (
                RiskLevel.YELLOW,
                f"Monitor - cleanup optional ({total_mb:.0f}MB, {percentage:.1f}% of disk)",
            )
        elif percentage < 20.0:
            return (
                RiskLevel.ORANGE,
                f"Plan cleanup after insights extracted ({total_mb:.0f}MB, {percentage:.1f}% of disk)",
            )
        else:
            return (
                RiskLevel.RED,
                f"URGENT: Extract insights and cleanup NOW ({total_mb:.0f}MB, {percentage:.1f}% of disk)",
            )
