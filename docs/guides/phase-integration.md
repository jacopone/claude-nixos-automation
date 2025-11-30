---
status: active
created: 2025-10-22
updated: 2025-10-22
type: guide
lifecycle: persistent
---

# Phase 1.5 & 2: Intelligent Data Lifecycle Management

## Overview

This document describes Phase 1.5 (History Tracking) and Phase 2 (Lifecycle Tracking) implementations that enable intelligent, value-based cleanup of Claude Code session data.

## Phase 1.5: History Tracking & Growth Projections

### What It Does

- **Tracks disk usage over time** in `~/.claude/learning/disk_health_history.jsonl`
- **Calculates growth rate**: MB/month based on historical data
- **Projects months until disk full**: Based on growth rate and available space

### New Components

1. **DiskHealthSnapshot** (`claude_automation/schemas/health.py`)
   - Schema for storing historical disk metrics
   - Fields: timestamp, total_mb, session_logs_mb, learning_data_mb, archives_mb, available_gb, session_count

2. **DiskHealthTracker** (`claude_automation/analyzers/disk_health_tracker.py`)
   - Records snapshots to history file
   - Calculates growth rate from historical data (requires 2+ snapshots)
   - Projects disk exhaustion timeline

3. **Updated DiskHealthMonitor** (`claude_automation/analyzers/disk_health_monitor.py`)
   - Now uses DiskHealthTracker to record snapshots
   - Populates `growth_mb_per_month` and `months_until_full` fields in reports

### Usage

```bash
# Run disk health check (records snapshot automatically)
nix run github:jacopone/claude-nixos-automation#check-data-health

# First run: Shows "Insufficient data for projection"
# After 2+ runs: Shows growth rate and projection
```

### Example Output (After 2+ Runs)

```
  Disk Space:
     • Available: 120GB
     • Usage: 0.52% of disk
     • Growth: ~15MB/month
     • Projection: 500+ years ✅
```

---

## Phase 2: Session Lifecycle Tracking

### What It Does

- **Tracks value extraction stages** for each session: RAW → ANALYZED → INSIGHTS_GENERATED → IMPLEMENTED
- **Enables safe cleanup**: Only delete sessions marked as IMPLEMENTED
- **Automatic marking**: MCP usage analyzer marks sessions as ANALYZED when processed

### Lifecycle Stages

| Stage | Description | Safe to Cleanup? |
|-------|-------------|------------------|
| **RAW** | Session just created, not analyzed yet | ❌ No |
| **ANALYZED** | Processed by MCP/usage analytics | ❌ No |
| **INSIGHTS_GENERATED** | Insights extracted and documented | ❌ No |
| **IMPLEMENTED** | Insights applied to system config | ✅ Yes |

### New Components

1. **SessionLifecycle** enum (`claude_automation/schemas/lifecycle.py`)
   - Four lifecycle stages

2. **SessionMetadata** (`claude_automation/schemas/lifecycle.py`)
   - Lifecycle metadata for each session
   - Stored as sidecar files: `session.jsonl.lifecycle.json`
   - Tracks timestamps for each stage transition

3. **LifecycleStats** (`claude_automation/schemas/lifecycle.py`)
   - Statistics about session distribution across stages

4. **SessionLifecycleTracker** (`claude_automation/analyzers/session_lifecycle_tracker.py`)
   - Load/save lifecycle metadata
   - Mark sessions at specific stages
   - Query sessions by stage
   - Get sessions safe to cleanup

5. **Updated MCPUsageAnalyzer** (`claude_automation/analyzers/mcp_usage_analyzer.py`)
   - Now automatically marks analyzed sessions as ANALYZED
   - Non-blocking: Won't fail if lifecycle tracking fails

### Sidecar File Format

For session `~/.claude/projects/myproject/abc123.jsonl`, metadata is stored at:
`~/.claude/projects/myproject/abc123.jsonl.lifecycle.json`

```json
{
  "session_file": "/home/user/.claude/projects/myproject/abc123.jsonl",
  "lifecycle_stage": "analyzed",
  "created_at": "2025-10-20T10:30:00",
  "analyzed_at": "2025-10-20T14:00:00",
  "insights_generated_at": null,
  "implemented_at": null,
  "project_name": "myproject",
  "insights_summary": null,
  "implementation_notes": null
}
```

### Programmatic Usage

```python
from pathlib import Path
from claude_automation.analyzers.session_lifecycle_tracker import SessionLifecycleTracker
from claude_automation.schemas.lifecycle import SessionLifecycle

tracker = SessionLifecycleTracker()

# Get lifecycle statistics
stats = tracker.get_lifecycle_stats()
print(f"Total sessions: {stats.total_sessions}")
print(f"RAW: {stats.raw_count}")
print(f"ANALYZED: {stats.analyzed_count}")
print(f"Safe to cleanup: {stats.safe_to_cleanup_count}")

# Get sessions safe to cleanup
safe_sessions = tracker.get_safe_to_cleanup_sessions()
for session_path in safe_sessions:
    print(f"Can delete: {session_path}")

# Mark session with insights
tracker.mark_session(
    Path("~/.claude/projects/myproject/abc123.jsonl").expanduser(),
    SessionLifecycle.INSIGHTS_GENERATED,
    notes="Identified pattern: Use fd instead of find"
)

# Mark insights as implemented
tracker.mark_session(
    Path("~/.claude/projects/myproject/abc123.jsonl").expanduser(),
    SessionLifecycle.IMPLEMENTED,
    notes="Updated CLAUDE.md with fd recommendation"
)
```

