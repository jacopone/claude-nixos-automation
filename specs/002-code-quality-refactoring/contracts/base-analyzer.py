"""
BaseAnalyzer Abstract Interface Contract

This contract defines the required interface for all analyzer components
in the claude-automation-system. All Tier 3 analyzers MUST inherit from
this base class to ensure API consistency.

Status: Contract Definition (not executable code)
Version: 1.0
Date: 2025-10-19
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzer components.

    Provides standardized constructor interface and common utilities.
    All Tier 3 analyzers (permission patterns, MCP optimization, context
    optimization, workflow detection, instruction tracking, project archetypes,
    meta-learning) MUST inherit from this class.

    Constructor Contract:
        def __init__(self, storage_dir: Path | None = None, days: int = 30)

    Required Methods:
        analyze() -> Any  (abstract, subclasses must implement)

    Provided Methods:
        _validate_parameters() -> None  (common validation logic)
    """

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRUCTOR CONTRACT (MUST MATCH IN ALL SUBCLASSES)
    # ─────────────────────────────────────────────────────────────────────────

    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        """Initialize analyzer with standard parameters.

        This constructor signature is standardized across ALL analyzers to
        fix the 24 failing tests in the test suite.

        Args:
            storage_dir: Directory for analytics storage.
                         Defaults to ~/.claude if not provided.
                         Will be created if it doesn't exist.

            days: Number of days of history to analyze.
                  Must be >= 1.
                  Default: 30 days.

        Raises:
            ValueError: If days < 1

        Examples:
            # Use default storage and 30 days
            analyzer = PermissionPatternDetector()

            # Custom storage, default days
            analyzer = GlobalMCPAnalyzer(storage_dir=Path("/tmp/analytics"))

            # Custom days
            analyzer = ContextOptimizer(days=90)

            # Both custom
            analyzer = MetaLearner(
                storage_dir=Path("/custom/path"),
                days=60
            )
        """
        self.storage_dir = storage_dir or Path.home() / ".claude"
        self.days = days
        self._validate_parameters()

    # ─────────────────────────────────────────────────────────────────────────
    # VALIDATION (PROVIDED BY BASE CLASS)
    # ─────────────────────────────────────────────────────────────────────────

    def _validate_parameters(self) -> None:
        """Validate constructor parameters.

        Common validation logic shared across all analyzers.
        Subclasses may extend but should call super()._validate_parameters().

        Validation Rules:
            - days must be >= 1
            - storage_dir will be created if it doesn't exist

        Raises:
            ValueError: If days < 1
        """
        if self.days < 1:
            raise ValueError(
                f"days parameter must be >= 1, got {self.days}. "
                f"Analyzers need at least 1 day of history."
            )

        # Ensure storage directory exists
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # ABSTRACT METHODS (SUBCLASSES MUST IMPLEMENT)
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def analyze(self) -> Any:
        """Perform analysis and return results.

        This method MUST be implemented by all subclasses.

        The return type is intentionally flexible (Any) because different
        analyzers return different result types:
            - PermissionPatternDetector -> list[PermissionPattern]
            - GlobalMCPAnalyzer -> GlobalMCPReport
            - ContextOptimizer -> list[ContextOptimization]
            - WorkflowDetector -> list[WorkflowSequence]
            - InstructionTracker -> InstructionEffectivenessReport
            - ProjectArchetypeDetector -> list[ProjectArchetype]
            - MetaLearner -> LearningHealthReport

        Returns:
            Analysis results (type varies by analyzer)

        Raises:
            Subclass-specific exceptions for analysis failures
        """
        pass


# ═════════════════════════════════════════════════════════════════════════════
# CONTRACT COMPLIANCE EXAMPLES
# ═════════════════════════════════════════════════════════════════════════════

class PermissionPatternDetector(BaseAnalyzer):
    """Example: Compliant analyzer implementation.

    CORRECT:
        - Inherits from BaseAnalyzer
        - Constructor matches signature (storage_dir, days)
        - Implements analyze() method
        - Calls super().__init__() to run validation
    """

    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        super().__init__(storage_dir, days)
        # Additional initialization if needed
        self.history_file = self.storage_dir / "approval-history.jsonl"

    def analyze(self) -> list:  # Returns list[PermissionPattern]
        """Detect permission approval patterns from history."""
        # Implementation logic here
        return []


class ProjectArchetypeDetector(BaseAnalyzer):
    """Example: Fixed analyzer (previously had wrong constructor).

    BEFORE (INCORRECT - caused test failures):
        def __init__(self, project_paths: list[Path]):
            self.project_paths = project_paths

    AFTER (CORRECT - matches BaseAnalyzer contract):
        def __init__(self, storage_dir: Path | None = None, days: int = 30):
            super().__init__(storage_dir, days)
            # Discover projects from storage_dir
    """

    def __init__(self, storage_dir: Path | None = None, days: int = 30):
        super().__init__(storage_dir, days)
        # Discover project paths from storage directory
        self.project_paths = self._discover_projects()

    def _discover_projects(self) -> list[Path]:
        """Discover projects from storage directory."""
        # Implementation: scan for .git directories, pyproject.toml, etc.
        return []

    def analyze(self) -> list:  # Returns list[ProjectArchetype]
        """Detect project archetype patterns."""
        return []


# ═════════════════════════════════════════════════════════════════════════════
# TEST CONTRACT ASSERTIONS
# ═════════════════════════════════════════════════════════════════════════════

def test_base_analyzer_contract():
    """Contract tests that will be implemented in tests/contract/"""

    # Test 1: Constructor signature compliance
    import inspect
    sig = inspect.signature(BaseAnalyzer.__init__)
    params = list(sig.parameters.keys())
    assert params == ['self', 'storage_dir', 'days'], \
        "BaseAnalyzer constructor must have (self, storage_dir, days) parameters"

    # Test 2: Default parameter values
    assert sig.parameters['storage_dir'].default is None
    assert sig.parameters['days'].default == 30

    # Test 3: Abstract method enforcement
    try:
        BaseAnalyzer()  # Should fail - can't instantiate abstract class
        assert False, "Should not be able to instantiate BaseAnalyzer"
    except TypeError as e:
        assert "abstract" in str(e).lower()

    # Test 4: Validation enforcement
    class TestAnalyzer(BaseAnalyzer):
        def analyze(self): return []

    try:
        TestAnalyzer(days=0)  # Should fail - days must be >= 1
        assert False, "Should reject days=0"
    except ValueError as e:
        assert "days" in str(e).lower()

    print("✅ All contract assertions passed")


if __name__ == "__main__":
    test_base_analyzer_contract()
