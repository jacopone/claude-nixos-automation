#!/usr/bin/env python3
"""
Migration script for existing per-project TIER_1_SAFE patterns to global settings.

This script identifies TIER_1_SAFE patterns currently in per-project settings
and migrates them to ~/.claude/settings.json for global application.

Usage:
    # Dry run - see what would be migrated
    python -m claude_automation.cli.migrate_permissions --dry-run

    # Execute migration
    python -m claude_automation.cli.migrate_permissions --execute

    # Migrate from specific project
    python -m claude_automation.cli.migrate_permissions --execute --project ~/my-project
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_automation.analyzers.permission_pattern_detector import (
    PermissionPatternDetector,
)
from claude_automation.generators.global_permissions_manager import (
    GlobalPermissionsManager,
)

# Get PATTERN_CATEGORIES from the class
_detector = PermissionPatternDetector.__dict__.get("PATTERN_CATEGORIES", {})

# TIER_1_SAFE pattern types that should be migrated to global
TIER_1_SAFE_TYPES = {
    ptype for ptype, config in _detector.items() if config.get("tier") == "TIER_1_SAFE"
}

# Command prefixes that are TIER_1_SAFE (read-only operations)
TIER_1_SAFE_COMMAND_PREFIXES = [
    "git status",
    "git log",
    "git diff",
    "git show",
    "git branch",
    "git remote",
    "git stash list",
    "fd",
    "rg",
    "bat",
    "eza",
    "cat",
    "head",
    "tail",
    "ls",
    "tree",
    "wc",
    "which",
    "file",
    "readlink",
    "pytest",
    "ruff check",
    "ruff format --check",
]


def find_project_settings() -> list[Path]:
    """Find all per-project settings files."""
    settings_files = []

    # Common project locations
    search_paths = [
        Path.home() / "nixos-config",
        Path.home() / "claude-nixos-automation",
        Path.home() / "projects",
        Path.home() / "code",
        Path.home() / "dev",
    ]

    for base_path in search_paths:
        if not base_path.exists():
            continue

        # Find .claude/settings.local.json files
        for settings_file in base_path.rglob(".claude/settings.local.json"):
            if settings_file.is_file():
                settings_files.append(settings_file)

    return settings_files


def is_project_specific_path(rule: str) -> bool:
    """Check if a rule contains project-specific paths that shouldn't be global."""
    # Project-specific path patterns to exclude from global
    project_patterns = [
        r"/home/[^/]+/[a-zA-Z0-9_-]+/",  # /home/user/project-name/
        r"/home/[^/]+/\.[^/]+/",  # /home/user/.dotfolder/
    ]

    # Generic paths that ARE suitable for global
    generic_patterns = [
        r"Read\(/\*\*\)",  # Read(/**)
        r"Read\(/tmp/",  # /tmp is generic
        r"Read\(/etc/",  # /etc is system-wide
        r"Glob\(\*\*\)",  # Glob(**)
    ]

    # If it's a generic pattern, it's not project-specific
    for pattern in generic_patterns:
        if re.search(pattern, rule):
            return False

    # Check for project-specific paths
    for pattern in project_patterns:
        if re.search(pattern, rule):
            return True

    return False


def is_tier1_safe_rule(rule: str, skip_project_paths: bool = False) -> bool:
    """Check if a permission rule is TIER_1_SAFE (read-only).

    Args:
        rule: The permission rule to check
        skip_project_paths: If True, exclude project-specific paths from migration
    """
    # Skip comments
    if rule.strip().startswith("//"):
        return False

    # Check for Bash rules with safe commands
    bash_match = re.match(r"Bash\(([^:]+):?\*?\)", rule)
    if bash_match:
        command = bash_match.group(1)
        for prefix in TIER_1_SAFE_COMMAND_PREFIXES:
            if command.startswith(prefix):
                return True
        # Also check for bare commands that are read-only
        if command in ["cat", "head", "tail", "ls", "tree", "which", "file", "wc"]:
            return True

    # Check for Read and Glob operations (always safe)
    if rule.startswith("Read(") or rule.startswith("Glob("):
        # Optionally skip project-specific paths
        if skip_project_paths and is_project_specific_path(rule):
            return False
        return True

    return False


def extract_tier1_rules(settings: dict, skip_project_paths: bool = False) -> list[str]:
    """Extract TIER_1_SAFE rules from settings.

    Args:
        settings: Settings dictionary
        skip_project_paths: If True, exclude project-specific paths
    """
    tier1_rules = []

    permissions = settings.get("permissions", {})
    allow_rules = permissions.get("allow", [])

    for rule in allow_rules:
        if is_tier1_safe_rule(rule, skip_project_paths=skip_project_paths):
            tier1_rules.append(rule)

    return tier1_rules


