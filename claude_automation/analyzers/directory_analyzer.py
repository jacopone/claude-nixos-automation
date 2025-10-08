"""
Directory analyzer for detecting purpose and generating context.
"""

import logging
from collections import Counter
from pathlib import Path

from ..schemas import DirectoryContextConfig, DirectoryPurpose

logger = logging.getLogger(__name__)


class DirectoryAnalyzer:
    """Analyzes directories to determine purpose and generate context."""

    # Patterns for directory purpose detection
    SOURCE_PATTERNS = ["src", "lib", "app", "source"]
    TEST_PATTERNS = ["test", "tests", "__tests__", "spec", "specs"]
    DOC_PATTERNS = ["docs", "doc", "documentation", "wiki"]
    CONFIG_PATTERNS = ["config", "configs", "configuration", "settings"]
    MODULE_PATTERNS = ["modules", "plugins", "packages", "components"]
    SCRIPT_PATTERNS = ["scripts", "bin", "tools", "utilities"]
    TEMPLATE_PATTERNS = ["templates", "scaffolds", "boilerplate"]
    DATA_PATTERNS = ["data", "datasets", "fixtures", "samples"]
    BUILD_PATTERNS = ["build", "dist", "target", "out", "output", ".next", ".nuxt"]

    # Protected patterns - do not touch
    PROTECTED_PATTERNS = [
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "target",  # Rust build
        "result",  # Nix build
        ".direnv",
        ".devenv",
    ]

    def __init__(self, directory_path: Path):
        """Initialize analyzer with directory path."""
        self.directory_path = directory_path
        self.directory_name = directory_path.name

    def analyze(self) -> DirectoryContextConfig:
        """
        Analyze directory and build configuration.

        Returns:
            DirectoryContextConfig with analyzed data
        """
        # Detect purpose
        purpose = self._detect_purpose()

        # Count files and subdirectories
        file_count = sum(1 for _ in self.directory_path.glob("*") if _.is_file())
        subdirectory_count = sum(1 for _ in self.directory_path.glob("*") if _.is_dir())

        # Analyze file types
        primary_file_types = self._get_primary_file_types()

        # Identify do-not-touch files
        do_not_touch = self._identify_protected_files()

        # Find key files
        key_files = self._find_key_files()

        # Generate description
        description = self._generate_description(purpose, primary_file_types)

        return DirectoryContextConfig(
            directory_path=self.directory_path,
            directory_name=self.directory_name,
            purpose=purpose,
            file_count=file_count,
            subdirectory_count=subdirectory_count,
            primary_file_types=primary_file_types,
            do_not_touch=do_not_touch,
            key_files=key_files,
            description=description,
        )

    def _detect_purpose(self) -> DirectoryPurpose:
        """Detect directory purpose from name and contents."""
        dir_name_lower = self.directory_name.lower()

        # Check name patterns
        if any(pattern in dir_name_lower for pattern in self.SOURCE_PATTERNS):
            return DirectoryPurpose.SOURCE_CODE

        if any(pattern in dir_name_lower for pattern in self.TEST_PATTERNS):
            return DirectoryPurpose.TESTS

        if any(pattern in dir_name_lower for pattern in self.DOC_PATTERNS):
            return DirectoryPurpose.DOCUMENTATION

        if any(pattern in dir_name_lower for pattern in self.CONFIG_PATTERNS):
            return DirectoryPurpose.CONFIGURATION

        if any(pattern in dir_name_lower for pattern in self.MODULE_PATTERNS):
            return DirectoryPurpose.MODULES

        if any(pattern in dir_name_lower for pattern in self.SCRIPT_PATTERNS):
            return DirectoryPurpose.SCRIPTS

        if any(pattern in dir_name_lower for pattern in self.TEMPLATE_PATTERNS):
            return DirectoryPurpose.TEMPLATES

        if any(pattern in dir_name_lower for pattern in self.DATA_PATTERNS):
            return DirectoryPurpose.DATA

        if any(pattern in dir_name_lower for pattern in self.BUILD_PATTERNS):
            return DirectoryPurpose.BUILD

        # Check contents for clues
        if self._contains_mainly_tests():
            return DirectoryPurpose.TESTS

        if self._contains_mainly_docs():
            return DirectoryPurpose.DOCUMENTATION

        if self._contains_mainly_configs():
            return DirectoryPurpose.CONFIGURATION

        return DirectoryPurpose.UNKNOWN

    def _contains_mainly_tests(self) -> bool:
        """Check if directory contains mainly test files."""
        test_files = sum(
            1
            for f in self.directory_path.glob("*.py")
            if f.name.startswith("test_") or f.name.endswith("_test.py")
        )
        test_files += sum(
            1
            for f in self.directory_path.glob("*.js")
            if ".test." in f.name or ".spec." in f.name
        )
        test_files += sum(
            1
            for f in self.directory_path.glob("*.ts")
            if ".test." in f.name or ".spec." in f.name
        )

        total_files = sum(1 for _ in self.directory_path.glob("*") if _.is_file())
        return total_files > 0 and test_files / total_files > 0.5

    def _contains_mainly_docs(self) -> bool:
        """Check if directory contains mainly documentation."""
        doc_files = sum(
            1
            for f in self.directory_path.glob("*")
            if f.suffix.lower() in [".md", ".rst", ".txt", ".adoc"]
        )
        total_files = sum(1 for _ in self.directory_path.glob("*") if _.is_file())
        return total_files > 0 and doc_files / total_files > 0.7

    def _contains_mainly_configs(self) -> bool:
        """Check if directory contains mainly configuration files."""
        config_files = sum(
            1
            for f in self.directory_path.glob("*")
            if f.suffix.lower()
            in [".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".nix"]
        )
        total_files = sum(1 for _ in self.directory_path.glob("*") if _.is_file())
        return total_files > 0 and config_files / total_files > 0.6

    def _get_primary_file_types(self, top_n: int = 3) -> list[str]:
        """Get the most common file extensions."""
        extensions = []

        for file in self.directory_path.rglob("*"):
            if file.is_file() and file.suffix:
                extensions.append(file.suffix.lower())

        if not extensions:
            return []

        # Count and return top N
        counter = Counter(extensions)
        return [ext for ext, _ in counter.most_common(top_n)]

    def _identify_protected_files(self) -> list[str]:
        """Identify files that should not be modified."""
        protected = []

        for item in self.directory_path.glob("*"):
            if any(pattern in item.name for pattern in self.PROTECTED_PATTERNS):
                protected.append(item.name)

        # Add common lock files
        lock_files = [
            "package-lock.json",
            "Cargo.lock",
            "poetry.lock",
            "Pipfile.lock",
            "flake.lock",
        ]
        for lock_file in lock_files:
            if (self.directory_path / lock_file).exists():
                protected.append(lock_file)

        return protected

    def _find_key_files(self) -> list[str]:
        """Identify important/key files in the directory."""
        key_files = []

        # Common important files
        important_patterns = [
            "README.md",
            "README.rst",
            "README.txt",
            "INDEX.md",
            "OVERVIEW.md",
            "__init__.py",
            "mod.rs",
            "index.js",
            "index.ts",
            "main.py",
            "main.rs",
            "main.js",
            "app.py",
            "default.nix",
            "flake.nix",
        ]

        for pattern in important_patterns:
            if (self.directory_path / pattern).exists():
                key_files.append(pattern)

        return key_files

    def _generate_description(
        self, purpose: DirectoryPurpose, file_types: list[str]
    ) -> str:
        """Generate a brief description of the directory."""
        purpose_descriptions = {
            DirectoryPurpose.SOURCE_CODE: f"Source code directory containing {', '.join(file_types) if file_types else 'code'} files",
            DirectoryPurpose.TESTS: f"Test suite directory with {', '.join(file_types) if file_types else 'test'} files",
            DirectoryPurpose.DOCUMENTATION: "Documentation directory with project guides and references",
            DirectoryPurpose.CONFIGURATION: "Configuration directory containing project settings and configs",
            DirectoryPurpose.MODULES: "Modular components directory with reusable functionality",
            DirectoryPurpose.SCRIPTS: "Utility scripts and automation tools directory",
            DirectoryPurpose.TEMPLATES: "Template files for code generation and scaffolding",
            DirectoryPurpose.DATA: "Data files directory for fixtures, samples, or datasets",
            DirectoryPurpose.BUILD: "Build artifacts directory (auto-generated, do not edit)",
            DirectoryPurpose.UNKNOWN: f"Directory containing {', '.join(file_types) if file_types else 'various'} files",
        }

        return purpose_descriptions.get(purpose, "Directory")
