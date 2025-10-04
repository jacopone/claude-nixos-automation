# Claude NixOS Automation

Automation tools for managing `CLAUDE.md` configurations in NixOS environments.

## Overview

This package automatically generates and maintains:
- **User policies** `~/.claude/CLAUDE-USER-POLICIES.md` - Your custom policies (preserved, never regenerated)
- **Example policies** `~/.claude/CLAUDE-USER-POLICIES.md.example` - Latest best practices (auto-updated)
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
# Update user policies (example template + initial user file if missing)
nix run ~/claude-nixos-automation#update-user-policies

# Update system-level CLAUDE.md
nix run ~/claude-nixos-automation#update-system

# Update project-level CLAUDE.md
nix run ~/claude-nixos-automation#update-project

# Update all files (RECOMMENDED)
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

- ✅ **User Policy Management** - Preserve custom policies across rebuilds
- ✅ **Community Best Practices** - Auto-updated example templates
- ✅ Template-based Jinja2 generation
- ✅ Robust Nix configuration parsing
- ✅ Automatic tool inventory extraction
- ✅ Fish abbreviation detection
- ✅ Content validation
- ✅ Modern Python with `uv` package management

## Files Generated

### User Policies (`~/.claude/CLAUDE-USER-POLICIES.md`)
**PRESERVED - Never Regenerated After Initial Creation**
- Your custom git commit policies
- System limitations (e.g., sudo restrictions)
- Documentation creation preferences
- Documentation standards (no temporal markers, no hyperbolic language)
- Code quality preferences
- Communication style preferences
- Project management policies

Rich template with commented examples you can uncomment to enable.

### Example Policies (`~/.claude/CLAUDE-USER-POLICIES.md.example`)
**AUTO-UPDATED on Every Rebuild**
- Latest community best practices
- New policy examples from official documentation
- Proven patterns from real-world usage
- Use as reference to discover new policies

Compare files: `diff CLAUDE-USER-POLICIES.md CLAUDE-USER-POLICIES.md.example`

### System-level (`~/.claude/CLAUDE.md`)
**AUTO-GENERATED on Every Rebuild**
- Complete system tool inventory
- Fish shell abbreviations
- Command examples and best practices
- Modern CLI tool substitution policies
- Reference to user policies file

### Project-level (`CLAUDE.md`)
**AUTO-GENERATED on Every Rebuild**
- Project structure and tech stack
- Development conventions
- Working features and known issues
- Essential commands

## Architecture

```
claude_automation/
├── generators/        # CLAUDE.md generators
│   ├── base_generator.py
│   ├── system_generator.py
│   ├── project_generator.py
│   └── user_policies_generator.py  # NEW: User policies management
├── parsers/          # Nix configuration parsers
├── templates/        # Jinja2 templates
│   ├── user-policies.j2             # NEW: Initial user policies template
│   ├── user-policies-example.j2     # NEW: Auto-updated example template
│   ├── system-claude.j2
│   └── project-claude.j2
├── validators/       # Content validators
└── schemas.py        # Data models
```

## User Policies System (2025 Best Practices)

### Problem Solved

**Before:** User-defined policies (git commit rules, documentation standards, etc.) were being overwritten on every system rebuild, losing your custom preferences.

**After:** Separate user policies file that is:
- ✅ Created once on first run with rich template
- ✅ NEVER regenerated or overwritten
- ✅ Accompanied by auto-updating example file with latest best practices
- ✅ Preserves your customizations across all rebuilds

### File Lifecycle

#### 1. First Run (Initial Setup)
```bash
nix run .#update-all
```

Creates:
- `~/.claude/CLAUDE-USER-POLICIES.md` - Rich template with commented examples
- `~/.claude/CLAUDE-USER-POLICIES.md.example` - Reference with best practices

#### 2. Customization
Edit `~/.claude/CLAUDE-USER-POLICIES.md`:
1. Uncomment sections you want to enable
2. Delete sections you don't need
3. Customize as needed
4. This file is now YOURS - never touched by automation

#### 3. Subsequent Runs
```bash
nix run .#update-all
```

- ✅ Preserves your `CLAUDE-USER-POLICIES.md` exactly as is
- ✅ Updates `CLAUDE-USER-POLICIES.md.example` with latest best practices
- ✅ Regenerates `CLAUDE.md` files (tool inventory, project context)

#### 4. Discovering New Policies

