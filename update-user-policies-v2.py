#!/usr/bin/env python3
"""
Generate/update user policies files for Claude Code.
- ALWAYS updates: ~/.claude/CLAUDE-USER-POLICIES.md.example
- ONLY creates if missing: ~/.claude/CLAUDE-USER-POLICIES.md
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.generators.user_policies_generator import UserPoliciesGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for user policies generation."""
    logger.info("🔧 User Policies Generation System v2.0")
    logger.info("")

    # Initialize generator
    generator = UserPoliciesGenerator()

    # Check status
    status = generator.get_user_file_status()
    logger.info(f"📊 Current Status:")
    logger.info(f"   User file exists: {status['user_file_exists']}")
    logger.info(f"   Example file exists: {status['example_file_exists']}")
    logger.info(f"   User file path: {status['user_file_path']}")
    logger.info(f"   Example path: {status['example_file_path']}")
    logger.info("")

    # Update both files
    logger.info("🔄 Updating user policies files...")
    results = generator.update_both_files()

    # Report results
    logger.info("")
    logger.info("📊 Generation Results:")
    logger.info("")

    # Example file result
    example_result = results["example"]
    if example_result.success:
        logger.info(
            f"✅ Example template updated: {example_result.output_path}"
        )
    else:
        logger.error(
            f"❌ Failed to update example template: {', '.join(example_result.errors)}"
        )

    # User file result
    user_result = results["user_file"]
    if user_result.success:
        if user_result.stats.get("skipped"):
            logger.info(
                f"✅ User policies file already exists (preserved): {user_result.output_path}"
            )
        else:
            logger.info(
                f"✅ Created initial user policies file: {user_result.output_path}"
            )
            logger.info("")
            logger.info("💡 Next Steps:")
            logger.info("   1. Edit ~/.claude/CLAUDE-USER-POLICIES.md")
            logger.info("   2. Uncomment the policies you want to enable")
            logger.info("   3. Delete sections you don't need")
            logger.info("   4. This file will NEVER be regenerated automatically")
    else:
        logger.error(
            f"❌ Failed to generate user policies: {', '.join(user_result.errors)}"
        )

    logger.info("")
    logger.info("✨ User policies generation complete!")
    logger.info("")
    logger.info("📚 Documentation:")
    logger.info("   - User file: Your customized policies (never auto-updated)")
    logger.info("   - Example file: Latest best practices (auto-updated on rebuild)")
    logger.info("   - Compare: diff CLAUDE-USER-POLICIES.md CLAUDE-USER-POLICIES.md.example")

    # Exit with appropriate status code
    sys.exit(0 if all(r.success for r in results.values()) else 1)


if __name__ == "__main__":
    main()
