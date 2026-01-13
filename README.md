---
status: active
created: 2024-01-01
updated: 2026-01-12
type: reference
lifecycle: persistent
---

# Claude NixOS Automation

> The permission learning engine for Claude Code on NixOS

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/nixos-unstable-blue.svg)](https://nixos.org/)
[![Tests](https://img.shields.io/badge/tests-212%20passing-brightgreen.svg)](TESTING.md)
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
│  PATTERN DETECTION + TIER CLASSIFICATION                        │
│                                                                 │
│  PermissionPatternDetector analyzes & classifies:               │
│                                                                 │
│  TIER_1_SAFE (read-only):     git status, fd, rg, cat, pytest   │
│  TIER_2_MODERATE (writes):    git push, npm, nix build          │
│  TIER_3_RISKY (destructive):  git --force, cloud CLIs, sudo     │
│  CROSS_FOLDER (broad trust):  Tools used in 2+ projects         │
│                                                                 │
│  Confidence thresholds: TIER_1=0.3, TIER_2=0.4, TIER_3=0.5      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER-BASED ROUTING                                             │
│                                                                 │
│  TIER_1_SAFE + CROSS_FOLDER → ~/.claude/settings.json (GLOBAL)  │
│  TIER_2_MODERATE + TIER_3   → .claude/settings.local.json       │
│                                                                 │
│  Philosophy: "If you approve a tool multiple times across       │
│  different contexts, you trust that tool." (Boris Cherny)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  NEXT SESSION (any project)                                     │
│                                                                 │
│  "git status" → Auto-approved globally. No prompt.              │
│  "fd -e py"   → Auto-approved globally. No prompt.              │
│  "git push"   → Per-project rule or prompt.                     │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | What It Does |
|---------|--------------|
| **Tier-Based Permission Routing** | TIER_1_SAFE → global, TIER_2/3 → per-project. Learn once, apply everywhere. |
| **Cross-Folder Detection** | Tools used in 2+ projects auto-promote to global settings |
| **GlobalPermissionsManager** | Manages `~/.claude/settings.json` with backup, deduplication, wildcard coverage |
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
| **Global Permissions** | `~/.claude/settings.json` | TIER_1_SAFE rules (all projects) |
| Project CLAUDE.md | `./CLAUDE.md` | Project-specific context |
| Project Permissions | `.claude/settings.local.json` | TIER_2/3 rules (this project) |
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

# Permission migration (TIER_1 → global)
python -m claude_automation.cli.migrate_permissions --dry-run   # Preview
python -m claude_automation.cli.migrate_permissions --execute   # Apply
python -m claude_automation.cli.migrate_permissions --execute --skip-project-paths

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
│   ├── run_adaptive_learning.py  # Main learning cycle
│   └── migrate_permissions.py    # TIER_1 → global migration
├── core/
│   ├── adaptive_system_engine.py # Orchestrates 7 analyzers
│   ├── interactive_approval_ui.py # User review interface
│   └── improvement_applicator.py  # Applies approved changes
├── analyzers/
│   ├── permission_pattern_detector.py  # Pattern learning + tier classification
│   ├── tool_usage_analyzer.py         # H vs C tracking
│   ├── mcp_utilization_analyzer.py    # Server stats
│   └── session_lifecycle_tracker.py   # Value-aware cleanup
├── generators/
│   ├── global_permissions_manager.py  # ~/.claude/settings.json (TIER_1)
│   ├── intelligent_permissions_generator.py  # Tier-based routing
│   ├── system_generator.py     # ~/.claude/CLAUDE.md
│   ├── project_generator.py    # ./CLAUDE.md
│   └── permissions_generator.py # .claude/settings.local.json
├── hooks/
│   └── permission_auto_learner.py  # Auto-learn with tier routing
├── templates/              # 27 Jinja2 templates
└── schemas/               # 10+ Pydantic models
```

## Tier-Based Permission System

Permissions are classified into tiers that determine where rules are applied:

| Tier | Confidence | Destination | Examples |
|------|------------|-------------|----------|
| **TIER_1_SAFE** | 0.30 | `~/.claude/settings.json` (global) | git status/log/diff, fd, rg, bat, cat, pytest |
| **TIER_2_MODERATE** | 0.40 | `.claude/settings.local.json` | git add/commit/push, npm, nix build |
| **TIER_3_RISKY** | 0.50 | `.claude/settings.local.json` | git --force, cloud CLIs, sudo |
| **CROSS_FOLDER** | 0.30+ | `~/.claude/settings.json` (global) | Any tool used in 2+ projects |

**Philosophy:** Read-only tools are inherently safe. Once you've approved `fd` in one project, you trust `fd` everywhere. Write operations remain per-project for safety.

### Cross-Folder Detection

When a tool is used across multiple projects (2+ folders, 3+ total approvals), it's promoted to global:

```
Project A: "curl api.example.com" approved
Project B: "curl api.other.com" approved
Project C: "curl localhost:8000" approved

→ Pattern detected: CrossFolder_curl
→ Added to ~/.claude/settings.json: Bash(curl:*)
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
