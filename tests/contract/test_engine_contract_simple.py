"""
Contract tests for AdaptiveSystemEngine (Phase 10) - simplified version.

Verifies engine exists and has expected structure without requiring all dependencies.
"""

import pytest


class TestEngineContractSimple:
    """Test AdaptiveSystemEngine basic contract."""

    def test_engine_exists(self):
        """Test T109: Engine class exists."""
        try:
            from claude_automation.core.adaptive_system_engine import (
                AdaptiveSystemEngine,
            )
            assert AdaptiveSystemEngine is not None
        except ImportError as e:
            if "jinja2" in str(e):
                pytest.skip("jinja2 not available in system python")
            raise

    def test_engine_has_run_method(self):
        """Test T109: Engine has run_full_learning_cycle method."""
        try:
            from claude_automation.core.adaptive_system_engine import (
                AdaptiveSystemEngine,
            )
            assert hasattr(AdaptiveSystemEngine, "run_full_learning_cycle")
        except ImportError as e:
            if "jinja2" in str(e):
                pytest.skip("jinja2 not available in system python")
            raise
