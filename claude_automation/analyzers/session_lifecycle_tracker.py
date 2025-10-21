"""
Session Lifecycle Tracker - Manages lifecycle stages of Claude Code sessions.

This is a Tier 1 analyzer that tracks session value extraction progress to
enable safe, value-based cleanup decisions.

Phase 2: Lifecycle tracking and metadata management.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from claude_automation.analyzers.base_analyzer import BaseAnalyzer
from claude_automation.schemas.lifecycle import (
    LifecycleStats,
    SessionLifecycle,
    SessionMetadata,
)

logger = logging.getLogger(__name__)


class SessionLifecycleTracker(BaseAnalyzer):
    """
    Track lifecycle stages of Claude Code sessions.

    Manages lifecycle metadata stored as sidecar files alongside session logs:
    - session.jsonl → session.jsonl.lifecycle.json

    Enables value-based cleanup: only delete sessions marked as IMPLEMENTED.
    """

    def __init__(self, projects_dir: Path | None = None, **kwargs):
        """
        Initialize session lifecycle tracker.

        Args:
            projects_dir: Path to projects directory (default: ~/.claude/projects)
            **kwargs: Optional parameters (for future extension)
        """
        super().__init__(**kwargs)

        self.projects_dir = (
            projects_dir if projects_dir else Path.home() / ".claude" / "projects"
        )

    def _get_analysis_method_name(self) -> str:
        """Return the primary analysis method name."""
        return "get_lifecycle_stats"

    def _get_metadata_path(self, session_file: Path) -> Path:
        """
        Get path to lifecycle metadata file for a session.

        Args:
            session_file: Path to session .jsonl file

        Returns:
            Path to sidecar metadata file
        """
        return session_file.parent / f"{session_file.name}.lifecycle.json"

    def load_metadata(self, session_file: Path) -> SessionMetadata:
        """
        Load lifecycle metadata for a session.

        If no metadata file exists, creates default metadata (RAW stage).

        Args:
            session_file: Path to session .jsonl file

        Returns:
            SessionMetadata for the session
        """
        metadata_path = self._get_metadata_path(session_file)

        if metadata_path.exists():
            try:
                with open(metadata_path, encoding="utf-8") as f:
                    data = json.load(f)
                    # Parse datetime strings
                    for field in ["created_at", "analyzed_at", "insights_generated_at", "implemented_at"]:
                        if data.get(field):
                            data[field] = datetime.fromisoformat(data[field])
                    return SessionMetadata(**data)
            except Exception as e:
                logger.warning(f"Could not load metadata for {session_file.name}: {e}")

        # Create default metadata if none exists
        return SessionMetadata(
            session_file=str(session_file),
            lifecycle_stage=SessionLifecycle.RAW,
            created_at=datetime.fromtimestamp(session_file.stat().st_ctime),
        )

    def save_metadata(self, metadata: SessionMetadata) -> None:
        """
        Save lifecycle metadata for a session.

        Args:
            metadata: SessionMetadata to save
        """
        session_file = Path(metadata.session_file)
        metadata_path = self._get_metadata_path(session_file)

        try:
            # Ensure parent directory exists
            metadata_path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize with ISO timestamps
            data = metadata.model_dump()
            for field in ["created_at", "analyzed_at", "insights_generated_at", "implemented_at"]:
                if data.get(field):
                    data[field] = data[field].isoformat()

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved metadata for {session_file.name}: {metadata.lifecycle_stage.value}")

        except Exception as e:
            logger.warning(f"Could not save metadata for {session_file.name}: {e}")

    def mark_session(
        self,
        session_file: Path,
        stage: SessionLifecycle,
        notes: str | None = None
    ) -> SessionMetadata:
        """
        Mark a session at a specific lifecycle stage.

        Args:
            session_file: Path to session .jsonl file
            stage: Lifecycle stage to set
            notes: Optional notes about this transition

        Returns:
            Updated SessionMetadata
        """
        metadata = self.load_metadata(session_file)
        metadata.lifecycle_stage = stage

        # Update timestamp for this stage
        now = datetime.now()
        if stage == SessionLifecycle.ANALYZED:
            metadata.analyzed_at = now
        elif stage == SessionLifecycle.INSIGHTS_GENERATED:
            metadata.insights_generated_at = now
            if notes:
                metadata.insights_summary = notes
        elif stage == SessionLifecycle.IMPLEMENTED:
            metadata.implemented_at = now
            if notes:
                metadata.implementation_notes = notes

        self.save_metadata(metadata)
        return metadata

    def get_all_sessions(self) -> list[tuple[Path, SessionMetadata]]:
        """
        Get all sessions with their lifecycle metadata.

        Returns:
            List of (session_file, metadata) tuples
        """
        if not self.projects_dir.exists():
            logger.debug(f"Projects directory not found: {self.projects_dir}")
            return []

        sessions = []

        try:
            for session_file in self.projects_dir.rglob("*.jsonl"):
                if session_file.is_file():
                    metadata = self.load_metadata(session_file)
                    sessions.append((session_file, metadata))
        except Exception as e:
            logger.warning(f"Error scanning sessions: {e}")

        return sessions

    def get_sessions_by_stage(self, stage: SessionLifecycle) -> list[tuple[Path, SessionMetadata]]:
        """
        Get all sessions at a specific lifecycle stage.

        Args:
            stage: Lifecycle stage to filter by

        Returns:
            List of (session_file, metadata) tuples for matching sessions
        """
        all_sessions = self.get_all_sessions()
        return [(path, meta) for path, meta in all_sessions if meta.lifecycle_stage == stage]

    def get_lifecycle_stats(self) -> LifecycleStats:
        """
        Get statistics about session lifecycle distribution.

        Returns:
            LifecycleStats with counts for each stage
        """
        all_sessions = self.get_all_sessions()

        raw_count = 0
        analyzed_count = 0
        insights_generated_count = 0
        implemented_count = 0

        for _, metadata in all_sessions:
            if metadata.lifecycle_stage == SessionLifecycle.RAW:
                raw_count += 1
            elif metadata.lifecycle_stage == SessionLifecycle.ANALYZED:
                analyzed_count += 1
            elif metadata.lifecycle_stage == SessionLifecycle.INSIGHTS_GENERATED:
                insights_generated_count += 1
            elif metadata.lifecycle_stage == SessionLifecycle.IMPLEMENTED:
                implemented_count += 1

        return LifecycleStats(
            total_sessions=len(all_sessions),
            raw_count=raw_count,
            analyzed_count=analyzed_count,
            insights_generated_count=insights_generated_count,
            implemented_count=implemented_count,
        )

    def get_safe_to_cleanup_sessions(self) -> list[Path]:
        """
        Get sessions that are safe to cleanup (IMPLEMENTED stage).

        Returns:
            List of session file paths safe to delete
        """
        implemented_sessions = self.get_sessions_by_stage(SessionLifecycle.IMPLEMENTED)
        return [path for path, _ in implemented_sessions]

    def get_valuable_sessions(self) -> list[tuple[Path, SessionMetadata]]:
        """
        Get sessions that still have value to extract (not IMPLEMENTED).

        Returns:
            List of (session_file, metadata) tuples for valuable sessions
        """
        all_sessions = self.get_all_sessions()
        return [(path, meta) for path, meta in all_sessions if meta.has_value]
