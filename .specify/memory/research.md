---
status: draft
created: 2025-10-20
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# Research: Self-Improving Claude Code System

**Date**: 2025-10-17
**Phase**: Phase 0 - Research
**Status**: Complete

This document captures technical research decisions for algorithm selection, methodologies, and implementation strategies for the self-improving Claude Code system.

---

## 1. Permission Pattern Detection Algorithms

**Question**: What's the optimal algorithm for detecting generalizable patterns from approval history?

### Research Approach

Evaluated:
- **Frequent Itemset Mining (FP-Growth)**: Computational overhead too high for real-time suggestions
- **Sequence Mining (PrefixSpan)**: Overkill for command-level patterns
- **Statistical Frequency Analysis**: Simple, fast, interpretable ✓ SELECTED

### Decision: Statistical Frequency with Confidence Scoring

**Algorithm**:
```python
def detect_pattern(approvals, min_occurrences=3, time_window_days=30):
    # Filter to time window
    recent = filter_by_time(approvals, days=time_window_days)

    # Group by pattern type
    patterns = group_by_pattern_type(recent)  # git, pytest, ruff, etc.

    # Count occurrences
    pattern_counts = count_occurrences(patterns)

    # Filter by threshold
    candidates = filter(pattern_counts, min_count=min_occurrences)

    # Calculate confidence score
    for pattern in candidates:
        pattern.confidence = calculate_confidence(pattern)

    return sort_by_confidence(candidates)
```

**Confidence Scoring**:
```python
confidence = (
    frequency_score * 0.4 +      # How often approved (normalized to 0-1)
    consistency_score * 0.3 +    # Pattern consistency (variance in approval timing)
    coverage_score * 0.3         # % of recent approvals matching this pattern
)
```

**Thresholds**:
- `min_occurrences`: 3 (prevents false positives from rare commands)
- `time_window`: 30 days (balances recency vs statistical significance)
- `min_confidence`: 0.7 (70% confidence threshold for suggestions)

**Rationale**:
- Simple to implement and understand
- Fast execution (<100ms for 1000 approvals)
- Confidence scoring provides actionable feedback
- Thresholds tuneable via meta-learning

---

## 2. Token-Based MCP ROI Calculation

**Question**: How to accurately calculate ROI for MCP servers given token consumption?

### Research Approach

Evaluated cost models:
- **Invocations Only**: Ignores token overhead
- **Token Cost Only**: Ignores utility value
- **Hybrid ROI Model**: Balances utility and cost ✓ SELECTED

### Decision: Utility-Per-Token ROI

**Formula**:
```python
ROI = (invocations / (tokens / 1000)) * utilization_rate

Where:
- invocations: Total tool calls to server
- tokens: Total tokens consumed by server
- utilization_rate: used_sessions / loaded_sessions
```

**Interpretation**:
- **High ROI (>5.0)**: High-value server - frequently used, low overhead
- **Medium ROI (2.0-5.0)**: Acceptable - moderate usage and cost
- **Low ROI (<2.0)**: Underutilized - consider removing or moving to project-level

**Session Overhead Estimation**:
```python
estimated_overhead_per_server = {
    "filesystem": 500,   # Tool definitions ~500 tokens
    "serena": 800,       # Complex tool schemas
    "sequential-thinking": 300,  # Simple interface
}
```

**Utilization Metrics**:
```python
utilization_rate = used_sessions / loaded_sessions

Where:
- loaded_sessions: Sessions where server was available
- used_sessions: Sessions where ≥1 tool from server was invoked
```

**Rationale**:
- Accounts for both utility (invocations) and cost (tokens)
- Utilization rate provides context (is it loaded but unused?)
- Easy to interpret and act on
- Enables objective server optimization decisions

---

## 3. Context Effectiveness Measurement

**Question**: How to track which CLAUDE.md sections Claude actually uses?

### Research Approach

Evaluated:
- **Session Log Parsing**: Requires Claude internal logs (unavailable)
- **Reference Detection in Responses**: Indirect proxy measure
- **Token Attribution**: Can't directly measure section-level usage ✗
- **Heuristic Tracking via Tool Selection**: Proxy metric ✓ SELECTED

### Decision: Tool Usage as Context Proxy

**Methodology**:
Since direct section access tracking isn't available, we infer context effectiveness from:

1. **Tool Selection Patterns**:
   ```python
   # If user frequently uses `bat` but CLAUDE.md mentions `cat`
   # → "Modern CLI Tools" section is effective
   # → "POSIX Tools" section may be noise
   ```

2. **Effective Context Ratio (Proxy)**:
   ```python
   effective_ratio = tools_mentioned_and_used / total_tools_in_context
   ```

3. **Noise Detection**:
   - Section loaded but referenced tools never invoked in 30+ days → candidate for pruning
   - Example: "Fish Abbreviations" section with 50 abbreviations, but only 3 ever used

4. **Context Gap Detection**:
   - User repeatedly requests tool not in CLAUDE.md → missing context
   - Example: Frequent "how do I use X?" when X isn't documented

**Reordering Algorithm**:
```python
def reorder_sections(section_usage_scores):
    # Sort sections by usage frequency
    sorted_sections = sort(sections, key=lambda s: s.access_count, reverse=True)

    # Top 20% → "Quick Reference" section at top
    quick_ref = top_percent(sorted_sections, 20)

    # Remaining → sorted by category and usage
    body = sort_by_category_then_usage(sorted_sections[20:])

    return [quick_ref, *body]
```

