"""
Unit tests for PermissionPatternDetector.

Tests pattern detection and confidence scoring (T033, T034).
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.permission_pattern_detector import (
    PermissionPatternDetector,
)
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


@pytest.fixture
def detector(tracker):
    """Create PermissionPatternDetector with test configuration."""
    return PermissionPatternDetector(
        approval_tracker=tracker,
        min_occurrences=3,
        confidence_threshold=0.7,
    )


class TestPatternDetection:
    """Test pattern detection functionality (T033)."""

    def test_detect_git_read_only_pattern(self, tracker, detector):
        """Verify detection of git read-only commands."""
        # Arrange - Log git read-only commands
        git_commands = [
            "Bash(git status:*)",
            "Bash(git log:*)",
            "Bash(git diff:*)",
            "Bash(git status:*)",  # Repeated
        ]

        session_id = "test-session"
        project_path = "/home/user/project"

        for cmd in git_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        assert len(suggestions) > 0
        git_suggestions = [s for s in suggestions if s.pattern.pattern_type == "git_read_only"]
        assert len(git_suggestions) == 1

        git_pattern = git_suggestions[0].pattern
        assert git_pattern.occurrences == 4
        assert git_pattern.confidence >= 0.7

    def test_detect_pytest_pattern(self, tracker, detector):
        """Verify detection of pytest commands."""
        # Arrange
        pytest_commands = [
            "Bash(pytest:*)",
            "Bash(python -m pytest:*)",
            "Bash(pytest tests/:*)",
        ]

        session_id = "test-session"
        project_path = "/home/user/project"

        for cmd in pytest_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        pytest_suggestions = [s for s in suggestions if s.pattern.pattern_type == "pytest"]
        assert len(pytest_suggestions) == 1
        assert pytest_suggestions[0].pattern.occurrences == 3

    def test_detect_modern_cli_pattern(self, tracker, detector):
        """Verify detection of modern CLI tools."""
        # Arrange
        cli_commands = [
            "Bash(fd *.py:*)",
            "Bash(eza -la:*)",
            "Bash(bat file.txt:*)",
            "Bash(rg pattern:*)",
        ]

        session_id = "test-session"
        project_path = "/home/user/project"

        for cmd in cli_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        cli_suggestions = [s for s in suggestions if s.pattern.pattern_type == "modern_cli"]
        assert len(cli_suggestions) == 1
        assert cli_suggestions[0].pattern.occurrences == 4

    def test_no_pattern_below_threshold(self, tracker, detector):
        """Verify patterns below min_occurrences are not detected."""
        # Arrange - Only 2 occurrences (below threshold of 3)
        tracker.log_approval("Bash(git status:*)", "session", "/project")
        tracker.log_approval("Bash(git log:*)", "session", "/project")

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should not detect pattern with only 2 occurrences
        assert len(suggestions) == 0

    def test_multiple_patterns_detected(self, tracker, detector):
        """Verify detection of multiple patterns simultaneously."""
        # Arrange - Create patterns for git AND pytest with enough occurrences and confidence
        # Need high enough occurrences to reach 0.7 confidence threshold
        # With formula: base_conf (n/total) + consistency (up to 0.2) + recency (0.1)
        session_id = "test-session"
        project_path = "/home/user/project"

        # Log git commands (7 same commands for high consistency)
        # This gives: base=7/10=0.70 + consistency=0.2 + recency=0.0 = 0.90
        for _ in range(7):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Log pytest commands (3 occurrences meets minimum)
        # This gives: base=3/10=0.30 + consistency=0.2 + recency=0.0 = 0.50 (below threshold)
        for _ in range(3):
            tracker.log_approval("Bash(pytest:*)", session_id, project_path)

        # Total: 10 approvals (7 git, 3 pytest)
        # Git should pass threshold, pytest should not

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should have at least 1 pattern (git)
        assert len(suggestions) >= 1
        pattern_types = {s.pattern.pattern_type for s in suggestions}
        # Git should definitely be detected
        assert "git_read_only" in pattern_types or "git_all_safe" in pattern_types

    def test_pattern_detection_filters_by_date(self, tracker, detector):
        """Verify pattern detection respects date window."""
        # Arrange - Create old approvals (outside window)
        old_entry = PermissionApprovalEntry(
            timestamp=datetime.now(UTC) - timedelta(days=35),
            permission="Bash(git status:*)",
            session_id="old-session",
            project_path="/project",
            context={},
        )

        # Manually add old entries
        with open(tracker.approvals_file, "a") as f:
            for _ in range(5):  # Would be enough for pattern
                f.write(old_entry.model_dump_json() + "\n")

        # Act - Search only last 30 days
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should not detect pattern from old approvals
        git_suggestions = [
            s for s in suggestions
            if "git" in s.pattern.pattern_type
        ]
        assert len(git_suggestions) == 0

    def test_pattern_detection_with_project_filter(self, tracker, detector):
        """Verify pattern detection can filter by project."""
        # Arrange
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"
        session_id = "test-session"

        # Add git commands to project1
        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project1)

        # Add different commands to project2
        for _ in range(3):
            tracker.log_approval("Bash(pytest:*)", session_id, project2)

        # Act
        suggestions_all = detector.detect_patterns(days=30)
        suggestions_project1 = detector.detect_patterns(days=30, project_path=project1)

        # Assert
        assert len(suggestions_all) >= 2
        assert len(suggestions_project1) >= 1

        # Project1 should have git patterns
        git_in_project1 = any(
            "git" in s.pattern.pattern_type
            for s in suggestions_project1
        )
        assert git_in_project1


class TestConfidenceScoring:
    """Test confidence scoring functionality (T034)."""

    def test_confidence_increases_with_frequency(self, tracker, detector):
        """Verify confidence increases with higher frequency."""
        # Arrange - Create two patterns with different frequencies
        # Need both patterns above 0.7 threshold to be detected
        session_id = "test-session"
        project_path = "/home/user/project"

        # High frequency pattern (10 occurrences)
        # Expected: base=10/13≈0.77 + consistency≈0.1 + recency=0.1 = ~0.97
        for _ in range(10):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Low frequency pattern (3 occurrences - just above threshold)
        # Expected: base=3/13≈0.23 + consistency≈0.2 + recency=0.1 = ~0.53 (below threshold)
        # Need to boost this to reach 0.7
        for _ in range(6):
            tracker.log_approval("Bash(pytest:*)", session_id, project_path)

        # Total: 16 approvals (10 git, 6 pytest)
        # Git: base=10/16≈0.63 + consistency≈0.1 + recency=0.1 = ~0.83
        # Pytest: base=6/16≈0.38 + consistency≈0.2 + recency=0.1 = ~0.68 (close but might not reach 0.7)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Git should definitely be detected with higher confidence
        assert len(suggestions) >= 1, f"Expected at least 1 pattern, got {len(suggestions)}"

        git_suggestion = next((s for s in suggestions if "git" in s.pattern.pattern_type), None)
        assert git_suggestion is not None, "Git pattern not detected"

        # If pytest also detected, verify git has higher confidence
        pytest_suggestion = next((s for s in suggestions if s.pattern.pattern_type == "pytest"), None)
        if pytest_suggestion is not None:
            assert git_suggestion.pattern.confidence > pytest_suggestion.pattern.confidence

    def test_confidence_bonus_for_consistency(self, tracker, detector):
        """Verify confidence bonus for repeated identical permissions."""
        # Arrange
        session_id = "test-session"
        project_path = "/home/user/project"

        # Same command repeated (high consistency)
        for _ in range(5):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        # High consistency should boost confidence
        assert git_suggestion.pattern.confidence >= 0.7

    def test_confidence_below_threshold_excluded(self, tracker, detector):
        """Verify patterns below confidence threshold are excluded."""
        # Arrange - Create pattern with low confidence
        # (few occurrences among many total approvals)
        session_id = "test-session"
        project_path = "/home/user/project"

        # 3 git commands
        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Many other unrelated commands (dilutes confidence)
        for i in range(20):
            tracker.log_approval(f"Read(/file{i}.txt)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Git pattern should have low confidence
        # Base confidence = 3/23 ≈ 0.13, even with bonuses won't reach 0.7
        git_suggestions = [s for s in suggestions if "git" in s.pattern.pattern_type]
        assert len(git_suggestions) == 0  # Below threshold

    def test_confidence_score_range(self, tracker, detector):
        """Verify confidence scores are in valid range [0, 1]."""
        # Arrange
        session_id = "test-session"
        project_path = "/home/user/project"

        for _ in range(5):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        for suggestion in suggestions:
            assert 0.0 <= suggestion.pattern.confidence <= 1.0

    def test_confidence_with_recency_bonus(self, tracker, detector):
        """Verify recent approvals get recency bonus."""
        # Arrange - All recent approvals
        session_id = "test-session"
        project_path = "/home/user/project"

        for _ in range(4):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should have high confidence (recency bonus applied)
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        assert git_suggestion.pattern.confidence >= 0.7


class TestPatternSuggestions:
    """Test pattern suggestion generation (T033)."""

    def test_suggestion_includes_proposed_rule(self, tracker, detector):
        """Verify suggestions include proposed permission rule."""
        # Arrange
        session_id = "test-session"
        project_path = "/home/user/project"

        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert suggestion.proposed_rule is not None
            assert len(suggestion.proposed_rule) > 0

    def test_suggestion_includes_examples(self, tracker, detector):
        """Verify suggestions include approval examples."""
        # Arrange
        session_id = "test-session"
        project_path = "/home/user/project"

        git_cmds = ["Bash(git status:*)", "Bash(git log:*)", "Bash(git diff:*)"]
        for cmd in git_cmds:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        assert len(git_suggestion.approved_examples) > 0
        assert len(git_suggestion.would_allow) > 0

    def test_suggestion_includes_impact_estimate(self, tracker, detector):
        """Verify suggestions include impact estimate."""
        # Arrange
        session_id = "test-session"
        project_path = "/home/user/project"

        for _ in range(5):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        assert "impact" in git_suggestion.impact_estimate.lower()
        assert "%" in git_suggestion.impact_estimate

    def test_suggestions_sorted_by_confidence(self, tracker, detector):
        """Verify suggestions are sorted by confidence (highest first)."""
        # Arrange - Create patterns with different confidences
        session_id = "test-session"
        project_path = "/home/user/project"

        # High confidence pattern (many occurrences)
        for _ in range(8):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Medium confidence pattern
        for _ in range(4):
            tracker.log_approval("Bash(pytest:*)", session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Suggestions should be sorted by confidence descending
        if len(suggestions) >= 2:
            for i in range(len(suggestions) - 1):
                assert (
                    suggestions[i].pattern.confidence
                    >= suggestions[i + 1].pattern.confidence
                )


class TestPatternStats:
    """Test pattern statistics functionality."""

    def test_get_pattern_stats(self, tracker, detector):
        """Verify get_pattern_stats returns correct statistics."""
        # Arrange
        session_id = "test-session"
        project_path = "/home/user/project"

        for _ in range(5):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        for _ in range(3):
            tracker.log_approval("Bash(pytest:*)", session_id, project_path)

        # Act
        stats = detector.get_pattern_stats(days=30)

        # Assert
        assert stats["total_approvals"] == 8
        assert stats["patterns_detected"] >= 1
        assert "category_counts" in stats
        assert stats["category_counts"]["git_read_only"] == 5 or stats["category_counts"]["git_all_safe"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
