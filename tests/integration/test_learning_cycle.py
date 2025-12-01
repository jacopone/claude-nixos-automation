"""
Integration tests for permission learning cycle.

Tests the full flow: approval → pattern detection → suggestion (T035).
"""

import tempfile
from pathlib import Path

import pytest

from claude_automation.analyzers import ApprovalTracker, PermissionPatternDetector


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
    """Create PermissionPatternDetector.

    Uses monkeypatch to change CWD to temp_storage to prevent loading
    real settings.local.json patterns during tests.
    """
    # Isolate from real settings.local.json
    monkeypatch.chdir(temp_storage)

    return PermissionPatternDetector(
        approval_tracker=tracker,
        min_occurrences=3,
        confidence_threshold=0.5,  # Match TIER_1_SAFE threshold
    )


class TestApprovalToPatternToSuggestion:
    """Test full learning cycle from approval to suggestion (T035)."""

    def test_end_to_end_git_workflow(self, tracker, detector):
        """
        Test complete flow: user approves git commands → pattern detected → suggestion generated.
        """
        # STEP 1: Simulate user approving git commands
        session_id = "test-session-123"
        project_path = "/home/user/myproject"

        git_commands = [
            "Bash(git status:*)",
            "Bash(git log --oneline:*)",
            "Bash(git diff:*)",
            "Bash(git status:*)",  # User ran status twice
            "Bash(git branch:*)",
        ]

        for cmd in git_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # STEP 2: Pattern detector analyzes approval history
        suggestions = detector.detect_patterns(days=30)

        # STEP 3: Verify suggestion was generated
        assert len(suggestions) > 0, "No patterns detected from git commands"

        # Find git-related suggestion
        git_suggestions = [
            s for s in suggestions
            if "git" in s.pattern.pattern_type.lower()
        ]
        assert len(git_suggestions) > 0, "No git pattern detected"

        git_suggestion = git_suggestions[0]

        # STEP 4: Verify suggestion quality
        assert git_suggestion.pattern.occurrences == 5
        assert git_suggestion.pattern.confidence >= 0.6
        assert git_suggestion.proposed_rule is not None
        assert len(git_suggestion.approved_examples) > 0
        assert git_suggestion.description is not None

        # STEP 5: Verify suggestion is actionable
        # Proposed rule should be a valid permission string
        assert "Bash(git" in git_suggestion.proposed_rule or "git" in git_suggestion.proposed_rule

    def test_end_to_end_pytest_workflow(self, tracker, detector):
        """
        Test complete flow for pytest pattern.
        """
        # STEP 1: User approves pytest commands
        session_id = "test-session-456"
        project_path = "/home/user/myproject"

        pytest_commands = [
            "Bash(pytest tests/:*)",
            "Bash(pytest tests/unit/:*)",
            "Bash(python -m pytest:*)",
            "Bash(pytest -v:*)",
        ]

        for cmd in pytest_commands:
            tracker.log_approval(cmd, session_id, project_path)

        # STEP 2: Detect patterns
        suggestions = detector.detect_patterns(days=30)

        # STEP 3: Verify pytest pattern detected
        pytest_suggestions = [
            s for s in suggestions
            if s.pattern.pattern_type == "pytest"
        ]
        assert len(pytest_suggestions) > 0

        pytest_suggestion = pytest_suggestions[0]
        assert pytest_suggestion.pattern.occurrences == 4
        assert "pytest" in pytest_suggestion.proposed_rule.lower()

    def test_multiple_patterns_same_session(self, tracker, detector):
        """
        Test detecting multiple patterns from same session.
        """
        # STEP 1: User works on project, uses git AND pytest
        session_id = "test-session-789"
        project_path = "/home/user/myproject"

        # Git commands
        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # Pytest commands
        for _ in range(3):
            tracker.log_approval("Bash(pytest:*)", session_id, project_path)

        # Modern CLI tools
        tracker.log_approval("Bash(fd *.py:*)", session_id, project_path)
        tracker.log_approval("Bash(eza -la:*)", session_id, project_path)
        tracker.log_approval("Bash(bat file.txt:*)", session_id, project_path)

        # STEP 2: Detect all patterns
        suggestions = detector.detect_patterns(days=30)

        # STEP 3: Verify multiple patterns detected
        assert len(suggestions) >= 2

        pattern_types = {s.pattern.pattern_type for s in suggestions}
        # Should detect git and pytest at minimum
        assert any("git" in pt for pt in pattern_types)
        assert "pytest" in pattern_types

    def test_cross_project_pattern_detection(self, tracker, detector):
        """
        Test pattern detection across multiple projects.
        """
        # STEP 1: User approves same commands in different projects
        session_id = "test-session"
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"

        # Git commands in project1
        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project1)

        # Git commands in project2
        for _ in range(2):
            tracker.log_approval("Bash(git status:*)", session_id, project2)

        # STEP 2: Detect patterns globally (no project filter)
        suggestions = detector.detect_patterns(days=30, project_path=None)

        # STEP 3: Verify cross-project pattern detected
        git_suggestions = [
            s for s in suggestions
            if "git" in s.pattern.pattern_type
        ]
        assert len(git_suggestions) > 0
        # Total occurrences should be 5 (across both projects)
        assert git_suggestions[0].pattern.occurrences == 5

    def test_low_occurrence_no_suggestion(self, tracker, detector):
        """
        Test that patterns below threshold don't generate suggestions.
        """
        # STEP 1: User approves command only once (below TIER_1_SAFE threshold of 2)
        session_id = "test-session"
        project_path = "/home/user/project"

        tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # STEP 2: Try to detect patterns
        suggestions = detector.detect_patterns(days=30)

        # STEP 3: Verify no suggestions (below minimum occurrences)
        # Note: TIER_1_SAFE requires 2 occurrences minimum
        assert len(suggestions) == 0

    def test_pattern_confidence_affects_suggestions(self, tracker):
        """
        Test that confidence threshold filters suggestions.

        The new reliability-based confidence formula doesn't dilute based on
        unrelated commands. Instead, it measures session/project spread.
        To test filtering, we use a high threshold with single-session approvals.
        """
        # Create detector with HIGH threshold (requires multi-session spread)
        high_threshold_detector = PermissionPatternDetector(
            approval_tracker=tracker,
            min_occurrences=2,
            confidence_threshold=0.9,  # Very high threshold
        )

        # Single session = no session spread bonus
        session_id = "single-session"
        project_path = "/home/user/project"

        # 3 git commands from single session
        # Confidence = 0.5 (base) + 0.025 (1 session) + 0.03 (1 project) + ~0.05 + 0.05 = ~0.655
        # Below 0.9 threshold
        for _ in range(3):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # STEP 2: Detect patterns with high threshold
        suggestions = high_threshold_detector.detect_patterns(days=30)

        # STEP 3: Git pattern should be excluded due to low confidence (< 0.9)
        git_suggestions = [
            s for s in suggestions
            if "git" in s.pattern.pattern_type
        ]
        assert len(git_suggestions) == 0  # Filtered out by confidence threshold

    def test_time_window_affects_pattern_detection(self, tracker, detector):
        """
        Test that time window filters old approvals.
        """
        # STEP 1: Create approvals
        session_id = "test-session"
        project_path = "/home/user/project"

        for _ in range(5):
            tracker.log_approval("Bash(git status:*)", session_id, project_path)

        # STEP 2: Detect with short time window
        suggestions_7d = detector.detect_patterns(days=7)
        suggestions_30d = detector.detect_patterns(days=30)

        # STEP 3: Both should detect pattern (all approvals are recent)
        assert len(suggestions_7d) > 0
        assert len(suggestions_30d) > 0

        # Same pattern should be detected in both
        git_7d = [s for s in suggestions_7d if "git" in s.pattern.pattern_type]
        git_30d = [s for s in suggestions_30d if "git" in s.pattern.pattern_type]
        assert len(git_7d) > 0
        assert len(git_30d) > 0


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_developer_workflow_python_project(self, tracker, detector):
        """
        Simulate typical Python developer workflow.
        """
        # Developer working on Python project
        session_id = "dev-session"
        project_path = "/home/dev/python-app"

        # Typical workflow commands
        commands = [
            # Testing
            "Bash(pytest tests/:*)",
            "Bash(pytest tests/:*)",
            "Bash(pytest -v:*)",
            # Linting
            "Bash(ruff check .:*)",
            "Bash(ruff format .:*)",
            "Bash(ruff check --fix:*)",
            # Git
            "Bash(git status:*)",
            "Bash(git add .:*)",
            "Bash(git commit -m 'fix':*)",
            "Bash(git status:*)",
            "Bash(git log --oneline:*)",
            # File operations
            "Read(/home/dev/python-app/src/main.py)",
            "Edit(/home/dev/python-app/src/main.py)",
            "Read(/home/dev/python-app/tests/test_main.py)",
        ]

        for cmd in commands:
            tracker.log_approval(cmd, session_id, project_path)

        # Detect patterns
        suggestions = detector.detect_patterns(days=30)

        # Should detect at least git pattern (most frequent)
        # pytest and ruff have low confidence with only 3/14 occurrences each
        assert len(suggestions) >= 1

        pattern_types = {s.pattern.pattern_type for s in suggestions}
        # Git should be detected (5/14 occurrences)
        assert any("git" in pt for pt in pattern_types)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
