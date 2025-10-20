---
status: active
created: 2025-10-17
updated: 2025-10-17
type: reference
lifecycle: persistent
---

# AdaptiveSystemEngine Contract

Interface contract for the adaptive system orchestration engine.

**Purpose**: Define the contract for the central coordinator that runs all 8 learning analyzers and consolidates their suggestions into a unified learning report.

---

## Engine Interface

**Module**: `claude_automation/core/adaptive_system_engine.py`

```python
class AdaptiveSystemEngine:
    """Orchestrates all learning components in the self-improving system.

    Responsibilities:
    1. Initialize and manage 8 learning analyzers
    2. Run full learning cycle on demand (e.g., during rebuild)
    3. Consolidate suggestions from all analyzers
    4. Present unified report to user
    5. Collect user approvals
    6. Apply approved improvements
    7. Feed results back to meta-learner
    """

    def __init__(self, config: AdaptiveSystemConfig):
        """Initialize engine with configuration.

        Args:
            config: Master configuration for adaptive learning system

        Side effects:
            - Initializes all 8 analyzers
            - Loads historical data from ~/.claude/
        """
        self.config = config

        # Tier 1: High-value learning components
        self.approval_tracker = ApprovalTracker()
        self.permission_detector = PermissionPatternDetector(
            self.approval_tracker, config
        )
        self.mcp_analyzer = GlobalMCPAnalyzer(config)
        self.context_optimizer = ContextOptimizer(config=config)

        # Tier 2: Medium-value learning components
        self.workflow_detector = WorkflowDetector(config=config)
        self.instruction_tracker = InstructionTracker(config=config)

        # Tier 3: Advanced learning components
        self.archetype_detector = ProjectArchetypeDetector(config)
        self.meta_learner = MetaLearner(config=config)

    def run_full_learning_cycle(
        self,
        interactive: bool = True,
        components: Optional[list[str]] = None
    ) -> LearningReport:
        """Run full learning cycle across all enabled components.

        Args:
            interactive: Whether to prompt user for approvals
            components: Specific components to run (None = all enabled)

        Returns:
            LearningReport with suggestions from all analyzers

        Steps:
        1. Run enabled analyzers in parallel (where possible)
        2. Build consolidated report
        3. If interactive: present report and collect approvals
        4. Apply approved improvements
        5. Update meta-learning metrics

        Performance:
        - Target: <10s for full cycle
        - Parallelization: Run independent analyzers concurrently
        """
        report = self._build_report(components)

        if interactive:
            self._present_report(report)
            approvals = self._collect_approvals(report)
            self._apply_improvements(approvals)
            self._update_meta_learning(report, approvals)

        return report

    def run_single_component(
        self,
        component: str,
        interactive: bool = True
    ) -> list[Any]:
        """Run a single learning component.

        Args:
            component: Component name (e.g., "permission_learning", "mcp_optimization")
            interactive: Whether to prompt user for approvals

        Returns:
            List of suggestions from that component

        Raises:
            ValueError: If component name invalid or not enabled
        """
        ...

    def get_system_health(self) -> LearningHealthReport:
        """Get overall system health from meta-learner.

        Returns:
            Health report with metrics for all components
        """
        return self.meta_learner.get_health_report()

    # Private orchestration methods

    def _build_report(
        self,
        components: Optional[list[str]] = None
    ) -> LearningReport:
        """Build consolidated report from all analyzers.

        Steps:
        1. Run each enabled analyzer
        2. Collect suggestions
        3. Prioritize by confidence and impact
        4. Add meta-learning health metrics

        Returns:
            LearningReport
        """
        report = LearningReport(generated_at=datetime.now())

        # Tier 1: Critical learning components
        if self._should_run("permission_learning", components):
            report.permission_suggestions = self._analyze_permissions()

        if self._should_run("mcp_optimization", components):
            report.mcp_recommendations = self._analyze_mcp_servers()

        if self._should_run("context_optimization", components):
            report.context_optimizations = self._analyze_context()

        # Tier 2: Workflow improvements
        if self._should_run("workflow_detection", components):
            report.workflow_suggestions = self._analyze_workflows()

        if self._should_run("instruction_tracking", components):
            report.instruction_improvements = self._analyze_instructions()

        # Tier 3: Advanced learning
        if self._should_run("cross_project_learning", components):
            report.transfer_suggestions = self._analyze_cross_project()

        # Meta-learning (always run)
        if self._should_run("meta_learning", components):
            report.learning_health = self._analyze_meta_learning()

        return report

    def _analyze_permissions(self) -> list[PatternSuggestion]:
        """Run permission pattern detection."""
        try:
            return self.permission_detector.analyze()
        except Exception as e:
            logger.error(f"Permission analysis failed: {e}")
            return []

    def _analyze_mcp_servers(self) -> list[MCPUsageRecommendation]:
        """Run global MCP usage analysis."""
        try:
            return self.mcp_analyzer.analyze()
        except Exception as e:
            logger.error(f"MCP analysis failed: {e}")
            return []

    def _analyze_context(self) -> list[ContextOptimization]:
        """Run context optimization analysis."""
        try:
            return self.context_optimizer.analyze()
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return []

    def _analyze_workflows(self) -> list[WorkflowSuggestion]:
        """Run workflow pattern detection."""
        try:
            return self.workflow_detector.analyze()
        except Exception as e:
            logger.error(f"Workflow analysis failed: {e}")
            return []

    def _analyze_instructions(self) -> list[InstructionImprovement]:
        """Run instruction effectiveness analysis."""
        try:
            return self.instruction_tracker.analyze()
        except Exception as e:
            logger.error(f"Instruction analysis failed: {e}")
            return []

    def _analyze_cross_project(self) -> list[TransferSuggestion]:
        """Run cross-project pattern transfer."""
        try:
            return self.archetype_detector.analyze()
        except Exception as e:
            logger.error(f"Cross-project analysis failed: {e}")
            return []

    def _analyze_meta_learning(self) -> LearningHealthReport:
        """Run meta-learning health check."""
        try:
            return self.meta_learner.get_health_report()
        except Exception as e:
            logger.error(f"Meta-learning analysis failed: {e}")
            return LearningHealthReport(overall_health="unknown")

    def _present_report(self, report: LearningReport) -> None:
        """Present learning report to user.

        Format:
        - Use colored output (rich library)
        - Group by component
        - Show confidence scores
        - Highlight high-impact suggestions
        """
        ...

    def _collect_approvals(
        self,
        report: LearningReport
    ) -> dict[str, list[str]]:
        """Collect user approvals for suggestions.

        Args:
            report: Learning report with suggestions

        Returns:
            Map of component → list of approved suggestion IDs

        Interactive prompts:
        - Show each suggestion with context
        - Ask: "Apply this suggestion? (y/n/skip-component)"
        - Support bulk approval: "Apply all low-risk? (y/n)"
        """
        ...

    def _apply_improvements(
        self,
        approvals: dict[str, list[str]]
    ) -> None:
        """Apply approved improvements.

        Args:
            approvals: Map of component → approved suggestion IDs

        Side effects:
        - May modify settings.local.json
        - May modify CLAUDE.md files
        - May create slash commands
        - May modify .claude/mcp.json
        """
        ...

    def _update_meta_learning(
        self,
        report: LearningReport,
        approvals: dict[str, list[str]]
    ) -> None:
        """Update meta-learner with suggestion outcomes.

        Args:
            report: Full learning report
            approvals: User approval decisions

        Side effects:
        - Logs acceptance/rejection to meta-learning data
        - Updates component effectiveness metrics
        """
        for component, suggestions in self._get_all_suggestions(report).items():
            for suggestion in suggestions:
                suggestion_id = self._get_suggestion_id(suggestion)
                accepted = suggestion_id in approvals.get(component, [])
                self.meta_learner.track_suggestion_outcome(
                    component, suggestion_id, accepted
                )

    def _should_run(
        self,
        component: str,
        components: Optional[list[str]]
    ) -> bool:
        """Check if component should run.

        Returns:
            True if component is enabled and (components is None or component in components)
        """
        if not self._is_component_enabled(component):
            return False

        if components is None:
            return True

        return component in components

    def _is_component_enabled(self, component: str) -> bool:
        """Check if component is enabled in config."""
        component_flags = {
            "permission_learning": self.config.permission_learning_enabled,
            "mcp_optimization": self.config.mcp_optimization_enabled,
            "context_optimization": self.config.context_optimization_enabled,
            "workflow_detection": self.config.workflow_detection_enabled,
            "instruction_tracking": self.config.instruction_tracking_enabled,
            "cross_project_learning": self.config.cross_project_learning_enabled,
            "meta_learning": self.config.meta_learning_enabled,
        }
        return component_flags.get(component, False)
```

