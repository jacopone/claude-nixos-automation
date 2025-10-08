"""
Directory context generator for directory-level CLAUDE.md files.
"""

import logging
from pathlib import Path

from ..schemas import DirectoryContextConfig, GenerationResult
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class DirectoryContextGenerator(BaseGenerator):
    """Generates directory-level CLAUDE.md files."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize directory context generator."""
        super().__init__(template_dir)

    def generate(self, config: DirectoryContextConfig) -> GenerationResult:
        """
        Generate directory-level CLAUDE.md file.

        Args:
            config: DirectoryContextConfig with directory info

        Returns:
            GenerationResult with success status and stats
        """
        output_path = config.claude_file

        try:
            # Prepare template context
            context = self._prepare_template_context(config)

            # Select template based on purpose
            template_name = self._select_template(config.purpose)

            # Render template
            content = self.render_template(template_name, context)

            # Write file
            result = self.write_file(output_path, content)

            # Add generation stats
            if result.success:
                result.stats.update(
                    {
                        "directory_name": config.directory_name,
                        "purpose": config.purpose.value,
                        "file_count": config.file_count,
                        "subdirectory_count": config.subdirectory_count,
                        "primary_file_types": config.primary_file_types,
                        "key_files_count": len(config.key_files),
                        "protected_count": len(config.do_not_touch),
                    }
                )

                logger.info(
                    f"Generated directory context for {config.directory_name} ({config.purpose.value})"
                )

            return result

        except Exception as e:
            error_msg = f"Directory context generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _select_template(self, purpose) -> str:
        """Select template based on directory purpose."""
        template_map = {
            "source_code": "directory/source_code.j2",
            "tests": "directory/tests.j2",
            "documentation": "directory/documentation.j2",
            "configuration": "directory/configuration.j2",
            "modules": "directory/modules.j2",
            "scripts": "directory/scripts.j2",
            "templates": "directory/templates.j2",
            "data": "directory/data.j2",
            "build": "directory/build.j2",
            "unknown": "directory/generic.j2",
        }

        return template_map.get(purpose.value, "directory/generic.j2")

    def _prepare_template_context(self, config: DirectoryContextConfig) -> dict:
        """Prepare Jinja2 template context from DirectoryContextConfig."""
        return {
            "directory_path": str(config.directory_path),
            "directory_name": config.directory_name,
            "purpose": config.purpose.value,
            "file_count": config.file_count,
            "subdirectory_count": config.subdirectory_count,
            "primary_file_types": config.primary_file_types,
            "do_not_touch": config.do_not_touch,
            "key_files": config.key_files,
            "description": config.description,
            "timestamp": config.timestamp.isoformat(),
        }
