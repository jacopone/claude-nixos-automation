---
status: active
created: 2025-10-17
updated: 2025-10-17
type: reference
lifecycle: persistent
---

# Analyzer Contracts

Interface contracts for all 8 learning analyzers in the Self-Improving Claude Code System.

**Purpose**: This document defines the interfaces that all analyzers MUST implement, ensuring consistent integration with the AdaptiveSystemEngine.

---

## Base Analyzer Interface

All analyzers MUST implement this interface (informal protocol, not enforced by inheritance):

```python
class BaseAnalyzer(Protocol):
    """Base protocol for all learning analyzers."""

    def analyze(self) -> list[Suggestion]:
        """Run analysis and return suggestions.

        Returns:
            List of suggestions (type varies by analyzer).
            Returns empty list if no suggestions.

        Raises:
            AnalysisError: If analysis fails critically.
        """
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics for this analyzer.

        Returns:
            Dictionary with at least:
            - 'healthy': bool
            - 'last_run': datetime
            - 'total_suggestions': int
            - 'acceptance_rate': float (if applicable)
        """
        ...
```

---

## 1. ApprovalTracker

**Purpose**: Track permission approval events and provide history for pattern detection.

**Module**: `claude_automation/analyzers/approval_tracker.py`

**Interface**:

```python
class ApprovalTracker:
    """Tracks permission approval events."""

    def __init__(self, log_file: Path = Path.home() / ".claude" / "approval-history.jsonl"):
        """Initialize tracker with log file path."""
        ...

    def log_approval(
        self,
        session_id: str,
        permission_pattern: str,
        project_root: Optional[Path] = None
    ) -> None:
        """Log a permission approval event.

        Args:
            session_id: Claude Code session ID
            permission_pattern: Full permission string (e.g., "Read(//path/**)")
            project_root: Project context (if any)

        Side effects:
            Appends entry to approval-history.jsonl
        """
        ...

    def get_recent_approvals(
        self,
        days: int = 30,
        project_root: Optional[Path] = None
    ) -> list[PermissionApprovalEntry]:
        """Get recent approval entries.

        Args:
            days: Number of days to look back
            project_root: Filter by project (None = all projects)

        Returns:
            List of approval entries, newest first
        """
        ...

    def get_approval_count(self, days: int = 30) -> int:
        """Get total approval count for date range."""
        ...
```

**Data Models**:
- Input: Raw approval events from Claude Code
- Output: `PermissionApprovalEntry` (see data-model.md)

**Storage**: `~/.claude/approval-history.jsonl` (JSONL format)

**Integration**: Called by Claude Code when user approves a permission

---

## 2. PermissionPatternDetector

**Purpose**: Detect permission patterns from approval history and suggest generalizations.

**Module**: `claude_automation/analyzers/permission_pattern_detector.py`

**Interface**:

```python
class PermissionPatternDetector:
    """Detects permission patterns from approval history."""

    def __init__(
        self,
        approval_tracker: ApprovalTracker,
        config: AdaptiveSystemConfig
    ):
        """Initialize detector with approval tracker and config."""
        ...

    def detect_patterns(
        self,
        days: int = 30,
        project_root: Optional[Path] = None
    ) -> list[PermissionPattern]:
        """Detect permission patterns.

        Args:
            days: Analysis window
            project_root: Filter by project (None = all projects)

        Returns:
            List of detected patterns with confidence scores,
            sorted by confidence (highest first)

        Filters:
            - Only patterns with occurrences >= config.min_pattern_occurrences
            - Only patterns with confidence >= config.confidence_threshold
        """
        ...

    def calculate_confidence(
        self,
        pattern: PermissionPattern,
        total_approvals: int
    ) -> float:
        """Calculate confidence score for a pattern.

        Formula:
            confidence = (occurrences / total_approvals) * recency_weight
            recency_weight = 1.0 if last_seen within 7 days else 0.8

        Returns:
            Confidence score [0.0, 1.0]
        """
        ...

    def analyze(self) -> list[PatternSuggestion]:
        """Implement BaseAnalyzer interface."""
        patterns = self.detect_patterns()
        return [self._to_suggestion(p) for p in patterns]

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        return {
            'healthy': True,
            'last_run': datetime.now(),
            'total_patterns': len(self.detect_patterns()),
            'acceptance_rate': self._get_acceptance_rate()
        }
```

