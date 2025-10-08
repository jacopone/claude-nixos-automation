# Claude NixOS Automation

**Comprehensive automation system for Claude Code awareness in NixOS environments.**

Automatically generates and maintains CLAUDE.md configurations, permissions, slash commands, and usage analytics to maximize Claude Code effectiveness.

## 🎯 Overview

This system provides **5 automation phases** that enhance Claude Code's understanding of your development environment:

| Phase | Output | Purpose |
|-------|--------|---------|
| **1. Permissions** | `.claude/settings.local.json` | Auto-detects project type, generates optimized permissions |
| **2. Directory Context** | `*/CLAUDE.md` | Generates purpose-specific docs for each directory |
| **3. Local Context** | `.claude/CLAUDE.local.md` | Machine-specific info (hardware, services, WIP notes) |
| **4. Slash Commands** | `~/.claude/commands/*.md` | Workflow-based shortcuts (detects from git history) |
| **6. Usage Analytics** | Appends to `CLAUDE.md` | Command usage patterns from Fish shell history |

**Plus:** User policies management, system-level tool inventory, and project-level configurations.

## ✨ Features

### Core Automation (Phases 1-4, 6)

- ✅ **Auto-detects project type** - Python, Node.js, Rust, NixOS, Mixed
- ✅ **Generates optimized permissions** - No manual configuration
- ✅ **Workflow-aware slash commands** - Analyzes git commits for patterns
- ✅ **Directory-level context** - Purpose-specific guidelines (tests/, docs/, src/)
- ✅ **Usage analytics** - Learns from your actual command usage
- ✅ **Hardware introspection** - CPU, memory, disk, running services
- ✅ **WIP notes preservation** - Edit local context freely, notes are preserved

### User Policies System

- ✅ **Never overwrites user policies** - Preserved across rebuilds
- ✅ **Auto-updating examples** - Latest best practices from community
- ✅ **Interactive setup wizard** - Guided first-time configuration
- ✅ **Community integration** - Web scraping from Anthropic docs, GitHub
- ✅ **NEW badges** - Automatic versioning shows new policies

### Quality & Reliability

- ✅ **59 automated tests** - 100% passing (schemas, templates, integration)
- ✅ **Pydantic validation** - Type-safe data models
- ✅ **Template syntax validation** - Catches Jinja2 errors
- ✅ **Idempotent generators** - Safe to run multiple times
- ✅ **Modern Python** - uv package management, Python 3.13

## 🚀 Quick Start

### As a Nix Flake Input

Add to your `flake.nix`:

```nix
inputs.claude-automation = {
  url = "github:jacopone/claude-nixos-automation";
};
```

### First-Time Setup (Interactive)

```bash
# Guided wizard for user policies
nix run github:jacopone/claude-nixos-automation#setup-user-policies

# Generate all configurations
nix run github:jacopone/claude-nixos-automation#update-all
```

### Regular Usage

```bash
# Recommended: Update everything at once
nix run ~/claude-nixos-automation#update-all

# Or run individual phases:
nix run .#update-permissions       # Phase 1: Generate permissions
nix run .#update-directory-context # Phase 2: Directory CLAUDE.md files
nix run .#update-local-context     # Phase 3: Machine-specific context
nix run .#update-slash-commands    # Phase 4: Workflow shortcuts
nix run .#update-usage-analytics   # Phase 6: Command usage patterns

# User policies
nix run .#update-user-policies     # Update example file only
nix run .#setup-user-policies      # Interactive wizard

# Legacy (still supported)
nix run .#update-system            # System-level CLAUDE.md
nix run .#update-project           # Project-level CLAUDE.md
```

## 📊 Phase Details

### Phase 1: Permissions Generator

**Output:** `.claude/settings.local.json`

Auto-generates project-specific permissions based on detected project type.

**Detection:**
- Python: `pyproject.toml`, `setup.py`, `requirements.txt`
- Node.js: `package.json`, `package-lock.json`
- Rust: `Cargo.toml`, `Cargo.lock`
- NixOS: `flake.nix`, `configuration.nix`

