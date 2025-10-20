"""
Integration test for source/artifact protection.

Tests end-to-end protection of source files from being overwritten.
"""


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

        # Create source files
        packages_file = modules / "packages.nix"
        packages_file.write_text("""
        {pkgs, ...}: {
          environment.systemPackages = with pkgs; [
            fd
            eza
            bat
          ];
        }
        """)

        base_file = home_modules / "base.nix"
        base_file.write_text("""
        {pkgs, ...}: {
          home.packages = with pkgs; [
            ripgrep
          ];
        }
        """)

        # Create .git directory to mark as repo
        git_dir = project / ".git"
        git_dir.mkdir()

        return project

    def test_generator_cannot_overwrite_source_files(self, temp_project):
        """Test that generator cannot overwrite declared source files."""
        generator = SystemGenerator()

        # Try to write to a source file (packages.nix)
        source_file = temp_project / "modules" / "core" / "packages.nix"
        assert source_file.exists()

        original_content = source_file.read_text()

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

        # Should be able to write artifact
        result = generator.write_artifact(
            artifact_path,
            "# System CLAUDE.md\n\nGenerated content",
            source_files=["packages.nix", "base.nix"],
        )

        assert result.success
        assert artifact_path.exists()

        # Content should include header
        content = artifact_path.read_text()
        assert "AUTO-GENERATED" in content
        assert "Generated content" in content

    def test_full_generation_cycle(self, temp_project):
        """Test full generation cycle with proper source reading and artifact writing."""
        generator = SystemGenerator()

        # Output artifact
        output_path = temp_project / "CLAUDE.md"

        # Generate (this reads sources and writes artifact)
        result = generator.generate(output_path, config_dir=temp_project)

        # Should succeed
        assert result.success

        # Artifact should exist
        assert output_path.exists()

        # Should have generation header
        content = output_path.read_text()
        assert "<!--" in content
        assert "AUTO-GENERATED" in content
        assert "SystemGenerator" in content

        # Should have actual content (tool substitutions, etc.)
        assert "fd" in content or "eza" in content or "bat" in content

    def test_artifact_update_preserves_sources(self, temp_project):
        """Test that updating artifact doesn't affect source files."""
        generator = SystemGenerator()

        # Record original source content
        packages_file = temp_project / "modules" / "core" / "packages.nix"
        original_packages = packages_file.read_text()

        # Generate artifact
        output_path = temp_project / "CLAUDE.md"
        result1 = generator.generate(output_path, config_dir=temp_project)
        assert result1.success

        # Generate again (update)
        result2 = generator.generate(output_path, config_dir=temp_project)
        assert result2.success

        # Source files should be unchanged
        assert packages_file.read_text() == original_packages

        # Artifact should have been updated (different timestamp)
        content1 = output_path.read_text()
        content2 = output_path.read_text()

        # Both should have headers
        assert "AUTO-GENERATED" in content1
        assert "AUTO-GENERATED" in content2

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
                    return GenerationResult(success=True, output_path="", errors=[], warnings=[], stats={})

            BadGenerator()

        assert "overlap" in str(exc_info.value).lower()
