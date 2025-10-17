---
status: planning
created: 2025-10-10
updated: 2025-10-10
type: architecture
lifecycle: persistent
---

# NixOS Intelligence Vision

**Goal**: Leverage NixOS's declarative, text-based nature to build semantic understanding of system usage that improves coding agent responses.

## Intelligence Levels

### Level 1: Static Inventory (CURRENT ✅)
**What**: List what's installed
**How**: Parse `.nix` files for package names
**Value**: Basic awareness

### Level 2: Usage Correlation (CURRENT ✅)
**What**: Track which commands are used
**How**: Parse Fish history, detect patterns
**Value**: Basic personalization

### Level 3: Semantic Understanding (VISION 🎯)
**What**: Understand WHY and HOW
**How**: Multi-source intelligence (git + nix + usage)
**Value**: Intelligent recommendations

### Level 4: Adaptive Optimization (FUTURE 🔮)
**What**: Auto-optimize configuration
**How**: Detect needs, suggest packages, generate code
**Value**: Self-improving system

---

## Level 3 Implementation Roadmap

### A. Git History Intelligence

**Data Source**: `git log` of `nixos-config/` repository

**Capabilities**:
1. **Intent Mining**: Extract "why" from commit messages
   - "Added ripgrep for faster text search" → Purpose documented
   - "Switched from grep to rg for performance" → Migration context

2. **Evolution Tracking**: When was each package added?
   - Package age: days since addition
   - Frequency of config changes
   - Correlation with project milestones

3. **Pattern Detection**: Common modification patterns
   - Weekly rebuilds? (experimenter)
   - Rare changes? (stable system)
   - Frequent rollbacks? (issues)

**Implementation**:
```python
class GitHistoryAnalyzer:
    def analyze_package_evolution(self, package_name: str):
        """Extract when/why a package was added."""
        # git log -p --all -S 'ripgrep' -- '*.nix'
        # Parse commits that added/removed package
        # Extract commit message for intent

    def detect_configuration_velocity(self):
        """How often does user rebuild?"""
        # Indicates experimentation vs. stability

    def correlate_packages_with_projects(self):
        """Did package addition coincide with new project?"""
        # Cross-reference with other repos
```

**Claude Code Benefits**:
- "You installed `ripgrep` 6 months ago for faster search. Consider using it for this task."
- "Your config has been stable (3 changes/year). Major changes may need testing."

---

### B. Dependency Intelligence

**Data Source**: `nix why-depends`, `nix-tree`, dependency graphs

**Capabilities**:
1. **Tool Chain Mapping**: What depends on what?
   - `python313` → pulls in `python313Packages.pip`
   - Visualize dependency trees

2. **Transitive Dependency Detection**:
   - "You have gcc because python needs it for native modules"

3. **Dead Dependency Detection**:
   - Packages installed as deps but parent removed

4. **Closure Size Analysis**:
   - "Adding package X will pull 200MB of dependencies"

**Implementation**:
```python
class NixDependencyAnalyzer:
    def build_dependency_graph(self):
        """Use nix why-depends to map relationships."""
        # nix why-depends /run/current-system nixpkgs#ripgrep

    def detect_tool_chains(self):
        """Find common tool combinations."""
        # gcc + python = native module builds
        # docker + kubernetes = container orchestration
```

**Claude Code Benefits**:
- "You need gcc for Python native modules. It's already installed via python313."
- "These 5 packages are unused (no dependents, not in Fish history)."

---

### C. Usage vs. Installed Cross-Reference

**Data Source**: Fish history + packages.nix

**Capabilities**:
1. **Unused Package Detection**:
   - Installed but never run (0 Fish history matches)
   - Candidates for removal

2. **Missing Package Detection**:
   - Commands used but not in nixpkgs
   - Manual installations or aliases

3. **Tool Preference Detection**:
   - User has both `ls` and `eza` - which do they use?
   - Inform recommendations

