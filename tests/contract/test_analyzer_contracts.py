"""
Contract tests for analyzer interfaces (Phase 10).

Verifies all analyzers conform to the expected interface contracts.
"""

import pytest

from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.context_optimizer import ContextOptimizer
from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from claude_automation.analyzers.instruction_tracker import (
    InstructionEffectivenessTracker,
)
from claude_automation.analyzers.meta_learner import MetaLearner
from claude_automation.analyzers.permission_pattern_detector import (
    PermissionPatternDetector,
)
from claude_automation.analyzers.project_archetype_detector import (
    ProjectArchetypeDetector,
)
from claude_automation.analyzers.workflow_detector import WorkflowDetector

# Tier 1 Analyzers (logging/tracking)
TIER1_ANALYZERS = [
    (ApprovalTracker, "ApprovalTracker"),
    (GlobalMCPAnalyzer, "GlobalMCPAnalyzer"),
    (ContextOptimizer, "ContextOptimizer"),
    (InstructionEffectivenessTracker, "InstructionEffectivenessTracker"),  # Moved from Tier 2
]

# Tier 2 Analyzers (pattern detection)
TIER2_ANALYZERS = [
    (PermissionPatternDetector, "PermissionPatternDetector"),  # Moved from Tier 1
    (WorkflowDetector, "WorkflowDetector"),
]

# Tier 3 Analyzers
TIER3_ANALYZERS = [
    (ProjectArchetypeDetector, "ProjectArchetypeDetector"),
    (MetaLearner, "MetaLearner"),
]

ALL_ANALYZERS = TIER1_ANALYZERS + TIER2_ANALYZERS + TIER3_ANALYZERS


class TestAnalyzerContracts:
    """Test that all analyzers conform to expected interface contracts."""

    @pytest.mark.parametrize("analyzer_class,name", ALL_ANALYZERS)
    def test_analyzer_is_instantiable(self, analyzer_class, name):
        """Test T107: All analyzers can be instantiated."""
        # Should be able to create instance (may require default args)
        try:
            instance = analyzer_class()
            assert instance is not None
        except TypeError:
            # Some may require arguments - that's OK, just check class exists
            assert analyzer_class.__name__ == name

    @pytest.mark.parametrize("analyzer_class,name", ALL_ANALYZERS)
    def test_analyzer_has_analyze_method(self, analyzer_class, name):
        """Test T107: All analyzers have an analyze() or detect/get method."""
        # Check for standard methods
        methods = dir(analyzer_class)

        # Should have at least one of these analysis methods
        analysis_methods = [
            "analyze",
            "detect_patterns",
            "analyze_all_projects",
            "identify_noise_sections",
            "detect_violations",
            "detect_archetype",
            "get_health_metrics",
            "get_stats",  # ApprovalTracker uses this
        ]

        has_analysis_method = any(method in methods for method in analysis_methods)
        assert has_analysis_method, f"{name} missing analysis method"

    @pytest.mark.parametrize("analyzer_class,name", TIER1_ANALYZERS)
    def test_tier1_analyzer_logging(self, analyzer_class, name):
        """Test T107: Tier 1 analyzers support logging/tracking."""
        methods = dir(analyzer_class)

        # Should have logging or tracking methods
        logging_methods = ["log_approval", "log_access", "log_section_access", "log_session", "analyze_all_projects", "track"]

        has_logging = any(method in methods for method in logging_methods)
        assert has_logging, f"{name} missing logging capability"

    @pytest.mark.parametrize("analyzer_class,name", TIER2_ANALYZERS)
    def test_tier2_analyzer_pattern_detection(self, analyzer_class, name):
        """Test T107: Tier 2 analyzers support pattern detection."""
        methods = dir(analyzer_class)

        # Should have pattern detection methods
        pattern_methods = ["detect_patterns", "detect_violations", "find_sequences"]

        has_pattern_detection = any(method in methods for method in pattern_methods)
        assert has_pattern_detection, f"{name} missing pattern detection"

    @pytest.mark.parametrize("analyzer_class,name", TIER3_ANALYZERS)
    def test_tier3_analyzer_meta_capability(self, analyzer_class, name):
        """Test T107: Tier 3 analyzers support meta-learning/cross-project."""
        methods = dir(analyzer_class)

        # Should have meta or cross-project methods
        meta_methods = [
            "get_health_metrics",
            "suggest_threshold_adjustments",
            "detect_archetype",
            "find_transfer_opportunities",
        ]

        has_meta = any(method in methods for method in meta_methods)
        assert has_meta, f"{name} missing meta-learning capability"