def migrate_project(
    project_settings_path: Path,
    global_manager: GlobalPermissionsManager,
    dry_run: bool = True,
    remove_from_project: bool = False,
    skip_project_paths: bool = False,
) -> dict:
    """Migrate TIER_1_SAFE rules from a project to global settings.

    Args:
        project_settings_path: Path to project's settings.local.json
        global_manager: GlobalPermissionsManager instance
        dry_run: If True, don't actually modify files
        remove_from_project: If True, remove migrated rules from project settings
        skip_project_paths: If True, exclude project-specific paths

    Returns:
        dict with migration results
    """
    result = {
        "project": str(project_settings_path.parent.parent),
        "rules_found": [],
        "rules_migrated": [],
        "rules_skipped": [],
        "errors": [],
    }

    try:
        with open(project_settings_path) as f:
            settings = json.load(f)
    except json.JSONDecodeError as e:
        result["errors"].append(f"JSON parse error: {e}")
        return result
    except Exception as e:
        result["errors"].append(f"Read error: {e}")
        return result

    tier1_rules = extract_tier1_rules(settings, skip_project_paths=skip_project_paths)
    result["rules_found"] = tier1_rules

    if not tier1_rules:
        return result

    if dry_run:
        # Just check what would be migrated
        for rule in tier1_rules:
            if global_manager.is_covered_by_existing(rule):
                result["rules_skipped"].append(rule)
            else:
                result["rules_migrated"].append(rule)
    else:
        # Actually migrate
        added, skipped = global_manager.add_permissions(
            tier1_rules, source="migration", tier="TIER_1_SAFE"
        )
        result["rules_migrated"] = added
        result["rules_skipped"] = skipped

        # Optionally remove from project settings
        if remove_from_project and added:
            try:
                permissions = settings.get("permissions", {})
                allow_rules = permissions.get("allow", [])
                new_allow = [r for r in allow_rules if r not in added]
                settings["permissions"]["allow"] = new_allow

                with open(project_settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
            except Exception as e:
                result["errors"].append(f"Failed to update project settings: {e}")

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate TIER_1_SAFE permissions from per-project to global settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # See what would be migrated (dry run)
    python -m claude_automation.cli.migrate_permissions --dry-run

    # Execute migration
    python -m claude_automation.cli.migrate_permissions --execute

    # Migrate from specific project only
    python -m claude_automation.cli.migrate_permissions --execute --project ~/nixos-config

    # Migrate and remove from project settings
    python -m claude_automation.cli.migrate_permissions --execute --remove-from-project
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the migration",
    )
    parser.add_argument(
        "--project",
        type=Path,
        help="Migrate from specific project path only",
    )
    parser.add_argument(
        "--remove-from-project",
        action="store_true",
        help="Remove migrated rules from project settings after migration",
    )
    parser.add_argument(
        "--skip-project-paths",
        action="store_true",
        help="Skip Read/Glob rules with project-specific paths (e.g., /home/user/project/)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")

    if args.dry_run and args.execute:
        parser.error("Cannot specify both --dry-run and --execute")

    dry_run = args.dry_run

    # Initialize global manager
    global_manager = GlobalPermissionsManager()

    # Find project settings to migrate
    if args.project:
        project_path = args.project.expanduser().resolve()
        settings_path = project_path / ".claude" / "settings.local.json"
        if not settings_path.exists():
            print(f"Error: No settings file found at {settings_path}")
            sys.exit(1)
        project_settings = [settings_path]
    else:
        project_settings = find_project_settings()

    if not project_settings:
        print("No project settings files found to migrate.")
        sys.exit(0)

    # Print header
    mode = "DRY RUN" if dry_run else "EXECUTING"
    print(f"\n{'=' * 60}")
    print(f"  TIER_1_SAFE Permission Migration ({mode})")
    print(f"{'=' * 60}")
    print(f"\nGlobal settings: {global_manager.GLOBAL_SETTINGS_PATH}")
    print(f"Projects found: {len(project_settings)}")
    if args.skip_project_paths:
        print("Skipping: Project-specific paths (Read/Glob with /home/user/project/)")
    print()

    # Create backup before migration
    if not dry_run:
        backup_path = global_manager.create_backup()
        print(f"Backup created: {backup_path}\n")

    # Process each project
    total_migrated = 0
    total_skipped = 0
    total_errors = 0

    for settings_path in project_settings:
        result = migrate_project(
            settings_path,
            global_manager,
            dry_run=dry_run,
            remove_from_project=args.remove_from_project,
            skip_project_paths=args.skip_project_paths,
        )

        project_name = Path(result["project"]).name
        found = len(result["rules_found"])
        migrated = len(result["rules_migrated"])
        skipped = len(result["rules_skipped"])
        errors = len(result["errors"])

        total_migrated += migrated
        total_skipped += skipped
        total_errors += errors

        # Print project summary
        if found > 0 or errors > 0:
            status = "✓" if errors == 0 else "✗"
            print(
                f"{status} {project_name}: {found} found, {migrated} migrated, {skipped} skipped"
            )

            if args.verbose:
                if result["rules_migrated"]:
                    print("  Migrated:")
                    for rule in result["rules_migrated"]:
                        print(f"    + {rule}")
                if result["rules_skipped"]:
                    print("  Skipped (already covered):")
                    for rule in result["rules_skipped"]:
                        print(f"    - {rule}")
                if result["errors"]:
                    print("  Errors:")
                    for error in result["errors"]:
                        print(f"    ! {error}")

    # Print summary
    print(f"\n{'=' * 60}")
    print("  Summary")
    print(f"{'=' * 60}")
    print(f"  Rules migrated to global: {total_migrated}")
    print(f"  Rules skipped (duplicate): {total_skipped}")
    if total_errors > 0:
        print(f"  Errors: {total_errors}")

    if dry_run and total_migrated > 0:
        print("\nTo apply these changes, run:")
        print("  python -m claude_automation.cli.migrate_permissions --execute")

    print()


if __name__ == "__main__":
    main()
