"""
Unit tests for GlobalMCPAnalyzer.

Tests global MCP discovery, usage aggregation, and recommendation generation.
"""

import json
import tempfile
from pathlib import Path

from claude_automation.analyzers import GlobalMCPAnalyzer
from claude_automation.schemas import (
    GlobalMCPReport,
    MCPServerInfo,
    MCPServerStatus,
    MCPServerType,
    MCPToolUsage,
    MCPUsageRecommendation,
)


class TestGlobalMCPDiscovery:
    """Test global MCP project discovery."""

    def test_discover_projects_finds_all_configs(self):
        """Test that discover_projects finds all .claude/mcp.json files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create multiple projects with MCP configs
            projects = ["project1", "project2", "subdir/project3"]
            for project in projects:
                project_path = home / project
                project_path.mkdir(parents=True, exist_ok=True)
                claude_dir = project_path / ".claude"
                claude_dir.mkdir(exist_ok=True)
                mcp_config = claude_dir / "mcp.json"
                mcp_config.write_text(
                    json.dumps({"mcpServers": {"test-server": {"command": "node"}}})
                )

            # Discover projects
            analyzer = GlobalMCPAnalyzer(home)
            discovered = analyzer.discover_projects()

            # Should find all 3 projects
            assert len(discovered) == 3
            assert all(isinstance(p, Path) for p in discovered)

    def test_discover_projects_skips_hidden_directories(self):
        """Test that hidden directories (except .claude) are skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Valid project
            valid_project = home / "valid_project"
            valid_project.mkdir()
            (valid_project / ".claude").mkdir()
            (valid_project / ".claude" / "mcp.json").write_text(
                json.dumps({"mcpServers": {}})
            )

            # Invalid: project inside .hidden directory
            hidden_dir = home / ".hidden"
            hidden_dir.mkdir()
            hidden_project = hidden_dir / "project"
            hidden_project.mkdir()
            (hidden_project / ".claude").mkdir()
            (hidden_project / ".claude" / "mcp.json").write_text(
                json.dumps({"mcpServers": {}})
            )

            analyzer = GlobalMCPAnalyzer(home)
            discovered = analyzer.discover_projects()

            # Should only find valid project
            assert len(discovered) == 1
            assert discovered[0] == valid_project

    def test_discover_projects_handles_empty_home(self):
        """Test that discover_projects handles empty home directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            analyzer = GlobalMCPAnalyzer(home)
            discovered = analyzer.discover_projects()

            assert len(discovered) == 0
            assert isinstance(discovered, list)


class TestGlobalUsageAggregation:
    """Test usage aggregation across projects."""

    def test_analyze_all_projects_aggregates_data(self):
        """Test that analyze_all_projects aggregates data correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create project with MCP config
            project = home / "test_project"
            project.mkdir()
            claude_dir = project / ".claude"
            claude_dir.mkdir()
            mcp_config = claude_dir / "mcp.json"
            mcp_config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "server1": {"command": "npx", "args": ["@test/server1"]},
                            "server2": {"command": "python", "args": ["server2.py"]},
                        }
                    }
                )
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            # Verify report structure
            assert isinstance(report, GlobalMCPReport)
            assert report.total_projects == 1
            assert report.total_servers == 2

    def test_analyze_global_config(self):
        """Test that global MCP config is analyzed correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create global config
            global_config = home / ".claude.json"
            global_config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "global-server": {
                                "command": "node",
                                "args": ["global-server.js"],
                            }
                        }
                    }
                )
            )

            analyzer = GlobalMCPAnalyzer(home)
            analyzer._analyze_global_config()

            # Should have 1 global server
            assert len(analyzer.global_servers) == 1
            assert "global-server" in analyzer.global_servers

            server = analyzer.global_servers["global-server"]
            assert isinstance(server, MCPServerInfo)
            assert server.name == "global-server"
            assert server.type == MCPServerType.NPM
            assert server.config_location == "global (~/.claude.json)"

    def test_detect_server_type(self):
        """Test that server types are detected correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            analyzer = GlobalMCPAnalyzer(home)

            # NPM server
            assert analyzer._detect_server_type({"command": "npx"}) == MCPServerType.NPM
            assert (
                analyzer._detect_server_type({"command": "node"}) == MCPServerType.NPM
            )

            # Python server
            assert (
                analyzer._detect_server_type({"command": "python"})
                == MCPServerType.PYTHON
            )
            assert (
                analyzer._detect_server_type({"command": "uv"}) == MCPServerType.PYTHON
            )

            # Binary server
            assert (
                analyzer._detect_server_type({"command": "/usr/bin/server"})
                == MCPServerType.BINARY
            )
            assert (
                analyzer._detect_server_type({"command": "./local-server"})
                == MCPServerType.BINARY
            )

            # Unknown
            assert (
                analyzer._detect_server_type({"command": "unknown"})
                == MCPServerType.UNKNOWN
            )


