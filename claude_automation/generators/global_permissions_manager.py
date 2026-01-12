"""
GlobalPermissionsManager - Manages ~/.claude/settings.json permissions.

Handles TIER_1_SAFE patterns and cross-folder patterns that indicate
broad user trust across all projects.

Philosophy (Boris-style):
- If you approve a tool multiple times across different contexts, you trust that tool
- TIER_1_SAFE patterns (read-only tools) should be applied globally
- Cross-folder patterns (tools used in 2+ folders) indicate broad trust
"""

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GlobalPermissionsManager:
    """
    Manages global permissions in ~/.claude/settings.json.

    Responsibilities:
    1. Read/write ~/.claude/settings.json preserving existing structure
    2. Merge TIER_1_SAFE patterns without duplicates
    3. Handle cross-folder patterns (CrossFolder_*)
    4. Preserve user customizations and backup before changes
    """

    GLOBAL_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
    BACKUP_DIR = Path.home() / ".claude" / ".backups"

    def __init__(self, settings_path: Path | None = None):
        """
        Initialize GlobalPermissionsManager.

        Args:
            settings_path: Custom path for settings (defaults to ~/.claude/settings.json)
        """
        self.settings_path = settings_path or self.GLOBAL_SETTINGS_PATH
        self.backup_dir = self.settings_path.parent / ".backups"

    def load_settings(self) -> dict[str, Any]:
        """
        Load global settings, create structure if missing.

        Returns:
            Settings dictionary with at least permissions.allow structure
        """
        if not self.settings_path.exists():
            logger.info(f"Global settings not found at {self.settings_path}, creating new")
            return self._create_default_structure()

        try:
            with open(self.settings_path, encoding="utf-8") as f:
                settings = json.load(f)

            # Ensure permissions structure exists
            if "permissions" not in settings:
                settings["permissions"] = {"allow": [], "deny": []}
            if "allow" not in settings["permissions"]:
                settings["permissions"]["allow"] = []
            if "deny" not in settings["permissions"]:
                settings["permissions"]["deny"] = []

            return settings

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse global settings: {e}")
            # Create backup of corrupted file
            self._backup_corrupted_file()
            return self._create_default_structure()

    def _create_default_structure(self) -> dict[str, Any]:
        """Create default settings structure with permissions section."""
        return {
            "permissions": {
                "allow": [],
                "deny": [],
                "_tier1_learned": [],
                "_cross_folder_learned": [],
                "_last_updated": None,
            }
        }

    def save_settings(self, settings: dict[str, Any]) -> bool:
        """
        Save settings, preserving existing structure.

        Args:
            settings: Settings dictionary to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)

            # Update last modified timestamp
            if "permissions" in settings:
                settings["permissions"]["_last_updated"] = datetime.now().isoformat()

            # Write with nice formatting
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved global settings to {self.settings_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save global settings: {e}")
            return False

    def get_existing_permissions(self) -> set[str]:
        """
        Get existing global permission rules.

        Returns:
            Set of permission strings from the allow list
        """
        settings = self.load_settings()
        allow_list = settings.get("permissions", {}).get("allow", [])
        # Filter out comments (strings starting with //)
        return {rule for rule in allow_list if not rule.strip().startswith("//")}

    def add_permissions(
        self,
        rules: list[str],
        source: str = "auto-learned",
        tier: str | None = None,
    ) -> tuple[list[str], list[str]]:
        """
        Add permissions to global settings.

        Args:
            rules: List of permission rules to add
            source: Source of the rules (for tracking)
            tier: Tier classification (TIER_1_SAFE, CrossFolder, etc.)

        Returns:
            Tuple of (added_rules, skipped_rules)
        """
        if not rules:
            return [], []

        # Create backup before modification
        self.create_backup()

        settings = self.load_settings()
        existing = self.get_existing_permissions()

        added = []
        skipped = []

        for rule in rules:
            # Skip comments
            if rule.strip().startswith("//"):
                continue

            # Check if already exists or is covered by broader pattern
            if rule in existing:
                skipped.append(rule)
                logger.debug(f"Skipped (exact match): {rule}")
            elif self.is_covered_by_existing(rule, existing):
                skipped.append(rule)
                logger.debug(f"Skipped (covered by wildcard): {rule}")
            else:
                added.append(rule)

        if added:
            # Get current allow list
            allow_list = settings.get("permissions", {}).get("allow", [])

            # Add new rules with comment header if first time
            if not any(
                "TIER_1_SAFE" in r or "auto-learned globally" in r for r in allow_list
            ):
                allow_list.append("// === TIER_1_SAFE (auto-learned globally) ===")

            allow_list.extend(added)
            settings["permissions"]["allow"] = allow_list

            # Track what was learned
            if tier:
                tracking_key = (
                    "_cross_folder_learned"
                    if tier in ("CrossFolder", "CROSS_FOLDER")
                    else "_tier1_learned"
                )
                if tracking_key not in settings["permissions"]:
                    settings["permissions"][tracking_key] = []
                settings["permissions"][tracking_key].append(
                    {
                        "rules": added,
                        "source": source,
                        "added_at": datetime.now().isoformat(),
                    }
                )

            self.save_settings(settings)
            logger.info(f"Added {len(added)} global permissions: {added}")

        return added, skipped

    def is_covered_by_existing(
        self, rule: str, existing: set[str] | None = None
    ) -> bool:
        """
        Check if rule is already covered by broader pattern.

        Examples:
            - Bash(git status:*) is covered by Bash(git:*)
            - Bash(fd --type f:*) is covered by Bash(fd:*)

        Args:
            rule: The rule to check
            existing: Existing rules to check against (loads if None)

        Returns:
            True if the rule is covered by an existing broader pattern
        """
        if existing is None:
            existing = self.get_existing_permissions()

        # Extract tool name from Bash(tool ...) pattern
        bash_match = re.match(r"Bash\(([a-zA-Z0-9_-]+)", rule)
        if bash_match:
            tool_name = bash_match.group(1)
            # Check for tool:* wildcard
            if f"Bash({tool_name}:*)" in existing:
                return True
            # Check for tool * wildcard (older format)
            if f"Bash({tool_name} *)" in existing:
                return True

        # Check for Read/Write/Edit/Glob wildcards
        for op in ["Read", "Write", "Edit", "Glob"]:
            if rule.startswith(f"{op}("):
                # Check if /**) or **) wildcard exists
                if f"{op}(/**)" in existing or f"{op}(**)" in existing:
                    return True

        return False

    def create_backup(self) -> Path | None:
        """
        Create backup before modification.

        Returns:
            Path to backup file, or None if backup failed
        """
        if not self.settings_path.exists():
            return None

        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_filename = f"settings.json.backup-{timestamp}"
            backup_path = self.backup_dir / backup_filename

            shutil.copy2(self.settings_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

            # Cleanup old backups (keep last 10)
            self._cleanup_old_backups(keep_count=10)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """Remove old backups, keeping only the most recent."""
        try:
            backup_files = list(self.backup_dir.glob("settings.json.backup-*"))
            if len(backup_files) <= keep_count:
                return

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Remove excess backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

    def _backup_corrupted_file(self) -> None:
        """Backup corrupted settings file before overwriting."""
        if not self.settings_path.exists():
            return

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            corrupted_path = self.backup_dir / f"settings.json.corrupted-{timestamp}"
            shutil.copy2(self.settings_path, corrupted_path)
            logger.warning(f"Backed up corrupted settings to: {corrupted_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted file: {e}")

    def remove_permission(self, rule: str) -> bool:
        """
        Remove a specific permission rule.

        Args:
            rule: The rule to remove

        Returns:
            True if removed, False if not found
        """
        self.create_backup()
        settings = self.load_settings()
        allow_list = settings.get("permissions", {}).get("allow", [])

        if rule in allow_list:
            allow_list.remove(rule)
            settings["permissions"]["allow"] = allow_list
            self.save_settings(settings)
            logger.info(f"Removed global permission: {rule}")
            return True

        return False

    def get_tier1_learned(self) -> list[dict]:
        """Get list of TIER_1 patterns that were learned."""
        settings = self.load_settings()
        return settings.get("permissions", {}).get("_tier1_learned", [])

    def get_cross_folder_learned(self) -> list[dict]:
        """Get list of cross-folder patterns that were learned."""
        settings = self.load_settings()
        return settings.get("permissions", {}).get("_cross_folder_learned", [])

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about global permissions.

        Returns:
            Dictionary with permission statistics
        """
        settings = self.load_settings()
        permissions = settings.get("permissions", {})
        allow_list = permissions.get("allow", [])

        # Filter out comments
        actual_rules = [r for r in allow_list if not r.strip().startswith("//")]

        return {
            "total_rules": len(actual_rules),
            "tier1_learned_count": len(permissions.get("_tier1_learned", [])),
            "cross_folder_learned_count": len(
                permissions.get("_cross_folder_learned", [])
            ),
            "last_updated": permissions.get("_last_updated"),
            "settings_path": str(self.settings_path),
        }
