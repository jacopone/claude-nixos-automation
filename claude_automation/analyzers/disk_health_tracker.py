"""
Disk Health Tracker - Manages historical disk health data for growth analysis.

This is a Tier 1 analyzer that stores and analyzes historical disk usage snapshots
to calculate growth rates and project future disk space needs.

Phase 1.5: History tracking and growth projections.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from claude_automation.analyzers.base_analyzer import BaseAnalyzer
from claude_automation.schemas.health import DiskHealthSnapshot

logger = logging.getLogger(__name__)


class DiskHealthTracker(BaseAnalyzer):
    """
    Track historical disk health metrics for growth analysis.

    Stores snapshots in ~/.claude/learning/disk_health_history.jsonl and
    calculates growth rates to project future disk space needs.
    """

    def __init__(self, **kwargs):
        """
        Initialize disk health tracker.

        Args:
            **kwargs: Optional parameters (for future extension)
        """
        super().__init__(**kwargs)

        self.history_file = (
            Path.home() / ".claude" / "learning" / "disk_health_history.jsonl"
        )
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_analysis_method_name(self) -> str:
        """Return the primary analysis method name."""
        return "calculate_growth_rate"

    def record_snapshot(self, snapshot: DiskHealthSnapshot) -> None:
        """
        Record a disk health snapshot to history.

        Args:
            snapshot: DiskHealthSnapshot to append to history
        """
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                # Serialize with ISO timestamp for readability
                data = snapshot.model_dump()
                data["timestamp"] = snapshot.timestamp.isoformat()
                f.write(json.dumps(data) + "\n")

            logger.debug(
                f"Recorded snapshot: {snapshot.total_mb}MB at {snapshot.timestamp}"
            )

        except Exception as e:
            logger.warning(f"Could not record snapshot: {e}")

    def get_history(self, days: int = 90) -> list[DiskHealthSnapshot]:
        """
        Load recent disk health history.

        Args:
            days: Number of days of history to retrieve

        Returns:
            List of DiskHealthSnapshot objects, sorted by timestamp
        """
        if not self.history_file.exists():
            logger.debug("No history file found")
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        snapshots = []

        try:
            with open(self.history_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        # Parse ISO timestamp
                        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                        snapshot = DiskHealthSnapshot(**data)

                        # Only include snapshots within date range
                        if snapshot.timestamp >= cutoff_date:
                            snapshots.append(snapshot)

                    except Exception as e:
                        logger.debug(f"Could not parse snapshot line: {e}")
                        continue

            logger.debug(f"Loaded {len(snapshots)} snapshots from last {days} days")

        except Exception as e:
            logger.warning(f"Could not load history: {e}")
            return []

        # Sort by timestamp
        snapshots.sort(key=lambda s: s.timestamp)
        return snapshots

    def calculate_growth_rate(self, days: int = 90) -> float | None:
        """
        Calculate monthly growth rate from historical data.

        Uses simple linear calculation: (last - first) / time_diff * 30 days

        Args:
            days: Number of days of history to analyze

        Returns:
            Growth rate in MB per month, or None if insufficient data
        """
        snapshots = self.get_history(days=days)

        # Need at least 2 snapshots to calculate growth
        if len(snapshots) < 2:
            logger.debug(
                "Insufficient history for growth calculation (need 2+ snapshots)"
            )
            return None

        first = snapshots[0]
        last = snapshots[-1]

        # Calculate time difference in days
        time_diff = (last.timestamp - first.timestamp).total_seconds() / 86400

        # Need at least 1 day of data
        if time_diff < 1:
            logger.debug("Snapshots too close together for growth calculation")
            return None

        # Calculate growth: (change in MB) / (days) * 30 (to get monthly rate)
        size_diff_mb = last.total_mb - first.total_mb
        growth_per_day = size_diff_mb / time_diff
        growth_per_month = growth_per_day * 30

        logger.info(
            f"Growth rate: {growth_per_month:.1f}MB/month "
            f"(based on {len(snapshots)} snapshots over {time_diff:.1f} days)"
        )

        return growth_per_month

    def calculate_months_until_full(
        self, current_mb: int, available_gb: int, growth_mb_per_month: float
    ) -> float | None:
        """
        Project months until disk fills based on growth rate.

        Args:
            current_mb: Current learning data size in MB
            available_gb: Available disk space in GB
            growth_mb_per_month: Monthly growth rate in MB

        Returns:
            Estimated months until disk full, or None if not applicable
        """
        # Can't project if no growth
        if growth_mb_per_month <= 0:
            logger.debug("No growth or negative growth - cannot project disk full")
            return None

        # Convert available space to MB
        available_mb = available_gb * 1024

        # Calculate how much space learning data can grow into
        # (We're assuming learning data will fill available space)
        space_remaining_mb = available_mb

        # Calculate months
        months_until_full = space_remaining_mb / growth_mb_per_month

        logger.debug(
            f"Projection: {months_until_full:.1f} months until {space_remaining_mb:.0f}MB "
            f"filled at {growth_mb_per_month:.1f}MB/month"
        )

        return months_until_full
