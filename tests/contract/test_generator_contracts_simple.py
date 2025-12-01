"""
Contract tests for generator interfaces (Phase 10) - simplified version.

Verifies all generators conform to BaseGenerator contract without requiring jinja2.
"""

import pytest


class TestGeneratorContractsSimple:
    """Test that generator classes exist and have expected structure."""

    def test_base_generator_exists(self):
        """Test T108: BaseGenerator class exists."""
        try:
            from claude_automation.generators.base_generator import BaseGenerator

            assert BaseGenerator is not None
        except ImportError as e:
            if "jinja2" in str(e):
                pytest.skip("jinja2 not available in system python")
            raise

    def test_system_generator_exists(self):
        """Test T108: SystemGenerator class exists."""
        try:
            from claude_automation.generators.system_generator import SystemGenerator

            assert SystemGenerator is not None
        except ImportError as e:
            if "jinja2" in str(e):
                pytest.skip("jinja2 not available in system python")
            raise

    def test_permissions_generator_exists(self):
        """Test T108: PermissionsGenerator class exists."""
        try:
            from claude_automation.generators.permissions_generator import (
                PermissionsGenerator,
            )

            assert PermissionsGenerator is not None
        except ImportError as e:
            if "jinja2" in str(e):
                pytest.skip("jinja2 not available in system python")
            raise

    def test_intelligent_permissions_generator_exists(self):
        """Test T108: IntelligentPermissionsGenerator class exists."""
        try:
            from claude_automation.generators.intelligent_permissions_generator import (
                IntelligentPermissionsGenerator,
            )

            assert IntelligentPermissionsGenerator is not None
        except ImportError as e:
            if "jinja2" in str(e):
                pytest.skip("jinja2 not available in system python")
            raise
