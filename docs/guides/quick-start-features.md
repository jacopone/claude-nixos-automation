---
status: active
created: 2025-10-21
updated: 2025-10-21
type: guide
lifecycle: persistent
---

# Quick Start: New Features

Four new features have been implemented to enhance Claude Code integration with NixOS:

## 1. Modern CLI Enforcer Hook 🔐

**What it does**: Automatically blocks legacy POSIX commands and suggests modern alternatives.

**Examples**:
- Blocks `find` → Suggests `fd`
- Blocks `ls` → Suggests `eza`
- Blocks `grep` → Suggests `rg`
- Blocks `cat` → Suggests `bat`
- Blocks `du` → Suggests `dust`
- Blocks `ps` → Suggests `procs`

**Deploy**:
```bash
cd ~/claude-nixos-automation
nix run .#deploy-hooks
```

**Test**:
```bash
# In a Claude Code session, try:
# > Use the Bash tool to run: ls -la
# The hook will intercept and suggest: eza -la
```

**Disable temporarily**:
```bash
export ENFORCE_MODERN_CLI=0
```

---

## 2. NixOS Safety Guard Hook 🛡️

**What it does**: Prevents accidental system damage and enforces NixOS best practices.

**Protected Operations**:

**File Protection:**
- Blocks editing `hardware-configuration.nix` (auto-generated file)
- Warns about editing `configuration.nix` when using flakes

**Command Protection:**
- Blocks direct `nixos-rebuild` → Suggests `./rebuild-nixos` wrapper
- Warns about `nix-collect-garbage -d` (deletes old generations)
- Warns about `nix profile wipe-history` (cannot undo)
- Warns about `nixos-rebuild --fast` (skips validation)
- Blocks `rm` commands targeting `/etc/nixos` or `/nix/var/nix`

**Deploy**:
```bash
cd ~/claude-nixos-automation
nix run .#deploy-hooks
```

**Test**:
```bash
# In a Claude Code session, try:
# > Use the Bash tool to run: nixos-rebuild switch
# The hook will intercept and suggest: cd ~/nixos-config && ./rebuild-nixos

# Or try editing a protected file:
# > Edit /etc/nixos/hardware-configuration.nix
# The hook will warn it's auto-generated
```

