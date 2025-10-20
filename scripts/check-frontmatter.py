#!/usr/bin/env python3
"""
Check that staged markdown files have YAML frontmatter.

This script is designed to be used as a pre-commit hook to prevent
committing markdown files without frontmatter.

Exit Codes:
    0: All staged markdown files have frontmatter
    1: One or more staged markdown files are missing frontmatter

Usage:
    python3 scripts/check-frontmatter.py
"""

import subprocess
import sys
from pathlib import Path

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Files to exclude from frontmatter check
EXCLUDE_FILES = [
    'CLAUDE.md',  # Auto-generated file
]


def get_staged_markdown_files():
    """Get list of staged markdown files from git."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n')
        # Filter for markdown files only
        md_files = [f for f in files if f.endswith('.md') and f]
        return md_files
    except subprocess.CalledProcessError:
        print(f"{RED}Error: Failed to get staged files from git{RESET}")
        return []


def has_frontmatter(file_path):
    """Check if a markdown file has YAML frontmatter."""
    try:
        with open(file_path, encoding='utf-8') as f:
            first_line = f.readline().strip()
            return first_line == '---'
    except FileNotFoundError:
        # File might have been deleted
        return True
    except Exception as e:
        print(f"{YELLOW}Warning: Could not read {file_path}: {e}{RESET}")
        return True  # Don't block commit on read errors


def is_excluded(file_path):
    """Check if file should be excluded from frontmatter check."""
    filename = Path(file_path).name
    return filename in EXCLUDE_FILES


def main():
    """Main execution function."""
    staged_files = get_staged_markdown_files()

    if not staged_files:
        # No markdown files staged, nothing to check
        sys.exit(0)

    missing_frontmatter = []

    for file_path in staged_files:
        if is_excluded(file_path):
            continue

        if not has_frontmatter(file_path):
            missing_frontmatter.append(file_path)

    if missing_frontmatter:
        print(f"\n{RED}ERROR: Markdown files missing frontmatter:{RESET}")
        for file_path in missing_frontmatter:
            print(f"  - {file_path}")
        print(f"\n{YELLOW}Please add frontmatter to these files.{RESET}")
        print(f"{YELLOW}You can run:{RESET} python3 scripts/add-frontmatter.py\n")
        sys.exit(1)

    # All staged markdown files have frontmatter
    sys.exit(0)


if __name__ == "__main__":
    main()
