---
status: archived
created: 2025-10-07
updated: 2025-10-20
archived: 2025-10-20
type: planning
lifecycle: ephemeral
superseded_by: docs/architecture/IMPLEMENTATION_COMPLETE.md
---

# 🚀 Comprehensive Claude Code Awareness Automation - Implementation Roadmap

> **ARCHIVED**: This planning document has been fully implemented. All 6 phases complete.
> See [IMPLEMENTATION_COMPLETE.md](../../architecture/IMPLEMENTATION_COMPLETE.md) for current status.

**Date**: 2025-10-07
**Original Status**: Approved - Ready to implement
**Final Status**: ✅ ALL PHASES IMPLEMENTED (2025-10-20)
**Goal**: Create the most context-aware AI development system possible

---

## 🎯 Vision

Extend `claude-nixos-automation` to automatically maintain **ALL** Claude Code best practices identified through research:

1. ✅ System-wide CLAUDE.md (EXISTS)
2. ✅ Project-level CLAUDE.md (EXISTS)
3. 🔄 Permissions optimization (Phase 1 - Planned in PERMISSIONS_AUTOMATION_SESSION_HANDOFF.md)
4. 🆕 Directory-level CLAUDE.md (Phase 2)
5. 🆕 Local context CLAUDE.md (Phase 3)
6. 🆕 Custom slash commands (Phase 4)
7. 🆕 MCP server auto-config (Phase 5)
8. 🆕 Usage analytics (Phase 6)

**Research Sources**:
- Anthropic Claude Code Best Practices (2025)
- ClaudeLog best practices documentation
- Builder.io Claude Code guide
- Community patterns from 20+ hours of production usage

---

## 📊 Current vs Target State

### Current (Baseline)
```
System CLAUDE.md       21KB    162 tools listed
Project CLAUDE.md      ~5KB    Project structure + workflows
Permissions            Manual  User manages per-project
Directory Context      None    No directory-level files
Local Context          None    No machine-specific notes
Slash Commands         0       No custom commands
MCP Servers            2       Manually configured (serena, mcp-nixos)
Usage Analytics        None    No tracking
```

### Target (After Full Implementation)
```
System CLAUDE.md       15KB    Optimized with usage data
Project CLAUDE.md      ~7KB    Enhanced with best practices
Permissions            Auto    Per-project templates (Python/Node/Rust/NixOS)
Directory Context      5-7     Auto-generated (docs/, modules/, basb/, etc.)
Local Context          1       Machine-specific (hardware, WIP, experiments)
Slash Commands         10-15   Common workflows automated
MCP Servers            4-6     Auto-configured based on project type
Usage Analytics        Weekly  Top 20 tools prioritized in context
```

**Expected Impact**:
- 40% token reduction (better prioritization)
- 100% best practices coverage (all 8 areas)
- Zero manual maintenance
- Context quality improvement: Measurable via session efficiency

---

## 🏗️ Architecture: 6 New Generators

Following existing pattern: `BaseGenerator` + Jinja2 templates + Pydantic schemas