**Pattern Types**:
- `git_read_only`: Read-only git access
- `pytest`: Python testing with pytest
- `ruff`: Ruff linter/formatter
- `modern_cli`: Modern CLI tools (bat, eza, rg, etc.)
- `project_full_access`: Full read/write access to project

**Data Models**:
- Input: `PermissionApprovalEntry` (from ApprovalTracker)
- Output: `PatternSuggestion` (see data-model.md)

---

## 3. GlobalMCPAnalyzer

**Purpose**: Analyze MCP server usage across all projects and optimize server configuration.

**Module**: `claude_automation/analyzers/global_mcp_analyzer.py`

**Interface**:

```python
class GlobalMCPAnalyzer:
    """Analyzes MCP server usage across all projects."""

    def __init__(self, config: AdaptiveSystemConfig):
        """Initialize analyzer with config."""
        ...

    def discover_projects(self, search_paths: list[Path]) -> list[Path]:
        """Find all projects with .claude/mcp.json files.

        Args:
            search_paths: Directories to search

        Returns:
            List of project root paths
        """
        ...

    def analyze_all_projects(
        self,
        search_paths: Optional[list[Path]] = None
    ) -> GlobalMCPReport:
        """Analyze MCP usage across all projects.

        Args:
            search_paths: Directories to search (default: [~/projects, ~/nixos-config])

        Returns:
            Full global MCP report with recommendations
        """
        ...

    def calculate_utilization(
        self,
        server_id: str,
        sessions: list[MCPSessionStats]
    ) -> MCPServerSessionUtilization:
        """Calculate utilization metrics for a server.

        Metrics:
        - total_sessions: Times server was loaded
        - sessions_used: Times server was invoked
        - utilization_rate: sessions_used / total_sessions
        - roi_score: invocations / tokens * 1000
        - underutilized: utilization_rate < 0.3
        """
        ...

    def generate_recommendations(
        self,
        report: GlobalMCPReport
    ) -> list[MCPUsageRecommendation]:
        """Generate optimization recommendations.

        Rules:
        - Global server with utilization < 0.3 AND used in <2 projects: remove_global
        - Project server with utilization > 0.7 AND used in >3 projects: promote_to_global
        - Global server with utilization > 0.5: keep
        - Project server with utilization < 0.2: move_to_project (or remove)
        """
        ...

    def analyze(self) -> list[MCPUsageRecommendation]:
        """Implement BaseAnalyzer interface."""
        report = self.analyze_all_projects()
        return report.recommendations

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        ...
```

**Data Models**:
- Input: `.claude/mcp.json` files, `~/.claude/mcp-analytics.jsonl`
- Output: `GlobalMCPReport`, `MCPUsageRecommendation` (see data-model.md)

**Integration**: Runs during rebuild, recommendations shown in output

---

## 4. ContextOptimizer

**Purpose**: Track CLAUDE.md section usage and suggest context optimizations.

**Module**: `claude_automation/analyzers/context_optimizer.py`

**Interface**:

```python
class ContextOptimizer:
    """Optimizes CLAUDE.md context based on usage patterns."""

    def __init__(
        self,
        log_file: Path = Path.home() / ".claude" / "context-access.jsonl",
        config: AdaptiveSystemConfig
    ):
        """Initialize optimizer."""
        ...

    def log_access(
        self,
        session_id: str,
        section_name: str,
        access_type: str,  # "load" | "reference"
        file_path: Path,
        token_count: int
    ) -> None:
        """Log context section access.

        NOTE: Requires Claude Code API integration (future).
        """
        ...

    def calculate_effective_context_ratio(
        self,
        days: int = 30
    ) -> float:
        """Calculate effective context ratio.

        Formula:
            effective_ratio = total_references / total_loads

        Returns:
            Ratio [0.0, 1.0] (higher is better, means less noise)
        """
        ...

    def identify_noise_sections(
        self,
        days: int = 30,
        threshold: float = 0.1
    ) -> list[SectionUsage]:
        """Identify sections with low reference rate.

        Args:
            days: Analysis window
            threshold: Sections with reference_rate < threshold are noise

        Returns:
            List of noisy sections, sorted by noise_score (highest first)
        """
        ...

    def detect_context_gaps(
        self,
        days: int = 30
    ) -> list[str]:
        """Detect frequently-queried information not in CLAUDE.md.

        NOTE: Requires Claude Code API integration (future).

        Returns:
            List of topic strings that should be added to CLAUDE.md
        """
        ...

    def generate_quick_reference(
        self,
        days: int = 30,
        top_n: int = 10
    ) -> str:
        """Generate quick reference from most-accessed sections.

        Returns:
            Markdown quick reference to prepend to CLAUDE.md
        """
        ...

    def analyze(self) -> list[ContextOptimization]:
        """Implement BaseAnalyzer interface."""
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        return {
            'healthy': True,
            'effective_ratio': self.calculate_effective_context_ratio(),
            'noise_sections': len(self.identify_noise_sections()),
            'total_sections': self._get_total_sections()
        }
```

**Data Models**:
- Input: `ContextAccessLog` (from Claude Code - future)
- Output: `ContextOptimization` (see data-model.md)

**Limitation**: Requires Claude Code API to track section access (Phase 3+ feature)

---

## 5. WorkflowDetector

**Purpose**: Detect repeated slash command sequences and suggest workflow bundling.

**Module**: `claude_automation/analyzers/workflow_detector.py`

**Interface**:

```python
class WorkflowDetector:
    """Detects workflow patterns from slash command sequences."""

    def __init__(
        self,
        log_file: Path = Path.home() / ".claude" / "workflow-analytics.jsonl",
        config: AdaptiveSystemConfig
    ):
        """Initialize detector."""
        ...

    def log_command(
        self,
        session_id: str,
        command_name: str,
        success: bool,
        duration_seconds: float,
        project_root: Optional[Path] = None
    ) -> None:
        """Log slash command execution.

        NOTE: Requires Claude Code integration (future).
        """
        ...

    def detect_sequences(
        self,
        days: int = 30,
        min_length: int = 2,
        max_length: int = 5
    ) -> list[WorkflowSequence]:
        """Detect command sequences.

        Args:
            days: Analysis window
            min_length: Minimum commands in sequence
            max_length: Maximum commands in sequence

        Returns:
            List of detected sequences, sorted by occurrences (highest first)

        Filters:
            - Only sequences with occurrences >= config.min_pattern_occurrences
            - Only sequences with completion_rate > 0.5
        """
        ...

    def calculate_completion_rate(
        self,
        sequence: WorkflowSequence
    ) -> float:
        """Calculate sequence completion rate.

        Formula:
            completion_rate = successful_completions / total_attempts

        Returns:
            Rate [0.0, 1.0]
        """
        ...

    def analyze(self) -> list[WorkflowSuggestion]:
        """Implement BaseAnalyzer interface."""
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        ...
```

**Data Models**:
- Input: `SlashCommandLog` (from Claude Code - future)
- Output: `WorkflowSuggestion` (see data-model.md)

**Limitation**: Requires Claude Code integration (Phase 3+ feature)

---

## 6. InstructionTracker

**Purpose**: Track policy adherence and suggest instruction improvements.

**Module**: `claude_automation/analyzers/instruction_tracker.py`

**Interface**:

