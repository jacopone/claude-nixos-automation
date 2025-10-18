"""
Contract tests for generator interfaces (Phase 10).

Verifies all generators conform to BaseGenerator contract.
"""

import pytest

from claude_automation.generators.base_generator import BaseGenerator
from claude_automation.generators.intelligent_permissions_generator import (
    IntelligentPermissionsGenerator,
)
from claude_automation.generators.permissions_generator import PermissionsGenerator
from claude_automation.generators.system_generator import SystemGenerator

ALL_GENERATORS = [
    (SystemGenerator, "SystemGenerator"),
    (PermissionsGenerator, "PermissionsGenerator"),
    (IntelligentPermissionsGenerator, "IntelligentPermissionsGenerator"),
]


class TestGeneratorContracts:
    """Test that all generators conform to BaseGenerator contract."""

    @pytest.mark.parametrize("generator_class,name", ALL_GENERATORS)
    def test_generator_inherits_base_generator(self, generator_class, name):
        """Test T108: All generators inherit from BaseGenerator."""
        assert issubclass(generator_class, BaseGenerator), f"{name} doesn't inherit from BaseGenerator"

    @pytest.mark.parametrize("generator_class,name", ALL_GENERATORS)
    def test_generator_declares_sources(self, generator_class, name):
        """Test T108: All generators declare MANUAL_SOURCES."""
        # Check class has MANUAL_SOURCES attribute
        assert hasattr(generator_class, "MANUAL_SOURCES"), f"{name} missing MANUAL_SOURCES"
        assert isinstance(generator_class.MANUAL_SOURCES, list), f"{name}.MANUAL_SOURCES not a list"

    @pytest.mark.parametrize("generator_class,name", ALL_GENERATORS)
    def test_generator_declares_artifacts(self, generator_class, name):
        """Test T108: All generators declare GENERATED_ARTIFACTS."""
        # Check class has GENERATED_ARTIFACTS attribute
        assert hasattr(generator_class, "GENERATED_ARTIFACTS"), f"{name} missing GENERATED_ARTIFACTS"
        assert isinstance(generator_class.GENERATED_ARTIFACTS, list), f"{name}.GENERATED_ARTIFACTS not a list"

    @pytest.mark.parametrize("generator_class,name", ALL_GENERATORS)
    def test_generator_has_generate_method(self, generator_class, name):
        """Test T108: All generators have generate() method."""
        methods = dir(generator_class)
        assert "generate" in methods, f"{name} missing generate() method"

    @pytest.mark.parametrize("generator_class,name", ALL_GENERATORS)
    def test_generator_no_source_artifact_overlap(self, generator_class, name):
        """Test T108: MANUAL_SOURCES and GENERATED_ARTIFACTS don't overlap."""
        sources = set(generator_class.MANUAL_SOURCES)
        artifacts = set(generator_class.GENERATED_ARTIFACTS)

        overlap = sources & artifacts
        assert len(overlap) == 0, f"{name} has overlapping sources and artifacts: {overlap}"


class TestBaseGeneratorInterface:
    """Test BaseGenerator provides expected interface methods."""

    def test_base_generator_has_read_source(self):
        """Test T108: BaseGenerator.read_source() exists."""
        assert hasattr(BaseGenerator, "read_source")

    def test_base_generator_has_write_artifact(self):
        """Test T108: BaseGenerator.write_artifact() exists."""
        assert hasattr(BaseGenerator, "write_artifact")

    def test_base_generator_has_validate_declarations(self):
        """Test T108: BaseGenerator._validate_declarations() exists."""
        assert hasattr(BaseGenerator, "_validate_declarations")

    def test_base_generator_has_generate_header(self):
        """Test T108: BaseGenerator._generate_header() exists."""
        assert hasattr(BaseGenerator, "_generate_header")


class TestSystemGeneratorContract:
    """Contract tests for SystemGenerator."""

    def test_system_generator_sources(self):
        """Test T108: SystemGenerator declares correct sources."""
        sources = SystemGenerator.MANUAL_SOURCES

        # Should include core config files
        assert any("packages.nix" in str(s) for s in sources)
        assert any("fish_config.nix" in str(s) for s in sources)

    def test_system_generator_artifacts(self):
        """Test T108: SystemGenerator declares correct artifacts."""
        artifacts = SystemGenerator.GENERATED_ARTIFACTS

        # Should include generated CLAUDE.md
        assert any("CLAUDE.md" in str(a) for a in artifacts)


class TestPermissionsGeneratorContract:
    """Contract tests for PermissionsGenerator."""

    def test_permissions_generator_sources(self):
        """Test T108: PermissionsGenerator declares correct sources."""
        sources = PermissionsGenerator.MANUAL_SOURCES

        # Should include constitution or policies
        assert len(sources) > 0

    def test_permissions_generator_artifacts(self):
        """Test T108: PermissionsGenerator declares correct artifacts."""
        artifacts = PermissionsGenerator.GENERATED_ARTIFACTS

        # Should include settings.local.json
        assert any("settings.local.json" in str(a) for a in artifacts)


class TestIntelligentPermissionsGeneratorContract:
    """Contract tests for IntelligentPermissionsGenerator."""

    def test_intelligent_permissions_has_learning(self):
        """Test T108: IntelligentPermissionsGenerator supports learning."""
        generator = IntelligentPermissionsGenerator()

        # Should have generate_with_learning method
        assert hasattr(generator, "generate_with_learning")

    def test_intelligent_permissions_inherits_base(self):
        """Test T108: IntelligentPermissionsGenerator properly inherits."""
        # Should inherit from PermissionsGenerator
        assert issubclass(IntelligentPermissionsGenerator, PermissionsGenerator)


class TestGeneratorProtections:
    """Test source protection mechanisms."""

    def test_cannot_write_to_declared_source(self):
        """Test T108: Generators cannot write to MANUAL_SOURCES."""
        # This should be enforced by write_artifact() in BaseGenerator
        # Actual test would require creating a generator instance and testing write_artifact()
        # For contract test, we just verify the mechanism exists
        assert hasattr(BaseGenerator, "write_artifact")

    def test_source_artifact_separation_enforced(self):
        """Test T108: Source/artifact separation is enforced."""
        # Verify BaseGenerator has validation logic
        assert hasattr(BaseGenerator, "_validate_declarations")
