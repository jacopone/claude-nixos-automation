#!/usr/bin/env python3
"""
Project-level CLAUDE.md generator v2.0
Modern, template-based automation following 2025 best practices.
"""

import logging
import sys
from pathlib import Path

from claude_automation.generators.project_generator import ProjectGenerator
from claude_automation.validators.content_validator import ContentValidator


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    """Main function."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        print("🔄 Updating project-level CLAUDE.md...")

        # Determine paths
        # If run from nixos-config directory, use current dir
        # Otherwise try to find it in common locations
        if len(sys.argv) > 1:
            config_dir = Path(sys.argv[1])
        elif (Path.cwd() / "flake.nix").exists() and (Path.cwd() / "modules").exists():
            config_dir = Path.cwd()
        elif (Path.home() / "nixos-config" / "flake.nix").exists():
            config_dir = Path.home() / "nixos-config"
        else:
            logger.error(
                "Could not find nixos-config directory. Please run from nixos-config or pass path as argument."
            )
            return 1

        output_path = config_dir / "CLAUDE.md"

        # Initialize generator
        generator = ProjectGenerator()

        # Get summary stats first
        stats = generator.get_summary_stats(config_dir)
        if "error" in stats:
            logger.error(f"Failed to analyze configuration: {stats['error']}")
            return 1

        # Generate the file
        result = generator.generate(output_path, config_dir)

        if result.success:
            print("✅ Updated project CLAUDE.md")
            print(f"📊 Package count: {stats['package_count']}")
            print(f"🐟 Fish abbreviations: {stats['fish_abbreviation_count']}")
            print(f"📁 Git status: {stats['git_status']}")

            # Validate the generated content
            validator = ContentValidator()
            validation = validator.validate_file(output_path, "project")

            if not validation["valid"]:
                print("⚠️  Content validation warnings:")
                for error in validation["errors"]:
                    print(f"   - {error}")
            else:
                print("✅ Content validation passed")

            return 0

        else:
            print("❌ Failed to update project-level CLAUDE.md")
            for error in result.errors:
                print(f"   Error: {error}")
            for warning in result.warnings:
                print(f"   Warning: {warning}")
            return 1

    except Exception as e:
        logger.error(f"Project generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
