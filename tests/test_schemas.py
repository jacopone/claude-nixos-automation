"""
Tests for Pydantic schemas and validation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from claude_automation.schemas import (
    CommandCategory,
    CommandUsage,
    DirectoryContextConfig,
    DirectoryPurpose,
    FishAbbreviation,
    GitStatus,
    LocalContextConfig,
    PermissionsConfig,
    ProjectType,
    SlashCommand,
    SlashCommandsConfig,
    ToolCategory,
    ToolInfo,
    UsageAnalyticsConfig,
)


class TestToolInfo:
    """Tests for ToolInfo schema."""

    def test_valid_tool_info(self, sample_tool_info):
        """Valid ToolInfo should validate."""
        assert sample_tool_info.name == "git"
        assert sample_tool_info.category == ToolCategory.DEVELOPMENT

    def test_invalid_name(self):
        """Invalid tool name should raise ValidationError."""
        with pytest.raises(ValidationError):
            ToolInfo(
                name="",  # Empty name
                description="Test",
                category=ToolCategory.DEVELOPMENT,
            )

    def test_invalid_url(self):
        """Invalid URL should raise ValidationError."""
        with pytest.raises(ValidationError):
            ToolInfo(
                name="test",
                description="Test",
                category=ToolCategory.DEVELOPMENT,
                url="not-a-url",  # Missing http://
            )

    def test_short_description(self):
        """Short description should raise ValidationError."""
        with pytest.raises(ValidationError):
            ToolInfo(
                name="test",
                description="ab",
                category=ToolCategory.DEVELOPMENT,  # Too short
            )


class TestFishAbbreviation:
    """Tests for FishAbbreviation schema."""

    def test_valid_abbreviation(self, sample_fish_abbr):
        """Valid FishAbbreviation should validate."""
        assert sample_fish_abbr.abbr == "lg"
        assert sample_fish_abbr.command == "eza -la --git"

    def test_invalid_abbreviation(self):
        """Invalid abbreviation format should raise ValidationError."""
        with pytest.raises(ValidationError):
            FishAbbreviation(abbr="invalid-abbr", command="test")  # Contains hyphen


class TestGitStatus:
    """Tests for GitStatus schema."""

    def test_status_string(self, sample_git_status):
        """GitStatus should format status string correctly."""
        assert sample_git_status.status_string == "2M 1A 3U"

    def test_clean_status(self):
        """Clean GitStatus should show 'clean'."""
        clean = GitStatus(modified=0, added=0, untracked=0)
        assert clean.status_string == "clean"

    def test_from_string(self):
        """GitStatus.from_string should parse correctly."""
        status = GitStatus.from_string("2M 1A 3U")
        assert status.modified == 2
        assert status.added == 1
        assert status.untracked == 3

    def test_from_string_clean(self):
        """GitStatus.from_string should handle 'clean'."""
        status = GitStatus.from_string("clean")
        assert status.modified == 0
        assert status.added == 0
        assert status.untracked == 0

    def test_negative_values(self):
        """Negative values should raise ValidationError."""
        with pytest.raises(ValidationError):
            GitStatus(modified=-1, added=0, untracked=0)


class TestSlashCommand:
    """Tests for SlashCommand schema."""

    def test_valid_command(self, sample_slash_command):
        """Valid SlashCommand should validate."""
        assert sample_slash_command.name == "test-cmd"
        assert sample_slash_command.category == CommandCategory.TESTING

    def test_name_normalization(self):
        """Command name should be lowercased."""
        cmd = SlashCommand(
            name="TEST-CMD",
            description="Test",
            category=CommandCategory.TESTING,
            prompt="Test",
        )
        assert cmd.name == "test-cmd"

    def test_invalid_name(self):
        """Invalid command name should raise ValidationError."""
        with pytest.raises(ValidationError):
            SlashCommand(
                name="invalid name!",  # Contains space and special char
                description="Test",
                category=CommandCategory.TESTING,
                prompt="Test",
            )


class TestCommandUsage:
    """Tests for CommandUsage schema."""

    def test_valid_usage(self, sample_command_usage):
        """Valid CommandUsage should validate."""
        assert sample_command_usage.command == "git"
        assert sample_command_usage.count == 97

    def test_zero_count(self):
        """Zero count should raise ValidationError."""
        with pytest.raises(ValidationError):
            CommandUsage(
                command="git",
                count=0,
                last_used=datetime.now(),
                category="git",  # Must be >= 1
            )

    def test_empty_command(self):
        """Empty command should raise ValidationError."""
        with pytest.raises(ValidationError):
            CommandUsage(
                command="", count=1, last_used=datetime.now(), category="unknown"
            )


class TestDirectoryContextConfig:
    """Tests for DirectoryContextConfig schema."""

    def test_valid_config(self, tmp_project):
        """Valid DirectoryContextConfig should validate."""
        config = DirectoryContextConfig(
            directory_path=tmp_project,
            directory_name="test_project",
            purpose=DirectoryPurpose.SOURCE_CODE,
            file_count=5,
            subdirectory_count=2,
        )
        assert config.directory_path == tmp_project
        assert config.claude_file == tmp_project / "CLAUDE.md"

    def test_nonexistent_directory(self, tmp_path):
        """Nonexistent directory should raise ValidationError."""
        with pytest.raises(ValidationError):
            DirectoryContextConfig(
                directory_path=tmp_path / "nonexistent",
                directory_name="test",
                purpose=DirectoryPurpose.SOURCE_CODE,
            )

    def test_file_not_directory(self, tmp_path):
        """File path (not directory) should raise ValidationError."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("test")

        with pytest.raises(ValidationError):
            DirectoryContextConfig(
                directory_path=test_file,
                directory_name="test",
                purpose=DirectoryPurpose.SOURCE_CODE,
            )


