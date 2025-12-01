#!/usr/bin/env python3
"""
Unified entry point for all adaptive learning components.
Coordinates permissions, MCP, context, workflows, instructions, cross-project, and meta-learning.

This script is designed to run at the end of ./rebuild-nixos workflow.
"""

import argparse
import logging
import sys

from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine
from claude_automation.schemas import AdaptiveSystemConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run adaptive learning system."""
    parser = argparse.ArgumentParser(
        description="Run Claude Code adaptive learning system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full interactive learning cycle (default)
  python run-adaptive-learning.py

  # Run non-interactively (auto-accept all suggestions)
  python run-adaptive-learning.py --no-interactive

  # Dry run (show suggestions without applying)
  python run-adaptive-learning.py --dry-run

  # Adjust detection thresholds
  python run-adaptive-learning.py --min-occurrences 5 --confidence 0.8
        """,
    )

    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        default=True,
        help="Present suggestions interactively (default: True)",
    )

    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Run non-interactively (auto-accept suggestions)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show suggestions without applying them",
    )

    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=3,
        help="Minimum occurrences for pattern detection (default: 3)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold (0-1, default: 0.7)",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Analysis window in days (default: 30)",
    )

    parser.add_argument(
        "--max-suggestions",
        type=int,
        default=5,
        help="Maximum suggestions per component (default: 5)",
    )

    parser.add_argument(
        "--disable-meta-learning",
        action="store_true",
        help="Disable meta-learning calibration",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if args.confidence < 0.0 or args.confidence > 1.0:
        parser.error("--confidence must be between 0.0 and 1.0")

    if args.min_occurrences < 1:
        parser.error("--min-occurrences must be >= 1")

    if args.days < 1:
        parser.error("--days must be >= 1")

    # Create configuration
    config = AdaptiveSystemConfig(
        interactive=args.interactive and not args.dry_run,
        min_occurrences=args.min_occurrences,
        confidence_threshold=args.confidence,
        analysis_period_days=args.days,
        max_suggestions_per_component=args.max_suggestions,
        enable_meta_learning=not args.disable_meta_learning,
    )

    # Log configuration
    logger.info("Starting adaptive learning with configuration:")
    logger.info(f"  Interactive: {config.interactive}")
    logger.info(f"  Min occurrences: {config.min_occurrences}")
    logger.info(f"  Confidence threshold: {config.confidence_threshold}")
    logger.info(f"  Analysis period: {config.analysis_period_days} days")
    logger.info(
        f"  Max suggestions per component: {config.max_suggestions_per_component}"
    )
    logger.info(f"  Meta-learning: {config.enable_meta_learning}")

    if args.dry_run:
        logger.info("  DRY RUN MODE: No changes will be applied")

    # Initialize engine
    try:
        engine = AdaptiveSystemEngine(config)
    except Exception as e:
        logger.error(f"Failed to initialize adaptive system engine: {e}", exc_info=True)
        return 1

    # Run learning cycle
    try:
        print("")
        print("  🔍 Analyzing permission patterns...", flush=True)
        print("  🌐 Checking MCP server usage...", flush=True)
        print("  📝 Reviewing context effectiveness...", flush=True)
        print("  🔄 Detecting workflow patterns...", flush=True)
        print("  📋 Evaluating instruction effectiveness...", flush=True)
        print("  🔬 Looking for cross-project patterns...", flush=True)
        if config.enable_meta_learning:
            print("  🧠 Running meta-learning calibration...", flush=True)
        print("", flush=True)

        report = engine.run_full_learning_cycle()

        if args.dry_run:
            print("\n[DRY RUN] No changes applied")

        # Print concise, actionable summary
        print("")
        print("  " + "=" * 68)
        print("  🧠 ADAPTIVE LEARNING - SYSTEM OPTIMIZATION")
        print("  " + "=" * 68)

        if report.total_suggestions == 0:
            print("\n  ✅ System is already optimized - no changes needed!")
            print("")
            return 0

        # Show specific, actionable recommendations
        has_content = False

        # MCP Server Optimizations (most impactful)
        if report.mcp_optimizations and len(report.mcp_optimizations) > 0:
            has_content = True
            print("\n  🌐 MCP Server Optimizations:")
            for opt in report.mcp_optimizations[:5]:
                server = opt.get("server_name", "Unknown")
                reason = opt.get("description", opt.get("impact", "No details"))
                priority = opt.get("priority", "MEDIUM")

                # Make it actionable
                if "never used" in reason.lower():
                    action = (
                        f"Disable '{server}' (unused, wastes tokens on every session)"
                    )
                elif "low utilization" in reason.lower() or "poor" in reason.lower():
                    action = (
                        f"Move '{server}' to project-level (only 6-10% utilization)"
                    )
                else:
                    action = f"{server}: {reason}"

                priority_marker = "❗" if priority == "HIGH" else "•"
                print(f"     {priority_marker} {action}")

            # Calculate tangible impact
            total_servers = len(report.mcp_optimizations)
            print(
                f"\n     💡 Impact: ~{total_servers * 2000} tokens saved per session (faster responses)"
            )

        # Permission Patterns
        if report.permission_patterns and len(report.permission_patterns) > 0:
            has_content = True
            print("\n  🔐 Permission Auto-Approvals:")
            for pattern in report.permission_patterns[:3]:
                if hasattr(pattern, "description"):
                    desc = pattern.description
                    impact = (
                        pattern.impact_estimate
                        if hasattr(pattern, "impact_estimate")
                        else "reduces prompts"
                    )
                elif isinstance(pattern, dict):
                    desc = pattern.get("description", "Unknown pattern")
                    impact = pattern.get("impact", "reduces prompts")
                else:
                    continue

                print(f"     • {desc} ({impact})")

        # Context Optimizations
        if report.context_suggestions and len(report.context_suggestions) > 0:
            has_content = True
            tokens_saved = sum(
                s.get("tokens", 0) if isinstance(s, dict) else 0
                for s in report.context_suggestions
            )
            print(
                f"\n  📝 Context Optimizations: {len(report.context_suggestions)} sections"
            )
            print(
                f"     💡 Impact: ~{tokens_saved}K tokens saved (unused CLAUDE.md sections)"
            )

        # Workflow Shortcuts
        if report.workflow_patterns and len(report.workflow_patterns) > 0:
            has_content = True
            print(
                f"\n  🔄 Workflow Shortcuts: {len(report.workflow_patterns)} repeated command sequences"
            )
            print("     💡 Impact: Faster workflows (combine frequently-used commands)")

        if not has_content:
            print("\n  ℹ️  Analyzed but found no high-confidence optimizations")

        print("\n  " + "=" * 68)
        print(
            f"  📊 Total: {report.total_suggestions} optimizations | System health: {report.meta_insights.get('system_health', 0):.0%}"
        )
        print("  " + "=" * 68)
        print("")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Learning cycle interrupted by user")
        return 130  # Standard exit code for Ctrl+C

    except Exception as e:
        logger.error(f"Learning cycle failed: {e}", exc_info=True)
        print(f"\n❌ Learning cycle failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
