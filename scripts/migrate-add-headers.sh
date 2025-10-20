#!/usr/bin/env bash
#
# Migration script: Add generation headers to existing CLAUDE.md files
#
# This script is idempotent - safe to run multiple times.
# It adds AUTO-GENERATED headers to CLAUDE.md files that don't have them yet.
#
# Usage:
#   ./scripts/migrate-add-headers.sh [--dry-run]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run]"
            exit 1
            ;;
    esac
done

echo "======================================"
echo "CLAUDE.md Header Migration Script"
echo "======================================"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}Running in DRY-RUN mode (no files will be modified)${NC}"
    echo ""
fi

# Function to check if file already has header
has_header() {
    local file="$1"

    # Check for AUTO-GENERATED marker in first 20 lines
    if head -n 20 "$file" 2>/dev/null | grep -q "AUTO-GENERATED"; then
        return 0  # Has header
    else
        return 1  # No header
    fi
}

# Function to add header to file
add_header() {
    local file="$1"
    local backup="$2"

    # Determine generator name based on file location
    local generator_name="Unknown"
    if [[ "$file" == *"/.claude/CLAUDE.md" ]]; then
        generator_name="SystemGenerator"
    elif [[ "$file" == *"/CLAUDE.md" ]] && [[ "$file" != *"/.claude/"* ]]; then
        generator_name="ProjectGenerator"
    fi

    # Get current timestamp
    local timestamp=$(date -Iseconds)

    # Create header
    local header=$(cat <<EOF
<!--
============================================================
  AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY

  Generated: ${timestamp}
  Generator: ${generator_name}
  Sources: N/A (migrated from legacy format)

  To modify, edit source files and regenerate.
============================================================
-->

EOF
)

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would add header to: $file"
        return 0
    fi

    # Create backup
    cp "$file" "$backup"
    echo -e "${GREEN}✓${NC} Created backup: $backup"

    # Add header
    echo "$header" | cat - "$file" > "${file}.tmp"
    mv "${file}.tmp" "$file"
    echo -e "${GREEN}✓${NC} Added header to: $file"
}

# Function to process a CLAUDE.md file
process_file() {
    local file="$1"

    echo ""
    echo "Processing: $file"

    if [[ ! -f "$file" ]]; then
        echo -e "${RED}✗${NC} File not found, skipping"
        return 1
    fi

    # Check if already has header
    if has_header "$file"; then
        echo -e "${GREEN}✓${NC} Already has header, skipping"
        return 0
    fi

    # Create backup filename
    local backup_dir="$(dirname "$file")/.backups"
    mkdir -p "$backup_dir"
    local backup="$backup_dir/$(basename "$file").backup-$(date +%Y%m%d-%H%M%S)"

    # Add header
    add_header "$file" "$backup"

    return 0
}

# Main migration logic
echo "Searching for CLAUDE.md files..."
echo ""

PROCESSED=0
SKIPPED=0
FAILED=0

# Find all CLAUDE.md files
# 1. System-level: ~/.claude/CLAUDE.md
# 2. Project-level: any CLAUDE.md in project directories

# System-level CLAUDE.md
SYSTEM_CLAUDE="$HOME/.claude/CLAUDE.md"
if [[ -f "$SYSTEM_CLAUDE" ]]; then
    if process_file "$SYSTEM_CLAUDE"; then
        if ! has_header "$SYSTEM_CLAUDE"; then
            ((PROCESSED++))
        else
            ((SKIPPED++))
        fi
    else
        ((FAILED++))
    fi
fi

# Project-level CLAUDE.md files
# Search in common project locations
PROJECT_DIRS=(
    "$HOME/projects"
    "$HOME/nixos-config"
    "$HOME/claude-nixos-automation"
)

for dir in "${PROJECT_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        while IFS= read -r -d '' file; do
            if process_file "$file"; then
                if ! has_header "$file"; then
                    ((PROCESSED++))
                else
                    ((SKIPPED++))
                fi
            else
                ((FAILED++))
            fi
        done < <(find "$dir" -maxdepth 2 -name "CLAUDE.md" -type f -print0 2>/dev/null || true)
    fi
done

# Summary
echo ""
echo "======================================"
echo "Migration Summary"
echo "======================================"
echo -e "Processed: ${GREEN}$PROCESSED${NC}"
echo -e "Skipped (already has header): ${YELLOW}$SKIPPED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}This was a DRY-RUN. No files were modified.${NC}"
    echo "Run without --dry-run to apply changes."
    echo ""
fi

if [[ $FAILED -gt 0 ]]; then
    exit 1
else
    exit 0
fi
