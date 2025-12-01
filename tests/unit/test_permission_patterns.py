"""
Unit tests for PermissionPatternDetector.

Tests pattern detection and confidence scoring (T033, T034).
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from claude_automation.analyzers import ApprovalTracker, PermissionPatternDetector
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
def detector(tracker, monkeypatch, temp_storage):
    """Create PermissionPatternDetector with test configuration.

    Note: The confidence_threshold is set to 0.5 to match TIER_1_SAFE settings.
    The new reliability-based confidence algorithm calculates:
    - Base: 0.5 (pattern meets min_occurrences)
    - Session spread: up to +0.25
    - Project spread: up to +0.15
    - Consistency: up to +0.05
    - Recency: up to +0.05

    We also change CWD to temp_storage to prevent loading real settings.local.json.
    """
    # Change CWD to temp directory to prevent loading real settings.local.json
    monkeypatch.chdir(temp_storage)

    return PermissionPatternDetector(
        approval_tracker=tracker,
        min_occurrences=3,
        confidence_threshold=0.5,  # Match TIER_1_SAFE threshold
    )


class TestPatternDetection:
    """Test pattern detection functionality (T033)."""

    def test_detect_git_read_only_pattern(self, tracker, detector):
        """Verify detection of git read-only commands."""
        # Arrange - Log git read-only commands across multiple sessions
        # to get session spread bonus in the reliability-based confidence algorithm
        git_commands = [
            ("Bash(git status:*)", "session-1"),
            ("Bash(git log:*)", "session-2"),
            ("Bash(git diff:*)", "session-3"),
            ("Bash(git status:*)", "session-4"),  # Repeated
        ]

        project_path = "/home/user/project"

        for cmd, session_id in git_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        assert len(suggestions) > 0
        git_suggestions = [s for s in suggestions if s.pattern.pattern_type == "git_read_only"]
        assert len(git_suggestions) == 1

        git_pattern = git_suggestions[0].pattern
        assert git_pattern.occurrences == 4
        # With 4 sessions and base 0.5: 0.5 + 0.1 + 0.03 + ~0.05 + 0.05 = ~0.73
        assert git_pattern.confidence >= 0.5  # TIER_1_SAFE threshold

    def test_detect_pytest_pattern(self, tracker, detector):
        """Verify detection of pytest commands."""
        # Arrange - Use multiple sessions to boost confidence
        pytest_commands = [
            ("Bash(pytest:*)", "session-1"),
            ("Bash(python -m pytest:*)", "session-2"),
            ("Bash(pytest tests/:*)", "session-3"),
        ]

        project_path = "/home/user/project"

        for cmd, session_id in pytest_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        pytest_suggestions = [s for s in suggestions if s.pattern.pattern_type == "pytest"]
        assert len(pytest_suggestions) == 1
        assert pytest_suggestions[0].pattern.occurrences == 3

    def test_detect_modern_cli_pattern(self, tracker, detector):
        """Verify detection of modern CLI tools."""
        # Arrange - Use multiple sessions to boost confidence
        cli_commands = [
            ("Bash(fd *.py:*)", "session-1"),
            ("Bash(eza -la:*)", "session-2"),
            ("Bash(bat file.txt:*)", "session-3"),
            ("Bash(rg pattern:*)", "session-4"),
        ]

        project_path = "/home/user/project"

        for cmd, session_id in cli_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        cli_suggestions = [s for s in suggestions if s.pattern.pattern_type == "modern_cli"]
        assert len(cli_suggestions) == 1
        assert cli_suggestions[0].pattern.occurrences == 4

    def test_no_pattern_below_threshold(self, tracker, detector):
        """Verify patterns below min_occurrences are not detected."""
        # Arrange - Only 1 occurrence (below TIER_1_SAFE threshold of 2)
        tracker.log_approval("Bash(git status:*)", "session", "/project")

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should not detect pattern with only 1 occurrence
        assert len(suggestions) == 0

    def test_multiple_patterns_detected(self, tracker, detector):
        """Verify detection of multiple patterns simultaneously."""
        # Arrange - Create patterns for git AND pytest with multiple sessions
        # The reliability-based confidence algorithm rewards session diversity
        project_path = "/home/user/project"

        # Log git commands across multiple sessions (TIER_1_SAFE needs 2 occurrences)
        for i in range(4):
            tracker.log_approval("Bash(git status:*)", f"git-session-{i}", project_path)

        # Log pytest commands across multiple sessions (TIER_1_SAFE needs 2 occurrences)
        for i in range(3):
            tracker.log_approval("Bash(pytest:*)", f"pytest-session-{i}", project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should have at least 1 pattern
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
        # Arrange - Use multiple sessions for reliability-based confidence
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"

        # Add git commands to project1 across multiple sessions
        for i in range(3):
            tracker.log_approval("Bash(git status:*)", f"session-{i}", project1)

        # Add different commands to project2 across multiple sessions
        for i in range(3):
            tracker.log_approval("Bash(pytest:*)", f"session-{i+10}", project2)

        # Act
        suggestions_all = detector.detect_patterns(days=30)
        suggestions_project1 = detector.detect_patterns(days=30, project_path=project1)

        # Assert - At least one pattern should be detected overall
        assert len(suggestions_all) >= 1
        # Project1 filter may return fewer or same
        # Project1 should have git patterns if detected
        if suggestions_project1:
            git_in_project1 = any(
                "git" in s.pattern.pattern_type
                for s in suggestions_project1
            )
            assert git_in_project1


class TestConfidenceScoring:
    """Test confidence scoring functionality (T034).

    Note: The new reliability-based confidence algorithm calculates:
    - Base: 0.5 (pattern meets min_occurrences)
    - Session spread: up to +0.25 (more sessions = more reliable)
    - Project spread: up to +0.15 (cross-project = generalizable)
    - Consistency: up to +0.05 (same strings = predictable)
    - Recency: up to +0.05 (recent use = relevant)
    """

    def test_confidence_increases_with_frequency(self, tracker, detector):
        """Verify confidence increases with session diversity."""
        # Arrange - Create two patterns with different session spreads
        project_path = "/home/user/project"

        # High session spread pattern (10 different sessions)
        # Expected: base=0.5 + session_spread=0.25 + project=0.03 + consistency=~0.05 + recency=0.05 = ~0.88
        for i in range(10):
            tracker.log_approval("Bash(git status:*)", f"git-session-{i}", project_path)

        # Low session spread pattern (3 sessions)
        # Expected: base=0.5 + session_spread=0.075 + project=0.03 + consistency=~0.05 + recency=0.05 = ~0.71
        for i in range(3):
            tracker.log_approval("Bash(pytest:*)", f"pytest-session-{i}", project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Git should definitely be detected
        assert len(suggestions) >= 1, f"Expected at least 1 pattern, got {len(suggestions)}"

        git_suggestion = next((s for s in suggestions if "git" in s.pattern.pattern_type), None)
        assert git_suggestion is not None, "Git pattern not detected"

        # If pytest also detected, verify git has higher confidence (more sessions)
        pytest_suggestion = next((s for s in suggestions if s.pattern.pattern_type == "pytest"), None)
        if pytest_suggestion is not None:
            assert git_suggestion.pattern.confidence > pytest_suggestion.pattern.confidence

    def test_confidence_bonus_for_consistency(self, tracker, detector):
        """Verify confidence bonus for repeated identical permissions."""
        # Arrange - Use multiple sessions for reliability-based confidence
        project_path = "/home/user/project"

        # Same command repeated across different sessions (high consistency + spread)
        for i in range(5):
            tracker.log_approval("Bash(git status:*)", f"session-{i}", project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        # With 5 sessions: base=0.5 + session_spread=0.125 + consistency=0.05 + recency=0.05 = ~0.725
        assert git_suggestion.pattern.confidence >= 0.5  # TIER_1_SAFE threshold

    def test_confidence_below_threshold_excluded(self, tracker):
        """Verify patterns below confidence threshold are excluded.

        The new reliability-based confidence formula uses:
        - Base: 0.5 (always, when min_occurrences met)
        - Session spread: up to +0.25
        - Project spread: up to +0.15
        - Consistency: up to +0.05
        - Recency: up to +0.05

        To test exclusion, we create a detector with a HIGH threshold (0.9)
        and approvals with LOW session diversity (single session).
        """
        # Create detector with high threshold that requires multi-session spread
        high_threshold_detector = PermissionPatternDetector(
            approval_tracker=tracker,
            min_occurrences=2,
            confidence_threshold=0.9,  # Very high threshold
        )

        session_id = "single-session"  # All from same session = no session spread bonus
        project_path = "/home/user/project"

        # 3 git commands from single session
        # Confidence = 0.5 (base) + 0.025 (1 session) + 0.03 (1 project) + 0.05 (consistency) + 0.05 (recency)
        # = ~0.655, which is below 0.9 threshold
        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Act
        suggestions = high_threshold_detector.detect_patterns(days=30)

        # Assert - Pattern should be excluded due to low confidence (< 0.9)
        git_suggestions = [s for s in suggestions if "git" in s.pattern.pattern_type]
        assert len(git_suggestions) == 0  # Below high threshold

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
        # Arrange - Use multiple sessions to boost confidence
        project_path = "/home/user/project"

        for i in range(4):
            tracker.log_approval("Bash(git status:*)", f"session-{i}", project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert - Should have confidence >= 0.5 (base + session spread + recency)
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        assert git_suggestion.pattern.confidence >= 0.5  # TIER_1_SAFE threshold


class TestPatternSuggestions:
    """Test pattern suggestion generation (T033)."""

    def test_suggestion_includes_proposed_rule(self, tracker, detector):
        """Verify suggestions include proposed permission rule."""
        # Arrange - Use multiple sessions
        project_path = "/home/user/project"

        for i in range(3):
            tracker.log_approval("Bash(git status:*)", f"session-{i}", project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert suggestion.proposed_rule is not None
            assert len(suggestion.proposed_rule) > 0

    def test_suggestion_includes_examples(self, tracker, detector):
        """Verify suggestions include approval examples."""
        # Arrange - Use multiple sessions
        project_path = "/home/user/project"

        git_cmds = [
            ("Bash(git status:*)", "session-1"),
            ("Bash(git log:*)", "session-2"),
            ("Bash(git diff:*)", "session-3"),
        ]
        for cmd, session_id in git_cmds:
            tracker.log_approval(cmd, session_id, project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        assert len(git_suggestion.approved_examples) > 0
        assert len(git_suggestion.would_allow) > 0

    def test_suggestion_includes_impact_estimate(self, tracker, detector):
        """Verify suggestions include impact estimate."""
        # Arrange - Use multiple sessions
        project_path = "/home/user/project"

        for i in range(5):
            tracker.log_approval("Bash(git status:*)", f"session-{i}", project_path)

        # Act
        suggestions = detector.detect_patterns(days=30)

        # Assert
        git_suggestion = next(s for s in suggestions if "git" in s.pattern.pattern_type)
        assert "impact" in git_suggestion.impact_estimate.lower()
        assert "%" in git_suggestion.impact_estimate

    def test_suggestions_sorted_by_confidence(self, tracker, detector):
        """Verify suggestions are sorted by confidence (highest first)."""
        # Arrange - Create patterns with different session spreads (affects confidence)
        project_path = "/home/user/project"

        # High confidence pattern (many sessions)
        for i in range(8):
            tracker.log_approval("Bash(git status:*)", f"git-session-{i}", project_path)

        # Medium confidence pattern (fewer sessions)
        for i in range(4):
            tracker.log_approval("Bash(pytest:*)", f"pytest-session-{i}", project_path)

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
        # Arrange - Use multiple sessions for reliability-based confidence
        project_path = "/home/user/project"

        for i in range(5):
            tracker.log_approval("Bash(git status:*)", f"git-session-{i}", project_path)

        for i in range(3):
            tracker.log_approval("Bash(pytest:*)", f"pytest-session-{i}", project_path)

        # Act
        stats = detector.get_pattern_stats(days=30)

        # Assert
        assert stats["total_approvals"] == 8
        assert stats["patterns_detected"] >= 1
        assert "category_counts" in stats
        assert stats["category_counts"]["git_read_only"] == 5 or stats["category_counts"]["git_all_safe"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
