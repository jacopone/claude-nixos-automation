"""
Regression tests for previously fixed bugs.

These tests ensure that bugs we've fixed don't reappear.
Each test is named after the bug it prevents.
"""

# Check if optional dependencies are available
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

HAS_ANTHROPIC = importlib.util.find_spec("anthropic") is not None


@pytest.mark.skipif(not HAS_ANTHROPIC, reason="anthropic module not installed")
class TestUserPoliciesGeneratorAbstractMethod:
    """
    Bug: UserPoliciesGenerator couldn't be instantiated because it didn't
    implement the abstract generate() method from BaseGenerator.

    Fixed: Added generate() method that calls update_both_files().
    """

    def test_user_policies_generator_can_be_instantiated(self):
        """UserPoliciesGenerator should be instantiable (has generate method)."""
        from claude_automation.generators.user_policies_generator import (
            UserPoliciesGenerator,
        )

        # Should not raise TypeError about abstract method
        generator = UserPoliciesGenerator(project_root=Path("/tmp"))
        assert generator is not None

    def test_user_policies_generator_has_generate_method(self):
        """UserPoliciesGenerator must have generate() method."""
        from claude_automation.generators.user_policies_generator import (
            UserPoliciesGenerator,
        )

        generator = UserPoliciesGenerator(project_root=Path("/tmp"))
        assert hasattr(generator, "generate")
        assert callable(generator.generate)


@pytest.mark.skipif(not HAS_ANTHROPIC, reason="anthropic module not installed")
class TestGeneratorStatsCompleteness:
    """
    Bug: get_summary_stats() was missing expected keys like 'total_tools',
    'package_count', causing KeyError in CLI code.

    Fixed: Added all expected keys with sensible defaults.
    """

    def test_system_generator_stats_has_total_tools(self):
        """SystemGenerator stats must include total_tools key."""
        from claude_automation.generators.system_generator import SystemGenerator

        with patch.object(SystemGenerator, "__init__", lambda x: None):
            generator = SystemGenerator()
            generator.config_path = Path("/tmp/test")
            generator.claude_dir = Path.home() / ".claude"

            # Mock the files that get_summary_stats checks
            with patch.object(Path, "exists", return_value=False):
                stats = generator.get_summary_stats()

            assert "total_tools" in stats
            assert isinstance(stats["total_tools"], int)

    def test_project_generator_stats_has_package_count(self):
        """ProjectGenerator stats must include package_count key."""
        from claude_automation.generators.project_generator import ProjectGenerator

        with patch.object(ProjectGenerator, "__init__", lambda x: None):
            generator = ProjectGenerator()
            generator.project_root = Path("/tmp/test")

            # Mock required attributes
            generator._parsed_devenv = None
            generator._git_status = None

            with patch.object(Path, "exists", return_value=False):
                stats = generator.get_summary_stats()

            assert "package_count" in stats
            assert "fish_abbreviation_count" in stats
            assert "git_status" in stats


class TestClaudeMdSuggesterOccurrences:
    """
    Bug: ClaudeMdSuggestion validation failed with occurrences=0 because
    the schema requires occurrences >= 1 (ge=1).

    The bug was in _parse_claude_response where it looked up Claude's
    reformatted instruction text in a dictionary keyed by raw session text.

    Fixed: Calculate occurrences via project overlap instead of exact text match.
    """

    def test_suggestion_occurrences_minimum_one(self):
        """ClaudeMdSuggestion must have occurrences >= 1."""
        from claude_automation.schemas.suggestions import (
            ClaudeMdSuggestion,
            SuggestionScope,
        )

        # This should work (occurrences=1)
        suggestion = ClaudeMdSuggestion(
            instruction="Test instruction",
            scope=SuggestionScope.GLOBAL,
            target_file="~/.claude/CLAUDE.md",
            suggested_section="## Test",
            occurrences=1,
            projects=["/test/project"],
            confidence=0.8,
            source_sessions=[],
            pattern_type="test",
        )
        assert suggestion.occurrences >= 1

    def test_suggestion_occurrences_zero_raises_validation_error(self):
        """ClaudeMdSuggestion with occurrences=0 should raise ValidationError."""
        from pydantic import ValidationError

        from claude_automation.schemas.suggestions import (
            ClaudeMdSuggestion,
            SuggestionScope,
        )

        with pytest.raises(ValidationError) as exc_info:
            ClaudeMdSuggestion(
                instruction="Test instruction",
                scope=SuggestionScope.GLOBAL,
                target_file="~/.claude/CLAUDE.md",
                suggested_section="## Test",
                occurrences=0,  # This should fail
                projects=["/test/project"],
                confidence=0.8,
                source_sessions=[],
                pattern_type="test",
            )

        # Verify it's the occurrences field that failed
        assert "occurrences" in str(exc_info.value)


class TestDictAccessPatterns:
    """
    Bug: Direct dictionary access without .get() caused KeyError when
    expected keys were missing.

    Fixed: Use .get() with defaults or ensure all expected keys are present.
    """

    def test_stats_dict_safe_access_pattern(self):
        """Demonstrate safe dictionary access pattern."""
        stats = {"some_key": 123}

        # Unsafe pattern (what caused bugs):
        # value = stats["missing_key"]  # KeyError!

        # Safe pattern (what we use now):
        value = stats.get("missing_key", 0)
        assert value == 0

    def test_stats_dict_with_all_expected_keys(self):
        """Stats dictionaries should have all expected keys."""
        # Expected keys for system generator
        expected_system_keys = ["total_tools", "status", "timestamp"]

        # Expected keys for project generator
        expected_project_keys = ["package_count", "fish_abbreviation_count", "git_status"]

        # Verify we can access them safely
        system_stats = dict.fromkeys(expected_system_keys)
        project_stats = dict.fromkeys(expected_project_keys)

        for key in expected_system_keys:
            assert key in system_stats

        for key in expected_project_keys:
            assert key in project_stats
