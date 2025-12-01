"""
Adaptive System Engine - Central coordinator for all learning components.
Orchestrates permission learning, MCP optimization, context tuning, and meta-learning.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from claude_automation.analyzers import (
    ApprovalTracker,
    ContextOptimizer,
    ContextUsageTracker,
    GlobalMCPAnalyzer,
    InstructionEffectivenessTracker,
    MetaLearner,
    PermissionPatternDetector,
    ProjectArchetypeDetector,
    WorkflowDetector,
)
from claude_automation.analyzers.health_checker import create_default_health_checker
from claude_automation.core.improvement_applicator import ImprovementApplicator
from claude_automation.core.interactive_approval_ui import InteractiveApprovalUI
from claude_automation.generators import IntelligentPermissionsGenerator
from claude_automation.schemas import AdaptiveSystemConfig, LearningReport

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

        # Initialize UI handler
        self.ui = InteractiveApprovalUI()

        # Initialize improvement applicator
        self.applicator = ImprovementApplicator(meta_learner=self.meta_learner)

        # Initialize health checker
        self.health_checker = create_default_health_checker()

        logger.info("Adaptive System Engine initialized")

    def run_full_learning_cycle(
        self, interactive: bool | None = None, components: list[str] | None = None
    ) -> LearningReport:
        """
        Run complete learning cycle across all components.

        Called by ./rebuild-nixos as final step.

        Args:
            interactive: Override interactive mode (default: use config)
            components: Optional list of components to run (default: all)

        Returns:
            LearningReport with all suggestions
        """
        # Override config if parameters provided
        if interactive is not None:
            original_interactive = self.config.interactive
            self.config.interactive = interactive

        logger.info("🧠 Starting adaptive learning cycle...")

        # Phase 0: Health Check - Validate analyzer prerequisites
        health_report = self.health_checker.check_all_analyzers()

        if health_report.failed_count > 0 or health_report.degraded_count > 0:
            print("\n⚠️  Warning: Some analyzers have issues")
            print(
                f"   • Healthy: {health_report.healthy_count}/{health_report.total_analyzers}"
            )
            if health_report.degraded_count > 0:
                print(f"   • Degraded: {health_report.degraded_count} (missing data)")
            if health_report.failed_count > 0:
                print(
                    f"   • Failed: {health_report.failed_count} (configuration errors)"
                )

            # Show brief details for unhealthy analyzers
            for status in health_report.analyzer_statuses:
                if not status.is_healthy:
                    print(f"   • {status.analyzer_name}: {status.status_message}")
                    if status.missing_prerequisites:
                        print(
                            f"     Missing: {', '.join(status.missing_prerequisites)}"
                        )

            print(
                "\n💡 Some suggestions may be limited. Continuing with available analyzers...\n"
            )
            logger.warning(
                f"Analyzer health: {health_report.health_percentage:.0f}% ({health_report.healthy_count}/{health_report.total_analyzers} healthy)"
            )
        else:
            logger.debug(
                f"All analyzers healthy ({health_report.total_analyzers}/{health_report.total_analyzers})"
            )

        # Phase 1: Collect insights from all learners
        # If components filter provided, only run specified components
        all_components = {
            "permission_learning": self._analyze_permissions,
            "mcp_optimization": self._analyze_mcp_servers,
            "context_optimization": self._analyze_context,
            "workflow_detection": self._analyze_workflows,
            "instruction_tracking": self._analyze_instructions,
            "cross_project": self._analyze_cross_project,
            "meta_learning": self._analyze_meta_learning,
        }

        # Determine which components to run
        if components:
            # Run only specified components in parallel
            tasks_to_run = []
            for comp_name in components:
                if comp_name in all_components:
                    tasks_to_run.append((comp_name, all_components[comp_name]))

            # Execute in parallel
            results = self._run_analyzers_parallel(tasks_to_run)

            # Unpack results
            permission_patterns = results.get("permission_learning", [])
            mcp_suggestions = results.get("mcp_optimization", [])
            context_suggestions = results.get("context_optimization", [])
            workflow_patterns = results.get("workflow_detection", [])
            instruction_improvements = results.get("instruction_tracking", [])
            cross_project_patterns = results.get("cross_project", [])
            meta_insights = results.get("meta_learning", {})
        else:
            # Run all components in parallel (saves ~1.5-2s)
            tasks_to_run = [
                ("permission_learning", self._analyze_permissions),
                ("mcp_optimization", self._analyze_mcp_servers),
                ("context_optimization", self._analyze_context),
                ("workflow_detection", self._analyze_workflows),
                ("instruction_tracking", self._analyze_instructions),
                ("cross_project", self._analyze_cross_project),
                ("meta_learning", self._analyze_meta_learning),
            ]

            # Execute in parallel
            results = self._run_analyzers_parallel(tasks_to_run)

            # Unpack results
            permission_patterns = results.get("permission_learning", [])
            mcp_suggestions = results.get("mcp_optimization", [])
            context_suggestions = results.get("context_optimization", [])
            workflow_patterns = results.get("workflow_detection", [])
            instruction_improvements = results.get("instruction_tracking", [])
            cross_project_patterns = results.get("cross_project", [])
            meta_insights = results.get("meta_learning", {})

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
            self.ui.present_report(report)
            approved = self.ui.collect_approvals(report)
            self.applicator.apply_improvements(approved)

        # Phase 4: Update meta-learning
        if self.config.enable_meta_learning:
            self.applicator.update_meta_learning(report, approved)

        # Restore original interactive setting if it was overridden
        if interactive is not None:
            self.config.interactive = original_interactive

        logger.info("✅ Learning cycle complete")
        return report

    def _run_analyzers_parallel(
        self, tasks: list[tuple[str, callable]]
    ) -> dict[str, any]:
        """
        Run multiple analyzer methods in parallel.

        Args:
            tasks: List of (component_name, analyzer_function) tuples

        Returns:
            Dictionary mapping component names to their results

        Performance: Saves ~1.5-2s by running analyzers concurrently instead of sequentially
        """
        results = {}

        # Use ThreadPoolExecutor to run analyzers in parallel
        # max_workers=7 allows all analyzers to run concurrently
        with ThreadPoolExecutor(max_workers=min(len(tasks), 7)) as executor:
            # Submit all tasks
            future_to_component = {
                executor.submit(analyzer_func): component_name
                for component_name, analyzer_func in tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_component):
                component_name = future_to_component[future]
                try:
                    result = future.result()
                    results[component_name] = result
                    logger.debug(f"✓ {component_name} analysis complete")
                except Exception as e:
                    logger.error(f"✗ {component_name} analysis failed: {e}")
                    # Return empty result on failure (maintains compatibility)
                    results[component_name] = (
                        [] if component_name != "meta_learning" else {}
                    )

        return results

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
            for rec in report.recommendations[
                : self.config.max_suggestions_per_component
            ]:
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

    def _analyze_instructions(self) -> list:
        """Find low-effectiveness instructions needing improvement."""
        try:
            # TODO: Calculate actual session count from logs
            total_sessions = 10  # Placeholder

            improvements = self.instruction_tracker.suggest_improvements(
                total_sessions=total_sessions,
                days=self.config.analysis_period_days,
                min_violations=3,
            )

            # Return full InstructionImprovement objects (maintain type safety)
            return improvements[: self.config.max_suggestions_per_component]
        except Exception as e:
            logger.error(f"Instruction analysis failed: {e}")
            return []

    def _analyze_cross_project(self) -> list:
        """Identify cross-project pattern transfer opportunities."""
        try:
            transfers = self.archetype_detector.find_transfer_opportunities()

            # Return full TransferSuggestion objects (maintain type safety)
            return transfers[: self.config.max_suggestions_per_component]
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
            permission_patterns=permissions,  # Pass actual dicts
            mcp_optimizations=mcp,
            context_suggestions=context,  # Pass actual dicts
            workflow_patterns=workflows,  # Pass actual dicts
            instruction_improvements=instructions,  # Pass actual dicts
            cross_project_transfers=cross_project,  # Pass actual dicts
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