**Implementation**:
```python
class UsageAlignmentAnalyzer:
    def detect_unused_packages(self):
        """Packages installed but never used."""
        installed = set(nix_packages)
        used = set(extract_base_commands(fish_history))
        unused = installed - used
        # Filter: only CLI tools, exclude libs/deps

    def detect_missing_packages(self):
        """Commands used but not in nix config."""
        # Could be aliases, scripts, or manual installs

    def detect_tool_preferences(self):
        """When multiple options exist, which is preferred?"""
        # ls vs eza, grep vs rg, cat vs bat
```

**Claude Code Benefits**:
- "You have `dust` installed but never use it. Consider removing."
- "You frequently use `jq` (142 times) but it's not in your nix config - did you install it manually?"
- "When searching files, you prefer `rg` over `grep` (80 vs 5 uses)."

---

### D. Tool Chain & Pipeline Detection

**Data Source**: Fish history sequences

**Capabilities**:
1. **Command Pipelines**: Detect common sequences
   - `fd | rg | bat` → File search and view pipeline
   - `git diff | delta | less` → Enhanced diff viewing

2. **Workflow Sequences**: Multi-command workflows
   - `cd project && nix develop && python` → Dev environment pattern

3. **Tool Substitution Suggestions**:
   - "You use `find | grep` often. Consider `fd | rg` for better performance."

**Implementation**:
```python
class WorkflowSequenceAnalyzer:
    def detect_pipelines(self, window_size=60):
        """Find commands run within N seconds of each other."""
        # Group by timestamp proximity
        # Detect | (pipe) operators
        # Build pipeline graphs

    def suggest_optimizations(self):
        """Suggest better tool combinations."""
        # find + grep → fd + rg
        # cat + grep → rg directly
```

**Claude Code Benefits**:
- "You often run `fd` then `bat`. This is a file search+view workflow."
- "Instead of `cat file | grep pattern`, use `rg pattern file` directly."

---

### E. Failure Pattern Analysis

**Data Source**: Fish history with exit codes (requires logging enhancement)

**Capabilities**:
1. **Failed Command Detection**:
   - Commands that frequently return non-zero exit codes

2. **Missing Dependency Detection**:
   - "command not found" errors

3. **Permission Issues**:
   - Frequent sudo usage patterns

**Implementation**:
```python
# Requires enhancement to Fish history logging
# Fish doesn't log exit codes by default

# Alternative: Parse bash history if available
# Or: Add custom Fish function to log failures
```

**Claude Code Benefits**:
- "You've tried `docker ps` 5 times with failures. Docker service isn't running."
- "`nixos-rebuild` fails frequently. Check for syntax errors in config."

---

### F. Cross-Project Intelligence

**Data Source**: Multiple project directories + per-project CLAUDE.md

**Capabilities**:
1. **Project-Type Tool Correlation**:
   - Python projects → ruff, pytest, uv
   - Rust projects → clippy, cargo-watch
   - NixOS projects → nix flake check, devenv

2. **Tool Recommendation Engine**:
   - "In Python projects, you use ruff 80% of the time. Add it to this project?"

3. **Missing Tool Detection**:
   - "Your other Rust projects use clippy, but this one doesn't."

**Implementation**:
```python
class CrossProjectAnalyzer:
    def analyze_tool_usage_by_project_type(self):
        """Map project types to common tools."""
        # Group projects by type
        # Extract tool usage per project
        # Find patterns

    def recommend_tools_for_new_project(self, project_type):
        """Suggest tools based on similar projects."""
```

**Claude Code Benefits**:
- "In your 5 Python projects, 100% use `ruff`. Add to this project?"
- "Your Rust projects average 12 dev dependencies. This one has 3 - missing tools?"

---

### G. Configuration Drift Detection

**Data Source**: Nix config vs. actual system state

**Capabilities**:
1. **Manual Installation Detection**:
   - `which <tool>` exists but not in nixpkgs
   - Suggest adding to config for reproducibility

2. **Version Drift Detection**:
   - Package versions differ from declared

3. **Environment Pollution Detection**:
   - `~/.local/bin` additions outside Nix
   - `pip install --user` packages

**Implementation**:
```python
class DriftAnalyzer:
    def detect_manual_installations(self):
        """Find binaries in PATH not from Nix."""
        # Compare `which` output with nix-store paths

    def detect_python_pollution(self):
        """Find pip packages not in pyproject.toml."""
        # pip list vs uv pip list
```

