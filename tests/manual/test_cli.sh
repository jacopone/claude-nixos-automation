#!/usr/bin/env bash
cd /home/guyfawkes/claude-nixos-automation

echo "🧪 Testing CLI..."
echo ""

devenv shell -c "python run-adaptive-learning.py --dry-run" 2>&1
