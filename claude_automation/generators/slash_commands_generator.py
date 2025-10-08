"""
Slash commands generator for Claude Code.
Generates individual command files in ~/.claude/commands/ based on project type and workflows.
"""

import logging

from ..schemas import GenerationResult, SlashCommandsConfig
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class SlashCommandsGenerator(BaseGenerator):
    """Generates slash command files for Claude Code."""

    def generate(self, config: SlashCommandsConfig) -> GenerationResult:
        """
        Generate slash command files.

        Args:
            config: Slash commands configuration

        Returns:
            GenerationResult with generation status and stats
        """
        try:
            # Ensure commands directory exists
            config.commands_dir.mkdir(parents=True, exist_ok=True)

            # Track generated files
            generated_files = []
            skipped_files = []

            # Generate each command
            for command in config.commands:
                command_file = config.commands_dir / f"{command.name}.md"

                # Check if file already exists
                if command_file.exists():
                    logger.debug(
                        f"Command file already exists: {command_file}, overwriting"
                    )

                # Create command content
                content = self._generate_command_content(command, config.project_type)

                # Write command file
                try:
                    command_file.write_text(content)
                    generated_files.append(command.name)
                    logger.info(f"✅ Generated command: /{command.name}")
                except Exception as e:
                    logger.error(f"Failed to write command file {command_file}: {e}")
                    skipped_files.append(command.name)

            # Collect stats
            stats = {
                "commands_generated": len(generated_files),
                "commands_skipped": len(skipped_files),
                "commands_dir": str(config.commands_dir),
                "project_type": config.project_type.value,
                "workflows_detected": len(config.common_workflows),
                "generated_commands": generated_files,
            }

            # Build result
            if generated_files:
                return GenerationResult(
                    success=True,
                    output_path=str(config.commands_dir),
                    stats=stats,
                    warnings=(
                        [f"Skipped {len(skipped_files)} commands"]
                        if skipped_files
                        else []
                    ),
                )
            else:
                return GenerationResult(
                    success=False,
                    output_path=str(config.commands_dir),
                    errors=["No commands were generated"],
                    stats=stats,
                )

        except Exception as e:
            logger.error(f"Failed to generate slash commands: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                output_path=str(config.commands_dir),
                errors=[str(e)],
            )

    def _generate_command_content(self, command, project_type: str) -> str:
        """
        Generate content for a command file.

        Args:
            command: SlashCommand object
            project_type: Project type for context

        Returns:
            Command file content
        """
        # Command files are simple markdown with the prompt
        # Claude Code reads these and executes the prompt when invoked

        content_lines = [
            f"# /{command.name}",
            "",
            f"**Category**: {command.category.value}",
            f"**Description**: {command.description}",
            "",
        ]

        if command.requires_args:
            content_lines.extend(
                [
                    "**Requires arguments**: Yes",
                    f"**Example**: `{command.example_usage}`",
                    "",
                ]
            )
        else:
            content_lines.extend(
                [
                    "**Requires arguments**: No",
                    f"**Example**: `{command.example_usage}`",
                    "",
                ]
            )

        content_lines.extend(
            [
                "---",
                "",
                command.prompt,
            ]
        )

        return "\n".join(content_lines)
