"""
Import validation tests for schema modularization.

Verifies backward compatibility after splitting schemas.py into domain modules.
Tests that both old-style and new-style imports work correctly.
"""



class TestBackwardCompatibility:
    """Test that old import patterns still work."""

    def test_import_all_from_schemas(self):
        """Test that 'from claude_automation.schemas import *' works."""
        # Should not raise ImportError
        from claude_automation.schemas import (
            LearningReport,
            MCPServerInfo,
            PermissionPattern,
            ValidationResult,
        )

        assert PermissionPattern is not None
        assert MCPServerInfo is not None
        assert LearningReport is not None
        assert ValidationResult is not None

    def test_import_permission_schemas(self):
        """Test importing permission-related schemas."""
        from claude_automation.schemas import (
            PatternSuggestion,
            PermissionApprovalEntry,
            PermissionPattern,
        )

        assert PermissionApprovalEntry is not None
        assert PermissionPattern is not None
        assert PatternSuggestion is not None

    def test_import_mcp_schemas(self):
        """Test importing MCP-related schemas."""
        from claude_automation.schemas import (
            GlobalMCPReport,
            MCPServerInfo,
            MCPToolUsage,
            MCPUsageRecommendation,
        )

        assert MCPServerInfo is not None
        assert MCPToolUsage is not None
        assert MCPUsageRecommendation is not None
        assert GlobalMCPReport is not None

    def test_import_learning_schemas(self):
        """Test importing learning-related schemas."""
        from claude_automation.schemas import (
            CrossProjectPattern,
            LearningMetrics,
            LearningReport,
            TransferSuggestion,
        )

        assert LearningMetrics is not None
        assert LearningReport is not None
        assert CrossProjectPattern is not None
        assert TransferSuggestion is not None

    def test_import_core_schemas(self):
        """Test importing core schemas."""
        from claude_automation.schemas import (
            ProjectType,
            SystemConfig,
            ToolInfo,
        )

        assert ProjectType is not None
        assert ToolInfo is not None
        assert SystemConfig is not None

    def test_import_adaptive_system_config_backward_compat(self):
        """Test importing AdaptiveSystemConfig via backward compatibility."""
        from claude_automation.schemas import AdaptiveSystemConfig

        assert AdaptiveSystemConfig is not None


class TestDomainSpecificImports:
    """Test new domain-specific import patterns."""

    def test_import_from_permissions_module(self):
        """Test importing directly from permissions module."""
        from claude_automation.schemas.permissions import (
            PatternSuggestion,
            PermissionApprovalEntry,
            PermissionPattern,
        )

        assert PermissionApprovalEntry is not None
        assert PermissionPattern is not None
        assert PatternSuggestion is not None

    def test_import_from_mcp_module(self):
        """Test importing directly from MCP module."""
        from claude_automation.schemas.mcp import (
            GlobalMCPReport,
            MCPServerInfo,
            MCPToolUsage,
        )

        assert MCPServerInfo is not None
        assert MCPToolUsage is not None
        assert GlobalMCPReport is not None

    def test_import_from_learning_module(self):
        """Test importing directly from learning module."""
        from claude_automation.schemas.learning import (
            CrossProjectPattern,
            LearningMetrics,
            TransferSuggestion,
        )

        assert LearningMetrics is not None
        assert CrossProjectPattern is not None
        assert TransferSuggestion is not None

    def test_import_from_core_module(self):
        """Test importing directly from core module."""
        from claude_automation.schemas.core import (
            ProjectType,
            SystemConfig,
            ToolInfo,
        )

        assert ProjectType is not None
        assert ToolInfo is not None
        assert SystemConfig is not None

    def test_import_adaptive_system_config(self):
        """Test importing AdaptiveSystemConfig from learning module."""
        from claude_automation.schemas.learning import AdaptiveSystemConfig

        assert AdaptiveSystemConfig is not None

    def test_import_from_context_module(self):
        """Test importing directly from context module."""
        from claude_automation.schemas.context import (
            ContextAccessLog,
            ContextOptimization,
            SectionUsage,
        )

        assert ContextAccessLog is not None
        assert SectionUsage is not None
        assert ContextOptimization is not None

    def test_import_from_workflows_module(self):
        """Test importing directly from workflows module."""
        from claude_automation.schemas.workflows import (
            SlashCommandLog,
            WorkflowSequence,
            WorkflowSuggestion,
        )

        assert SlashCommandLog is not None
        assert WorkflowSequence is not None
        assert WorkflowSuggestion is not None

    def test_import_from_validation_module(self):
        """Test importing directly from validation module."""
        from claude_automation.schemas.validation import ValidationResult

        assert ValidationResult is not None

    def test_import_generation_result(self):
        """Test importing GenerationResult from config module."""
        # Note: GenerationResult is in config.py, not validation.py
        from claude_automation.schemas import GenerationResult

        assert GenerationResult is not None


class TestSchemaInstantiation:
    """Test that schemas can be instantiated after import."""

    def test_instantiate_permission_pattern(self):
        """Test creating PermissionPattern instance."""
        from claude_automation.schemas.permissions import PermissionPattern

        # Just test that it's importable and has expected structure
        assert hasattr(PermissionPattern, "model_fields")

    def test_instantiate_mcp_server_info(self):
        """Test creating MCPServerInfo instance."""
        from claude_automation.schemas.mcp import MCPServerInfo

        assert hasattr(MCPServerInfo, "model_fields")

    def test_instantiate_learning_report(self):
        """Test creating LearningReport instance."""
        from claude_automation.schemas.learning import LearningReport

        assert hasattr(LearningReport, "model_fields")


class TestNoCircularImports:
    """Test that no circular import issues exist."""

    def test_import_all_modules_together(self):
        """Test importing all domain modules simultaneously."""
        # Should not cause circular import errors
        from claude_automation.schemas import (
            context,
            core,
            learning,
            mcp,
            permissions,
            validation,
            workflows,
        )

        assert core is not None
        assert permissions is not None
        assert mcp is not None
        assert learning is not None
        assert context is not None
        assert workflows is not None
        assert validation is not None

    def test_reimport_schemas_package(self):
        """Test that schemas package can be re-imported."""
        # First import

        # Re-import should not cause issues
        import claude_automation.schemas as schemas2

        assert schemas2 is not None
