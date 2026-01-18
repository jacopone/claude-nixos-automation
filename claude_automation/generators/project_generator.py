"""
Project-level CLAUDE.md generator using templates with auto-detection.

Enhanced: Detects project type from package.json, devenv.nix, flake.nix,
and git history to select appropriate templates and populate context.
"""

import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..schemas import GenerationResult
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class ProjectGenerator(BaseGenerator):
    """Generates project-level CLAUDE.md files with auto-detection.

    The generator:
    1. Detects project type (MCP server, Nix package, Python, TypeScript, etc.)
    2. Extracts context from package.json, devenv.nix, flake.nix
    3. Analyzes recent git history for activity patterns
    4. Selects appropriate template based on project type
    5. Preserves user memory content between regenerations
    """

    # Project type detection priority
    PROJECT_TYPES = ["mcp_server", "nix_package", "python_devenv", "typescript", "generic"]

    def __init__(self, template_dir: Path = None):
        super().__init__(template_dir)

    def generate(
        self, output_path: Path, config_dir: Path = None, auto_detect: bool = True
    ) -> GenerationResult:
        """Generate project-level CLAUDE.md file.

        Args:
            output_path: Where to write the CLAUDE.md file
            config_dir: Project directory to analyze (defaults to repo root)
            auto_detect: Whether to auto-detect project type and context
        """
        if config_dir is None:
            config_dir = self._get_repo_root()

        try:
            # Extract existing user memory content before regeneration
            user_memory = self._extract_user_memory(output_path)

            # Auto-detect project context if enabled
            if auto_detect:
                context = self.detect_project_context(config_dir)
                template_name = self._select_template(context)
                logger.info(f"Auto-detected project type: {context.get('project_type', 'generic')}")
            else:
                context = {"timestamp": datetime.now()}
                template_name = "project-claude.j2"

            # Render template
            content = self.render_template(template_name, context)

            # Inject preserved user memory content
            if user_memory:
                content = self._inject_user_memory(content, user_memory)
                logger.info("Preserved user memory content during regeneration")

            # Write file
            result = self.write_file(output_path, content)

            if result.success:
                logger.info(f"Generated project CLAUDE.md using {template_name}")
                result.stats["template_used"] = template_name
                result.stats["project_type"] = context.get("project_type", "generic")

            return result

        except Exception as e:
            error_msg = f"Project generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _extract_user_memory(self, file_path: Path) -> str:
        """Extract user memory content from existing CLAUDE.md file.

        Returns:
            str: Content between USER_MEMORY_START and USER_MEMORY_END markers,
                 or empty string if not found.
        """
        if not file_path.exists():
            return ""

        try:
            content = file_path.read_text(encoding="utf-8")

            # Find markers
            start_marker = "<!-- USER_MEMORY_START -->"
            end_marker = "<!-- USER_MEMORY_END -->"

            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)

            if start_idx == -1 or end_idx == -1:
                return ""

            # Extract content between markers (including the markers themselves)
            extracted = content[start_idx : end_idx + len(end_marker)]

            return extracted

        except Exception as e:
            logger.warning(f"Failed to extract user memory: {e}")
            return ""

    def _inject_user_memory(self, rendered_content: str, user_memory: str) -> str:
        """Inject preserved user memory into rendered template.

        Args:
            rendered_content: Newly rendered template content
            user_memory: Preserved user memory content (with markers)

        Returns:
            str: Content with user memory injected
        """
        if not user_memory:
            return rendered_content

        # Find the markers in the new content
        start_marker = "<!-- USER_MEMORY_START -->"
        end_marker = "<!-- USER_MEMORY_END -->"

        start_idx = rendered_content.find(start_marker)
        end_idx = rendered_content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            logger.warning("Could not find memory markers in rendered content")
            return rendered_content

        # Replace the section between markers with preserved content
        before = rendered_content[:start_idx]
        after = rendered_content[end_idx + len(end_marker) :]

        return before + user_memory + after

    def get_summary_stats(self, config_dir: Path = None) -> dict:
        """Get summary statistics."""
        if config_dir is None:
            config_dir = self._get_repo_root()

        context = self.detect_project_context(config_dir)

        # Count packages (from various sources)
        package_count = 0
        if context.get("npm"):
            package_count += len(context["npm"].get("dependencies", []))
            package_count += len(context["npm"].get("dev_dependencies", []))

        # Count fish abbreviations if this is a NixOS config
        fish_abbreviation_count = 0
        fish_files = list(config_dir.glob("**/fish*.nix")) + list(
            config_dir.glob("**/shell/*.nix")
        )
        for f in fish_files:
            try:
                content = f.read_text(encoding="utf-8")
                # Count shellAbbrs entries
                abbrs = re.findall(r"shellAbbrs\s*=\s*\{([^}]+)\}", content, re.DOTALL)
                for abbr_block in abbrs:
                    fish_abbreviation_count += len(re.findall(r"(\w+)\s*=", abbr_block))
            except Exception:
                pass

        # Git status summary
        git_context = context.get("git", {})
        git_status = "active" if git_context.get("commit_count", 0) > 0 else "empty"

        return {
            "project_type": context.get("project_type", "generic"),
            "detected_context": bool(context.get("npm") or context.get("devenv") or context.get("flake")),
            "template": self._select_template(context),
            "timestamp": datetime.now().isoformat(),
            # Expected by CLI
            "package_count": package_count,
            "fish_abbreviation_count": fish_abbreviation_count,
            "git_status": git_status,
        }

    # =========================================================================
    # Auto-Detection Methods
    # =========================================================================

    def detect_project_context(self, project_path: Path) -> dict[str, Any]:
        """Detect project type and extract context from project files.

        Analyzes:
        - package.json (npm/Node projects)
        - devenv.nix (devenv projects)
        - flake.nix (Nix packages)
        - pyproject.toml (Python projects)
        - git history (recent activity)

        Returns:
            dict with detected context and project_type classification
        """
        context = {
            "timestamp": datetime.now(),
            "project_name": project_path.name,
            "project_path": str(project_path),
        }

        # Detect from various sources
        npm_context = self._detect_npm_context(project_path)
        if npm_context:
            context["npm"] = npm_context

        devenv_context = self._detect_devenv_context(project_path)
        if devenv_context:
            context["devenv"] = devenv_context

        flake_context = self._detect_flake_context(project_path)
        if flake_context:
            context["flake"] = flake_context

        python_context = self._detect_python_context(project_path)
        if python_context:
            context["python"] = python_context

        git_context = self._detect_git_context(project_path)
        if git_context:
            context["git"] = git_context

        # Classify project type based on detected context
        context["project_type"] = self._classify_project_type(context)

        return context

    def _detect_npm_context(self, project_path: Path) -> dict[str, Any] | None:
        """Extract context from package.json if present."""
        pkg_json = project_path / "package.json"
        if not pkg_json.exists():
            return None

        try:
            with open(pkg_json, encoding="utf-8") as f:
                pkg = json.load(f)

            context = {
                "name": pkg.get("name", ""),
                "description": pkg.get("description", ""),
                "version": pkg.get("version", ""),
                "scripts": list(pkg.get("scripts", {}).keys()),
                "dependencies": list(pkg.get("dependencies", {}).keys())[:15],
                "dev_dependencies": list(pkg.get("devDependencies", {}).keys())[:10],
            }

            # Check for MCP SDK
            all_deps = list(pkg.get("dependencies", {}).keys()) + list(
                pkg.get("devDependencies", {}).keys()
            )
            context["is_mcp_server"] = "@modelcontextprotocol/sdk" in all_deps
            context["is_typescript"] = "typescript" in all_deps

            return context

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to parse package.json: {e}")
            return None

    def _detect_devenv_context(self, project_path: Path) -> dict[str, Any] | None:
        """Extract context from devenv.nix if present."""
        devenv_nix = project_path / "devenv.nix"
        if not devenv_nix.exists():
            return None

        try:
            content = devenv_nix.read_text(encoding="utf-8")

            context = {
                "has_devenv": True,
                "languages": [],
                "scripts": [],
                "services": [],
            }

            # Detect languages (e.g., languages.python.enable = true)
            lang_pattern = r"languages\.(\w+)\.enable\s*=\s*true"
            context["languages"] = re.findall(lang_pattern, content)

            # Detect scripts (e.g., scripts.foo.exec = "...")
            script_pattern = r"scripts\.(\w+)\s*[.=]"
            context["scripts"] = list(set(re.findall(script_pattern, content)))

            # Detect services (e.g., services.postgres.enable = true)
            service_pattern = r"services\.(\w+)\.enable\s*=\s*true"
            context["services"] = re.findall(service_pattern, content)

            return context

        except OSError as e:
            logger.warning(f"Failed to read devenv.nix: {e}")
            return None

    def _detect_flake_context(self, project_path: Path) -> dict[str, Any] | None:
        """Extract context from flake.nix if present."""
        flake_nix = project_path / "flake.nix"
        if not flake_nix.exists():
            return None

        try:
            content = flake_nix.read_text(encoding="utf-8")

            context = {
                "has_flake": True,
                "description": "",
                "has_packages": False,
                "has_overlay": False,
                "has_devshell": False,
            }

            # Extract description
            desc_match = re.search(r'description\s*=\s*"([^"]+)"', content)
            if desc_match:
                context["description"] = desc_match.group(1)

            # Check for outputs
            context["has_packages"] = "packages" in content or "packages." in content
            context["has_overlay"] = "overlays" in content or "overlay" in content
            context["has_devshell"] = "devShells" in content or "devShell" in content

            # Check if this is a NixOS config vs a package
            context["is_nixos_config"] = "nixosConfigurations" in content
            context["is_package"] = context["has_packages"] and not context["is_nixos_config"]

            return context

        except OSError as e:
            logger.warning(f"Failed to read flake.nix: {e}")
            return None

    def _detect_python_context(self, project_path: Path) -> dict[str, Any] | None:
        """Extract context from pyproject.toml if present."""
        pyproject = project_path / "pyproject.toml"
        if not pyproject.exists():
            return None

        try:
            content = pyproject.read_text(encoding="utf-8")

            context = {
                "has_pyproject": True,
                "name": "",
                "description": "",
            }

            # Extract project name
            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
            if name_match:
                context["name"] = name_match.group(1)

            # Extract description
            desc_match = re.search(r'description\s*=\s*"([^"]+)"', content)
            if desc_match:
                context["description"] = desc_match.group(1)

            # Detect tools
            context["uses_uv"] = "[tool.uv]" in content or "uv.lock" in str(
                list(project_path.glob("uv.lock"))
            )
            context["uses_pytest"] = "[tool.pytest" in content or "pytest" in content

            return context

        except OSError as e:
            logger.warning(f"Failed to read pyproject.toml: {e}")
            return None

    def _detect_git_context(self, project_path: Path) -> dict[str, Any] | None:
        """Extract context from git history."""
        try:
            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-10", "--format=%s"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=project_path,
            )

            if result.returncode != 0:
                return None

            commits = result.stdout.strip().split("\n") if result.stdout.strip() else []

            # Get last commit date
            date_result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=project_path,
            )

            last_commit_date = date_result.stdout.strip() if date_result.returncode == 0 else ""

            return {
                "recent_commits": commits[:5],
                "commit_count": len(commits),
                "last_commit_date": last_commit_date,
            }

        except (subprocess.TimeoutExpired, OSError) as e:
            logger.warning(f"Failed to get git context: {e}")
            return None

    def _classify_project_type(self, context: dict[str, Any]) -> str:
        """Classify project type based on detected context.

        Priority order:
        1. MCP server (has @modelcontextprotocol/sdk)
        2. Nix package (has flake.nix with packages output, not NixOS config)
        3. Python devenv (has devenv.nix with Python)
        4. TypeScript (has package.json with typescript)
        5. Generic (fallback)
        """
        npm = context.get("npm", {})
        flake = context.get("flake", {})
        devenv = context.get("devenv", {})

        # MCP server detection
        if npm.get("is_mcp_server"):
            return "mcp_server"

        # Nix package detection
        if flake.get("is_package"):
            return "nix_package"

        # Python devenv detection
        if devenv.get("has_devenv") and "python" in devenv.get("languages", []):
            return "python_devenv"

        # TypeScript detection
        if npm.get("is_typescript"):
            return "typescript"

        # Generic fallback
        return "generic"

    def _select_template(self, context: dict[str, Any]) -> str:
        """Select appropriate template based on project type.

        Returns template filename (e.g., 'project-claude-mcp.j2')
        """
        project_type = context.get("project_type", "generic")

        template_map = {
            "mcp_server": "project-claude-mcp.j2",
            "nix_package": "project-claude-nix.j2",
            "python_devenv": "project-claude.j2",  # Use generic for now
            "typescript": "project-claude.j2",  # Use generic for now
            "generic": "project-claude.j2",
        }

        template = template_map.get(project_type, "project-claude.j2")

        # Verify template exists, fallback to generic if not
        if not self.validate_template_exists(template):
            logger.warning(f"Template {template} not found, using generic")
            return "project-claude.j2"

        return template
