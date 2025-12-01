"""
Permission validator for Claude Code settings.
Ensures permissions are syntactically valid and safe.
"""

import re
from typing import Literal

from ..schemas import ValidationResult


class PermissionValidator:
    """
    Validates Claude Code permission strings.

    Enforces critical safety rules:
    - No newlines (breaks JSON formatting)
    - No heredoc markers (injection risk)
    - Length limit of 200 characters
    - Valid command format
    """

    MAX_LENGTH = 200
    HEREDOC_PATTERNS = [
        r"<<",  # Heredoc start
        r"EOF",  # Common heredoc delimiter
        r"<<-",  # Indented heredoc
    ]

    def validate(self, permission: str) -> ValidationResult:
        """
        Validate a single permission string.

        Args:
            permission: Permission string to validate

        Returns:
            ValidationResult with errors if invalid

        Example:
            >>> validator = PermissionValidator()
            >>> result = validator.validate("Bash(git status:*)")
            >>> result.valid
            True
        """
        errors = []
        warnings = []
        info = []

        # Check 1: Empty permission
        if not permission or len(permission.strip()) == 0:
            errors.append("Permission cannot be empty")
            return ValidationResult(
                valid=False,
                severity="fail",
                errors=errors,
                warnings=warnings,
                info=info,
            )

        # Check 2: Length limit
        if len(permission) > self.MAX_LENGTH:
            errors.append(
                f"Permission too long ({len(permission)} chars, max {self.MAX_LENGTH})"
            )

        # Check 3: Newlines (critical - breaks JSON)
        if "\n" in permission or "\r" in permission:
            errors.append("Permission cannot contain newlines (breaks JSON formatting)")

        # Check 4: Heredoc markers (critical - injection risk)
        for pattern in self.HEREDOC_PATTERNS:
            if re.search(pattern, permission, re.IGNORECASE):
                errors.append(
                    f"Permission cannot contain heredoc marker '{pattern}' (injection risk)"
                )

        # Check 5: Basic format validation
        if not self._has_valid_format(permission):
            warnings.append(
                "Permission format unusual (expected: Tool(pattern:*) or Read(path))"
            )

        # Check 6: Dangerous patterns (warning only)
        dangerous = self._check_dangerous_patterns(permission)
        if dangerous:
            warnings.extend(dangerous)

        # Summary
        if errors:
            info.append(
                f"Permission '{permission[:50]}...' failed {len(errors)} critical check(s)"
            )
        elif warnings:
            info.append(
                f"Permission '{permission[:50]}...' has {len(warnings)} warning(s)"
            )
        else:
            info.append(f"Permission '{permission[:50]}...' is valid")

        valid = len(errors) == 0
        severity: Literal["fail", "warn", "info"] = (
            "fail" if errors else ("warn" if warnings else "info")
        )

        return ValidationResult(
            valid=valid,
            severity=severity,
            errors=errors,
            warnings=warnings,
            info=info,
        )

    def validate_batch(
        self, permissions: list[str]
    ) -> tuple[list[ValidationResult], bool]:
        """
        Validate a batch of permissions.

        Args:
            permissions: List of permission strings

        Returns:
            Tuple of (list of results, all_valid flag)
        """
        results = [self.validate(p) for p in permissions]
        all_valid = all(r.valid for r in results)
        return results, all_valid

    def _has_valid_format(self, permission: str) -> bool:
        """
        Check if permission follows expected format.

        Valid formats:
        - Bash(command:*)
        - Read(path)
        - Write(path)
        - Edit(path)
        - Glob(pattern)
        """
        # Known tools
        known_tools = [
            "Bash",
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "Task",
            "SlashCommand",
        ]

        # Extract tool name
        tool_match = re.match(r"^(\w+)\(", permission)
        if not tool_match:
            return False

        tool_name = tool_match.group(1)

        # Must be a known tool
        if tool_name not in known_tools:
            return False

        # Must follow basic Tool(arg) format
        if not re.match(r"^\w+\([^)]+\)$", permission):
            return False

        # Multiple comma-separated args are unusual (except for specific cases)
        # Extract args inside parentheses
        args_match = re.search(r"\(([^)]+)\)", permission)
        if args_match:
            args = args_match.group(1)
            # Count commas - more than 0 is unusual
            if "," in args:
                return False

        return True

    def _check_dangerous_patterns(self, permission: str) -> list[str]:
        """
        Check for potentially dangerous permission patterns.

        Returns warnings (not errors - these are allowed but flagged).
        """
        warnings = []

        # Check for shell command injection patterns
        dangerous_chars = [";", "|", "&", "$", "`"]
        for char in dangerous_chars:
            if char in permission:
                warnings.append(
                    f"Contains potentially dangerous character '{char}' (shell injection risk)"
                )

        # Check for filesystem traversal
        if ".." in permission:
            warnings.append("Contains '..' (filesystem traversal risk)")

        # Check for absolute paths with overly broad wildcards
        # Patterns like /home/* or Read(/home/*/file) are suspicious
        # But /**/ (recursive glob) is fine
        if re.search(r"\(/[^)]*\*/", permission):  # /path/*/something pattern
            warnings.append("Absolute path with wildcard (may grant excessive access)")
        elif permission.startswith("/") and re.search(r"/\*[^*/]", permission):
            # Starts with / and has /* but not /** or **/
            warnings.append("Absolute path with wildcard (may grant excessive access)")

        # Check for /etc or /sys access (usually not needed)
        if "/etc" in permission or "/sys" in permission:
            warnings.append("Accesses system directories (/etc or /sys)")

        return warnings

    def generate_report(self, results: list[ValidationResult]) -> str:
        """
        Generate human-readable validation report.

        Args:
            results: List of validation results

        Returns:
            Formatted report string
        """
        total = len(results)
        valid = sum(1 for r in results if r.valid)
        failed = total - valid

        errors_total = sum(len(r.errors) for r in results)
        warnings_total = sum(len(r.warnings) for r in results)

        lines = []
        lines.append("=" * 60)
        lines.append("PERMISSION VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Total permissions: {total}")
        lines.append(f"Valid: {valid} ({valid / total * 100:.1f}%)")
        lines.append(f"Failed: {failed} ({failed / total * 100:.1f}%)")
        lines.append(f"Total errors: {errors_total}")
        lines.append(f"Total warnings: {warnings_total}")
        lines.append("")

        # Show failures
        if failed > 0:
            lines.append("FAILURES:")
            for idx, result in enumerate(results, 1):
                if not result.valid:
                    lines.append(f"  [{idx}] {result.errors}")

        # Show warnings
        if warnings_total > 0:
            lines.append("")
            lines.append("WARNINGS:")
            for idx, result in enumerate(results, 1):
                if result.warnings:
                    lines.append(f"  [{idx}] {result.warnings}")

        lines.append("=" * 60)
        return "\n".join(lines)