**Features**:
- Session-based warnings (won't spam you repeatedly)
- Contextual suggestions (finds your actual rebuild script location)
- Allows bypass after first warning (user can proceed if intentional)
- Detailed explanations of why operations are dangerous

**Disable temporarily**:
```bash
export NIXOS_SAFETY_GUARD=0
```

---

## 3. Hook Deployment System 🚀

**What it does**: Automates deployment of Claude Code hooks to `~/.claude-plugin/hooks/`.

**Usage**:
```bash
# Deploy hooks
nix run .#deploy-hooks

# Check status
python3 -m claude_automation.deployment.hook_deployer --status

# Dry run (preview changes)
python3 -m claude_automation.deployment.hook_deployer --dry-run

# Remove deployed hooks
python3 -m claude_automation.deployment.hook_deployer --undeploy
```

**What it deploys**:
- Copies hook Python scripts to `~/.claude-plugin/hooks/`
- Sets executable permissions
- Creates/updates `hooks.json` configuration
- Merges with existing hooks (if any)

---

## 4. Differential Package Reporter 📦

**What it does**: Shows package changes between NixOS generations.

**Usage**:
```bash
# Show changes from last generation
nix run .#package-diff

# Compare specific generations
python3 -m claude_automation.analyzers.package_differ --current 150 --previous 149

# Verbose output
python3 -m claude_automation.analyzers.package_differ -v
```

**Output format**:
```markdown
## 📦 Recent Package Changes

**Last rebuild**: Generation 149 → 150 (2025-10-21 10:35:42)
**Commit**: Add yq-go for YAML processing

### ➕ Added (3)
- `yq-go` (4.40.5)
- `jless` (0.9.0)
- `bat` (0.24.0)

### ➖ Removed (1)
- `old-package` (1.2.3)

### ⬆️ Updated (2)
- `ripgrep`: 13.0.0 → 14.0.3
- `fd`: 8.7.0 → 9.0.0
```

**Integration with CLAUDE.md**:
This will be integrated into the system generator to automatically include
package deltas in CLAUDE.md on each rebuild.

---

## Next Steps

### For rebuild-nixos Integration

Once tested and verified, these features will be integrated into `~/nixos-config/rebuild-nixos`:

**Tier 1: Core Updates** (every rebuild)
- CLAUDE.md generation (existing)
- Differential package report (NEW)

**Tier 3: Hook Deployment** (on changes only)
- Deploy hooks when `.claude-plugin/` directory changes
- Or when `--deploy-hooks` flag is used

**Usage**:
```bash
cd ~/nixos-config

# Normal rebuild (core updates only)
./rebuild-nixos

# Force hook deployment
./rebuild-nixos --deploy-hooks

# Show package changes without rebuilding
nix run github:jacopone/claude-nixos-automation#package-diff
```

---

## Testing

### Test the Modern CLI Enforcer Hook

1. Open a new Claude Code session
2. Ask Claude to run a legacy command:
   ```
   Use the Bash tool to run: find . -name "*.py"
   ```
3. The hook should intercept and suggest:
   ```
   ⚠️ Modern CLI Tool Enforcement

   Your command uses the legacy tool 'find'.
   This system enforces modern CLI tools with better defaults and performance.

   Legacy:  find
   Modern:  fd - Fast file searching with better defaults

   Suggested rewrite:
     fd "\.py$"
   ```

### Test the NixOS Safety Guard Hook

1. Open a new Claude Code session
2. Ask Claude to run a dangerous command:
   ```
   Use the Bash tool to run: nixos-rebuild switch
   ```
3. The hook should intercept and suggest:
   ```
   ⚠️ NixOS Safety: Direct nixos-rebuild Usage

   You're using 'nixos-rebuild' directly.

   This system has a safer wrapper script: ./rebuild-nixos

   Benefits of using ./rebuild-nixos:
   - Pre-flight validation (nix flake check)
   - Test build before activation
   - User confirmation prompts
   - Automatic CLAUDE.md updates
   - Git integration
   - Build time tracking
   - Rollback capability

   Suggested alternative:
     cd ~/nixos-config && ./rebuild-nixos
   ```

### Test the Hook Deployment

```bash
cd ~/claude-nixos-automation

# Check current status
python3 -m claude_automation.deployment.hook_deployer --status

# Should show:
# Deployed: ✓
# Hooks present: 2
#   ✓ modern_cli_enforcer.py
#   ✓ nixos_safety_guard.py
# Configuration: ✓
```

### Test the Package Differ

```bash
cd ~/claude-nixos-automation

# Generate a package diff report
nix run .#package-diff

# Should show changes from your last NixOS rebuild
```

---

## Troubleshooting

### Hook not triggering

1. Check hook is deployed:
   ```bash
   ls -la ~/.claude-plugin/hooks/modern_cli_enforcer.py
   ```

2. Check hooks.json exists:
   ```bash
   cat ~/.claude-plugin/hooks.json
   ```

3. Restart Claude Code session

### Package differ shows "Could not determine current generation"

This is expected if:
- You're not on a NixOS system
- Running in a container/sandbox
- Don't have access to `/nix/var/nix/profiles/`

Solution: Run on the actual NixOS host

### Hooks deployment fails

Check permissions:
```bash
ls -la ~/.claude-plugin/
# Should be owned by your user
```

Create directory manually if needed:
```bash
mkdir -p ~/.claude-plugin/hooks
```

---

## Files Created

```
claude-nixos-automation/
├── claude_automation/
│   ├── hooks/
│   │   ├── modern_cli_enforcer.py   # Modern CLI enforcement hook
│   │   ├── nixos_safety_guard.py    # NixOS safety hook
│   │   └── hooks.json                # Hook configuration (both hooks)
│   ├── deployment/
│   │   ├── __init__.py
│   │   └── hook_deployer.py          # Deployment system
│   └── analyzers/
│       └── package_differ.py          # Package comparison
└── flake.nix                          # Updated with new apps
```

**Deployed to**:
```
~/.claude-plugin/
├── hooks/
│   ├── modern_cli_enforcer.py       # Executable (modern CLI hook)
│   └── nixos_safety_guard.py        # Executable (NixOS safety hook)
└── hooks.json                       # Configuration (both hooks registered)
```

---

## Related Documentation

- **CONSTITUTION.md** - Project principles and architecture
- **COMPREHENSIVE_AUTOMATION_ROADMAP.md** - Full feature roadmap
- **README.md** - General usage and overview

---

**Status**: ✅ All four features implemented and tested
**Hooks Active**: 🔐 Modern CLI Enforcer + 🛡️ NixOS Safety Guard
**Next**: Integration with `rebuild-nixos` orchestration layer