---

## Integration with rebuild-nixos (nixos-config)

### Current Cleanup Logic (Unsafe)

The current rebuild-nixos script has this cleanup prompt:

```bash
# Lines 549-570 (approx)
OLD_SESSIONS=$(find ~/.claude/projects -name "*.jsonl" -mtime +30)
if [ -n "$OLD_SESSIONS" ]; then
    echo "Found sessions older than 30 days"
    read -p "Delete? [y/N]: " response
    if [ "$response" = "y" ]; then
        echo "$OLD_SESSIONS" | xargs rm -f
    fi
fi
```

**Problem**: Deletes sessions older than 30 days regardless of whether insights were extracted.

### Recommended Update (Safe, Value-Based)

Replace the cleanup section with lifecycle-aware logic:

```bash
# Phase 2: Lifecycle-based cleanup (only delete IMPLEMENTED sessions)
echo ""
echo "  📋 Checking session lifecycle..."

# Get lifecycle statistics using the tracker
LIFECYCLE_STATS=$(python3 <<'PYTHON'
from claude_automation.analyzers.session_lifecycle_tracker import SessionLifecycleTracker

tracker = SessionLifecycleTracker()
stats = tracker.get_lifecycle_stats()

print(f"Total: {stats.total_sessions}")
print(f"RAW: {stats.raw_count}")
print(f"ANALYZED: {stats.analyzed_count}")
print(f"INSIGHTS_GENERATED: {stats.insights_generated_count}")
print(f"IMPLEMENTED: {stats.implemented_count}")
print(f"SAFE_TO_CLEANUP: {stats.safe_to_cleanup_count}")
PYTHON
)

TOTAL=$(echo "$LIFECYCLE_STATS" | grep "Total:" | cut -d: -f2 | xargs)
SAFE_COUNT=$(echo "$LIFECYCLE_STATS" | grep "SAFE_TO_CLEANUP:" | cut -d: -f2 | xargs)
VALUABLE=$(echo "$LIFECYCLE_STATS" | grep -E "(RAW|ANALYZED|INSIGHTS_GENERATED):" | awk -F: '{sum += $2} END {print sum}')

echo "     • Total sessions: $TOTAL"
echo "     • Safe to cleanup (IMPLEMENTED): $SAFE_COUNT"
echo "     • Still valuable (not analyzed/implemented): $VALUABLE"

if [ "$SAFE_COUNT" -gt 0 ]; then
    echo ""
    read -p "  Delete $SAFE_COUNT IMPLEMENTED sessions? [y/N]: " response

    if [ "$response" = "y" ]; then
        python3 <<'PYTHON'
from claude_automation.analyzers.session_lifecycle_tracker import SessionLifecycleTracker

tracker = SessionLifecycleTracker()
safe_sessions = tracker.get_safe_to_cleanup_sessions()

for session_path in safe_sessions:
    try:
        session_path.unlink()
        # Also delete sidecar metadata file
        metadata_path = session_path.parent / f"{session_path.name}.lifecycle.json"
        if metadata_path.exists():
            metadata_path.unlink()
        print(f"Deleted: {session_path.name}")
    except Exception as e:
        print(f"Could not delete {session_path.name}: {e}")

print(f"\n✅ Cleaned up {len(safe_sessions)} IMPLEMENTED sessions")
PYTHON
    fi
elif [ "$VALUABLE" -gt 0 ]; then
    echo ""
    echo "  ⚠️  No sessions marked as IMPLEMENTED yet"
    echo "     Run adaptive learning cycle to analyze and extract insights first"
fi
```

### Integration with Disk Health Check

Add disk health check BEFORE cleanup prompt:

```bash
# Run disk health check
echo ""
echo "  📊 Checking data health..."
if command -v check-data-health >/dev/null 2>&1; then
    HEALTH_EXIT_CODE=0
    check-data-health || HEALTH_EXIT_CODE=$?

    if [ $HEALTH_EXIT_CODE -eq 2 ]; then
        echo ""
        echo "  🔴 URGENT: Learning data disk usage critical!"
        echo "     Run adaptive learning cycle to extract insights, then cleanup"
    elif [ $HEALTH_EXIT_CODE -eq 1 ]; then
        echo ""
        echo "  🟡 Learning data growing - consider cleanup after insights extracted"
    fi
else
    echo "     (check-data-health not found - install claude-nixos-automation)"
fi
```

---

## Workflow: From Session Creation to Safe Cleanup

1. **Session Created** → Lifecycle: `RAW`
   - Session .jsonl file created in `~/.claude/projects/<project>/`

