"""
Unit tests for ProjectArchetypeDetector (Phase 8).

Tests archetype detection and pattern transfer across projects.
"""

import tempfile
from pathlib import Path

import pytest

from claude_automation.analyzers.project_archetype_detector import (
    ProjectArchetypeDetector,
)


@pytest.fixture
def temp_projects_dir():
    """Create temporary projects directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def detector(temp_projects_dir):
    """Create ProjectArchetypeDetector instance."""
    return ProjectArchetypeDetector(base_path=temp_projects_dir)


def create_project_structure(base_path: Path, name: str, archetype: str):
    """Helper to create project structure for testing."""
    project_dir = base_path / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create archetype-specific files
    if archetype == "python-pytest":
        (project_dir / "pyproject.toml").write_text("[tool.pytest]\n")
        (project_dir / "tests").mkdir(exist_ok=True)
        (project_dir / "tests" / "test_example.py").write_text("def test_foo(): pass")
    elif archetype == "typescript-vitest":
        (project_dir / "package.json").write_text('{"devDependencies": {"vitest": "1.0.0"}}')
        (project_dir / "vitest.config.ts").write_text("export default {}")
    elif archetype == "rust-cargo":
        (project_dir / "Cargo.toml").write_text("[package]\nname = 'test'\n")
        (project_dir / "src").mkdir(exist_ok=True)
        (project_dir / "src" / "main.rs").write_text("fn main() {}")

    # Create .claude directory with settings
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "settings.local.json").write_text('{"autoApprove": []}')

    return project_dir


def test_archetype_detection_python_pytest(detector, temp_projects_dir):
    """Test T090: Detect Python/pytest archetype."""
    # Create Python/pytest project
    project = create_project_structure(temp_projects_dir, "test-python", "python-pytest")

    # Detect archetype
    archetype = detector.detect_archetype(project)

    assert archetype is not None
    assert archetype.name == "python-pytest"
    assert "pytest" in archetype.test_framework.lower()


def test_archetype_detection_typescript_vitest(detector, temp_projects_dir):
    """Test T090: Detect TypeScript/vitest archetype."""
    # Create TypeScript/vitest project
    project = create_project_structure(
        temp_projects_dir, "test-typescript", "typescript-vitest"
    )

    # Detect archetype
    archetype = detector.detect_archetype(project)

    assert archetype is not None
    assert archetype.name == "typescript-vitest"
    assert "vitest" in archetype.test_framework.lower()


def test_archetype_detection_rust_cargo(detector, temp_projects_dir):
    """Test T090: Detect Rust/cargo archetype."""
    # Create Rust/cargo project
    project = create_project_structure(temp_projects_dir, "test-rust", "rust-cargo")

    # Detect archetype
    archetype = detector.detect_archetype(project)

    assert archetype is not None
    assert archetype.name == "rust-cargo"
    assert "cargo" in archetype.build_system.lower()


def test_archetype_detection_unknown_project(detector, temp_projects_dir):
    """Test T090: Return None for unknown project types."""
    # Create minimal project with no recognizable structure
    project_dir = temp_projects_dir / "unknown-project"
    project_dir.mkdir()

    archetype = detector.detect_archetype(project_dir)

    # Should return None or generic archetype
    assert archetype is None or archetype.name == "generic"


def test_pattern_transfer_permissions(detector, temp_projects_dir):
    """Test T091: Transfer permission patterns between similar projects."""
    # Create source project with permissions
    source = create_project_structure(temp_projects_dir, "source", "python-pytest")
    source_settings = source / ".claude" / "settings.local.json"
    source_settings.write_text(
        '{"autoApprove": ["Bash(pytest:*)"]}'
    )

    # Create target project
    target = create_project_structure(temp_projects_dir, "target", "python-pytest")

    # Build knowledge base
    detector.build_knowledge_base([source])

    # Find transfer opportunities
    opportunities = detector.find_transfer_opportunities(target)

    # Should find permission pattern to transfer
    assert len(opportunities) > 0
    has_pytest_permission = any(
        "pytest" in str(opp.pattern).lower() for opp in opportunities
    )
    assert has_pytest_permission


def test_pattern_transfer_mcp_servers(detector, temp_projects_dir):
    """Test T091: Transfer MCP server configurations."""
    # Create source project with MCP config
    source = create_project_structure(temp_projects_dir, "source", "python-pytest")
    mcp_config = source / ".claude" / "mcp.json"
    mcp_config.write_text(
        '{"mcpServers": {"filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"]}}}'
    )

    # Create target project
    target = create_project_structure(temp_projects_dir, "target", "python-pytest")

    # Build knowledge base
    detector.build_knowledge_base([source])

    # Find transfer opportunities
    opportunities = detector.find_transfer_opportunities(target)

    # Should find MCP server to transfer
    mcp_opportunities = [
        opp for opp in opportunities if opp.pattern_type == "mcp_server"
    ]
    assert len(mcp_opportunities) > 0


def test_new_project_pattern_application(detector, temp_projects_dir):
    """Test T092: Apply patterns to new project based on archetype."""
    # Create multiple existing projects with patterns
    for i in range(3):
        project = create_project_structure(
            temp_projects_dir, f"existing-{i}", "python-pytest"
        )
        settings = project / ".claude" / "settings.local.json"
        settings.write_text('{"autoApprove": ["Bash(pytest:*)", "Bash(ruff:*)"]}')

    # Build knowledge base
    detector.build_knowledge_base(list(temp_projects_dir.iterdir()))

    # Create new project
    new_project = create_project_structure(temp_projects_dir, "new-project", "python-pytest")

    # Find and apply patterns
    opportunities = detector.find_transfer_opportunities(new_project)

    # Should suggest pytest and ruff patterns
    assert len(opportunities) >= 2

    # Apply first pattern
    applied = detector.transfer_pattern(new_project, opportunities[0])

    assert applied is True


def test_cross_archetype_no_transfer(detector, temp_projects_dir):
    """Test that patterns don't transfer across incompatible archetypes."""
    # Create Python project with pytest
    python_project = create_project_structure(temp_projects_dir, "python", "python-pytest")
    python_settings = python_project / ".claude" / "settings.local.json"
    python_settings.write_text('{"autoApprove": ["Bash(pytest:*)"]}')

    # Create Rust project
    rust_project = create_project_structure(temp_projects_dir, "rust", "rust-cargo")

    # Build knowledge base
    detector.build_knowledge_base([python_project])

    # Find transfer opportunities for Rust project
    opportunities = detector.find_transfer_opportunities(rust_project)

    # Should not suggest pytest for Rust project
    pytest_opportunities = [
        opp for opp in opportunities if "pytest" in str(opp.pattern).lower()
    ]
    assert len(pytest_opportunities) == 0