**Rationale**:
- Cannot directly measure section access without Claude internals
- Tool usage is a strong proxy for context effectiveness
- Focuses on actionable metrics (what tools are actually used)
- Provides clear signals for optimization (add/remove/reorder)

---

## 4. Meta-Learning Threshold Calibration

**Question**: How should the system adjust detection thresholds based on user feedback?

### Research Approach

Evaluated:
- **Fixed Thresholds**: No adaptation (baseline)
- **Linear Adjustment**: Simple but can overshoot
- **Exponential Decay**: Complex, hard to tune
- **Acceptance-Rate Feedback Loop**: Balanced, intuitive ✓ SELECTED

### Decision: Adaptive Threshold via Acceptance Feedback

**Algorithm**:
```python
def adjust_thresholds(acceptance_rate, current_thresholds):
    """
    Adjust detection thresholds based on suggestion acceptance rate.

    Target acceptance rate: 70-90%
    - <70%: Too many false positives → tighten thresholds
    - >90%: Too conservative → relax thresholds
    """

    if acceptance_rate < 0.5:
        # Very low acceptance - aggressively tighten
        new_min_occurrences = current_thresholds.min_occurrences + 2
        new_confidence = min(0.95, current_thresholds.min_confidence + 0.1)

    elif acceptance_rate < 0.7:
        # Low acceptance - moderately tighten
        new_min_occurrences = current_thresholds.min_occurrences + 1
        new_confidence = min(0.9, current_thresholds.min_confidence + 0.05)

    elif acceptance_rate > 0.9:
        # Very high acceptance - relax to find more patterns
        new_min_occurrences = max(2, current_thresholds.min_occurrences - 1)
        new_confidence = max(0.6, current_thresholds.min_confidence - 0.05)

    else:
        # Goldilocks zone (70-90%) - no change
        return current_thresholds

    return Thresholds(
        min_occurrences=new_min_occurrences,
        min_confidence=new_confidence
    )
```

**Initial Thresholds**:
```python
initial_thresholds = {
    "min_occurrences": 3,
    "min_confidence": 0.7,
    "time_window_days": 30,
}
```

**Calibration Metrics**:
```python
class LearningHealthMetrics:
    acceptance_rate: float  # % of suggestions accepted
    false_positive_rate: float  # % of accepted patterns later rejected
    coverage: float  # % of approvals covered by learned patterns

    # Derived health score
    health_score = (
        acceptance_rate * 0.4 +
        (1 - false_positive_rate) * 0.3 +
        coverage * 0.3
    )
```

**Rationale**:
- Self-correcting based on actual user behavior
- Target acceptance rate (70-90%) balances utility and annoyance
- Conservative initial thresholds prevent overwhelming users
- Gradual adjustments prevent oscillation
- Health metrics provide visibility into learning effectiveness

---

## 5. Pattern Categorization

**Categories Identified**:

1. **git_read_only**: Read-only git commands (status, diff, log)
2. **git_all_safe**: All safe git operations (includes add, commit - excludes push --force)
3. **pytest**: Test execution patterns (pytest with various flags)
4. **ruff**: Linting and formatting (ruff check, ruff format)
5. **modern_cli**: Modern CLI tool usage (eza, bat, rg, fd, etc.)
6. **project_full_access**: Read access to entire project directory
7. **file_operations**: Common file operations (Read, Write, Edit patterns)

**Detection Rules**:
```python
PATTERN_DETECTORS = {
    'git_read_only': lambda cmds: all(c.startswith('git') and c.split()[1] in ['status', 'diff', 'log'] for c in cmds),
    'pytest': lambda cmds: all('pytest' in c for c in cmds),
    # ... etc
}
```

---

## Implementation Implications

### Performance Requirements

From research decisions:
- Pattern detection: <100ms for 1000 approval entries
- MCP ROI calculation: <2s for 10 projects, 50 servers
- Context optimization: <500ms for CLAUDE.md analysis
- Meta-learning calibration: <50ms per adjustment

**Total Learning Cycle Budget**: <10s (well within requirement)

### Data Storage

All learning data in append-only JSONL files:
- `~/.claude/approval-history.jsonl`: Permission approvals
- `~/.claude/mcp-analytics.jsonl`: MCP usage metrics
- `~/.claude/context-analytics.jsonl`: Context effectiveness logs
- `~/.claude/workflow-analytics.jsonl`: Slash command sequences
- `~/.claude/instruction-analytics.jsonl`: Policy adherence
- `~/.claude/meta-learning.jsonl`: Learning system health

**Rationale**: JSONL is:
- Human-readable for debugging
- Append-only (no corruption risk)
- Fast to parse line-by-line
- Easy to filter by time windows

### Error Handling

Conservative approach:
- If detection fails → log error, return empty suggestions
- If ROI calculation fails → assume neutral (ROI=1.0)
- If context analysis fails → skip optimization round
- Never crash rebuild process due to learning failures

---

## References

1. Frequent Pattern Mining: "Mining Frequent Patterns without Candidate Generation" (Han et al., 2000)
2. Confidence Scoring: Bayesian approach adapted from spam filtering algorithms
3. Token Efficiency Metrics: Inspired by database query optimization techniques
4. Adaptive Thresholds: PID controller concepts adapted for discrete events

---

**Conclusion**: Research phase complete. All algorithm choices documented with rationale. Ready for implementation in Phase 1.
