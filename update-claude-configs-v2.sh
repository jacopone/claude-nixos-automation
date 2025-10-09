#!/usr/bin/env bash
# Modern standalone script to update both CLAUDE.md configurations v2.0
# Uses Jinja2 templating and Pydantic validation via DevEnv

set -e

# Track statistics
declare -a COMPLETED=()
declare -a WARNINGS=()
START_TIME=$(date +%s)

# Helper to run and track
run_step() {
    local step_name="$1"
    local step_cmd="$2"
    local optional="${3:-false}"

    if eval "$step_cmd" 2>&1; then
        COMPLETED+=("$step_name")
        return 0
    else
        if [ "$optional" = "true" ]; then
            WARNINGS+=("$step_name failed (non-critical)")
            return 0
        else
            echo "❌ Failed: $step_name"
            return 1
        fi
    fi
}

echo "🔄 Updating Claude Code configurations (v2.0)..."
echo

# Change to nixos-config directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"
cd "$CONFIG_DIR"

echo "📁 Working directory: $PWD"
echo

# Update user policies
echo "📝 Updating user-defined policies..."
run_step "User policies" "(cd scripts && devenv shell python update-user-policies-v2.py)" true
echo

# Update permissions
echo "🔒 Updating project permissions (.claude/settings.local.json)..."
run_step "Project permissions" "(cd scripts && devenv shell python update-permissions-v2.py \"$CONFIG_DIR\")" true
echo

# Update system-level CLAUDE.md
echo "🛠️  Updating system-level tool inventory (~/.claude/CLAUDE.md)..."
run_step "System CLAUDE.md" "(cd scripts && devenv shell python update-system-claude-v2.py)"
echo

# Update project-level CLAUDE.md
echo "📋 Updating project-level CLAUDE.md (./CLAUDE.md)..."
run_step "Project CLAUDE.md" "(cd scripts && devenv shell python update-project-claude-v2.py)"
echo

# Update local context
echo "💻 Updating machine-specific context (.claude/CLAUDE.local.md)..."
run_step "Local context" "(cd scripts && devenv shell python update-local-context-v2.py \"$CONFIG_DIR\")" true
echo

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Print summary
echo "╔════════════════════════════════════════════════════════╗"
echo "║           Configuration Update Summary                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo
echo "✅ Completed in ${DURATION}s:"
for item in "${COMPLETED[@]}"; do
    echo "   • $item"
done

if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo
    echo "⚠️  Warnings:"
    for warning in "${WARNINGS[@]}"; do
        echo "   • $warning"
    done
fi

echo
echo "📝 Generated files:"
echo "   • ~/.claude/CLAUDE.md (system tools)"
echo "   • ~/.claude/CLAUDE-USER-POLICIES.md (your policies)"
echo "   • ./CLAUDE.md (project context)"
echo "   • ./.claude/settings.local.json (permissions)"
echo "   • ./.claude/CLAUDE.local.md (machine state)"
echo

if [ ${#WARNINGS[@]} -eq 0 ]; then
    echo "✅ All updates completed successfully!"
else
    echo "⚠️  Updates completed with ${#WARNINGS[@]} warning(s)"
    echo "   Review logs for details if needed"
fi
echo

# Show git status if in a git repo
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📝 Git status:"
    git status --porcelain CLAUDE.md 2>/dev/null || echo "   No changes to project CLAUDE.md"
fi
