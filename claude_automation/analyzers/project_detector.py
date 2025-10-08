"""
Project type detection analyzer for permissions optimization.
Detects project type by examining files and directory structure.
"""

import logging
from pathlib import Path

from ..schemas import ProjectType

logger = logging.getLogger(__name__)


class ProjectDetector:
    """Detects project type by analyzing files and structure."""

    # File markers for project types
    PYTHON_MARKERS = [
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "poetry.lock",
        "Pipfile",
        "setup.cfg",
    ]

    NODEJS_MARKERS = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "tsconfig.json",
    ]

    RUST_MARKERS = [
        "Cargo.toml",
        "Cargo.lock",
    ]

    NIXOS_MARKERS = [
        "flake.nix",
        "configuration.nix",
        "hardware-configuration.nix",
    ]

    def __init__(self, project_path: Path):
        """Initialize detector with project path."""
        self.project_path = project_path

    def detect(self) -> ProjectType:
        """
        Detect project type by examining files.

        Returns:
            ProjectType enum value
        """
        if not self.project_path.exists() or not self.project_path.is_dir():
            logger.warning(f"Project path does not exist: {self.project_path}")
            return ProjectType.UNKNOWN

        detected_types = []

        # Check for each project type
        if self._has_markers(self.PYTHON_MARKERS):
            detected_types.append(ProjectType.PYTHON)

        if self._has_markers(self.NODEJS_MARKERS):
            detected_types.append(ProjectType.NODEJS)

        if self._has_markers(self.RUST_MARKERS):
            detected_types.append(ProjectType.RUST)

        if self._has_markers(self.NIXOS_MARKERS):
            detected_types.append(ProjectType.NIXOS)

        # Return based on findings
        if len(detected_types) == 0:
            return ProjectType.UNKNOWN
        elif len(detected_types) == 1:
            logger.info(f"Detected project type: {detected_types[0].value}")
            return detected_types[0]
        else:
            logger.info(
                f"Detected multiple types: {[t.value for t in detected_types]}, using MIXED"
            )
            return ProjectType.MIXED

    def _has_markers(self, markers: list[str]) -> bool:
        """Check if any marker file exists in project root."""
        return any((self.project_path / marker).exists() for marker in markers)

    def detect_quality_tools(self) -> list[str]:
        """
        Detect available quality tools in project.

        Returns:
            List of quality tool names found
        """
        tools = []

        # Python tools
        if self._check_python_tool("pytest"):
            tools.append("pytest")
        if self._check_python_tool("ruff"):
            tools.append("ruff")
        if self._check_python_tool("black"):
            tools.append("black")
        if self._check_python_tool("lizard"):
            tools.append("lizard")
        if self._check_python_tool("radon"):
            tools.append("radon")

        # Node.js tools
        if self._check_nodejs_tool("jest"):
            tools.append("jest")
        if self._check_nodejs_tool("eslint"):
            tools.append("eslint")
        if self._check_nodejs_tool("prettier"):
            tools.append("prettier")
        if self._check_nodejs_tool("typescript"):
            tools.append("tsc")
        if self._check_nodejs_tool("jscpd"):
            tools.append("jscpd")

        # Rust tools
        if self._has_markers(self.RUST_MARKERS):
            tools.append("clippy")
            tools.append("rustfmt")

        # Nix tools
        if self._has_markers(self.NIXOS_MARKERS):
            tools.append("nixpkgs-fmt")
            tools.append("alejandra")
            tools.append("statix")
            if (self.project_path / "devenv.nix").exists():
                tools.append("devenv")

        return tools

    def detect_package_managers(self) -> list[str]:
        """
        Detect package managers used in project.

        Returns:
            List of package manager names
        """
        managers = []

        # Python
        if (self.project_path / "pyproject.toml").exists():
            # Check if it's poetry or uv
            try:
                content = (self.project_path / "pyproject.toml").read_text()
                if "[tool.poetry]" in content:
                    managers.append("poetry")
                if "[tool.uv]" in content or "uv" in content:
                    managers.append("uv")
            except Exception:
                pass

        if (self.project_path / "requirements.txt").exists():
            managers.append("pip")

        # Node.js
        if (self.project_path / "package-lock.json").exists():
            managers.append("npm")
        if (self.project_path / "yarn.lock").exists():
            managers.append("yarn")
        if (self.project_path / "pnpm-lock.yaml").exists():
            managers.append("pnpm")

        # Rust
        if (self.project_path / "Cargo.toml").exists():
            managers.append("cargo")

        return managers

    def detect_sensitive_paths(self) -> list[str]:
        """
        Identify sensitive paths that should be protected.

        Returns:
            List of sensitive path patterns
        """
        sensitive = []

        # Environment files
        if (self.project_path / ".env").exists():
            sensitive.append(str(self.project_path / ".env"))
        if (self.project_path / ".env.local").exists():
            sensitive.append(str(self.project_path / ".env.local"))

        # Credentials directories
        for cred_dir in ["credentials", "secrets", ".secrets", "certs"]:
            if (self.project_path / cred_dir).exists():
                sensitive.append(str(self.project_path / cred_dir))

        # SSH keys
        if (self.project_path / ".ssh").exists():
            sensitive.append(str(self.project_path / ".ssh"))

        # API keys and tokens
        for key_file in ["api_keys.json", "tokens.json", ".secrets.json"]:
            if (self.project_path / key_file).exists():
                sensitive.append(str(self.project_path / key_file))

        return sensitive

    def has_tests(self) -> bool:
        """
        Check if project has a test directory or test files.

        Returns:
            True if tests are found
        """
        # Common test directories
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (self.project_path / test_dir).exists():
                return True

        # Python test files in src
        if (self.project_path / "src").exists():
            src_path = self.project_path / "src"
            if any(src_path.rglob("test_*.py")) or any(src_path.rglob("*_test.py")):
                return True

        # Node.js test files
        if any(self.project_path.glob("*.test.js")) or any(
            self.project_path.glob("*.test.ts")
        ):
            return True

        # Rust test files (usually integrated in src/)
        if (self.project_path / "src").exists() and self._has_markers(
            self.RUST_MARKERS
        ):
            return True  # Rust has tests integrated in source files

        return False

    def _check_python_tool(self, tool_name: str) -> bool:
        """Check if Python tool is configured in pyproject.toml."""
        pyproject = self.project_path / "pyproject.toml"
        if not pyproject.exists():
            return False

        try:
            content = pyproject.read_text()
            return f"[tool.{tool_name}]" in content or tool_name in content
        except Exception:
            return False

    def _check_nodejs_tool(self, tool_name: str) -> bool:
        """Check if Node.js tool is in package.json dependencies."""
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return False

        try:
            import json

            data = json.loads(package_json.read_text())
            return (
                tool_name in data.get("dependencies", {})
                or tool_name in data.get("devDependencies", {})
                or tool_name in data.get("scripts", {}).values()
            )
        except Exception:
            return False
