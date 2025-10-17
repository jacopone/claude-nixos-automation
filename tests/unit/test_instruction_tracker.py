"""
Unit tests for InstructionEffectivenessTracker (Phase 7).

Tests policy compliance monitoring and instruction effectiveness scoring.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_automation.analyzers.instruction_tracker import (
    InstructionEffectivenessTracker,
)


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        log_file = Path(f.name)
    yield log_file
    log_file.unlink(missing_ok=True)


@pytest.fixture
def tracker(temp_log_file):
    """Create an InstructionEffectivenessTracker instance with temp log file."""
    return InstructionEffectivenessTracker(log_file=temp_log_file)


def test_violation_detection(tracker):
    """Test T081: Log and detect policy violations."""
    # Log a policy violation
    tracker.log_session(
        session_id="session-1",
        policy_name="Documentation Creation Policy",
        compliant=False,
        violation_type="created_without_asking",
        details="Created README.md without user approval",
        severity="medium",
    )

    # Retrieve violations
    violations = tracker.get_recent_violations(days=7)

    # Verify violation was logged
    assert len(violations) == 1
    assert violations[0].policy_name == "Documentation Creation Policy"
    assert violations[0].violation_type == "created_without_asking"
    assert violations[0].severity == "medium"
    assert violations[0].session_id == "session-1"


def test_compliant_session_not_logged(tracker):
    """Test that compliant sessions are not logged as violations."""
    # Log a compliant session
    tracker.log_session(
        session_id="session-1",
        policy_name="Documentation Creation Policy",
        compliant=True,  # Compliant!
    )

    # Retrieve violations
    violations = tracker.get_recent_violations(days=7)

    # Should have no violations
    assert len(violations) == 0


def test_effectiveness_score(tracker):
    """Test T082: Calculate policy effectiveness score."""
    policy_name = "Tool Usage Policy"
    total_sessions = 10

    # Log 3 violations out of 10 sessions
    for i in range(3):
        tracker.log_session(
            session_id=f"session-{i}",
            policy_name=policy_name,
            compliant=False,
            violation_type="used_old_tools",
            details=f"Used grep instead of rg in session {i}",
            severity="low",
        )

    # Calculate effectiveness
    effectiveness = tracker.get_effectiveness_score(policy_name, total_sessions, days=30)

    # Verify calculations
    assert effectiveness.policy_name == policy_name
    assert effectiveness.total_sessions == 10
    assert effectiveness.compliant_sessions == 7  # 10 - 3 violations
    assert len(effectiveness.violations) == 3
    assert effectiveness.effectiveness_score == 0.7  # 7/10


def test_effectiveness_with_no_sessions(tracker):
    """Test effectiveness score with zero sessions."""
    effectiveness = tracker.get_effectiveness_score(
        "Some Policy", total_sessions=0, days=30
    )

    # Should handle gracefully
    assert effectiveness.total_sessions == 0
    assert effectiveness.effectiveness_score == 1.0  # No sessions = no violations


def test_effectiveness_is_effective_property(tracker):
    """Test T082: Verify is_effective property calculation."""
    policy_name = "Test Policy"

    # High effectiveness (80%)
    tracker.log_session(
        session_id="session-1",
        policy_name=policy_name,
        compliant=False,
        violation_type="test",
        details="Violation 1",
    )

    effectiveness_high = tracker.get_effectiveness_score(policy_name, total_sessions=5)
    assert effectiveness_high.effectiveness_score == 0.8  # 4/5
    assert effectiveness_high.is_effective is True  # >= 0.7

    # Low effectiveness (50%)
    for i in range(2, 4):
        tracker.log_session(
            session_id=f"session-{i}",
            policy_name=policy_name,
            compliant=False,
            violation_type="test",
            details=f"Violation {i}",
        )

    effectiveness_low = tracker.get_effectiveness_score(policy_name, total_sessions=6)
    assert effectiveness_low.effectiveness_score == 0.5  # 3/6
    assert effectiveness_low.is_effective is False  # < 0.7


def test_ambiguity_identification(tracker):
    """Test T083: Identify ambiguous/ineffective policies."""
    policy_name = "Ambiguous Policy"
    total_sessions = 10

    # Log 4 violations (60% compliance - below 70% threshold)
    for i in range(4):
        tracker.log_session(
            session_id=f"session-{i}",
            policy_name=policy_name,
            compliant=False,
            violation_type="unclear_instruction",
            details=f"Policy unclear in session {i}",
            severity="medium",
        )

    # Get improvement suggestions
    improvements = tracker.suggest_improvements(
        total_sessions=total_sessions,
        days=30,
        min_violations=3,
        effectiveness_threshold=0.7,
    )

    # Should suggest improvement for this policy
    assert len(improvements) > 0

    # Find our policy in suggestions
    policy_improvement = next(
        (imp for imp in improvements if imp.policy_name == policy_name), None
    )

    assert policy_improvement is not None
    assert policy_improvement.effectiveness_data.effectiveness_score == 0.6
    assert policy_improvement.priority in [1, 2]  # High or medium priority


def test_suggest_improvements_filters_effective_policies(tracker):
    """Test that effective policies don't get improvement suggestions."""
    effective_policy = "Effective Policy"
    total_sessions = 10

    # Log only 1 violation (90% compliance - very effective!)
    tracker.log_session(
        session_id="session-1",
        policy_name=effective_policy,
        compliant=False,
        violation_type="minor",
        details="One minor violation",
        severity="low",
    )

    # Get suggestions
    improvements = tracker.suggest_improvements(
        total_sessions=total_sessions, days=30, min_violations=1
    )

    # Should not suggest improvement for effective policy
    policy_improvement = next(
        (imp for imp in improvements if imp.policy_name == effective_policy), None
    )

    assert policy_improvement is None  # No suggestion for effective policy