The system now includes **automatic policy versioning** with NEW badges!

**Automated Detection:**
- New policies are automatically marked with 🆕 badge in the example file
- Header shows count: "🆕 **3 new policies** added since last update!"
- Based on web scraping from:
  - Anthropic official documentation
  - GitHub community examples
  - ClaudeLog database

**Manual Comparison:**
```bash
diff ~/.claude/CLAUDE-USER-POLICIES.md ~/.claude/CLAUDE-USER-POLICIES.md.example
```

See what new policies are available, copy ones you want.

#### 5. Interactive Setup (First-Time Users)

For new users who want a guided setup experience:

```bash
nix run github:jacopone/claude-nixos-automation#setup-user-policies
```

This launches an **interactive CLI wizard** that:
- ✅ Asks which policy categories you want to enable
- ✅ Generates a customized file with only selected policies
- ✅ Automatically uncomments your chosen policies
- ✅ Creates backup of existing file if present
- ✅ Uses questionary for beautiful CLI prompts

**Example interaction:**
```
🤖 Claude Code User Policies - Interactive Setup
================================================================

📋 Select which policy categories to enable:

? Enable Git Commit Policies? (--no-verify restrictions) (Y/n)
? Enable System Limitation Warnings? (sudo restrictions) (Y/n)
? Enable Documentation Standards? (no temporal markers) (Y/n)
? Enable Code Quality Policies? (complexity limits) (y/N)
...
```

### Available Policy Categories

The templates include best practices for:

**1. Git Commit Policy** [RECOMMENDED]
- Prevents `--no-verify` without user permission
- Enforces quality gate compliance
- Based on: Security best practices 2025

**2. System Limitations** [RECOMMENDED FOR NIXOS]
- Documents Claude Code's inability to run sudo commands
- Prevents errors from attempting `./rebuild-nixos`
- Based on: Claude Code limitations

**3. Documentation Standards** [RECOMMENDED FOR SWE]
- No temporal markers ("NEW 2025", "Week 1", "Recently added")
- No hyperbolic language ("enterprise-grade", "cutting-edge")
- Documentation creation approval workflow
- Based on: Technical writing best practices 2025

**4. Code Quality** [OPTIONAL]
- Prefer editing over creating new files
- No partial implementations
- Cyclomatic complexity limits
- Based on: SWE best practices

**5. Communication Style** [OPTIONAL]
- Concise vs verbose mode
- Based on: User preferences

**6. Project Management** [OPTIONAL]
- Todo list usage patterns
- Planning requirements
- Based on: Agile/SWE practices

### Community Best Practices Integration (NEW!)

The system now includes **automatic web scraping** to stay up-to-date with the latest best practices!

**Web Scraping Sources:**
- 🌐 **Anthropic Official Docs** - `https://docs.anthropic.com/claude-code/best-practices`
  - Automatically parses policy headings and descriptions
  - Categorizes policies by content keywords
  - Confidence score: 0.8 (official source)

- 🐙 **GitHub Community Examples** - Searches for `.claude/CLAUDE.md` files
  - GitHub code search API: `filename:CLAUDE.md path:.claude`
  - Extracts patterns from real-world usage
  - Confidence score: 0.6 (community patterns)

- 📊 **ClaudeLog Database** - `https://claudelog.com/mechanics/custom-agents/`
  - Aggregated best practices from Claude conversations
  - Note: Currently placeholder, awaiting API access
  - Confidence score: 0.7 (when available)

**Scraping Features:**
- Non-blocking (failures don't prevent generation)
- Timeout protection (5 seconds per source)
- Rate limit handling (GitHub API)
- Automatic categorization and merging with curated policies
- NEW badge detection based on scraped content

**Curated Sources (Always Available):**
- Anthropic official Claude Code documentation
- 2025 AI coding workflow patterns
- Technical writing standards
- Security best practices
- Proven patterns from real usage
- Community GitHub `.claude/CLAUDE.md` examples
- ClaudeLog best practices database
- Automatic updates from multiple sources

To contribute best practices, submit PRs with updates to `_fetch_community_best_practices()` in `user_policies_generator.py`.

### Integration with rebuild-nixos

The user policies system is automatically run as part of:

```bash
./rebuild-nixos  # In nixos-config
```

This ensures:
1. User policies example file always has latest best practices
2. Your custom policies are preserved
3. New users get rich initial template
4. Zero manual maintenance required

## License

MIT
