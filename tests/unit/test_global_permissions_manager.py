"""
Unit tests for GlobalPermissionsManager.

Tests global settings management for TIER_1_SAFE permissions.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_automation.generators.global_permissions_manager import (
    GlobalPermissionsManager,
)


@pytest.fixture
def temp_home():
    """Create temporary home directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        home = Path(tmpdir)
        claude_dir = home / ".claude"
        claude_dir.mkdir(parents=True)
        yield home


@pytest.fixture
def manager(temp_home):
    """Create GlobalPermissionsManager with temporary home."""
    with patch.object(GlobalPermissionsManager, "GLOBAL_SETTINGS_PATH", temp_home / ".claude" / "settings.json"):
        with patch.object(GlobalPermissionsManager, "BACKUP_DIR", temp_home / ".claude" / ".backups"):
            yield GlobalPermissionsManager()


class TestLoadSettings:
    """Test settings loading functionality."""

    def test_load_nonexistent_creates_structure(self, manager):
        """Verify loading non-existent file creates proper structure."""
        settings = manager.load_settings()

        assert "permissions" in settings
        assert "allow" in settings["permissions"]
        assert isinstance(settings["permissions"]["allow"], list)

    def test_load_existing_preserves_structure(self, manager, temp_home):
        """Verify loading existing file preserves all fields."""
        # Create existing settings
        existing = {
            "permissions": {
                "allow": ["Bash(git status:*)"],
                "deny": ["Bash(rm -rf:*)"],
            },
            "hooks": {"PreToolUse": []},
            "customField": "preserved",
        }
        with open(manager.GLOBAL_SETTINGS_PATH, "w") as f:
            json.dump(existing, f)

        # Load and verify
        settings = manager.load_settings()

        assert settings["customField"] == "preserved"
        assert "Bash(git status:*)" in settings["permissions"]["allow"]
        assert "Bash(rm -rf:*)" in settings["permissions"]["deny"]
        assert "hooks" in settings

    def test_load_invalid_json_returns_default(self, manager, temp_home):
        """Verify invalid JSON returns default structure."""
        with open(manager.GLOBAL_SETTINGS_PATH, "w") as f:
            f.write("invalid json {{{")

        settings = manager.load_settings()

        assert "permissions" in settings
        assert "allow" in settings["permissions"]


class TestAddPermissions:
    """Test permission addition functionality."""

    def test_add_new_permission(self, manager):
        """Verify adding new permission rule."""
        added, skipped = manager.add_permissions(["Bash(git status:*)"])

        assert "Bash(git status:*)" in added
        assert len(skipped) == 0

        # Verify saved
        settings = manager.load_settings()
        assert "Bash(git status:*)" in settings["permissions"]["allow"]

    def test_add_duplicate_skipped(self, manager):
        """Verify duplicate rules are skipped."""
        # Add first time
        manager.add_permissions(["Bash(git status:*)"])

        # Try to add again
        added, skipped = manager.add_permissions(["Bash(git status:*)"])

        assert len(added) == 0
        assert "Bash(git status:*)" in skipped

    def test_add_multiple_permissions(self, manager):
        """Verify adding multiple permissions at once."""
        rules = ["Bash(git status:*)", "Bash(fd:*)", "Bash(bat:*)"]
        added, skipped = manager.add_permissions(rules)

        assert len(added) == 3
        assert len(skipped) == 0

        settings = manager.load_settings()
        for rule in rules:
            assert rule in settings["permissions"]["allow"]

    def test_add_with_source_tracking(self, manager):
        """Verify source and tier metadata is tracked."""
        manager.add_permissions(
            ["Bash(pytest:*)"],
            source="auto-learned",
            tier="TIER_1_SAFE",
        )

        settings = manager.load_settings()
        tier1_learned = settings["permissions"].get("_tier1_learned", [])
        assert len(tier1_learned) > 0
        # Check structure: list of objects with rules, source, added_at
        assert "rules" in tier1_learned[0]
        assert "source" in tier1_learned[0]
        assert "Bash(pytest:*)" in tier1_learned[0]["rules"]
        assert settings["permissions"].get("_last_updated") is not None

    def test_add_preserves_existing_rules(self, manager):
        """Verify existing rules are preserved when adding new ones."""
        # Add first batch
        manager.add_permissions(["Bash(git status:*)"])

        # Add second batch
        manager.add_permissions(["Bash(fd:*)"])

        settings = manager.load_settings()
        assert "Bash(git status:*)" in settings["permissions"]["allow"]
        assert "Bash(fd:*)" in settings["permissions"]["allow"]