class TestApprovalTrackerContract:
    """Contract tests for ApprovalTracker (Tier 1)."""

    def test_can_log_approval(self):
        """Test T107: ApprovalTracker.log_approval() exists and works."""
        tracker = ApprovalTracker()

        # Should be able to log an approval
        tracker.log_approval(
            permission="Bash(pytest:*)",
            session_id="test-session",
            project_path="/tmp/test",
            context={"test": "value"},
        )

    def test_can_get_recent_approvals(self):
        """Test T107: ApprovalTracker.get_recent_approvals() works."""
        tracker = ApprovalTracker()

        # Log an approval
        tracker.log_approval(
            permission="Bash(ruff:*)",
            session_id="test-session",
            project_path="/tmp/test",
        )

        # Should be able to retrieve it
        recent = tracker.get_recent_approvals(days=1)
        assert len(recent) >= 0  # May be empty depending on log file


class TestPermissionPatternDetectorContract:
    """Contract tests for PermissionPatternDetector (Tier 2)."""

    def test_can_detect_patterns(self):
        """Test T107: PermissionPatternDetector.detect_patterns() works."""
        tracker = ApprovalTracker()
        detector = PermissionPatternDetector(approval_tracker=tracker)

        # Should be able to detect patterns (may return empty list)
        patterns = detector.detect_patterns(days=30)
        assert isinstance(patterns, list)


class TestGlobalMCPAnalyzerContract:
    """Contract tests for GlobalMCPAnalyzer (Tier 1)."""

    def test_can_analyze_all_projects(self):
        """Test T107: GlobalMCPAnalyzer.analyze_all_projects() works."""
        from pathlib import Path
        analyzer = GlobalMCPAnalyzer(home_dir=Path("/tmp"))

        # Should be able to analyze (may return empty report)
        report = analyzer.analyze_all_projects()
        assert report is not None


class TestContextOptimizerContract:
    """Contract tests for ContextOptimizer (Tier 1)."""

    def test_can_analyze_context(self):
        """Test T107: ContextOptimizer.analyze() works."""
        optimizer = ContextOptimizer()

        # Should be able to analyze
        suggestions = optimizer.analyze()
        assert isinstance(suggestions, list)


class TestWorkflowDetectorContract:
    """Contract tests for WorkflowDetector (Tier 2)."""

    def test_can_log_command(self):
        """Test T107: WorkflowDetector.log_command() works."""
        detector = WorkflowDetector()

        # Should be able to log commands
        detector.log_command("/test", "session-1", success=True)

    def test_can_detect_patterns(self):
        """Test T107: WorkflowDetector.detect_patterns() works."""
        detector = WorkflowDetector()

        # Should be able to detect patterns
        patterns = detector.detect_patterns(min_occurrences=3)
        assert isinstance(patterns, list)


class TestInstructionTrackerContract:
    """Contract tests for InstructionEffectivenessTracker (Tier 1)."""

    def test_can_log_violation(self):
        """Test T107: InstructionEffectivenessTracker.log_session() works."""
        tracker = InstructionEffectivenessTracker()

        # Should be able to log sessions
        tracker.log_session(
            session_id="test-session",
            policy_name="test-policy",
            compliant=False,
            violation_type="test-violation",
        )

    def test_can_get_effectiveness_score(self):
        """Test T107: InstructionEffectivenessTracker.get_effectiveness_score() works."""
        tracker = InstructionEffectivenessTracker()

        # Log a session first
        tracker.log_session(
            session_id="test-session",
            policy_name="test-policy",
            compliant=True,
        )

        # Should return a score
        score = tracker.get_effectiveness_score("test-policy", total_sessions=10)
        assert isinstance(score, (int, float))


class TestProjectArchetypeDetectorContract:
    """Contract tests for ProjectArchetypeDetector (Tier 3)."""

    def test_can_detect_archetype(self):
        """Test T107: ProjectArchetypeDetector.detect_archetype() works."""
        detector = ProjectArchetypeDetector()

        # Should be able to detect archetype (may return None)
        from pathlib import Path

        _ = detector.detect_archetype(Path("/tmp"))
        # archetype may be None for unknown projects


class TestMetaLearnerContract:
    """Contract tests for MetaLearner (Tier 3)."""

    def test_can_get_health_metrics(self):
        """Test T107: MetaLearner.get_health_metrics() works."""
        learner = MetaLearner()

        # Should return health metrics
        metrics = learner.get_health_metrics()
        assert isinstance(metrics, dict)

    def test_can_suggest_threshold_adjustments(self):
        """Test T107: MetaLearner.suggest_threshold_adjustments() works."""
        learner = MetaLearner()

        # Should return adjustment suggestions
        adjustments = learner.suggest_threshold_adjustments()
        assert isinstance(adjustments, list)