class TestLocalContextConfig:
    """Tests for LocalContextConfig schema."""

    def test_valid_config(self, tmp_project):
        """Valid LocalContextConfig should validate."""
        config = LocalContextConfig(
            project_path=tmp_project,
            hostname="testhost",
            cpu_info="Test CPU",
            memory_total="16GB",
        )
        assert config.project_path == tmp_project
        assert config.local_claude_file == tmp_project / ".claude" / "CLAUDE.local.md"

    def test_nonexistent_project(self, tmp_path):
        """Nonexistent project should raise ValidationError."""
        with pytest.raises(ValidationError):
            LocalContextConfig(project_path=tmp_path / "nonexistent", hostname="test")


class TestPermissionsConfig:
    """Tests for PermissionsConfig schema."""

    def test_valid_config(self, tmp_project):
        """Valid PermissionsConfig should validate."""
        config = PermissionsConfig(
            project_path=tmp_project,
            project_type=ProjectType.PYTHON,
            username="testuser",
        )
        assert config.project_path == tmp_project
        assert config.settings_file == tmp_project / ".claude" / "settings.local.json"

    def test_empty_username(self, tmp_project):
        """Empty username should raise ValidationError."""
        with pytest.raises(ValidationError):
            PermissionsConfig(
                project_path=tmp_project, project_type=ProjectType.PYTHON, username=""
            )


class TestSlashCommandsConfig:
    """Tests for SlashCommandsConfig schema."""

    def test_valid_config(self, tmp_path, sample_slash_command):
        """Valid SlashCommandsConfig should validate."""
        config = SlashCommandsConfig(
            commands_dir=tmp_path / "commands",
            project_type=ProjectType.PYTHON,
            commands=[sample_slash_command],
        )
        # Validator should create the directory
        assert config.commands_dir.exists()

    def test_creates_directory(self, tmp_path, sample_slash_command):
        """Validator should create commands_dir if it doesn't exist."""
        commands_dir = tmp_path / "new_commands"
        assert not commands_dir.exists()

        config = SlashCommandsConfig(
            commands_dir=commands_dir,
            project_type=ProjectType.PYTHON,
            commands=[sample_slash_command],
        )

        assert config.commands_dir.exists()


class TestUsageAnalyticsConfig:
    """Tests for UsageAnalyticsConfig schema."""

    def test_valid_config(self, tmp_project, tmp_fish_history):
        """Valid UsageAnalyticsConfig should validate."""
        config = UsageAnalyticsConfig(
            project_path=tmp_project, fish_history_path=tmp_fish_history
        )
        assert config.project_path == tmp_project
        assert config.claude_file == tmp_project / "CLAUDE.md"

    def test_unique_commands_property(self, tmp_project, tmp_fish_history):
        """unique_commands property should count command_stats."""
        config = UsageAnalyticsConfig(
            project_path=tmp_project,
            fish_history_path=tmp_fish_history,
            command_stats={
                "git": CommandUsage(
                    command="git", count=10, last_used=datetime.now(), category="git"
                ),
                "cd": CommandUsage(
                    command="cd",
                    count=20,
                    last_used=datetime.now(),
                    category="file_operations",
                ),
            },
        )
        assert config.unique_commands == 2

    def test_nonexistent_history(self, tmp_project, tmp_path):
        """Nonexistent Fish history should raise ValidationError."""
        with pytest.raises(ValidationError):
            UsageAnalyticsConfig(
                project_path=tmp_project,
                fish_history_path=tmp_path / "nonexistent_history",
            )
