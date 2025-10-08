#!/usr/bin/env python3
"""
Update .claude/settings.local.json with optimized permissions.
Auto-detects project type and generates appropriate permissions.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_automation.analyzers import ProjectDetector
from claude_automation.generators.permissions_generator import PermissionsGenerator
from claude_automation.schemas import PermissionsConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate optimized Claude Code permissions for a project"
    )

    parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to project directory (default: current directory)",
    )

    parser.add_argument(
        "--preserve-customizations",
        action="store_true",
        default=True,
        help="Preserve user customizations (default: True)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite all settings, ignoring user customizations",
    )

    parser.add_argument(
        "--project-type",
        choices=["python", "nodejs", "rust", "nixos", "base"],
        help="Force specific project type instead of auto-detection",
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


def get_modern_cli_tools() -> list[str]:
    """Get list of modern CLI tools from system CLAUDE.md."""
    # Hardcoded list of modern CLI tools for permissions
    return [
        "fd",
        "eza",
        "bat",
        "rg",
        "dust",
        "procs",
        "jless",
        "yq",
        "jq",
        "delta",
        "choose",
        "btm",
        "bottom",
    ]


def analyze_project(
    project_path: Path, forced_type: str | None = None
) -> PermissionsConfig:
    """
    Analyze project and build PermissionsConfig.

    Args:
        project_path: Path to project
        forced_type: Optional forced project type

    Returns:
        PermissionsConfig instance
    """
    detector = ProjectDetector(project_path)

    # Detect project type
    if forced_type:
        from claude_automation.schemas import ProjectType

        project_type = ProjectType[forced_type.upper()]
        logger.info(f"Using forced project type: {project_type.value}")
    else:
        project_type = detector.detect()
        logger.info(f"Detected project type: {project_type.value}")

    # Detect quality tools
    quality_tools = detector.detect_quality_tools()
    logger.info(f"Detected quality tools: {quality_tools}")

    # Detect package managers
    package_managers = detector.detect_package_managers()
    logger.info(f"Detected package managers: {package_managers}")

    # Detect sensitive paths
    sensitive_paths = detector.detect_sensitive_paths()
    if sensitive_paths:
        logger.info(f"Detected sensitive paths: {sensitive_paths}")

    # Check for tests
    has_tests = detector.has_tests()
    logger.info(f"Has tests: {has_tests}")

    # Get username
    username = os.getenv("USER", "unknown")

    # Determine template name
    template_map = {
        "PYTHON": "python.j2",
        "NODEJS": "nodejs.j2",
        "RUST": "rust.j2",
        "NIXOS": "nixos.j2",
        "MIXED": "base.j2",
        "UNKNOWN": "base.j2",
    }
    template_name = f"permissions/{template_map[project_type.name]}"

    # Build configuration
    config = PermissionsConfig(
        project_path=project_path,
        project_type=project_type,
        usage_patterns=[],  # TODO: Implement usage pattern analysis in Phase 6
        existing_hooks=None,
        quality_tools=quality_tools,
        package_managers=package_managers,
        sensitive_paths=sensitive_paths,
        modern_cli_tools=get_modern_cli_tools(),
        username=username,
        timestamp=datetime.now(),
        has_tests=has_tests,
        template_name=template_name,
    )

    return config


def main():
    """Main entry point."""
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate project path
    project_path = args.project_path.resolve()
    if not project_path.exists():
        logger.error(f"Project path does not exist: {project_path}")
        sys.exit(1)

    if not project_path.is_dir():
        logger.error(f"Project path is not a directory: {project_path}")
        sys.exit(1)

    logger.info(f"Analyzing project: {project_path}")

    try:
        # Analyze project
        config = analyze_project(project_path, args.project_type)

        # Dry run mode
        if args.dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Project type: {config.project_type.value}")
            logger.info(f"Template: {config.template_name}")
            logger.info(f"Quality tools: {config.quality_tools}")
            logger.info(f"Package managers: {config.package_managers}")
            logger.info(f"Modern CLI tools: {len(config.modern_cli_tools)}")
            logger.info(f"Sensitive paths: {config.sensitive_paths}")
            logger.info(f"Has tests: {config.has_tests}")
            logger.info(f"Output path: {config.settings_file}")
            logger.info("=== END DRY RUN ===")
            return 0

        # Generate permissions
        generator = PermissionsGenerator()
        preserve_customizations = not args.force and args.preserve_customizations

        result = generator.generate(config, preserve_customizations)

        # Report results
        if result.success:
            logger.info("✅ Permissions generated successfully")
            logger.info(f"   Output: {result.output_path}")
            if result.backup_path:
                logger.info(f"   Backup: {result.backup_path}")
            logger.info(f"   Project type: {result.stats.get('project_type')}")
            logger.info(
                f"   Quality tools: {result.stats.get('quality_tools_count', 0)}"
            )
            logger.info(
                f"   Package managers: {result.stats.get('package_managers_count', 0)}"
            )
            logger.info(f"   Template used: {result.stats.get('template_used')}")
            return 0
        else:
            logger.error("❌ Permissions generation failed")
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
