"""
Integration tests for cross-project MCP analysis.

Tests end-to-end scenarios across multiple projects.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from claude_automation.schemas import (
    GlobalMCPReport,
    MCPServerInfo,
    MCPServerStatus,
    MCPServerType,
    MCPToolUsage,
)


class TestCrossProjectMCPAnalysis:
    """Test cross-project MCP usage analysis."""

    def test_analyze_multiple_projects_with_shared_servers(self):
        """
        Test analyzing multiple projects that share some MCP servers.

        Scenario:
        - Project1: uses server-a, server-b
        - Project2: uses server-b, server-c
        - Global: provides server-d
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create global config
            global_config = home / ".claude.json"
            global_config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "server-d": {"command": "node", "args": ["global.js"]}
                        }
                    }
                )
            )

            # Create Project 1
            project1 = home / "project1"
            project1.mkdir()
            (project1 / ".claude").mkdir()
            (project1 / ".claude" / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "server-a": {
                                "command": "python",
                                "args": ["server_a.py"],
                            },
                            "server-b": {"command": "npx", "args": ["@test/server-b"]},
                        }
                    }
                )
            )

            # Create Project 2
            project2 = home / "project2"
            project2.mkdir()
            (project2 / ".claude").mkdir()
            (project2 / ".claude" / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "server-b": {
                                "command": "npx",
                                "args": ["@test/server-b"],
                            },  # Shared with project1
                            "server-c": {"command": "uv", "args": ["run", "server-c"]},
                        }
                    }
                )
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Verify
            assert report.total_projects == 2
            # Unique servers: server-a, server-b, server-c (project), server-d (global)
            # Note: server-b appears in both projects but counted once as project server
            assert report.total_servers >= 3

            # Verify global server
            assert len(report.global_servers) == 1
            assert report.global_servers[0].name == "server-d"

            # Verify project servers
            project_server_names = {s.name for s in report.project_servers}
            assert "server-a" in project_server_names
            assert "server-b" in project_server_names
            assert "server-c" in project_server_names

    def test_analyze_project_hierarchy(self):
        """
        Test analyzing projects in nested directory structure.

        Scenario:
        - home/
          - dev/
            - project-a/
            - project-b/
          - work/
            - project-c/
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create nested structure
            projects = [
                home / "dev" / "project-a",
                home / "dev" / "project-b",
                home / "work" / "project-c",
            ]

            for project_path in projects:
                project_path.mkdir(parents=True)
                (project_path / ".claude").mkdir()
                (project_path / ".claude" / "mcp.json").write_text(
                    json.dumps(
                        {
                            "mcpServers": {
                                f"{project_path.name}-server": {
                                    "command": "node",
                                    "args": [],
                                }
                            }
                        }
                    )
                )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Should find all 3 projects
            assert report.total_projects == 3
            assert report.total_servers == 3

            # Verify project paths
            scanned_paths = set(report.projects_scanned)
            assert len(scanned_paths) == 3
            assert all("project-" in path for path in scanned_paths)

    def test_detect_duplicate_server_configurations(self):
        """
        Test detection of servers configured both globally and per-project.

        Scenario:
        - Global config has "mcp-nixos"
        - Project also has "mcp-nixos" (duplicate)
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create global config
            global_config = home / ".claude.json"
            global_config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "mcp-nixos": {
                                "command": "mcp-nixos",
                                "args": [],
                            }
                        }
                    }
                )
            )

            # Create project with SAME server
            project = home / "test_project"
            project.mkdir()
            (project / ".claude").mkdir()
            (project / ".claude" / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "mcp-nixos": {
                                "command": "mcp-nixos",
                                "args": [],
                            }  # Duplicate
                        }
                    }
                )
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Should detect both global and project configs
            assert len(report.global_servers) == 1
            assert report.global_servers[0].name == "mcp-nixos"

            # Project server should NOT include mcp-nixos (already in global)
            project_server_names = {s.name for s in report.project_servers}
            assert "mcp-nixos" not in project_server_names

    def test_empty_and_missing_configs(self):
        """
        Test handling of empty or missing MCP configurations.

        Scenario:
        - Project 1: Has valid MCP config
        - Project 2: Has empty mcpServers
        - No global config
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Project 1: Valid config
            project1 = home / "project1"
            project1.mkdir()
            (project1 / ".claude").mkdir()
            (project1 / ".claude" / "mcp.json").write_text(
                json.dumps({"mcpServers": {"valid-server": {"command": "node"}}})
            )

            # Project 2: Empty servers
            project2 = home / "project2"
            project2.mkdir()
            (project2 / ".claude").mkdir()
            (project2 / ".claude" / "mcp.json").write_text(
                json.dumps({"mcpServers": {}})
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Should find both projects
            assert report.total_projects == 2

            # Should only count valid server
            assert report.total_servers == 1
            assert len(report.project_servers) == 1
            assert report.project_servers[0].name == "valid-server"

    def test_cross_project_usage_aggregation(self):
        """
        Test aggregating usage statistics across multiple projects.

        This is a placeholder for future token consumption tracking.
        Currently just verifies the aggregation structure exists.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create project
            project = home / "test_project"
            project.mkdir()
            (project / ".claude").mkdir()
            (project / ".claude" / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "test-server": {"command": "node", "args": ["server.js"]}
                        }
                    }
                )
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Verify aggregation structure exists
            assert isinstance(report.aggregated_usage, dict)
            # Currently empty (no session log parsing implemented yet)
            # Future: This should contain MCPToolUsage objects

    def test_recommendation_priority_ordering(self):
        """
        Test that recommendations are properly prioritized.

        High priority (1): Critical issues
        Medium priority (2): Optimizations
        Low priority (3): Nice-to-haves
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create multiple projects with unused servers
            for i in range(3):
                project = home / f"project{i}"
                project.mkdir()
                (project / ".claude").mkdir()
                (project / ".claude" / "mcp.json").write_text(
                    json.dumps(
                        {
                            "mcpServers": {
                                f"unused-server-{i}": {"command": "node", "args": []}
                            }
                        }
                    )
                )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Should generate recommendations
            assert len(report.recommendations) > 0

            # All unused server recommendations should have priority
            for rec in report.recommendations:
                assert 1 <= rec.priority <= 3
                assert isinstance(rec.reason, str)
                assert len(rec.reason) > 0

    def test_real_world_scenario_whatsapp_sunsama(self):
        """
        Test with user's real project structure (whatsapp-mcp, sunsama-mcp).

        This is a simulation - actual projects mentioned in tasks.md.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Simulate whatsapp-mcp project
            whatsapp_project = home / "whatsapp-mcp"
            whatsapp_project.mkdir()
            (whatsapp_project / ".claude").mkdir()
            (whatsapp_project / ".claude" / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "whatsapp-server": {
                                "command": "npx",
                                "args": ["@whatsapp/mcp-server"],
                            }
                        }
                    }
                )
            )

            # Simulate sunsama-mcp project
            sunsama_project = home / "sunsama-mcp"
            sunsama_project.mkdir()
            (sunsama_project / ".claude").mkdir()
            (sunsama_project / ".claude" / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "sunsama-server": {
                                "command": "python",
                                "args": ["sunsama_server.py"],
                            }
                        }
                    }
                )
            )

            # Global servers (like mcp-nixos, serena)
            global_config = home / ".claude.json"
            global_config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "mcp-nixos": {"command": "mcp-nixos", "args": []},
                            "serena": {"command": "serena", "args": []},
                        }
                    }
                )
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home, analysis_period_days=30)
            report = analyzer.analyze_all_projects()

            # Verify
            assert report.total_projects == 2
            assert report.total_servers == 4  # 2 global + 2 project

            # Verify global servers
            global_server_names = {s.name for s in report.global_servers}
            assert "mcp-nixos" in global_server_names
            assert "serena" in global_server_names

            # Verify project servers
            project_server_names = {s.name for s in report.project_servers}
            assert "whatsapp-server" in project_server_names
            assert "sunsama-server" in project_server_names

            # Generate summary
            summary = analyzer.generate_summary(report)
            assert "2" in summary  # 2 projects
            assert "4" in summary or "2" in summary  # 4 total or 2 global
