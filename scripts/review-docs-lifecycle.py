#!/usr/bin/env python3
"""
Review documentation lifecycle and identify stale documents.

This script scans all markdown files and flags:
- Draft documents older than 30 days
- Ephemeral documents older than 90 days

Output provides recommendations for archiving or updating status.

Usage:
    python3 scripts/review-docs-lifecycle.py
"""

import sys
from datetime import datetime
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Repository root
REPO_ROOT = Path(__file__).parent.parent

# Age thresholds (in days)
DRAFT_THRESHOLD = 30
EPHEMERAL_THRESHOLD = 90


def parse_frontmatter(file_path):
    """
    Parse YAML frontmatter from markdown file.

    Returns:
        dict with frontmatter fields or None if no frontmatter
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check for frontmatter
        if not content.startswith("---"):
            return None

        # Extract frontmatter block
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_text = parts[1]

        # Parse YAML fields (simple key: value parsing)
        frontmatter = {}
        for line in frontmatter_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter
    except Exception as e:
        print(f"{YELLOW}Warning: Could not parse {file_path}: {e}{RESET}")
        return None


def calculate_age(created_date_str):
    """
    Calculate age in days from created date string.

    Args:
        created_date_str: Date string in YYYY-MM-DD format

    Returns:
        int: Age in days, or None if parsing fails
    """
    try:
        created_date = datetime.strptime(created_date_str, "%Y-%m-%d")
        age = (datetime.now() - created_date).days
        return age
    except ValueError:
        return None


def find_markdown_files():
    """Find all markdown files in repository."""
    markdown_files = []
    for md_file in REPO_ROOT.rglob("*.md"):
        # Skip .git directory
        if ".git" in md_file.parts:
            continue
        # Skip node_modules, venv, etc.
        if any(
            exclude in md_file.parts
            for exclude in ["node_modules", "venv", ".venv", "__pycache__"]
        ):
            continue
        markdown_files.append(md_file)
    return markdown_files


def main():
    """Main execution function."""
    print(f"\n{'=' * 70}")
    print("Documentation Lifecycle Review")
    print(f"Repository: {REPO_ROOT}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'=' * 70}\n")

    # Find all markdown files
    markdown_files = find_markdown_files()
    print(f"Scanning {len(markdown_files)} markdown files...\n")

    # Track findings
    draft_flagged = []
    ephemeral_flagged = []
    total_scanned = 0
    no_frontmatter = 0

    for md_file in sorted(markdown_files):
        rel_path = md_file.relative_to(REPO_ROOT)
        total_scanned += 1

        # Parse frontmatter
        frontmatter = parse_frontmatter(md_file)
        if not frontmatter:
            no_frontmatter += 1
            continue

        status = frontmatter.get("status", "")
        lifecycle = frontmatter.get("lifecycle", "")
        created = frontmatter.get("created", "")

        # Skip if no created date
        if not created:
            continue

        # Calculate age
        age_days = calculate_age(created)
        if age_days is None:
            continue

        # Flag draft docs older than 30 days
        if status == "draft" and age_days > DRAFT_THRESHOLD:
            draft_flagged.append(
                {
                    "path": rel_path,
                    "created": created,
                    "age_days": age_days,
                    "lifecycle": lifecycle,
                }
            )

        # Flag ephemeral docs older than 90 days (skip persistent)
        if lifecycle == "ephemeral" and age_days > EPHEMERAL_THRESHOLD:
            ephemeral_flagged.append(
                {
                    "path": rel_path,
                    "created": created,
                    "age_days": age_days,
                    "status": status,
                }
            )

    # Report findings
    print(f"{'=' * 70}")
    print("FINDINGS")
    print(f"{'=' * 70}\n")

    if draft_flagged:
        print(f"{YELLOW}⚠️  Draft documents older than {DRAFT_THRESHOLD} days:{RESET}\n")
        for doc in draft_flagged:
            print(f"  📄 {doc['path']}")
            print(f"     Created: {doc['created']} ({doc['age_days']} days ago)")
            print(
                f"     {BLUE}Recommendation:{RESET} Archive or update status to 'active'\n"
            )
    else:
        print(f"{GREEN}✓ No draft documents older than {DRAFT_THRESHOLD} days{RESET}\n")

    if ephemeral_flagged:
        print(
            f"{YELLOW}🗄️  Ephemeral documents older than {EPHEMERAL_THRESHOLD} days:{RESET}\n"
        )
        for doc in ephemeral_flagged:
            print(f"  📄 {doc['path']}")
            print(f"     Created: {doc['created']} ({doc['age_days']} days ago)")

            # Suggest archive location based on path
            if ".claude/sessions" in str(doc["path"]):
                archive_date = doc["created"][:7]  # YYYY-MM
                print(
                    f"     {BLUE}Recommendation:{RESET} Already in sessions, verify archive location (.claude/sessions/archive/{archive_date}/)\n"
                )
            else:
                print(
                    f"     {BLUE}Recommendation:{RESET} Move to .claude/sessions/archive/{doc['created'][:7]}/\n"
                )
    else:
        print(
            f"{GREEN}✓ No ephemeral documents older than {EPHEMERAL_THRESHOLD} days{RESET}\n"
        )

    # Summary
    print(f"{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total documents scanned: {total_scanned}")
    print(f"  Documents without frontmatter: {no_frontmatter}")
    print(f"  Draft docs flagged (>{DRAFT_THRESHOLD} days): {len(draft_flagged)}")
    print(
        f"  Ephemeral docs flagged (>{EPHEMERAL_THRESHOLD} days): {len(ephemeral_flagged)}"
    )
    print(f"{'=' * 70}\n")

    if draft_flagged or ephemeral_flagged:
        print(f"{YELLOW}Action recommended: Review flagged documents{RESET}\n")
    else:
        print(f"{GREEN}No action needed: All documents are current{RESET}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