```
claude_automation/
├── generators/
│   ├── base_generator.py                 ✅ EXISTS
│   ├── system_generator.py               ✅ EXISTS
│   ├── project_generator.py              ✅ EXISTS
│   ├── user_policies_generator.py        ✅ EXISTS
│   ├── permissions_generator.py          🔄 Phase 1
│   ├── directory_context_generator.py    🆕 Phase 2
│   ├── local_context_generator.py        🆕 Phase 3
│   ├── slash_commands_generator.py       🆕 Phase 4
│   ├── mcp_config_generator.py           🆕 Phase 5
│   └── usage_analytics_generator.py      🆕 Phase 6
├── analyzers/                             🆕 NEW DIRECTORY
│   ├── __init__.py
│   ├── project_detector.py               🔄 Phase 1
│   ├── directory_analyzer.py             🆕 Phase 2
│   ├── system_analyzer.py                🆕 Phase 3
│   ├── workflow_analyzer.py              🆕 Phase 4
│   ├── mcp_detector.py                   🆕 Phase 5
│   └── usage_tracker.py                  🆕 Phase 6
├── templates/
│   ├── permissions/                       🔄 Phase 1
│   │   ├── base.j2
│   │   ├── python.j2
│   │   ├── nodejs.j2
│   │   ├── rust.j2
│   │   └── nixos.j2
│   ├── directory_context/                 🆕 Phase 2
│   │   ├── docs.j2
│   │   ├── modules.j2
│   │   ├── basb.j2
│   │   └── templates.j2
│   ├── local_context.j2                   🆕 Phase 3
│   ├── slash_commands/                    🆕 Phase 4
│   │   ├── rebuild-check.j2
│   │   ├── tool-info.j2
│   │   └── module-structure.j2
│   ├── mcp_config.j2                      🆕 Phase 5
│   └── usage_analytics.j2                 🆕 Phase 6
└── schemas.py                              🔄 EXTEND (each phase adds schemas)
```

---

## 📅 Implementation Phases

### Phase 1: Permissions Generator [7-8 hours]

**Status**: Detailed plan in `PERMISSIONS_AUTOMATION_SESSION_HANDOFF.md`

**Summary**:
- Generate `.claude/settings.local.json` per project
- Detect project type (Python/Node.js/Rust/NixOS)
- Security-first templates (deny sensitive paths)
- Preserve user customizations via marker
- Analyze git history for usage patterns

**Deliverables**:
- [x] PermissionsConfig schema
- [ ] PermissionsGenerator class
- [ ] ProjectDetector analyzer
- [ ] 5 templates (base + 4 project types)
- [ ] update-permissions-v2.py script
- [ ] Flake app: `update-permissions`

**Testing**:
- ai-project-orchestration (Python + TDD)
- nixos-config (NixOS)
- whisper-dictation (Rust)
- birthday-manager (Python)

**Next Session**: Start with schemas.py additions (code in handoff doc)

---

### Phase 2: Directory Context Generator [3-4 hours]

**Goal**: Auto-generate directory-level CLAUDE.md files

**New Files**:
```python
# claude_automation/generators/directory_context_generator.py
class DirectoryContextGenerator(BaseGenerator):
    """Generate directory-specific CLAUDE.md files."""

    def generate(self, config: DirectoryContextConfig) -> GenerationResult:
        # Analyze directory structure
        # Detect purpose (docs, modules, system, etc.)
        # Choose appropriate template
        # Render and write CLAUDE.md
        pass

# claude_automation/analyzers/directory_analyzer.py
class DirectoryAnalyzer:
    """Analyze directory to determine purpose and structure."""

    def analyze(self, path: Path) -> DirectoryInfo:
        # Count files by extension
        # Detect README presence
        # Identify primary purpose
        # Build file tree summary
        pass
```

**Schema** (add to `schemas.py`):
```python
class DirectoryType(str, Enum):
    DOCS = "docs"
    MODULES = "modules"
    BASB = "basb"
    TEMPLATES = "templates"
    SCRIPTS = "scripts"
    TESTS = "tests"
    UNKNOWN = "unknown"

class DirectoryInfo(BaseModel):
    path: Path
    type: DirectoryType
    file_count: int
    file_types: dict[str, int]  # {".py": 10, ".md": 5}
    has_readme: bool
    subdirectories: list[str]

class DirectoryContextConfig(BaseModel):
    directory_info: DirectoryInfo
    project_path: Path
    parent_context: Optional[str]  # Content from parent CLAUDE.md
    template_name: str = "base.j2"
```

**Templates**:

`templates/directory_context/docs.j2`:
```jinja2
# Documentation Directory Context

## Purpose
{{ purpose_description }}

## Structure
{% for subdir in subdirectories %}
- `{{ subdir }}/` - {{ subdir_descriptions[subdir] }}
{% endfor %}

## Do Not
- Add code examples longer than 20 lines (link to templates/)
- Create duplicate content (check existing docs first)
- Use temporal markers ("NEW 2025", "Week 1")
- Add personal opinions (keep factual)

## Guidelines
- Use markdown for all documentation
- Include code examples in fenced blocks
- Link to related documentation
- Keep files under 500 lines
```

