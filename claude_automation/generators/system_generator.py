"""
System-level CLAUDE.md generator.

Simplified: No longer extracts tool lists from packages.nix.
MCP-NixOS provides real-time package queries instead.
"""

import logging
from datetime import datetime
from pathlib import Path

from ..schemas import GenerationResult
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class SystemGenerator(BaseGenerator):
    """
    Generates system-level CLAUDE.md files.

    Sources: CLAUDE-USER-POLICIES.md (user policies)
    Artifacts: System-level CLAUDE.md with policies + tool substitution table

    Note: Tool lists removed in favor of MCP-NixOS for dynamic queries.
    """

    # Source/Artifact declarations
    MANUAL_SOURCES = [
        "CLAUDE-USER-POLICIES.md",  # User policies
    ]
    GENERATED_ARTIFACTS = [
        "CLAUDE.md",  # System-level CLAUDE.md
    ]

    def __init__(self, template_dir: Path = None):
        super().__init__(template_dir)

    def generate(self, output_path: Path, config_dir: Path = None) -> GenerationResult:
        """Generate system-level CLAUDE.md file."""
        if config_dir is None:
            config_dir = self._get_repo_root()

        try:
            # Read user policies if they exist
            user_policies_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
            user_policies_content = ""
            has_user_policies = False

            if user_policies_file.exists():
                try:
                    user_policies_content = user_policies_file.read_text(encoding="utf-8")
                    has_user_policies = True
                    logger.info(f"Read user policies from {user_policies_file}")
                except Exception as e:
                    logger.warning(f"Failed to read user policies: {e}")

            # Prepare template context (minimal - no tool extraction)
            context = {
                "timestamp": datetime.now(),
                "user_policies": user_policies_content,
                "has_user_policies": has_user_policies,
            }

            # Render template
            content = self.render_template("system-claude.j2", context)

            # Determine source files used
            source_files = []
            if has_user_policies:
                source_files.append("CLAUDE-USER-POLICIES.md")

            # Write artifact with protection and header
            result = self.write_artifact(
                output_path, content, source_files=source_files
            )

            if result.success:
                result.stats.update({
                    "has_user_policies": has_user_policies,
                    "note": "Slim version - MCP-NixOS for package queries",
                })
                logger.info("Generated system CLAUDE.md (slim version)")

            return result

        except Exception as e:
            error_msg = f"System generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def get_summary_stats(self, config_dir: Path = None) -> dict:
        """Get summary statistics without generating the full file."""
        user_policies_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"

        return {
            "status": "slim_version",
            "has_user_policies": user_policies_file.exists(),
            "note": "Tool extraction removed - use MCP-NixOS for queries",
            "timestamp": datetime.now().isoformat(),
        }
