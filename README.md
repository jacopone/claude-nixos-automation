---
status: active
created: 2024-01-01
updated: 2025-11-30
type: reference
lifecycle: persistent
---

# Claude NixOS Automation

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![NixOS](https://img.shields.io/badge/nixos-unstable-blue.svg)](https://nixos.org/)
[![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen.svg)](TESTING.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Automated configuration generator for [Claude Code](https://claude.ai/code) on NixOS systems.

> **Note**: This tool is designed for NixOS systems. It analyzes your Nix configuration to generate Claude Code settings.

## Highlights

- **Zero configuration** — Detects project type automatically from manifest files
- **NixOS-native** — Reads your flake.nix and home-manager configuration
- **Smart permissions** — Generates auto-approval patterns for your toolchain
- **Modern CLI awareness** — Documents tool substitutions (fd→find, rg→grep, eza→ls)

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
| System docs | `~/.claude/CLAUDE.md` | Available tools, command substitutions |
| Permissions | `.claude/settings.local.json` | Auto-approval patterns for your toolchain |
| Local context | `.claude/CLAUDE.local.md` | Machine-specific state (gitignored) |

## Project Detection

Automatically detects your project type and generates appropriate permissions:

| Manifest | Project Type | Generated Permissions |
|----------|--------------|----------------------|
| `pyproject.toml` | Python | pytest, ruff, uv, black |
| `package.json` | Node.js | npm, eslint, prettier |
| `Cargo.toml` | Rust | cargo, clippy, rustfmt |
| `flake.nix` | NixOS | nix build, nix flake check |

## Available Commands

```bash
# Main entry point - generates all config
nix run .#update-all

# Individual commands
nix run .#update-system            # ~/.claude/CLAUDE.md
nix run .#update-project           # ./CLAUDE.md
nix run .#update-permissions       # .claude/settings.local.json
nix run .#update-local-context     # .claude/CLAUDE.local.md
nix run .#update-directory-context # Per-directory CLAUDE.md files
nix run .#update-slash-commands    # ~/.claude/commands/*.md

# Setup & utilities
nix run .#setup-user-policies      # Interactive policy wizard
nix run .#check-data-health        # Monitor learning data disk usage
```

## Integration with NixOS Rebuild

If using with [nixos-config](https://github.com/jacopone/nixos-config), the rebuild script can call this automatically:

```bash
./rebuild-nixos  # Runs nix run #update-all as part of rebuild
```

## Tool Filtering

Not all installed packages are relevant to Claude Code. This tool filters by relevance:

- **Essential** — Tool substitutions (fd→find, eza→ls, bat→cat, rg→grep)
- **High** — Non-obvious tools with unique syntax (jless, miller, pgcli)
- **Filtered** — System libraries, fonts, build dependencies

## Architecture

```
claude_automation/
├── cli/              # Command-line entry points
├── generators/       # Content generators (system, project, permissions)
├── analyzers/        # Pattern detection (project type, usage, workflows)
├── templates/        # Jinja2 templates (27 templates)
├── schemas/          # Pydantic data models (10+ schemas)
└── validators/       # Content validation
```

## Development

```bash
# Enter development shell
nix develop

# Run test suite (59 tests)
pytest -v

# Run specific test categories
pytest tests/test_schemas.py -v      # Schema validation (28 tests)
pytest tests/test_templates.py -v    # Template rendering (24 tests)
pytest tests/test_integration.py -v  # End-to-end workflows (7 tests)

# Lint
ruff check claude_automation/
```

See [TESTING.md](TESTING.md) for detailed test documentation.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT — See [LICENSE](LICENSE)