def test_build_knowledge_base(detector, temp_projects_dir):
    """Test building knowledge base from multiple projects."""
    # Create multiple projects
    projects = []
    for i in range(5):
        project = create_project_structure(
            temp_projects_dir, f"project-{i}", "python-pytest"
        )
        projects.append(project)

    # Build knowledge base
    kb = detector.build_knowledge_base(projects)

    # Should have knowledge for python-pytest archetype
    assert "python-pytest" in kb
    assert kb["python-pytest"]["count"] == 5


def test_archetype_characteristics(detector, temp_projects_dir):
    """Test extraction of archetype characteristics."""
    project = create_project_structure(temp_projects_dir, "test", "python-pytest")

    archetype = detector.detect_archetype(project)

    # Should have characteristic fields
    assert hasattr(archetype, "name")
    assert hasattr(archetype, "test_framework")
    assert hasattr(archetype, "build_system")
    assert hasattr(archetype, "common_tools")


def test_find_similar_projects(detector, temp_projects_dir):
    """Test finding similar projects by archetype."""
    # Create projects with different archetypes
    create_project_structure(temp_projects_dir, "py1", "python-pytest")
    create_project_structure(temp_projects_dir, "py2", "python-pytest")
    create_project_structure(temp_projects_dir, "ts1", "typescript-vitest")

    # Build knowledge base
    detector.build_knowledge_base(list(temp_projects_dir.iterdir()))

    # Create new Python project
    new_py = create_project_structure(temp_projects_dir, "new-py", "python-pytest")

    # Find similar projects
    similar = detector.find_similar_projects(new_py)

    # Should find 2 Python projects, not TypeScript
    assert len(similar) == 2
    assert all("py" in str(p) for p in similar)
