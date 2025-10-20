#!/usr/bin/env python3
"""
Add YAML frontmatter to markdown files in claude-nixos-automation repository.

This script follows the exact pattern from ~/nixos-config/scripts/add-frontmatter.py
with repository-specific RULES for file categorization.

Usage:
    python3 scripts/add-frontmatter.py

Frontmatter Schema:
    status: draft | active | deprecated | archived
    created: YYYY-MM-DD
    updated: YYYY-MM-DD
    type: guide | architecture | reference | session-note | planning
    lifecycle: persistent | ephemeral
"""

import sys
from datetime import datetime
from pathlib import Path

# ANSI color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Repository root
REPO_ROOT = Path(__file__).parent.parent

# File categorization rules
# Format: (path_pattern, status, type, lifecycle, created_date)
RULES = [
    # Session notes from October 2025 - archive together
    ("PHASE*.md", "archived", "session-note", "ephemeral", "2025-10-01"),
    ("IMPLEMENTATION*.md", "archived", "session-note", "ephemeral", "2025-10-01"),
    ("FINAL_STATUS.md", "archived", "session-note", "ephemeral", "2025-10-01"),
    ("*_SUMMARY.md", "archived", "session-note", "ephemeral", "2025-10-01"),
    ("*_COMPLETE.md", "archived", "session-note", "ephemeral", "2025-10-01"),

    # Architectural documentation
    ("CONSTITUTION.md", "active", "architecture", "persistent", "2024-01-01"),
    ("CLAUDE_ORCHESTRATION.md", "active", "architecture", "persistent", "2024-01-01"),
    ("THE_CLOSED_LOOP.md", "active", "architecture", "persistent", "2024-01-01"),

    # Guides and reference docs
    ("TESTING.md", "active", "guide", "persistent", "2024-01-01"),
    ("README.md", "active", "reference", "persistent", "2024-01-01"),
    ("CONTRIBUTING.md", "active", "guide", "persistent", "2024-01-01"),
    ("COMMON_TASKS.md", "active", "guide", "persistent", "2024-01-01"),

    # Planning documents in specs/
    ("specs/*/spec.md", "active", "planning", "persistent", None),
    ("specs/*/plan.md", "active", "planning", "persistent", None),
    ("specs/*/research.md", "active", "planning", "persistent", None),
    ("specs/*/tasks.md", "active", "planning", "persistent", None),

    # Session notes in .claude/sessions/
    (".claude/sessions/*.md", "archived", "session-note", "ephemeral", None),

    # Documentation in docs/
    ("docs/**/*.md", "active", "guide", "persistent", None),
]

# Files to exclude from processing
EXCLUDE_FILES = [
    "CLAUDE.md",  # Auto-generated file
]


def matches_pattern(file_path: Path, pattern: str) -> bool:
    """Check if file path matches a glob pattern."""
    from fnmatch import fnmatch
    rel_path = file_path.relative_to(REPO_ROOT)
    return fnmatch(str(rel_path), pattern)


def classify_file(file_path: Path) -> tuple:
    """
    Classify a markdown file based on RULES.

    Returns:
        Tuple of (status, type, lifecycle, created_date)
    """
    for pattern, status, file_type, lifecycle, created in RULES:
        if matches_pattern(file_path, pattern):
            # Use current date if created_date is None
            if created is None:
                created = datetime.now().strftime("%Y-%m-%d")
            return (status, file_type, lifecycle, created)

    # Default classification for unmatched files
    return ("draft", "reference", "persistent", datetime.now().strftime("%Y-%m-%d"))


def has_frontmatter(file_path: Path) -> bool:
    """Check if file already has YAML frontmatter."""
    try:
        with open(file_path, encoding='utf-8') as f:
            first_line = f.readline().strip()
            return first_line == '---'
    except Exception:
        return False


def generate_frontmatter(status: str, file_type: str, lifecycle: str, created: str) -> str:
    """Generate YAML frontmatter block."""
    updated = datetime.now().strftime("%Y-%m-%d")
    return f"""---
status: {status}
created: {created}
updated: {updated}
type: {file_type}
lifecycle: {lifecycle}
---

"""


def add_frontmatter_to_file(file_path: Path) -> bool:
    """
    Add frontmatter to a markdown file.

    Returns:
        True if frontmatter was added, False if skipped
    """
    try:
        # Read existing content
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # Classify file
        status, file_type, lifecycle, created = classify_file(file_path)

        # Generate and prepend frontmatter
        frontmatter = generate_frontmatter(status, file_type, lifecycle, created)
        new_content = frontmatter + content

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"{RED}✗ Error processing {file_path}: {e}{RESET}")
        return False


def find_markdown_files() -> list:
    """Find all markdown files in repository."""
    markdown_files = []
    for md_file in REPO_ROOT.rglob("*.md"):
        # Skip excluded files
        if md_file.name in EXCLUDE_FILES:
            continue
        # Skip .git directory
        if '.git' in md_file.parts:
            continue
        # Skip node_modules, venv, etc.
        if any(exclude in md_file.parts for exclude in ['node_modules', 'venv', '.venv', '__pycache__']):
            continue
        markdown_files.append(md_file)
    return markdown_files


def main():
    """Main execution function."""
    print(f"\n{'='*60}")
    print("Adding YAML frontmatter to markdown files")
    print(f"Repository: {REPO_ROOT}")
    print(f"{'='*60}\n")

    # Find all markdown files
    markdown_files = find_markdown_files()
    print(f"Found {len(markdown_files)} markdown files\n")

    # Process each file
    processed = 0
    skipped = 0
    errors = 0

    for md_file in sorted(markdown_files):
        rel_path = md_file.relative_to(REPO_ROOT)

        if has_frontmatter(md_file):
            print(f"{YELLOW}⏭️  Skipping (has frontmatter): {rel_path}{RESET}")
            skipped += 1
        else:
            if add_frontmatter_to_file(md_file):
                print(f"{GREEN}✅ Added frontmatter: {rel_path}{RESET}")
                processed += 1
            else:
                errors += 1

    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Processed: {processed}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
