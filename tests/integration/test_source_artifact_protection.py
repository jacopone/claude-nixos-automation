"""
Integration test for source/artifact protection.

Tests end-to-end protection of source files from being overwritten.

Note: After refactoring (2025-12), SystemGenerator no longer reads packages.nix.
It only uses CLAUDE-USER-POLICIES.md as a source. Tool extraction was removed
in favor of MCP-NixOS for dynamic package queries.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_automation.generators import SystemGenerator


class TestSourceArtifactProtection:
    """Integration tests for source/artifact protection."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure."""
        # Create project structure
        project = tmp_path / "nixos-config"
        project.mkdir()

        modules = project / "modules" / "core"
        modules.mkdir(parents=True)

        home_modules = project / "modules" / "home-manager"
        home_modules.mkdir(parents=True)

        # Create .claude directory with user policies
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True)

        policies_file = claude_dir / "CLAUDE-USER-POLICIES.md"
        policies_file.write_text("""
# User Policies

Never use git commit --no-verify.
        """)

        # Create .git directory to mark as repo
        git_dir = project / ".git"
        git_dir.mkdir()

        return project

    def test_generator_cannot_overwrite_source_files(self, tmp_path):
        """Test that generator cannot overwrite declared source files.

        Note: SystemGenerator now only has CLAUDE-USER-POLICIES.md as a source.
        We mock Path.home() to use our temp directory for this test.
        """
        generator = SystemGenerator()

        # Create policies file in temp home
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True)
        source_file = claude_dir / "CLAUDE-USER-POLICIES.md"
        source_file.write_text("# User Policies\n\nOriginal content")

        original_content = source_file.read_text()

        # Mock Path.home() to return our temp directory
        with patch.object(Path, "home", return_value=tmp_path):
            # Attempting to write to source should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                generator.write_artifact(source_file, "MALICIOUS OVERWRITE")

            assert "PROTECTION VIOLATION" in str(exc_info.value)
            assert "source file" in str(exc_info.value).lower()

        # Source file should be unchanged
        assert source_file.read_text() == original_content

    def test_generator_can_write_artifacts(self, temp_project):
        """Test that generator can write declared artifacts."""
        generator = SystemGenerator()

        artifact_path = temp_project / "CLAUDE.md"

        # Should be able to write artifact (source_files now just user policies)
        result = generator.write_artifact(
            artifact_path,
            "# System CLAUDE.md\n\nGenerated content",
            source_files=["CLAUDE-USER-POLICIES.md"],
        )

        assert result.success
        assert artifact_path.exists()

        # Content should include header
        content = artifact_path.read_text()
        assert "AUTO-GENERATED" in content
        assert "Generated content" in content

    def test_full_generation_cycle(self, tmp_path):
        """Test full generation cycle with proper source reading and artifact writing.

        Note: Uses tmp_path to mock user policies location.
        """
        generator = SystemGenerator()

        # Create project dir
        project = tmp_path / "nixos-config"
        project.mkdir()

        # Create .git to mark as repo
        (project / ".git").mkdir()

        # Create user policies in mock home
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True)
        policies_file = claude_dir / "CLAUDE-USER-POLICIES.md"
        policies_file.write_text("# User Policies\n\nNever skip hooks.")

        # Output artifact
        output_path = project / "CLAUDE.md"

        # Generate (mock home to find policies)
        with patch.object(Path, "home", return_value=tmp_path):
            result = generator.generate(output_path, config_dir=project)

        # Should succeed
        assert result.success

        # Artifact should exist
        assert output_path.exists()

        # Should have generation header
        content = output_path.read_text()
        assert "<!--" in content
        assert "AUTO-GENERATED" in content
        assert "SystemGenerator" in content

        # Should have policy content (tool lists removed in favor of MCP-NixOS)
        assert "USER-DEFINED POLICIES" in content or "TOOL SELECTION POLICY" in content

    def test_artifact_update_preserves_sources(self, tmp_path):
        """Test that updating artifact doesn't affect source files."""
        generator = SystemGenerator()

        # Create user policies in mock home
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True)
        policies_file = claude_dir / "CLAUDE-USER-POLICIES.md"
        policies_file.write_text("# User Policies\n\nOriginal policies.")
        original_policies = policies_file.read_text()

        # Create project dir
        project = tmp_path / "nixos-config"
        project.mkdir()
        (project / ".git").mkdir()

        # Generate artifact with mocked home
        output_path = project / "CLAUDE.md"
        with patch.object(Path, "home", return_value=tmp_path):
            result1 = generator.generate(output_path, config_dir=project)
            assert result1.success

            # Generate again (update)
            result2 = generator.generate(output_path, config_dir=project)
            assert result2.success

        # Source files should be unchanged
        assert policies_file.read_text() == original_policies

        # Artifact should have been updated
        content = output_path.read_text()

        # Should have headers
        assert "AUTO-GENERATED" in content

    def test_declaration_validation_at_init(self):
        """Test that invalid declarations are caught at initialization."""

        # This should fail because of overlapping declarations
        with pytest.raises(ValueError) as exc_info:
            from claude_automation.generators.base_generator import BaseGenerator
            from claude_automation.schemas import GenerationResult

            class BadGenerator(BaseGenerator):
                MANUAL_SOURCES = ["config.nix", "CLAUDE.md"]
                GENERATED_ARTIFACTS = ["CLAUDE.md"]

                def generate(self):
                    return GenerationResult(
                        success=True, output_path="", errors=[], warnings=[], stats={}
                    )

            BadGenerator()

        assert "overlap" in str(exc_info.value).lower()
