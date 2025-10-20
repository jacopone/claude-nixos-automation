"""
Unit tests for BaseAnalyzer abstract base class.

Tests that BaseAnalyzer provides the contract expected by all analyzers.
"""

import pytest

from claude_automation.analyzers import BaseAnalyzer


class ConcreteAnalyzer(BaseAnalyzer):
    """Test implementation of BaseAnalyzer."""

    def _get_analysis_method_name(self) -> str:
        """Return the name of the primary analysis method."""
        return "analyze"

    def analyze(self):
        """Test analysis method."""
        return {"result": "analyzed"}


class TestBaseAnalyzer:
    """Test BaseAnalyzer contract."""

    def test_can_instantiate_with_no_args(self):
        """Test T018: BaseAnalyzer subclasses can be instantiated without arguments."""
        analyzer = ConcreteAnalyzer()
        assert analyzer is not None

    def test_can_instantiate_with_kwargs(self):
        """Test T018: BaseAnalyzer subclasses accept arbitrary keyword arguments."""
        analyzer = ConcreteAnalyzer(some_param="value", another_param=42)
        assert analyzer is not None

    def test_requires_analysis_method_name(self):
        """Test T018: BaseAnalyzer requires _get_analysis_method_name() implementation."""

        class IncompleteAnalyzer(BaseAnalyzer):
            pass

        # Should raise TypeError due to abstract method
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteAnalyzer()

    def test_subclass_has_analysis_method(self):
        """Test T018: BaseAnalyzer subclasses should have their primary analysis method."""
        analyzer = ConcreteAnalyzer()
        method_name = analyzer._get_analysis_method_name()

        assert hasattr(analyzer, method_name)
        assert callable(getattr(analyzer, method_name))

    def test_analysis_method_works(self):
        """Test T018: BaseAnalyzer subclass analysis methods function correctly."""
        analyzer = ConcreteAnalyzer()
        result = analyzer.analyze()

        assert result == {"result": "analyzed"}
