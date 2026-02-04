#!/usr/bin/env bash
# Timestamp injector for Claude Code
# Outputs current date, day of week, and time in Italian

# Get day of week number (1=Monday, 7=Sunday)
DAY_NUM=$(date +%u)

# Map to Italian
case $DAY_NUM in
    1) DAY_IT="Lunedì" ;;
    2) DAY_IT="Martedì" ;;
    3) DAY_IT="Mercoledì" ;;
    4) DAY_IT="Giovedì" ;;
    5) DAY_IT="Venerdì" ;;
    6) DAY_IT="Sabato" ;;
    7) DAY_IT="Domenica" ;;
esac

# Format: Giovedì 2026-01-22 14:35
TIMESTAMP="${DAY_IT} $(date '+%Y-%m-%d %H:%M')"

# Output as system context
echo "[Timestamp: ${TIMESTAMP}]"