---

## CLI Interface

**Module**: `scripts/run-adaptive-learning.py`

```python
#!/usr/bin/env python3
"""Run adaptive learning cycle."""

import argparse
from claude_automation.core.adaptive_system_engine import AdaptiveSystemEngine
from claude_automation.schemas import AdaptiveSystemConfig

def main():
    parser = argparse.ArgumentParser(
        description="Run Claude Code adaptive learning cycle"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Prompt for approval before applying changes"
    )
    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Run without user interaction (dry-run mode)"
    )
    parser.add_argument(
        "--components",
        nargs="+",
        choices=[
            "permission_learning",
            "mcp_optimization",
            "context_optimization",
            "workflow_detection",
            "instruction_tracking",
            "cross_project_learning",
            "meta_learning"
        ],
        help="Run specific components only (default: all enabled)"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Show system health report and exit"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Load config
    config = AdaptiveSystemConfig()  # Uses defaults from ~/.claude/config.yaml

    # Initialize engine
    engine = AdaptiveSystemEngine(config)

    # Health check mode
    if args.health:
        health = engine.get_system_health()
        print_health_report(health)
        return

    # Run learning cycle
    print("Running adaptive learning cycle...")
    report = engine.run_full_learning_cycle(
        interactive=args.interactive,
        components=args.components
    )

    # Summary
    print("\nLearning Cycle Complete!")
    print_summary(report)

if __name__ == "__main__":
    main()
```

