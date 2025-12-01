#!/usr/bin/env python3
"""
Generate tool usage analytics and append to CLAUDE.md.
Analyzes installed system tools and their usage patterns.
"""

import argparse
import logging
import sys
from pathlib import Path

from claude_automation.analyzers.tool_usage_analyzer import ToolUsageAnalyzer
from claude_automation.generators.tool_usage_analytics_generator import (
    ToolUsageAnalyticsGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate tool usage analytics for CLAUDE.md"
    )

    parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to project directory (default: current directory)",
    )

    parser.add_argument(
        "--analysis-period",
        type=int,
        default=30,
        help="Analysis period in days (default: 30)",
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

    logger.info(f"Analyzing tool usage for project: {project_path}")

    try:
        # Analyze tool usage
        analyzer = ToolUsageAnalyzer(project_path)
        config = analyzer.analyze(analysis_period_days=args.analysis_period)

        # Dry run mode
        if args.dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Project: {config.project_path}")
            logger.info(
                f"Packages.nix: {project_path / 'modules' / 'core' / 'packages.nix'}"
            )
            logger.info("")
            logger.info(f"Total tools: {config.total_tools}")
            logger.info(
                f"Used tools: {len(config.used_tools)} ({config.adoption_rate:.1f}%)"
            )
            logger.info(f"Dormant tools: {config.unused_tool_count}")
            logger.info(f"Human tools: {config.human_tool_count}")
            logger.info(f"Claude tools: {config.claude_tool_count}")
            logger.info("")
            logger.info("Top 5 tools:")
            for i, tool in enumerate(
                sorted(
                    config.used_tools, key=lambda t: t.total_invocations, reverse=True
                )[:5],
                1,
            ):
                logger.info(
                    f"  {i}. {tool.tool_name}: {tool.total_invocations} uses (H:{tool.human_invocations} C:{tool.claude_invocations})"
                )
            logger.info("")
            logger.info(f"Recommendations: {len(config.recommendations)}")
            for rec in sorted(config.recommendations, key=lambda r: r.priority)[:5]:
                logger.info(
                    f"  [{rec.recommendation_type}] {rec.tool_name}: {rec.reason}"
                )
            logger.info("")
            logger.info(f"Output would be appended to: {config.claude_file}")
            logger.info("=== END DRY RUN ===")
            return 0

        # Generate analytics
        generator = ToolUsageAnalyticsGenerator()
        result = generator.generate(config)

        # Report results
        if result.success:
            logger.info("✅ Tool usage analytics generated successfully")
            logger.info(f"   Output: {result.output_path}")
            logger.info(f"   Total tools: {result.stats.get('total_tools', 0)}")
            logger.info(
                f"   Used tools: {result.stats.get('used_tools', 0)} ({result.stats.get('adoption_rate', 0):.1f}%)"
            )
            logger.info(f"   Dormant tools: {result.stats.get('dormant_tools', 0)}")
            logger.info(f"   Recommendations: {result.stats.get('recommendations', 0)}")
            logger.info("")
            logger.info("💡 Check your CLAUDE.md for the System Tool Usage section!")
            logger.info("   Full report available at: .claude/tool-analytics.md")
            return 0
        else:
            logger.error("❌ Tool usage analytics generation failed")
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