**Permissions include:**
- Git operations (status, diff, log, commit)
- Quality tools (ruff, eslint, clippy, etc.)
- Package managers (uv, npm, cargo)
- Modern CLI tools (eza, bat, rg, fd)
- Project-specific test runners

**Example:**
```bash
cd ~/my-python-project
nix run ~/claude-nixos-automation#update-permissions

# Generates .claude/settings.local.json with:
# - pytest permissions
# - ruff/black permissions
# - uv package manager permissions
# - Python-specific paths
```

### Phase 2: Directory Context Generator

**Output:** `<directory>/CLAUDE.md`

Generates purpose-specific documentation for each directory.

**Detects 10 directory purposes:**
- `source_code/` - Code guidelines, entry points
- `tests/` - Testing best practices, coverage goals
- `documentation/` - Writing style, clarity guidelines
- `configuration/` - Config file safety warnings
- `modules/` - Module architecture guidance
- `scripts/` - Script usage instructions
- `templates/` - Template usage guidelines
- `data/` - Data handling policies
- `build/` - Build artifact warnings
- `generic/` - Default for unknown purposes

**Auto-discovers:**
- File counts and types
- Key files (`__init__.py`, `README.md`, `main.rs`)
- Protected files (`node_modules/`, `__pycache__/`)

**Example:**
```bash
nix run ~/claude-nixos-automation#update-directory-context

# Analyzes: src/, tests/, docs/, scripts/, etc.
# Generates: src/CLAUDE.md, tests/CLAUDE.md, docs/CLAUDE.md
```

### Phase 3: Local Context Generator

**Output:** `.claude/CLAUDE.local.md` (gitignored)

Machine-specific context with editable WIP notes.

**Auto-detects:**
- Hostname, CPU, memory, disk usage
- Running services (Docker, PostgreSQL, Redis, etc.)
- Active git branches
- Hardware limitations

**User-editable sections (preserved):**
- Work in Progress notes
- Experimental features
- Machine-specific quirks

**Example:**
```bash
nix run ~/claude-nixos-automation#update-local-context

# Generates .claude/CLAUDE.local.md with:
# - Intel i7-8665U, 15.4GB RAM
# - Docker service running
# - Current branch: main
# - WIP: Your notes here (preserved on next run)
```

### Phase 4: Slash Commands Generator

**Output:** `~/.claude/commands/*.md`

Generates workflow shortcuts based on git commit analysis.

**Base commands (all projects):**
- `/rebuild-check` - Validate config before rebuild
- `/explain-file <file>` - Explain file purpose
- `/quick-fix <issue>` - Quick fixes for common problems
- `/review-changes` - Review uncommitted changes

**Project-type commands:**
- Python: `/run-tests`, `/check-quality` (ruff, black)
- Node.js: `/run-tests`, `/check-quality` (eslint, prettier)
- Rust: `/run-tests`, `/check-quality` (clippy, fmt)
- NixOS: `/nix-check`, `/nix-search <package>`

**Workflow-detected commands:**
- "bug fix" pattern → `/debug-helper <issue>`
- "documentation" pattern → `/doc-update <changes>`
- "refactoring" pattern → `/refactor-suggest <file>`

**Example:**
```bash
cd ~/my-project
nix run ~/claude-nixos-automation#update-slash-commands

# Analyzes last 100 commits
# Detects: "bug fix" (15×), "documentation" (8×)
# Generates: /rebuild-check, /debug-helper, /doc-update
```

### Phase 6: Usage Analytics Generator

**Output:** Appends to `CLAUDE.md` (with HTML markers)

Parses Fish shell history to generate usage insights.

**Analytics include:**
- Total commands analyzed
- Top 20 most-used commands
- Modern CLI tools usage (eza, bat, rg, etc.)
- Workflow patterns detected
- AI-personalized insights

