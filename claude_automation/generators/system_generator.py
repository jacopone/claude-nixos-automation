"""
System-level CLAUDE.md generator using templates and robust parsing.
"""

import logging
from datetime import datetime
from pathlib import Path

from ..parsers.cached_nix_parser import CachedNixParser
from ..schemas import (
    ClaudeRelevance,
    FishAbbreviation,
    GenerationResult,
    SystemConfig,
    ToolCategory,
    ToolInfo,
)
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class SystemGenerator(BaseGenerator):
    """
    Generates system-level CLAUDE.md files.

    Sources: Nix configuration files (packages.nix, base.nix, etc.)
    Artifacts: System-level CLAUDE.md
    """

    # Source/Artifact declarations
    MANUAL_SOURCES = [
        "packages.nix",  # Core system packages
        "base.nix",  # Home-manager packages
        "CLAUDE-USER-POLICIES.md",  # User policies
    ]
    GENERATED_ARTIFACTS = [
        "CLAUDE.md",  # System-level CLAUDE.md
    ]

    def __init__(self, template_dir: Path = None):
        super().__init__(template_dir)
        self.parser = CachedNixParser()

    def generate(self, output_path: Path, config_dir: Path = None) -> GenerationResult:
        """Generate system-level CLAUDE.md file."""
        if config_dir is None:
            config_dir = self._get_repo_root()

        try:
            # Parse configuration files
            system_config = self._build_system_config(config_dir)

            # Validate the configuration
            try:
                system_config.dict()  # Triggers Pydantic validation
            except Exception as e:
                logger.error(f"Configuration validation failed: {e}")
                return GenerationResult(
                    success=False,
                    output_path=str(output_path),
                    errors=[f"Configuration validation failed: {e}"],
                    warnings=[],
                    stats={},
                )

            # Prepare template context
            context = self._prepare_template_context(system_config)

            # Render template
            content = self.render_template("system-claude.j2", context)

            # Determine source files used
            source_files = ["packages.nix", "base.nix"]
            if system_config.has_user_policies:
                source_files.append("CLAUDE-USER-POLICIES.md")

            # Write artifact with protection and header
            result = self.write_artifact(
                output_path, content, source_files=source_files
            )

            # Add generation stats
            if result.success:
                result.stats.update(
                    {
                        "total_tools": system_config.total_tools,
                        "package_count": system_config.package_count,
                        "abbreviation_count": system_config.abbreviation_count,
                        "categories": len(system_config.tool_categories),
                    }
                )

                logger.info(
                    f"Generated system CLAUDE.md with {system_config.total_tools} tools"
                )

            return result

        except Exception as e:
            error_msg = f"System generation failed: {e}"
            logger.error(error_msg)
            return GenerationResult(
                success=False,
                output_path=str(output_path),
                errors=[error_msg],
                warnings=[],
                stats={},
            )

    def _build_system_config(self, config_dir: Path) -> SystemConfig:
        """Build system configuration from Nix files."""
        # Parse system packages
        packages_file = config_dir / "modules" / "core" / "packages.nix"
        if not packages_file.exists():
            raise FileNotFoundError(f"Packages file not found: {packages_file}")

        parsing_result = self.parser.parse_packages(packages_file)
        if not parsing_result.success:
            raise RuntimeError(f"Failed to parse packages: {parsing_result.errors}")

        # Parse home-manager packages (if any)
        home_file = config_dir / "modules" / "home-manager" / "base.nix"
        home_packages = {}
        if home_file.exists():
            try:
                home_result = self.parser.parse_packages(home_file)
                if home_result.success:
                    home_packages = home_result.packages
            except Exception as e:
                logger.warning(f"Failed to parse home packages: {e}")

        # Merge packages and organize by category
        all_packages = {**parsing_result.packages, **home_packages}
        tool_categories = self._organize_by_category(all_packages)

        # Parse fish abbreviations
        fish_abbreviations = self._parse_fish_abbreviations(home_file)

        # Get git status
        git_status = self.get_current_git_status()

        # Read user policies if they exist
        user_policies_file = Path.home() / ".claude" / "CLAUDE-USER-POLICIES.md"
        user_policies_content = ""
        has_user_policies = False

        if user_policies_file.exists():
            try:
                user_policies_content = user_policies_file.read_text(encoding="utf-8")
                has_user_policies = True
                logger.info(f"Read user policies from {user_policies_file}")
            except Exception as e:
                logger.warning(f"Failed to read user policies: {e}")

        return SystemConfig(
            timestamp=datetime.now(),
            package_count=len(all_packages),
            fish_abbreviations=fish_abbreviations,
            tool_categories=tool_categories,
            git_status=git_status,
            user_policies=user_policies_content,
            has_user_policies=has_user_policies,
        )

    # Tools that are substitutions for standard POSIX commands - ESSENTIAL
    TOOL_SUBSTITUTIONS = {
        "fd": "find",
        "eza": "ls",
        "bat": "cat",
        "ripgrep": "grep",
        "rg": "grep",
        "dust": "du",
        "procs": "ps",
        "bottom": "top",
        "btm": "top",
        "choose": "cut/awk",
        "duf": "df",
        "zoxide": "cd",
        "xh": "curl",
    }

    # Tools with unique syntax Claude wouldn't guess - HIGH relevance
    HIGH_RELEVANCE_TOOLS = {
        "jless",
        "miller",
        "mlr",
        "pgcli",
        "mycli",
        "usql",
        "csvlook",
        "yq",
        "yq-go",
        "glow",
        "hyperfine",
        "tokei",
        "ast-grep",
        "semgrep",
        "hurl",
        "broot",
        "atuin",
        "mcfly",
        "just",
        "entr",
    }

    # Standard tools Claude already knows - LOW relevance (skip)
    STANDARD_TOOLS = {
        "git",
        "gcc",
        "gnumake",
        "docker",
        "docker-compose",
        "podman",
        "npm",
        "nodejs",
        "python",
        "wget",
        "curl",
        "ssh",
        "tmux",
        "vim",
        "neovim",
        "sqlite",
        "jq",
        "gh",
        "nmap",
        "wireshark",
        "tcpdump",
        "strace",
        "gdb",
        "valgrind",
        "pkg-config",
        "cmake",
        "ninja",
        "file",
        "parallel",
    }

    def _calculate_relevance(self, tool: ToolInfo) -> ClaudeRelevance:
        """Calculate Claude relevance for a tool."""
        name_lower = tool.name.lower()

        # System Support Packages are never relevant
        if tool.category == ToolCategory.SYSTEM_PACKAGES:
            return ClaudeRelevance.NONE

        # Tool substitutions are ESSENTIAL
        if name_lower in self.TOOL_SUBSTITUTIONS:
            return ClaudeRelevance.ESSENTIAL

        # AI & MCP tools are ESSENTIAL (Claude should know about AI tools)
        if tool.category == ToolCategory.AI_MCP_TOOLS:
            return ClaudeRelevance.ESSENTIAL

        # Modern CLI Tools are ESSENTIAL (they're the substitutions)
        if tool.category == ToolCategory.CLI_TOOLS:
            return ClaudeRelevance.ESSENTIAL

        # High relevance tools with unique syntax
        if name_lower in self.HIGH_RELEVANCE_TOOLS:
            return ClaudeRelevance.HIGH

        # Standard tools Claude knows
        if name_lower in self.STANDARD_TOOLS:
            return ClaudeRelevance.LOW

        # Default to MEDIUM for unknown tools
        return ClaudeRelevance.MEDIUM

    def _filter_by_relevance(
        self, categories: dict[ToolCategory, list]
    ) -> dict[ToolCategory, list]:
        """Filter tools to only include ESSENTIAL and HIGH relevance."""
        filtered = {}

        for category, tools in categories.items():
            # Skip System Support Packages entirely
            if category == ToolCategory.SYSTEM_PACKAGES:
                continue

            filtered_tools = []
            for tool in tools:
                relevance = self._calculate_relevance(tool)
                # Update tool's relevance field
                tool.relevance = relevance
                # Only include ESSENTIAL and HIGH
                if relevance in (ClaudeRelevance.ESSENTIAL, ClaudeRelevance.HIGH):
                    filtered_tools.append(tool)

            # Only include category if it has tools
            if filtered_tools:
                filtered[category] = filtered_tools

        return filtered

    def _organize_by_category(self, packages: dict) -> dict[ToolCategory, list]:
        """Organize packages by category and filter by relevance."""
        categories = {}

        for tool_info in packages.values():
            category = tool_info.category
            if category not in categories:
                categories[category] = []
            categories[category].append(tool_info)

        # Sort tools within each category by name
        for category in categories:
            categories[category].sort(key=lambda t: t.name.lower())

        # Apply relevance filtering
        return self._filter_by_relevance(categories)

    def _parse_fish_abbreviations(self, home_file: Path) -> list[FishAbbreviation]:
        """Parse fish abbreviations from home-manager config."""
        if not home_file.exists():
            return []

        try:
            abbreviations_data = self.parser.extract_fish_abbreviations(home_file)
            return [
                FishAbbreviation(abbr=item["abbr"], command=item["command"])
                for item in abbreviations_data
            ]
        except Exception as e:
            logger.warning(f"Failed to parse fish abbreviations: {e}")
            return []

    def _prepare_template_context(self, config: SystemConfig) -> dict:
        """Prepare context for template rendering."""
        return {
            "timestamp": config.timestamp,
            "package_count": config.package_count,
            "fish_abbreviations": config.fish_abbreviations,
            "tool_categories": config.tool_categories,
            "git_status": config.git_status,
            "total_tools": config.total_tools,
            "user_policies": config.user_policies,
            "has_user_policies": config.has_user_policies,
            "generation_info": {
                "generator": "SystemGenerator",
                "version": "2.1.0",
                "template": "system-claude.j2",
            },
        }

    def get_summary_stats(self, config_dir: Path = None) -> dict:
        """Get summary statistics without generating the full file."""
        if config_dir is None:
            config_dir = self._get_repo_root()

        try:
            system_config = self._build_system_config(config_dir)
            return {
                "total_tools": system_config.total_tools,
                "package_count": system_config.package_count,
                "abbreviation_count": system_config.abbreviation_count,
                "categories": {
                    category.value: len(tools)
                    for category, tools in system_config.tool_categories.items()
                },
                "git_status": system_config.git_status.status_string,
                "timestamp": system_config.timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get summary stats: {e}")
            return {"error": str(e)}
