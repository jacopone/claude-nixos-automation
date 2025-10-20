#!/usr/bin/env python3
"""
Import migration script for T015-T016.

Migrates from:
- Relative imports: from ..analyzers.approval_tracker import ApprovalTracker
- Direct class imports: from claude_automation.analyzers.approval_tracker import ApprovalTracker

To domain-level imports:
- from claude_automation.analyzers import ApprovalTracker
- from claude_automation.generators import PermissionsGenerator
- from claude_automation.validators import ContentValidator
- from claude_automation.scrapers import AnthropicDocsScraper
- from claude_automation.schemas import ProjectType

This improves:
1. Code clarity - imports show domain structure
2. Maintainability - easier to refactor internal structure
3. Consistency - all modules use same import style
"""

import re
from pathlib import Path

# Define the domain structure from __init__.py files
DOMAINS = {
    "analyzers": [
        "ApprovalTracker",
        "ContextOptimizer",
        "ContextUsageTracker",
        "DirectoryAnalyzer",
        "GlobalMCPAnalyzer",
        "InstructionEffectivenessTracker",
        "MCPUsageAnalyzer",
        "MetaLearner",
        "PermissionPatternDetector",
        "ProjectArchetypeDetector",
        "ProjectDetector",
        "SystemAnalyzer",
        "UsageTracker",
        "WorkflowAnalyzer",
        "WorkflowDetector",
    ],
    "generators": [
        "BaseGenerator",
        "DirectoryContextGenerator",
        "IntelligentPermissionsGenerator",
        "LocalContextGenerator",
        "PermissionsGenerator",
        "SlashCommandsGenerator",
        "SystemGenerator",
        "UsageAnalyticsGenerator",
    ],
    "validators": [
        "ContentValidator",
        "PermissionValidator",
    ],
    "scrapers": [
        "AnthropicDocsScraper",
        "GitHubExamplesScraper",
        "ClaudeLogScraper",
    ],
    "schemas": [
        # Core types
        "ProjectType",
        "AnalysisResult",
        "GenerationResult",
        "ValidationResult",
        # Config types
        "AdaptiveSystemConfig",
        "IntelligentPermissionsConfig",
        "MCPAnalysisConfig",
        "MCPUsageAnalyticsConfig",
        "ProjectArchetypeConfig",
        "ContextOptimizerConfig",
        "InstructionTrackerConfig",
        "MetaLearnerConfig",
        "PermissionPatternConfig",
        "SystemAnalyzerConfig",
        "UsageAnalyticsConfig",
        "WorkflowDetectorConfig",
        # Permission types
        "PermissionApprovalEntry",
        "PermissionPattern",
        "PermissionSource",
        "PermissionContext",
        # MCP types
        "MCPServerUsage",
        "MCPRecommendation",
        "MCPAnalysisReport",
        "MCPInstalledServers",
        "MCPServerRecord",
        "MCPToolUsageRecord",
        "MCPServerUtilization",
        "MCPUsageStatistics",
        "MCPServerInfo",
        # Learning types
        "LearningReport",
        "SuggestedPermissionPattern",
        "ContextOptimizationSuggestion",
        "WorkflowPattern",
        "InstructionImprovement",
        "CrossProjectTransfer",
        "MetaLearningMetrics",
        "EffectivenessMetrics",
        "InstructionEffectiveness",
        # Context types
        "ContextUsage",
        "ContextSection",
        "ProjectContext",
        # Workflow types
        "Workflow",
        "WorkflowSequence",
        # Validation types
        "ValidationError",
        "ValidationWarning",
    ],
}

# Build reverse lookup: class/type name -> domain
CLASS_TO_DOMAIN: dict[str, str] = {}
for domain, classes in DOMAINS.items():
    for cls in classes:
        CLASS_TO_DOMAIN[cls] = domain


