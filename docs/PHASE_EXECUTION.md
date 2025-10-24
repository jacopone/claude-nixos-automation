---
status: active
created: 2025-01-24
updated: 2025-01-24
type: architecture
lifecycle: persistent
---

# rebuild-nixos Phase Execution Architecture

## Overview

The `rebuild-nixos` script executes 14 sequential phases to rebuild the NixOS system, update configurations, and clean up resources. Each phase is designed with:

- **Clear success/failure criteria**
- **Graceful degradation** (non-critical phases continue on failure)
- **User visibility** (progress indicators, summaries, error details)
- **Rollback safety** (critical phases have rollback paths)

## Phase Execution Flow

```
┌───────────────────────────────────────────────────────────────────┐
│                 rebuild-nixos Execution Flow                      │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Update Flake Inputs                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Updates flake.lock to latest package versions                   │
│ Exit on failure: YES (can't build without valid inputs)         │
│ Rollback: No (changes not activated yet)                        │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Test Build                                             │
│ ─────────────────────────────────────────────────────────────── │
│ Builds new configuration WITHOUT activating (safe to fail)      │
│ Exit on failure: YES (don't activate broken config)             │
│ Rollback: No (no system changes made)                           │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Activate Configuration  ⚠️ CRITICAL                    │
│ ─────────────────────────────────────────────────────────────── │
│ Switches running system to new configuration (requires sudo)    │
│ Exit on failure: YES (activation failed, system unchanged)      │
│ Rollback: YES (sudo nixos-rebuild switch --rollback)            │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Update Claude Code Configurations                      │
│ ─────────────────────────────────────────────────────────────── │
│ Regenerates 5 Claude context files (CLAUDE.md, permissions, etc)│
│ Exit on failure: NO (continue with warnings - not critical)     │
│ Rollback: No (files can be manually reverted via git)           │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: MCP Usage Analytics                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Analyzes MCP server utilization, generates report               │
│ Exit on failure: NO (non-critical analytics)                    │
│ Rollback: No (read-only analysis)                               │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: Tool Usage Analytics                                   │
│ ─────────────────────────────────────────────────────────────── │
│ Tracks which system tools are used vs installed                 │
│ Exit on failure: NO (non-critical analytics)                    │
│ Rollback: No (read-only analysis)                               │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 7: Adaptive Learning Cycle  🧠 INTERACTIVE               │
│ ─────────────────────────────────────────────────────────────── │
│ Runs 7 parallel ML analyzers, presents suggestions to user      │
│ Exit on failure: NO (learning is optional)                      │
│ User interaction: YES (approval of suggestions)                 │
│ Rollback: Per-suggestion (each has undo instructions)           │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 8: User Acceptance  👤 INTERACTIVE                        │
│ ─────────────────────────────────────────────────────────────── │
│ User tests configuration, can rollback or create git commit     │
│ Exit on failure: NO (user choice)                               │
│ Rollback: YES (if user rejects changes)                         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 9: Generation Cleanup                                     │
│ ─────────────────────────────────────────────────────────────── │
│ Deletes old NixOS generations, runs garbage collection          │
│ Exit on failure: NO (cleanup is optional)                       │
│ Rollback: No (user selects which generations to delete)         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 10: Disk Space Analysis                                   │
│ ─────────────────────────────────────────────────────────────── │
│ Scans for oversized logs, sessions, configs, backups            │
│ Exit on failure: NO (analysis only, no changes)                 │
│ Rollback: No (read-only)                                        │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 11: Cache Cleanup                                         │
│ ─────────────────────────────────────────────────────────────── │
│ Cleans UV, Chrome, Yarn, npm, pnpm caches                       │
│ Exit on failure: NO (cleanup is optional)                       │
│ Rollback: No (caches regenerate on demand)                      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 12: Claude Session Lifecycle Cleanup                      │
│ ─────────────────────────────────────────────────────────────── │
│ Deletes sessions marked as IMPLEMENTED (insights extracted)     │
│ Exit on failure: NO (cleanup is optional)                       │
│ Rollback: No (only deletes IMPLEMENTED sessions)                │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 13: Claude Backup Cleanup                                 │
│ ─────────────────────────────────────────────────────────────── │
│ Cleans .backups/ directory (old Claude backup files)            │
│ Exit on failure: NO (cleanup is optional)                       │
│ Rollback: No (user confirms before deletion)                    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 14: Git Push                                              │
│ ─────────────────────────────────────────────────────────────── │
│ Pushes committed changes to remote repository                   │
│ Exit on failure: NO (user can manually push later)              │
│ Rollback: No (requires manual git operations)                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
                   REBUILD COMPLETE ✅
```

## Phase Categories

### Critical Phases (Exit on Failure)

These phases MUST succeed for rebuild to continue:

