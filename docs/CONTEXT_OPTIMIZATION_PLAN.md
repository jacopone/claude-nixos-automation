---
status: planning
created: 2025-10-10
updated: 2025-10-10
type: architecture
lifecycle: ephemeral
---

# Context Optimization Plan

Fix CLAUDE.md bloat and broken permissions automation.

## Problems Identified

### 1. CLAUDE.md: Static, Universal Context
- ❌ All 123 tools loaded for every task
- ❌ Same context regardless of project type
- ❌ No prioritization by usage
- ❌ Violates Anthropic's "focused context" principle

### 2. Permissions: Broken Automation
- ❌ Captures artifacts (commit messages in permissions!)
- ❌ No validation
- ❌ Disconnected from CLAUDE.md
- ❌ No feedback on effectiveness

### 3. No Intelligence
- ❌ Doesn't know which tools are relevant
- ❌ Doesn't track permission usage
- ❌ Can't adapt based on context

---

## Solution: Dynamic, Intelligent Context

### Architecture

```
┌─────────────────────────────────────────────┐
│         Context Intelligence Layer          │
│                                             │
│  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Project   │  │  Usage Analytics    │  │
│  │   Detector  │  │  - Command freq     │  │
│  │  - Type     │  │  - Tool preferences │  │
│  │  - Tech     │  │  - Patterns         │  │
│  └─────────────┘  └─────────────────────┘  │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │      Dynamic Context Generator      │   │
│  │  - Filter tools by relevance        │   │
│  │  - Prioritize by usage              │   │
│  │  - Load task-specific context       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
              │                    │
              ▼                    ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  CLAUDE.md       │  │  settings.local  │
    │  (Dynamic)       │  │  (Validated)     │
    │                  │  │                  │
    │  - Relevant only │  │  - Clean perms   │
    │  - Prioritized   │  │  - Coordinated   │
    │  - Task-aware    │  │  - Tracked       │
    └──────────────────┘  └──────────────────┘
```

---

## Phase 1: Fix Permissions (4 hours)

### 1.1 Clean Artifact Pollution

**Problem**: Line 19 in settings.local.json contains entire commit message

**Fix**:
```python
# claude_automation/generators/permissions_generator.py

class PermissionsGenerator:
    def _validate_permission(self, perm: str) -> bool:
        """Ensure permission is well-formed."""
        # Reject multi-line strings
        if '\n' in perm:
            logger.warning(f"Rejected multi-line permission: {perm[:50]}...")
            return False

        # Reject heredocs
        if '<<' in perm or 'EOF' in perm:
            logger.warning(f"Rejected heredoc permission: {perm[:50]}...")
            return False

        # Reject overly specific commands
        if len(perm) > 200:  # Arbitrary but reasonable
            logger.warning(f"Rejected too-long permission: {perm[:50]}...")
            return False

        return True

    def generate_permissions(self, project_type):
        """Generate clean, validated permissions."""
        perms = self._get_base_permissions(project_type)

        # Filter and validate
        clean_perms = [p for p in perms if self._validate_permission(p)]

        return {
            'permissions': {
                'allow': clean_perms,
                'deny': self._get_deny_rules(),
                'ask': self._get_ask_rules()
            }
        }
```

### 1.2 Coordinate CLAUDE.md with Permissions

**Problem**: CLAUDE.md lists "approved tools" but they're not in settings

**Fix**:
```python
# Generate both from same source

class UnifiedPermissionsGenerator:
    def generate_both(self, project_config):
        """Generate settings.local.json AND CLAUDE.md permissions section."""

        # Single source of truth
        allowed_tools = self._compute_allowed_tools(project_config)

        # Generate settings.json
        settings = {
            'permissions': {
                'allow': self._to_permission_patterns(allowed_tools),
                'deny': [...],
                'ask': [...]
            }
        }

        # Generate CLAUDE.md section
        claude_md_section = self._render_template(
            'approved_tools.j2',
            allowed_tools=allowed_tools
        )

        return settings, claude_md_section
```

### 1.3 Add Permission Analytics

**Problem**: No idea if permissions actually work

**Fix**:
```python
# New analyzer

class PermissionEffectivenessAnalyzer:
    def analyze(self, session_logs):
        """Track permission usage and approval requests."""

        # Parse Claude Code logs for approval requests
        approval_requests = extract_approval_requests(session_logs)

        # Compare with configured permissions
        missing_perms = self._find_missing_permissions(approval_requests)
        unused_perms = self._find_unused_permissions()

        return {
            'approval_requests_count': len(approval_requests),
            'missing_permissions': missing_perms,
            'unused_permissions': unused_perms,
            'effectiveness_score': calculate_score(...)
        }
```

---

