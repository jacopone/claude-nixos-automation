"""
Unit tests for ApprovalTracker.

Tests the permission approval logging and retrieval functionality.
"""

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from claude_automation.analyzers import ApprovalTracker
from claude_automation.schemas import PermissionApprovalEntry


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def tracker(temp_storage):
    """Create ApprovalTracker with temporary storage."""
    return ApprovalTracker(storage_dir=temp_storage)


class TestApprovalLogging:
    """Test approval logging functionality (T032)."""

    def test_log_approval_creates_file(self, tracker):
        """Verify log_approval creates JSONL file."""
        # Arrange
        permission = "Read(//home/user/project/**)"
        session_id = "test-session-123"
        project_path = "/home/user/project"

        # Act
        tracker.log_approval(permission, session_id, project_path)

        # Assert
        assert tracker.approvals_file.exists()

    def test_log_approval_appends_to_file(self, tracker):
        """Verify log_approval appends entries."""
        # Arrange
        permission1 = "Read(//home/user/project/**)"
        permission2 = "Bash(git status:*)"
        session_id = "test-session-123"
        project_path = "/home/user/project"

        # Act
        tracker.log_approval(permission1, session_id, project_path)
        tracker.log_approval(permission2, session_id, project_path)

        # Assert
        with open(tracker.approvals_file) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_log_approval_stores_correct_data(self, tracker):
        """Verify logged data matches input."""
        # Arrange
        permission = "Read(//home/user/project/**)"
        session_id = "test-session-123"
        project_path = "/home/user/project"
        context = {"tool": "Read", "path": "/home/user/project/file.py"}

        # Act
        tracker.log_approval(permission, session_id, project_path, context)

        # Assert
        with open(tracker.approvals_file) as f:
            line = f.readline()
        data = json.loads(line)

        assert data["permission"] == permission
        assert data["session_id"] == session_id
        assert data["project_path"] == project_path
        assert data["context"] == context
        assert "timestamp" in data

    def test_log_approval_handles_missing_context(self, tracker):
        """Verify log_approval works without context."""
        # Arrange
        permission = "Read(//home/user/project/**)"
        session_id = "test-session-123"
        project_path = "/home/user/project"

        # Act
        tracker.log_approval(permission, session_id, project_path)

        # Assert
        with open(tracker.approvals_file) as f:
            line = f.readline()
        data = json.loads(line)

        assert data["context"] == {}

    def test_log_approval_multiple_projects(self, tracker):
        """Verify tracking approvals across multiple projects."""
        # Arrange
        permission = "Read(//home/user/**)"
        session_id = "test-session-123"
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"

        # Act
        tracker.log_approval(permission, session_id, project1)
        tracker.log_approval(permission, session_id, project2)

        # Assert
        approvals = tracker.get_recent_approvals(days=30)
        assert len(approvals) == 2
        assert {a.project_path for a in approvals} == {project1, project2}


