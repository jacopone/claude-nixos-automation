"""
Permissions generator for .claude/settings.local.json files.
Generates optimized permissions based on project type and usage patterns.
"""

import json
import logging
from pathlib import Path

from ..schemas import GenerationResult, PermissionsConfig
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class PermissionsGenerator(BaseGenerator):
    """Generates .claude/settings.local.json with optimized permissions."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize permissions generator."""
        super().__init__(template_dir)

    def generate(
        self, config: PermissionsConfig, preserve_user_customizations: bool = True
    ) -> GenerationResult:
        """
        Generate .claude/settings.local.json file.

        Args:
            config: PermissionsConfig with project info
            preserve_user_customizations: If True, preserve entries marked with _user_customized

        Returns:
            GenerationResult with success status and stats
        """
        output_path = config.settings_file

        try:
            # Ensure .claude directory exists
            config.claude_dir.mkdir(exist_ok=True)

            # Load existing settings if present
            existing_settings = self._load_existing_settings(output_path)

            # Prepare template context
            context = self._prepare_template_context(config)

            # Render template
            rendered_content = self.render_template(config.template_name, context)

            # Parse rendered JSON
            new_settings = json.loads(rendered_content)

            # Merge with existing if needed
            if preserve_user_customizations and existing_settings:
                merged_settings = self._merge_settings(existing_settings, new_settings)
            else:
                merged_settings = new_settings

            # Write to file
            content = json.dumps(merged_settings, indent=2, ensure_ascii=False)
            result = self.write_file(output_path, content + "\n")

            # Add generation stats
            if result.success:
                result.stats.update(
                    {
                        "project_type": config.project_type.value,
                        "quality_tools_count": len(config.quality_tools),
                        "package_managers_count": len(config.package_managers),
                        "modern_cli_tools_count": len(config.modern_cli_tools),
                        "has_tests": config.has_tests,
                        "template_used": config.template_name,
                        "user_customizations_preserved": preserve_user_customizations,
                    }
                )

                logger.info(
                    f"Generated permissions for {config.project_type.value} project at {output_path}"
                )

            return result

        except Exception as e:
            error_msg = f"Permissions generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _load_existing_settings(self, settings_path: Path) -> dict | None:
        """Load existing settings.local.json if it exists."""
        if not settings_path.exists():
            return None

        try:
            with open(settings_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load existing settings: {e}")
            return None

    def _merge_settings(self, existing: dict, new: dict) -> dict:
        """
        Merge existing and new settings, preserving user customizations.

        Logic:
        - If existing entry has "_user_customized": true, keep it
        - Otherwise, use new generated value
        - Preserve any custom keys not in new settings
        """
        merged = new.copy()

        # Check for user-customized marker at root level
        if existing.get("_user_customized"):
            return existing  # Preserve entire file if marked

        # Merge permissions section
        if "permissions" in existing and "permissions" in new:
            merged["permissions"] = self._merge_permissions(
                existing["permissions"], new["permissions"]
            )

        # Merge hooks section
        if "hooks" in existing and "hooks" in new:
            merged["hooks"] = self._merge_hooks(existing["hooks"], new["hooks"])

        # Preserve custom root-level keys
        for key, value in existing.items():
            if key not in merged and not key.startswith("_"):
                merged[key] = value

        return merged

    def _merge_permissions(self, existing: dict, new: dict) -> dict:
        """Merge permissions section."""
        merged = new.copy()

        for permission_type in ["allow", "deny", "ask"]:
            if permission_type in existing:
                existing_list = existing[permission_type]

                # Check if user marked this section as customized
                if isinstance(existing_list, dict) and existing_list.get(
                    "_user_customized"
                ):
                    merged[permission_type] = existing_list
                    continue

                # Otherwise merge lists
                if permission_type in new:
                    # Combine and deduplicate
                    combined = list(set(existing_list + new[permission_type]))
                    merged[permission_type] = sorted(combined)

        return merged

    def _merge_hooks(self, existing: dict, new: dict) -> dict:
        """Merge hooks section, preserving existing hooks."""
        # If existing hooks are marked as user-customized, keep them
        if existing.get("_user_customized"):
            return existing

        # Otherwise, prefer new hooks but warn user
        logger.info("Replacing hooks with new generated hooks")
        return new

    def _prepare_template_context(self, config: PermissionsConfig) -> dict:
        """Prepare Jinja2 template context from PermissionsConfig."""
        return {
            "project_path": str(config.project_path),
            "project_type": config.project_type.value,
            "username": config.username,
            "timestamp": config.timestamp.isoformat(),
            "quality_tools": config.quality_tools,
            "package_managers": config.package_managers,
            "sensitive_paths": config.sensitive_paths,
            "modern_cli_tools": config.modern_cli_tools,
            "has_tests": config.has_tests,
            "existing_hooks": config.existing_hooks or {},
            "usage_patterns": [
                {
                    "command": p.command,
                    "frequency": p.frequency,
                    "last_used": p.last_used.isoformat(),
                }
                for p in config.usage_patterns
            ],
        }
