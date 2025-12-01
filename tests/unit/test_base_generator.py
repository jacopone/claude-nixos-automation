"""
Unit tests for BaseGenerator.

Tests source/artifact protection and generation header functionality.
"""

from pathlib import Path

import pytest

from claude_automation.generators import BaseGenerator
from claude_automation.schemas import GenerationResult


# Test generators for testing
class ValidGenerator(BaseGenerator):
    """Valid generator with proper declarations."""

    MANUAL_SOURCES = ["config.nix", "packages.nix"]
    GENERATED_ARTIFACTS = ["CLAUDE.md", "output.md"]

    def generate(self) -> GenerationResult:
        """Dummy generate method."""
        return GenerationResult(
            success=True,
            output_path="test.md",
            errors=[],
            warnings=[],
            stats={},
        )


class OverlappingGenerator(BaseGenerator):
    """Invalid generator with overlapping declarations."""

    MANUAL_SOURCES = ["config.nix", "CLAUDE.md"]
    GENERATED_ARTIFACTS = ["CLAUDE.md", "output.md"]

    def generate(self) -> GenerationResult:
        """Dummy generate method."""
        return GenerationResult(
            success=True, output_path="", errors=[], warnings=[], stats={}
        )


class DuplicateSourcesGenerator(BaseGenerator):
    """Invalid generator with duplicate sources."""

    MANUAL_SOURCES = ["config.nix", "config.nix", "packages.nix"]
    GENERATED_ARTIFACTS = ["CLAUDE.md"]

    def generate(self) -> GenerationResult:
        """Dummy generate method."""
        return GenerationResult(
            success=True, output_path="", errors=[], warnings=[], stats={}
        )


class TestBaseGeneratorDeclarations:
    """Test source/artifact declaration validation."""

    def test_valid_declarations_accepted(self):
        """Test that valid declarations are accepted."""
        gen = ValidGenerator()
        assert len(gen.MANUAL_SOURCES) == 2
        assert len(gen.GENERATED_ARTIFACTS) == 2

    def test_overlapping_declarations_rejected(self):
        """Test that overlapping declarations are rejected."""
        with pytest.raises(ValueError) as exc_info:
            OverlappingGenerator()

        assert "overlap detected" in str(exc_info.value).lower()
        assert "CLAUDE.md" in str(exc_info.value)

    def test_duplicate_sources_rejected(self):
        """Test that duplicate sources are rejected."""
        with pytest.raises(ValueError) as exc_info:
            DuplicateSourcesGenerator()

        assert "duplicate" in str(exc_info.value).lower()

    def test_empty_declarations_allowed(self):
        """Test that empty declarations are allowed."""

        class EmptyGenerator(BaseGenerator):
            MANUAL_SOURCES = []
            GENERATED_ARTIFACTS = []

            def generate(self):
                return GenerationResult(
                    success=True, output_path="", errors=[], warnings=[], stats={}
                )

        gen = EmptyGenerator()
        assert len(gen.MANUAL_SOURCES) == 0
        assert len(gen.GENERATED_ARTIFACTS) == 0


