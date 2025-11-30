#!/usr/bin/env python3
"""
Generate MCP usage analytics and append to CLAUDE.md.
Analyzes configured MCP servers and their connection status.
"""

import argparse
import logging
import sys
from pathlib import Path

from claude_automation.analyzers.mcp_usage_analyzer import MCPUsageAnalyzer
from claude_automation.generators.mcp_usage_analytics_generator import (
    MCPUsageAnalyticsGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate MCP usage analytics for CLAUDE.md"
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

    logger.info(f"Analyzing MCP usage for project: {project_path}")

    try:
        # Analyze MCP usage
        analyzer = MCPUsageAnalyzer(project_path)
        config = analyzer.analyze(analysis_period_days=args.analysis_period)

        # Dry run mode
        if args.dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Project: {config.project_path}")
            logger.info(f"Global config: {config.global_mcp_config or 'Not found'}")
            logger.info(f"Project config: {config.project_mcp_config or 'Not found'}")
            logger.info("")
            logger.info(f"Configured servers: {config.total_configured_servers}")
            for server in config.configured_servers:
                logger.info(
                    f"  - {server.name}: {server.status.value} ({server.config_location})"
                )
            logger.info("")
            logger.info(f"Connected servers: {len(config.connected_servers)}")
            logger.info(f"Unused servers: {len(config.unused_servers)}")
            logger.info(f"Recommendations: {len(config.recommendations)}")
            for rec in config.recommendations:
                logger.info(
                    f"  [{rec.recommendation_type}] {rec.server_name}: {rec.reason}"
                )
            logger.info("")
            logger.info(f"Output would be appended to: {config.claude_file}")
            logger.info("=== END DRY RUN ===")
            return 0

        # Generate analytics
        generator = MCPUsageAnalyticsGenerator()
        result = generator.generate(config)

        # Report results
        if result.success:
            logger.info("✅ MCP usage analytics generated successfully")
            logger.info(f"   Output: {result.output_path}")
            logger.info(
                f"   Configured servers: {result.stats.get('configured_servers', 0)}"
            )
            logger.info(
                f"   Connected servers: {result.stats.get('connected_servers', 0)}"
            )
            logger.info(f"   Recommendations: {result.stats.get('recommendations', 0)}")
            logger.info("")
            logger.info("💡 Check your CLAUDE.md for the MCP Server Status section!")
            return 0
        else:
            logger.error("❌ MCP usage analytics generation failed")
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
