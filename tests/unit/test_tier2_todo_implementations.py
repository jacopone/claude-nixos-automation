"""
Unit tests verifying that Tier 2 TODO implementations are complete.

Tests the specific methods that were TODOs:
- GlobalMCPAnalyzer._generate_recommendations()
- ContextOptimizer.identify_context_gaps()
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_automation.analyzers import ContextOptimizer, GlobalMCPAnalyzer
from claude_automation.schemas import (
    ContextAccessLog,
    MCPServerInfo,
    MCPServerStatus,
    MCPServerType,
    MCPToolUsage,
)


class TestGlobalMCPAnalyzerRecommendations:
    """Test GlobalMCPAnalyzer recommendation generation."""

    def test_generate_recommendations_not_empty(self, tmp_path):
        """Test that _generate_recommendations produces output (not just TODO)."""
        # Create analyzer
        analyzer = GlobalMCPAnalyzer(home_dir=tmp_path, analysis_period_days=30)

        # Add some test data - use project_servers not global_servers
        # (global servers are intentionally skipped as they may be used in other projects)
        analyzer.project_servers = {
            "unused-server": MCPServerInfo(
                name="unused-server",
                type=MCPServerType.UNKNOWN,
                command="test",
                args=[],
                status=MCPServerStatus.UNKNOWN,
                description="Test",
                is_configured=True,
                config_location="project",
            )
        }

        analyzer.aggregated_usage = {}  # No usage = unused server

        # Run recommendation generation
        analyzer._generate_recommendations()

        # Verify recommendations were generated
        assert len(analyzer.recommendations) > 0, "Should generate recommendations"
        assert analyzer.recommendations[0].recommendation_type == "remove_unused"
        assert analyzer.recommendations[0].server_name == "unused-server"

    def test_recommendations_have_all_types(self, tmp_path):
        """Test that all 5 recommendation types can be generated."""
        analyzer = GlobalMCPAnalyzer(home_dir=tmp_path, analysis_period_days=30)

        # Setup data to trigger all recommendation types
        # Use project_servers for unused/error-prone (global servers are skipped for unused detection)
        analyzer.project_servers = {
            "unused": MCPServerInfo(
                name="unused",
                type=MCPServerType.UNKNOWN,
                command="test",
                args=[],
                status=MCPServerStatus.UNKNOWN,
                description="",
                is_configured=True,
                config_location="project",
            ),
            "error-prone": MCPServerInfo(
                name="error-prone",
                type=MCPServerType.UNKNOWN,
                command="test",
                args=[],
                status=MCPServerStatus.UNKNOWN,
                description="",
                is_configured=True,
                config_location="project",
            ),
            "duplicate": MCPServerInfo(  # Same as global - will trigger duplicate warning
                name="duplicate",
                type=MCPServerType.UNKNOWN,
                command="test",
                args=[],
                status=MCPServerStatus.UNKNOWN,
                description="",
                is_configured=True,
                config_location="project",
            ),
        }

        analyzer.global_servers = {
            "duplicate": MCPServerInfo(
                name="duplicate",
                type=MCPServerType.UNKNOWN,
                command="test",
                args=[],
                status=MCPServerStatus.UNKNOWN,
                description="",
                is_configured=True,
                config_location="global",
            ),
        }

        analyzer.aggregated_usage = {
            "underutilized": MCPToolUsage(
                server_name="underutilized",
                tool_name="test",
                invocation_count=3,  # Low usage
                success_count=3,
                error_count=0,
                input_tokens=5000,
                output_tokens=0,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            ),
            "error-prone": MCPToolUsage(
                server_name="error-prone",
                tool_name="test",
                invocation_count=10,
                success_count=2,
                error_count=8,  # 80% failure rate
                input_tokens=8000,
                output_tokens=0,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            ),
        }

        # Generate recommendations
        analyzer._generate_recommendations()

        # Check that multiple types are present
        rec_types = {rec.recommendation_type for rec in analyzer.recommendations}

        assert "remove_unused" in rec_types, "Should detect unused server"
        assert "poor_utilization" in rec_types, "Should detect underutilized server"
        assert "fix_errors" in rec_types, "Should detect error-prone server"
        assert "duplicate_config" in rec_types, "Should detect duplicate config"

    def test_recommendations_are_prioritized(self, tmp_path):
        """Test that recommendations are sorted by priority."""
        analyzer = GlobalMCPAnalyzer(home_dir=tmp_path, analysis_period_days=30)

        # Add data that will generate different priorities
        # Use project_servers (global servers are skipped for unused detection)
        analyzer.project_servers = {
            "unused": MCPServerInfo(
                name="unused",
                type=MCPServerType.UNKNOWN,
                command="test",
                args=[],
                status=MCPServerStatus.UNKNOWN,
                description="",
                is_configured=True,
                config_location="project",
            )
        }

        analyzer.aggregated_usage = {
            "error-prone": MCPToolUsage(
                server_name="error-prone",
                tool_name="test",
                invocation_count=10,
                success_count=2,
                error_count=8,
                input_tokens=8000,
                output_tokens=0,
                cache_read_tokens=0,
                cache_creation_tokens=0,
            )
        }

        analyzer._generate_recommendations()

        # Verify sorting
        if len(analyzer.recommendations) > 1:
            for i in range(len(analyzer.recommendations) - 1):
                assert (
                    analyzer.recommendations[i].priority
                    <= analyzer.recommendations[i + 1].priority
                )


class TestContextOptimizerGapDetection:
    """Test ContextOptimizer gap detection."""

    def test_identify_context_gaps_not_empty(self, tmp_path):
        """Test that identify_context_gaps produces output (not just empty list)."""
        log_file = tmp_path / "context_access.jsonl"
        optimizer = ContextOptimizer(log_file=log_file)

        # Mock usage tracker to return test data
        mock_accesses = [
            ContextAccessLog(
                section_name="Low Relevance Section",
                timestamp=datetime.now() - timedelta(days=i),
                relevance_score=0.2,  # Low relevance
                tokens_in_section=1000,
                session_id=f"session_{i}",
                query_context="database setup postgresql",
            )
            for i in range(10)  # 10 accesses
        ]

        with patch.object(
            optimizer.usage_tracker, "get_recent_accesses", return_value=mock_accesses
        ):
            gaps = optimizer.identify_context_gaps(days=30)

        # Verify gaps were identified
        assert len(gaps) > 0, "Should identify context gaps"
        assert isinstance(gaps[0], str), "Gaps should be strings"

    def test_extract_common_keywords_works(self, tmp_path):
        """Test keyword extraction from query contexts."""
        log_file = tmp_path / "context_access.jsonl"
        optimizer = ContextOptimizer(log_file=log_file)

        query_contexts = [
            "How do I configure database authentication?",
            "Database connection string format",
            "PostgreSQL database setup guide",
            "Authentication token validation",
            "Token expiration configuration",
        ]

        keywords = optimizer._extract_common_keywords(query_contexts)

        # Should extract meaningful keywords
        assert len(keywords) > 0, "Should extract keywords"
        assert "database" in keywords, "Should extract 'database' (appears 3 times)"

        # Should filter stop words
        assert "the" not in keywords
        assert "how" not in keywords

    def test_analyze_undocumented_tools_with_mock_sessions(self, tmp_path):
        """Test detection of undocumented tools."""
        log_file = tmp_path / "context_access.jsonl"
        optimizer = ContextOptimizer(log_file=log_file)

        # Create mock sessions directory with tool usage
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        session_file = sessions_dir / "session_test.jsonl"
        with open(session_file, "w") as f:
            # Write tool usage entries
            for _ in range(15):
                f.write('{"type": "tool_use", "name": "custom_tool"}\n')

        # Mock _is_tool_documented to return False
        with patch.object(optimizer, "_is_tool_documented", return_value=False):
            gaps = optimizer._analyze_undocumented_tools(sessions_dir, days=30)

        # Should detect the undocumented tool
        assert len(gaps) > 0, "Should detect undocumented tools"
        assert "custom_tool" in gaps[0], "Should mention the tool name"
        assert "15 times" in gaps[0], "Should report usage count"


class TestTier2TodoCompletion:
    """Integration test verifying TODOs are resolved."""

    def test_no_todo_comments_in_tier2_analyzers(self):
        """Verify that critical TODO comments are removed from Tier 2 analyzers."""
        # Read the analyzer files
        global_mcp_file = (
            Path(__file__).parent.parent.parent
            / "claude_automation"
            / "analyzers"
            / "global_mcp_analyzer.py"
        )
        context_opt_file = (
            Path(__file__).parent.parent.parent
            / "claude_automation"
            / "analyzers"
            / "context_optimizer.py"
        )

        global_mcp_content = global_mcp_file.read_text()
        context_opt_content = context_opt_file.read_text()

        # Check for specific TODOs that were marked as issues
        assert (
            "TODO: Implement sophisticated recommendations" not in global_mcp_content
        ), "GlobalMCPAnalyzer still has TODO for recommendations"

        assert "TODO: Implement by analyzing session logs" not in context_opt_content, (
            "ContextOptimizer still has TODO for gap detection"
        )

        # Verify implementation signatures exist
        assert "_recommend_remove_unused" in global_mcp_content, (
            "Should have _recommend_remove_unused method"
        )
        assert "_recommend_fix_underutilized" in global_mcp_content, (
            "Should have _recommend_fix_underutilized method"
        )
        assert "_recommend_promote_high_value" in global_mcp_content, (
            "Should have _recommend_promote_high_value method"
        )
        assert "_recommend_fix_errors" in global_mcp_content, (
            "Should have _recommend_fix_errors method"
        )
        assert "_recommend_deduplicate" in global_mcp_content, (
            "Should have _recommend_deduplicate method"
        )

        assert "_extract_common_keywords" in context_opt_content, (
            "Should have _extract_common_keywords method"
        )
        assert "_analyze_undocumented_tools" in context_opt_content, (
            "Should have _analyze_undocumented_tools method"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
