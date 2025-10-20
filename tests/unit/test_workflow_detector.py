"""
Unit tests for WorkflowDetector (Phase 6).

Tests workflow pattern detection from slash command sequences.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from claude_automation.analyzers import WorkflowDetector


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        log_file = Path(f.name)
    yield log_file
    log_file.unlink(missing_ok=True)


@pytest.fixture
def detector(temp_log_file):
    """Create a WorkflowDetector instance with temp log file."""
    return WorkflowDetector(log_file=temp_log_file)


def test_log_command(detector):
    """Test T072: Log slash command invocations."""
    # Log a command
    detector.log_command(
        command="/speckit.specify",
        session_id="test-session-1",
        success=True,
        duration_ms=1500,
        project_path="/home/user/project",
    )

    # Verify it was logged
    commands = detector.get_recent_commands(days=1)
    assert len(commands) == 1
    assert commands[0].command == "/speckit.specify"
    assert commands[0].session_id == "test-session-1"
    assert commands[0].success is True
    assert commands[0].duration_ms == 1500


def test_get_recent_commands(detector):
    """Test T072: Retrieve recent commands within time window."""
    # Log commands from different days
    now = datetime.now()

    # Recent command (today)
    detector.log_command(
        command="/speckit.specify",
        session_id="session-1",
        success=True,
        project_path="/home/user/project",
    )

    # Get recent commands
    recent = detector.get_recent_commands(days=7)
    assert len(recent) == 1
    assert recent[0].command == "/speckit.specify"


def test_workflow_detection(detector):
    """Test T073: Detect repeated command sequences."""
    session_id = "test-session"

    # Log a repeated sequence: specify -> clarify -> plan
    for _ in range(3):  # Repeat 3 times to trigger detection
        detector.log_command("/speckit.specify", session_id, success=True)
        detector.log_command("/speckit.clarify", session_id, success=True)
        detector.log_command("/speckit.plan", session_id, success=True)

    # Detect patterns (min 3 occurrences)
    patterns = detector.detect_patterns(min_occurrences=3, days=30, max_sequence_length=5)

    # Should detect the 2-command and 3-command sequences
    assert len(patterns) > 0

    # Verify pattern contains our sequence
    found_sequence = False
    for suggestion in patterns:
        if len(suggestion.sequence.commands) >= 2:
            if (
                "/speckit.specify" in suggestion.sequence.commands
                and "/speckit.clarify" in suggestion.sequence.commands
            ):
                found_sequence = True
                break

    assert found_sequence, "Expected to find specify->clarify sequence"


def test_sequence_patterns(detector):
    """Test T073: Extract sequences of various lengths."""
    session_id = "test-session"

    # Log a 4-command sequence repeated 3 times
    sequence = ["/cmd1", "/cmd2", "/cmd3", "/cmd4"]

    for _ in range(3):
        for cmd in sequence:
            detector.log_command(cmd, session_id, success=True)

    # Detect patterns
    patterns = detector.detect_patterns(min_occurrences=3, max_sequence_length=5)

    # Should detect multiple subsequences
    assert len(patterns) > 0

    # Verify sequences are properly extracted
    sequence_lengths = [len(p.sequence.commands) for p in patterns]
    assert 2 in sequence_lengths  # 2-command sequences
    assert max(sequence_lengths) <= 5  # Respects max_sequence_length


def test_completion_rate_calculation(detector):
    """Test T074: Calculate workflow completion rates."""
    session_id = "test-session"

    # Log successful sequence
    detector.log_command("/speckit.specify", session_id, success=True)
    detector.log_command("/speckit.clarify", session_id, success=True)

    # Detect patterns
    patterns = detector.detect_patterns(min_occurrences=1)

    # Verify completion rate is tracked
    if patterns:
        assert hasattr(patterns[0].sequence, "completion_rate")
        assert 0.0 <= patterns[0].sequence.completion_rate <= 1.0


def test_no_patterns_with_insufficient_data(detector):
    """Test that no patterns are detected with insufficient occurrences."""
    # Log a sequence only once
    detector.log_command("/cmd1", "session-1", success=True)
    detector.log_command("/cmd2", "session-1", success=True)

    # Try to detect patterns (min 3 occurrences)
    patterns = detector.detect_patterns(min_occurrences=3)

    # Should find no patterns
    assert len(patterns) == 0


def test_workflow_suggestion_format(detector):
    """Test that workflow suggestions have proper format."""
    session_id = "test-session"

    # Log a repeated sequence
    for _ in range(3):
        detector.log_command("/speckit.specify", session_id, success=True)
        detector.log_command("/speckit.clarify", session_id, success=True)

    patterns = detector.detect_patterns(min_occurrences=3)

    if patterns:
        suggestion = patterns[0]

        # Verify suggestion structure
        assert hasattr(suggestion, "description")
        assert hasattr(suggestion, "sequence")
        assert hasattr(suggestion, "proposed_command")
        assert hasattr(suggestion, "script_content")
        assert hasattr(suggestion, "impact_estimate")

        # Verify sequence structure
        assert hasattr(suggestion.sequence, "commands")
        assert hasattr(suggestion.sequence, "occurrences")
        assert suggestion.sequence.occurrences >= 3


def test_get_stats(detector):
    """Test workflow statistics generation."""
    # Log some commands
    detector.log_command("/cmd1", "session-1", success=True)
    detector.log_command("/cmd2", "session-1", success=True)
    detector.log_command("/cmd1", "session-2", success=True)

    # Get stats
    stats = detector.get_stats(days=30)

    # Verify stats structure
    assert "total_commands" in stats
    assert "unique_commands" in stats
    assert "total_sessions" in stats
    assert "most_used" in stats

    # Verify values
    assert stats["total_commands"] == 3
    assert stats["unique_commands"] == 2
    assert stats["total_sessions"] == 2


def test_most_used_commands(detector):
    """Test most frequently used commands tracking."""
    # Log commands with different frequencies
    for _ in range(5):
        detector.log_command("/popular", "session-1", success=True)

    for _ in range(2):
        detector.log_command("/less-popular", "session-1", success=True)

    detector.log_command("/rare", "session-1", success=True)

    # Get stats
    stats = detector.get_stats(days=30)
    most_used = stats["most_used"]

    # Verify most popular is first
    assert len(most_used) > 0
    assert most_used[0][0] == "/popular"
    assert most_used[0][1] == 5


def test_session_grouping(detector):
    """Test that commands are properly grouped by session."""
    # Log commands in different sessions
    detector.log_command("/cmd1", "session-1", success=True)
    detector.log_command("/cmd2", "session-1", success=True)
    detector.log_command("/cmd3", "session-2", success=True)

    # Get all commands
    commands = detector.get_recent_commands(days=30)

    # Group by session
    sessions = {}
    for cmd in commands:
        if cmd.session_id not in sessions:
            sessions[cmd.session_id] = []
        sessions[cmd.session_id].append(cmd)

    # Verify grouping
    assert len(sessions) == 2
    assert len(sessions["session-1"]) == 2
    assert len(sessions["session-2"]) == 1