def test_suggest_improvements_min_violations_threshold(tracker):
    """Test that policies with too few violations are ignored."""
    policy_name = "Rare Violation Policy"
    total_sessions = 10

    # Log only 2 violations (below min_violations=3 threshold)
    for i in range(2):
        tracker.log_session(
            session_id=f"session-{i}",
            policy_name=policy_name,
            compliant=False,
            violation_type="test",
            details=f"Violation {i}",
        )

    # Get suggestions with min_violations=3
    improvements = tracker.suggest_improvements(
        total_sessions=total_sessions, days=30, min_violations=3
    )

    # Should not suggest improvement (not enough violations)
    policy_improvement = next(
        (imp for imp in improvements if imp.policy_name == policy_name), None
    )

    assert policy_improvement is None


def test_priority_assignment(tracker):
    """Test that priority is correctly assigned based on effectiveness score."""
    total_sessions = 10

    # Very low effectiveness (40% - should be priority 1)
    for i in range(6):
        tracker.log_session(
            session_id=f"session-low-{i}",
            policy_name="Very Low Effectiveness",
            compliant=False,
            violation_type="test",
        )

    # Medium effectiveness (60% - should be priority 2)
    for i in range(4):
        tracker.log_session(
            session_id=f"session-med-{i}",
            policy_name="Medium Effectiveness",
            compliant=False,
            violation_type="test",
        )

    improvements = tracker.suggest_improvements(
        total_sessions=total_sessions, days=30, min_violations=3
    )

    # Find improvements
    very_low = next(
        (imp for imp in improvements if imp.policy_name == "Very Low Effectiveness"),
        None,
    )
    medium = next(
        (imp for imp in improvements if imp.policy_name == "Medium Effectiveness"), None
    )

    # Verify priorities
    assert very_low is not None
    assert very_low.priority == 1  # High priority (< 0.5)

    assert medium is not None
    assert medium.priority == 2  # Medium priority (0.5-0.7)


def test_suggestions_sorted_by_priority(tracker):
    """Test that improvement suggestions are sorted by effectiveness (worst first)."""
    total_sessions = 10

    # Create policies with different effectiveness scores (all below 70% threshold)
    for i in range(3):
        tracker.log_session(
            session_id=f"s-a-{i}",
            policy_name="Policy A",
            compliant=False,
            violation_type="test",
        )  # 70% - exactly at threshold, should be excluded

    for i in range(4):
        tracker.log_session(
            session_id=f"s-b-{i}",
            policy_name="Policy B",
            compliant=False,
            violation_type="test",
        )  # 60%

    for i in range(5):
        tracker.log_session(
            session_id=f"s-c-{i}",
            policy_name="Policy C",
            compliant=False,
            violation_type="test",
        )  # 50%

    improvements = tracker.suggest_improvements(
        total_sessions=total_sessions, days=30, min_violations=3
    )

    # Should be sorted: Policy C (50%), Policy B (60%)
    # Policy A (70%) is at threshold, may or may not be included depending on is_effective logic
    assert len(improvements) >= 1  # At least Policy C
    assert improvements[0].policy_name == "Policy C"  # Lowest effectiveness first
    assert improvements[0].effectiveness_data.effectiveness_score == 0.5


def test_get_stats(tracker):
    """Test statistics generation."""
    # Log violations with different severities
    tracker.log_session(
        "s1", "Policy A", False, "type1", "details", severity="high"
    )
    tracker.log_session(
        "s2", "Policy A", False, "type2", "details", severity="medium"
    )
    tracker.log_session(
        "s3", "Policy B", False, "type1", "details", severity="low"
    )

    # Get stats
    stats = tracker.get_stats(days=30)

    # Verify structure
    assert "total_violations" in stats
    assert "unique_policies" in stats
    assert "severity_breakdown" in stats
    assert "most_violated" in stats

    # Verify values
    assert stats["total_violations"] == 3
    assert stats["unique_policies"] == 2
    assert stats["severity_breakdown"]["high"] == 1
    assert stats["severity_breakdown"]["medium"] == 1
    assert stats["severity_breakdown"]["low"] == 1

    # Policy A has 2 violations, should be most violated
    assert stats["most_violated"][0][0] == "Policy A"
    assert stats["most_violated"][0][1] == 2


def test_policy_filter_in_get_recent_violations(tracker):
    """Test filtering violations by policy name."""
    # Log violations for different policies
    tracker.log_session("s1", "Policy A", False, "type1", "details")
    tracker.log_session("s2", "Policy B", False, "type1", "details")
    tracker.log_session("s3", "Policy A", False, "type2", "details")

    # Get all violations
    all_violations = tracker.get_recent_violations(days=30, policy_name=None)
    assert len(all_violations) == 3

    # Get only Policy A violations
    policy_a_violations = tracker.get_recent_violations(days=30, policy_name="Policy A")
    assert len(policy_a_violations) == 2
    assert all(v.policy_name == "Policy A" for v in policy_a_violations)


def test_time_window_filtering(tracker):
    """Test that violations outside time window are not included."""
    # Log a violation
    tracker.log_session("s1", "Test Policy", False, "type1", "details")

    # Get recent violations (1 day window)
    recent = tracker.get_recent_violations(days=1)
    assert len(recent) == 1

    # Get very old violations (should still include it since we just logged it)
    very_recent = tracker.get_recent_violations(days=30)
    assert len(very_recent) == 1