`templates/directory_context/modules.j2`:
```jinja2
# NixOS Modules Directory Context

## Purpose
NixOS configuration modules for system configuration.

## Structure
- `core/` - Essential system packages and settings
- `home-manager/` - User-specific configurations
- `development/` - Development environment setup

## Do Not
- Modify files without running `nix flake check` first
- Add packages without descriptions
- Use absolute paths (use relative imports)
- Hardcode values (use variables)

## Conventions
- One module per concern (single responsibility)
- Import dependencies explicitly
- Comment complex configurations
- Group related options
```

**Script**: `update-directory-context-v2.py`
```python
#!/usr/bin/env python3
"""Generate directory-level CLAUDE.md files."""

from pathlib import Path
from claude_automation.generators.directory_context_generator import DirectoryContextGenerator
from claude_automation.analyzers.directory_analyzer import DirectoryAnalyzer

def main():
    project_root = Path.cwd()

    # Directories to generate context for
    target_dirs = [
        "docs",
        "modules",
        "basb-system",
        "templates"
    ]

    analyzer = DirectoryAnalyzer()
    generator = DirectoryContextGenerator()

    for dir_name in target_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue

        # Analyze directory
        info = analyzer.analyze(dir_path)

        # Build config
        config = DirectoryContextConfig(
            directory_info=info,
            project_path=project_root
        )

        # Generate CLAUDE.md
        result = generator.generate(config)
        print(f"Generated: {result.output_path}")
```

**Integration**: Add to `update-all` script in flake.nix

**Testing**:
- Verify `docs/CLAUDE.md` created
- Verify `modules/CLAUDE.md` created
- Check content accuracy
- Test with subdirectories

---

### Phase 3: Local Context Generator [2-3 hours]

**Goal**: Generate machine-specific `.claude/CLAUDE.local.md`

**New Files**:
```python
# claude_automation/generators/local_context_generator.py
class LocalContextGenerator(BaseGenerator):
    """Generate machine-specific context file."""

    def generate(self, config: LocalContextConfig) -> GenerationResult:
        # Gather system info
        # Detect current work
        # Check running services
        # Render template
        pass

# claude_automation/analyzers/system_analyzer.py
class SystemAnalyzer:
    """Analyze system hardware and state."""

    def get_hardware_info(self) -> HardwareInfo:
        # RAM, CPU, GPU, Disk
        pass

    def get_active_services(self) -> list[ServiceInfo]:
        # Docker, PostgreSQL, etc.
        pass

    def detect_current_work(self, project_path: Path) -> list[str]:
        # Git branches, uncommitted changes, recent files
        pass
```

**Schema**:
```python
class HardwareInfo(BaseModel):
    ram_gb: int
    cpu_model: str
    cpu_cores: int
    gpu_model: Optional[str]
    disk_total_gb: int
    disk_type: str  # "SSD", "HDD", "NVMe"

class ServiceInfo(BaseModel):
    name: str
    status: str  # "running", "stopped"
    containers: Optional[int]  # For Docker

class LocalContextConfig(BaseModel):
    hardware: HardwareInfo
    active_services: list[ServiceInfo]
    current_work: list[str]
    wip_notes: Optional[str]
    project_path: Path
```

**Template**: `templates/local_context.j2`
```jinja2
# Machine-Specific Context

> ⚠️ Auto-generated on every rebuild
> Gitignored - machine-specific information

## Hardware Specifications

- **RAM**: {{ hardware.ram_gb }}GB
- **CPU**: {{ hardware.cpu_model }} ({{ hardware.cpu_cores }} cores)
{% if hardware.gpu_model %}
- **GPU**: {{ hardware.gpu_model }}
{% endif %}
- **Disk**: {{ hardware.disk_total_gb }}GB {{ hardware.disk_type }}

## Active Services

{% for service in active_services %}
- **{{ service.name }}**: {{ service.status }}{% if service.containers %} ({{ service.containers }} containers){% endif %}
{% endfor %}

## Current Work

{% for item in current_work %}
- {{ item }}
{% endfor %}

{% if wip_notes %}
## WIP Notes

{{ wip_notes }}
{% endif %}

---
*Last updated: {{ timestamp }}*
```

