---
status: planning
created: 2025-10-10
updated: 2025-10-10
type: guide
lifecycle: ephemeral
---

# Quick Intelligence Wins

High-impact improvements that leverage NixOS's declarative nature.

## 1. Git History Mining (4 hours)

**Value**: Understand WHY packages were added

**Implementation**:
```python
# claude_automation/analyzers/git_history_analyzer.py

class GitHistoryAnalyzer:
    def analyze_package_additions(self, nixos_config_path):
        """Extract when/why packages were added."""
        packages = {}

        for package in installed_packages:
            # git log --all -S 'ripgrep' -- '*.nix'
            result = run(['git', 'log', '--all', '-S', package,
                         '--format=%H|%ai|%s', '--', '*.nix'])

            commits = parse_commits(result.stdout)
            if commits:
                first_commit = commits[-1]  # Earliest
                packages[package] = {
                    'added_date': first_commit.date,
                    'added_why': first_commit.message,
                    'modification_count': len(commits)
                }

        return packages
```

**Output Enhancement**:
```markdown
## Tool Intelligence

- **ripgrep**: Added 2024-04-12 ("switch from grep for performance"), modified 3 times
- **bat**: Added 2024-05-20 ("better file previews"), stable (1 change)
```

**Claude Code Benefit**:
- "Use ripgrep - you added it specifically for performance over grep"

---

## 2. Usage vs. Installed Gap Analysis (3 hours)

**Value**: Identify unused packages & missing tools

**Implementation**:
```python
# claude_automation/analyzers/usage_alignment_analyzer.py

class UsageAlignmentAnalyzer:
    def detect_gaps(self):
        """Cross-reference installed packages with usage."""
        installed = set(parse_nix_packages())
        used = set(extract_commands_from_fish_history())

        # Filter to CLI tools only (exclude libs, fonts)
        cli_tools = {pkg for pkg in installed
                    if is_cli_tool(pkg)}

        unused = cli_tools - used
        missing = used - installed

        return {
            'unused_packages': list(unused),
            'missing_packages': list(missing),
            'usage_rate': len(used & cli_tools) / len(cli_tools)
        }
```

**Output Enhancement**:
```markdown
## Configuration Health

- **Usage rate**: 78% (89/114 installed CLI tools actually used)
- **Unused packages**: dust, dua, jless (0 uses in 6 months)
- **Missing from config**: `jq` (used 47 times but not in nixpkgs)
```

**Claude Code Benefit**:
- "I see you use `jq` frequently but it's not in your nix config. Should I add it?"
- "You have `dust` installed but never use it. Use `du` instead?"

---

## 3. Tool Preference Detection (2 hours)

**Value**: Know which tools user prefers when alternatives exist

**Implementation**:
```python
# claude_automation/analyzers/tool_preference_analyzer.py

class ToolPreferenceAnalyzer:
    # Alternatives map
    ALTERNATIVES = {
        'search': ['grep', 'rg', 'ripgrep', 'ack'],
        'list': ['ls', 'eza', 'exa'],
        'cat': ['cat', 'bat'],
        'find': ['find', 'fd'],
        'df': ['df', 'duf', 'dust'],
    }

    def detect_preferences(self, usage_stats):
        """Determine preferred tools."""
        preferences = {}

        for category, tools in self.ALTERNATIVES.items():
            usage = {tool: usage_stats.get(tool, 0)
                    for tool in tools}

            if sum(usage.values()) > 0:
                preferred = max(usage, key=usage.get)
                alternatives = {t: c for t, c in usage.items()
                              if t != preferred and c > 0}

                preferences[category] = {
                    'preferred': preferred,
                    'usage': usage[preferred],
                    'alternatives': alternatives
                }

        return preferences
```

**Output Enhancement**:
```markdown
## Tool Preferences

- **Search**: ripgrep (156 uses) over grep (5 uses) - 97% preference
- **List files**: eza (89 uses) over ls (12 uses) - 88% preference
- **View files**: bat (67 uses) exclusively (no cat usage)
```

**Claude Code Benefit**:
- "I'll use `rg` instead of grep - it's your preferred search tool (97% usage)"
- "Listing files with `eza` as usual"

---

## 4. Tool Chain Detection (4 hours)

**Value**: Understand common command workflows

