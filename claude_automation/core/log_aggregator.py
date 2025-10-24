"""
Log Aggregator - Captures phase-level logs and provides error summaries.

Solves Error Discoverability issue:
- Captures logs per phase (test-build, activation, automation, learning)
- Auto-tails last 20 lines on failure
- Groups errors by type for easier diagnosis
- Provides actionable error messages with context
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PhaseLog:
    """Log data for a single phase."""

    phase_name: str
    lines: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    exit_code: int = 0

    @property
    def has_errors(self) -> bool:
        """Check if phase had errors."""
        return self.exit_code != 0 or len(self.errors) > 0

    @property
    def last_n_lines(self, n: int = 20) -> list[str]:
        """Get last N lines of log."""
        return self.lines[-n:] if len(self.lines) > n else self.lines


class LogAggregator:
    """
    Aggregates logs from multiple phases and provides error summaries.

    Usage:
        aggregator = LogAggregator(log_file_path)

        with aggregator.capture_phase("test-build") as phase:
            # Run test build
            # Log output is captured
            pass

        if aggregator.has_errors:
            aggregator.print_error_summary()
    """

    def __init__(self, log_file: Path):
        """
        Initialize log aggregator.

        Args:
            log_file: Path to main log file
        """
        self.log_file = log_file
        self.phases: dict[str, PhaseLog] = {}
        self.current_phase: PhaseLog | None = None

    @contextmanager
    def capture_phase(self, phase_name: str):
        """
        Context manager to capture logs for a phase.

        Args:
            phase_name: Name of the phase (e.g., "test-build", "activation")

        Yields:
            PhaseLog object for this phase
        """
        phase = PhaseLog(phase_name=phase_name)
        self.phases[phase_name] = phase
        self.current_phase = phase

        try:
            yield phase
        finally:
            self.current_phase = None

    def log_line(self, line: str):
        """
        Log a line to the current phase.

        Args:
            line: Line to log
        """
        if self.current_phase:
            self.current_phase.lines.append(line)

            # Detect errors and warnings
            line_lower = line.lower()
            if any(marker in line_lower for marker in ["error:", "failed:", "fatal:"]):
                self.current_phase.errors.append(line)
            elif any(marker in line_lower for marker in ["warning:", "warn:"]):
                self.current_phase.warnings.append(line)

    def set_phase_exit_code(self, phase_name: str, exit_code: int):
        """
        Set exit code for a phase.

        Args:
            phase_name: Name of the phase
            exit_code: Exit code (0 = success, non-zero = failure)
        """
        if phase_name in self.phases:
            self.phases[phase_name].exit_code = exit_code

    @property
    def has_errors(self) -> bool:
        """Check if any phase had errors."""
        return any(phase.has_errors for phase in self.phases.values())

    @property
    def failed_phases(self) -> list[PhaseLog]:
        """Get list of phases that failed."""
        return [phase for phase in self.phases.values() if phase.has_errors]

    def print_error_summary(self, tail_lines: int = 20):
        """
        Print error summary with auto-tailed logs.

        Args:
            tail_lines: Number of lines to tail from each failed phase (default: 20)
        """
        if not self.has_errors:
            return

        print("\n" + "=" * 70)
        print("❌ ERROR SUMMARY")
        print("=" * 70)

        for phase in self.failed_phases:
            print(f"\n🔴 Phase: {phase.phase_name} (exit code: {phase.exit_code})")

            # Show errors
            if phase.errors:
                print(f"\n   Errors detected ({len(phase.errors)}):")
                for error in phase.errors[:5]:  # Show first 5 errors
                    # Truncate long lines
                    error_line = error[:120] + "..." if len(error) > 120 else error
                    print(f"   • {error_line}")

                if len(phase.errors) > 5:
                    print(f"   ... and {len(phase.errors) - 5} more errors")

            # Auto-tail last N lines
            print(f"\n   📋 Last {tail_lines} lines:")
            print("   " + "-" * 66)
            for line in phase.last_n_lines(tail_lines):
                # Indent and truncate
                line_truncated = line[:120] + "..." if len(line) > 120 else line
                print(f"   {line_truncated}")
            print("   " + "-" * 66)

        print(f"\n📁 Full logs: {self.log_file}")
        print("=" * 70 + "\n")

    def get_phase_summary(self, phase_name: str) -> str:
        """
        Get one-line summary for a phase.

        Args:
            phase_name: Name of the phase

        Returns:
            Summary string (e.g., "✅ test-build" or "❌ test-build (3 errors)")
        """
        if phase_name not in self.phases:
            return f"❓ {phase_name} (not run)"

        phase = self.phases[phase_name]

        if phase.has_errors:
            error_count = len(phase.errors)
            return f"❌ {phase_name} ({error_count} errors)"
        elif phase.warnings:
            return f"⚠️  {phase_name} ({len(phase.warnings)} warnings)"
        else:
            return f"✅ {phase_name}"

    def print_phase_summaries(self):
        """Print one-line summary for all phases."""
        print("\n📊 Phase Summary:")
        for phase_name in self.phases.keys():
            print(f"   {self.get_phase_summary(phase_name)}")
        print()