**Script**: `update-local-context-v2.py`

**Integration**:
- Add to rebuild-nixos
- Create `.gitignore` entry for `CLAUDE.local.md`

**Testing**:
- Verify hardware detection accurate
- Check service detection (Docker, PostgreSQL)
- Test on different machines

---

### Phase 4: Slash Commands Generator [4-5 hours]

**Goal**: Auto-create custom slash commands from workflow analysis

**New Files**:
```python
# claude_automation/generators/slash_commands_generator.py
class SlashCommandsGenerator(BaseGenerator):
    """Generate custom slash commands from workflow patterns."""

    def generate(self, config: SlashCommandsConfig) -> GenerationResult:
        # Analyze workflows
        # Generate command files
        # Write to ~/.claude/commands/
        pass

# claude_automation/analyzers/workflow_analyzer.py
class WorkflowAnalyzer:
    """Analyze git history and scripts for common workflows."""

    def analyze_git_history(self, repo_path: Path, days: int = 90) -> list[CommandPattern]:
        # Parse git log
        # Extract commands from commit messages
        # Identify frequent sequences
        pass

    def detect_scripts(self, project_path: Path) -> list[ScriptInfo]:
        # Find executable files
        # Parse shebang
        # Extract purpose from comments
        pass
```

**Schema**:
```python
class CommandPattern(BaseModel):
    command: str
    frequency: int
    last_used: datetime
    contexts: list[str]  # Where it's used

class ScriptInfo(BaseModel):
    path: Path
    name: str
    purpose: Optional[str]
    requires_sudo: bool

class SlashCommandsConfig(BaseModel):
    command_patterns: list[CommandPattern]
    available_scripts: list[ScriptInfo]
    project_type: ProjectType
    output_dir: Path = Path.home() / ".claude" / "commands"
```

**Templates**: `templates/slash_commands/`

`rebuild-check.j2`:
```markdown
Check if NixOS configuration is valid before rebuild.

This command validates your NixOS flake without applying changes.

Steps:
1. Run `nix flake check` to validate syntax
2. Display any errors found
3. If valid, show summary of changes
4. Remind user to run `./rebuild-nixos` manually (requires sudo)

Usage: `/rebuild-check`
```

`tool-info.j2`:
```markdown
Explain a system tool in detail: $ARGUMENTS

Provides comprehensive information about any CLI tool on your system.

Information provided:
1. Tool description and purpose
2. Modern alternative (if exists)
3. Fish shell abbreviation (if configured)
4. Common usage examples
5. Related tools
6. Package manager source (nixpkgs, npm, cargo, etc.)

Usage: `/tool-info <tool-name>`
Example: `/tool-info fd`
```

`module-structure.j2`:
```markdown
Explain NixOS module organization: $ARGUMENTS

Shows structure and relationships for a NixOS module.

Information provided:
1. Module location in modules/ directory
2. Imports and dependencies
3. Key configuration options
4. Related modules
5. Usage examples

Usage: `/module-structure <module-name>`
Example: `/module-structure home-manager`
```

**Script**: `update-slash-commands-v2.py`

**Integration**:
- Run weekly (not every rebuild)
- Preserve user-created commands
- Add marker: `# AUTO-GENERATED` vs `# USER-CREATED`

**Testing**:
- Create commands
- Test invocation: `/rebuild-check`, `/tool-info fd`
- Verify $ARGUMENTS substitution
- Check preservation of user commands

---

### Phase 5: MCP Config Generator [5-6 hours]