def analyze_file(file_path: Path) -> dict[str, set[str]]:
    """
    Analyze import statements in a file and categorize them by domain.

    Returns:
        Dict mapping domain -> set of imported classes/types
    """
    imports_by_domain: dict[str, set[str]] = {}

    content = file_path.read_text()

    # Pattern 1: Relative imports (from ..analyzers.approval_tracker import ApprovalTracker)
    relative_pattern = r'from \.\.(analyzers|generators|validators|scrapers|schemas)\.[\w_]+ import ([\w\s,]+)'

    # Pattern 2: Direct class imports (from claude_automation.analyzers.approval_tracker import ApprovalTracker)
    direct_pattern = r'from claude_automation\.(analyzers|generators|validators|scrapers|schemas)\.[\w_]+ import ([\w\s,]+)'

    # Pattern 3: Already migrated (from claude_automation.analyzers import ApprovalTracker)
    migrated_pattern = r'from claude_automation\.(analyzers|generators|validators|scrapers|schemas) import ([\w\s,]+)'

    for pattern in [relative_pattern, direct_pattern]:
        for match in re.finditer(pattern, content):
            domain = match.group(1)
            imports = match.group(2)

            # Parse the imports (handle multi-line and parentheses)
            import_names = [name.strip() for name in imports.split(',')]

            if domain not in imports_by_domain:
                imports_by_domain[domain] = set()
            imports_by_domain[domain].update(import_names)

    return imports_by_domain


