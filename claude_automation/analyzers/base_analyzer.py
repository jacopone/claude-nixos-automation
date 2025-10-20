"""
Base analyzer class providing standardized constructor interface.

All Tier 2 and Tier 3 analyzers inherit from this to ensure consistent
constructor signatures and reduce test friction.
"""

from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers.

    Provides standardized constructor interface with optional parameters,
    allowing analyzers to be instantiated with defaults for testing.

    Tier 1 Analyzers (logging/tracking):
    - ApprovalTracker
    - GlobalMCPAnalyzer
    - ContextOptimizer
    - InstructionEffectivenessTracker

    Tier 2 Analyzers (pattern detection):
    - PermissionPatternDetector
    - WorkflowDetector

    Tier 3 Analyzers (meta-learning/cross-project):
    - ProjectArchetypeDetector
    - MetaLearner
    """

    def __init__(self, **kwargs):  # noqa: B027
        """
        Initialize analyzer with optional keyword arguments.

        This base constructor accepts any keyword arguments to allow
        subclasses flexibility in their initialization parameters.

        Args:
            **kwargs: Subclass-specific initialization parameters
        """

    @abstractmethod
    def _get_analysis_method_name(self) -> str:
        """
        Return the name of the primary analysis method for this analyzer.

        Returns:
            Method name (e.g., 'analyze', 'detect_patterns', 'get_health_metrics')
        """
        pass
