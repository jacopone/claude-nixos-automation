#!/usr/bin/env python3
"""
Permission Cleaner Hook - Runs after each tool use to clean invalid permissions.

This hook catches invalid permissions added by Claude Code's built-in learning
and removes them immediately.
"""

import json
import re
import sys
from pathlib import Path


def is_invalid_permission(perm):
    """Check if a permission is invalid."""
    # Newlines, heredocs, __NEW_LINE__
    if "\n" in perm or "EOF" in perm or "__NEW_LINE__" in perm:
        return True

    # Wildcard only
    if perm == "*":
        return True

    # Bare pattern types
    bare_types = ["file_write_operations", "git_workflow", "read_operations"]
    if perm.lower() in bare_types:
        return True

    # Bash-specific checks
    if perm.startswith("Bash("):
        inner = perm[5:-1] if perm.endswith(")") else perm[5:]

        # Shell fragments
        if inner.strip() in ["done", "fi", "then", "else", "do", "esac", "in"]:
            return True

        # Shell constructs at start
        if re.match(r"^(do |for |while |if |export |then )", inner):
            return True

        # Unmatched quotes
        quote_count = inner.count('"') - inner.count('\\"')
        if quote_count % 2 != 0:
            return True

    return False


def clean_permissions(filepath):
    """Remove invalid permissions from a settings file."""
    try:
        with open(filepath) as f:
            settings = json.load(f)

        perms = settings.get("permissions", {}).get("allow", [])
        if not perms:
            return 0

        clean = [p for p in perms if not is_invalid_permission(p)]
        removed = len(perms) - len(clean)

        if removed > 0:
            settings["permissions"]["allow"] = clean
            with open(filepath, "w") as f:
                json.dump(settings, f, indent=2)

        return removed
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return 0


def main():
    """Main hook function."""
    try:
        sys.stdin.read()
    except Exception:
        pass

    # Clean global settings
    global_settings = Path.home() / ".claude" / "settings.local.json"
    clean_permissions(global_settings)

    sys.exit(0)


if __name__ == "__main__":
    main()
