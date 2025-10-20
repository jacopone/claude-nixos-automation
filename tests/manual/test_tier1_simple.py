#!/usr/bin/env python3
"""
Simple end-to-end test for Tier 1 components (no pytest required).
Run with: devenv shell -c "python test_tier1_simple.py"
"""
import sys
import tempfile
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_phase3_approval_tracker():
    """Test Phase 3: Permission Learning (ApprovalTracker)"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Phase 3: Permission Learning - ApprovalTracker{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    try:
        from claude_automation.analyzers.approval_tracker import ApprovalTracker
        print(f"{GREEN}✓{RESET} ApprovalTracker imported successfully")

        # Create temp directory
        storage_dir = Path(tempfile.mkdtemp())

        try:
            tracker = ApprovalTracker(storage_dir=storage_dir)
            print(f"{GREEN}✓{RESET} ApprovalTracker initialized")

            # Test recording approval
            tracker.record_approval(
                tool_name="Bash",
                command="ls -la",
                context={"working_dir": "/home/user"},
                approved=True
            )
            print(f"{GREEN}✓{RESET} Recorded approval")

            # Test getting recent approvals
            approvals = tracker.get_recent_approvals(days=7)
            assert len(approvals) == 1, f"Expected 1 approval, got {len(approvals)}"
            print(f"{GREEN}✓{RESET} Retrieved recent approvals: {len(approvals)}")

            # Test pattern detection
            patterns = tracker.detect_approval_patterns(min_occurrences=1)
            print(f"{GREEN}✓{RESET} Detected approval patterns: {len(patterns)}")

            # Test suggestions
            suggestions = tracker.suggest_auto_approvals(min_confidence=0.5)
            print(f"{GREEN}✓{RESET} Generated suggestions: {len(suggestions)}")

            print(f"\n{GREEN}{'='*80}")
            print("PHASE 3: ALL TESTS PASSED ✓")
            print(f"{'='*80}{RESET}\n")
            return True

        finally:
            import shutil
            shutil.rmtree(storage_dir, ignore_errors=True)

    except Exception as e:
        print(f"\n{RED}{'='*80}")
        print("PHASE 3: FAILED ✗")
        print(f"Error: {e}")
        print(f"{'='*80}{RESET}\n")
        import traceback
        traceback.print_exc()
        return False

def test_phase4_permission_patterns():
    """Test Phase 4: Permission Pattern Detection"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Phase 4: Global MCP Optimization - Permission Patterns{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    try:
        from claude_automation.analyzers.approval_tracker import ApprovalTracker
        from claude_automation.analyzers.permission_pattern_detector import (
            PermissionPatternDetector,
        )
        print(f"{GREEN}✓{RESET} PermissionPatternDetector imported successfully")

        storage_dir = Path(tempfile.mkdtemp())

        try:
            # Create ApprovalTracker first (required by PermissionPatternDetector)
            approval_tracker = ApprovalTracker(storage_dir=storage_dir)
            detector = PermissionPatternDetector(approval_tracker=approval_tracker)
            print(f"{GREEN}✓{RESET} PermissionPatternDetector initialized")

            # Test logging permission usage
            detector.log_permission_usage(
                tool_name="Read",
                pattern="//home/user/**",
                access_type="read",
                matched_path="/home/user/project/file.py",
                context={"operation": "code_review"}
            )
            print(f"{GREEN}✓{RESET} Logged permission usage")

            # Test pattern analysis
            patterns = detector.analyze_patterns(min_usage=1)
            assert len(patterns) > 0, "Expected at least 1 pattern"
            print(f"{GREEN}✓{RESET} Analyzed patterns: {len(patterns)}")

            # Test optimization suggestions
            suggestions = detector.suggest_permission_optimizations()
            print(f"{GREEN}✓{RESET} Generated optimization suggestions: {len(suggestions)}")

            print(f"\n{GREEN}{'='*80}")
            print("PHASE 4: ALL TESTS PASSED ✓")
            print(f"{'='*80}{RESET}\n")
            return True

        finally:
            import shutil
            shutil.rmtree(storage_dir, ignore_errors=True)

    except Exception as e:
        print(f"\n{RED}{'='*80}")
        print("PHASE 4: FAILED ✗")
        print(f"Error: {e}")
        print(f"{'='*80}{RESET}\n")
        import traceback
        traceback.print_exc()
        return False