**Claude Code Benefits**:
- "You have `jq` in PATH but it's not in your nix config. Add it?"
- "Found 12 pip packages installed outside Nix. Consider adding to project."

---

### H. MCP Server Usage Intelligence (NEW)

**Data Source**: MCP usage logs + session analytics

**Capabilities**:
1. **MCP Tool Effectiveness**:
   - Which MCP tools are actually used?
   - Success/failure rates

2. **Context Optimization**:
   - Which contexts lead to better responses?

3. **Prompt Engineering Insights**:
   - Patterns in successful vs. failed prompts

**Implementation**:
- See existing `mcp_usage_analyzer.py` (already started!)
- Enhance with deeper analytics

**Claude Code Benefits**:
- "You use serena 10x more than mcp-nixos. Prioritize its context."
- "Sessions with usage analytics have 30% better outcomes. Always include?"

---

## Data Architecture

### Data Sources
```
nixos-config/
  ├── modules/core/packages.nix    → Package declarations
  ├── .git/                        → Evolution & intent
  └── flake.lock                   → Exact versions

~/.local/share/fish/fish_history   → Command usage
/run/current-system                → Actual system state
~/.claude/                         → Claude Code state
~/*/                               → Project directories
```

### Intelligence Pipeline
```
1. COLLECT: Parse all data sources
2. ANALYZE: Extract patterns and relationships
3. CORRELATE: Cross-reference data points
4. SYNTHESIZE: Generate insights
5. PRESENT: Enrich CLAUDE.md with intelligence
```

### Storage Strategy
```
~/.claude/intelligence/
  ├── package_evolution.json       → When/why packages added
  ├── dependency_graph.json        → Tool relationships
  ├── usage_alignment.json         → Installed vs. used
  ├── tool_chains.json             → Pipeline patterns
  ├── cross_project_patterns.json  → Project-type correlations
  └── drift_report.json            → Config vs. reality
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. ✅ Git history analyzer
2. ✅ Usage vs. installed cross-reference
3. ✅ Basic dependency graphing

### Phase 2: Intelligence (Week 2)
4. ✅ Tool chain detection
5. ✅ Cross-project analysis
6. ✅ Intent mining from commits

### Phase 3: Optimization (Week 3)
7. ✅ Drift detection
8. ✅ Recommendation engine
9. ✅ Auto-generation capabilities

---

## Success Metrics

**Measure effectiveness by:**
1. **Reduction in context needed**: Claude Code makes fewer clarifying questions
2. **Tool recommendation accuracy**: Suggestions match actual needs
3. **Configuration quality**: Fewer unused packages, complete dependencies
4. **User time saved**: Faster setup of new projects

---

## Example Enhanced Output

**Before (Current Level 1-2)**:
```markdown
## Available Tools
- ripgrep - Super fast grep (rg command)
- bat - Better cat with syntax highlighting
```

**After (Level 3)**:
```markdown
## Tool Intelligence

### ripgrep (rg)
- **Purpose**: Faster text search (added 6mo ago: "performance over grep")
- **Usage**: 156 times (rank: #5)
- **Context**: Preferred over grep (5 uses)
- **Workflow**: Often piped to bat for viewing results
- **Dependencies**: None (standalone binary)
- **Recommendation**: Primary search tool for this system

### bat
- **Purpose**: Syntax-highlighted file viewer
- **Usage**: 89 times (rank: #12)
- **Context**: Paired with fd/rg in search workflows
- **Tool Chain**: fd → rg → bat (file search pipeline)
- **Recommendation**: Use for all file previews
```

---

## Questions for User

1. **Priority**: Which intelligence features are most valuable?
   - Git history mining?
   - Dependency graphing?
   - Usage alignment?
   - Tool chain detection?

2. **Scope**: Focus on system-level or project-level first?

3. **Data privacy**: Comfortable with caching intelligence data?

4. **Integration**: Add to existing analyzers or new module?

---

*This is the vision for truly leveraging NixOS's declarative nature.*