class TestUnderutilizedDetection:
    """Test detection of underutilized MCP servers."""

    def test_generate_recommendations_unused_servers(self):
        """Test that unused servers generate removal recommendations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create project with MCP config
            project = home / "test_project"
            project.mkdir()
            claude_dir = project / ".claude"
            claude_dir.mkdir()
            mcp_config = claude_dir / "mcp.json"
            mcp_config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "unused-server": {"command": "node", "args": ["server.js"]}
                        }
                    }
                )
            )

            # Analyze
            analyzer = GlobalMCPAnalyzer(home)
            analyzer.projects = analyzer.discover_projects()
            analyzer._analyze_project(project)

            # Generate recommendations (no usage data = unused)
            analyzer._generate_recommendations()

            # Should recommend removal
            assert len(analyzer.recommendations) > 0
            assert any(
                r.recommendation_type == "remove_unused"
                for r in analyzer.recommendations
            )
            assert any(
                r.server_name == "unused-server" for r in analyzer.recommendations
            )

    def test_generate_recommendations_skips_global_servers(self):
        """Test that global servers are not recommended for removal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create global config
            global_config = home / ".claude.json"
            global_config.write_text(
                json.dumps(
                    {"mcpServers": {"global-server": {"command": "node", "args": []}}}
                )
            )

            analyzer = GlobalMCPAnalyzer(home)
            analyzer._analyze_global_config()
            analyzer._generate_recommendations()

            # Should NOT recommend removing global server even if unused
            # (currently, only project-specific servers are recommended for removal)
            assert not any(
                r.server_name == "global-server" for r in analyzer.recommendations
            )

    def test_build_report_structure(self):
        """Test that _build_report creates correct report structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create test data
            analyzer = GlobalMCPAnalyzer(home)
            analyzer.projects = [home / "project1", home / "project2"]
            analyzer.global_servers = {
                "server1": MCPServerInfo(
                    name="server1",
                    type=MCPServerType.NPM,
                    command="npx",
                    status=MCPServerStatus.CONNECTED,
                    config_location="global",
                )
            }
            analyzer.project_servers = {
                "server2": MCPServerInfo(
                    name="server2",
                    type=MCPServerType.PYTHON,
                    command="python",
                    status=MCPServerStatus.UNKNOWN,
                    config_location="project",
                )
            }

            report = analyzer._build_report()

            # Verify structure
            assert isinstance(report, GlobalMCPReport)
            assert report.total_projects == 2
            assert report.total_servers == 2
            assert report.connected_servers == 1
            assert len(report.global_servers) == 1
            assert len(report.project_servers) == 1


class TestGlobalMCPReportMethods:
    """Test GlobalMCPReport utility methods."""

    def test_generate_summary(self):
        """Test summary generation for rebuild output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            # Create report
            report = GlobalMCPReport(
                total_projects=3,
                total_servers=5,
                connected_servers=4,
                global_servers=[
                    MCPServerInfo(
                        name="global1", type=MCPServerType.NPM, command="npx"
                    ),
                    MCPServerInfo(
                        name="global2", type=MCPServerType.PYTHON, command="python"
                    ),
                ],
                project_servers=[
                    MCPServerInfo(
                        name="project1", type=MCPServerType.BINARY, command="./server"
                    )
                ],
                recommendations=[
                    MCPUsageRecommendation(
                        server_name="test",
                        recommendation_type="remove_unused",
                        reason="Never used",
                        action="Remove",
                        priority=1,
                    )
                ],
            )

            analyzer = GlobalMCPAnalyzer(home)
            summary = analyzer.generate_summary(report)

            # Verify summary content
            assert "Global MCP Analysis" in summary
            assert "Projects: 3" in summary
            assert "Servers: 4/5 connected" in summary
            assert "Global: 2" in summary
            assert "Project-specific: 1" in summary
            assert "1 high-priority action(s)" in summary

    def test_report_total_invocations_property(self):
        """Test total_invocations property calculation."""
        usage1 = MCPToolUsage(
            server_name="server1",
            tool_name="tool1",
            invocation_count=10,
        )
        usage2 = MCPToolUsage(
            server_name="server2",
            tool_name="tool2",
            invocation_count=15,
        )

        report = GlobalMCPReport(
            aggregated_usage={"server1:tool1": usage1, "server2:tool2": usage2}
        )

        assert report.total_invocations == 25

    def test_report_total_tokens_property(self):
        """Test total_tokens property calculation."""
        usage1 = MCPToolUsage(
            server_name="server1",
            tool_name="tool1",
            input_tokens=100,
            output_tokens=200,
        )
        usage2 = MCPToolUsage(
            server_name="server2",
            tool_name="tool2",
            input_tokens=150,
            output_tokens=250,
        )

        report = GlobalMCPReport(
            aggregated_usage={"server1:tool1": usage1, "server2:tool2": usage2}
        )

        # 100 + 200 + 150 + 250 = 700
        assert report.total_tokens == 700
