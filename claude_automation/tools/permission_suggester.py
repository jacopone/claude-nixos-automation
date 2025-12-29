#!/usr/bin/env python3
"""
Permission Suggester - Standalone CLI Tool

Analyzes approval history and suggests permission rules for Claude Code projects.

Usage:
    python3 permission_suggester.py [project_path]
    python3 permission_suggester.py --analyze-all
    python3 permission_suggester.py --apply [project_path]

Features:
- Analyzes approval patterns from ~/.claude/learning/permission_approvals.jsonl
- Detects high-confidence patterns (>= 75% confidence, >= 3 occurrences)
- Suggests permission rules to add to .claude/settings.local.json
- Can auto-apply high-confidence rules with --apply flag
- Can analyze all projects with --analyze-all flag
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def setup_path():
    """Add claude-nixos-automation to Python path."""
    automation_dir = Path.home() / "claude-nixos-automation"
    if automation_dir.exists():
        sys.path.insert(0, str(automation_dir))


def analyze_project(project_path=None, days=30, min_confidence=0.75):
    """
    Analyze approval patterns for a project.

    Args:
        project_path: Project directory or None for all projects
        days: Days of history to analyze
        min_confidence: Minimum confidence threshold

    Returns:
        list: Pattern suggestions
    """
    setup_path()

    from claude_automation.analyzers import ApprovalTracker, PermissionPatternDetector

    tracker = ApprovalTracker()
    detector = PermissionPatternDetector(
        approval_tracker=tracker, min_occurrences=3, confidence_threshold=min_confidence
    )

    # Detect patterns
    suggestions = detector.detect_patterns(days=days, project_path=project_path)

    return suggestions


def display_suggestions(suggestions, show_details=True):
    """
    Display pattern suggestions in a human-readable format.

    Args:
        suggestions: List of PatternSuggestion objects
        show_details: Whether to show detailed breakdown
    """
    if not suggestions:
        print("\n✓ No new permission patterns detected.")
        print(
            "  Your approval history is too sparse or permissions are already optimal."
        )
        return

    print(f"\n📊 Found {len(suggestions)} permission pattern suggestions:\n")

    for i, suggestion in enumerate(suggestions, 1):
        pattern = suggestion.pattern

        # Header
        print(f"{i}. {suggestion.description}")
        print(f"   {'─' * 60}")

        # Confidence and metrics
        confidence_bar = "█" * int(pattern.confidence * 20)
        print(f"   Confidence: {pattern.confidence:.1%} {confidence_bar}")
        print(f"   Occurrences: {pattern.occurrences}")
        print(f"   Impact: {suggestion.impact_estimate}")
        print()

        # Proposed rule
        print("   📋 Proposed Permission Rules:")
        for rule in suggestion.proposed_rule.split(", "):
            print(f"      • {rule}")
        print()

        if show_details:
            # Examples
            print("   ✓ Would auto-allow:")
            for example in suggestion.would_allow[:3]:
                print(f"      - {example}")

            if suggestion.would_still_ask:
                print("\n   ⚠️  Would still ask for:")
                for example in suggestion.would_still_ask[:2]:
                    print(f"      - {example}")

            print()


def apply_suggestions(suggestions, project_path):
    """
    Apply high-confidence suggestions to settings.local.json.

    Args:
        suggestions: List of PatternSuggestion objects
        project_path: Project directory

    Returns:
        int: Number of rules added
    """
    project_dir = Path(
        project_path.replace("-", "/", 2) if "-" in project_path else project_path
    )
    settings_file = project_dir / ".claude" / "settings.local.json"

    # Load or create settings
    if settings_file.exists():
        with open(settings_file) as f:
            settings = json.load(f)
    else:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings = {"permissions": {"allow": []}}

    # Ensure structure
    if "permissions" not in settings:
        settings["permissions"] = {}
    if "allow" not in settings["permissions"]:
        settings["permissions"]["allow"] = []

    # Get existing permissions
    existing = set(settings["permissions"]["allow"])

    # Add new rules (with validation)
    setup_path()  # Ensure imports are available
    from claude_automation.validators import is_valid_permission

    added = []
    skipped = []
    for suggestion in suggestions:
        for rule in suggestion.proposed_rule.split(", "):
            if rule not in existing:
                # Validate rule before adding
                if not is_valid_permission(rule):
                    skipped.append(rule)
                    print(f"  ⚠️  Skipping invalid rule: {rule}")
                    continue
                settings["permissions"]["allow"].append(rule)
                added.append(rule)

    # Update metadata
    if added:
        if "_auto_generated_permissions" not in settings:
            settings["_auto_generated_permissions"] = {}

        settings["_auto_generated_permissions"]["last_updated"] = (
            datetime.now().isoformat()
        )
        settings["_auto_generated_permissions"]["tool"] = "permission_suggester.py"
        if "rules_added" not in settings["_auto_generated_permissions"]:
            settings["_auto_generated_permissions"]["rules_added"] = []
        settings["_auto_generated_permissions"]["rules_added"].extend(added)

        # Write back
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        print(f"\n✓ Added {len(added)} permission rules to {settings_file}")
        for rule in added:
            print(f"  • {rule}")

    return len(added)


def analyze_all_projects(days=30):
    """
    Analyze all projects in approval history.

    Args:
        days: Days of history to analyze

    Returns:
        dict: Map of project_path -> suggestions
    """
    setup_path()

    from claude_automation.analyzers import ApprovalTracker

    tracker = ApprovalTracker()

    # Get all projects
    approvals_by_project = tracker.get_approvals_by_project(days=days)

    print(f"\n📁 Found {len(approvals_by_project)} projects with approval history:\n")

    results = {}

    for project_path, approvals in approvals_by_project.items():
        print(f"  • {project_path}: {len(approvals)} approvals")

        # Analyze this project
        suggestions = analyze_project(project_path=project_path, days=days)
        if suggestions:
            results[project_path] = suggestions

    return results


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze approval history and suggest permission rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current project
  python3 permission_suggester.py

  # Analyze specific project
  python3 permission_suggester.py /home/user/my-project

  # Analyze all projects
  python3 permission_suggester.py --analyze-all

  # Apply suggestions to specific project
  python3 permission_suggester.py --apply /home/user/my-project

  # Analyze with custom parameters
  python3 permission_suggester.py --days 60 --confidence 0.8
        """,
    )

    parser.add_argument(
        "project_path",
        nargs="?",
        help="Project directory to analyze (default: current directory)",
    )

    parser.add_argument(
        "--analyze-all",
        action="store_true",
        help="Analyze all projects in approval history",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Auto-apply high-confidence suggestions to settings.local.json",
    )

    parser.add_argument(
        "--days", type=int, default=30, help="Days of history to analyze (default: 30)"
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.75,
        help="Minimum confidence threshold 0-1 (default: 0.75)",
    )

    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    try:
        # Analyze all projects
        if args.analyze_all:
            results = analyze_all_projects(days=args.days)

            if args.json:
                # JSON output (for scripting)
                output = {}
                for project, suggestions in results.items():
                    output[project] = [
                        {
                            "description": s.description,
                            "confidence": s.pattern.confidence,
                            "occurrences": s.pattern.occurrences,
                            "proposed_rule": s.proposed_rule,
                            "impact": s.impact_estimate,
                        }
                        for s in suggestions
                    ]
                print(json.dumps(output, indent=2))
            else:
                # Human-readable output
                print("\n" + "=" * 70)
                for project, suggestions in results.items():
                    print(f"\n📁 Project: {project}")
                    display_suggestions(suggestions, show_details=False)

            return

        # Analyze specific project
        project_path = args.project_path or Path.cwd()

        print(f"\n🔍 Analyzing approval patterns for: {project_path}")
        print(f"   Looking back: {args.days} days")
        print(f"   Confidence threshold: {args.confidence:.0%}")

        suggestions = analyze_project(
            project_path=str(project_path),
            days=args.days,
            min_confidence=args.confidence,
        )

        if args.json:
            # JSON output
            output = [
                {
                    "description": s.description,
                    "confidence": s.pattern.confidence,
                    "occurrences": s.pattern.occurrences,
                    "proposed_rule": s.proposed_rule,
                    "impact": s.impact_estimate,
                    "examples": s.approved_examples,
                }
                for s in suggestions
            ]
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            display_suggestions(suggestions, show_details=True)

        # Apply if requested
        if args.apply and suggestions:
            print("\n🔧 Applying suggestions...")
            added_count = apply_suggestions(suggestions, str(project_path))

            if added_count == 0:
                print("\n✓ All suggested rules were already present.")
        elif suggestions and not args.apply:
            print("\n💡 To apply these suggestions, run with --apply flag:")
            print(f"   python3 permission_suggester.py --apply {project_path}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
