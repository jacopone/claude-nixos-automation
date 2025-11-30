---
status: active
created: 2025-11-30
updated: 2025-11-30
type: guide
lifecycle: persistent
---

# Contributing to Claude NixOS Automation

Thank you for your interest in contributing! This guide will help you get started.

## Prerequisites

- **NixOS** with flakes enabled
- **Python 3.13+** (provided by the dev shell)
- Basic familiarity with Nix and Claude Code

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/jacopone/claude-nixos-automation.git
cd claude-nixos-automation
```

2. Enter the development shell:

```bash
nix develop
```

This provides Python 3.13, pytest, ruff, uv, and all dependencies.

## Running Tests

The test suite contains 59 tests covering schemas, templates, and integration:

```bash
# Run all tests
pytest -v

# Run specific test categories
pytest tests/test_schemas.py -v      # Schema validation (28 tests)
pytest tests/test_templates.py -v    # Template rendering (24 tests)
pytest tests/test_integration.py -v  # End-to-end workflows (7 tests)
```

See [TESTING.md](TESTING.md) for detailed test documentation.

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check for issues
ruff check claude_automation/

# Auto-fix issues
ruff check --fix claude_automation/

# Format code
ruff format claude_automation/
```

Configuration is in `pyproject.toml`.

## Project Structure

```
claude_automation/
├── cli/          # Command-line entry points
├── generators/   # Content generators (system, project, permissions)
├── analyzers/    # Pattern detection and learning
├── templates/    # Jinja2 templates
├── schemas/      # Pydantic data models
└── validators/   # Content validation
```

## Pull Request Guidelines

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Run the test suite** before submitting
4. **Keep commits focused** - one logical change per commit
5. **Write clear commit messages** following conventional commits

## Commit Message Format

```
type: short description

Longer description if needed.
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Testing Your Changes

Before submitting, verify your changes work with the flake:

```bash
# Build the package
nix build .#claude-automation

# Test the main entry point
nix run .#update-all

# Run flake checks
nix flake check
```

## Questions?

Open an issue for questions or discussions about potential contributions.