**Example output:**
```markdown
## 📊 Usage Analytics

### Command Usage Statistics
- Total commands: 883
- Unique commands: 223

### Top 5 Most Used Commands
1. cd (111×) - file_operations
2. git (97×) - git
3. rm (44×) - file_operations
...

### Workflow Patterns Detected
- ✓ Heavy git user
- ✓ Modern CLI tools adoption
- ✓ AI-assisted development

### Insights for Claude Code
- Git-heavy workflow: You use git frequently...
- Modern CLI adoption: Prefer eza, bat, rg...
```

**Example:**
```bash
nix run ~/claude-nixos-automation#update-usage-analytics

# Parses ~/.local/share/fish/fish_history
# Updates CLAUDE.md with analytics section
# Replaces existing section (no duplicates)
```

## 🧪 Testing

Comprehensive test suite with **59 automated tests, 100% passing**:

```bash
# Enter dev environment
nix develop

# Run all tests
pytest -v

# Run specific test categories
pytest tests/test_schemas.py -v      # Schema validation (28 tests)
pytest tests/test_templates.py -v    # Template rendering (24 tests)
pytest tests/test_integration.py -v  # End-to-end workflows (7 tests)

# Run with coverage
pytest --cov=claude_automation
```

**Test coverage:**
- ✅ **Schema validation** - All Pydantic models enforce business rules
- ✅ **Template rendering** - All 15 Jinja2 templates render without errors
- ✅ **Integration workflows** - Each phase tested end-to-end
- ✅ **Edge cases** - Empty data, None values, nonexistent paths
- ✅ **Idempotency** - Generators can run multiple times safely

📖 **[Read full testing documentation →](TESTING.md)**

## 📁 Files Generated

### User Policies

**`~/.claude/CLAUDE-USER-POLICIES.md`** _(preserved)_
- Your custom policies (git, documentation, code quality)
- Created once, never regenerated
- Fully editable

**`~/.claude/CLAUDE-USER-POLICIES.md.example`** _(auto-updated)_
- Latest community best practices
- NEW badges for new policies
- Use as reference for discovering new patterns

### Phase Outputs

**`.claude/settings.local.json`** _(Phase 1)_
- Project-specific permissions
- Auto-detected based on project type

**`<directory>/CLAUDE.md`** _(Phase 2)_
- Purpose-specific guidelines
- File structure documentation
- DO NOT TOUCH warnings for protected files

**`.claude/CLAUDE.local.md`** _(Phase 3, gitignored)_
- Machine-specific context
- Hardware info, running services
- Editable WIP notes (preserved)

**`~/.claude/commands/*.md`** _(Phase 4)_
- Slash command definitions
- Workflow shortcuts
- Usage examples

**`CLAUDE.md`** _(Phase 6 appends)_
- Usage analytics section
- Command statistics
- Workflow insights

### Legacy Outputs (Still Supported)

**`~/.claude/CLAUDE.md`** _(system-level)_
- Complete tool inventory (123 packages)
- Fish abbreviations (57)
- Modern CLI tool substitutions

**`CLAUDE.md`** _(project-level)_
- Tech stack and conventions
- Essential commands
- Working features

## 🏗️ Architecture

```
claude_automation/
├── analyzers/           # Project analysis
│   ├── directory_analyzer.py    # Detects directory purpose
│   ├── project_detector.py      # Detects project type
│   ├── system_analyzer.py       # Hardware/service detection
│   ├── usage_tracker.py         # Fish history parsing
│   └── workflow_analyzer.py     # Git commit analysis
├── generators/          # Content generators
│   ├── base_generator.py
│   ├── directory_context_generator.py
│   ├── local_context_generator.py
│   ├── permissions_generator.py
│   ├── slash_commands_generator.py
│   ├── usage_analytics_generator.py
│   ├── system_generator.py      # Legacy
│   ├── project_generator.py     # Legacy
│   └── user_policies_generator.py
├── parsers/             # Nix config parsers
│   ├── nix_evaluator.py
│   └── regex_parser.py
├── templates/           # Jinja2 templates
│   ├── directory/       # 10 directory templates
│   ├── permissions/     # 5 permission templates
│   ├── local_context.j2
│   ├── usage_analytics.j2
│   ├── user-policies.j2
│   └── user-policies-example.j2
├── validators/          # Content validators
├── schemas.py           # Pydantic data models
└── utils.py
tests/
├── conftest.py          # Shared fixtures
├── test_schemas.py      # Schema validation tests (28)
├── test_templates.py    # Template rendering tests (24)
└── test_integration.py  # End-to-end tests (7)
```

