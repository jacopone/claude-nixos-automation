#!/usr/bin/env python3
"""
Generate usage analytics from Fish shell history.
Appends analytics section to project CLAUDE.md file.
"""

import argparse
import logging
import sys
from pathlib import Path

from claude_automation.analyzers.usage_tracker import UsageTracker
from claude_automation.generators.usage_analytics_generator import (
    UsageAnalyticsGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate usage analytics from Fish shell history"
    )

    parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to project directory (default: current directory)",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of top commands to include (default: 20)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate project path
    project_path = args.project_path.resolve()
    if not project_path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        return 1

    if not project_path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        return 1

    logger.info(f"Analyzing usage for project: {project_path}")

    try:
        # Track usage
        tracker = UsageTracker(project_path)
        config = tracker.analyze(top_n=args.top_n)

        # Dry run mode
        if args.dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Fish history: {config.fish_history_path}")
            logger.info(f"Total commands: {config.total_commands:,}")
            logger.info(f"Unique commands: {config.unique_commands}")
            logger.info("")
            logger.info(f"Top {len(config.top_commands)} commands:")
            for i, cmd in enumerate(config.top_commands, 1):
                stats = config.command_stats[cmd]
                logger.info(f"  {i}. {cmd}: {stats.count} times ({stats.category})")
            logger.info("")
            logger.info(f"Tools tracked: {len(config.tool_usage)}")
            for tool, count in sorted(
                config.tool_usage.items(), key=lambda x: x[1], reverse=True
            ):
                logger.info(f"  - {tool}: {count} times")
            logger.info("")
            logger.info(f"Workflow patterns: {len(config.workflow_patterns)}")
            for pattern in config.workflow_patterns:
                logger.info(f"  - {pattern}")
            logger.info("")
            logger.info(f"Output would be written to: {config.claude_file}")
            logger.info("=== END DRY RUN ===")
            return 0

        # Generate analytics
        generator = UsageAnalyticsGenerator()
        result = generator.generate(config)

        # Report results
        if result.success:
            logger.info("✅ Usage analytics generated successfully")
            logger.info(f"   Output: {result.output_path}")
            logger.info(f"   Total commands: {result.stats.get('total_commands', 0):,}")
            logger.info(f"   Unique commands: {result.stats.get('unique_commands', 0)}")
            logger.info(f"   Top commands: {result.stats.get('top_commands_count', 0)}")
            logger.info(f"   Tools tracked: {result.stats.get('tools_tracked', 0)}")
            logger.info(
                f"   Workflow patterns: {result.stats.get('workflow_patterns', 0)}"
            )
            logger.info("")
            logger.info(
                "💡 Check your CLAUDE.md to see usage analytics section appended!"
            )
            return 0
        else:
            logger.error("❌ Usage analytics generation failed")
            for error in result.errors:
                logger.error(f"   Error: {error}")
            for warning in result.warnings:
                logger.warning(f"   Warning: {warning}")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
