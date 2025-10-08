"""
Integration smoke tests for each phase.
These tests verify end-to-end workflows work correctly.
"""

import pytest

from claude_automation.analyzers import (
    DirectoryAnalyzer,
    ProjectDetector,
    SystemAnalyzer,
    UsageTracker,
    WorkflowAnalyzer,
)
from claude_automation.generators import (
    DirectoryContextGenerator,
    LocalContextGenerator,
    PermissionsGenerator,
    SlashCommandsGenerator,
    UsageAnalyticsGenerator,
)
from claude_automation.schemas import ProjectType


class TestPhase1Integration:
    """Integration tests for Phase 1: Permissions Generator."""

    def test_permissions_end_to_end(self, tmp_project):
        """Test full permissions generation workflow."""
        # Create Python project markers
        (tmp_project / "pyproject.toml").write_text(
            """
[project]
name = "test"
"""
        )
        (tmp_project / "tests").mkdir(exist_ok=True)
        (tmp_project / "tests" / "test_example.py").write_text("def test_foo(): pass")

        # Detect project
        detector = ProjectDetector(tmp_project)
        project_type = detector.detect()
        assert project_type == ProjectType.PYTHON

        # Detect quality tools
        quality_tools = detector.detect_quality_tools()
        package_managers = detector.detect_package_managers()

        # Generate permissions
        from claude_automation.schemas import PermissionsConfig

        config = PermissionsConfig(
            project_path=tmp_project,
            project_type=project_type,
            username="testuser",
            quality_tools=quality_tools,
            package_managers=package_managers,
            has_tests=True,
        )

        generator = PermissionsGenerator()
        result = generator.generate(config)

        # Verify
        assert result.success
        settings_file = tmp_project / ".claude" / "settings.local.json"
        assert settings_file.exists()

        # Verify it's valid JSON
        import json

        settings = json.loads(settings_file.read_text())
        assert "permissions" in settings


class TestPhase2Integration:
    """Integration tests for Phase 2: Directory Context Generator."""

    def test_directory_context_end_to_end(self, tmp_project):
        """Test full directory context generation workflow."""
        # Create source directory with files
        src_dir = tmp_project / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "main.py").write_text("def main(): pass")
        (src_dir / "utils.py").write_text("def util(): pass")

        # Analyze directory
        analyzer = DirectoryAnalyzer(src_dir)
        config = analyzer.analyze()

        # Verify analysis
        assert config.directory_name == "src"
        assert config.file_count == 3
        assert "__init__.py" in config.key_files

        # Generate context
        generator = DirectoryContextGenerator()
        result = generator.generate(config)

        # Verify
        assert result.success
        claude_file = src_dir / "CLAUDE.md"
        assert claude_file.exists()

        content = claude_file.read_text()
        assert "src" in content
        assert "Source Code" in content or "Purpose" in content


class TestPhase3Integration:
    """Integration tests for Phase 3: Local Context Generator."""

    def test_local_context_end_to_end(self, tmp_project):
        """Test full local context generation workflow."""
        # Create .claude directory
        claude_dir = tmp_project / ".claude"
        claude_dir.mkdir()

        # Analyze system
        analyzer = SystemAnalyzer(tmp_project)
        config = analyzer.analyze()

        # Verify analysis
        assert config.hostname is not None
        assert len(config.hostname) > 0

        # Generate context
        generator = LocalContextGenerator()
        result = generator.generate(config)

        # Verify
        assert result.success
        local_file = tmp_project / ".claude" / "CLAUDE.local.md"
        assert local_file.exists()

        content = local_file.read_text()
        assert "Machine Information" in content
        assert config.hostname in content


class TestPhase4Integration:
    """Integration tests for Phase 4: Slash Commands Generator."""

    def test_slash_commands_end_to_end(self, tmp_project):
        """Test full slash commands generation workflow."""
        # Create git repository with commits
        git_dir = tmp_project / ".git"
        git_dir.mkdir(exist_ok=True)

        # Create simple git log output
        import subprocess

        try:
            subprocess.run(["git", "init"], cwd=tmp_project, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmp_project,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp_project,
                capture_output=True,
            )
            (tmp_project / "test.txt").write_text("test")
            subprocess.run(["git", "add", "."], cwd=tmp_project, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "fix: test bug"],
                cwd=tmp_project,
                capture_output=True,
            )
        except Exception:
            pytest.skip("Git not available")

        # Detect project type
        detector = ProjectDetector(tmp_project)
        project_type = detector.detect()

        # Analyze workflows
        analyzer = WorkflowAnalyzer(tmp_project, project_type)
        commands_dir = tmp_project / ".claude" / "commands"
        config = analyzer.analyze(commands_dir)

        # Generate commands
        generator = SlashCommandsGenerator()
        result = generator.generate(config)

        # Verify
        assert result.success
        assert commands_dir.exists()

        # Check at least one command was generated
        command_files = list(commands_dir.glob("*.md"))
        assert len(command_files) > 0

        # Verify command file format
        sample_cmd = command_files[0]
        content = sample_cmd.read_text()
        assert "Category" in content or "category" in content