1. **Phase 1: Update Flake Inputs** - Can't build without valid lock file
2. **Phase 2: Test Build** - Don't activate broken configurations
3. **Phase 3: Activate Configuration** - System activation must succeed

If any critical phase fails, the script exits immediately with error details.

### Non-Critical Phases (Continue on Failure)

These phases improve system but are optional:

- **Phase 4-7**: Configuration updates and analytics (logged, not blocking)
- **Phase 9-13**: Cleanup operations (user can skip or do manually)
- **Phase 14**: Git push (user can push manually later)

If a non-critical phase fails, a warning is logged and execution continues.

### Interactive Phases (User Approval Required)

These phases require user interaction:

- **Phase 7**: Adaptive learning (user approves suggestions)
- **Phase 8**: User acceptance (test and commit)
- **Phase 9**: Generation cleanup (select generations)
- **Phase 11**: Cache cleanup (confirm deletion)
- **Phase 12**: Session cleanup (confirm deletion)
- **Phase 13**: Backup cleanup (select option)
- **Phase 14**: Git push (confirm push)

## Error Handling Patterns

### Pattern 1: Exit on Failure (Critical Phases)

```bash
if [ $BUILD_EXIT -ne 0 ]; then
    log_error "Test build failed (exit code: $BUILD_EXIT)"
    echo "Check logs: $LOG_FILE"
    exit 1
fi
```

**When to use**: Phases where failure makes continuation impossible or dangerous.

### Pattern 2: Warn and Continue (Non-Critical Phases)

```bash
if [ $AUTOMATION_EXIT -ne 0 ]; then
    log_warning "Claude automation had issues (check logs)"
    # Continue execution
fi
```

**When to use**: Phases where failure is inconvenient but not blocking.

### Pattern 3: Graceful Degradation (Analytics)

```bash
if (cd ~/nixos-config && $MCP_CMD 2>/dev/null); then
    log_success "MCP analysis completed"
else
    log_warning "MCP analysis had issues (non-critical)"
fi
```

**When to use**: Analytics and reporting phases that enhance UX but aren't essential.

### Pattern 4: User Confirmation (Cleanup Operations)

```bash
read -p "Clean these cache directories? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Perform cleanup
else
    log_warning "Cache cleanup skipped"
fi
```

**When to use**: Potentially destructive operations where user should have final say.

## Progress Visibility

### Real-Time Progress Indicators

For long-running phases (test build, activation), the script shows:

- **Spinner**: Animated indicator that the process is running
- **Elapsed time**: Current duration (MM:SS format)
- **ETA**: Estimated time remaining (based on last 5 builds)
- **Live status**: Current operation from log file (e.g., "building chromium")

Example output:
```
⠋  ⏱️  02:34 | ~01:15 remaining | building chromium
```

### Phase Summaries

At the end, the script prints:

1. **Actions completed**: What changed (e.g., "Updated flake.lock", "Cleared 450MB of cache")
2. **Statistics**: Quantitative data (e.g., "Tools: 87/122 used | 71% adoption")
3. **Warnings**: Issues that need attention (e.g., "5 log files >100MB")

## Log Management

### Log Files Created

- `~/.claude/.logs/rebuild-YYYYMMDD-HHMMSS.log` - Main rebuild log
- `~/.claude/.logs/rebuild-YYYYMMDD-HHMMSS.log.automation` - Automation subprocess log

### Log Retention

- Last 10 build times stored in `~/.claude/.logs/build-times.log` (for ETA calculation)
- Rebuild logs kept indefinitely (user must manually clean)

### Finding Errors in Logs

**Auto-tail on failure**: When a critical phase fails, the last 20 lines are automatically displayed.

**Manual inspection**:
```bash
# View last rebuild log
bat ~/.claude/.logs/rebuild-*.log | tail -100

# Search for errors
rg "error:|failed:" ~/.claude/.logs/rebuild-*.log
```

## Rollback Procedures

### Rollback Activated Configuration (Phase 3 failure)

```bash
sudo nixos-rebuild switch --rollback
```

This reverts to the previous generation (before activation).

### Rollback User-Rejected Changes (Phase 8)

The script automatically runs rollback if user rejects changes:

```bash
# Automatic rollback triggered by user answering "n"
log_step "Changes rejected. Rolling back to previous configuration..."
sudo nixos-rebuild switch --rollback
```

### Undo Individual Improvements (Phase 7)

Each adaptive learning suggestion includes undo instructions:

- **Permission patterns**: Remove from `.claude/settings.local.json`
- **MCP optimizations**: Edit `.claude/mcp.json` and restore server
- **Context changes**: Revert CLAUDE.md via git
- **Workflow shortcuts**: Delete slash command file

## Performance Optimization

### Parallel Execution

- **Phase 7** runs 7 analyzers concurrently (saves ~1.5-2s)
- **Phase 12** uses bash+jq instead of Python (saves ~300ms)

