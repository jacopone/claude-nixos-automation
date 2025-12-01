"""
RejectionTracker - Logs and retrieves suggestion rejection history.

Tracks when users reject workflow/permission/mcp/context suggestions to prevent
re-suggesting the same patterns. Auto-filters rejections older than 90 days.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..schemas import SuggestionRejectionEntry

logger = logging.getLogger(__name__)


class RejectionTracker:
    """
    Tracks suggestion rejections in JSONL format with 90-day expiry.

    Storage: ~/.claude/learning/suggestion_rejections.jsonl
    Format: One JSON object per line, append-only

    Features:
    - 90-day auto-expiry on read
    - In-memory cache for performance
    - Simple fingerprinting for exact matching
    """

    def __init__(self, storage_dir: Path | None = None):
        """
        Initialize rejection tracker.

        Args:
            storage_dir: Directory for learning data (default: ~/.claude/learning/)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".claude" / "learning"

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.rejections_file = storage_dir / "suggestion_rejections.jsonl"
        self._cache: list[SuggestionRejectionEntry] | None = None
        self._cache_timestamp: datetime | None = None
        self._cache_ttl_seconds = 60  # Cache for 1 minute

    def log_rejection(
        self,
        suggestion_type: str,
        suggestion_fingerprint: str,
        project_path: str = "",
    ) -> None:
        """
        Log a suggestion rejection.

        Args:
            suggestion_type: Type of suggestion ('workflow', 'permission', 'mcp', or 'context')
            suggestion_fingerprint: Unique identifier for the suggestion
            project_path: Project where rejection occurred
        """
        entry = SuggestionRejectionEntry(
            timestamp=datetime.now(),
            suggestion_type=suggestion_type,
            suggestion_fingerprint=suggestion_fingerprint,
            project_path=project_path,
        )

        # Append to JSONL file
        try:
            with open(self.rejections_file, "a", encoding="utf-8") as f:
                json_line = entry.model_dump_json()
                f.write(json_line + "\n")

            logger.debug(
                f"Logged rejection: {suggestion_type}:{suggestion_fingerprint}"
            )

            # Invalidate cache
            self._cache = None

        except Exception as e:
            logger.error(f"Failed to log rejection: {e}")

    def get_recent_rejections(
        self, days: int = 90, suggestion_type: str | None = None
    ) -> list[SuggestionRejectionEntry]:
        """
        Get recent rejections with auto-filtering of old entries.

        Args:
            days: Number of days to look back (default 90)
            suggestion_type: Filter by type ('workflow', 'permission', 'mcp', 'context', or None for all)

        Returns:
            List of rejection entries, newest first
        """
        # Check cache first
        if self._is_cache_valid():
            return self._filter_cached(days, suggestion_type)

        # Load from disk
        if not self.rejections_file.exists():
            self._cache = []
            self._cache_timestamp = datetime.now()
            return []

        cutoff = datetime.now(UTC) - timedelta(days=days)
        rejections = []

        try:
            with open(self.rejections_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    data = json.loads(line)
                    entry = SuggestionRejectionEntry(**data)

                    # Make timestamp timezone-aware if naive
                    if entry.timestamp.tzinfo is None:
                        entry.timestamp = entry.timestamp.replace(tzinfo=UTC)

                    # Auto-filter old entries
                    if entry.timestamp < cutoff:
                        continue

                    # Filter by type if specified
                    if suggestion_type and entry.suggestion_type != suggestion_type:
                        continue

                    rejections.append(entry)

        except Exception as e:
            logger.error(f"Failed to read rejections: {e}")
            return []

        # Update cache
        self._cache = rejections
        self._cache_timestamp = datetime.now()

        # Sort newest first
        rejections.sort(key=lambda e: e.timestamp, reverse=True)
        return rejections

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache is None or self._cache_timestamp is None:
            return False

        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl_seconds

    def _filter_cached(
        self, days: int, suggestion_type: str | None
    ) -> list[SuggestionRejectionEntry]:
        """Filter cached results."""
        if self._cache is None:
            return []

        cutoff = datetime.now(UTC) - timedelta(days=days)
        filtered = [
            r
            for r in self._cache
            if r.timestamp >= cutoff
            and (suggestion_type is None or r.suggestion_type == suggestion_type)
        ]
        return filtered

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about rejection history.

        Returns:
            Dictionary with statistics
        """
        rejections_90d = self.get_recent_rejections(days=90)
        rejections_30d = self.get_recent_rejections(days=30)

        workflow_rejections = [
            r for r in rejections_90d if r.suggestion_type == "workflow"
        ]
        permission_rejections = [
            r for r in rejections_90d if r.suggestion_type == "permission"
        ]
        mcp_rejections = [r for r in rejections_90d if r.suggestion_type == "mcp"]
        context_rejections = [
            r for r in rejections_90d if r.suggestion_type == "context"
        ]

        return {
            "total_rejections_90d": len(rejections_90d),
            "total_rejections_30d": len(rejections_30d),
            "workflow_rejections_90d": len(workflow_rejections),
            "permission_rejections_90d": len(permission_rejections),
            "mcp_rejections_90d": len(mcp_rejections),
            "context_rejections_90d": len(context_rejections),
            "storage_file": str(self.rejections_file),
            "storage_exists": self.rejections_file.exists(),
        }
