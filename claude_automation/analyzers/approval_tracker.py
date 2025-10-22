"""
ApprovalTracker - Logs and retrieves permission approval history.

This module tracks when users approve Claude Code permissions, storing
them in JSONL format for pattern detection.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..schemas import PermissionApprovalEntry

logger = logging.getLogger(__name__)


class ApprovalTracker:
    """
    Tracks permission approvals in JSONL format.

    Storage: ~/.claude/learning/permission_approvals.jsonl
    Format: One JSON object per line, append-only
    """

    def __init__(self, storage_dir: Path | None = None):
        """
        Initialize approval tracker.

        Args:
            storage_dir: Directory for learning data (default: ~/.claude/learning/)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".claude" / "learning"

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.approvals_file = storage_dir / "permission_approvals.jsonl"
        self.max_file_size_mb = 10  # Rotate after 10MB

    def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds size limit."""
        if not self.approvals_file.exists():
            return

        size_mb = self.approvals_file.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            # Archive old file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = self.storage_dir / f"permission_approvals_{timestamp}.jsonl"

            logger.info(f"Rotating approval log: {size_mb:.1f}MB → {archive_path.name}")
            self.approvals_file.rename(archive_path)

            # Optionally compress old archives
            import gzip
            import shutil
            compressed_path = archive_path.with_suffix('.jsonl.gz')
            with open(archive_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            archive_path.unlink()  # Remove uncompressed
            logger.info(f"Compressed archive: {compressed_path.name}")

    def log_approval(
        self,
        permission: str,
        session_id: str,
        project_path: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a permission approval.

        Args:
            permission: The approved permission string
            session_id: Claude Code session identifier
            project_path: Project where approval occurred
            context: Additional context metadata
        """
        # Create approval entry
        entry = PermissionApprovalEntry(
            timestamp=datetime.now(),
            permission=permission,
            session_id=session_id,
            project_path=project_path,
            context=context or {},
        )

        # Rotate log file if needed (before writing)
        self._rotate_if_needed()

        # Append to JSONL file
        try:
            with open(self.approvals_file, "a", encoding="utf-8") as f:
                json_line = entry.model_dump_json()
                f.write(json_line + "\n")

            logger.debug(f"Logged approval: {permission} (session: {session_id})")

        except Exception as e:
            logger.error(f"Failed to log approval: {e}")

    def get_recent_approvals(
        self, days: int = 30, project_path: str | None = None
    ) -> list[PermissionApprovalEntry]:
        """
        Get recent permission approvals.

        Args:
            days: Number of days to look back
            project_path: Filter by project path (optional)

        Returns:
            List of approval entries, newest first
        """
        if not self.approvals_file.exists():
            return []

        cutoff = datetime.now(UTC) - timedelta(days=days)
        approvals = []

        try:
            with open(self.approvals_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse JSON line
                    data = json.loads(line)
                    entry = PermissionApprovalEntry(**data)

                    # Make timestamp timezone-aware if naive
                    if entry.timestamp.tzinfo is None:
                        entry.timestamp = entry.timestamp.replace(tzinfo=UTC)

                    # Filter by date
                    if entry.timestamp < cutoff:
                        continue

                    # Filter by project if specified
                    if project_path and entry.project_path != project_path:
                        continue

                    approvals.append(entry)

        except Exception as e:
            logger.error(f"Failed to read approvals: {e}")
            return []

        # Sort newest first
        approvals.sort(key=lambda e: e.timestamp, reverse=True)

        return approvals

    def get_approval_count(self, permission: str, days: int = 30) -> int:
        """
        Count how many times a permission was approved.

        Args:
            permission: Permission to count
            days: Time window in days

        Returns:
            Number of approvals
        """
        approvals = self.get_recent_approvals(days=days)
        return sum(1 for a in approvals if a.permission == permission)

    def get_all_unique_permissions(self, days: int = 30) -> set[str]:
        """
        Get all unique permissions approved in time window.

        Args:
            days: Time window in days

        Returns:
            Set of unique permission strings
        """
        approvals = self.get_recent_approvals(days=days)
        return {a.permission for a in approvals}

    def get_approvals_by_project(self, days: int = 30) -> dict[str, list[PermissionApprovalEntry]]:
        """
        Group approvals by project.

        Args:
            days: Time window in days

        Returns:
            Dictionary mapping project paths to approval lists
        """
        approvals = self.get_recent_approvals(days=days)
        by_project: dict[str, list[PermissionApprovalEntry]] = {}

        for approval in approvals:
            if approval.project_path not in by_project:
                by_project[approval.project_path] = []
            by_project[approval.project_path].append(approval)

        return by_project

    def clear_old_approvals(self, days: int = 90) -> int:
        """
        Remove approvals older than specified days.

        Args:
            days: Keep approvals newer than this

        Returns:
            Number of approvals removed
        """
        if not self.approvals_file.exists():
            return 0

        cutoff = datetime.now(UTC) - timedelta(days=days)
        kept_approvals = []
        removed_count = 0

        try:
            # Read all approvals
            with open(self.approvals_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    data = json.loads(line)
                    entry = PermissionApprovalEntry(**data)

                    # Make timestamp timezone-aware if naive
                    if entry.timestamp.tzinfo is None:
                        entry.timestamp = entry.timestamp.replace(tzinfo=UTC)

                    if entry.timestamp >= cutoff:
                        kept_approvals.append(data)
                    else:
                        removed_count += 1

            # Write back kept approvals
            with open(self.approvals_file, "w", encoding="utf-8") as f:
                for data in kept_approvals:
                    f.write(json.dumps(data) + "\n")

            logger.info(f"Cleared {removed_count} old approvals (older than {days} days)")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to clear old approvals: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about approval history.

        Returns:
            Dictionary with statistics
        """
        approvals_30d = self.get_recent_approvals(days=30)
        approvals_7d = self.get_recent_approvals(days=7)

        unique_permissions_30d = {a.permission for a in approvals_30d}
        unique_projects_30d = {a.project_path for a in approvals_30d}

        return {
            "total_approvals_30d": len(approvals_30d),
            "total_approvals_7d": len(approvals_7d),
            "unique_permissions_30d": len(unique_permissions_30d),
            "unique_projects_30d": len(unique_projects_30d),
            "storage_file": str(self.approvals_file),
            "storage_exists": self.approvals_file.exists(),
        }
