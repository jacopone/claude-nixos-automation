"""
Project-level CLAUDE.md generator using templates.

Simplified: No longer extracts package counts or working features.
The template is now static with only user memory preservation.
"""

import logging
from datetime import datetime
from pathlib import Path

from ..schemas import GenerationResult
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class ProjectGenerator(BaseGenerator):
    """Generates project-level CLAUDE.md files.

    The generator preserves user memory content between regenerations
    but no longer extracts dynamic data like package counts.
    MCP-NixOS is used for real-time package queries instead.
    """

    def __init__(self, template_dir: Path = None):
        super().__init__(template_dir)

    def generate(self, output_path: Path, config_dir: Path = None) -> GenerationResult:
        """Generate project-level CLAUDE.md file."""
        if config_dir is None:
            config_dir = self._get_repo_root()

        try:
            # Extract existing user memory content before regeneration
            user_memory = self._extract_user_memory(output_path)

            # Prepare minimal template context
            context = {
                "timestamp": datetime.now(),
            }

            # Render template
            content = self.render_template("project-claude.j2", context)

            # Inject preserved user memory content
            if user_memory:
                content = self._inject_user_memory(content, user_memory)
                logger.info("Preserved user memory content during regeneration")

            # Write file
            result = self.write_file(output_path, content)

            if result.success:
                logger.info("Generated project CLAUDE.md (slim version)")

            return result

        except Exception as e:
            error_msg = f"Project generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _extract_user_memory(self, file_path: Path) -> str:
        """Extract user memory content from existing CLAUDE.md file.

        Returns:
            str: Content between USER_MEMORY_START and USER_MEMORY_END markers,
                 or empty string if not found.
        """
        if not file_path.exists():
            return ""

        try:
            content = file_path.read_text(encoding="utf-8")

            # Find markers
            start_marker = "<!-- USER_MEMORY_START -->"
            end_marker = "<!-- USER_MEMORY_END -->"

            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)

            if start_idx == -1 or end_idx == -1:
                return ""

            # Extract content between markers (including the markers themselves)
            extracted = content[start_idx : end_idx + len(end_marker)]

            return extracted

        except Exception as e:
            logger.warning(f"Failed to extract user memory: {e}")
            return ""

    def _inject_user_memory(self, rendered_content: str, user_memory: str) -> str:
        """Inject preserved user memory into rendered template.

        Args:
            rendered_content: Newly rendered template content
            user_memory: Preserved user memory content (with markers)

        Returns:
            str: Content with user memory injected
        """
        if not user_memory:
            return rendered_content

        # Find the markers in the new content
        start_marker = "<!-- USER_MEMORY_START -->"
        end_marker = "<!-- USER_MEMORY_END -->"

        start_idx = rendered_content.find(start_marker)
        end_idx = rendered_content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            logger.warning("Could not find memory markers in rendered content")
            return rendered_content

        # Replace the section between markers with preserved content
        before = rendered_content[:start_idx]
        after = rendered_content[end_idx + len(end_marker) :]

        return before + user_memory + after

    def get_summary_stats(self, config_dir: Path = None) -> dict:
        """Get summary statistics."""
        return {
            "status": "slim_version",
            "note": "Package counts removed - use MCP-NixOS for queries",
            "timestamp": datetime.now().isoformat(),
        }
