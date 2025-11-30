#!/usr/bin/env python3
"""
Generate machine-specific .claude/CLAUDE.local.md files.
Includes hardware info, running services, WIP notes, and experiments.
This file should be gitignored and is unique to each development machine.
"""

import argparse
import logging
import sys
from pathlib import Path

from claude_automation.analyzers import SystemAnalyzer
from claude_automation.generators.local_context_generator import LocalContextGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate machine-specific CLAUDE.local.md context file"
    )

    parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to project directory (default: current directory)",
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

    logger.info(f"Analyzing system for project: {project_path}")

    try:
        # Analyze system
        analyzer = SystemAnalyzer(project_path)
        config = analyzer.analyze()

        # Dry run mode
        if args.dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Hostname: {config.hostname}")
            logger.info(f"CPU: {config.cpu_info}")
            logger.info(f"Memory: {config.memory_total}")
            logger.info(f"Disk: {config.disk_usage}")
            logger.info(f"Running services: {len(config.running_services)}")
            for service in config.running_services:
                logger.info(f"  - {service}")
            logger.info(f"Git branches: {len(config.current_branches)}")
            for branch in config.current_branches:
                logger.info(f"  - {branch}")
            logger.info(f"WIP notes: {len(config.wip_notes)}")
            logger.info(f"Experiments: {len(config.experiments)}")
            logger.info(f"Output path: {config.local_claude_file}")
            logger.info("=== END DRY RUN ===")
            return 0

        # Generate local context
        generator = LocalContextGenerator()
        result = generator.generate(config)

        # Report results
        if result.success:
            logger.info("✅ Local context generated successfully")
            logger.info(f"   Output: {result.output_path}")
            logger.info(f"   Hostname: {result.stats.get('hostname')}")
            logger.info(f"   CPU: {result.stats.get('cpu_info')}")
            logger.info(f"   Memory: {result.stats.get('memory_total')}")
            logger.info(f"   Services: {result.stats.get('services_count', 0)}")
            logger.info(f"   Branches: {result.stats.get('branches_count', 0)}")
            logger.info(f"   WIP notes: {result.stats.get('wip_notes_count', 0)}")
            logger.info(f"   Experiments: {result.stats.get('experiments_count', 0)}")
            logger.info("")
            logger.info(
                "💡 Edit .claude/CLAUDE.local.md to add WIP notes and experiments"
            )
            logger.info("   This file is gitignored and machine-specific")
            return 0
        else:
            logger.error("❌ Local context generation failed")
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
