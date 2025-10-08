#!/usr/bin/env bash
# Modern standalone script to update both CLAUDE.md configurations v2.0
# Uses Jinja2 templating and Pydantic validation via DevEnv

set -e

echo "🔄 Updating Claude Code configurations (v2.0)..."
echo

# Change to nixos-config directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"
cd "$CONFIG_DIR"

echo "📁 Working directory: $PWD"
echo

# FIRST: Update user policies (example file always, user file only if missing)
echo "📝 Updating user-defined policies..."
if (cd scripts && devenv shell python update-user-policies-v2.py); then
    echo "✅ User policies files updated"
else
    echo "⚠️  Warning: User policies update failed (continuing...)"
fi
echo

# SECOND: Update project permissions (auto-detect project type and optimize)
echo "🔒 Updating project permissions (.claude/settings.local.json)..."
if (cd scripts && devenv shell python update-permissions-v2.py "$CONFIG_DIR"); then
    echo "✅ Project permissions optimized"
else
    echo "⚠️  Warning: Permissions update failed (continuing...)"
fi
echo

# THEN: Use DevEnv-managed modern template-based system
echo "🛠️  Updating system-level tool inventory (~/.claude/CLAUDE.md)..."
if (cd scripts && devenv shell python update-system-claude-v2.py); then
    echo "✅ System-level Claude configuration updated"
else
    echo "❌ Failed to update system-level Claude config"
    exit 1
fi
echo

echo "📋 Updating project-level CLAUDE.md (./CLAUDE.md)..."
if (cd scripts && devenv shell python update-project-claude-v2.py); then
    echo "✅ Project-level CLAUDE.md updated"
else
    echo "❌ Failed to update project-level CLAUDE.md"
    exit 1
fi
echo

echo "🎉 All Claude Code configurations updated successfully!"
echo
echo "📊 Summary:"
echo "   - User policies: ~/.claude/CLAUDE-USER-POLICIES.md (your custom policies, preserved)"
echo "   - Example policies: ~/.claude/CLAUDE-USER-POLICIES.md.example (latest best practices)"
echo "   - Project permissions: ./.claude/settings.local.json (auto-optimized per project type)"
echo "   - System-level: ~/.claude/CLAUDE.md (tool inventory for Claude Code)"
echo "   - Project-level: ./CLAUDE.md (project guidance and context)"
echo
echo "💡 These files are now synchronized with your current NixOS configuration."
echo "🔧 Generated using modern Jinja2 templates with Pydantic validation"

# Show git status if in a git repo
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo
    echo "📝 Git status:"
    git status --porcelain CLAUDE.md 2>/dev/null || echo "   No changes to project CLAUDE.md"
fi