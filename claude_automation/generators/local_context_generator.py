"""
Local context generator for machine-specific CLAUDE.local.md files.
These files are gitignored and contain hardware/WIP/experiment notes.
"""

import logging
from pathlib import Path

from ..schemas import GenerationResult, LocalContextConfig
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class LocalContextGenerator(BaseGenerator):
    """Generates machine-specific .claude/CLAUDE.local.md files."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize local context generator."""
        super().__init__(template_dir)

    def generate(self, config: LocalContextConfig) -> GenerationResult:
        """
        Generate .claude/CLAUDE.local.md file.

        Args:
            config: LocalContextConfig with system and project info

        Returns:
            GenerationResult with success status and stats
        """
        output_path = config.local_claude_file

        try:
            # Ensure .claude directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare template context
            context = self._prepare_template_context(config)

            # Render template
            content = self.render_template("local_context.j2", context)

            # Write file (backup not needed - local changes are expected)
            result = self.write_file(output_path, content, create_backup=False)

            # Add generation stats
            if result.success:
                result.stats.update(
                    {
                        "hostname": config.hostname,
                        "cpu_info": config.cpu_info,
                        "memory_total": config.memory_total,
                        "services_count": len(config.running_services),
                        "branches_count": len(config.current_branches),
                        "wip_notes_count": len(config.wip_notes),
                        "experiments_count": len(config.experiments),
                    }
                )

                logger.info(
                    f"Generated local context for {config.hostname} at {output_path}"
                )

            return result

        except Exception as e:
            error_msg = f"Local context generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _prepare_template_context(self, config: LocalContextConfig) -> dict:
        """Prepare Jinja2 template context from LocalContextConfig."""
        return {
            "project_path": str(config.project_path),
            "hostname": config.hostname,
            "cpu_info": config.cpu_info,
            "memory_total": config.memory_total,
            "disk_usage": config.disk_usage,
            "running_services": config.running_services,
            "current_branches": config.current_branches,
            "wip_notes": config.wip_notes,
            "experiments": config.experiments,
            "timestamp": config.timestamp.isoformat(),
        }
