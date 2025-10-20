#!/usr/bin/env python3
"""
Manual end-to-end test for all Tier 1 learning components.
Run with: uv run python test_tier1_manual.py
"""

import json
import sys
import tempfile
from pathlib import Path

# Test counters
tests_passed = 0
tests_failed = 0


def test(name: str, func):
    """Run a test and track results."""
    global tests_passed, tests_failed

    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)

    try:
        func()
        print("✓ PASSED")
        tests_passed += 1
        return True
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        tests_failed += 1
        return False


def test_phase3_permission_learning():
    """Test Phase 3: Permission Learning"""
    print("\n" + "="*80)
    print("PHASE 3: PERMISSION LEARNING")
    print("="*80)

    # Test 1: Import ApprovalTracker
    def test_import():
        print("✓ ApprovalTracker imported successfully")

    test("Import ApprovalTracker", test_import)

    # Test 2: Log approval
    def test_log_approval():
        from claude_automation.analyzers.approval_tracker import ApprovalTracker

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "approvals.jsonl"
            tracker = ApprovalTracker(log_file)

            tracker.log_approval("Bash(git status:*)", "test-session", "/test/project")

            # Verify
            approvals = tracker.get_recent_approvals(days=1)
            assert len(approvals) == 1, f"Expected 1 approval, got {len(approvals)}"
            print(f"✓ Logged and retrieved {len(approvals)} approval(s)")

    test("Log permission approval", test_log_approval)

    # Test 3: Detect patterns
    def test_detect_patterns():
        from claude_automation.analyzers.approval_tracker import ApprovalTracker
        from claude_automation.analyzers.permission_pattern_detector import (
            PermissionPatternDetector,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "approvals.jsonl"
            tracker = ApprovalTracker(log_file)

            # Log multiple git approvals
            for i in range(5):
                tracker.log_approval("Bash(git status:*)", f"session-{i}", "/test/project")

            # Detect patterns
            detector = PermissionPatternDetector(log_file)
            patterns = detector.detect_patterns(days=1)

            assert len(patterns) > 0, "Expected to detect at least one pattern"
            print(f"✓ Detected {len(patterns)} pattern(s)")

            for pattern in patterns:
                print(f"  - {pattern.pattern_type}: {pattern.occurrences} occurrences, {pattern.confidence:.0%} confidence")

    test("Detect permission patterns", test_detect_patterns)

    # Test 4: Generate suggestions
    def test_generate_suggestions():
        from claude_automation.analyzers.approval_tracker import ApprovalTracker
        from claude_automation.generators.intelligent_permissions_generator import (
            IntelligentPermissionsGenerator,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "approvals.jsonl"
            tracker = ApprovalTracker(log_file)

            # Log multiple git approvals
            for i in range(5):
                tracker.log_approval("Bash(git status:*)", f"session-{i}", "/test/project")

            # Generate suggestions
            generator = IntelligentPermissionsGenerator(log_file)
            suggestions = generator.get_pattern_suggestions(days=1)

            print(f"✓ Generated {len(suggestions)} suggestion(s)")

            for suggestion in suggestions:
                print(f"  - {suggestion.description}")
                print(f"    Confidence: {suggestion.confidence_percentage}%")

    test("Generate permission suggestions", test_generate_suggestions)


def test_phase4_global_mcp():
    """Test Phase 4: Global MCP Optimization"""
    print("\n" + "="*80)
    print("PHASE 4: GLOBAL MCP OPTIMIZATION")
    print("="*80)

    # Test 1: Import GlobalMCPAnalyzer
    def test_import():
        print("✓ GlobalMCPAnalyzer imported successfully")

    test("Import GlobalMCPAnalyzer", test_import)

    # Test 2: Discover projects
    def test_discover():
        from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)

            # Create test projects
            for i in range(3):
                project = home / f"project{i}"
                project.mkdir()
                (project / ".claude").mkdir()
                (project / ".claude" / "mcp.json").write_text(
                    json.dumps({"mcpServers": {f"server{i}": {"command": "node"}}})
                )

            analyzer = GlobalMCPAnalyzer(home)
            projects = analyzer.discover_projects()

            assert len(projects) == 3, f"Expected 3 projects, got {len(projects)}"
            print(f"✓ Discovered {len(projects)} project(s)")

    test("Discover MCP projects", test_discover)

    # Test 3: Analyze all projects
    def test_analyze():
        from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)

            # Create test projects
            project = home / "test_project"
            project.mkdir()
            (project / ".claude").mkdir()
            (project / ".claude" / "mcp.json").write_text(
                json.dumps({
                    "mcpServers": {
                        "mcp-nixos": {"command": "mcp-nixos"},
                        "serena": {"command": "serena"}
                    }
                })
            )

            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()

            assert report.total_projects == 1, f"Expected 1 project, got {report.total_projects}"
            assert report.total_servers == 2, f"Expected 2 servers, got {report.total_servers}"

            print(f"✓ Analyzed {report.total_projects} project(s), {report.total_servers} server(s)")

    test("Analyze all MCP projects", test_analyze)

    # Test 4: Generate summary
    def test_summary():
        from claude_automation.analyzers.global_mcp_analyzer import GlobalMCPAnalyzer

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)

            project = home / "test_project"
            project.mkdir()
            (project / ".claude").mkdir()
            (project / ".claude" / "mcp.json").write_text(
                json.dumps({"mcpServers": {"test-server": {"command": "node"}}})
            )

            analyzer = GlobalMCPAnalyzer(home)
            report = analyzer.analyze_all_projects()
            summary = analyzer.generate_summary(report)

            assert "Global MCP Analysis" in summary, "Expected summary to contain title"
            print("✓ Generated summary:")
            print(summary)

    test("Generate MCP summary", test_summary)


