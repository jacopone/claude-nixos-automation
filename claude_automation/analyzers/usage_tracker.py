"""
Usage tracker analyzer for Fish shell history.
Parses command history to identify usage patterns and frequently used tools.
"""

import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from ..schemas import CommandUsage, UsageAnalyticsConfig

logger = logging.getLogger(__name__)


class UsageTracker:
    """Analyzes Fish shell history to track command usage patterns."""

    def __init__(self, project_path: Path):
        """Initialize usage tracker."""
        self.project_path = project_path
        self.fish_history_path = (
            Path.home() / ".local" / "share" / "fish" / "fish_history"
        )

    def analyze(self, top_n: int = 20) -> UsageAnalyticsConfig:
        """
        Analyze Fish history and build usage analytics configuration.

        Args:
            top_n: Number of top commands to include

        Returns:
            UsageAnalyticsConfig with usage statistics
        """
        # Parse Fish history
        commands = self._parse_fish_history()

        # Count command frequencies
        command_stats = self._calculate_command_stats(commands)

        # Get top commands
        top_commands = self._get_top_commands(command_stats, top_n)

        # Detect tool usage
        tool_usage = self._detect_tool_usage(commands)

        # Detect workflow patterns
        workflow_patterns = self._detect_workflow_patterns(commands)

        return UsageAnalyticsConfig(
            project_path=self.project_path,
            fish_history_path=self.fish_history_path,
            command_stats=command_stats,
            top_commands=top_commands,
            tool_usage=tool_usage,
            workflow_patterns=workflow_patterns,
            total_commands=len(commands),
        )

    def _parse_fish_history(self) -> list[tuple[str, datetime]]:
        """
        Parse Fish history file.

        Returns:
            List of (command, timestamp) tuples
        """
        commands = []

        if not self.fish_history_path.exists():
            logger.warning(f"Fish history file not found: {self.fish_history_path}")
            return commands

        try:
            content = self.fish_history_path.read_text(
                encoding="utf-8", errors="ignore"
            )

            # Parse YAML-like format
            # Format: "- cmd: <command>\n  when: <timestamp>"
            cmd_pattern = re.compile(r"- cmd: (.+?)\n  when: (\d+)", re.MULTILINE)

            for match in cmd_pattern.finditer(content):
                cmd = match.group(1).strip()
                timestamp = int(match.group(2))
                dt = datetime.fromtimestamp(timestamp)
                commands.append((cmd, dt))

            logger.info(f"Parsed {len(commands)} commands from Fish history")

        except Exception as e:
            logger.error(f"Failed to parse Fish history: {e}")

        return commands

    def _calculate_command_stats(
        self, commands: list[tuple[str, datetime]]
    ) -> dict[str, CommandUsage]:
        """
        Calculate usage statistics for each command.

        Args:
            commands: List of (command, timestamp) tuples

        Returns:
            Dictionary mapping command to CommandUsage
        """
        # Group by base command (first word)
        command_map = {}

        for cmd, timestamp in commands:
            # Extract base command
            base_cmd = self._extract_base_command(cmd)

            if base_cmd not in command_map:
                command_map[base_cmd] = {
                    "command": base_cmd,
                    "count": 0,
                    "last_used": timestamp,
                }

            command_map[base_cmd]["count"] += 1
            # Keep most recent timestamp
            if timestamp > command_map[base_cmd]["last_used"]:
                command_map[base_cmd]["last_used"] = timestamp

        # Convert to CommandUsage objects
        stats = {}
        for base_cmd, data in command_map.items():
            stats[base_cmd] = CommandUsage(
                command=data["command"],
                count=data["count"],
                last_used=data["last_used"],
                category=self._categorize_command(base_cmd),
            )

        return stats

    def _extract_base_command(self, cmd: str) -> str:
        """
        Extract base command from full command line.

        Args:
            cmd: Full command string

        Returns:
            Base command name
        """
        # Remove leading/trailing whitespace
        cmd = cmd.strip()

        # Extract first word
        parts = cmd.split()
        if not parts:
            return cmd

        base = parts[0]

        # Handle special cases
        if base in ("sudo", "time", "watch"):
            # Get next word after sudo/time/watch
            if len(parts) > 1:
                return parts[1]

        return base

    def _categorize_command(self, cmd: str) -> str:
        """
        Categorize command by type.

        Args:
            cmd: Command name

        Returns:
            Category string
        """
        # Common categories
        file_ops = {
            "ls",
            "eza",
            "cd",
            "mkdir",
            "rm",
            "cp",
            "mv",
            "touch",
            "cat",
            "bat",
            "less",
            "head",
            "tail",
        }
        git_cmds = {"git", "gh", "lazygit", "gitui"}
        dev_tools = {
            "npm",
            "node",
            "python",
            "python3",
            "cargo",
            "rustc",
            "gcc",
            "make",
            "uv",
            "ruff",
        }
        nix_cmds = {"nix", "nixos-rebuild", "nix-env", "nix-shell", "nix-build"}
        system_cmds = {
            "sudo",
            "systemctl",
            "ps",
            "procs",
            "top",
            "htop",
            "btm",
            "kill",
        }
        search_cmds = {"grep", "rg", "fd", "find", "fzf", "skim"}

        if cmd in file_ops:
            return "file_operations"
        elif cmd in git_cmds:
            return "git"
        elif cmd in dev_tools:
            return "development"
        elif cmd in nix_cmds:
            return "nix"
        elif cmd in system_cmds:
            return "system"
        elif cmd in search_cmds:
            return "search"
        else:
            return "unknown"

    def _get_top_commands(
        self, command_stats: dict[str, CommandUsage], top_n: int
    ) -> list[str]:
        """
        Get top N most used commands.

        Args:
            command_stats: Command usage statistics
            top_n: Number of top commands to return

        Returns:
            List of top command names
        """
        # Sort by count descending
        sorted_cmds = sorted(
            command_stats.items(), key=lambda x: x[1].count, reverse=True
        )

        return [cmd for cmd, _ in sorted_cmds[:top_n]]

    def _detect_tool_usage(
        self, commands: list[tuple[str, datetime]]
    ) -> dict[str, int]:
        """
        Detect usage of specific tools.

        Args:
            commands: List of (command, timestamp) tuples

        Returns:
            Dictionary mapping tool name to usage count
        """
        # List of interesting tools to track
        tools = {
            # Modern CLI tools
            "eza",
            "bat",
            "rg",
            "fd",
            "dust",
            "procs",
            "bottom",
            "btm",
            "jless",
            "yq",
            "glow",
            "zoxide",
            # Development tools
            "git",
            "gh",
            "lazygit",
            "gitui",
            "aider",
            "ruff",
            "uv",
            # Nix tools
            "nix",
            "nixos-rebuild",
            "devenv",
            # AI tools
            "claude-flow",
            "mcp",
        }

        tool_counts = Counter()

        for cmd, _ in commands:
            base_cmd = self._extract_base_command(cmd)
            if base_cmd in tools:
                tool_counts[base_cmd] += 1

        return dict(tool_counts)

    def _detect_workflow_patterns(
        self, commands: list[tuple[str, datetime]]
    ) -> list[str]:
        """
        Detect common workflow patterns from command sequences.

        Args:
            commands: List of (command, timestamp) tuples

        Returns:
            List of detected workflow patterns
        """
        patterns = []

        # Extract just commands
        cmd_list = [self._extract_base_command(cmd) for cmd, _ in commands]

        # Detect patterns
        if cmd_list.count("git") > 50:
            patterns.append("Heavy git user")

        if cmd_list.count("nix") + cmd_list.count("nixos-rebuild") > 30:
            patterns.append("Frequent NixOS rebuilds")

        if "eza" in cmd_list and cmd_list.count("eza") > cmd_list.count("ls"):
            patterns.append("Modern CLI tools adoption")

        if "aider" in cmd_list or "claude-flow" in cmd_list:
            patterns.append("AI-assisted development")

        if cmd_list.count("ruff") > 20 or cmd_list.count("uv") > 20:
            patterns.append("Python development with modern tools")

        if "cargo" in cmd_list:
            patterns.append("Rust development")

        if "npm" in cmd_list or "node" in cmd_list:
            patterns.append("Node.js development")

        return patterns