### Minimal Python Startups

- **Lifecycle operations** consolidated into single Python script (saves ~300ms)
- **Health checks** done once before analyzer execution

### Build Time Tracking

The script learns from past builds to provide accurate ETAs:

- Tracks last 10 build durations
- Calculates average and displays ETA
- Updates estimates after each build

## Safety Mechanisms

### 1. Sudo Credential Caching

```bash
# Cache credentials early to avoid timeout during activation
sudo -v || { log_error "Failed to obtain sudo access"; exit 1; }
```

Prevents sudo timeout during long-running Phase 2.

### 2. Test Build Before Activation

Phase 2 builds the new configuration but doesn't activate it. This catches:
- Syntax errors
- Missing dependencies
- Build failures
- Configuration conflicts

If Phase 2 fails, system is unchanged and can be fixed.

### 3. User Acceptance Gate

Phase 8 requires explicit user confirmation before committing changes. User can:
- Test the new configuration
- Verify services are running
- Check for regressions
- Roll back if issues found

### 4. Verbose Mode Safety

Run with `--verbose` to see all output in real-time:

```bash
./rebuild-nixos --verbose
```

Useful for:
- Debugging build failures
- Watching package downloads
- Seeing exact error messages

## Common Failure Scenarios

### Scenario 1: Test Build Fails (Phase 2)

**Symptoms**:
```
❌ Test build failed (exit code: 1)
Check logs: ~/.claude/.logs/rebuild-20250124-153042.log
```

**Resolution**:
1. Check logs: `bat ~/.claude/.logs/rebuild-*.log | tail -100`
2. Look for error messages (syntax errors, missing packages)
3. Fix configuration issues
4. Re-run `./rebuild-nixos`

### Scenario 2: Activation Fails (Phase 3)

**Symptoms**:
```
❌ Activation failed (exit code: 1)
📁 Check logs: ~/.claude/.logs/rebuild-20250124-153042.log
```

**Resolution**:
1. System is still on old configuration (safe)
2. Check logs for activation errors
3. Common causes:
   - Conflicting services
   - Invalid systemd units
   - Permission issues
4. Fix issues and retry

### Scenario 3: Adaptive Learning Crashes (Phase 7)

**Symptoms**:
```
⚠️  Adaptive learning had issues (exit code: 1)
```

**Resolution**:
1. Non-critical - system rebuild succeeded
2. Check learning logs: `bat ~/claude-nixos-automation/devenv.log`
3. Common causes:
   - Missing prerequisites (approval history, session logs)
   - Analyzer failures (permission errors, data corruption)
4. Run health check: `python3 ~/claude-nixos-automation/check-analyzer-health.py`

### Scenario 4: Out of Disk Space

**Symptoms**:
```
🔴 URGENT: Learning data disk usage critical!
```

**Resolution**:
1. Run adaptive learning to extract insights
2. Delete IMPLEMENTED sessions (Phase 12)
3. Clean caches (Phase 11)
4. Delete old generations (Phase 9)
5. Consider archiving old logs

## Integration with claude-nixos-automation

### Local Development Mode

If `~/claude-nixos-automation` exists, the script uses the local flake:

```bash
nix run ~/claude-nixos-automation#update-all
```

### Production Mode (GitHub Fallback)

If local directory doesn't exist, uses published version:

```bash
nix run github:jacopone/claude-nixos-automation#update-all
```

### Automation Commands Invoked

1. **Phase 4**: `nix run <flake>#update-all`
   - Runs `update-claude-configs-v2.sh`
   - Updates 5 Claude configuration files
   - Generates tool inventory and permissions

2. **Phase 5**: `nix run <flake>#update-mcp-usage-analytics`
   - Analyzes MCP server usage
   - Marks sessions as ANALYZED
   - Generates `.claude/mcp-analytics.md`

3. **Phase 6**: `python3 <flake>/update-tool-usage-analytics.py`
   - Tracks tool usage vs installation
   - Calculates adoption rate
   - Generates `.claude/tool-analytics.md`

4. **Phase 7**: `devenv shell -- python run-adaptive-learning.py --interactive`
   - Runs 7 parallel analyzers
   - Presents suggestions interactively
   - Applies approved improvements

## Future Improvements

### Planned Enhancements

1. **Structured error reporting** - Log aggregator to auto-tail errors
2. **Analyzer health dashboard** - Pre-flight validation before Phase 7
3. **Phase timing metrics** - Track duration per phase for optimization
4. **Configurable phase selection** - Skip phases via CLI flags

### Monitoring Integration Ideas

- Export phase durations to metrics system (Prometheus, InfluxDB)
- Alert on critical phase failures
- Track rebuild success rate over time
- Correlate failures with flake updates

---

*Last updated: 2025-01-24*
*Maintainer: Claude Code*
*Related: adaptive_system_engine.py, run-adaptive-learning.py*