**Goal**: Auto-configure MCP servers based on available tools

**New Files**:
```python
# claude_automation/generators/mcp_config_generator.py
class MCPConfigGenerator(BaseGenerator):
    """Generate MCP server configuration."""

    def generate(self, config: MCPConfigConfig) -> GenerationResult:
        # Detect available MCP servers
        # Build configuration
        # Merge with existing config
        # Write to ~/.claude.json
        pass

# claude_automation/analyzers/mcp_detector.py
class MCPDetector:
    """Detect available MCP servers."""

    def detect_npm_servers(self) -> list[MCPServerInfo]:
        # Check @modelcontextprotocol/server-* packages
        pass

    def detect_custom_servers(self) -> list[MCPServerInfo]:
        # Scan ~/.local/bin/, ~/bin/ for MCP servers
        pass
```

**Schema**:
```python
class MCPServerInfo(BaseModel):
    name: str
    type: str  # "npm", "python", "binary"
    command: str
    args: list[str]
    available: bool
    description: Optional[str]

class MCPConfigConfig(BaseModel):
    available_servers: list[MCPServerInfo]
    project_path: Optional[Path]
    existing_config: Optional[dict]
    username: str
```

**Template**: `templates/mcp_config.j2`
```jinja2
{
  "_generated_by": "claude-nixos-automation",
  "_timestamp": "{{ timestamp }}",
  "mcpServers": {
    {% for server in available_servers %}
    "{{ server.name }}": {
      "command": "{{ server.command }}",
      "args": {{ server.args | tojson }}
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  }
}
```

**MCP Servers to Auto-Configure**:
1. **filesystem**: `@modelcontextprotocol/server-filesystem`
2. **git**: `@modelcontextprotocol/server-git`
3. **serena**: Already configured (preserve)
4. **mcp-nixos**: Already configured (preserve)
5. **nixos-introspection**: Custom (if created in bonus)

**Script**: `update-mcp-config-v2.py`

**Integration**:
- Run on rebuild
- Merge with existing ~/.claude.json (preserve user settings)
- Prompt user for review if adding new servers

**Bonus: Custom NixOS Introspection MCP**

Create `~/.local/bin/nixos-mcp-server.py`:
```python
#!/usr/bin/env python3
"""MCP server for NixOS system introspection."""

import json
import subprocess
from typing import Any

class NixOSMCPServer:
    """Provide NixOS system information via MCP."""

    def systemctl_status(self, service: str) -> dict[str, Any]:
        """Get systemd service status."""
        result = subprocess.run(
            ["systemctl", "status", service],
            capture_output=True,
            text=True
        )
        return {
            "service": service,
            "status": result.stdout,
            "active": "active" in result.stdout
        }

    def nixos_version(self) -> str:
        """Get NixOS version."""
        result = subprocess.run(
            ["nixos-version"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def list_kernel_modules(self) -> list[str]:
        """List active kernel modules."""
        result = subprocess.run(
            ["lsmod"],
            capture_output=True,
            text=True
        )
        return [line.split()[0] for line in result.stdout.split("\n")[1:]]

# MCP server implementation...
```

**Testing**:
- Verify filesystem MCP configured
- Test git MCP operations
- Check custom server detection
- Verify user config preservation

---

### Phase 6: Usage Analytics Generator [6-7 hours]

**Goal**: Track tool usage, optimize CLAUDE.md content

**New Files**:
```python
# claude_automation/generators/usage_analytics_generator.py
class UsageAnalyticsGenerator(BaseGenerator):
    """Generate usage analytics and optimize CLAUDE.md."""

    def generate(self, config: UsageAnalyticsConfig) -> GenerationResult:
        # Collect usage data
        # Calculate statistics
        # Generate insights
        # Update system CLAUDE.md with "Frequently Used" section
        pass

# claude_automation/analyzers/usage_tracker.py
class UsageTracker:
    """Track CLI tool usage from shell history."""

    def analyze_fish_history(self, days: int = 30) -> list[UsageMetric]:
        # Parse ~/.local/share/fish/fish_history
        # Count command frequency
        # Calculate usage patterns
        pass

    def analyze_git_commits(self, repo_path: Path, days: int = 30) -> list[UsageMetric]:
        # Parse git log
        # Extract commands from commit messages
        # Identify trends
        pass
```

