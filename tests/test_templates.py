"""
Tests for Jinja2 template rendering.
Ensures all templates render without syntax errors.
"""

from datetime import datetime
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

from claude_automation.schemas import (
    CommandUsage,
    DirectoryPurpose,
)


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment with template directory."""
    template_dir = Path(__file__).parent.parent / "claude_automation" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))

    # Add custom filters used in templates
    def status_icon(status_value):
        """Convert status value to icon."""
        icons = {
            "active": "✓",
            "unused": "✗",
            "low_value": "⚠",
            "misconfigured": "⚠",
        }
        return icons.get(status_value, "?")

    def priority_label(priority_num):
        """Convert priority number to label."""
        labels = {
            1: "HIGH PRIORITY",
            2: "MEDIUM PRIORITY",
            3: "LOW PRIORITY",
        }
        return labels.get(priority_num, "PRIORITY")

    env.filters["status_icon"] = status_icon
    env.filters["priority_label"] = priority_label
    return env


class TestDirectoryTemplates:
    """Tests for directory context templates."""

    @pytest.mark.parametrize(
        "template_name",
        [
            "directory/generic.j2",
            "directory/source_code.j2",
            "directory/tests.j2",
            "directory/documentation.j2",
            "directory/configuration.j2",
            "directory/modules.j2",
            "directory/scripts.j2",
            "directory/templates.j2",
            "directory/data.j2",
            "directory/build.j2",
        ],
    )
    def test_directory_template_renders(self, jinja_env, tmp_project, template_name):
        """All directory templates should render without errors."""
        template = jinja_env.get_template(template_name)

        context = {
            "directory_name": "test_dir",
            "purpose": DirectoryPurpose.SOURCE_CODE.value,
            "file_count": 10,
            "subdirectory_count": 3,
            "primary_file_types": [".py", ".txt", ".md"],
            "do_not_touch": ["__pycache__", "node_modules"],
            "key_files": ["__init__.py", "main.py"],
            "description": "Test directory description",
            "timestamp": datetime.now(),
        }

        result = template.render(**context)

        # Basic checks
        assert len(result) > 0
        assert "test_dir" in result
        assert "CLAUDE.md" in result or "purpose" in result.lower()

    def test_directory_template_handles_empty_lists(self, jinja_env, tmp_project):
        """Directory templates should handle empty lists gracefully."""
        template = jinja_env.get_template("directory/generic.j2")

        context = {
            "directory_name": "empty_dir",
            "purpose": DirectoryPurpose.UNKNOWN.value,
            "file_count": 0,
            "subdirectory_count": 0,
            "primary_file_types": [],  # Empty
            "do_not_touch": [],  # Empty
            "key_files": [],  # Empty
            "description": "",
            "timestamp": datetime.now(),
        }

        result = template.render(**context)
        assert len(result) > 0


class TestLocalContextTemplate:
    """Tests for local context template."""

    def test_local_context_renders(self, jinja_env):
        """Local context template should render without errors."""
        template = jinja_env.get_template("local_context.j2")

        context = {
            "hostname": "testhost",
            "cpu_info": "Intel Core i7",
            "memory_total": "16GB",
            "disk_usage": "100G / 500G",
            "project_path": "/home/user/project",
            "running_services": ["Docker", "PostgreSQL"],
            "current_branches": ["main", "feature/test"],
            "wip_notes": ["Working on feature X", "Debugging issue Y"],
            "experiments": ["Testing new caching strategy"],
            "timestamp": datetime.now(),
        }

        result = template.render(**context)

        # Verify content
        assert "testhost" in result
        assert "Intel Core i7" in result
        assert "Docker" in result
        assert "main" in result

    def test_local_context_empty_lists(self, jinja_env):
        """Local context should handle empty services/branches/notes."""
        template = jinja_env.get_template("local_context.j2")

        context = {
            "hostname": "testhost",
            "cpu_info": "Intel Core i7",
            "memory_total": "16GB",
            "disk_usage": "100G / 500G",
            "project_path": "/home/user/project",
            "running_services": [],
            "current_branches": [],
            "wip_notes": [],
            "experiments": [],
            "timestamp": datetime.now(),
        }

        result = template.render(**context)
        assert len(result) > 0


class TestUsageAnalyticsTemplate:
    """Tests for usage analytics template."""

    def test_usage_analytics_renders(self, jinja_env):
        """Usage analytics template should render without errors."""
        template = jinja_env.get_template("usage_analytics.j2")

        context = {
            "total_commands": 883,
            "unique_commands": 223,
            "top_commands": ["cd", "git", "rm", "cat", "eza"],
            "command_stats": {
                "cd": CommandUsage(
                    command="cd",
                    count=111,
                    last_used=datetime.now(),
                    category="file_operations",
                ),
                "git": CommandUsage(
                    command="git", count=97, last_used=datetime.now(), category="git"
                ),
                "rm": CommandUsage(
                    command="rm",
                    count=44,
                    last_used=datetime.now(),
                    category="file_operations",
                ),
                "cat": CommandUsage(
                    command="cat",
                    count=32,
                    last_used=datetime.now(),
                    category="file_operations",
                ),
                "eza": CommandUsage(
                    command="eza",
                    count=19,
                    last_used=datetime.now(),
                    category="file_operations",
                ),
            },
            "tool_usage": {"git": 97, "eza": 19, "bat": 6},
            "workflow_patterns": ["Heavy git user", "Modern CLI tools adoption"],
            "timestamp": datetime.now(),
            "start_marker": "<!-- USAGE_ANALYTICS_START -->",
            "end_marker": "<!-- USAGE_ANALYTICS_END -->",
        }

        result = template.render(**context)

        # Verify content
        assert "883" in result
        assert "223" in result
        assert "cd" in result
        assert "git" in result
        assert "Heavy git user" in result
        assert "<!-- USAGE_ANALYTICS_START -->" in result
        assert "<!-- USAGE_ANALYTICS_END -->" in result

    def test_usage_analytics_empty_data(self, jinja_env):
        """Usage analytics should handle empty data gracefully."""
        template = jinja_env.get_template("usage_analytics.j2")

        context = {
            "total_commands": 0,
            "unique_commands": 0,
            "top_commands": [],
            "command_stats": {},
            "tool_usage": {},
            "workflow_patterns": [],
            "timestamp": datetime.now(),
            "start_marker": "<!-- USAGE_ANALYTICS_START -->",
            "end_marker": "<!-- USAGE_ANALYTICS_END -->",
        }

        result = template.render(**context)
        assert len(result) > 0
        assert (
            "No modern CLI tools tracked" in result or "No specific workflow" in result
        )


class TestPermissionsTemplates:
    """Tests for permissions templates."""

    @pytest.mark.parametrize(
        "template_name",
        [
            "permissions/base.j2",
            "permissions/python.j2",
            "permissions/nodejs.j2",
            "permissions/rust.j2",
            "permissions/nixos.j2",
        ],
    )
    def test_permissions_template_renders(self, jinja_env, template_name):
        """All permissions templates should render without errors."""
        template = jinja_env.get_template(template_name)

        context = {
            "project_path": "/home/user/project",
            "username": "testuser",
            "quality_tools": ["ruff", "black", "pytest"],
            "package_managers": ["uv", "pip"],
            "sensitive_paths": [".env", "secrets/"],
            "modern_cli_tools": ["eza", "bat", "rg", "fd"],
            "has_tests": True,
            "timestamp": datetime.now(),
        }

        result = template.render(**context)

        # Basic checks
        assert len(result) > 0
        # Should contain JSON structure
        assert "{" in result
        assert "}" in result
        # Should contain some permissions
        assert "Bash" in result or "Read" in result

    def test_permissions_template_no_tools(self, jinja_env):
        """Permissions templates should handle empty tool lists."""
        template = jinja_env.get_template("permissions/base.j2")

        context = {
            "project_path": "/home/user/project",
            "username": "testuser",
            "quality_tools": [],
            "package_managers": [],
            "sensitive_paths": [],
            "modern_cli_tools": [],
            "has_tests": False,
            "timestamp": datetime.now(),
        }

        result = template.render(**context)
        assert len(result) > 0


class TestTemplateEdgeCases:
    """Tests for template edge cases and error handling."""

    def test_all_templates_load(self, jinja_env):
        """All templates should load without syntax errors."""
        template_dir = Path(__file__).parent.parent / "claude_automation" / "templates"

        # Collect all .j2 files
        template_files = list(template_dir.rglob("*.j2"))

        assert len(template_files) > 0, "No template files found"

        # Try to get each template (will raise if syntax error)
        for template_file in template_files:
            rel_path = template_file.relative_to(template_dir)
            template = jinja_env.get_template(str(rel_path))
            assert template is not None

    def test_templates_handle_none_values(self, jinja_env):
        """Templates should handle None values gracefully."""
        template = jinja_env.get_template("local_context.j2")

        context = {
            "hostname": "testhost",
            "cpu_info": None,  # None value
            "memory_total": None,  # None value
            "disk_usage": None,  # None value
            "project_path": "/test",
            "running_services": [],
            "current_branches": [],
            "wip_notes": [],
            "experiments": [],
            "timestamp": datetime.now(),
        }

        # Should not raise
        result = template.render(**context)
        assert len(result) > 0
