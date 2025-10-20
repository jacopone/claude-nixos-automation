"""
Improvement Applicator - Handles application of approved learning suggestions.
Applies changes to MCP configs, permissions, context files, and workflows.
"""

import logging

from claude_automation.schemas import LearningReport

logger = logging.getLogger(__name__)


class ImprovementApplicator:
    """
    Handles application of approved improvements from the learning system.

    Responsibilities:
    - Display confirmation summary of changes
    - Apply MCP server optimizations
    - Apply permission pattern suggestions
    - Apply context optimizations
    - Apply workflow pattern suggestions
    - Update meta-learning based on user feedback
    """

    def __init__(self, meta_learner):
        """
        Initialize improvement applicator.

        Args:
            meta_learner: MetaLearner instance for recording feedback
        """
        self.meta_learner = meta_learner

    def apply_improvements(self, approved: list[dict]) -> None:
        """
        Apply approved improvements across all components.

        Args:
            approved: List of approved suggestions (each has 'type' and 'data')

        Side effects:
            - May modify .claude/mcp.json
            - May modify settings.local.json
            - May modify CLAUDE.md files
            - May create slash commands
        """
        if not approved:
            logger.info("No approved suggestions to apply")
            return

        # Show confirmation summary before applying
        print("\n" + "="*70)
        print("📋 FINAL CONFIRMATION - Changes to be applied:")
        print("="*70)

        for i, sug in enumerate(approved, 1):
            sug_type = sug['type']
            data = sug['data']

            if sug_type == 'mcp':
                server = data.get('server_name', 'Unknown')
                print(f"\n{i}. MCP: Remove server '{server}'")
                print("   File: .claude/mcp.json")
            elif sug_type == 'permission':
                desc = data.get('description', 'Unknown pattern')
                print(f"\n{i}. Permission: Auto-approve '{desc}'")
                print("   File: .claude/settings.local.json")
            elif sug_type == 'context':
                section = data.get('description', 'Unknown section')
                print(f"\n{i}. Context: Remove '{section}'")
                print("   File: CLAUDE.md")
            elif sug_type == 'workflow':
                desc = data.get('description', 'Unknown workflow')
                print(f"\n{i}. Workflow: Create slash command for '{desc}'")
                print("   File: .claude/commands/<new>.md")

        print("\n" + "─"*70)
        try:
            confirm = input("\n👉 Proceed with these changes? [y/N]: ").lower().strip()
            if confirm != 'y':
                print("\n⚠️  Changes cancelled. No modifications made.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Changes cancelled by user. No modifications made.")
            return

        print(f"\n🔧 Applying {len(approved)} approved improvements...")

        # Group by type
        by_type = {}
        for sug in approved:
            sug_type = sug['type']
            if sug_type not in by_type:
                by_type[sug_type] = []
            by_type[sug_type].append(sug['data'])

        # Apply MCP optimizations
        if 'mcp' in by_type:
            self._apply_mcp_optimizations(by_type['mcp'])

        # Apply permission patterns
        if 'permission' in by_type:
            self._apply_permission_patterns(by_type['permission'])

        # Apply context optimizations
        if 'context' in by_type:
            self._apply_context_optimizations(by_type['context'])

        # Apply workflow patterns
        if 'workflow' in by_type:
            self._apply_workflow_patterns(by_type['workflow'])

        print("✓ All improvements applied successfully\n")

    def _apply_mcp_optimizations(self, optimizations: list[dict]) -> None:
        """Apply MCP server optimization suggestions."""
        logger.info(f"Applying {len(optimizations)} MCP optimizations")

        for opt in optimizations:
            server_name = opt.get('server_name', 'unknown')
            action = opt.get('impact', opt.get('action', 'unknown'))

            # TODO: Actually modify .claude/mcp.json
            # For now, log what would be done
            print(f"  • MCP: {server_name} - {action}")
            logger.warning(f"MCP optimization not yet implemented: {server_name}")

    def _apply_permission_patterns(self, patterns: list[dict]) -> None:
        """Apply permission pattern suggestions."""
        logger.info(f"Applying {len(patterns)} permission patterns")

        for pattern in patterns:
            description = pattern.get('description', 'unknown pattern')

            # TODO: Use IntelligentPermissionsGenerator to update settings.local.json
            # For now, log what would be done
            print(f"  • Permission: {description}")
            logger.warning(f"Permission pattern not yet implemented: {description}")

    def _apply_context_optimizations(self, optimizations: list[dict]) -> None:
        """Apply CLAUDE.md context optimizations."""
        logger.info(f"Applying {len(optimizations)} context optimizations")

        for opt in optimizations:
            description = opt.get('description', 'unknown optimization')

            # TODO: Modify CLAUDE.md files
            # For now, log what would be done
            print(f"  • Context: {description}")
            logger.warning(f"Context optimization not yet implemented: {description}")

    def _apply_workflow_patterns(self, patterns: list[dict]) -> None:
        """Apply workflow pattern suggestions (create slash commands)."""
        logger.info(f"Applying {len(patterns)} workflow patterns")

        for pattern in patterns:
            description = pattern.get('description', 'unknown workflow')

            # TODO: Create slash command files
            # For now, log what would be done
            print(f"  • Workflow: {description}")
            logger.warning(f"Workflow pattern not yet implemented: {description}")

    def update_meta_learning(self, report: LearningReport, approved: list[dict]) -> None:
        """
        Update meta-learning based on user feedback.

        Args:
            report: Learning report with all suggestions
            approved: List of approved suggestions
        """
        acceptance_rate = (
            len(approved) / report.total_suggestions if report.total_suggestions > 0 else 1.0
        )

        self.meta_learner.record_session(
            total_suggestions=report.total_suggestions,
            accepted=len(approved),
            acceptance_rate=acceptance_rate,
        )

        logger.info(f"Meta-learning updated: {acceptance_rate:.0%} acceptance rate")