def migrate_file(file_path: Path, dry_run: bool = True) -> bool:
    """
    Migrate imports in a file to use domain-level imports.

    Returns:
        True if file was modified, False otherwise
    """
    content = file_path.read_text()
    original_content = content
    lines = content.split('\n')

    # Track what we're importing by domain
    imports_by_domain: dict[str, set[str]] = {}

    # Track which lines to remove (imports we're consolidating)
    lines_to_remove: set[int] = set()

    # Relative imports pattern - can span multiple lines
    for i, line in enumerate(lines):
        # Pattern 1: Relative imports
        match = re.match(r'from \.\.(analyzers|generators|validators|scrapers|schemas)\.[\w_]+ import (.+)', line)
        if match:
            domain = match.group(1)
            imports_str = match.group(2).strip()

            if domain not in imports_by_domain:
                imports_by_domain[domain] = set()

            # Check if this is a multi-line import
            if '(' in imports_str and ')' not in imports_str:
                # Multi-line import starting
                lines_to_remove.add(i)
                # Collect imports from subsequent lines
                j = i + 1
                while j < len(lines) and ')' not in lines[j]:
                    import_line = lines[j].strip()
                    if import_line:
                        # Remove trailing comma
                        import_line = import_line.rstrip(',').strip()
                        if import_line:
                            imports_by_domain[domain].add(import_line)
                    lines_to_remove.add(j)
                    j += 1
                # Add the closing line
                if j < len(lines):
                    last_line = lines[j].strip()
                    if last_line and last_line != ')':
                        last_line = last_line.rstrip(')').strip().rstrip(',').strip()
                        if last_line:
                            imports_by_domain[domain].add(last_line)
                    lines_to_remove.add(j)
            elif '(' in imports_str and ')' in imports_str:
                # Single line with parentheses
                imports_str = imports_str.strip('()').strip()
                names = [n.strip() for n in imports_str.split(',') if n.strip()]
                imports_by_domain[domain].update(names)
                lines_to_remove.add(i)
            else:
                # Simple single-line import
                names = [n.strip() for n in imports_str.split(',') if n.strip()]
                imports_by_domain[domain].update(names)
                lines_to_remove.add(i)

        # Pattern 2: Direct imports
        match = re.match(r'from claude_automation\.(analyzers|generators|validators|scrapers|schemas)\.[\w_]+ import (.+)', line)
        if match:
            domain = match.group(1)
            imports_str = match.group(2).strip()

            if domain not in imports_by_domain:
                imports_by_domain[domain] = set()

            # Check if this is a multi-line import
            if '(' in imports_str and ')' not in imports_str:
                # Multi-line import starting
                lines_to_remove.add(i)
                # Collect imports from subsequent lines
                j = i + 1
                while j < len(lines) and ')' not in lines[j]:
                    import_line = lines[j].strip()
                    if import_line:
                        import_line = import_line.rstrip(',').strip()
                        if import_line:
                            imports_by_domain[domain].add(import_line)
                    lines_to_remove.add(j)
                    j += 1
                # Add the closing line
                if j < len(lines):
                    last_line = lines[j].strip()
                    if last_line and last_line != ')':
                        last_line = last_line.rstrip(')').strip().rstrip(',').strip()
                        if last_line:
                            imports_by_domain[domain].add(last_line)
                    lines_to_remove.add(j)
            elif '(' in imports_str and ')' in imports_str:
                # Single line with parentheses
                imports_str = imports_str.strip('()').strip()
                names = [n.strip() for n in imports_str.split(',') if n.strip()]
                imports_by_domain[domain].update(names)
                lines_to_remove.add(i)
            else:
                # Simple single-line import
                names = [n.strip() for n in imports_str.split(',') if n.strip()]
                imports_by_domain[domain].update(names)
                lines_to_remove.add(i)

    # Remove old import lines
    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
    content = '\n'.join(new_lines)

    # Find where to insert new imports (after module docstring and other imports)
    # Look for the last import statement or after docstring
    import_insertion_point = 0
    new_lines = content.split('\n')

    # Skip module docstring if present
    in_docstring = False
    last_import_line = -1

    for i, line in enumerate(new_lines):
        stripped = line.strip()

        # Track docstring
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                in_docstring = False
                import_insertion_point = i + 1
                continue
        elif in_docstring:
            if '"""' in line or "'''" in line:
                in_docstring = False
                import_insertion_point = i + 1
                continue

        # Track import statements
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import_line = i

        # Found first non-import, non-comment, non-docstring, non-blank line
        elif stripped and not stripped.startswith('#') and last_import_line >= 0:
            # Insert after last import, before this line
            import_insertion_point = last_import_line + 1
            break

    # If we only found imports, insert after them
    if last_import_line >= 0 and import_insertion_point <= last_import_line:
        import_insertion_point = last_import_line + 1

    # Build new import statements
    new_imports = []
    for domain in sorted(imports_by_domain.keys()):
        classes = sorted(imports_by_domain[domain])
        if len(classes) <= 3:
            # Single line
            new_imports.append(f"from claude_automation.{domain} import {', '.join(classes)}")
        else:
            # Multi-line
            new_imports.append(f"from claude_automation.{domain} import (")
            for cls in classes:
                new_imports.append(f"    {cls},")
            new_imports.append(")")

    # Insert new imports
    if new_imports:
        # Find right insertion point considering blank lines
        while import_insertion_point < len(new_lines) and not new_lines[import_insertion_point].strip():
            import_insertion_point += 1

        new_lines.insert(import_insertion_point, '\n'.join(new_imports))
        content = '\n'.join(new_lines)

    # Clean up multiple blank lines
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    if content != original_content:
        if not dry_run:
            file_path.write_text(content)
            print(f"✓ Migrated: {file_path}")
        else:
            print(f"[DRY RUN] Would migrate: {file_path}")
        return True
    else:
        print(f"  Unchanged: {file_path}")
        return False


def main():
    """Main migration script."""
    import sys

    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print()

    # Find all Python files
    base_path = Path(__file__).parent

    patterns = [
        "claude_automation/**/*.py",
        "tests/**/*.py",
    ]

    files_to_migrate = []
    for pattern in patterns:
        files_to_migrate.extend(base_path.glob(pattern))

    # Exclude __init__.py files (they already define the domain exports)
    files_to_migrate = [f for f in files_to_migrate if f.name != "__init__.py"]

    print(f"Found {len(files_to_migrate)} Python files to analyze")
    print()

    modified_count = 0
    for file_path in sorted(files_to_migrate):
        if migrate_file(file_path, dry_run=dry_run):
            modified_count += 1

    print()
    print(f"Summary: {modified_count}/{len(files_to_migrate)} files " +
          ("would be" if dry_run else "were") + " modified")

    if dry_run:
        print()
        print("Run without --dry-run to apply changes:")
        print("  python migrate_imports.py")


if __name__ == "__main__":
    main()
