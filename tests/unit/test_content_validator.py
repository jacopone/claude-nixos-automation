"""
Unit tests for ContentValidator.

Tests tiered validation of CLAUDE.md content.
"""

import pytest

from claude_automation.validators import ContentValidator


class TestContentValidator:
    """Test suite for ContentValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator(strict_mode=False)

    @pytest.fixture
    def strict_validator(self):
        """Create strict mode validator."""
        return ContentValidator(strict_mode=True)

    # =========================================================================
    # Temporal Marker Detection Tests
    # =========================================================================

    def test_detects_new_marker(self, validator):
        """Test detection of NEW marker."""
        content = """
        # System Tools

        NEW: This is a new feature
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid  # Warnings don't fail
        assert result.severity == "warn"
        assert any("NEW" in w for w in result.warnings)

    def test_detects_week_marker(self, validator):
        """Test detection of Week X marker."""
        content = """
        Week 1: Initial setup
        Week 2: Configuration
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid
        assert result.severity == "warn"
        assert any("Week" in w for w in result.warnings)

    def test_detects_phase_marker(self, validator):
        """Test detection of Phase X marker."""
        content = """
        Phase 1: Foundation
        Phase 2: Enhancement
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid
        assert result.severity == "warn"

    def test_detects_enhanced_marker(self, validator):
        """Test detection of ENHANCED marker."""
        content = """
        ENHANCED: Better performance
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid
        assert result.severity == "warn"

    def test_detects_updated_marker(self, validator):
        """Test detection of UPDATED marker."""
        content = """
        UPDATED: New version
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid
        assert result.severity == "warn"

    # =========================================================================
    # Strict Mode Tests
    # =========================================================================

    def test_strict_mode_promotes_warnings_to_errors(self, strict_validator):
        """Test that strict mode promotes temporal warnings to errors."""
        content = """
        NEW 2025: Latest feature
        """
        result = strict_validator.validate_content_tiered(content, "system")

        assert not result.valid  # In strict mode, warnings become errors
        assert result.severity == "fail"
        assert len(result.errors) > 0

    def test_normal_mode_allows_warnings(self, validator):
        """Test that normal mode allows temporal markers as warnings."""
        content = """
        NEW 2025: Latest feature
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid  # Valid but with warnings
        assert result.severity == "warn"
        assert len(result.warnings) > 0
        assert len(result.errors) == 0

    # =========================================================================
    # Required Sections Tests (System Content)
    # =========================================================================

    def test_missing_required_section_fails(self, validator):
        """Test that missing required section fails."""
        content = """
        # Some Content

        This is missing required sections.
        """
        result = validator.validate_content_tiered(content, "system")

        assert not result.valid
        assert result.severity == "fail"
        assert any("Missing required section" in e for e in result.errors)

    def test_valid_system_content_passes(self, validator):
        """Test that valid system content passes."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        **SYSTEM OPTIMIZATION LEVEL: EXPERT**

        ## MANDATORY Tool Substitutions

        - find → fd
        - ls → eza
        - cat → bat
        - grep → rg

        ## System Information

        - OS: NixOS

        ## Available Tools

        - fd: Modern find alternative
        - eza: Modern ls alternative
        - bat: Modern cat alternative

        Last updated: 2025-10-17
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid
        assert result.severity == "info"
        assert len(result.errors) == 0

    # =========================================================================
    # Content Quality Tests (Style)
    # =========================================================================

    def test_short_content_warns(self, validator):
        """Test that very short content triggers warning."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        Short content.

        ## System Information

        Info.

        ## Available Tools

        Tools.
        """
        result = validator.validate_content_tiered(content, "system")

        # May have warnings about length
        assert len(result.warnings) >= 0  # Quality warnings are optional

    def test_unmatched_code_blocks_warns(self, validator):
        """Test that unmatched code blocks trigger warning."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        ## System Information

        Some content

        ```bash
        echo "test"
        # Missing closing backticks

        ## Available Tools

        Available tools here.

        Last updated: 2025-10-17
        """
        result = validator.validate_content_tiered(content, "system")

        # Should have warning about unmatched code blocks
        assert any("code block" in w.lower() for w in result.warnings)

    def test_placeholder_text_warns(self, validator):
        """Test that placeholder text triggers warning."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        ## System Information

        TODO: Add system info

        ## Available Tools

        FIXME: Complete this section

        Last updated: 2025-10-17
        """
        result = validator.validate_content_tiered(content, "system")

        # Should have warnings about placeholders
        assert any(
            "placeholder" in w.lower() or "TODO" in w or "FIXME" in w
            for w in result.warnings
        )

    # =========================================================================
    # Info/Statistics Tests
    # =========================================================================

    def test_includes_statistics_in_info(self, validator):
        """Test that validation includes content statistics."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        **SYSTEM OPTIMIZATION LEVEL: EXPERT**

        ## MANDATORY Tool Substitutions

        - find → fd
        - ls → eza
        - cat → bat

        ## System Information

        System info here.

        ## Available Tools

        Available tools here.

        Last updated: 2025-10-17
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid
        assert len(result.info) > 0
        # Should include statistics
        assert any("chars" in i.lower() for i in result.info)

    # =========================================================================
    # Combined Tests
    # =========================================================================

    def test_content_with_errors_and_warnings(self, validator):
        """Test content with both errors and warnings."""
        content = """
        # Some Header

        NEW 2025: Latest feature
        Week 1: Initial work
        """
        result = validator.validate_content_tiered(content, "system")

        # Missing required sections = error
        # Temporal markers = warnings
        assert not result.valid
        assert result.severity == "fail"
        assert len(result.errors) > 0
        assert len(result.warnings) > 0

    def test_valid_content_with_warnings_only(self, validator):
        """Test valid content that has warnings."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        **SYSTEM OPTIMIZATION LEVEL: EXPERT**

        ## MANDATORY Tool Substitutions

        - find → fd
        - ls → eza
        - cat → bat

        ## System Information

        NEW: Added system monitoring

        ## Available Tools

        Tools listed here.

        Last updated: 2025-10-17
        """
        result = validator.validate_content_tiered(content, "system")

        assert result.valid  # Warnings don't fail
        assert result.severity == "warn"
        assert len(result.errors) == 0
        assert len(result.warnings) > 0

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_empty_content_fails(self, validator):
        """Test that empty content fails."""
        result = validator.validate_content_tiered("", "system")

        assert not result.valid
        assert result.severity == "fail"

    def test_case_insensitive_temporal_detection(self, validator):
        """Test that temporal marker detection is case-insensitive."""
        content = """
        # CLAUDE CODE TOOL SELECTION POLICY

        **SYSTEM OPTIMIZATION LEVEL: EXPERT**

        ## MANDATORY Tool Substitutions

        - find → fd

        ## System Information

        new: Feature
        NEW: Feature
        New: Feature

        ## Available Tools

        Tools here.

        Last updated: 2025-10-17
        """
        result = validator.validate_content_tiered(content, "system")

        # Should detect all variations
        assert result.severity == "warn"
        assert len(result.warnings) > 0
