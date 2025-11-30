#!/usr/bin/env python3
"""
Generate slash commands for Claude Code based on project type and workflows.
Creates command files in ~/.claude/commands/ directory.
"""

import argparse
import logging
import sys
from pathlib import Path

from claude_automation.analyzers.project_detector import ProjectDetector
from claude_automation.analyzers.workflow_analyzer import WorkflowAnalyzer
from claude_automation.generators.slash_commands_generator import (
    SlashCommandsGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate slash commands for Claude Code"
    )

    parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to project directory (default: current directory)",
    )

    parser.add_argument(
        "--commands-dir",
        type=Path,
        default=Path.home() / ".claude" / "commands",
        help="Commands directory (default: ~/.claude/commands)",
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

    logger.info(f"Analyzing project: {project_path}")

    try:
        # Detect project type
        detector = ProjectDetector(project_path)
        project_type = detector.detect()
        logger.info(f"Detected project type: {project_type.value}")

        # Analyze workflows
        analyzer = WorkflowAnalyzer(project_path, project_type)
        config = analyzer.analyze(args.commands_dir)

        # Dry run mode
        if args.dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Project type: {config.project_type.value}")
            logger.info(f"Commands directory: {config.commands_dir}")
            logger.info(f"Commands to generate: {len(config.commands)}")
            logger.info("")
            logger.info("Commands:")
            for cmd in config.commands:
                logger.info(f"  /{cmd.name} - {cmd.description}")
            logger.info("")
            logger.info(f"Common workflows detected: {len(config.common_workflows)}")
            for workflow in config.common_workflows:
                logger.info(f"  - {workflow}")
            logger.info("=== END DRY RUN ===")
            return 0

        # Generate commands
        generator = SlashCommandsGenerator()
        result = generator.generate(config)

        # Report results
        if result.success:
            logger.info("✅ Slash commands generated successfully")
            logger.info(f"   Commands directory: {result.output_path}")
            logger.info(
                f"   Commands generated: {result.stats.get('commands_generated', 0)}"
            )
            logger.info(f"   Project type: {result.stats.get('project_type')}")
            logger.info(
                f"   Workflows detected: {result.stats.get('workflows_detected', 0)}"
            )
            logger.info("")
            logger.info("Generated commands:")
            for cmd_name in result.stats.get("generated_commands", []):
                logger.info(f"   /{cmd_name}")
            logger.info("")
            logger.info(
                "💡 Commands are now available in Claude Code! Try typing / to see them."
            )
            return 0
        else:
            logger.error("❌ Slash commands generation failed")
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
