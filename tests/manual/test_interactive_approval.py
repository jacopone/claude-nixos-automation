#!/usr/bin/env python3
"""
Quick test of interactive approval flow.
Run this to verify that the user is prompted for approvals.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine
from claude_automation.schemas import AdaptiveSystemConfig


def main():
    """Test interactive approval flow."""
    print("=" * 70)
    print("INTERACTIVE APPROVAL TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("1. Run the adaptive learning cycle")
    print("2. Show you any suggestions it finds")
    print("3. Prompt you to approve/reject each one")
    print("4. Apply approved changes (currently logs only)")
    print("\n" + "=" * 70)
    print("")

    # Configure for interactive mode
    config = AdaptiveSystemConfig(
        interactive=True,
        min_occurrences=1,  # Low threshold for testing
        confidence_threshold=0.3,  # Low threshold for testing
        analysis_period_days=90,
        max_suggestions_per_component=5,
        enable_meta_learning=True,
    )

    # Initialize engine
    engine = AdaptiveSystemEngine(config)

    # Run full learning cycle
    print("Running learning cycle...\n")
    report = engine.run_full_learning_cycle()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"\nTotal suggestions found: {report.total_suggestions}")
    print(f"Estimated improvements: {report.estimated_improvements}")
    print(
        "\nIf you were prompted to approve suggestions, the interactive flow is working! ✓"
    )
    print(
        "If you saw NO prompts, there were no suggestions found (system already optimal)."
    )
    print("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
