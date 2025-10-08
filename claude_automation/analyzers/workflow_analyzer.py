"""
Workflow analyzer for detecting common development workflows.
Analyzes git history and project structure to suggest slash commands.
"""

import logging
import subprocess
from collections import Counter
from pathlib import Path

from ..schemas import (
    CommandCategory,
    ProjectType,
    SlashCommand,
    SlashCommandsConfig,
)

logger = logging.getLogger(__name__)


class WorkflowAnalyzer:
    """Analyzes project workflows to generate slash commands."""

    def __init__(self, project_path: Path, project_type: ProjectType):
        """Initialize analyzer."""
        self.project_path = project_path
        self.project_type = project_type

    def analyze(self, commands_dir: Path) -> SlashCommandsConfig:
        """
        Analyze workflows and build slash commands configuration.

        Args:
            commands_dir: Directory for slash commands (~/.claude/commands)

        Returns:
            SlashCommandsConfig with generated commands
        """
        # Analyze git history for common workflows
        common_workflows = self._analyze_git_workflows()

        # Generate base commands for project type
        commands = self._generate_base_commands()

        # Add workflow-specific commands
        workflow_commands = self._generate_workflow_commands(common_workflows)
        commands.extend(workflow_commands)

        return SlashCommandsConfig(
            commands_dir=commands_dir,
            project_type=self.project_type,
            commands=commands,
            common_workflows=common_workflows[:10],  # Top 10
        )

    def _analyze_git_workflows(self) -> list[str]:
        """Analyze git commit messages for common workflows."""
        workflows = []

        try:
            # Get recent commit messages
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--format=%s",
                    "--no-merges",
                    "-n",
                    "100",
                ],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                messages = result.stdout.strip().split("\n")

                # Extract workflow patterns
                for msg in messages:
                    msg_lower = msg.lower()

                    # Common patterns
                    if "fix" in msg_lower or "bug" in msg_lower:
                        workflows.append("bug fix")
                    if "test" in msg_lower:
                        workflows.append("testing")
                    if "refactor" in msg_lower:
                        workflows.append("refactoring")
                    if "doc" in msg_lower or "readme" in msg_lower:
                        workflows.append("documentation")
                    if "feat" in msg_lower or "add" in msg_lower:
                        workflows.append("feature development")
                    if "perf" in msg_lower or "optim" in msg_lower:
                        workflows.append("performance optimization")
                    if "ci" in msg_lower or "pipeline" in msg_lower:
                        workflows.append("CI/CD")
                    if "deploy" in msg_lower or "release" in msg_lower:
                        workflows.append("deployment")

                # Count frequencies
                counter = Counter(workflows)
                return [workflow for workflow, _ in counter.most_common(10)]

        except Exception as e:
            logger.warning(f"Failed to analyze git workflows: {e}")

        return []

    def _generate_base_commands(self) -> list[SlashCommand]:
        """Generate base commands for all project types."""
        commands = [
            SlashCommand(
                name="rebuild-check",
                description="Check if rebuild is needed and validate config",
                category=CommandCategory.BUILD,
                prompt="Check if a system/project rebuild is needed. Run appropriate validation commands (nix flake check, cargo check, npm run build --dry-run, etc.) and report any issues.",
                requires_args=False,
                example_usage="/rebuild-check",
            ),
            SlashCommand(
                name="explain-file",
                description="Explain what a file does and its purpose",
                category=CommandCategory.DOCUMENTATION,
                prompt="Read the file $ARGUMENTS and provide a clear explanation of:\n1. What this file does\n2. Its role in the project\n3. Key functions/classes/exports\n4. Dependencies and relationships with other files",
                requires_args=True,
                example_usage="/explain-file src/main.py",
            ),
            SlashCommand(
                name="quick-fix",
                description="Quick fix for common issues",
                category=CommandCategory.DEVELOPMENT,
                prompt="Analyze the described issue: $ARGUMENTS\n\nProvide a quick fix if it's a common problem (typo, missing import, syntax error, etc.). If it's complex, suggest debugging steps instead.",
                requires_args=True,
                example_usage="/quick-fix import error in module",
            ),
            SlashCommand(
                name="review-changes",
                description="Review uncommitted changes",
                category=CommandCategory.GIT,
                prompt="Run git diff to see uncommitted changes. Review them for:\n1. Code quality issues\n2. Potential bugs\n3. Missing tests\n4. Documentation needs\n5. Suggest improvements",
                requires_args=False,
                example_usage="/review-changes",
            ),
        ]

        # Add project-type specific commands
        if self.project_type == ProjectType.PYTHON:
            commands.extend(
                [
                    SlashCommand(
                        name="run-tests",
                        description="Run Python tests with pytest",
                        category=CommandCategory.TESTING,
                        prompt="Run pytest with appropriate options. If $ARGUMENTS is provided, run specific test: pytest $ARGUMENTS. Otherwise run all tests with: pytest -v",
                        requires_args=False,
                        example_usage="/run-tests tests/test_api.py",
                    ),
                    SlashCommand(
                        name="check-quality",
                        description="Run Python quality checks (ruff, black)",
                        category=CommandCategory.DEVELOPMENT,
                        prompt="Run quality checks:\n1. ruff check .\n2. ruff format --check .\n3. Report any issues found",
                        requires_args=False,
                        example_usage="/check-quality",
                    ),
                ]
            )

        elif self.project_type == ProjectType.NODEJS:
            commands.extend(
                [
                    SlashCommand(
                        name="run-tests",
                        description="Run Node.js tests",
                        category=CommandCategory.TESTING,
                        prompt="Run npm test or jest. If $ARGUMENTS provided, run specific test file.",
                        requires_args=False,
                        example_usage="/run-tests api.test.js",
                    ),
                    SlashCommand(
                        name="check-quality",
                        description="Run ESLint and Prettier checks",
                        category=CommandCategory.DEVELOPMENT,
                        prompt="Run quality checks:\n1. npm run lint (or eslint .)\n2. npm run format:check (or prettier --check .)\n3. Report any issues",
                        requires_args=False,
                        example_usage="/check-quality",
                    ),
                ]
            )

        elif self.project_type == ProjectType.RUST:
            commands.extend(
                [
                    SlashCommand(
                        name="run-tests",
                        description="Run Rust tests with cargo",
                        category=CommandCategory.TESTING,
                        prompt="Run cargo test. If $ARGUMENTS provided, run specific test: cargo test $ARGUMENTS",
                        requires_args=False,
                        example_usage="/run-tests integration_tests",
                    ),
                    SlashCommand(
                        name="check-quality",
                        description="Run Rust quality checks (clippy, fmt)",
                        category=CommandCategory.DEVELOPMENT,
                        prompt="Run quality checks:\n1. cargo clippy -- -D warnings\n2. cargo fmt --check\n3. Report any issues",
                        requires_args=False,
                        example_usage="/check-quality",
                    ),
                ]
            )

        elif self.project_type == ProjectType.NIXOS:
            commands.extend(
                [
                    SlashCommand(
                        name="nix-check",
                        description="Validate NixOS configuration",
                        category=CommandCategory.BUILD,
                        prompt="Run nix flake check to validate the configuration. Report any errors or warnings.",
                        requires_args=False,
                        example_usage="/nix-check",
                    ),
                    SlashCommand(
                        name="nix-search",
                        description="Search for a Nix package",
                        category=CommandCategory.SYSTEM,
                        prompt="Search for package: nix search nixpkgs $ARGUMENTS. Show top 5 results with descriptions.",
                        requires_args=True,
                        example_usage="/nix-search python3",
                    ),
                ]
            )

        return commands

    def _generate_workflow_commands(self, workflows: list[str]) -> list[SlashCommand]:
        """Generate commands based on detected workflows."""
        commands = []

        # Map workflows to commands
        if "bug fix" in workflows:
            commands.append(
                SlashCommand(
                    name="debug-helper",
                    description="Help debug an issue",
                    category=CommandCategory.DEVELOPMENT,
                    prompt="Help debug this issue: $ARGUMENTS\n\nProvide:\n1. Likely causes\n2. Debugging steps\n3. Tools to use\n4. Common solutions",
                    requires_args=True,
                    example_usage="/debug-helper login not working",
                )
            )

        if "documentation" in workflows:
            commands.append(
                SlashCommand(
                    name="doc-update",
                    description="Update documentation for changes",
                    category=CommandCategory.DOCUMENTATION,
                    prompt="Review recent changes (git diff) and suggest documentation updates needed for: $ARGUMENTS",
                    requires_args=True,
                    example_usage="/doc-update API changes",
                )
            )

        if "refactoring" in workflows:
            commands.append(
                SlashCommand(
                    name="refactor-suggest",
                    description="Suggest refactoring improvements",
                    category=CommandCategory.DEVELOPMENT,
                    prompt="Analyze $ARGUMENTS and suggest refactoring improvements:\n1. Code structure\n2. Naming conventions\n3. DRY violations\n4. Performance optimizations",
                    requires_args=True,
                    example_usage="/refactor-suggest src/utils.py",
                )
            )

        return commands
