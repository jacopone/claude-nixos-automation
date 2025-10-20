#!/usr/bin/env bash
#
# Reorganize documentation files based on YAML frontmatter classification.
#
# This script moves markdown files from the root directory to appropriate
# subdirectories based on their frontmatter type and lifecycle fields.
#
# Usage:
#     bash scripts/reorganize-docs.sh [--dry-run]
#
# Options:
#     --dry-run    Show what would be moved without actually moving files
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Dry-run mode flag
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}Running in DRY-RUN mode - no files will be moved${NC}"
    echo ""
fi

# Files that MUST stay in root
EXCLUDE_FILES=(
    "README.md"
    "CLAUDE.md"
    "TESTING.md"
    "LICENSE"
    "CONTRIBUTING.md"
)

# Function to check if git repository exists
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}Error: Not a git repository${NC}"
        exit 1
    fi
}

# Function to extract frontmatter field value
get_frontmatter_field() {
    local file="$1"
    local field="$2"

    # Read frontmatter block (between first two --- lines)
    local in_frontmatter=false
    local value=""

    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if $in_frontmatter; then
                break
            else
                in_frontmatter=true
                continue
            fi
        fi

        if $in_frontmatter && [[ "$line" =~ ^"$field": ]]; then
            value="${line#*: }"
            value="${value# }" # Remove leading space
            break
        fi
    done < "$file"

    echo "$value"
}

# Function to check if file should be excluded
is_excluded() {
    local check_file="$1"
    for excluded_pattern in "${EXCLUDE_FILES[@]}"; do
        if [[ "$check_file" == "$excluded_pattern" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to move file using git mv
move_file() {
    local source="$1"
    local dest_dir="$2"
    local filename=$(basename "$source")

    # Create destination directory if needed
    if [[ ! -d "$dest_dir" ]]; then
        if $DRY_RUN; then
            echo -e "${BLUE}Would create directory: $dest_dir${NC}"
        else
            mkdir -p "$dest_dir"
            echo -e "${GREEN}Created directory: $dest_dir${NC}"
        fi
    fi

    # Move file
    if $DRY_RUN; then
        echo -e "${BLUE}Would move: $source → $dest_dir/$filename${NC}"
    else
        git mv "$source" "$dest_dir/$filename"
        echo -e "${GREEN}Moved: $source → $dest_dir/$filename${NC}"
    fi
}

# Main execution
main() {
    echo "============================================================"
    echo "Documentation Reorganization"
    echo "Repository: $REPO_ROOT"
    echo "============================================================"
    echo ""

    # Verify git repository
    check_git_repo

    # Counters
    local moved=0
    local skipped=0
    local excluded=0

    # Find all markdown files in root directory
    for md_file in *.md; do
        # Skip if no .md files found
        [[ -e "$md_file" ]] || continue

        local filename=$(basename "$md_file")

        # Skip excluded files
        if is_excluded "$filename"; then
            echo -e "${YELLOW}⏭️  Keeping in root (excluded): $filename${NC}"
            excluded=$((excluded + 1))
            continue
        fi

        # Get frontmatter fields
        local file_type=$(get_frontmatter_field "$md_file" "type")
        local lifecycle=$(get_frontmatter_field "$md_file" "lifecycle")

        # Skip if no frontmatter detected
        if [[ -z "$file_type" ]]; then
            echo -e "${YELLOW}⚠️  Skipping (no frontmatter): $filename${NC}"
            skipped=$((skipped + 1))
            continue
        fi

        # Determine destination based on type and lifecycle
        local dest_dir=""

        case "$file_type" in
            session-note)
                dest_dir=".claude/sessions/2025-10-archive"
                ;;
            architecture)
                dest_dir="docs/architecture"
                ;;
            planning)
                # Planning docs stay in specs/ - skip root level planning
                echo -e "${YELLOW}⏭️  Skipping (planning doc - should be in specs/): $filename${NC}"
                skipped=$((skipped + 1))
                continue
                ;;
            guide|reference)
                # Most guides stay in root, but some might move to docs/guides
                # For now, keep guides in root unless they're clearly not essential
                if [[ "$lifecycle" == "ephemeral" ]]; then
                    dest_dir=".claude/sessions/2025-10-archive"
                else
                    echo -e "${YELLOW}⏭️  Keeping in root (guide/reference): $filename${NC}"
                    excluded=$((excluded + 1))
                    continue
                fi
                ;;
            *)
                echo -e "${YELLOW}⏭️  Skipping (unknown type '$file_type'): $filename${NC}"
                skipped=$((skipped + 1))
                continue
                ;;
        esac

        # Move file if destination determined
        if [[ -n "$dest_dir" ]]; then
            move_file "$md_file" "$dest_dir"
            moved=$((moved + 1))
        fi
    done

    # Summary
    echo ""
    echo "============================================================"
    echo "Summary:"
    echo "  Moved: $moved"
    echo "  Kept in root: $excluded"
    echo "  Skipped: $skipped"
    echo "============================================================"
    echo ""

    if $DRY_RUN; then
        echo -e "${YELLOW}Dry-run complete. Run without --dry-run to actually move files.${NC}"
    fi
}

# Run main function
main "$@"