**Schema**:
```python
class UsageMetric(BaseModel):
    command: str
    count: int
    last_used: datetime
    percentage: float  # Of total commands
    category: str  # "git", "file-ops", "system", "development"

class UsageAnalyticsConfig(BaseModel):
    usage_metrics: list[UsageMetric]
    total_commands: int
    analysis_period_days: int
    threshold_percentage: float = 1.0  # Only show tools used >1%
    output_section_template: str = "usage_analytics.j2"
```

**Template**: `templates/usage_analytics.j2`
```jinja2
## 📊 Your Most-Used Tools (Last {{ analysis_period_days }} Days)

**Total commands analyzed**: {{ total_commands }}

### Top 20 Tools ({{ top_20_percentage }}% of usage)

{% for metric in top_20_metrics %}
{{ loop.index }}. **{{ metric.command }}** ({{ metric.count }} uses, {{ metric.percentage }}%)
   - Category: {{ metric.category }}
   - Last used: {{ metric.last_used.strftime('%Y-%m-%d') }}
{% endfor %}

### Rarely Used (Consider removing or replacing)

{% for metric in rarely_used %}
- **{{ metric.command }}** ({{ metric.count }} uses) - Consider: {{ metric.suggestion }}
{% endfor %}

---
*Analysis period: {{ start_date }} to {{ end_date }}*
*Next update: Weekly on rebuild*
```

**Script**: `update-usage-analytics-v2.py`

**Privacy & Opt-Out**:
```bash
# Disable analytics
export CLAUDE_AUTOMATION_ANALYTICS=false

# Or via config file
echo '{"analytics_enabled": false}' > ~/.claude/analytics-config.json
```