class TestPhase6Integration:
    """Integration tests for Phase 6: Usage Analytics Generator."""

    def test_usage_analytics_end_to_end(self, tmp_project, tmp_fish_history):
        """Test full usage analytics generation workflow."""
        # Track usage
        tracker = UsageTracker(tmp_project)
        # Override history path for testing
        tracker.fish_history_path = tmp_fish_history
        config = tracker.analyze(top_n=5)

        # Verify analysis
        assert config.total_commands > 0
        assert len(config.command_stats) > 0

        # Generate analytics
        generator = UsageAnalyticsGenerator()
        result = generator.generate(config)

        # Verify
        assert result.success
        claude_file = tmp_project / "CLAUDE.md"
        assert claude_file.exists()

        content = claude_file.read_text()
        assert "Usage Analytics" in content
        assert "USAGE_ANALYTICS_START" in content
        assert "USAGE_ANALYTICS_END" in content

        # Test update (should replace, not duplicate)
        result2 = generator.generate(config)
        assert result2.success

        content2 = claude_file.read_text()
        # Should only have one start marker
        assert content2.count("USAGE_ANALYTICS_START") == 1


class TestCrossPhaseIntegration:
    """Tests that verify multiple phases work together."""

    def test_full_project_setup(self, tmp_project, tmp_fish_history):
        """Test setting up a full project with all generators."""
        # Setup Python project
        (tmp_project / "pyproject.toml").write_text("[project]\nname = 'test'")
        (tmp_project / "src").mkdir(exist_ok=True)
        (tmp_project / "src" / "__init__.py").write_text("")
        (tmp_project / "tests").mkdir(exist_ok=True)

        # Phase 1: Permissions
        detector = ProjectDetector(tmp_project)
        project_type = detector.detect()

        from claude_automation.schemas import PermissionsConfig

        perm_config = PermissionsConfig(
            project_path=tmp_project,
            project_type=project_type,
            username="testuser",
            has_tests=True,
        )
        perm_gen = PermissionsGenerator()
        perm_result = perm_gen.generate(perm_config)
        assert perm_result.success

        # Phase 2: Directory Context
        src_analyzer = DirectoryAnalyzer(tmp_project / "src")
        dir_config = src_analyzer.analyze()
        dir_gen = DirectoryContextGenerator()
        dir_result = dir_gen.generate(dir_config)
        assert dir_result.success

        # Phase 3: Local Context
        sys_analyzer = SystemAnalyzer(tmp_project)
        local_config = sys_analyzer.analyze()
        local_gen = LocalContextGenerator()
        local_result = local_gen.generate(local_config)
        assert local_result.success

        # Phase 6: Usage Analytics
        tracker = UsageTracker(tmp_project)
        tracker.fish_history_path = tmp_fish_history
        usage_config = tracker.analyze(top_n=3)
        usage_gen = UsageAnalyticsGenerator()
        usage_result = usage_gen.generate(usage_config)
        assert usage_result.success

        # Verify all files exist
        assert (tmp_project / ".claude" / "settings.local.json").exists()
        assert (tmp_project / "src" / "CLAUDE.md").exists()
        assert (tmp_project / ".claude" / "CLAUDE.local.md").exists()
        assert (tmp_project / "CLAUDE.md").exists()

    def test_idempotency(self, tmp_project, tmp_fish_history):
        """Test that generators are idempotent (can run multiple times)."""
        # Setup
        (tmp_project / "pyproject.toml").write_text("[project]\nname = 'test'")

        detector = ProjectDetector(tmp_project)
        project_type = detector.detect()

        # Generate permissions twice
        from claude_automation.schemas import PermissionsConfig

        config = PermissionsConfig(
            project_path=tmp_project,
            project_type=project_type,
            username="testuser",
        )

        gen = PermissionsGenerator()
        result1 = gen.generate(config)
        assert result1.success

        settings_file = tmp_project / ".claude" / "settings.local.json"
        content1 = settings_file.read_text()

        # Generate again
        result2 = gen.generate(config)
        assert result2.success

        content2 = settings_file.read_text()

        # Should produce similar output (may differ in timestamp)
        import json

        json1 = json.loads(content1)
        json2 = json.loads(content2)

        # Core structure should be identical
        assert json1.keys() == json2.keys()