class TestApprovalRetrieval:
    """Test approval retrieval functionality (T032)."""

    def test_get_recent_approvals_empty_when_no_file(self, tracker):
        """Verify get_recent_approvals returns empty list when no approvals."""
        # Act
        approvals = tracker.get_recent_approvals(days=30)

        # Assert
        assert approvals == []

    def test_get_recent_approvals_filters_by_date(self, tracker):
        """Verify get_recent_approvals filters by date window."""
        # Arrange - Log approvals at different times
        permission = "Read(//home/user/project/**)"
        session_id = "test-session"
        project_path = "/home/user/project"

        # Recent approval (within 30 days)
        tracker.log_approval(permission, session_id, project_path)

        # Old approval (manually create old entry)
        old_entry = PermissionApprovalEntry(
            timestamp=datetime.now(UTC) - timedelta(days=35),
            permission=permission,
            session_id=session_id,
            project_path=project_path,
            context={},
        )
        with open(tracker.approvals_file, "a") as f:
            f.write(old_entry.model_dump_json() + "\n")

        # Act
        approvals_30d = tracker.get_recent_approvals(days=30)
        approvals_40d = tracker.get_recent_approvals(days=40)

        # Assert
        assert len(approvals_30d) == 1  # Only recent approval
        assert len(approvals_40d) == 2  # Both approvals

    def test_get_recent_approvals_filters_by_project(self, tracker):
        """Verify get_recent_approvals filters by project path."""
        # Arrange
        permission = "Read(**)"
        session_id = "test-session"
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"

        tracker.log_approval(permission, session_id, project1)
        tracker.log_approval(permission, session_id, project1)
        tracker.log_approval(permission, session_id, project2)

        # Act
        approvals_all = tracker.get_recent_approvals(days=30)
        approvals_project1 = tracker.get_recent_approvals(
            days=30, project_path=project1
        )
        approvals_project2 = tracker.get_recent_approvals(
            days=30, project_path=project2
        )

        # Assert
        assert len(approvals_all) == 3
        assert len(approvals_project1) == 2
        assert len(approvals_project2) == 1

    def test_get_recent_approvals_sorts_newest_first(self, tracker):
        """Verify approvals are sorted newest first."""
        # Arrange
        permission = "Read(**)"
        session_id = "test-session"
        project_path = "/home/user/project"

        # Log multiple approvals with small delays
        tracker.log_approval(f"{permission}-1", session_id, project_path)
        tracker.log_approval(f"{permission}-2", session_id, project_path)
        tracker.log_approval(f"{permission}-3", session_id, project_path)

        # Act
        approvals = tracker.get_recent_approvals(days=30)

        # Assert
        assert len(approvals) == 3
        # Newest first
        assert approvals[0].permission == f"{permission}-3"
        assert approvals[1].permission == f"{permission}-2"
        assert approvals[2].permission == f"{permission}-1"

    def test_get_approval_count(self, tracker):
        """Verify get_approval_count returns correct count."""
        # Arrange
        permission = "Read(//home/user/project/**)"
        other_permission = "Bash(git status:*)"
        session_id = "test-session"
        project_path = "/home/user/project"

        tracker.log_approval(permission, session_id, project_path)
        tracker.log_approval(permission, session_id, project_path)
        tracker.log_approval(permission, session_id, project_path)
        tracker.log_approval(other_permission, session_id, project_path)

        # Act
        count = tracker.get_approval_count(permission, days=30)
        other_count = tracker.get_approval_count(other_permission, days=30)

        # Assert
        assert count == 3
        assert other_count == 1

    def test_get_all_unique_permissions(self, tracker):
        """Verify get_all_unique_permissions returns unique set."""
        # Arrange
        perm1 = "Read(//home/user/project/**)"
        perm2 = "Bash(git status:*)"
        perm3 = "Write(//home/user/project/file.txt)"
        session_id = "test-session"
        project_path = "/home/user/project"

        tracker.log_approval(perm1, session_id, project_path)
        tracker.log_approval(perm1, session_id, project_path)  # Duplicate
        tracker.log_approval(perm2, session_id, project_path)
        tracker.log_approval(perm3, session_id, project_path)

        # Act
        unique_perms = tracker.get_all_unique_permissions(days=30)

        # Assert
        assert len(unique_perms) == 3
        assert unique_perms == {perm1, perm2, perm3}

    def test_get_approvals_by_project(self, tracker):
        """Verify get_approvals_by_project groups correctly."""
        # Arrange
        permission = "Read(**)"
        session_id = "test-session"
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"

        tracker.log_approval(permission, session_id, project1)
        tracker.log_approval(permission, session_id, project1)
        tracker.log_approval(permission, session_id, project2)

        # Act
        by_project = tracker.get_approvals_by_project(days=30)

        # Assert
        assert len(by_project) == 2
        assert len(by_project[project1]) == 2
        assert len(by_project[project2]) == 1

    def test_get_stats(self, tracker):
        """Verify get_stats returns correct statistics."""
        # Arrange
        permission = "Read(**)"
        session_id = "test-session"
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"

        tracker.log_approval(permission, session_id, project1)
        tracker.log_approval(f"{permission}-2", session_id, project2)

        # Act
        stats = tracker.get_stats()

        # Assert
        assert stats["total_approvals_30d"] == 2
        assert stats["total_approvals_7d"] == 2
        assert stats["unique_permissions_30d"] == 2
        assert stats["unique_projects_30d"] == 2
        assert stats["storage_exists"] is True


class TestApprovalMaintenance:
    """Test approval cleanup functionality (T032)."""

    def test_clear_old_approvals_removes_old_entries(self, tracker):
        """Verify clear_old_approvals removes entries older than threshold."""
        # Arrange
        permission = "Read(**)"
        session_id = "test-session"
        project_path = "/home/user/project"

        # Create old entry (100 days ago)
        old_entry = PermissionApprovalEntry(
            timestamp=datetime.now(UTC) - timedelta(days=100),
            permission=permission,
            session_id=session_id,
            project_path=project_path,
            context={},
        )
        with open(tracker.approvals_file, "a") as f:
            f.write(old_entry.model_dump_json() + "\n")

        # Create recent entry
        tracker.log_approval(permission, session_id, project_path)

        # Act
        removed_count = tracker.clear_old_approvals(days=90)

        # Assert
        assert removed_count == 1
        approvals = tracker.get_recent_approvals(days=365)
        assert len(approvals) == 1  # Only recent entry remains

    def test_clear_old_approvals_keeps_recent_entries(self, tracker):
        """Verify clear_old_approvals keeps recent entries."""
        # Arrange
        permission = "Read(**)"
        session_id = "test-session"
        project_path = "/home/user/project"

        tracker.log_approval(permission, session_id, project_path)
        tracker.log_approval(f"{permission}-2", session_id, project_path)

        # Act
        removed_count = tracker.clear_old_approvals(days=90)

        # Assert
        assert removed_count == 0
        approvals = tracker.get_recent_approvals(days=30)
        assert len(approvals) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