class TestWildcardCoverage:
    """Test wildcard pattern coverage detection."""

    def test_covered_by_broader_pattern(self, manager):
        """Verify specific command covered by wildcard."""
        manager.add_permissions(["Bash(git:*)"])

        assert manager.is_covered_by_existing("Bash(git status:*)")
        assert manager.is_covered_by_existing("Bash(git log:*)")
        assert manager.is_covered_by_existing("Bash(git diff:*)")

    def test_not_covered_by_different_tool(self, manager):
        """Verify different tools are not covered."""
        manager.add_permissions(["Bash(git:*)"])

        assert not manager.is_covered_by_existing("Bash(fd:*)")
        assert not manager.is_covered_by_existing("Bash(rg:*)")

    def test_exact_match_skipped_on_add(self, manager):
        """Verify exact match is skipped when adding (detected in add_permissions)."""
        # Add first time
        manager.add_permissions(["Bash(git status:*)"])

        # Try to add same rule - should be skipped
        added, skipped = manager.add_permissions(["Bash(git status:*)"])
        assert len(added) == 0
        assert "Bash(git status:*)" in skipped

    def test_tool_operations_covered(self, manager):
        """Verify tool operations like Read, Edit are handled."""
        manager.add_permissions(["Read(/**)"])

        # Read with any path should be covered
        assert manager.is_covered_by_existing("Read(/home/user/file.txt)")

    def test_skip_covered_rules_on_add(self, manager):
        """Verify adding covered rules skips them."""
        # Add broad pattern first
        manager.add_permissions(["Bash(git:*)"])

        # Try to add specific pattern
        added, skipped = manager.add_permissions(["Bash(git status:*)"])

        assert len(added) == 0
        assert "Bash(git status:*)" in skipped


class TestBackup:
    """Test backup functionality."""

    def test_create_backup(self, manager):
        """Verify backup creation."""
        # Create initial settings
        manager.add_permissions(["Bash(git status:*)"])

        # Create backup
        backup_path = manager.create_backup()

        assert backup_path.exists()
        assert "settings.json.backup" in backup_path.name

        # Verify backup content
        with open(backup_path) as f:
            backup = json.load(f)
        assert "Bash(git status:*)" in backup["permissions"]["allow"]

    def test_backup_directory_created(self, manager):
        """Verify backup directory is created if missing."""
        # First add some content so there's something to backup
        manager.add_permissions(["Bash(test:*)"])

        backup_path = manager.create_backup()

        # Manager uses self.backup_dir (instance attribute)
        assert manager.backup_dir.exists()
        assert backup_path.parent == manager.backup_dir


