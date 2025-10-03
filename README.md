# Claude NixOS Automation

Automation tools for managing `CLAUDE.md` configurations in NixOS environments.

## Overview

This package automatically generates and maintains:
- **System-level** `~/.claude/CLAUDE.md` - Tool inventory, Fish abbreviations, system info
- **Project-level** `CLAUDE.md` - Project-specific configuration, tech stack, conventions

## Usage

### As a Nix Flake Input

Add to your `nixos-config/flake.nix`:

```nix
inputs.claude-automation = {
  url = "path:/home/guyfawkes/claude-nixos-automation";
  # Or for remote: url = "github:yourusername/claude-nixos-automation";
};
```

### Running the Automation

```bash
# Update system-level CLAUDE.md
nix run ~/claude-nixos-automation#update-system

# Update project-level CLAUDE.md
nix run ~/claude-nixos-automation#update-project

# Update both
nix run ~/claude-nixos-automation#update-all
```

### Development

```bash
# Enter development shell
nix develop

# Run with devenv
devenv shell
```

## Features

- ✅ Template-based Jinja2 generation
- ✅ Robust Nix configuration parsing
- ✅ Automatic tool inventory extraction
- ✅ Fish abbreviation detection
- ✅ Content validation
- ✅ Modern Python with `uv` package management

## Files Generated

### System-level (`~/.claude/CLAUDE.md`)
- Complete system tool inventory
- Fish shell abbreviations
- Command examples and best practices
- Modern CLI tool substitution policies

### Project-level (`CLAUDE.md`)
- Project structure and tech stack
- Development conventions
- Working features and known issues
- Essential commands

## Architecture

```
claude_automation/
├── generators/        # CLAUDE.md generators
├── parsers/          # Nix configuration parsers
├── templates/        # Jinja2 templates
├── validators/       # Content validators
└── schemas.py        # Data models
```

## License

MIT
