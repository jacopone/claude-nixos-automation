"""
Unit tests for PermissionValidator.

Tests validation of Claude Code permission strings.
"""

import pytest

from claude_automation.validators import PermissionValidator


class TestPermissionValidator:
    """Test suite for PermissionValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return PermissionValidator()

    # =========================================================================
    # Valid Permission Tests
    # =========================================================================

    def test_valid_bash_permission(self, validator):
        """Test valid Bash permission."""
        result = validator.validate("Bash(git status:*)")
        assert result.valid
        assert result.severity == "info"
        assert len(result.errors) == 0

    def test_valid_read_permission(self, validator):
        """Test valid Read permission."""
        result = validator.validate("Read(/home/user/project/**)")
        assert result.valid
        assert result.severity == "info"

    def test_valid_write_permission(self, validator):
        """Test valid Write permission."""
        result = validator.validate("Write(/home/user/project/output.txt)")
        assert result.valid

    def test_valid_glob_permission(self, validator):
        """Test valid Glob permission."""
        result = validator.validate("Glob(src/**/*.py)")
        assert result.valid

    # =========================================================================
    # Critical Failure Tests (FAIL)
    # =========================================================================

    def test_empty_permission_fails(self, validator):
        """Test that empty permission fails."""
        result = validator.validate("")
        assert not result.valid
        assert result.severity == "fail"
        assert "cannot be empty" in result.errors[0].lower()

    def test_whitespace_only_permission_fails(self, validator):
        """Test that whitespace-only permission fails."""
        result = validator.validate("   ")
        assert not result.valid
        assert result.severity == "fail"

    def test_permission_with_newline_fails(self, validator):
        """Test that permission with newline fails."""
        result = validator.validate("Bash(git status:*)\nBash(git diff:*)")
        assert not result.valid
        assert result.severity == "fail"
        assert "cannot contain newlines" in result.errors[0].lower()

    def test_permission_with_heredoc_fails(self, validator):
        """Test that permission with heredoc marker fails."""
        result = validator.validate("Bash(cat <<EOF)")
        assert not result.valid
        assert "heredoc" in result.errors[0].lower()

    def test_permission_with_eof_fails(self, validator):
        """Test that permission with EOF marker fails."""
        result = validator.validate("Bash(echo 'test' EOF)")
        assert not result.valid
        assert "heredoc" in result.errors[0].lower()

    def test_permission_too_long_fails(self, validator):
        """Test that overly long permission fails."""
        long_permission = "Bash(" + "a" * 200 + ")"
        result = validator.validate(long_permission)
        assert not result.valid
        assert "too long" in result.errors[0].lower()

    # =========================================================================
    # Warning Tests (WARN)
    # =========================================================================

    def test_permission_with_semicolon_warns(self, validator):
        """Test that semicolon triggers warning."""
        result = validator.validate("Bash(git status; git diff)")
        assert result.valid  # Still valid but...
        assert result.severity == "warn"
        assert len(result.warnings) > 0
        assert ";" in result.warnings[0]

    def test_permission_with_pipe_warns(self, validator):
        """Test that pipe character triggers warning."""
        result = validator.validate("Bash(git status | grep foo)")
        assert result.valid
        assert result.severity == "warn"

    def test_permission_with_traversal_warns(self, validator):
        """Test that .. triggers traversal warning."""
        result = validator.validate("Read(/home/user/../../etc/passwd)")
        assert result.valid
        assert result.severity == "warn"
        assert any("traversal" in w.lower() for w in result.warnings)

    def test_permission_accessing_etc_warns(self, validator):
        """Test that /etc access triggers warning."""
        result = validator.validate("Read(/etc/shadow)")
        assert result.valid
        assert result.severity == "warn"
        assert any("/etc" in w or "/sys" in w for w in result.warnings)

    def test_absolute_path_with_wildcard_warns(self, validator):
        """Test that absolute path + wildcard warns."""
        result = validator.validate("Read(/home/**/secrets.txt)")
        assert result.valid
        assert result.severity == "warn"

    # =========================================================================
    # Batch Validation Tests
    # =========================================================================

    def test_batch_validation_all_valid(self, validator):
        """Test batch validation with all valid permissions."""
        permissions = [
            "Bash(git status:*)",
            "Read(/home/user/project/**)",
            "Write(/tmp/output.txt)",
        ]
        results, all_valid = validator.validate_batch(permissions)

        assert len(results) == 3
        assert all_valid
        assert all(r.valid for r in results)

    def test_batch_validation_mixed(self, validator):
        """Test batch validation with mixed valid/invalid."""
        permissions = [
            "Bash(git status:*)",  # Valid
            "Bash(cat <<EOF)",  # Invalid (heredoc)
            "Read(/home/user/**)",  # Valid
            "",  # Invalid (empty)
        ]
        results, all_valid = validator.validate_batch(permissions)

        assert len(results) == 4
        assert not all_valid
        assert results[0].valid
        assert not results[1].valid
        assert results[2].valid
        assert not results[3].valid

    # =========================================================================
    # Report Generation Tests
    # =========================================================================

    def test_generate_report_all_pass(self, validator):
        """Test report generation for all passing."""
        permissions = ["Bash(git status:*)", "Read(/tmp/test.txt)"]
        results, _ = validator.validate_batch(permissions)

        report = validator.generate_report(results)

        assert "PERMISSION VALIDATION REPORT" in report
        assert "Total permissions: 2" in report
        assert "Valid: 2" in report
        assert "100.0%" in report

    def test_generate_report_with_failures(self, validator):
        """Test report generation with failures."""
        permissions = [
            "Bash(git status:*)",  # Valid
            "",  # Invalid
            "Bash(cat <<EOF)",  # Invalid
        ]
        results, _ = validator.validate_batch(permissions)

        report = validator.generate_report(results)

        assert "FAILURES:" in report
        assert "Total permissions: 3" in report
        assert "Failed: 2" in report

    def test_generate_report_with_warnings(self, validator):
        """Test report generation with warnings."""
        permissions = [
            "Bash(git status; git diff)",  # Warning
            "Read(/etc/passwd)",  # Warning
        ]
        results, _ = validator.validate_batch(permissions)

        report = validator.generate_report(results)

        assert "WARNINGS:" in report

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_permission_with_carriage_return_fails(self, validator):
        """Test that carriage return fails."""
        result = validator.validate("Bash(test)\rBash(test2)")
        assert not result.valid

    def test_permission_with_dollar_sign_warns(self, validator):
        """Test that $ triggers warning."""
        result = validator.validate("Bash(echo $HOME)")
        assert result.valid
        assert result.severity == "warn"

    def test_permission_with_backticks_warns(self, validator):
        """Test that backticks trigger warning."""
        result = validator.validate("Bash(echo `whoami`)")
        assert result.valid
        assert result.severity == "warn"

    def test_unusual_format_warns(self, validator):
        """Test that unusual format triggers warning."""
        result = validator.validate("SomeWeirdTool(arg1, arg2, arg3)")
        assert result.valid
        assert result.severity == "warn"  # Unusual format

    # =========================================================================
    # Bare Pattern Type Tests (NEW - Root cause fix for file_write_operations bug)
    # =========================================================================

    def test_bare_pattern_type_file_write_operations_fails(self, validator):
        """Test that bare pattern type 'file_write_operations' fails.

        This was the root cause of the recurring bug where 'file_write_operations'
        was being added to settings.local.json instead of proper expanded rules
        like 'Write(/**)' or 'Edit(/**)'.
        """
        result = validator.validate("file_write_operations")
        assert not result.valid
        assert result.severity == "fail"
        assert "bare pattern type" in result.errors[0].lower()

    def test_bare_pattern_type_capitalized_still_fails(self, validator):
        """Test that even capitalized bare pattern types fail."""
        result = validator.validate("File_write_operations")
        assert not result.valid
        assert result.severity == "fail"
        assert "bare pattern type" in result.errors[0].lower()

    def test_all_bare_pattern_types_fail(self, validator):
        """Test that all known bare pattern types are rejected."""
        bare_types = [
            "file_write_operations",
            "file_operations",
            "git_workflow",
            "git_read_only",
            "git_destructive",
            "test_execution",
            "modern_cli",
            "project_full_access",
            "github_cli",
            "cloud_cli",
            "package_managers",
            "nix_tools",
            "database_cli",
            "network_tools",
            "runtime_tools",
            "posix_filesystem",
            "posix_search",
            "posix_read",
            "shell_utilities",
            "dangerous_operations",
            "pytest",
            "ruff",
        ]
        for bare_type in bare_types:
            result = validator.validate(bare_type)
            assert not result.valid, f"Should reject bare pattern type: {bare_type}"
            assert result.severity == "fail"

    # =========================================================================
    # Tool Name Casing Tests (NEW - Claude Code requires uppercase)
    # =========================================================================

    def test_lowercase_tool_name_fails(self, validator):
        """Test that lowercase tool names fail.

        Claude Code requires tool names to start with uppercase:
        'Bash(...)' not 'bash(...)'
        """
        result = validator.validate("bash(git status:*)")
        assert not result.valid
        assert result.severity == "fail"
        assert "uppercase" in result.errors[0].lower()

    def test_mcp_tools_are_valid(self, validator):
        """Test that MCP tools (mcp__server__tool) are valid.

        MCP tools have a special format and don't follow the uppercase rule.
        """
        result = validator.validate("mcp__playwright__browser_click")
        assert result.valid

    def test_webfetch_is_valid(self, validator):
        """Test that WebFetch permissions are valid."""
        result = validator.validate("WebFetch(domain:example.com)")
        assert result.valid

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================


class TestConvenienceFunctions:
    """Test the module-level convenience functions."""

    def test_is_valid_permission_valid_rule(self):
        """Test is_valid_permission with valid permission."""
        from claude_automation.validators import is_valid_permission

        assert is_valid_permission("Write(/**)")
        assert is_valid_permission("Edit(/**)")
        assert is_valid_permission("Bash(git:*)")
        assert is_valid_permission("mcp__playwright__browser_click")

    def test_is_valid_permission_invalid_rule(self):
        """Test is_valid_permission with invalid permissions."""
        from claude_automation.validators import is_valid_permission

        # Bare pattern types should be invalid
        assert not is_valid_permission("file_write_operations")
        assert not is_valid_permission("git_workflow")

        # Empty should be invalid
        assert not is_valid_permission("")

        # Lowercase tool should be invalid
        assert not is_valid_permission("bash(git:*)")

    def test_validate_permission_returns_error_message(self):
        """Test validate_permission returns helpful error messages."""
        from claude_automation.validators import validate_permission

        is_valid, error = validate_permission("file_write_operations")
        assert not is_valid
        assert "bare pattern type" in error.lower()

        is_valid, error = validate_permission("Write(/**)")
        assert is_valid
        assert error == ""