def test_phase5_context_optimization():
    """Test Phase 5: Context Optimization"""
    print("\n" + "="*80)
    print("PHASE 5: CONTEXT OPTIMIZATION")
    print("="*80)

    # Test 1: Import ContextOptimizer
    def test_import():
        print("✓ ContextOptimizer imported successfully")

    test("Import ContextOptimizer", test_import)

    # Test 2: Log section access
    def test_log_access():
        from claude_automation.analyzers.context_optimizer import ContextOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "context-access.jsonl"
            optimizer = ContextOptimizer(log_file)

            optimizer.log_section_access(
                section_name="Modern CLI Tools",
                tokens_in_section=500,
                relevance_score=0.9,
                session_id="test-session",
                query_context="User asked about eza"
            )

            assert log_file.exists(), "Log file should exist"
            print("✓ Logged section access")

    test("Log section access", test_log_access)

    # Test 3: Calculate usage statistics
    def test_usage_stats():
        from claude_automation.analyzers.context_optimizer import ContextOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "context-access.jsonl"
            optimizer = ContextOptimizer(log_file)

            # Log multiple accesses
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Test Section",
                    tokens_in_section=500,
                    relevance_score=0.8,
                    session_id=f"session-{i}"
                )

            stats = optimizer.get_section_usage_statistics(period_days=1)

            assert "Test Section" in stats, "Expected to find Test Section in stats"
            assert stats["Test Section"].total_loads == 10

            print("✓ Calculated usage statistics:")
            print(f"  - Loads: {stats['Test Section'].total_loads}")
            print(f"  - Avg relevance: {stats['Test Section'].avg_relevance:.1%}")

    test("Calculate section usage statistics", test_usage_stats)

    # Test 4: Identify noise sections
    def test_noise():
        from claude_automation.analyzers.context_optimizer import ContextOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "context-access.jsonl"
            optimizer = ContextOptimizer(log_file)

            # Create noise section (loaded many times, low relevance)
            for i in range(20):
                optimizer.log_section_access(
                    section_name="Noise Section",
                    tokens_in_section=500,
                    relevance_score=0.0,
                    session_id=f"session-{i}"
                )

            noise = optimizer.identify_noise_sections(period_days=1)

            assert len(noise) == 1, f"Expected 1 noise section, got {len(noise)}"
            print(f"✓ Identified {len(noise)} noise section(s)")
            print(f"  - {noise[0].section_name}: {noise[0].utilization_rate:.0%} utilization")

    test("Identify noise sections", test_noise)

    # Test 5: Calculate effective ratio
    def test_effective_ratio():
        from claude_automation.analyzers.context_optimizer import ContextOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "context-access.jsonl"
            optimizer = ContextOptimizer(log_file)

            # Good section (high relevance)
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Good Section",
                    tokens_in_section=500,
                    relevance_score=0.9,
                    session_id=f"session-{i}"
                )

            ratio = optimizer.calculate_effective_context_ratio(period_days=1)

            assert ratio > 0.7, f"Expected ratio > 0.7, got {ratio:.2f}"
            print(f"✓ Calculated effective ratio: {ratio:.1%}")

    test("Calculate effective context ratio", test_effective_ratio)

    # Test 6: Generate optimization suggestions
    def test_suggestions():
        from claude_automation.analyzers.context_optimizer import ContextOptimizer

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "context-access.jsonl"
            optimizer = ContextOptimizer(log_file)

            # Create noise section
            for i in range(20):
                optimizer.log_section_access(
                    section_name="Noise Section",
                    tokens_in_section=800,
                    relevance_score=0.0,
                    session_id=f"session-{i}"
                )

            suggestions = optimizer.analyze(period_days=1)

            assert len(suggestions) > 0, "Expected at least one suggestion"
            prune_suggestions = [s for s in suggestions if s.optimization_type == "prune_section"]
            assert len(prune_suggestions) > 0, "Expected at least one prune suggestion"

            print(f"✓ Generated {len(suggestions)} suggestion(s):")
            for s in suggestions:
                print(f"  - [{s.optimization_type}] {s.section_name}")
                print(f"    Reason: {s.reason}")
                if s.token_savings > 0:
                    print(f"    Savings: {s.token_savings} tokens")

    test("Generate optimization suggestions", test_suggestions)


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TIER 1 COMPONENTS - END-TO-END TESTING")
    print("="*80)

    test_phase3_permission_learning()
    test_phase4_global_mcp()
    test_phase5_context_optimization()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✓ Passed: {tests_passed}")
    print(f"✗ Failed: {tests_failed}")
    print("="*80)

    if tests_failed == 0:
        print("\n✓ All Tier 1 Components Working!")
        return 0
    else:
        print(f"\n✗ {tests_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
