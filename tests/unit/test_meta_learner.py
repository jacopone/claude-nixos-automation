"""
Unit tests for MetaLearner (Phase 9).

Tests meta-learning system effectiveness tracking and self-calibration.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_automation.analyzers.meta_learner import MetaLearner


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for meta-learner data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def meta_learner(temp_data_dir):
    """Create MetaLearner instance with temp data directory."""
    return MetaLearner(data_dir=temp_data_dir)


def test_track_suggestion_acceptance(meta_learner):
    """Test T098: Track suggestion acceptance rates."""
    # Record suggestions
    meta_learner.record_suggestion(
        component="permission_learning",
        suggestion_id="perm_001",
        confidence=0.9,
        accepted=True,
    )
    meta_learner.record_suggestion(
        component="permission_learning",
        suggestion_id="perm_002",
        confidence=0.8,
        accepted=True,
    )
    meta_learner.record_suggestion(
        component="permission_learning",
        suggestion_id="perm_003",
        confidence=0.7,
        accepted=False,
    )

    # Get acceptance rate
    rate = meta_learner.get_acceptance_rate("permission_learning")

    # Should be 2/3 = 0.667
    assert 0.65 <= rate <= 0.68


def test_track_false_positive_rate(meta_learner):
    """Test T098: Track false positive rates."""
    # Record suggestions with outcomes
    meta_learner.record_suggestion(
        component="mcp_optimization",
        suggestion_id="mcp_001",
        confidence=0.9,
        accepted=True,
    )
    # User later reverted this suggestion
    meta_learner.record_revert(
        component="mcp_optimization",
        suggestion_id="mcp_001",
        reason="caused_errors",
    )

    meta_learner.record_suggestion(
        component="mcp_optimization",
        suggestion_id="mcp_002",
        confidence=0.85,
        accepted=True,
    )
    # This one worked fine (no revert)

    # Get false positive rate
    fp_rate = meta_learner.get_false_positive_rate("mcp_optimization")

    # Should be 1/2 = 0.5 (1 reverted out of 2 accepted)
    assert 0.4 <= fp_rate <= 0.6


def test_acceptance_rate_monitoring(meta_learner):
    """Test T099: Monitor acceptance rates over time."""
    # Record suggestions over multiple days
    now = datetime.now()

    for i in range(10):
        timestamp = now - timedelta(days=i)
        meta_learner.record_suggestion(
            component="context_optimization",
            suggestion_id=f"ctx_{i}",
            confidence=0.8,
            accepted=i < 7,  # 70% acceptance rate
            timestamp=timestamp,
        )

    # Get acceptance rate for last 30 days
    rate = meta_learner.get_acceptance_rate("context_optimization", days=30)

    assert 0.65 <= rate <= 0.75


def test_threshold_adjustment_low_acceptance(meta_learner):
    """Test T099: Adjust confidence thresholds based on acceptance rate."""
    # Record low acceptance rate (< 50%)
    for i in range(10):
        meta_learner.record_suggestion(
            component="workflow_detection",
            suggestion_id=f"wf_{i}",
            confidence=0.7,
            accepted=i < 4,  # 40% acceptance rate
        )

    # Get threshold adjustment recommendation
    adjustments = meta_learner.suggest_threshold_adjustments()

    # Should recommend increasing threshold for workflow_detection
    workflow_adj = [
        adj for adj in adjustments if adj.component == "workflow_detection"
    ]
    assert len(workflow_adj) > 0
    assert workflow_adj[0].recommended_threshold > 0.7


def test_threshold_adjustment_high_acceptance(meta_learner):
    """Test T099: Lower threshold when acceptance rate is high."""
    # Record high acceptance rate (> 90%)
    for i in range(10):
        meta_learner.record_suggestion(
            component="instruction_tracking",
            suggestion_id=f"inst_{i}",
            confidence=0.8,
            accepted=i < 9,  # 90% acceptance rate
        )

    # Get threshold adjustment recommendation
    adjustments = meta_learner.suggest_threshold_adjustments()

    # Should recommend decreasing threshold for instruction_tracking
    instruction_adj = [
        adj for adj in adjustments if adj.component == "instruction_tracking"
    ]
    assert len(instruction_adj) > 0
    assert instruction_adj[0].recommended_threshold < 0.8


def test_learning_health_metrics(meta_learner):
    """Test T100: Generate health metrics for learning system."""
    # Record diverse data
    components = ["permission_learning", "mcp_optimization", "context_optimization"]

    for component in components:
        for i in range(5):
            meta_learner.record_suggestion(
                component=component,
                suggestion_id=f"{component}_{i}",
                confidence=0.8,
                accepted=i < 3,  # 60% acceptance
            )

    # Get health metrics
    health = meta_learner.get_health_metrics()

    # Should have metrics for all components
    assert "permission_learning" in health
    assert "mcp_optimization" in health
    assert "context_optimization" in health

    # Each should have acceptance rate
    for component in components:
        assert 0.5 <= health[component]["acceptance_rate"] <= 0.7


def test_confidence_scoring_calibration(meta_learner):
    """Test T099: Calibrate confidence scores based on outcomes."""
    # Record suggestions with varying confidence
    for i in range(10):
        confidence = 0.5 + (i * 0.05)  # 0.5 to 0.95
        accepted = confidence > 0.7  # High confidence should correlate with acceptance

        meta_learner.record_suggestion(
            component="test_component",
            suggestion_id=f"test_{i}",
            confidence=confidence,
            accepted=accepted,
        )

    # Get calibration metrics
    calibration = meta_learner.get_confidence_calibration("test_component")

    # High confidence suggestions should have higher acceptance rates
    assert calibration["high_confidence_accuracy"] > calibration["low_confidence_accuracy"]


def test_component_health_status(meta_learner):
    """Test T100: Determine health status of components."""
    # Create healthy component (high acceptance, low FP)
    for i in range(10):
        meta_learner.record_suggestion(
            component="healthy_component",
            suggestion_id=f"healthy_{i}",
            confidence=0.8,
            accepted=i < 9,  # 90% acceptance
        )

    # Create unhealthy component (low acceptance, high FP)
    for i in range(10):
        meta_learner.record_suggestion(
            component="unhealthy_component",
            suggestion_id=f"unhealthy_{i}",
            confidence=0.8,
            accepted=i < 3,  # 30% acceptance
        )
        if i < 3:
            meta_learner.record_revert(
                component="unhealthy_component",
                suggestion_id=f"unhealthy_{i}",
                reason="bad_suggestion",
            )

    health = meta_learner.get_health_metrics()

    # Healthy component should have good status
    assert health["healthy_component"]["status"] == "healthy"

    # Unhealthy component should have warning/critical status
    assert health["unhealthy_component"]["status"] in ["warning", "critical"]


def test_learning_velocity(meta_learner):
    """Test T100: Track learning velocity (suggestions per day)."""
    # Record suggestions over time
    now = datetime.now()

    for i in range(20):
        timestamp = now - timedelta(hours=i)
        meta_learner.record_suggestion(
            component="velocity_test",
            suggestion_id=f"vel_{i}",
            confidence=0.8,
            accepted=True,
            timestamp=timestamp,
        )

    health = meta_learner.get_health_metrics()

    # Should calculate velocity
    assert "velocity_test" in health
    assert "suggestions_per_day" in health["velocity_test"]
    assert health["velocity_test"]["suggestions_per_day"] > 0


def test_effectiveness_tracking(meta_learner):
    """Test T098: Track overall effectiveness of learning system."""
    # Record multiple components
    for component in ["comp1", "comp2", "comp3"]:
        for i in range(5):
            meta_learner.record_suggestion(
                component=component,
                suggestion_id=f"{component}_{i}",
                confidence=0.8,
                accepted=i < 4,  # 80% acceptance
            )

    effectiveness = meta_learner.get_overall_effectiveness()

    # Should have high effectiveness score
    assert 0.7 <= effectiveness <= 0.9


def test_suggestion_history_persistence(meta_learner, temp_data_dir):
    """Test that suggestion history is persisted to disk."""
    # Record suggestion
    meta_learner.record_suggestion(
        component="test",
        suggestion_id="test_001",
        confidence=0.8,
        accepted=True,
    )

    # Create new meta-learner instance with same data dir
    new_meta_learner = MetaLearner(data_dir=temp_data_dir)

    # Should still have the suggestion
    rate = new_meta_learner.get_acceptance_rate("test")
    assert rate == 1.0


def test_time_window_filtering(meta_learner):
    """Test filtering metrics by time window."""
    now = datetime.now()

    # Record old suggestions (60 days ago)
    for i in range(5):
        meta_learner.record_suggestion(
            component="time_test",
            suggestion_id=f"old_{i}",
            confidence=0.8,
            accepted=False,
            timestamp=now - timedelta(days=60),
        )

    # Record recent suggestions (10 days ago)
    for i in range(5):
        meta_learner.record_suggestion(
            component="time_test",
            suggestion_id=f"recent_{i}",
            confidence=0.8,
            accepted=True,
            timestamp=now - timedelta(days=10),
        )

    # Get acceptance rate for last 30 days (should only include recent)
    rate = meta_learner.get_acceptance_rate("time_test", days=30)

    assert rate == 1.0  # All recent suggestions were accepted


def test_component_comparison(meta_learner):
    """Test comparing effectiveness across components."""
    # Create components with different effectiveness
    components_data = {
        "excellent": (10, 10),  # 10 suggestions, 10 accepted
        "good": (10, 8),  # 10 suggestions, 8 accepted
        "poor": (10, 3),  # 10 suggestions, 3 accepted
    }

    for component, (total, accepted) in components_data.items():
        for i in range(total):
            meta_learner.record_suggestion(
                component=component,
                suggestion_id=f"{component}_{i}",
                confidence=0.8,
                accepted=i < accepted,
            )

    # Get rankings
    rankings = meta_learner.get_component_rankings()

    # Should rank excellent > good > poor
    assert rankings[0].component == "excellent"
    assert rankings[-1].component == "poor"
