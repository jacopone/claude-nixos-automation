#!/usr/bin/env python3
"""
Check learning data disk health and assess risk.

This CLI tool analyzes disk usage for adaptive learning data (session logs,
learning cache) and provides risk assessment with actionable recommendations.

Part of the claude-nixos-automation intelligent data lifecycle management system.
Phase 1: Monitoring and visibility (no automatic cleanup).
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.analyzers.disk_health_monitor import DiskHealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run disk health check."""
    parser = argparse.ArgumentParser(
        description="Check learning data disk health",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check disk health (default)
  python check-data-health.py

  # Verbose mode
  python check-data-health.py --verbose

Exit codes:
  0 = GREEN (no action needed)
  1 = YELLOW/ORANGE (optional/planned cleanup)
  2 = RED (urgent cleanup needed)
        """,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Run analysis
        monitor = DiskHealthMonitor()
        report = monitor.analyze()

        # Print formatted report
        print_report(report)

        # Return exit code based on risk level
        return report.exit_code

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        print(f"\n❌ Health check failed: {e}")
        return 1


def print_report(report):
    """
    Print formatted health report.

    Args:
        report: LearningDataHealthReport to display
    """
    print("")
    print("  " + "=" * 68)
    print("  📊 LEARNING DATA HEALTH CHECK")
    print("  " + "=" * 68)
    print("")

    # Data Size section
    print("  Data Size:")
    print(f"     • Session logs: {report.session_logs_mb}MB ({report.session_count} sessions)")
    print(f"     • Learning cache: {report.learning_data_mb}MB (patterns, metrics)")

    if report.archives_mb > 0:
        print(f"     • Archives: {report.archives_mb}MB (compressed)")

    print(f"     • Total: {report.total_mb}MB ({report.total_gb:.2f}GB)")
    print("")

    # Disk Space section
    print("  Disk Space:")
    print(f"     • Available: {report.available_gb}GB")
    print(f"     • Usage: {report.usage_percentage:.2f}% of disk")

    # Growth projection (if available)
    if report.growth_mb_per_month is not None:
        print(f"     • Growth: ~{report.growth_mb_per_month:.0f}MB/month")

        if report.projected_years is not None:
            if report.projected_years >= 5:
                print(f"     • Projection: {report.projected_years:.0f} years ✅")
            elif report.projected_years >= 1:
                print(f"     • Projection: {report.projected_years:.1f} years ⚠️")
            else:
                months = report.months_until_full
                print(f"     • Projection: {months:.0f} months 🔴")
    else:
        # Phase 1: No growth tracking yet
        print("     • Growth: Insufficient data (run 2+ rebuilds for projection)")

    print("")

    # Risk Assessment section
    risk_emoji = {
        "green": "✅",
        "yellow": "⚠️",
        "orange": "🟠",
        "red": "🔴",
    }
    emoji = risk_emoji.get(report.risk_level.value, "❓")

    print(f"  Assessment: {emoji} {report.risk_message}")
    print("")

    # Actionable recommendations based on risk level
    if report.risk_level.value == "green":
        pass  # No recommendations needed
    elif report.risk_level.value == "yellow":
        print("  💡 Recommendations:")
        print("     • Continue monitoring disk usage")
        print("     • Optional: Consider cleanup after implementing pending insights")
        print("")
    elif report.risk_level.value == "orange":
        print("  💡 Recommendations:")
        print("     • Plan cleanup after extracting insights from session data")
        print("     • Review pending adaptive learning suggestions")
        print("     • Consider archiving sessions older than 90 days")
        print("")
    else:  # red
        print("  ⚠️  URGENT RECOMMENDATIONS:")
        print("     • Run deep analysis mode to extract ALL insights NOW")
        print("     • Review and implement pending suggestions")
        print("     • Archive or delete processed sessions")
        print("     • Prevent data loss by acting before disk fills")
        print("")

    print("  " + "=" * 68)
    print("")


if __name__ == "__main__":
    sys.exit(main())