**Usage examples**:

```bash
# Interactive mode (default)
python run-adaptive-learning.py --interactive

# Dry-run mode (no changes)
python run-adaptive-learning.py --no-interactive

# Run specific components
python run-adaptive-learning.py --components permission_learning mcp_optimization

# Health check
python run-adaptive-learning.py --health

# Verbose output
python run-adaptive-learning.py --verbose
```

---

## Rebuild Integration

**Integration point**: `~/nixos-config/rebuild-nixos`

```bash
# After successful rebuild, run learning cycle
if command -v python3 &> /dev/null; then
    if [ -f ~/claude-nixos-automation/scripts/run-adaptive-learning.py ]; then
        echo ""
        echo "Running adaptive learning cycle..."
        python3 ~/claude-nixos-automation/scripts/run-adaptive-learning.py --interactive
    fi
fi
```

**User experience**:
1. User runs `./rebuild-nixos`
2. System rebuilds NixOS configuration
3. If rebuild succeeds: learning cycle runs
4. User sees suggestions and can approve/reject
5. Approved changes applied immediately
6. Next rebuild uses improved configuration

---

## Testing Contract

### 1. Full Cycle Integration Test

```python
def test_full_learning_cycle():
    """Test complete learning cycle end-to-end."""
    config = AdaptiveSystemConfig()
    engine = AdaptiveSystemEngine(config)

    # Run cycle (non-interactive)
    report = engine.run_full_learning_cycle(interactive=False)

    # Verify report structure
    assert isinstance(report, LearningReport)
    assert report.generated_at is not None
    assert isinstance(report.permission_suggestions, list)
    assert isinstance(report.mcp_recommendations, list)
    # ... etc for all components
```

### 2. Component Isolation Test

```python
def test_component_runs_independently():
    """Verify each component can run in isolation."""
    config = AdaptiveSystemConfig()
    engine = AdaptiveSystemEngine(config)

    # Run each component individually
    for component in [
        "permission_learning",
        "mcp_optimization",
        "context_optimization",
        "workflow_detection",
        "instruction_tracking",
        "cross_project_learning",
        "meta_learning"
    ]:
        result = engine.run_single_component(component, interactive=False)
        assert isinstance(result, list)
```

### 3. Error Handling Test

```python
def test_engine_handles_analyzer_failures():
    """Verify engine handles analyzer failures gracefully."""
    config = AdaptiveSystemConfig()
    engine = AdaptiveSystemEngine(config)

    # Inject failing analyzer
    engine.permission_detector.analyze = Mock(side_effect=Exception("Test error"))

    # Should not crash, should return partial report
    report = engine.run_full_learning_cycle(interactive=False)
    assert report is not None
    assert len(report.permission_suggestions) == 0  # Failed component returns empty
```

### 4. Performance Test

```python
def test_full_cycle_performance():
    """Verify full cycle completes within time budget."""
    config = AdaptiveSystemConfig()
    engine = AdaptiveSystemEngine(config)

    start = time.time()
    report = engine.run_full_learning_cycle(interactive=False)
    duration = time.time() - start

    assert duration < 10.0, f"Full cycle took {duration:.2f}s, budget is 10s"
```

---

## Contract Guarantees

The AdaptiveSystemEngine MUST guarantee:

1. **Backward Compatibility**: System works without learning enabled
2. **Graceful Degradation**: If analyzer fails, others continue
3. **User Control**: Interactive mode always asks before changes
4. **Dry-Run Safety**: Non-interactive mode never modifies files
5. **Performance**: Full cycle <10s
6. **Idempotency**: Running twice with no approvals is safe
7. **Transactional**: Either all approved changes apply, or none
8. **Auditability**: All decisions logged for meta-learning

---

## Extension Points

To add a new learning component:

1. Implement analyzer following `BaseAnalyzer` protocol (see `contracts/analyzers.md`)
2. Add to `AdaptiveSystemEngine.__init__()`:
   ```python
   self.my_new_analyzer = MyNewAnalyzer(config)
   ```
3. Add analysis method:
   ```python
   def _analyze_my_component(self) -> list[MySuggestion]:
       return self.my_new_analyzer.analyze()
   ```
4. Add to `_build_report()`:
   ```python
   if self._should_run("my_component", components):
       report.my_suggestions = self._analyze_my_component()
   ```
5. Add config flag:
   ```python
   # In AdaptiveSystemConfig
   my_component_enabled: bool = True
   ```
6. Add CLI option:
   ```python
   # In run-adaptive-learning.py
   choices=["permission_learning", ..., "my_component"]
   ```

---

*Last updated: 2025-10-17 (Phase 2 completion)*
