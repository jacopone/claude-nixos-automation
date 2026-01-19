#!/usr/bin/env python3
"""
CLAUDE.md Suggestion Engine CLI (Two-Stage Pipeline).

Stage 1: Regex extraction of candidate patterns from session logs
Stage 2: Claude API analysis for intelligent filtering and formatting

Usage:
  nix run .#suggest-claude-md               # Show suggestions
  nix run .#suggest-claude-md -- --apply    # Interactive apply
  nix run .#suggest-claude-md -- --json     # Machine-readable output
  nix run .#suggest-claude-md -- --days 7   # Analyze last 7 days

Requirements:
  ANTHROPIC_API_KEY environment variable must be set for Stage 2 analysis.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from claude_automation.analyzers.claude_md_suggester import ClaudeMdSuggester
from claude_automation.schemas.suggestions import SuggestionConfig, SuggestionScope

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ANSI colors for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


def main():
    """Run CLAUDE.md suggestion engine."""
    parser = argparse.ArgumentParser(
        description="Suggest CLAUDE.md edits based on session conversations (Two-Stage Pipeline)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show suggestions from last 30 days
  ANTHROPIC_API_KEY=sk-... python suggest_claude_md.py

  # Show suggestions from last 7 days
  python suggest_claude_md.py --days 7

  # Interactive apply mode
  python suggest_claude_md.py --apply

  # JSON output for scripting
  python suggest_claude_md.py --json

  # Lower confidence threshold
  python suggest_claude_md.py --confidence 0.5

How it works:
  Stage 1: Regex patterns extract candidate instructions from session logs
  Stage 2: Claude API analyzes candidates, filters noise, and formats suggestions
        """,
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )

    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=2,
        help="Minimum occurrences for suggestions (default: 2)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help="Minimum confidence threshold (0-1, default: 0.6)",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Interactive mode to apply suggestions",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for scripting)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output including Stage 1/2 progress",
    )

    parser.add_argument(
        "--claude-dir",
        type=Path,
        default=Path.home() / ".claude",
        help="Path to .claude directory (default: ~/.claude)",
    )

    parser.add_argument(
        "--skip-if-no-key",
        action="store_true",
        help="Skip gracefully if ANTHROPIC_API_KEY is not set (for automation)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        if args.skip_if_no_key:
            print(f"{Colors.DIM}⏭️  Skipping CLAUDE.md suggestions (ANTHROPIC_API_KEY not set){Colors.END}")
            sys.exit(0)
        print(f"{Colors.RED}Error: ANTHROPIC_API_KEY environment variable required{Colors.END}")
        print("\nThe suggestion engine uses Claude API to analyze and filter candidates.")
        print("Set your API key: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    # Create config
    config = SuggestionConfig(
        analysis_period_days=args.days,
        min_occurrences=args.min_occurrences,
        confidence_threshold=args.confidence,
    )

    # Create suggester and analyze
    suggester = ClaudeMdSuggester(claude_dir=args.claude_dir, config=config)

    if args.verbose:
        print(f"{Colors.CYAN}Stage 1: Extracting candidate patterns from session logs...{Colors.END}")

    try:
        report = suggester.analyze_sessions(days=args.days)
    except ValueError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    # Output based on mode
    if args.json:
        output_json(report)
    elif args.apply:
        interactive_apply(report)
    else:
        display_report(report)


def display_report(report):
    """Display suggestions in human-readable format."""
    if not report.has_suggestions:
        print(f"\n{Colors.DIM}No CLAUDE.md suggestions found.{Colors.END}")
        print(f"Analyzed {report.sessions_analyzed} sessions from the last {report.analysis_period_days} days.")
        print(f"\n{Colors.DIM}This could mean:{Colors.END}")
        print("  • No instruction patterns detected in conversations")
        print("  • Claude filtered all candidates as noise")
        print("  • Try lowering --confidence threshold (default: 0.6)")
        return

    print(f"\n{Colors.BOLD}{Colors.CYAN}📝 CLAUDE.md Suggestions{Colors.END}")
    print(f"{Colors.DIM}Based on {report.sessions_analyzed} sessions from the last {report.analysis_period_days} days{Colors.END}")
    print(f"{Colors.DIM}(Two-stage analysis: regex extraction → Claude filtering){Colors.END}\n")

    # Global suggestions
    if report.global_suggestions:
        print(f"{Colors.BOLD}{Colors.GREEN}GLOBAL{Colors.END} (add to ~/.claude/CLAUDE-USER-POLICIES.md):")
        print()
        for i, s in enumerate(report.global_suggestions, 1):
            print(f"  {Colors.BOLD}{i}.{Colors.END} {Colors.GREEN}\"{s.instruction}\"{Colors.END}")
            print(f"     {Colors.DIM}Projects: {', '.join(s.projects[:3])}{'...' if len(s.projects) > 3 else ''}{Colors.END}")
            print(f"     {Colors.DIM}→ Section: {s.suggested_section}{Colors.END}")
            print(f"     {Colors.DIM}Confidence: {s.confidence:.0%}{Colors.END}")
            print()

    # Project-specific suggestions
    if report.project_suggestions:
        for project_path, suggestions in report.project_suggestions.items():
            # Clean up project path for display
            display_path = project_path.replace("/home/", "~/")
            print(f"{Colors.BOLD}{Colors.YELLOW}PROJECT-SPECIFIC{Colors.END} ({display_path}/CLAUDE.md):")
            print()
            for i, s in enumerate(suggestions, 1):
                print(f"  {Colors.BOLD}{i}.{Colors.END} {Colors.YELLOW}\"{s.instruction}\"{Colors.END}")
                print(f"     {Colors.DIM}Seen: {s.occurrences} times in this project{Colors.END}")
                print(f"     {Colors.DIM}→ Section: {s.suggested_section}{Colors.END}")
                print(f"     {Colors.DIM}Confidence: {s.confidence:.0%}{Colors.END}")
                print()

    print(f"{Colors.DIM}Total suggestions: {report.total_suggestions}{Colors.END}")
    print(f"\n{Colors.DIM}Run with --apply to interactively add suggestions{Colors.END}")


def is_suggestion_already_applied(suggestion) -> bool:
    """Check if a suggestion (or similar) already exists in the target file."""
    try:
        target_path = Path(suggestion.target_file.replace("~", str(Path.home())))
        if not target_path.exists():
            return False

        content = target_path.read_text(encoding="utf-8").lower()
        instruction_lower = suggestion.instruction.lower()

        # Extract key words (4+ chars) for fuzzy matching
        key_words = [w for w in instruction_lower.split() if len(w) >= 4]

        # If 70%+ of key words are present, consider it already applied
        if key_words:
            matches = sum(1 for w in key_words if w in content)
            match_ratio = matches / len(key_words)
            if match_ratio >= 0.7:
                return True

        return False
    except (OSError, UnicodeDecodeError):
        return False


def interactive_apply(report):
    """Interactive mode to apply suggestions one by one."""
    if not report.has_suggestions:
        print(f"\n{Colors.DIM}No suggestions to apply.{Colors.END}")
        return

    print(f"\n{Colors.BOLD}{Colors.CYAN}📝 CLAUDE.md Suggestion Engine - Interactive Mode{Colors.END}")
    print(f"{Colors.DIM}(Claude-analyzed suggestions from your session history){Colors.END}\n")

    all_suggestions = report.get_all_suggestions()
    applied_count = 0
    skipped_count = 0
    already_applied_count = 0

    for i, s in enumerate(all_suggestions, 1):
        # Check if already applied (deduplication)
        if is_suggestion_already_applied(s):
            already_applied_count += 1
            continue

        scope_color = Colors.GREEN if s.scope == SuggestionScope.GLOBAL else Colors.YELLOW
        scope_label = "GLOBAL" if s.scope == SuggestionScope.GLOBAL else "PROJECT"

        print(f"\n{Colors.BOLD}[{i}/{len(all_suggestions)}]{Colors.END} {scope_color}[{scope_label}]{Colors.END}")
        print(f"  {Colors.BOLD}{s.instruction}{Colors.END}")
        print(f"  {Colors.DIM}Target: {s.target_file}{Colors.END}")
        print(f"  {Colors.DIM}Section: {s.suggested_section}{Colors.END}")
        print(f"  {Colors.DIM}Confidence: {s.confidence:.0%}{Colors.END}")

        while True:
            response = input(f"{Colors.CYAN}[a]dd / [e]dit / [s]kip / [v]iew / [q]uit: {Colors.END}").strip().lower()

            if response == "a":
                if apply_suggestion(s):
                    applied_count += 1
                    print(f"  {Colors.GREEN}✓ Added to {s.target_file}{Colors.END}")
                else:
                    print(f"  {Colors.RED}✗ Failed to apply (file may not exist){Colors.END}")
                break

            elif response == "e":
                print(f"  {Colors.DIM}Edit instruction (Enter to keep current, or type new):{Colors.END}")
                try:
                    edited = input("  > ").strip()
                    if edited:
                        s.instruction = edited
                    if apply_suggestion(s):
                        applied_count += 1
                        label = "(edited) " if edited else ""
                        print(f"  {Colors.GREEN}✓ Added {label}to {s.target_file}{Colors.END}")
                    else:
                        print(f"  {Colors.RED}✗ Failed to apply (file may not exist){Colors.END}")
                except (EOFError, KeyboardInterrupt):
                    print(f"\n  {Colors.DIM}Edit cancelled{Colors.END}")
                    continue
                break

            elif response == "s":
                skipped_count += 1
                print(f"  {Colors.DIM}Skipped{Colors.END}")
                break

            elif response == "v":
                print(f"\n  {Colors.BOLD}Details:{Colors.END}")
                print(f"    Analysis: {s.pattern_type}")
                if s.projects:
                    print(f"    Projects: {', '.join(s.projects[:5])}")
                print(f"    Target file: {s.target_file}")

            elif response == "q":
                print(f"\n{Colors.DIM}Quit. Applied {applied_count}, skipped {skipped_count}.{Colors.END}")
                return

            else:
                print(f"  {Colors.DIM}Invalid option. Use a/e/s/v/q.{Colors.END}")

    # Summary
    if already_applied_count > 0:
        print(f"\n{Colors.DIM}Skipped {already_applied_count} already-applied suggestion(s).{Colors.END}")
    print(f"{Colors.GREEN}Done!{Colors.END} Applied {applied_count}, skipped {skipped_count}.")


def apply_suggestion(suggestion) -> bool:
    """Apply a suggestion to the target file."""
    try:
        # Expand ~ in path
        target_path = Path(suggestion.target_file.replace("~", str(Path.home())))

        if not target_path.exists():
            logger.warning(f"Target file does not exist: {target_path}")
            return False

        content = target_path.read_text(encoding="utf-8")

        # Find the section or add at end
        section = suggestion.suggested_section
        instruction = f"- {suggestion.instruction}"

        if section in content:
            # Find the section and add after its header
            section_idx = content.find(section)
            # Find the next newline after section header
            newline_idx = content.find("\n", section_idx)
            if newline_idx != -1:
                # Insert the instruction after the section header
                content = (
                    content[:newline_idx + 1]
                    + f"{instruction}\n"
                    + content[newline_idx + 1:]
                )
        else:
            # Add new section before the last --- divider or at end
            divider_idx = content.rfind("\n---\n")
            if divider_idx != -1:
                content = (
                    content[:divider_idx]
                    + f"\n{section}\n{instruction}\n"
                    + content[divider_idx:]
                )
            else:
                content += f"\n\n{section}\n{instruction}\n"

        target_path.write_text(content, encoding="utf-8")
        return True

    except Exception as e:
        logger.error(f"Failed to apply suggestion: {e}")
        return False


def output_json(report):
    """Output report as JSON."""
    output = {
        "timestamp": report.timestamp.isoformat(),
        "analysis_period_days": report.analysis_period_days,
        "sessions_analyzed": report.sessions_analyzed,
        "total_suggestions": report.total_suggestions,
        "pipeline": "two-stage (regex + claude)",
        "global_suggestions": [
            {
                "instruction": s.instruction,
                "target_file": s.target_file,
                "suggested_section": s.suggested_section,
                "occurrences": s.occurrences,
                "projects": s.projects,
                "confidence": s.confidence,
            }
            for s in report.global_suggestions
        ],
        "project_suggestions": {
            project: [
                {
                    "instruction": s.instruction,
                    "target_file": s.target_file,
                    "suggested_section": s.suggested_section,
                    "occurrences": s.occurrences,
                    "confidence": s.confidence,
                }
                for s in suggestions
            ]
            for project, suggestions in report.project_suggestions.items()
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
