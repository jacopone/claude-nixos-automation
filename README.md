---
status: active
created: 2024-01-01
updated: 2025-11-30
type: reference
lifecycle: persistent
---

# Claude NixOS Automation

Automated CLAUDE.md and permission configuration generator for NixOS systems.

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/nixos-unstable-blue.svg)](https://nixos.org/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](TESTING.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## What It Does

This tool generates Claude Code configuration files by analyzing your NixOS system:

- **CLAUDE.md generation** - Documents installed tools, command substitutions, and system info
- **Permission detection** - Detects project type (Python/Node/Rust/NixOS) and generates appropriate auto-approval patterns
- **Directory context** - Creates purpose-specific CLAUDE.md files for subdirectories
- **Slash commands** - Generates workflow shortcuts from git commit patterns
- **Tool filtering** - Includes only tools relevant to Claude (filters out fonts, libraries)

## Installation

### As Nix Flake Input

```nix
{
  inputs.claude-automation.url = "github:jacopone/claude-nixos-automation";
}
```

### Generate Configuration

```bash
# Generate all configurations
nix run github:jacopone/claude-nixos-automation#update-all

# Or run individual phases
nix run .#update-permissions       # Project permissions
nix run .#update-directory-context # Directory-specific docs
nix run .#update-local-context     # Machine-specific info
nix run .#update-slash-commands    # Workflow shortcuts
```

## Features

### Configuration Generation

| Phase | Output | Description |
|-------|--------|-------------|
| Permissions | `.claude/settings.local.json` | Auto-approval patterns for detected project type |
| System CLAUDE.md | `~/.claude/CLAUDE.md` | System tools, command substitutions, policies |
| Directory Context | `<dir>/CLAUDE.md` | Purpose-specific guidelines per directory |
| Local Context | `.claude/CLAUDE.local.md` | Machine-specific info (gitignored) |
| Slash Commands | `~/.claude/commands/*.md` | Workflow shortcuts from git patterns |

### Project Type Detection

Detects project type from manifest files and generates appropriate permissions:

- **Python** (pyproject.toml) → pytest, ruff, black patterns
- **Node.js** (package.json) → npm, eslint, prettier patterns
- **Rust** (Cargo.toml) → cargo, clippy, rustfmt patterns
- **NixOS** (flake.nix) → nix, rebuild patterns

### Tool Relevance Filtering

Filters documented tools by relevance to Claude Code:

- **Essential** - Tool substitutions (fd→find, eza→ls, bat→cat, rg→grep)
- **High** - Non-obvious tools with unique syntax (jless, miller, pgcli)
- **Filtered out** - System libraries, fonts, build dependencies

## Usage

### With NixOS Rebuild

If using with [nixos-config](https://github.com/jacopone/nixos-config), the rebuild script calls this automatically:

```bash
./rebuild-nixos  # Phase 4 runs: nix run #update-all
```

### Standalone

```bash
# Full generation
nix run .#update-all

# Check generated output
bat ~/.claude/CLAUDE.md
```

### Adaptive Learning (Optional)

Analyzes usage patterns to suggest permission and context optimizations:

```bash
python run-adaptive-learning.py --dry-run    # Preview suggestions
python run-adaptive-learning.py --interactive # Review before applying
python run-adaptive-learning.py --no-interactive # Auto-apply
```

## Architecture

```
claude_automation/
├── generators/           # Content generators
│   ├── system_generator.py      # System CLAUDE.md
│   ├── permissions_generator.py # Project permissions
│   └── ...
├── analyzers/            # Pattern detection
│   ├── approval_tracker.py      # Permission patterns
│   ├── context_optimizer.py     # Section usage
│   └── ...
├── templates/            # Jinja2 templates
│   ├── system-claude.j2
│   └── shared/policies.j2
├── schemas/              # Pydantic models
│   ├── core.py           # ToolInfo, ClaudeRelevance
│   └── ...
└── validators/           # Content validation
```

## Development

```bash
# Enter dev environment
nix develop

# Run tests (59 tests)
pytest -v

# Run specific test categories
pytest tests/test_schemas.py -v      # Schema validation
pytest tests/test_templates.py -v    # Template rendering
pytest tests/test_integration.py -v  # End-to-end

# Lint
ruff check claude_automation/
```

## Files Generated

| File | Location | Purpose |
|------|----------|---------|
| `CLAUDE.md` | `~/.claude/` | System-level tool documentation |
| `settings.local.json` | `.claude/` | Project auto-approval patterns |
| `CLAUDE.local.md` | `.claude/` | Machine-specific context (gitignored) |
| `*.md` | `~/.claude/commands/` | Slash command definitions |
| `CLAUDE-USER-POLICIES.md` | `~/.claude/` | User policies (manually maintained) |

## Configuration

### User Policies

Create `~/.claude/CLAUDE-USER-POLICIES.md` for policies included in all generated CLAUDE.md files:

```markdown
## Git Commit Policy
Never use `git commit --no-verify` without explicit user permission.

## System Rebuild Restrictions
Never attempt to run `./rebuild-nixos` directly.
```

### Tool Categories

Tools are categorized in `packages.nix` and organized by:
- AI & MCP Tools
- Development Tools
- Modern CLI Tools
- Network & Security
- File Management
- System Monitoring

## Related Projects

- [nixos-config](https://github.com/jacopone/nixos-config) - NixOS configuration using this automation
- [Claude Code](https://claude.ai/code) - Anthropic's CLI for Claude

## License

MIT - See [LICENSE](LICENSE)