```python
class InstructionTracker:
    """Tracks instruction effectiveness and suggests improvements."""

    def __init__(
        self,
        log_file: Path = Path.home() / ".claude" / "policy-violations.jsonl",
        config: AdaptiveSystemConfig
    ):
        """Initialize tracker."""
        ...

    def log_violation(
        self,
        session_id: str,
        policy_name: str,
        violation_description: str,
        policy_text: str,
        severity: str  # "low" | "medium" | "high"
    ) -> None:
        """Log policy violation.

        NOTE: Requires Claude Code API integration (future).
        """
        ...

    def calculate_effectiveness(
        self,
        policy_name: str,
        days: int = 30
    ) -> InstructionEffectiveness:
        """Calculate effectiveness metrics for a policy.

        Formula:
            effectiveness_score = compliant_sessions / total_sessions
            ambiguous = effectiveness_score < 0.7
        """
        ...

    def identify_ambiguous_instructions(
        self,
        days: int = 30
    ) -> list[InstructionEffectiveness]:
        """Find instructions with low effectiveness (<0.7).

        Returns:
            List of ambiguous instructions, sorted by effectiveness (lowest first)
        """
        ...

    def suggest_improvements(
        self,
        effectiveness: InstructionEffectiveness
    ) -> InstructionImprovement:
        """Generate improvement suggestion for low-effectiveness instruction."""
        ...

    def analyze(self) -> list[InstructionImprovement]:
        """Implement BaseAnalyzer interface."""
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        ...
```

**Data Models**:
- Input: `PolicyViolation` (from Claude Code - future)
- Output: `InstructionImprovement` (see data-model.md)

**Limitation**: Requires Claude Code API integration (Phase 3+ feature)

---

## 7. ProjectArchetypeDetector

**Purpose**: Classify projects and transfer patterns between similar projects.

**Module**: `claude_automation/analyzers/project_archetype_detector.py`

**Interface**:

```python
class ProjectArchetypeDetector:
    """Detects project archetypes and transfers patterns."""

    def __init__(self, config: AdaptiveSystemConfig):
        """Initialize detector."""
        ...

    def detect_archetype(self, project_root: Path) -> ProjectArchetype:
        """Detect project archetype from filesystem and configuration.

        Detection rules:
        - pyproject.toml + pytest.ini → python_pytest
        - package.json + vitest.config.ts → typescript_vitest
        - Cargo.toml → rust_cargo
        - flake.nix → nixos_flake
        - etc.

        Returns:
            Detected archetype with common patterns
        """
        ...

    def build_knowledge_base(
        self,
        projects: list[Path]
    ) -> dict[str, ProjectArchetype]:
        """Build knowledge base of patterns per archetype.

        Returns:
            Map of archetype_type → ProjectArchetype
        """
        ...

    def find_transfer_opportunities(
        self,
        target_project: Path,
        knowledge_base: dict[str, ProjectArchetype]
    ) -> list[TransferSuggestion]:
        """Find patterns to transfer to target project.

        Logic:
        1. Detect target project archetype
        2. Find archetype in knowledge base
        3. Identify patterns in archetype but not in target project
        4. Generate transfer suggestions
        """
        ...

    def transfer_pattern(
        self,
        target_project: Path,
        pattern: CrossProjectPattern
    ) -> GenerationResult:
        """Apply pattern to target project.

        Side effects:
        - May modify settings.local.json (permissions)
        - May modify CLAUDE.md (tools, instructions)
        - May create slash commands
        """
        ...

    def analyze(self) -> list[TransferSuggestion]:
        """Implement BaseAnalyzer interface."""
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        ...
```

**Data Models**:
- Input: Project filesystem, existing configs
- Output: `TransferSuggestion` (see data-model.md)

**Integration**: Runs when new project detected (no .claude directory)

---

## 8. MetaLearner

**Purpose**: Track learning system effectiveness and self-calibrate thresholds.

**Module**: `claude_automation/analyzers/meta_learner.py`

**Interface**:

