#!/usr/bin/env bash
cd /home/guyfawkes/claude-nixos-automation

echo "🧪 Testing CLI..."
echo ""

devenv shell -c "uv run python run-adaptive-learning.py --dry-run" 2>&1
