#!/usr/bin/env python3
"""
Update Claude Code permissions using learning from approval history.

This script analyzes your permission approval history, detects patterns,
and suggests generalizations to reduce future permission prompts.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_automation.analyzers.approval_tracker import ApprovalTracker
from claude_automation.analyzers.permission_pattern_detector import (
    PermissionPatternDetector,
)
from claude_automation.generators.intelligent_permissions_generator import (
    IntelligentPermissionsGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Update Claude Code permissions with intelligent learning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default) - prompts for approval
  %(prog)s

  # Non-interactive mode - auto-apply high-confidence patterns
  %(prog)s --no-interactive

  # Apply to global config (all projects)
  %(prog)s --global

  # Apply to specific project
  %(prog)s --project /path/to/project

  # Adjust detection thresholds
  %(prog)s --min-occurrences 5 --confidence 0.8

  # Analyze longer history
  %(prog)s --days 60

  # Show statistics only (no changes)
  %(prog)s --stats-only

  # Dry-run mode (show suggestions without applying)
  %(prog)s --dry-run
        """,
    )

    parser.add_argument(
        "--global",
        dest="global_mode",
        action="store_true",
        help="Apply to global config (~/.claude.json) for all projects",
    )

    parser.add_argument(
        "--project",
        dest="project_path",
        type=str,
        help="Apply to specific project (default: current directory)",
    )

    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        default=True,
        help="Non-interactive mode - auto-apply patterns without prompting",
    )

    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=3,
        help="Minimum occurrences for pattern detection (default: 3)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold 0-1 (default: 0.7)",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days of history to analyze (default: 30)",
    )

    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Show statistics only, don't apply changes",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show suggestions without applying (implies --no-interactive)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output (debug logging)",
    )

    args = parser.parse_args()

    # Configure verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Validate arguments
    if args.confidence < 0 or args.confidence > 1:
        parser.error("--confidence must be between 0 and 1")

    if args.min_occurrences < 1:
        parser.error("--min-occurrences must be at least 1")

    if args.days < 1:
        parser.error("--days must be at least 1")

    # Dry-run implies non-interactive
    if args.dry_run:
        args.interactive = False

    try:
        # Initialize components
        logger.info("Initializing intelligent permissions learning...")
        approval_tracker = ApprovalTracker()
        pattern_detector = PermissionPatternDetector(
            approval_tracker=approval_tracker,
            min_occurrences=args.min_occurrences,
            confidence_threshold=args.confidence,
        )

        # Show statistics if requested
        if args.stats_only:
            show_statistics(approval_tracker, pattern_detector, args.days)
            return 0

        # Create generator
        generator = IntelligentPermissionsGenerator(
            approval_tracker=approval_tracker,
            pattern_detector=pattern_detector,
        )

        # Determine target file
        target_file = None
        if args.global_mode:
            target_file = Path.home() / ".claude.json"
            logger.info("Target: Global config (all projects)")
        elif args.project_path:
            target_file = Path(args.project_path) / ".claude" / "settings.local.json"
            logger.info(f"Target: Project {args.project_path}")
        else:
            target_file = Path.cwd() / ".claude" / "settings.local.json"
            logger.info(f"Target: Current project ({Path.cwd()})")

        # Generate with learning
        if args.dry_run:
            logger.info("DRY-RUN MODE: No changes will be applied")

        result = generator.generate_with_learning(
            target_file=target_file,
            global_mode=args.global_mode,
            interactive=args.interactive and not args.dry_run,
            min_occurrences=args.min_occurrences,
            confidence_threshold=args.confidence,
            days=args.days,
        )

        # Display results
        if result.success:
            print("\n" + "=" * 70)
            print("✅ PERMISSION LEARNING COMPLETE")
            print("=" * 70)

            if result.stats:
                print(f"\nStatistics:")
                for key, value in result.stats.items():
                    print(f"  {key}: {value}")

            if result.warnings:
                print(f"\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            if result.output_path:
                print(f"\nUpdated: {result.output_path}")

            if args.dry_run:
                print("\n⚠️  DRY-RUN MODE: No changes were applied")

            print()
            return 0
        else:
            print("\n❌ PERMISSION LEARNING FAILED")
            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"  ✗ {error}")
            print()
            return 1

    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


def show_statistics(
    tracker: ApprovalTracker,
    detector: PermissionPatternDetector,
    days: int,
):
    """
    Display statistics about approval history and patterns.

    Args:
        tracker: Approval tracker
        detector: Pattern detector
        days: Days of history
    """
    print("\n" + "=" * 70)
    print("📊 PERMISSION LEARNING STATISTICS")
    print("=" * 70)

    # Approval stats
    approval_stats = tracker.get_stats()
    print(f"\n📋 Approval History:")
    print(f"  Total approvals (30 days): {approval_stats['total_approvals_30d']}")
    print(f"  Total approvals (7 days):  {approval_stats['total_approvals_7d']}")
    print(f"  Unique permissions (30d):  {approval_stats['unique_permissions_30d']}")
    print(f"  Unique projects (30d):     {approval_stats['unique_projects_30d']}")

    # Pattern stats
    pattern_stats = detector.get_pattern_stats(days=days)
    print(f"\n🔍 Pattern Detection ({days} days):")
    print(f"  Patterns detected:         {pattern_stats['patterns_detected']}")
    print(f"  Patterns above threshold:  {pattern_stats['patterns_above_threshold']}")

    if pattern_stats.get('high_confidence_patterns'):
        print(f"\n✨ High Confidence Patterns:")
        for pattern_type in pattern_stats['high_confidence_patterns']:
            print(f"  • {pattern_type}")

    if pattern_stats.get('category_counts'):
        print(f"\n📂 Category Breakdown:")
        for category, count in sorted(
            pattern_stats['category_counts'].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]:
            print(f"  {category}: {count} approvals")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    sys.exit(main())