## Phase 2: Dynamic CLAUDE.md (8 hours)

### 2.1 Project-Aware Context

**Problem**: Python project gets info on Kubernetes tools

**Fix**:
```python
class ProjectAwareContextGenerator:
    def generate_tools_section(self, project_path):
        """Generate only relevant tools for this project."""

        # Detect project
        project_type = detect_project_type(project_path)

        # Filter tools
        all_tools = parse_system_tools()
        relevant_tools = self._filter_by_project_type(
            all_tools,
            project_type
        )

        return relevant_tools

    def _filter_by_project_type(self, tools, project_type):
        """Keep only relevant tools."""

        RELEVANCE_MAP = {
            'python': {'pytest', 'ruff', 'uv', 'black', 'mypy', 'git'},
            'rust': {'cargo', 'clippy', 'rustfmt', 'git'},
            'nixos': {'nix', 'nixos-rebuild', 'nix-tree', 'git'},
            'nodejs': {'npm', 'node', 'eslint', 'prettier', 'git'},
        }

        # Always include
        core_tools = {'git', 'eza', 'bat', 'rg', 'fd'}

        # Project-specific
        project_tools = RELEVANCE_MAP.get(project_type, set())

        # Combine
        relevant = core_tools | project_tools

        return [t for t in tools if t.name in relevant]
```

### 2.2 Usage-Based Prioritization

**Problem**: All tools treated equally

**Fix**:
```python
class UsagePrioritizedGenerator:
    def prioritize_tools(self, tools, usage_stats):
        """Order tools by actual usage."""

        # Annotate with usage
        for tool in tools:
            tool.usage_count = usage_stats.get(tool.name, 0)
            tool.last_used = usage_stats.get_last_used(tool.name)

        # Sort: most-used first
        tools.sort(key=lambda t: t.usage_count, reverse=True)

        # Categorize
        frequently_used = [t for t in tools if t.usage_count > 10]
        occasionally_used = [t for t in tools if 0 < t.usage_count <= 10]
        unused = [t for t in tools if t.usage_count == 0]

        return {
            'primary': frequently_used,
            'secondary': occasionally_used,
            'available': unused  # Mention but don't detail
        }
```

### 2.3 Task-Specific Context (Advanced)

**Problem**: Same context for "write code" vs "analyze logs"

**Vision** (future):
```python
class TaskAwareContextLoader:
    def load_for_task(self, task_description, project_path):
        """Load only task-relevant context."""

        # Classify task
        task_type = classify_task(task_description)

        if task_type == 'testing':
            return load_testing_context(project_path)
        elif task_type == 'debugging':
            return load_debugging_context(project_path)
        elif task_type == 'refactoring':
            return load_refactoring_context(project_path)

        # Default: full project context
        return load_project_context(project_path)
```

---

## Phase 3: Intelligence Layer (Future)

### 3.1 Adaptive Context

Learn what context leads to better responses:
- Track task success
- Correlate with context provided
- Optimize over time

### 3.2 Predictive Loading

Anticipate what tools will be needed:
- "git diff" → likely need "git commit" soon
- "pytest" → might need "ruff" for failures
- "nix flake check" → might need "nix build"

---

## Implementation Priorities

### Week 1: Critical Fixes (4 hours)
1. ✅ Clean permission artifacts
2. ✅ Add validation
3. ✅ Coordinate CLAUDE.md with settings

### Week 2: Dynamic Context (8 hours)
4. ✅ Project-aware tool filtering
5. ✅ Usage-based prioritization
6. ✅ Permission analytics

### Week 3: Intelligence (Future)
7. ⏳ Task-specific context
8. ⏳ Adaptive learning
9. ⏳ Predictive loading

---

## Expected Outcomes

### CLAUDE.md Size
- **Before**: 597 lines (all tools)
- **After**: ~200 lines (relevant tools only)
- **Reduction**: 66% smaller, higher signal

### Permission Quality
- **Before**: Artifact pollution, no validation
- **After**: Clean, validated, tracked
- **Improvement**: Measurable effectiveness

### Response Quality
- **Before**: Generic tool suggestions
- **After**: Project-specific, usage-informed recommendations
- **Improvement**: Anthropic best practice aligned

---

## Validation

### How to Verify Success

1. **CLAUDE.md relevance**:
   - Count tools listed per project type
   - Verify only relevant tools included
   - Check prioritization matches usage

2. **Permission effectiveness**:
   - Count approval requests before/after
   - Track which permissions are used
   - Identify missing permissions

3. **Response quality**:
   - Compare tool recommendations
   - Measure task completion speed
   - User satisfaction (subjective)

---

*This plan transforms claude-nixos-automation from inventory to intelligence.*
