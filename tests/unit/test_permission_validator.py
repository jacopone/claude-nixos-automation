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
