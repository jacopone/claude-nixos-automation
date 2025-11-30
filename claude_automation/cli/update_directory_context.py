#!/usr/bin/env python3
"""
Generate directory-level CLAUDE.md files for better organization.
Auto-detects directory purpose and generates appropriate context.
"""

import argparse
import logging
import sys
from pathlib import Path

from claude_automation.analyzers import DirectoryAnalyzer
from claude_automation.generators.directory_context_generator import (
    DirectoryContextGenerator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate directory-level CLAUDE.md context files"
    )

    parser.add_argument(
        "directories",
        type=Path,
        nargs="*",
        help="Directories to generate context for (default: auto-detect important dirs)",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    parser.add_argument(
        "--auto-discover",
        action="store_true",
        default=True,
        help="Auto-discover important directories (default: True)",
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


def discover_important_directories(project_root: Path) -> list[Path]:
    """
    Auto-discover important directories that should have context files.

    Args:
        project_root: Project root directory

    Returns:
        List of directory paths
    """
    important_dirs = []

    # Common important directory patterns
    patterns = [
        "src",
        "lib",
        "tests",
        "test",
        "docs",
        "doc",
        "modules",
        "scripts",
        "templates",
        "config",
        "data",
    ]

    for pattern in patterns:
        # Check root level
        candidate = project_root / pattern
        if candidate.exists() and candidate.is_dir():
            important_dirs.append(candidate)

        # Check one level deep (e.g., src/components)
        for subdir in candidate.glob("*"):
            if subdir.is_dir() and not subdir.name.startswith("."):
                # Only include if it has substantial content
                file_count = sum(1 for _ in subdir.glob("*") if _.is_file())
                if file_count >= 3:  # At least 3 files
                    important_dirs.append(subdir)

    return sorted(set(important_dirs))


def main():
    """Main entry point."""
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine directories to process
    if args.directories:
        directories = [d.resolve() for d in args.directories]
    elif args.auto_discover:
        logger.info(f"Auto-discovering directories in {args.project_root}")
        directories = discover_important_directories(args.project_root)
        logger.info(f"Found {len(directories)} directories to process")
    else:
        logger.error("No directories specified and auto-discover disabled")
        return 1

    if not directories:
        logger.warning("No directories to process")
        return 0

    # Validate directories
    for directory in directories:
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return 1
        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory}")
            return 1

    # Process each directory
    generator = DirectoryContextGenerator()
    success_count = 0
    fail_count = 0

    for directory in directories:
        logger.info(f"Processing: {directory}")

        try:
            # Analyze directory
            analyzer = DirectoryAnalyzer(directory)
            config = analyzer.analyze()

            # Dry run mode
            if args.dry_run:
                logger.info(f"  Would generate: {config.claude_file}")
                logger.info(f"  Purpose: {config.purpose.value}")
                logger.info(f"  Files: {config.file_count}")
                logger.info(f"  Key files: {config.key_files}")
                success_count += 1
                continue

            # Generate context
            result = generator.generate(config)

            # Report results
            if result.success:
                logger.info(f"  ✅ Generated: {result.output_path}")
                if result.backup_path:
                    logger.info(f"  Backup: {result.backup_path}")
                success_count += 1
            else:
                logger.error(f"  ❌ Failed: {directory}")
                for error in result.errors:
                    logger.error(f"     Error: {error}")
                fail_count += 1

        except Exception as e:
            logger.error(f"  ❌ Unexpected error: {e}", exc_info=True)
            fail_count += 1

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Summary: {success_count} succeeded, {fail_count} failed")
    logger.info("=" * 60)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
