"""
Pytest configuration and shared fixtures for testing.
"""

from datetime import datetime

import pytest

from claude_automation.schemas import (
    CommandCategory,
    CommandUsage,
    FishAbbreviation,
    GitStatus,
    SlashCommand,
    ToolCategory,
    ToolInfo,
)


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with basic structure."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create basic project structure
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / "docs").mkdir()
    (project / ".git").mkdir()

    # Create marker files
    (project / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (project / "README.md").write_text("# Test Project\n")

    return project


@pytest.fixture
def tmp_fish_history(tmp_path):
    """Create a temporary Fish history file."""
    history_file = tmp_path / "fish_history"
    history_file.write_text(
        """- cmd: git status
  when: 1726160221
- cmd: cd /tmp
  when: 1726160222
- cmd: eza -la
  when: 1726160223
- cmd: bat README.md
  when: 1726160224
- cmd: git commit -m "test"
  when: 1726160225
"""
    )
    return history_file


@pytest.fixture
def sample_tool_info():
    """Sample ToolInfo object."""
    return ToolInfo(
        name="git",
        description="Version control system",
        category=ToolCategory.DEVELOPMENT,
        url="https://git-scm.com",
    )


@pytest.fixture
def sample_fish_abbr():
    """Sample FishAbbreviation object."""
    return FishAbbreviation(abbr="lg", command="eza -la --git")


@pytest.fixture
def sample_git_status():
    """Sample GitStatus object."""
    return GitStatus(modified=2, added=1, untracked=3)


@pytest.fixture
def sample_slash_command():
    """Sample SlashCommand object."""
    return SlashCommand(
        name="test-cmd",
        description="A test command",
        category=CommandCategory.TESTING,
        prompt="Run tests",
        requires_args=False,
        example_usage="/test-cmd",
    )


@pytest.fixture
def sample_command_usage():
    """Sample CommandUsage object."""
    return CommandUsage(
        command="git",
        count=97,
        last_used=datetime(2025, 10, 7, 12, 34),
        category="git",
    )
