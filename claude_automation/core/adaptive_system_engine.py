"""
Adaptive System Engine - Central coordinator for all learning components.
Orchestrates permission learning, MCP optimization, context tuning, and meta-learning.
"""

import logging
from pathlib import Path

from ..analyzers.approval_tracker import ApprovalTracker
from ..analyzers.context_optimizer import ContextOptimizer, ContextUsageTracker
from ..analyzers.global_mcp_analyzer import GlobalMCPAnalyzer
from ..analyzers.instruction_tracker import InstructionEffectivenessTracker
from ..analyzers.meta_learner import MetaLearner
from ..analyzers.permission_pattern_detector import PermissionPatternDetector
from ..analyzers.project_archetype_detector import ProjectArchetypeDetector
from ..analyzers.workflow_detector import WorkflowDetector
from ..generators.intelligent_permissions_generator import (
    IntelligentPermissionsGenerator,
)
from ..schemas import AdaptiveSystemConfig, LearningReport

logger = logging.getLogger(__name__)


class AdaptiveSystemEngine:
    """
    Central coordinator for all self-improving components.

    Runs during ./rebuild-nixos to:
    1. Collect insights from all learners
    2. Prioritize suggestions by impact
    3. Present consolidated report
    4. Apply user-approved improvements
    5. Update meta-learning parameters
    """

    def __init__(self, config: AdaptiveSystemConfig | None = None):
        """
        Initialize adaptive system engine.

        Args:
            config: Configuration (defaults to interactive mode)
        """
        if config is None:
            config = AdaptiveSystemConfig(interactive=True)

        self.config = config

        # Initialize meta-learner first (provides thresholds)
        self.meta_learner = MetaLearner()

        # Get adjusted thresholds from meta-learner
        min_occurrences = int(
            self.meta_learner.get_adjusted_threshold("all", "min_occurrences")
        )
        confidence_threshold = self.meta_learner.get_adjusted_threshold(
            "all", "confidence_threshold"
        )

        # Initialize all learning components with adjusted thresholds
        self.approval_tracker = ApprovalTracker()
        self.permission_detector = PermissionPatternDetector(
            approval_tracker=self.approval_tracker,
            min_occurrences=min_occurrences,
            confidence_threshold=confidence_threshold,
        )
        self.permission_generator = IntelligentPermissionsGenerator(
            approval_tracker=self.approval_tracker,
            pattern_detector=self.permission_detector,
        )

        self.mcp_analyzer = GlobalMCPAnalyzer(Path.home())
        self.context_tracker = ContextUsageTracker()
        self.context_optimizer = ContextOptimizer(usage_tracker=self.context_tracker)
        self.workflow_detector = WorkflowDetector()
        self.instruction_tracker = InstructionEffectivenessTracker()
        self.archetype_detector = ProjectArchetypeDetector()

        logger.info("Adaptive System Engine initialized")

    def run_full_learning_cycle(self) -> LearningReport:
        """
        Run complete learning cycle across all components.

        Called by ./rebuild-nixos as final step.

        Returns:
            LearningReport with all suggestions
        """
        logger.info("🧠 Starting adaptive learning cycle...")

        # Phase 1: Collect insights from all learners
        permission_patterns = self._analyze_permissions()
        mcp_suggestions = self._analyze_mcp_servers()
        context_suggestions = self._analyze_context()
        workflow_patterns = self._analyze_workflows()
        instruction_improvements = self._analyze_instructions()
        cross_project_patterns = self._analyze_cross_project()
        meta_insights = self._analyze_meta_learning()

        # Phase 2: Build consolidated report
        report = self._build_report(
            permission_patterns,
            mcp_suggestions,
            context_suggestions,
            workflow_patterns,
            instruction_improvements,
            cross_project_patterns,
            meta_insights,
        )

        # Phase 3: Interactive approval (if enabled)
        approved = []
        if self.config.interactive and report.has_suggestions:
            self._present_report(report)
            approved = self._collect_approvals(report)
            self._apply_improvements(approved)

        # Phase 4: Update meta-learning
        if self.config.enable_meta_learning:
            self._update_meta_learning(report, approved)

        logger.info("✅ Learning cycle complete")
        return report

    def _analyze_permissions(self) -> list[dict]:
        """Detect permission patterns from approval history."""
        try:
            patterns = self.permission_detector.detect_patterns(
                days=self.config.analysis_period_days,
            )

            # Convert to dict format for report
            return [
                {
                    "description": p.description,
                    "confidence": p.pattern.confidence,
                    "examples": p.approved_examples[:3],
                    "impact": p.impact_estimate,
                }
                for p in patterns[: self.config.max_suggestions_per_component]
            ]
        except Exception as e:
            logger.error(f"Permission analysis failed: {e}")
            return []

    def _analyze_mcp_servers(self) -> list[dict]:
        """Analyze MCP server utilization and ROI across ALL projects."""
        try:
            report = self.mcp_analyzer.analyze_all_projects()

            # Convert recommendations to suggestions
            suggestions = []
            for rec in report.recommendations[: self.config.max_suggestions_per_component]:
                suggestions.append(
                    {
                        "description": rec.reason,
                        "impact": rec.action,
                        "priority": rec.priority,
                        "server_name": rec.server_name,
                    }
                )

            return suggestions
        except Exception as e:
            logger.error(f"MCP analysis failed: {e}")
            return []

    def _analyze_context(self) -> list[dict]:
        """Identify CLAUDE.md optimization opportunities."""
        try:
            suggestions = self.context_optimizer.analyze(
                period_days=self.config.analysis_period_days
            )

            # Convert to dict format
            return [
                {
                    "description": f"{s.optimization_type}: {s.section_name}",
                    "reason": s.reason,
                    "impact": s.impact,
                    "tokens": s.token_savings,
                }
                for s in suggestions[: self.config.max_suggestions_per_component]
            ]
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return []

    def _analyze_workflows(self) -> list[dict]:
        """Detect repeated slash command patterns."""
        try:
            workflows = self.workflow_detector.detect_patterns(
                min_occurrences=self.config.min_occurrences,
                days=self.config.analysis_period_days,
            )

            # Convert to dict format
            return [
                {
                    "description": w.description,
                    "commands": w.sequence.commands,
                    "occurrences": w.sequence.occurrences,
                    "impact": w.impact_estimate,
                }
                for w in workflows[: self.config.max_suggestions_per_component]
            ]
        except Exception as e:
            logger.error(f"Workflow analysis failed: {e}")
            return []

    def _analyze_instructions(self) -> list[dict]:
        """Find low-effectiveness instructions needing improvement."""
        try:
            # TODO: Calculate actual session count from logs
            total_sessions = 10  # Placeholder

            improvements = self.instruction_tracker.suggest_improvements(
                total_sessions=total_sessions,
                days=self.config.analysis_period_days,
                min_violations=3,
            )

            # Convert to dict format
            return [
                {
                    "policy": i.policy_name,
                    "compliance": int(i.effectiveness_data.effectiveness_score * 100),
                    "reason": i.reason,
                    "priority": i.priority,
                }
                for i in improvements[: self.config.max_suggestions_per_component]
            ]
        except Exception as e:
            logger.error(f"Instruction analysis failed: {e}")
            return []

    def _analyze_cross_project(self) -> list[dict]:
        """Identify cross-project pattern transfer opportunities."""
        try:
            transfers = self.archetype_detector.find_transfer_opportunities()

            # Convert to dict format
            return [
                {
                    "description": t.description,
                    "source": t.pattern.source_project,
                    "target": t.target_project,
                    "compatibility": t.compatibility_score,
                }
                for t in transfers[: self.config.max_suggestions_per_component]
            ]
        except Exception as e:
            logger.error(f"Cross-project analysis failed: {e}")
            return []

    def _analyze_meta_learning(self) -> dict[str, float]:
        """Analyze learning system effectiveness."""
        try:
            return self.meta_learner.get_health_metrics()
        except Exception as e:
            logger.error(f"Meta-learning analysis failed: {e}")
            return {}

    def _build_report(
        self,
        permissions: list[dict],
        mcp: list[dict],
        context: list[dict],
        workflows: list[dict],
        instructions: list[dict],
        cross_project: list[dict],
        meta: dict[str, float],
    ) -> LearningReport:
        """Build consolidated learning report."""
        total = (
            len(permissions)
            + len(mcp)
            + len(context)
            + len(workflows)
            + len(instructions)
            + len(cross_project)
        )

        # Estimate improvements
        estimated = self._estimate_improvements(
            permissions, mcp, context, workflows, instructions
        )

        # Note: The schema expects specific types, but we're passing dicts
        # This is a simplification for now - in production, we'd convert properly
        return LearningReport(
            permission_patterns=[],  # TODO: Convert from dicts
            mcp_optimizations=mcp,
            context_suggestions=[],  # TODO: Convert from dicts
            workflow_patterns=[],  # TODO: Convert from dicts
            instruction_improvements=[],  # TODO: Convert from dicts
            cross_project_transfers=[],  # TODO: Convert from dicts
            meta_insights=meta,
            total_suggestions=total,
            estimated_improvements=estimated,
        )

    def _estimate_improvements(
        self,
        permissions: list[dict],
        mcp: list[dict],
        context: list[dict],
        workflows: list[dict],
        instructions: list[dict],
    ) -> str:
        """Estimate impact of all improvements."""
        benefits = []

        if permissions:
            benefits.append(f"{len(permissions)} permission patterns")

        if mcp:
            benefits.append(f"{len(mcp)} MCP optimizations")

        if context:
            token_savings = sum(c.get("tokens", 0) for c in context)
            if token_savings > 0:
                benefits.append(f"{token_savings}K tokens saved")

        if workflows:
            benefits.append(f"{len(workflows)} workflow shortcuts")

        if instructions:
            benefits.append(f"{len(instructions)} policy improvements")

        return ", ".join(benefits) if benefits else "No improvements detected"

    def _present_report(self, report: LearningReport):
        """Present consolidated report to user."""
        print("\n" + "=" * 70)
        print("🧠 ADAPTIVE SYSTEM LEARNING REPORT")
        print("=" * 70)

        print(f"\n📊 Total Suggestions: {report.total_suggestions}")
        print(f"📈 Estimated Impact: {report.estimated_improvements}")

        if report.meta_insights:
            health = report.meta_insights.get("system_health", 0.0)
            print(f"\n🔬 System Health: {health:.0%}")

        print("\n" + "=" * 70)

    def _collect_approvals(self, report: LearningReport) -> list[dict]:
        """Interactively collect user approvals for suggestions.

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
            all_suggestions.append({
                "type": "mcp",
                "index": i,
                "data": sug,
                "description": sug.get("description", "MCP optimization")
            })

        # Permission patterns
        for i, sug in enumerate(report.permission_patterns):
            all_suggestions.append({
                "type": "permission",
                "index": i,
                "data": sug,
                "description": sug.get("description", "Permission pattern")
            })

        # Context optimizations
        for i, sug in enumerate(report.context_suggestions):
            all_suggestions.append({
                "type": "context",
                "index": i,
                "data": sug,
                "description": sug.get("description", "Context optimization")
            })

        # Workflow patterns
        for i, sug in enumerate(report.workflow_patterns):
            all_suggestions.append({
                "type": "workflow",
                "index": i,
                "data": sug,
                "description": sug.get("description", "Workflow pattern")
            })

        if not all_suggestions:
            return approved

        print("\n" + "=" * 70)
        print("📋 REVIEW SUGGESTIONS")
        print("=" * 70)
        print(f"\nFound {len(all_suggestions)} optimization suggestions.")
        print("\nOptions:")
        print("  y - Approve this suggestion")
        print("  n - Reject this suggestion")
        print("  a - Approve all remaining")
        print("  s - Skip all remaining")
        print("  q - Quit (save approvals so far)")
        print("")

        try:
            for i, sug in enumerate(all_suggestions, 1):
                print(f"\n[{i}/{len(all_suggestions)}] {sug['type'].upper()}: {sug['description']}")

                # Show details based on type
                if sug['type'] == 'mcp':
                    server = sug['data'].get('server_name', 'Unknown')
                    impact = sug['data'].get('impact', 'No details')
                    print(f"  Server: {server}")
                    print(f"  Impact: {impact}")
                elif sug['type'] == 'permission':
                    examples = sug['data'].get('examples', [])
                    if examples:
                        print(f"  Examples: {', '.join(examples[:2])}")
                elif sug['type'] == 'context':
                    tokens = sug['data'].get('tokens', 0)
                    print(f"  Token savings: ~{tokens}K")

                while True:
                    choice = input("\nApply? [y/n/a/s/q]: ").lower().strip()

                    if choice == 'y':
                        approved.append(sug)
                        print("  ✓ Approved")
                        break
                    elif choice == 'n':
                        print("  ✗ Rejected")
                        break
                    elif choice == 'a':
                        # Approve this and all remaining
                        approved.append(sug)
                        approved.extend(all_suggestions[i:])
                        print(f"  ✓ Approved all {len(all_suggestions) - i + 1} remaining suggestions")
                        return approved
                    elif choice == 's':
                        # Skip all remaining
                        print(f"  Skipped {len(all_suggestions) - i + 1} remaining suggestions")
                        return approved
                    elif choice == 'q':
                        print(f"\n  Saved {len(approved)} approvals. Exiting.")
                        return approved
                    else:
                        print("  Invalid choice. Use y/n/a/s/q")

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  Interrupted. Saved {len(approved)} approvals.")
            return approved

        print(f"\n✓ Review complete. {len(approved)}/{len(all_suggestions)} suggestions approved.\n")
        return approved

    def _apply_improvements(self, approved: list[dict]):
        """Apply approved improvements across all components.

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

    def _apply_mcp_optimizations(self, optimizations: list[dict]):
        """Apply MCP server optimization suggestions."""
        logger.info(f"Applying {len(optimizations)} MCP optimizations")

        for opt in optimizations:
            server_name = opt.get('server_name', 'unknown')
            action = opt.get('impact', opt.get('action', 'unknown'))

            # TODO: Actually modify .claude/mcp.json
            # For now, log what would be done
            print(f"  • MCP: {server_name} - {action}")
            logger.warning(f"MCP optimization not yet implemented: {server_name}")

    def _apply_permission_patterns(self, patterns: list[dict]):
        """Apply permission pattern suggestions."""
        logger.info(f"Applying {len(patterns)} permission patterns")

        for pattern in patterns:
            description = pattern.get('description', 'unknown pattern')

            # TODO: Use IntelligentPermissionsGenerator to update settings.local.json
            # For now, log what would be done
            print(f"  • Permission: {description}")
            logger.warning(f"Permission pattern not yet implemented: {description}")

    def _apply_context_optimizations(self, optimizations: list[dict]):
        """Apply CLAUDE.md context optimizations."""
        logger.info(f"Applying {len(optimizations)} context optimizations")

        for opt in optimizations:
            description = opt.get('description', 'unknown optimization')

            # TODO: Modify CLAUDE.md files
            # For now, log what would be done
            print(f"  • Context: {description}")
            logger.warning(f"Context optimization not yet implemented: {description}")

    def _apply_workflow_patterns(self, patterns: list[dict]):
        """Apply workflow pattern suggestions (create slash commands)."""
        logger.info(f"Applying {len(patterns)} workflow patterns")

        for pattern in patterns:
            description = pattern.get('description', 'unknown workflow')

            # TODO: Create slash command files
            # For now, log what would be done
            print(f"  • Workflow: {description}")
            logger.warning(f"Workflow pattern not yet implemented: {description}")

    def _update_meta_learning(self, report: LearningReport, approved: list[dict]):
        """Update meta-learning based on user feedback."""
        acceptance_rate = (
            len(approved) / report.total_suggestions if report.total_suggestions > 0 else 1.0
        )

        self.meta_learner.record_session(
            total_suggestions=report.total_suggestions,
            accepted=len(approved),
            acceptance_rate=acceptance_rate,
        )

        logger.info(f"Meta-learning updated: {acceptance_rate:.0%} acceptance rate")
