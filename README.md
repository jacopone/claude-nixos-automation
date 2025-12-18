---
status: active
created: 2024-01-01
updated: 2025-12-18
type: reference
lifecycle: persistent
---

# Claude NixOS Automation

> Your Claude Code learns from you

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/nixos-unstable-blue.svg)](https://nixos.org/)
[![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen.svg)](TESTING.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Sessions](https://img.shields.io/badge/sessions%20analyzed-469+-purple.svg)](#analytics)

## The Problem

Every Claude Code session:
- "Allow this command?" → Click yes → Repeat 50 times
- No visibility into which tools you actually use
- No memory of your permission patterns
- MCP servers running but never called

**Permission fatigue is real. Your AI should learn your preferences.**

## The Solution

This tool analyzes your Claude Code usage and generates intelligent configurations:

```
469+ sessions analyzed
 │
 ├─→ Permission patterns detected → auto-approve frequent commands
 ├─→ Tool usage tracked → identify dormant packages (120 unused)
 ├─→ MCP utilization monitored → suggest project vs system level
 └─→ CLAUDE.md generated → full system context for AI
```

**Result**: Claude Code that knows your workflow from day one.

## Key Features

| Feature | What It Does |
|---------|--------------|
| **Permission Learning** | Analyzes your approval patterns, suggests auto-approvals for frequent commands |
| **Tool Usage Analytics** | Tracks human vs AI tool usage over 30 days, identifies dormant packages |
| **MCP Optimization** | Monitors server utilization, recommends project-level vs system-level placement |
| **Smart Permissions** | Generates auto-approval patterns based on your project type (Python/Node/Rust/Nix) |
| **Zero-Drift Docs** | Keeps CLAUDE.md in sync with your actual NixOS configuration |

## Analytics Output

After running, you get visibility into your Claude Code usage:

```
📦 System Tool Usage
Installed: 145 tools | Used: 25 (17%) | Period: 30 days

Top 5 tools:
- git: 278 uses (H:27 C:251)
- devenv: 163 uses (H:15 C:148)
- gh: 121 uses (H:0 C:121)

⚠️ 120 dormant tools (unused in last 30 days)

Human vs Claude:
- 12 tools used by humans
- 18 tools used by Claude
```

## Integration with nixos-config

This is "the brain" behind [nixos-config](https://github.com/jacopone/nixos-config). On every rebuild:

```bash
./rebuild-nixos
    │
    ├─→ Parses Nix config → extracts 145 tools with descriptions
    ├─→ Runs permission analyzer → detects your patterns
    ├─→ Updates analytics → tool usage over 30 days
    ├─→ Generates suggestions → permission auto-approvals
    └─→ Creates CLAUDE.md → full context for Claude Code
```

## Quick Start

### Installation

Add to your flake inputs:

```nix
{
  inputs.claude-automation.url = "github:jacopone/claude-nixos-automation";
}
```

### Generate Configuration

```bash
# Generate all Claude Code configuration files
nix run github:jacopone/claude-nixos-automation#update-all
```

This creates:

| File | Location | Purpose |
|------|----------|---------|
| System docs | `~/.claude/CLAUDE.md` | Tools, commands, policies |
| Permissions | `.claude/settings.local.json` | Auto-approval patterns |
| Analytics | `.claude/tool-analytics.md` | Usage tracking |
| MCP stats | `.claude/mcp-analytics.md` | Server utilization |

## Available Commands

```bash
# Main entry point - generates all config
nix run .#update-all

# Individual generators
nix run .#update-system            # ~/.claude/CLAUDE.md
nix run .#update-project           # ./CLAUDE.md
nix run .#update-permissions       # .claude/settings.local.json
nix run .#update-local-context     # .claude/CLAUDE.local.md

# Analytics & learning
nix run .#analyze-permissions      # Suggest auto-approvals
nix run .#analyze-tool-usage       # Generate usage report
nix run .#check-data-health        # Monitor learning data
```

## Project Detection

Automatically generates appropriate permissions for your project type:

| Manifest | Project Type | Generated Permissions |
|----------|--------------|----------------------|
| `pyproject.toml` | Python | pytest, ruff, uv, black |
| `package.json` | Node.js | npm, eslint, prettier |
| `Cargo.toml` | Rust | cargo, clippy, rustfmt |
| `flake.nix` | NixOS | nix build, nix flake check |

## Architecture

```
claude_automation/
├── cli/              # Command-line entry points
├── generators/       # Content generators (system, project, permissions)
├── analyzers/        # Learning & pattern detection
│   ├── permission_patterns.py   # Learns from your approvals
│   ├── tool_usage.py            # Tracks human vs AI usage
│   └── mcp_utilization.py       # MCP server analytics
├── templates/        # Jinja2 templates (27 templates)
├── schemas/          # Pydantic data models (10+ schemas)
└── validators/       # Content validation
```

### Documentation

| Document | Description |
|----------|-------------|
| [Project Constitution](docs/architecture/CONSTITUTION.md) | Design principles and decisions |
| [Implementation Summary](docs/architecture/IMPLEMENTATION_COMPLETE.md) | What was built and why |

### Specifications

| Spec | Description |
|------|-------------|
| [001: Source/Artifact Architecture](specs/001-source-artifact-architecture/spec.md) | Template and output structure |
| [002: Code Quality Refactoring](specs/002-code-quality-refactoring/spec.md) | Quality gates and standards |
| [003: Documentation Governance](specs/003-doc-governance-cleanup/spec.md) | Doc lifecycle management |

## Development

```bash
# Enter development shell
nix develop

# Run test suite (59 tests)
pytest -v

# Test categories
pytest tests/test_schemas.py -v      # Schema validation (28 tests)
pytest tests/test_templates.py -v    # Template rendering (24 tests)
pytest tests/test_integration.py -v  # End-to-end workflows (7 tests)
```

See [TESTING.md](TESTING.md) for detailed test documentation.

## Related

- [nixos-config](https://github.com/jacopone/nixos-config) - NixOS configuration that uses this automation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT — See [LICENSE](LICENSE)