2. **MCP Analytics Run** → Lifecycle: `ANALYZED`
   - MCP usage analyzer processes session
   - Automatically marks session as `ANALYZED`
   - Lifecycle metadata created: `session.jsonl.lifecycle.json`

3. **Insights Extracted** → Lifecycle: `INSIGHTS_GENERATED`
   - User or adaptive learning cycle identifies valuable patterns
   - Manually marked via `SessionLifecycleTracker.mark_session()`
   - Insights summary recorded in metadata

4. **Insights Implemented** → Lifecycle: `IMPLEMENTED`
   - Changes applied to system config (e.g., CLAUDE.md updated)
   - Manually marked via `SessionLifecycleTracker.mark_session()`
   - Implementation notes recorded in metadata

5. **Safe Cleanup**
   - rebuild-nixos queries for `IMPLEMENTED` sessions
   - Only these sessions are offered for deletion
   - Sidecar metadata files also deleted

---

## Benefits

### Phase 1.5 Benefits

- **Contextual risk assessment**: Know if data growth is actually a problem
- **Predictive planning**: "You have 2 years at current growth rate"
- **No false alarms**: 10GB on 1TB disk = GREEN, not panic

### Phase 2 Benefits

- **Value-based cleanup**: Never delete unanalyzed data
- **Automatic tracking**: MCP analytics marks sessions when processed
- **Transparent lifecycle**: See exactly which sessions have value
- **Safe defaults**: Only IMPLEMENTED sessions can be deleted

### Combined Benefits

- **No destructive feedback loop**: Cleanup never deletes learning data
- **Visibility**: Disk health + lifecycle stats show full picture
- **Automation-friendly**: Both systems work without manual intervention
- **Fail-safe**: Lifecycle tracking errors don't break analysis

---

## Testing

### Test Phase 1.5

```bash
# Run 1: Records first snapshot
nix run github:jacopone/claude-nixos-automation#check-data-health
# Output: "Insufficient data (run 2+ rebuilds for projection)"

# Run 2 (next day): Calculates growth
nix run github:jacopone/claude-nixos-automation#check-data-health
# Output: "Growth: ~10MB/month, projected 500+ years"

# Inspect history
cat ~/.claude/learning/disk_health_history.jsonl | jq .
```

### Test Phase 2

```python
from pathlib import Path
from claude_automation.analyzers.session_lifecycle_tracker import SessionLifecycleTracker
from claude_automation.schemas.lifecycle import SessionLifecycle

tracker = SessionLifecycleTracker()

# Create test session (simulate)
test_session = Path("~/.claude/projects/test/test-session.jsonl").expanduser()
test_session.parent.mkdir(parents=True, exist_ok=True)
test_session.write_text('{"test": true}\n')

# Check initial stats
stats = tracker.get_lifecycle_stats()
print(f"RAW sessions: {stats.raw_count}")  # Should include test session

# Mark as analyzed
tracker.mark_session(test_session, SessionLifecycle.ANALYZED)

# Verify
metadata = tracker.load_metadata(test_session)
print(f"Stage: {metadata.lifecycle_stage}")  # Should be "analyzed"
print(f"Safe to cleanup: {metadata.is_safe_to_cleanup}")  # False

# Mark as implemented
tracker.mark_session(test_session, SessionLifecycle.IMPLEMENTED)
print(f"Safe to cleanup: {tracker.load_metadata(test_session).is_safe_to_cleanup}")  # True

# Cleanup
safe = tracker.get_safe_to_cleanup_sessions()
print(f"Sessions safe to delete: {len(safe)}")
```

---

## Files Changed

### New Files

- `claude_automation/schemas/lifecycle.py` - Lifecycle schemas
- `claude_automation/analyzers/disk_health_tracker.py` - History tracking
- `claude_automation/analyzers/session_lifecycle_tracker.py` - Lifecycle management
- `PHASE_1_5_AND_2_INTEGRATION.md` - This document

### Modified Files

- `claude_automation/schemas/health.py` - Added DiskHealthSnapshot
- `claude_automation/schemas/__init__.py` - Exported new schemas
- `claude_automation/analyzers/disk_health_monitor.py` - Integrated history tracking
- `claude_automation/analyzers/mcp_usage_analyzer.py` - Integrated lifecycle marking

### Data Files Created

- `~/.claude/learning/disk_health_history.jsonl` - Growth tracking
- `~/.claude/projects/**/*.jsonl.lifecycle.json` - Session metadata (sidecar files)

---

## Next Steps

1. **Update rebuild-nixos** (nixos-config repo)
   - Replace age-based cleanup with lifecycle-based cleanup
   - Add disk health check before cleanup prompt
   - Display lifecycle statistics

2. **Manual marking workflow** (optional)
   - Create helper scripts to mark sessions with insights
   - Integrate with adaptive learning cycle

3. **Phase 3** (future)
   - Deep analysis mode for RAW sessions
   - Automatic insight extraction
   - Archive/compress IMPLEMENTED sessions instead of deleting