```python
class MetaLearner:
    """Meta-learning: tracks learning system effectiveness."""

    def __init__(
        self,
        log_file: Path = Path.home() / ".claude" / "meta-learning.json",
        config: AdaptiveSystemConfig
    ):
        """Initialize meta-learner."""
        ...

    def track_suggestion_outcome(
        self,
        component: str,  # "PermissionLearning", "MCPOptimization", etc.
        suggestion_id: str,
        accepted: bool
    ) -> None:
        """Track whether user accepted a suggestion."""
        ...

    def get_component_metrics(
        self,
        component: str,
        days: int = 30
    ) -> LearningMetrics:
        """Get effectiveness metrics for a component.

        Metrics:
        - total_suggestions
        - accepted_suggestions
        - acceptance_rate
        - false_positives (rejected suggestions)
        - false_positive_rate
        """
        ...

    def suggest_threshold_adjustments(
        self,
        component: str,
        metrics: LearningMetrics
    ) -> list[ThresholdAdjustment]:
        """Suggest threshold adjustments based on metrics.

        Rules:
        - If acceptance_rate < 0.5: increase confidence_threshold
        - If acceptance_rate > 0.9: decrease confidence_threshold
        - If false_positive_rate > 0.3: increase min_pattern_occurrences
        """
        ...

    def get_health_report(self) -> LearningHealthReport:
        """Generate overall learning system health report.

        Health criteria:
        - healthy: All components acceptance_rate > 0.6, FP rate < 0.2
        - needs_tuning: Some components outside healthy range
        - malfunctioning: Multiple components acceptance_rate < 0.3
        """
        ...

    def analyze(self) -> list[ThresholdAdjustment]:
        """Implement BaseAnalyzer interface."""
        ...

    def get_health_metrics(self) -> dict[str, Any]:
        """Return health metrics."""
        return {
            'healthy': self._is_healthy(),
            'overall_acceptance_rate': self._calculate_overall_acceptance_rate(),
            'components': len(self._get_all_component_metrics())
        }
```

**Data Models**:
- Input: Suggestion outcomes from all components
- Output: `LearningHealthReport`, `ThresholdAdjustment` (see data-model.md)

**Storage**: `~/.claude/meta-learning.json`

**Integration**: Runs after user approves/rejects suggestions

---

## Integration with AdaptiveSystemEngine

The AdaptiveSystemEngine orchestrates all analyzers:

```python
class AdaptiveSystemEngine:
    def __init__(self, config: AdaptiveSystemConfig):
        # Initialize all 8 analyzers
        self.approval_tracker = ApprovalTracker()
        self.permission_detector = PermissionPatternDetector(self.approval_tracker, config)
        self.mcp_analyzer = GlobalMCPAnalyzer(config)
        self.context_optimizer = ContextOptimizer(config=config)
        self.workflow_detector = WorkflowDetector(config=config)
        self.instruction_tracker = InstructionTracker(config=config)
        self.archetype_detector = ProjectArchetypeDetector(config)
        self.meta_learner = MetaLearner(config=config)

    def run_full_learning_cycle(self) -> LearningReport:
        """Run all analyzers and consolidate results."""
        report = LearningReport()

        # Run each analyzer
        if self.config.permission_learning_enabled:
            report.permission_suggestions = self.permission_detector.analyze()

        if self.config.mcp_optimization_enabled:
            report.mcp_recommendations = self.mcp_analyzer.analyze()

        # ... etc for all analyzers

        if self.config.meta_learning_enabled:
            report.learning_health = self.meta_learner.get_health_report()

        return report
```

---

## Testing Contracts

All analyzers MUST have:

1. **Unit tests**: Test core logic in isolation
2. **Contract tests**: Verify interface compliance
3. **Integration tests**: Test with real data

**Example contract test**:

```python
def test_analyzer_contract():
    """Verify analyzer implements BaseAnalyzer protocol."""
    analyzer = PermissionPatternDetector(tracker, config)

    # Must have analyze() method
    assert hasattr(analyzer, 'analyze')
    assert callable(analyzer.analyze)

    # analyze() must return list
    result = analyzer.analyze()
    assert isinstance(result, list)

    # Must have get_health_metrics() method
    assert hasattr(analyzer, 'get_health_metrics')
    metrics = analyzer.get_health_metrics()
    assert isinstance(metrics, dict)
    assert 'healthy' in metrics
    assert 'last_run' in metrics
```

---

## Future Extensions

**Potential new analyzers**:
- **SecurityPatternDetector**: Detect security best practices
- **ErrorPatternAnalyzer**: Learn from error patterns and suggest fixes
- **DependencyOptimizer**: Analyze dependency usage and suggest removals
- **TestCoverageAnalyzer**: Identify undertested code paths

All future analyzers MUST implement the BaseAnalyzer protocol.

---

*Last updated: 2025-10-17 (Phase 2 completion)*
