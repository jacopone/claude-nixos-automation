#!/usr/bin/env python3
"""
Circular Import Detection Script

Detects circular import dependencies in schema modules using AST parsing.
Fails fast with clear error messages per clarification #2.

Usage:
    python scripts/detect_circular_imports.py claude_automation/schemas/
"""

import ast
import sys
from pathlib import Path


class CircularImportError(Exception):
    """Raised when circular import dependency detected."""

    def __init__(self, cycle_path: list[str]):
        self.cycle_path = cycle_path
        self.message = (
            f"\n{'='*80}\n"
            f"❌ CIRCULAR IMPORT DETECTED\n"
            f"{'='*80}\n\n"
            f"Cycle path: {' → '.join(cycle_path)}\n\n"
            f"This violates domain boundary rules. The '{cycle_path[0]}' domain\n"
            f"cannot import from the '{cycle_path[1]}' domain.\n\n"
            f"Resolution:\n"
            f"  1. Move shared types to the 'core' domain\n"
            f"  2. Update imports to reference 'core.py'\n"
            f"  3. Review contracts/schema-domains.md for boundary rules\n\n"
            f"{'='*80}\n"
        )
        super().__init__(self.message)


def extract_imports(file_path: Path) -> list[str]:
    """Extract import statements from a Python file using AST parsing.

    Args:
        file_path: Path to Python file

    Returns:
        List of imported module names (relative to schemas package)
    """
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError as e:
        print(f"⚠️  Warning: Syntax error in {file_path}: {e}")
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Only track imports from claude_automation.schemas
            if node.module and node.module.startswith("claude_automation.schemas"):
                # Extract just the domain name (e.g., "permissions" from "claude_automation.schemas.permissions")
                parts = node.module.split(".")
                if len(parts) > 2:  # Has a domain after "claude_automation.schemas"
                    domain = parts[2]
                    imports.append(domain)

            # Also track relative imports within schemas package
            elif node.module and node.module.startswith("."):
                # Relative import like "from .permissions import X"
                domain = node.module.lstrip(".")
                if domain:  # Not just "from . import X"
                    imports.append(domain)

    return list(set(imports))  # Remove duplicates


def build_dependency_graph(schema_dir: Path) -> dict[str, list[str]]:
    """Build dependency graph from schema modules.

    Args:
        schema_dir: Directory containing schema modules

    Returns:
        Dict mapping module name to list of imported modules
    """
    dependencies = {}

    for py_file in schema_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue  # Skip init file (it imports from all domains)

        module_name = py_file.stem
        imports = extract_imports(py_file)

        # Filter out 'core' from dependencies (core is allowed as foundation)
        imports = [imp for imp in imports if imp != "core"]

        dependencies[module_name] = imports

    return dependencies


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Find circular dependencies in dependency graph using DFS.

    Args:
        graph: Dependency graph (module -> list of imported modules)

    Returns:
        List of cycle paths (each cycle is a list of module names)
    """
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: list[str]) -> None:
        """Depth-first search to detect cycles."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        # Visit all dependencies
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # Cycle detected!
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        rec_stack.remove(node)

    # Run DFS from each unvisited node
    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles


def detect_circular_imports(schema_dir: Path) -> None:
    """Detect circular imports in schema directory.

    Args:
        schema_dir: Directory containing schema modules

    Raises:
        CircularImportError: If circular dependency detected (fail-fast)
    """
    if not schema_dir.exists():
        print(f"✅ Directory {schema_dir} does not exist yet (no validation needed)")
        return

    if not any(schema_dir.glob("*.py")):
        print(f"✅ No Python files in {schema_dir} yet (no validation needed)")
        return

    print(f"🔍 Analyzing schema modules in {schema_dir}...")

    # Build dependency graph
    dependencies = build_dependency_graph(schema_dir)

    print("\n📊 Dependency Graph:")
    for module, imports in sorted(dependencies.items()):
        if imports:
            print(f"  {module} → {', '.join(imports)}")
        else:
            print(f"  {module} → (no dependencies)")

    # Detect cycles
    cycles = find_cycles(dependencies)

    if cycles:
        # FAIL FAST: Halt immediately with clear error
        print(f"\n❌ Found {len(cycles)} circular import(s)!")
        raise CircularImportError(cycles[0])

    print("\n✅ No circular imports detected!")
    print("   All domain boundaries are correct.")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/detect_circular_imports.py <schema_dir>")
        sys.exit(1)

    schema_dir = Path(sys.argv[1])

    try:
        detect_circular_imports(schema_dir)
        sys.exit(0)
    except CircularImportError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