def test_phase5_context_optimizer():
    """Test Phase 5: Context Optimization"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Phase 5: Context Optimization{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    try:
        from claude_automation.analyzers.context_optimizer import (
            ContextOptimizer,
            ContextUsageTracker,
        )
        print(f"{GREEN}✓{RESET} ContextUsageTracker and ContextOptimizer imported successfully")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            usage_log = Path(f.name)

        try:
            # Test ContextUsageTracker
            tracker = ContextUsageTracker(log_file=usage_log)
            print(f"{GREEN}✓{RESET} ContextUsageTracker initialized")

            tracker.log_section_access(
                section_name="Git Commands",
                tokens_loaded=500,
                was_referenced=True,
                context={"query": "How to commit?"}
            )
            print(f"{GREEN}✓{RESET} Logged section access")

            # Test ContextOptimizer
            optimizer = ContextOptimizer(usage_log_path=usage_log)
            print(f"{GREEN}✓{RESET} ContextOptimizer initialized")

            # Test section usage analysis
            usage_stats = optimizer.analyze_section_usage(days=7)
            print(f"{GREEN}✓{RESET} Analyzed section usage: {len(usage_stats)} sections")

            # Test noise detection
            noise_sections = optimizer.detect_noise_sections(min_loads=1, utilization_threshold=0.5)
            print(f"{GREEN}✓{RESET} Detected noise sections: {len(noise_sections)}")

            # Test effective context ratio
            ratio = optimizer.calculate_effective_context_ratio(days=7)
            print(f"{GREEN}✓{RESET} Calculated effective context ratio: {ratio:.2%}")

            # Test optimization suggestions
            suggestions = optimizer.suggest_optimizations()
            print(f"{GREEN}✓{RESET} Generated optimization suggestions: {len(suggestions)}")

            print(f"\n{GREEN}{'='*80}")
            print("PHASE 5: ALL TESTS PASSED ✓")
            print(f"{'='*80}{RESET}\n")
            return True

        finally:
            usage_log.unlink(missing_ok=True)

    except Exception as e:
        print(f"\n{RED}{'='*80}")
        print("PHASE 5: FAILED ✗")
        print(f"Error: {e}")
        print(f"{'='*80}{RESET}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Tier 1 component tests"""
    print(f"\n{YELLOW}{'='*80}")
    print("TIER 1 COMPONENTS - END-TO-END TESTING")
    print(f"{'='*80}{RESET}\n")
    print("Testing all three Tier 1 learning components:")
    print("  • Phase 3: Permission Learning (ApprovalTracker)")
    print("  • Phase 4: Global MCP Optimization (PermissionPatternDetector)")
    print("  • Phase 5: Context Optimization (ContextOptimizer)")
    print()

    results = {
        'Phase 3': test_phase3_approval_tracker(),
        'Phase 4': test_phase4_permission_patterns(),
        'Phase 5': test_phase5_context_optimizer()
    }

    # Summary
    print(f"\n{YELLOW}{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}{RESET}\n")

    passed = sum(results.values())
    total = len(results)

    for phase, result in results.items():
        status = f"{GREEN}PASSED ✓{RESET}" if result else f"{RED}FAILED ✗{RESET}"
        print(f"  {phase}: {status}")

    print(f"\n{YELLOW}{'='*80}{RESET}")

    if passed == total:
        print(f"{GREEN}ALL TIER 1 COMPONENTS WORKING! ✓ ({passed}/{total}){RESET}")
        print(f"{YELLOW}{'='*80}{RESET}\n")
        return 0
    else:
        print(f"{RED}SOME TESTS FAILED ({passed}/{total} passed){RESET}")
        print(f"{YELLOW}{'='*80}{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