**Integration**:
- Cron job: Weekly
- Update system CLAUDE.md with generated section
- Skip if opted out
- Async processing (don't block rebuild)

**Testing**:
- Parse fish history correctly
- Calculate percentages accurately
- Verify privacy (no file paths in logs)
- Test opt-out mechanism
- Check weekly schedule

---

## 🔄 Complete Integration Flow

**Updated `~/nixos-config/rebuild-nixos`**:

```bash
# ... existing rebuild steps ...

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Updating Claude Code Configurations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ~/nixos-config

# Phase 1: Permissions (project-specific)
echo "  🔐 Optimizing permissions..."
if nix run github:jacopone/claude-nixos-automation#update-permissions; then
    echo "    ✅ Permissions optimized"
else
    echo "    ⚠️  Permissions update failed (continuing)"
fi

# Existing: System + Project CLAUDE.md
echo "  📄 Updating system and project CLAUDE.md..."
if nix run github:jacopone/claude-nixos-automation#update-all; then
    echo "    ✅ System CLAUDE.md: ~/.claude/CLAUDE.md"
    echo "    ✅ Project CLAUDE.md: ./CLAUDE.md"
else
    echo "    ⚠️  CLAUDE.md update failed (continuing)"
fi

# Phase 2: Directory context
echo "  📁 Generating directory-level CLAUDE.md files..."
if nix run github:jacopone/claude-nixos-automation#update-directory-context; then
    echo "    ✅ Directory context updated"
else
    echo "    ⚠️  Directory context update failed (continuing)"
fi

# Phase 3: Local context
echo "  💻 Updating machine-specific context..."
if nix run github:jacopone/claude-nixos-automation#update-local-context; then
    echo "    ✅ Local context: .claude/CLAUDE.local.md"
else
    echo "    ⚠️  Local context update failed (continuing)"
fi

# Phase 4: Slash commands (weekly only)
if [[ ! -d ~/.claude/commands ]] || [[ $(find ~/.claude/commands -name "*.md" -mtime -7 | wc -l) -eq 0 ]]; then
    echo "  ⚡ Generating custom slash commands..."
    if nix run github:jacopone/claude-nixos-automation#update-slash-commands; then
        echo "    ✅ Slash commands updated"
    else
        echo "    ⚠️  Slash commands update failed (continuing)"
    fi
else
    echo "  ⚡ Slash commands: Up to date (checked weekly)"
fi

# Phase 5: MCP configuration
echo "  🔌 Configuring MCP servers..."
if nix run github:jacopone/claude-nixos-automation#update-mcp-config; then
    echo "    ✅ MCP servers configured"
else
    echo "    ⚠️  MCP config update failed (continuing)"
fi

# Phase 6: Usage analytics (async, weekly)
if [[ "$CLAUDE_AUTOMATION_ANALYTICS" != "false" ]]; then
    if [[ $(date +%u) -eq 1 ]]; then  # Monday
        echo "  📊 Running usage analytics (async)..."
        nix run github:jacopone/claude-nixos-automation#update-usage-analytics &
        echo "    ✅ Analytics running in background"
    else
        echo "  📊 Usage analytics: Runs weekly (Monday)"
    fi
else
    echo "  📊 Usage analytics: Disabled (CLAUDE_AUTOMATION_ANALYTICS=false)"
fi

echo ""
echo "✅ All Claude Code optimizations complete!"
echo ""
```

---

## 📋 Implementation Checklist

### Phase 1: Permissions ✅ [Planned]
- [ ] Review PERMISSIONS_AUTOMATION_SESSION_HANDOFF.md
- [ ] Add PermissionsConfig schema to schemas.py
- [ ] Create PermissionsGenerator
- [ ] Create ProjectDetector analyzer
- [ ] Create 5 templates (base, python, nodejs, rust, nixos)
- [ ] Create update-permissions-v2.py
- [ ] Update flake.nix
- [ ] Test on 4 projects
- [ ] Document in README.md

### Phase 2: Directory Context
- [ ] Add DirectoryContextConfig schema to schemas.py
- [ ] Create DirectoryContextGenerator
- [ ] Create DirectoryAnalyzer
- [ ] Create 4 templates (docs, modules, basb, templates)
- [ ] Create update-directory-context-v2.py
- [ ] Update flake.nix
- [ ] Test on nixos-config
- [ ] Document in README.md

### Phase 3: Local Context
- [ ] Add LocalContextConfig schema to schemas.py
- [ ] Create LocalContextGenerator
- [ ] Create SystemAnalyzer
- [ ] Create local_context.j2 template
- [ ] Create update-local-context-v2.py
- [ ] Update flake.nix
- [ ] Add .gitignore entry
- [ ] Test on 2 machines
- [ ] Document in README.md

### Phase 4: Slash Commands
- [ ] Add SlashCommandsConfig schema to schemas.py
- [ ] Create SlashCommandsGenerator
- [ ] Create WorkflowAnalyzer
- [ ] Create 3+ command templates
- [ ] Create update-slash-commands-v2.py
- [ ] Update flake.nix
- [ ] Test command invocation
- [ ] Document in README.md

### Phase 5: MCP Configuration
- [ ] Add MCPConfigConfig schema to schemas.py
- [ ] Create MCPConfigGenerator
- [ ] Create MCPDetector
- [ ] Create mcp_config.j2 template
- [ ] Create update-mcp-config-v2.py
- [ ] Update flake.nix
- [ ] (Bonus) Create nixos-mcp-server.py
- [ ] Test with 3+ MCP servers
- [ ] Document in README.md

### Phase 6: Usage Analytics
- [ ] Add UsageAnalyticsConfig schema to schemas.py
- [ ] Create UsageAnalyticsGenerator
- [ ] Create UsageTracker
- [ ] Create usage_analytics.j2 template
- [ ] Create update-usage-analytics-v2.py
- [ ] Update flake.nix
- [ ] Implement opt-out mechanism
- [ ] Test privacy (no sensitive data)
- [ ] Document in README.md

### Integration
- [ ] Update rebuild-nixos with all phases
- [ ] Test complete rebuild flow
- [ ] Verify all generators run successfully
- [ ] Check performance (rebuild time increase)
- [ ] Document troubleshooting

### Documentation
- [ ] Update main README.md
- [ ] Create ARCHITECTURE.md explaining all 6 generators
- [ ] Create USAGE.md with examples
- [ ] Create TROUBLESHOOTING.md
- [ ] Update CHANGELOG.md

---

## 🎯 Success Metrics

### Quantitative
- [ ] Token usage reduced by 30-40% (measure before/after)
- [ ] All 6 generators implemented and tested
- [ ] 100% best practices coverage (8/8 areas)
- [ ] Zero manual maintenance required
- [ ] <2 second overhead per generator on rebuild

### Qualitative
- [ ] Claude Code context quality improved (subjective)
- [ ] Fewer "I don't know about that tool" responses
- [ ] Better understanding of project structure
- [ ] More relevant suggestions
- [ ] Workflow efficiency increased

### Coverage
- [ ] ✅ System-wide CLAUDE.md (EXISTS)
- [ ] ✅ Project-level CLAUDE.md (EXISTS)
- [ ] 🎯 Permissions optimization (Phase 1)
- [ ] 🎯 Directory context (Phase 2)
- [ ] 🎯 Local context (Phase 3)
- [ ] 🎯 Slash commands (Phase 4)
- [ ] 🎯 MCP auto-config (Phase 5)
- [ ] 🎯 Usage analytics (Phase 6)

---

## 🔐 Security & Privacy

### Security
- **Permissions**: Deny sensitive paths by default (.env, .ssh/, credentials)
- **MCP Config**: User review required for external servers
- **Scripts**: Never execute untrusted code
- **Backups**: All changes reversible via .backups/

### Privacy
- **Analytics**: Local-only, no cloud transmission
- **Opt-out**: CLAUDE_AUTOMATION_ANALYTICS=false
- **Data**: No file paths, no sensitive information logged
- **Transparency**: Open source, auditable code

### User Control
- **Markers**: _user_customized flag preserves manual edits
- **Backups**: Every change backed up to .backups/
- **Review**: Changes shown in rebuild-nixos output
- **Rollback**: Easy restoration from backups

---

## 📚 Additional Resources

### Research Sources
- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [ClaudeLog Documentation](https://claudelog.com/)
- [Builder.io Claude Code Guide](https://www.builder.io/blog/claude-code)
- [Simon Willison's Best Practices](https://simonwillison.net/2025/Apr/19/claude-code-best-practices/)

### Related Documentation
- `PERMISSIONS_AUTOMATION_SESSION_HANDOFF.md` - Phase 1 details
- `README.md` - Package overview
- `~/nixos-config/docs/architecture/CLAUDE_ORCHESTRATION.md` - Three-level architecture
- `~/nixos-config/docs/THE_CLOSED_LOOP.md` - Closed-loop system explanation

### Testing Projects
- `ai-project-orchestration` - Python with TDD
- `nixos-config` - NixOS configuration
- `whisper-dictation` - Rust project
- `birthday-manager` - Python CLI tool

---

## ⏭️ Next Steps

1. **Start with Phase 1**: Implement permissions generator (foundation)
2. **Incremental rollout**: One phase per session/day
3. **Test thoroughly**: Each phase on multiple projects
4. **Document as you go**: Update README after each phase
5. **User feedback**: Adjust based on actual usage
6. **Iterate**: Refine templates and analyzers based on data

---

**This roadmap creates the most context-aware AI development system possible.**

**Timeline**: 6 phases × ~5 hours each = ~30 hours total
**Expected completion**: 2-3 weeks of focused development
**Impact**: 100% best practices coverage, 40% token reduction, zero manual maintenance

---

*Last Updated: 2025-10-07*
*Status: Ready to implement*
*Next: Begin Phase 1 (Permissions)*