**Implementation**:
```python
# claude_automation/analyzers/tool_chain_analyzer.py

class ToolChainAnalyzer:
    def detect_pipelines(self, fish_history):
        """Find common command sequences."""
        # Parse commands with pipes
        pipelines = [cmd for cmd in fish_history
                    if '|' in cmd]

        pipeline_counter = Counter(
            normalize_pipeline(cmd) for cmd in pipelines
        )

        # Also detect temporal sequences (commands within 60s)
        sequences = self._detect_temporal_sequences(
            fish_history, window=60
        )

        return {
            'pipelines': pipeline_counter.most_common(10),
            'workflows': sequences
        }

    def _detect_temporal_sequences(self, commands, window):
        """Find commands run together in time."""
        sequences = []

        for i, (cmd1, time1) in enumerate(commands):
            subsequence = [cmd1]

            for cmd2, time2 in commands[i+1:i+5]:
                if (time2 - time1).total_seconds() < window:
                    subsequence.append(cmd2)
                else:
                    break

            if len(subsequence) >= 2:
                sequences.append(tuple(subsequence))

        return Counter(sequences).most_common(10)
```

**Output Enhancement**:
```markdown
## Detected Workflows

### File Search Pipeline (23 occurrences)
```bash
fd <pattern> | rg <query> | bat
```
**Purpose**: Find files, search content, view results

### Development Workflow (45 occurrences)
```bash
cd <project> → nix develop → uv run pytest
```
**Purpose**: Enter project, activate environment, run tests
```

**Claude Code Benefit**:
- "I see you typically pipe fd to rg for searching. I'll use that workflow."
- "After entering a project, you usually run `nix develop` first. Should I?"

---

## 5. Cross-Project Tool Correlation (5 hours)

**Value**: Project-type-specific tool recommendations

**Implementation**:
```python
# claude_automation/analyzers/cross_project_analyzer.py

class CrossProjectAnalyzer:
    def analyze_project_tools(self, projects_root):
        """Map project types to common tools."""
        project_profiles = {}

        for project_path in find_projects(projects_root):
            project_type = detect_project_type(project_path)
            tools_used = extract_project_tools(project_path)

            if project_type not in project_profiles:
                project_profiles[project_type] = []

            project_profiles[project_type].append({
                'path': project_path,
                'tools': tools_used
            })

        # Find common tools per type
        recommendations = {}
        for ptype, projects in project_profiles.items():
            tool_freq = Counter()
            for project in projects:
                tool_freq.update(project['tools'])

            total = len(projects)
            common_tools = {
                tool: count/total
                for tool, count in tool_freq.items()
                if count/total >= 0.7  # 70% threshold
            }

            recommendations[ptype] = common_tools

        return recommendations
```

**Output Enhancement**:
```markdown
## Project Type Patterns (analyzed 12 projects)

### Python Projects (5 total)
- **ruff**: 100% (5/5) - Linter
- **pytest**: 100% (5/5) - Testing
- **uv**: 80% (4/5) - Package manager
- **black**: 60% (3/5) - Formatter

### Rust Projects (3 total)
- **clippy**: 100% (3/3) - Linter
- **cargo-watch**: 67% (2/3) - Auto-rebuild
```

**Claude Code Benefit**:
- "This is a Python project. Your other Python projects all use ruff and pytest. Add them?"
- "Your Rust projects typically use clippy. Run `cargo clippy` for linting?"

---

## 6. Nix Dependency Intelligence (3 hours)

**Value**: Understand why packages are installed

**Implementation**:
```bash
# Use nix why-depends to understand relationships
nix why-depends /run/current-system nixpkgs#gcc

# Output:
# python3 -> gcc (for native module compilation)
```

```python
# claude_automation/analyzers/nix_dependency_analyzer.py

class NixDependencyAnalyzer:
    def build_dependency_map(self):
        """Map package dependencies."""
        deps = {}

        for package in user_installed_packages:
            result = run([
                'nix', 'why-depends',
                '/run/current-system',
                f'nixpkgs#{package}'
            ])

            if result.returncode == 0:
                deps[package] = parse_dependency_chain(result.stdout)

        return deps
```

**Output Enhancement**:
```markdown
## Dependency Intelligence

- **gcc**: Required by python313 (native module compilation)
- **pkg-config**: Required by multiple packages (build dependency)
- **ripgrep**: Standalone (no dependencies)
```

**Claude Code Benefit**:
- "gcc is available because Python needs it for native modules"
- "This will pull in 15 dependencies (200MB). Continue?"

---

## Implementation Order

### Week 1: Low-Hanging Fruit
1. ✅ Tool preference detection (2h)
2. ✅ Usage vs. installed gap (3h)
3. ✅ Git history mining (4h)

**Total**: 9 hours
**Impact**: HIGH - immediate usability improvements

### Week 2: Workflow Intelligence
4. ✅ Tool chain detection (4h)
5. ✅ Nix dependency intelligence (3h)

**Total**: 7 hours
**Impact**: MEDIUM - deeper understanding

### Week 3: Strategic Intelligence
6. ✅ Cross-project correlation (5h)

**Total**: 5 hours
**Impact**: HIGH - project-specific recommendations

---

## Total Effort: ~21 hours

**ROI**: Transforms claude-nixos-automation from inventory to intelligence
