#!/usr/bin/env python3
"""
Unified entry point for all adaptive learning components.
Coordinates permissions, MCP, context, workflows, instructions, cross-project, and meta-learning.

This script is designed to run at the end of ./rebuild-nixos workflow.
"""

import argparse
import logging
import sys

from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine
from claude_automation.schemas import AdaptiveSystemConfig

# Configure logging - WARNING by default (quiet), INFO with --verbose
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run adaptive learning system."""
    parser = argparse.ArgumentParser(
        description="Run Claude Code adaptive learning system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full interactive learning cycle (default)
  python run-adaptive-learning.py

  # Run non-interactively (auto-accept all suggestions)
  python run-adaptive-learning.py --no-interactive

  # Dry run (show suggestions without applying)
  python run-adaptive-learning.py --dry-run

  # Adjust detection thresholds
  python run-adaptive-learning.py --min-occurrences 5 --confidence 0.8
        """,
    )

    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        default=True,
        help="Present suggestions interactively (default: True)",
    )

    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Run non-interactively (auto-accept suggestions)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show suggestions without applying them",
    )

    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=1,
        help="Minimum occurrences for pattern detection (default: 1 for faster learning)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Minimum confidence threshold (0-1, default: 0.5 for faster learning)",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Analysis window in days (default: 30)",
    )

    parser.add_argument(
        "--max-suggestions",
        type=int,
        default=5,
        help="Maximum suggestions per component (default: 5)",
    )

    parser.add_argument(
        "--disable-meta-learning",
        action="store_true",
        help="Disable meta-learning calibration",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging level (--verbose shows detailed analyzer output)
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Validate arguments
    if args.confidence < 0.0 or args.confidence > 1.0:
        parser.error("--confidence must be between 0.0 and 1.0")

    if args.min_occurrences < 1:
        parser.error("--min-occurrences must be >= 1")

    if args.days < 1:
        parser.error("--days must be >= 1")

    # Create configuration
    config = AdaptiveSystemConfig(
        interactive=args.interactive and not args.dry_run,
        min_occurrences=args.min_occurrences,
        confidence_threshold=args.confidence,
        analysis_period_days=args.days,
        max_suggestions_per_component=args.max_suggestions,
        enable_meta_learning=not args.disable_meta_learning,
    )

    # Log configuration (only visible with --verbose)
    logger.info(
        f"Config: interactive={config.interactive}, threshold={config.confidence_threshold}, days={config.analysis_period_days}"
    )

    # Initialize engine
    try:
        engine = AdaptiveSystemEngine(config)
    except Exception as e:
        logger.error(f"Failed to initialize adaptive system engine: {e}", exc_info=True)
        return 1

    # Run learning cycle
    try:
        report = engine.run_full_learning_cycle()

        # Only show "no suggestions" message - if there WERE suggestions,
        # the interactive approval UI already displayed them
        if report.total_suggestions == 0:
            print("  ✓ No new suggestions")
        # else: interactive UI already showed the approval prompts

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Learning cycle interrupted by user")
        return 130  # Standard exit code for Ctrl+C

    except Exception as e:
        logger.error(f"Learning cycle failed: {e}", exc_info=True)
        print(f"\n❌ Learning cycle failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