class TestMetadataTracking:
    """Test metadata tracking for learned patterns."""

    def test_tier1_learned_tracking(self, manager):
        """Verify TIER_1_SAFE pattern types are tracked."""
        manager.add_permissions(
            ["Bash(git status:*)"],
            source="auto-learned",
            tier="TIER_1_SAFE",
        )

        settings = manager.load_settings()
        learned = settings["permissions"].get("_tier1_learned", [])
        assert len(learned) > 0

    def test_cross_folder_tracking(self, manager):
        """Verify cross-folder patterns are tracked separately."""
        # Implementation checks for tier == "CrossFolder" not "CROSS_FOLDER"
        manager.add_permissions(
            ["Bash(curl:*)"],
            source="cross-folder",
            tier="CrossFolder",
        )

        settings = manager.load_settings()
        cross_folder = settings["permissions"].get("_cross_folder_learned", [])
        assert len(cross_folder) > 0
        assert "Bash(curl:*)" in cross_folder[0]["rules"]

    def test_last_updated_timestamp(self, manager):
        """Verify last updated timestamp is set."""
        manager.add_permissions(["Bash(fd:*)"])

        settings = manager.load_settings()
        assert "_last_updated" in settings["permissions"]

        # Parse timestamp to verify format
        timestamp = settings["permissions"]["_last_updated"]
        datetime.fromisoformat(timestamp)  # Should not raise


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_rules_list(self, manager):
        """Verify empty rules list is handled."""
        added, skipped = manager.add_permissions([])

        assert len(added) == 0
        assert len(skipped) == 0

    def test_comment_rules_preserved(self, manager, temp_home):
        """Verify comment rules are preserved."""
        # Create settings with comments
        existing = {
            "permissions": {
                "allow": [
                    "// === TIER_1_SAFE ===",
                    "Bash(git status:*)",
                ],
            },
        }
        with open(manager.GLOBAL_SETTINGS_PATH, "w") as f:
            json.dump(existing, f)

        # Add new rule
        manager.add_permissions(["Bash(fd:*)"])

        settings = manager.load_settings()
        assert "// === TIER_1_SAFE ===" in settings["permissions"]["allow"]
        assert "Bash(fd:*)" in settings["permissions"]["allow"]

    def test_concurrent_access_safe(self, manager):
        """Verify multiple adds don't corrupt settings."""
        rules1 = ["Bash(git status:*)", "Bash(fd:*)"]
        rules2 = ["Bash(rg:*)", "Bash(bat:*)"]

        # Simulate concurrent adds
        manager.add_permissions(rules1)
        manager.add_permissions(rules2)

        settings = manager.load_settings()
        for rule in rules1 + rules2:
            assert rule in settings["permissions"]["allow"]


class TestIntegration:
    """Integration tests with real-world scenarios."""

    def test_full_tier1_migration_workflow(self, manager):
        """Test complete TIER_1_SAFE migration workflow."""
        # Phase 1: Add read-only git commands
        git_rules = [
            "Bash(git status:*)",
            "Bash(git log:*)",
            "Bash(git diff:*)",
        ]
        added1, _ = manager.add_permissions(git_rules, tier="TIER_1_SAFE")
        assert len(added1) == 3

        # Phase 2: Add modern CLI tools
        cli_rules = ["Bash(fd:*)", "Bash(rg:*)", "Bash(bat:*)"]
        added2, _ = manager.add_permissions(cli_rules, tier="TIER_1_SAFE")
        assert len(added2) == 3

        # Phase 3: Try to add duplicate (should skip)
        added3, skipped = manager.add_permissions(["Bash(git status:*)"])
        assert len(added3) == 0
        assert len(skipped) == 1

        # Verify final state
        settings = manager.load_settings()
        total_rules = [r for r in settings["permissions"]["allow"] if not r.startswith("//")]
        assert len(total_rules) == 6

    def test_cross_folder_promotion(self, manager):
        """Test cross-folder pattern promotion to global."""
        # Simulate cross-folder detection
        cross_folder_rules = ["Bash(httpie:*)", "Bash(curl:*)"]

        # Implementation checks for tier == "CrossFolder" not "CROSS_FOLDER"
        manager.add_permissions(
            cross_folder_rules,
            source="cross-folder",
            tier="CrossFolder",
        )

        settings = manager.load_settings()
        cross_learned = settings["permissions"].get("_cross_folder_learned", [])
        assert len(cross_learned) > 0

        # Rules should be in allow list
        for rule in cross_folder_rules:
            assert rule in settings["permissions"]["allow"]
