---
status: active
created: 2024-01-01
updated: 2025-12-31
type: reference
lifecycle: persistent
---

# Claude NixOS Automation

> The permission learning engine for Claude Code on NixOS

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/nixos-unstable-blue.svg)](https://nixos.org/)
[![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen.svg)](TESTING.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What This Does

This is **the brain** behind [nixos-config](https://github.com/jacopone/nixos-config). It:

1. **Learns your permission patterns** from actual approval behavior
2. **Auto-generates allow rules** for high-confidence commands
3. **Tracks tool usage** (human vs Claude, dormant detection)
4. **Keeps documentation in sync** with your NixOS configuration

**Result:** Permission prompts decrease over time as the system learns your workflow.

## How Permission Learning Works

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA COLLECTION (continuous)                                   │
│                                                                 │
│  Claude Code session logs → ~/.claude/projects/*/*.jsonl        │
│  Every tool approval is recorded with:                          │
│    - Tool type (Bash, Read, Write, Edit)                        │
│    - Command pattern                                            │
│    - Timestamp                                                  │
│    - Project context                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PATTERN DETECTION (on rebuild)                                 │
│                                                                 │
│  PermissionPatternDetector analyzes:                            │
│    - Frequency: "git *" approved 89 times                       │
│    - Consistency: 98% approval rate (vs 2% deny)                │
│    - Recency: Used in last 7 days                               │
│                                                                 │
│  Confidence = frequency × consistency × recency                 │
│  Threshold: 0.6+ → suggest auto-approval                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  INTERACTIVE APPROVAL (user in control)                         │
│                                                                 │
│  ./rebuild-nixos → Adaptive learning phase                      │
│                                                                 │
│  "Pattern detected: Bash(git:*) - 94% confidence"               │
│  "Apply this auto-approval? [y/n/review]"                       │
│                                                                 │
│  User approves → Added to .claude/settings.local.json           │
│  User rejects → Pattern suppressed for 30 days                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  NEXT SESSION                                                   │
│                                                                 │
│  "git status" → Auto-approved. No prompt.                       │
│  "git push --force" → Still prompts (not in learned pattern)    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | What It Does |
|---------|--------------|
| **Permission Pattern Detection** | Learns from your approvals, generates allow rules with confidence scoring |
| **Tool Usage Analytics** | Tracks 30-day usage, human vs Claude breakdown, dormant tool detection |
| **MCP Server Optimization** | Monitors utilization, suggests project vs system level placement |
| **Zero-Drift Documentation** | Auto-generates CLAUDE.md from your Nix config - always current |
| **Session Lifecycle Tracking** | RAW → ANALYZED → IMPLEMENTED - value-aware cleanup |

## Integration with nixos-config

On every `./rebuild-nixos`:

```
Phase 5: Update Claude configs
  ├─→ Parse packages.nix → extract 130+ tools with descriptions
  ├─→ Generate CLAUDE.md → full system context
  └─→ Update permissions → project-specific allow rules

Phase 6: Adaptive learning
  ├─→ Parse session logs → extract approval patterns
  ├─→ Detect high-confidence patterns → suggest auto-approvals
  └─→ Interactive review → user approves/rejects
```

## Quick Start

### As a Flake Input

```nix
{
  inputs.claude-automation.url = "github:jacopone/claude-nixos-automation";
}
```

### Generate Configuration

```bash
# Generate all Claude Code configuration files
nix run github:jacopone/claude-nixos-automation#update-all

# Run permission learning cycle
nix run github:jacopone/claude-nixos-automation#run-adaptive-learning
```

### Output Files

| File | Location | Purpose |
|------|----------|---------|
| System CLAUDE.md | `~/.claude/CLAUDE.md` | Global tool inventory, policies |
| Project CLAUDE.md | `./CLAUDE.md` | Project-specific context |
| Permissions | `.claude/settings.local.json` | Auto-generated allow rules |
| Tool Analytics | `.claude/tool-analytics.md` | 30-day usage report |
| MCP Analytics | `.claude/mcp-analytics.md` | Server utilization stats |

## Available Commands

```bash
# Main entry points
nix run .#update-all              # Generate all config files
nix run .#run-adaptive-learning   # Run permission learning cycle

# Individual generators
nix run .#update-system           # ~/.claude/CLAUDE.md
nix run .#update-project          # ./CLAUDE.md
nix run .#update-permissions      # .claude/settings.local.json
nix run .#update-local-context    # .claude/CLAUDE.local.md

# Analytics
nix run .#update-tool-analytics   # Generate usage report
nix run .#update-mcp-usage-analytics  # MCP server stats
nix run .#check-data-health       # Monitor learning data size
```

## Analytics Output

### Tool Usage Report

```
📦 System Tool Usage
Installed: 131 tools | Used: 34 (26%) | Period: 30 days

Top 5 tools:
- git: 1017 uses (H:28 C:989)
- devenv: 380 uses (H:7 C:373)
- gh: 207 uses (H:6 C:201)
- fd: 152 uses (H:0 C:152)
- rg: 100 uses (H:0 C:100)

⚠️ 97 dormant tools (unused in last 30 days)
```

### Permission Learning

```
Permission patterns detected:
- Bash(git:*) → 94% confidence (89 approvals)
- Bash(fd:*) → 87% confidence (152 approvals)
- Read(/home/user/**) → 91% confidence (340 approvals)
```

## Architecture

```
claude_automation/
├── cli/                    # Command-line entry points
│   └── run_adaptive_learning.py  # Main learning cycle
├── core/
│   ├── adaptive_system_engine.py # Orchestrates 7 analyzers
│   ├── interactive_approval_ui.py # User review interface
│   └── improvement_applicator.py  # Applies approved changes
├── analyzers/
│   ├── permission_pattern_detector.py  # Pattern learning
│   ├── tool_usage_analyzer.py         # H vs C tracking
│   ├── mcp_utilization_analyzer.py    # Server stats
│   └── session_lifecycle_tracker.py   # Value-aware cleanup
├── generators/
│   ├── system_generator.py     # ~/.claude/CLAUDE.md
│   ├── project_generator.py    # ./CLAUDE.md
│   └── permissions_generator.py # settings.local.json
├── templates/              # 27 Jinja2 templates
└── schemas/               # 10+ Pydantic models
```

## The Learning System

### 7 Parallel Analyzers

The adaptive learning system runs 7 analyzers in parallel:

1. **Permission Patterns** - Learn from approval behavior
2. **MCP Utilization** - Suggest project vs system level
3. **Context Optimization** - Remove unused CLAUDE.md sections
4. **Workflow Patterns** - Bundle repeated command sequences
5. **Instruction Effectiveness** - Improve low-compliance policies
6. **Cross-Project Transfer** - Apply patterns from similar projects
7. **Meta-Learning** - Calibrate detection thresholds

### Session Lifecycle

Sessions progress through lifecycle stages:

```
RAW → ANALYZED → INSIGHTS_GENERATED → IMPLEMENTED
```

Only IMPLEMENTED sessions are safe to delete (value has been extracted).

## Development

```bash
# Enter development shell
nix develop

# Run test suite (59 tests)
pytest -v

# Format code
ruff format .
ruff check --fix .
```

See [TESTING.md](TESTING.md) for detailed test documentation.

## Documentation

| Document | Description |
|----------|-------------|
| [CONSTITUTION.md](docs/architecture/CONSTITUTION.md) | Design principles |
| [IMPLEMENTATION_COMPLETE.md](docs/architecture/IMPLEMENTATION_COMPLETE.md) | What was built |

## Related

- **[nixos-config](https://github.com/jacopone/nixos-config)** - The system configuration that uses this automation

## License

MIT — See [LICENSE](LICENSE)