class TestBaseGeneratorReadSource:
    """Test read_source() method."""

    @pytest.fixture
    def generator(self):
        """Create valid generator."""
        return ValidGenerator()

    @pytest.fixture
    def temp_source_file(self, tmp_path):
        """Create temporary source file."""
        source_file = tmp_path / "config.nix"
        source_file.write_text("# Test config")
        return source_file

    def test_read_declared_source(self, generator, temp_source_file):
        """Test reading a declared source file."""
        content = generator.read_source(temp_source_file)
        assert content == "# Test config"

    def test_read_undeclared_source_warns(self, generator, tmp_path, caplog):
        """Test reading undeclared source logs warning."""
        undeclared = tmp_path / "undeclared.nix"
        undeclared.write_text("# Undeclared")

        content = generator.read_source(undeclared)
        assert content == "# Undeclared"

        # Should have warning about undeclared source
        assert any("undeclared" in record.message.lower() for record in caplog.records)

    def test_read_nonexistent_source_raises(self, generator, tmp_path):
        """Test reading nonexistent file raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist.nix"

        with pytest.raises(FileNotFoundError):
            generator.read_source(nonexistent)


class TestBaseGeneratorWriteArtifact:
    """Test write_artifact() method with source protection."""

    @pytest.fixture
    def generator(self):
        """Create valid generator."""
        return ValidGenerator()

    @pytest.fixture
    def artifact_path(self, tmp_path):
        """Create artifact path."""
        return tmp_path / "CLAUDE.md"

    @pytest.fixture
    def source_path(self, tmp_path):
        """Create source path."""
        source = tmp_path / "config.nix"
        source.write_text("# Source file")
        return source

    # =========================================================================
    # Protection Tests
    # =========================================================================

    def test_cannot_write_to_source_file(self, generator, source_path):
        """Test that writing to a source file raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            generator.write_artifact(source_path, "new content")

        assert "PROTECTION VIOLATION" in str(exc_info.value)
        assert "source file" in str(exc_info.value).lower()
        assert "config.nix" in str(exc_info.value)

    def test_cannot_write_to_undeclared_artifact(self, generator, tmp_path):
        """Test that writing to undeclared artifact raises ValueError."""
        undeclared = tmp_path / "undeclared.md"

        with pytest.raises(ValueError) as exc_info:
            generator.write_artifact(undeclared, "content")

        assert "undeclared artifact" in str(exc_info.value).lower()

    def test_can_write_to_declared_artifact(self, generator, artifact_path):
        """Test that writing to declared artifact succeeds."""
        result = generator.write_artifact(
            artifact_path, "Content here", source_files=["config.nix"]
        )

        assert result.success
        assert artifact_path.exists()

    # =========================================================================
    # Header Tests
    # =========================================================================

    def test_artifact_includes_header(self, generator, artifact_path):
        """Test that generated artifact includes HTML comment header."""
        result = generator.write_artifact(
            artifact_path, "Main content", source_files=["config.nix", "packages.nix"]
        )

        assert result.success

        content = artifact_path.read_text()

        # Check for header components
        assert "AUTO-GENERATED FILE" in content
        assert "DO NOT EDIT DIRECTLY" in content
        assert "Generator: ValidGenerator" in content
        assert "config.nix" in content
        assert "packages.nix" in content
        assert "<!--" in content
        assert "-->" in content

        # Check that actual content is present
        assert "Main content" in content

    def test_header_is_html_comment(self, generator, artifact_path):
        """Test that header uses HTML comment format."""
        result = generator.write_artifact(artifact_path, "Content", source_files=[])

        assert result.success

        content = artifact_path.read_text()
        lines = content.split("\n")

        # First line should start with <!--
        assert lines[0].startswith("<!--")

        # Should have closing -->
        assert any("-->" in line for line in lines[:20])

    def test_header_includes_timestamp(self, generator, artifact_path):
        """Test that header includes generation timestamp."""
        result = generator.write_artifact(artifact_path, "Content")

        assert result.success

        content = artifact_path.read_text()

        # Should contain a timestamp
        assert "Generated:" in content or "generated_at" in content.lower()

    def test_header_includes_source_files(self, generator, artifact_path):
        """Test that header lists source files."""
        source_files = ["config.nix", "packages.nix", "home.nix"]
        result = generator.write_artifact(
            artifact_path, "Content", source_files=source_files
        )

        assert result.success

        content = artifact_path.read_text()

        for source in source_files:
            assert source in content

    def test_header_with_no_sources(self, generator, artifact_path):
        """Test header generation with no source files."""
        result = generator.write_artifact(artifact_path, "Content", source_files=[])

        assert result.success

        content = artifact_path.read_text()

        # Should still have header
        assert "AUTO-GENERATED" in content
        # Should indicate no sources or N/A
        assert "N/A" in content or "Sources:" in content

    # =========================================================================
    # Backup Tests
    # =========================================================================

    def test_creates_backup_of_existing_artifact(self, generator, artifact_path):
        """Test that write_artifact creates backup of existing file."""
        # Create initial artifact
        artifact_path.write_text("Old content")

        # Update it
        result = generator.write_artifact(
            artifact_path, "New content", create_backup=True
        )

        assert result.success
        assert result.backup_path is not None

        # Backup should exist
        backup_path = Path(result.backup_path)
        assert backup_path.exists()

        # Backup should contain old content (without header since we wrote it directly)
        backup_content = backup_path.read_text()
        assert "Old content" in backup_content

    def test_no_backup_for_new_artifact(self, generator, artifact_path):
        """Test that no backup is created for new file."""
        result = generator.write_artifact(artifact_path, "Content")

        assert result.success
        assert result.backup_path is None

    def test_can_disable_backup(self, generator, artifact_path):
        """Test that backup can be disabled."""
        artifact_path.write_text("Old content")

        result = generator.write_artifact(
            artifact_path, "New content", create_backup=False
        )

        assert result.success
        assert result.backup_path is None

    # =========================================================================
    # Result Metadata Tests
    # =========================================================================

    def test_result_includes_header_metadata(self, generator, artifact_path):
        """Test that GenerationResult includes header metadata."""
        source_files = ["config.nix"]
        result = generator.write_artifact(
            artifact_path, "Content", source_files=source_files
        )

        assert result.success
        assert result.stats["header_added"] is True
        assert result.stats["source_files"] == source_files

    def test_result_includes_file_stats(self, generator, artifact_path):
        """Test that result includes file statistics."""
        result = generator.write_artifact(artifact_path, "Test content")

        assert result.success
        assert "file_size" in result.stats
        assert "line_count" in result.stats
        assert result.stats["file_size"] > 0


class TestBaseGeneratorAbstractMethod:
    """Test that generate() is properly abstract."""

    def test_cannot_instantiate_without_generate(self):
        """Test that BaseGenerator requires generate() implementation."""

        class IncompleteGenerator(BaseGenerator):
            MANUAL_SOURCES = []
            GENERATED_ARTIFACTS = []
            # Missing generate() method

        # Should not be able to instantiate without implementing generate()
        with pytest.raises(TypeError) as exc_info:
            IncompleteGenerator()

        assert "abstract" in str(exc_info.value).lower()

    def test_can_instantiate_with_generate(self):
        """Test that implementing generate() allows instantiation."""

        class CompleteGenerator(BaseGenerator):
            MANUAL_SOURCES = []
            GENERATED_ARTIFACTS = []

            def generate(self):
                return GenerationResult(
                    success=True, output_path="", errors=[], warnings=[], stats={}
                )

        gen = CompleteGenerator()
        assert gen is not None
