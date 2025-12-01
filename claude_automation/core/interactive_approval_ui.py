"""
Interactive approval UI for the adaptive learning system.
Handles user interaction for reviewing and approving suggested optimizations.
"""

import logging
from typing import Any

from claude_automation.schemas import LearningReport

logger = logging.getLogger(__name__)


class InteractiveApprovalUI:
    """
    Handles interactive presentation and approval collection for learning suggestions.

    Responsibilities:
    - Present learning reports to users
    - Collect approval decisions for suggestions
    - Display detailed information about each suggestion
    - Handle user input validation and error handling
    """

    def present_report(self, report: LearningReport) -> None:
        """
        Present consolidated learning report to user.

        Args:
            report: Learning report with suggestions from all components
        """
        print("\n" + "=" * 70)
        print("🧠 ADAPTIVE SYSTEM LEARNING REPORT")
        print("=" * 70)

        print(f"\n📊 Total Suggestions: {report.total_suggestions}")
        print(f"📈 Estimated Impact: {report.estimated_improvements}")

        if report.meta_insights:
            health = report.meta_insights.get("system_health", 0.0)
            print(f"\n🔬 System Health: {health:.0%}")

        print("\n" + "=" * 70)

    def collect_approvals(self, report: LearningReport) -> list[dict[str, Any]]:
        """
        Interactively collect user approvals for suggestions.

        Args:
            report: Learning report with suggestions from all components

        Returns:
            List of approved suggestions (dicts with type and details)
        """
        approved = []

        # Collect all suggestions by category
        all_suggestions = []

        # MCP optimizations
        for i, sug in enumerate(report.mcp_optimizations):
            all_suggestions.append(
                {
                    "type": "mcp",
                    "index": i,
                    "data": sug,
                    "description": sug.get("description", "MCP optimization"),
                }
            )

        # Permission patterns
        for i, sug in enumerate(report.permission_patterns):
            all_suggestions.append(
                {
                    "type": "permission",
                    "index": i,
                    "data": sug,
                    "description": sug.get("description", "Permission pattern"),
                }
            )

        # Context optimizations
        for i, sug in enumerate(report.context_suggestions):
            all_suggestions.append(
                {
                    "type": "context",
                    "index": i,
                    "data": sug,
                    "description": sug.get("description", "Context optimization"),
                }
            )

        # Workflow patterns
        for i, sug in enumerate(report.workflow_patterns):
            all_suggestions.append(
                {
                    "type": "workflow",
                    "index": i,
                    "data": sug,
                    "description": sug.get("description", "Workflow pattern"),
                }
            )

        if not all_suggestions:
            return approved

        self._print_review_header(len(all_suggestions))

        try:
            approved = self._review_suggestions(all_suggestions)
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  Interrupted. Saved {len(approved)} approvals.")
            return approved

        print(
            f"\n✓ Review complete. {len(approved)}/{len(all_suggestions)} suggestions approved.\n"
        )
        return approved

    def _print_review_header(self, total: int) -> None:
        """Print header for review process."""
        print("\n" + "=" * 70)
        print("📋 REVIEW SUGGESTIONS")
        print("=" * 70)
        print(f"\nFound {total} optimization suggestions.")
        print("\nOptions:")
        print("  y - Approve this suggestion")
        print("  n - Reject this suggestion")
        print("  a - Approve all remaining")
        print("  s - Skip all remaining")
        print("  q - Quit (save approvals so far)")
        print("")

    def _review_suggestions(
        self, all_suggestions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Review each suggestion and collect approvals.

        Args:
            all_suggestions: List of all suggestions to review

        Returns:
            List of approved suggestions
        """
        approved = []

        for i, sug in enumerate(all_suggestions, 1):
            print(f"\n{'=' * 70}")
            print(
                f"[{i}/{len(all_suggestions)}] {sug['type'].upper()}: {sug['description']}"
            )
            print(f"{'=' * 70}")

            # Display detailed information about the suggestion
            self._display_suggestion_details(sug)

            print(f"\n{'─' * 70}")

            # Get user decision
            decision = self._get_user_decision()

            if decision == "approve":
                approved.append(sug)
                print("  ✓ Approved")
            elif decision == "reject":
                # Log rejection silently
                from claude_automation.analyzers.rejection_tracker import (
                    RejectionTracker,
                )

                tracker = RejectionTracker()
                fingerprint = self._generate_fingerprint(sug)
                tracker.log_rejection(
                    suggestion_type=sug["type"],
                    suggestion_fingerprint=fingerprint,
                    project_path=sug.get("data", {}).get("project_path", ""),
                )
                print("  ✗ Rejected")
            elif decision == "approve_all":
                # Approve this and all remaining
                approved.append(sug)
                approved.extend(all_suggestions[i:])
                print(
                    f"  ✓ Approved all {len(all_suggestions) - i + 1} remaining suggestions"
                )
                return approved
            elif decision == "skip_all":
                # Skip all remaining
                print(f"  Skipped {len(all_suggestions) - i + 1} remaining suggestions")
                return approved
            elif decision == "quit":
                print(f"\n  Saved {len(approved)} approvals. Exiting.")
                return approved

        return approved

    def _get_user_decision(self) -> str:
        """
        Get and validate user decision for a suggestion.

        Returns:
            One of: 'approve', 'reject', 'approve_all', 'skip_all', 'quit'
        """
        while True:
            choice = input("\n👉 Apply this change? [y/n/a/s/q]: ").lower().strip()

            if choice == "y":
                return "approve"
            elif choice == "n":
                return "reject"
            elif choice == "a":
                return "approve_all"
            elif choice == "s":
                return "skip_all"
            elif choice == "q":
                return "quit"
            else:
                print("  Invalid choice. Use y/n/a/s/q")

    def _display_suggestion_details(self, sug: dict[str, Any]) -> None:
        """
        Display detailed information about a suggestion based on its type.

        Args:
            sug: Suggestion dict with type and data
        """
        sug_type = sug["type"]
        data = sug["data"]

        if sug_type == "mcp":
            self._display_mcp_details(data)
        elif sug_type == "permission":
            self._display_permission_details(data)
        elif sug_type == "context":
            self._display_context_details(data)
        elif sug_type == "workflow":
            self._display_workflow_details(data)

    def _display_mcp_details(self, data: dict[str, Any]) -> None:
        """Display details for MCP optimization suggestion."""
        server = data.get("server_name", "Unknown")
        impact = data.get("impact", "No details")
        priority = data.get("priority", "MEDIUM")

        print(f"\n📦 Server: {server}")
        print(f"⚡ Priority: {priority}")
        print(f"💡 Recommendation: {impact}")

        # Show what will be changed
        print("\n📝 What will change:")
        print("   • File: .claude/mcp.json (project-level MCP config)")

        if "never used" in impact.lower() or "remove" in impact.lower():
            print(f"   • Action: Remove '{server}' server entry from config")
            print("   • Result: Server won't load in future sessions")
        elif "move" in impact.lower() or "project-level" in impact.lower():
            print("   • Action: Remove from ~/.claude.json (global config)")
            print("   • Action: Add to .claude/mcp.json (project-specific)")
            print("   • Result: Server only loads in relevant projects")
        else:
            print(f"   • Action: {impact}")

        print("\n⚠️  Consequences:")
        print(f"   • MCP server '{server}' will not be available")
        print("   • Any tools provided by this server will be unavailable")
        print("   • You can manually re-add it later if needed")

        print("\n🔄 How to undo:")
        print("   • Manual: Edit .claude/mcp.json and restore the server")
        print("   • Git: git restore .claude/mcp.json (if changes committed)")

    def _display_permission_details(self, data: dict[str, Any]) -> None:
        """Display details for permission pattern suggestion."""
        examples = data.get("examples", [])
        description = data.get("description", "Unknown pattern")

        print(f"\n🔐 Pattern detected: {description}")
        print("\n📝 What will change:")
        print("   • File: .claude/settings.local.json (security permissions)")
        print("   • Action: Add auto-approval rule for this pattern")

        if examples:
            print("\n📋 Based on these approvals:")
            for ex in examples[:3]:
                print(f"   • {ex}")

        print("\n⚠️  Consequences:")
        print("   • Claude Code won't ask permission for this pattern")
        print("   • Saves time on repetitive approvals")
        print("   • Security: Only approve if you trust this pattern")

        print("\n🔄 How to undo:")
        print("   • Edit .claude/settings.local.json")
        print("   • Remove the corresponding allow pattern")

    def _display_context_details(self, data: dict[str, Any]) -> None:
        """Display details for context optimization suggestion."""
        tokens = data.get("tokens", 0)
        section = data.get("description", "Unknown section")
        reason = data.get("reason", "Not specified")

        print(f"\n📄 Section: {section}")
        print(f"💾 Token savings: ~{tokens}K tokens")
        print(f"📊 Reason: {reason}")

        print("\n📝 What will change:")
        print("   • File: CLAUDE.md or .claude/CLAUDE.md")
        print(f"   • Action: Remove or condense '{section}' section")

        print("\n⚠️  Consequences:")
        print("   • Claude Code won't see this context anymore")
        print("   • Faster responses (less context to process)")
        print("   • Only approve if section is truly unused")

        print("\n🔄 How to undo:")
        print("   • Git: git restore CLAUDE.md")
        print("   • Manual: Re-add the section to CLAUDE.md")

    def _display_workflow_details(self, data: dict[str, Any]) -> None:
        """Display details for workflow pattern suggestion."""
        commands = data.get("commands", [])
        occurrences = data.get("occurrences", 0)

        print(f"\n🔄 Repeated {occurrences} times")
        print("📋 Command sequence:")
        for cmd in commands:
            print(f"   • {cmd}")

        print("\n📝 What will change:")
        print("   • File: .claude/commands/<new-command>.md")
        print("   • Action: Create slash command combining these steps")

        print("\n✅ Benefits:")
        print(f"   • Single command instead of {len(commands)} separate steps")
        print("   • Faster workflow execution")

        print("\n🔄 How to undo:")
        print("   • Delete the .claude/commands/<new-command>.md file")

    def _generate_fingerprint(self, sug: dict[str, Any]) -> str:
        """
        Generate unique fingerprint for suggestion.

        Args:
            sug: Suggestion dict with type and data

        Returns:
            Fingerprint string for matching rejections
        """
        sug_type = sug["type"]
        data = sug["data"]

        if sug_type == "workflow":
            commands = data.get("commands", [])
            return "|".join(commands)
        elif sug_type == "permission":
            pattern = data.get("pattern", {})
            return pattern.get("pattern_type", "unknown")

        return f"{sug_type}:unknown"