## 🔄 Integration with rebuild-nixos

All automation runs automatically as part of `./rebuild-nixos` in your nixos-config:

```bash
cd ~/nixos-config
./rebuild-nixos

# Automatically runs:
# 1. update-user-policies (preserves your custom policies)
# 2. update-system-claude (tool inventory)
# 3. update-project-claude (project context)
# 4. All Phase 1-6 generators (if configured)
```

Zero manual maintenance required!

## 📖 Usage Examples

### Example 1: New Python Project

```bash
cd ~/my-new-api
nix run ~/claude-nixos-automation#update-permissions

# Auto-detects: Python project (found pyproject.toml)
# Generates: .claude/settings.local.json
# Includes: pytest, ruff, black, uv permissions
```

### Example 2: Understanding Command Usage

```bash
nix run ~/claude-nixos-automation#update-usage-analytics

# Parses: 883 commands from Fish history
# Discovers: Heavy git user, modern CLI adoption
# Insight: "You use git 97 times - Claude can help with commits"
```

### Example 3: Project-Specific Shortcuts

```bash
cd ~/nixos-config
nix run ~/claude-nixos-automation#update-slash-commands

# Analyzes: Last 100 commits
# Detects: Frequent "docs:" commits
# Generates: /doc-update command
# Usage: "/doc-update API changes" in Claude Code
```

### Example 4: Multi-Directory Documentation

```bash
nix run ~/claude-nixos-automation#update-directory-context

# Scans: src/, tests/, docs/, scripts/
# src/ → "Source code guidelines, entry points"
# tests/ → "Testing best practices, coverage goals"
# docs/ → "Writing style, no temporal markers"
```

## 🤝 Contributing

### Running Tests

```bash
nix develop
pytest -v

# Add new tests to:
# - tests/test_schemas.py (for new Pydantic models)
# - tests/test_templates.py (for new Jinja2 templates)
# - tests/test_integration.py (for new workflows)
```

### Adding New Phases

1. Create analyzer in `claude_automation/analyzers/`
2. Create generator in `claude_automation/generators/`
3. Add schema to `claude_automation/schemas.py`
4. Create template in `claude_automation/templates/`
5. Create script `update-<phase>-v2.py`
6. Update `flake.nix` with new app
7. Add tests to `tests/`

### Contributing Best Practices

Submit PRs with updates to:
- `user_policies_generator.py` - Add new policy sources
- `templates/` - Improve template quality
- `analyzers/` - Better detection algorithms

## 📊 Project Stats

- **Implementation time**: 10.5 hours (vs 30h estimate)
- **Test coverage**: 59 tests, 100% passing
- **Lines of code**: ~5,000
- **Templates**: 20 Jinja2 templates
- **Phases completed**: 5/6 (skipped Phase 5: MCP Config)
- **Schemas**: 15 Pydantic models

## 🔮 Future Enhancements

**Phase 5: MCP Config Generator** (not yet implemented)
- Auto-detect MCP servers (serena, mcp-nixos)
- Generate `~/.claude/mcp.json`
- Zero-configuration MCP integration

**Potential improvements:**
- GitHub Actions CI/CD integration
- More project type detectors (Go, Java, C++)
- Machine learning for workflow detection
- Integration with other AI coding tools

## 📄 License

MIT

## 🙏 Acknowledgments

- Built on NixOS with Nix Flakes
- Uses Anthropic's Claude Code best practices
- Inspired by ZaneyOS modular architecture
- Community-driven policy templates
