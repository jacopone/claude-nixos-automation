---
status: active
created: 2024-01-01
updated: 2025-10-20
type: reference
lifecycle: persistent
---

# Claude NixOS Automation

**Self-learning automation system for Claude Code that gets smarter with every rebuild**

Claude NixOS Automation analyzes your development workflow, learns from your patterns, and automatically optimizes Claude Code's configuration for maximum productivity. Zero manual setup, continuous improvement, and intelligent context management for NixOS environments.

[![Tests](https://img.shields.io/badge/tests-100%25%20passing-brightgreen)](TESTING.md)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen)](https://github.com/astral-sh/ruff)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![NixOS](https://img.shields.io/badge/nixos-unstable-blue)](https://nixos.org/)

---

## Why This Matters

**Problem**: Claude Code needs extensive configuration to understand your environment, but manual setup is tedious, outdated configs waste tokens, and you miss optimization opportunities.

**Solution**: An intelligent system that learns from your behavior and automatically maintains optimal Claude Code configuration. It analyzes permissions you approve, detects unused features wasting tokens, and adapts to your evolving workflow.

**Result**: ~60% fewer permission prompts, 6000+ tokens saved per session, faster responses, and zero maintenance overhead.

---

## Quick Start (2 Minutes)

```bash
# 1. Add to your flake
inputs.claude-automation.url = "github:jacopone/claude-nixos-automation";

# 2. Generate initial configuration
nix run github:jacopone/claude-nixos-automation#update-all

# 3. Run adaptive learning (learns from your patterns)
python run-adaptive-learning.py --no-interactive

# Done! System is now optimized and will continue learning.
```

**What just happened?**
- Auto-detected your project type (Python/Node/Rust/NixOS)
- Generated optimized permissions for your tools
- Analyzed your command history for workflow patterns
- Created project-specific slash commands
- Identified token-wasting unused features

---

## The Learning System

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR DEVELOPMENT WORKFLOW                                  │
│  (git commits, command usage, permission approvals)         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: Pattern Detection                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Permission   │  │  MCP Server  │  │   Workflow   │     │
│  │  Learning    │  │ Optimization │  │  Detection   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: Context Optimization                               │
│  • Prune unused CLAUDE.md sections (saves tokens)           │
│  • Reorder by access frequency (faster searches)            │
│  • Detect "noise" content (loaded but never referenced)     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: Meta-Learning                                      │
│  • Calibrate confidence thresholds                          │
│  • Track suggestion acceptance rates                        │
│  • Adapt to your preferences over time                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  OPTIMIZED CLAUDE CODE CONFIGURATION                        │
│  (Updated automatically, continuously improving)            │
└─────────────────────────────────────────────────────────────┘
```

### Real-World Impact

**Before Adaptive Learning**:
```bash
# Every pytest run requires manual approval
Claude Code: "Approve bash command: pytest tests/ -v?"
You: "Yes" (for the 10th time today)

# MCP servers you never use waste 6000 tokens per session
# Generic CLAUDE.md loaded but 40% never referenced
# No workflow shortcuts for repeated tasks
```

**After Adaptive Learning**:
```bash
# Auto-approved after detecting pattern
✅ Bash(pytest:*) auto-approved (you approved 5+ times)

# Unused MCP servers disabled
💡 Disabled 'serena', 'playwright' (unused, saves ~6000 tokens/session)

# Smart context
📊 CLAUDE.md pruned: 40% noise removed, reordered by usage

# Workflow shortcuts created
🎯 New slash command: /quick-commit (detected git pattern)
```

**Performance**: 1.38s execution (7.3x faster than target), 35MB memory (2.9x better than target)

---

## Core Features

### 🧠 Adaptive Learning (NEW!)
- **Permission Learning**: Auto-approve based on approval patterns (~60% fewer prompts)
- **Global MCP Optimization**: Disable unused servers, calculate ROI, save 6000+ tokens/session
- **Context Optimization**: Prune unused CLAUDE.md sections, reorder by access frequency
- **Workflow Detection**: Auto-generate slash commands from git commit patterns
- **Instruction Effectiveness**: Detect ambiguous policies, suggest rewording

### 🚀 Automated Context Generation
- **Phase 1 - Permissions**: Auto-detect project type, generate optimized `.claude/settings.local.json`
- **Phase 2 - Directory Context**: Purpose-specific docs for each directory (tests/, docs/, src/)
- **Phase 3 - Local Context**: Machine-specific info (hardware, services, WIP notes)
- **Phase 4 - Slash Commands**: Workflow shortcuts from git commit analysis
- **Phase 6 - Usage Analytics**: Command usage patterns from Fish shell history

### 🎯 Smart Project Detection
Automatically detects:
- **Python** (pyproject.toml, requirements.txt) → pytest, ruff, black permissions
- **Node.js** (package.json) → npm, eslint, prettier permissions
- **Rust** (Cargo.toml) → cargo, clippy, rustfmt permissions
- **NixOS** (flake.nix) → nix commands, rebuild-check permissions

### 📊 Usage Intelligence
- Analyzes Fish shell history (883 commands across 223 unique tools)
- Identifies workflow patterns (heavy git user, modern CLI adoption)
- Recommends optimizations based on actual usage
- Tracks modern CLI tool adoption (eza, bat, rg, fd)

---

## Installation

### As a Nix Flake Input (Recommended)

Add to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    claude-automation.url = "github:jacopone/claude-nixos-automation";
  };

  outputs = { self, nixpkgs, claude-automation, ... }: {
    # Use in your NixOS configuration or development shells
  };
}
```

### First-Time Setup

```bash
# Interactive wizard for user policies
nix run github:jacopone/claude-nixos-automation#setup-user-policies

# Generate all configurations
nix run github:jacopone/claude-nixos-automation#update-all

# Run adaptive learning
cd ~/claude-nixos-automation
python run-adaptive-learning.py --interactive  # Review before applying
# OR
python run-adaptive-learning.py --no-interactive  # Auto-apply all
```

---

## Usage

### Recommended: Update Everything

```bash
nix run ~/claude-nixos-automation#update-all
```

This runs all phases:
1. Permissions generation
2. Directory context
3. Local context (machine-specific)
4. Slash commands (workflow shortcuts)
5. Usage analytics
6. User policies update

### Individual Phases

```bash
# Generate project permissions
nix run .#update-permissions

# Generate directory-specific docs
nix run .#update-directory-context

# Update machine-specific context
nix run .#update-local-context

# Generate workflow slash commands
nix run .#update-slash-commands

# Update usage analytics
nix run .#update-usage-analytics

# Update user policy examples
nix run .#update-user-policies
```

### Adaptive Learning

```bash
# Interactive mode (review before applying)
python run-adaptive-learning.py --interactive

# Auto-apply all suggestions
python run-adaptive-learning.py --no-interactive

# Dry-run (show without applying)
python run-adaptive-learning.py --dry-run

# Check system health
python run-adaptive-learning.py --health

# Adjust sensitivity
python run-adaptive-learning.py --min-occurrences 5 --confidence 0.8
```

---

## Architecture

### 5 Learning Components

1. **Permission Learning** (`analyzers/approval_tracker.py`)
   - Tracks permission approvals across sessions
   - Detects patterns (>5 approvals = auto-approve)
   - Reduces prompts by ~60%

2. **Global MCP Optimization** (`analyzers/global_mcp_analyzer.py`)
   - Scans all projects for MCP server usage
   - Calculates ROI (tokens vs. usage)
   - Recommends disable/project-level/global placement

3. **Context Optimization** (`analyzers/context_optimizer.py`)
   - Tracks CLAUDE.md section access
   - Identifies "noise" (loaded but never used)
   - Reorders by frequency, prunes unused

4. **Workflow Detection** (`analyzers/workflow_detector.py`)
   - Analyzes git commit messages
   - Detects repeated patterns (bug fix, documentation, refactor)
   - Suggests slash commands for workflows

5. **Instruction Tracker** (`analyzers/instruction_tracker.py`)
   - Monitors policy compliance
   - Detects ambiguous policies (<70% compliance)
   - Suggests rewording for clarity

### Directory Structure

```
claude-nixos-automation/
├── claude_automation/
│   ├── analyzers/           # Pattern detection
│   │   ├── approval_tracker.py
│   │   ├── global_mcp_analyzer.py
│   │   ├── context_optimizer.py
│   │   ├── workflow_detector.py
│   │   └── instruction_tracker.py
│   ├── generators/          # Content generators
│   │   ├── permissions_generator.py
│   │   ├── directory_context_generator.py
│   │   ├── local_context_generator.py
│   │   ├── slash_commands_generator.py
│   │   └── usage_analytics_generator.py
│   ├── core/
│   │   └── adaptive_system_engine.py  # Orchestrates learning
│   ├── templates/           # 20 Jinja2 templates
│   ├── schemas.py           # 15 Pydantic models
│   └── utils.py
├── tests/                   # 59 tests, 100% passing
│   ├── test_schemas.py      # 28 schema tests
│   ├── test_templates.py    # 24 template tests
│   └── test_integration.py  # 7 integration tests
├── scripts/                 # Documentation governance
│   ├── add-frontmatter.py
│   ├── reorganize-docs.sh
│   ├── check-frontmatter.py
│   └── review-docs-lifecycle.py
└── run-adaptive-learning.py # Main CLI entry point
```

---

## Files Generated

### Configuration Files

| File | Phase | Description |
|------|-------|-------------|
| `.claude/settings.local.json` | Phase 1 | Project permissions (auto-detected) |
| `<dir>/CLAUDE.md` | Phase 2 | Directory-specific guidelines |
| `.claude/CLAUDE.local.md` | Phase 3 | Machine context (gitignored, editable) |
| `~/.claude/commands/*.md` | Phase 4 | Slash command definitions |
| `CLAUDE.md` (appended) | Phase 6 | Usage analytics section |
| `~/.claude/CLAUDE-USER-POLICIES.md` | User | Your custom policies (preserved) |

### Example Output

**Permissions** (`.claude/settings.local.json`):
```json
{
  "commandAutoApprovals": [
    {"pattern": "Bash(pytest:*)"},
    {"pattern": "Bash(git status)"},
    {"pattern": "Bash(ruff check:*)"}
  ]
}
```

**Slash Command** (`~/.claude/commands/quick-commit.md`):
```markdown
---
description: "Quick commit workflow (auto-detected pattern)"
---

Create a commit with conventional commit format.

Usage: /quick-commit "feat: add user authentication"

Runs:
1. git add .
2. git commit -m "<message>"
3. Shows git status
```

---

## Testing

### Run Tests

```bash
# Enter development environment
nix develop

# Run all tests (59 tests, 100% passing)
pytest -v

# Run specific categories
pytest tests/test_schemas.py -v      # Schema validation (28 tests)
pytest tests/test_templates.py -v    # Template rendering (24 tests)
pytest tests/test_integration.py -v  # End-to-end (7 tests)

# With coverage
pytest --cov=claude_automation
```

### Test Coverage

- ✅ **Schema Validation**: All Pydantic models enforce business rules
- ✅ **Template Rendering**: All 20 Jinja2 templates render without errors
- ✅ **Integration Workflows**: Each phase tested end-to-end
- ✅ **Edge Cases**: Empty data, None values, nonexistent paths
- ✅ **Idempotency**: Generators safe to run multiple times

**[Read full testing documentation →](TESTING.md)**

---

## Use Cases

### For Individual Developers

**Scenario**: You're tired of approving the same `pytest` command 10 times a day.

**Solution**: Run adaptive learning. After detecting the pattern, `Bash(pytest:*)` is auto-approved.

**Impact**: ~60% fewer permission prompts, faster development flow.

### For NixOS Users

**Scenario**: You have 5 projects, each with different MCP servers. Some servers waste tokens.

**Solution**: Global MCP analyzer scans all projects, identifies unused servers.

**Impact**: 6000+ tokens saved per session, faster Claude responses.

### For Teams

**Scenario**: New team member joins, needs optimal Claude Code setup.

**Solution**: Run `nix run .#update-all` in the project directory.

**Impact**: Instant project-specific configuration, no manual setup, consistent team experience.

### For Open Source Maintainers

**Scenario**: You want contributors to have the best Claude Code experience.

**Solution**: Include this system in your flake, auto-generates configs on clone.

**Impact**: Contributors get optimized setup automatically, better PR quality, faster onboarding.

---

## Performance

- **Execution Time**: 1.38 seconds (7.3x faster than 10s target)
- **Memory Usage**: ~35MB (2.9x better than 100MB target)
- **Project Scanning**: 6 projects/second
- **Error Handling**: Graceful degradation per component
- **Idempotency**: Safe to run multiple times

---

## Contributing

### Adding New Learning Components

1. Create analyzer in `claude_automation/analyzers/`
2. Implement `analyze()` method returning suggestions
3. Add to `adaptive_system_engine.py`
4. Write tests in `tests/unit/`

### Improving Detection Algorithms

- Permission patterns: `analyzers/approval_tracker.py`
- MCP optimization: `analyzers/global_mcp_analyzer.py`
- Workflow detection: `analyzers/workflow_detector.py`

### Testing

```bash
nix develop
pytest -v

# Add tests to:
# - tests/test_schemas.py (Pydantic models)
# - tests/test_templates.py (Jinja2 templates)
# - tests/test_integration.py (end-to-end workflows)
```

---

## Project Stats

- **Lines of Code**: ~5,000
- **Tests**: 59 (100% passing)
- **Templates**: 20 Jinja2 templates
- **Schemas**: 15 Pydantic models
- **Phases**: 6 (5 implemented)
- **Learning Components**: 5
- **Supported Project Types**: Python, Node.js, Rust, NixOS, Mixed

---

## Roadmap

- [x] **Phase 1-4, 6**: Auto-detection and generation ✅
- [x] **Adaptive Learning**: 5 learning components ✅
- [x] **Testing**: 59 automated tests, 100% passing ✅
- [x] **Documentation Governance**: Frontmatter, lifecycle management ✅
- [ ] **Phase 5**: MCP config auto-generation
- [ ] **GitHub Actions**: CI/CD integration
- [ ] **More Project Types**: Go, Java, C++, Kotlin
- [ ] **Machine Learning**: Advanced pattern detection

---

## License

MIT - See [LICENSE](LICENSE) for details

---

## Acknowledgments

- Built on **NixOS** with Nix Flakes
- Uses **Anthropic's Claude Code** best practices
- Inspired by **ZaneyOS** modular architecture
- Community-driven policy templates
- Testing framework: **pytest**
- Validation: **Pydantic**
- Templating: **Jinja2**

---

## Support

- **Documentation**: See [TESTING.md](TESTING.md) for testing guide
- **Issues**: [GitHub Issues](https://github.com/jacopone/claude-nixos-automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jacopone/claude-nixos-automation/discussions)

---

**Made with ❤️ for the NixOS and Claude Code communities**
