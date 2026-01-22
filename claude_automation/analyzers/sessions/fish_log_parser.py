"""
Fish command log parser for tool usage analysis.

Extracted from tool_usage_analyzer._analyze_fish_logs (CCN 23)
to reduce complexity with focused parsing methods.
"""

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from claude_automation.tool_categories import (
    ALL_CATEGORIZED_TOOLS,
    get_canonical_tool_name,
)

logger = logging.getLogger(__name__)


@dataclass
class FishCommandEntry:
    """A single parsed command entry from Fish log."""

    timestamp: datetime
    command: str
    source: str  # "human", "claude-code", "script"
    tool_name: str


@dataclass
class FishToolUsageData:
    """Tracks usage data for a single tool during parsing."""

    tool_name: str = ""
    total: int = 0
    human: int = 0
    claude: int = 0
    script: int = 0
    first_used: datetime | None = None
    last_used: datetime | None = None


class FishLogParser:
    """
    Parse Fish command logs for tool usage analysis.

    Splits the monolithic parsing into focused, testable methods.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path

    def parse(
        self,
        tool_names: set[str],
        days: int,
    ) -> dict[str, FishToolUsageData]:
        """
        Parse Fish log file for tool usage.

        Args:
            tool_names: Set of installed tool names for filtering
            days: Number of days to analyze

        Returns:
            Dict mapping tool name to FishToolUsageData
        """
        if not self.log_path.exists():
            logger.warning(f"Fish command log not found: {self.log_path}")
            return {}

        # Calculate cutoff timestamp
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        cutoff_timestamp = int(cutoff_date.timestamp())

        # Initialize usage tracking
        usage_data: dict[str, FishToolUsageData] = {}

        # Parse log entries
        for entry in self._parse_entries(cutoff_timestamp):
            # Filter to known tools
            if (
                entry.tool_name not in tool_names
                and entry.tool_name not in ALL_CATEGORIZED_TOOLS
            ):
                continue

            # Initialize if first time seeing this tool
            if entry.tool_name not in usage_data:
                usage_data[entry.tool_name] = FishToolUsageData(tool_name=entry.tool_name)

            # Update stats
            self._update_stats(usage_data[entry.tool_name], entry)

        logger.info(f"Found usage data for {len(usage_data)} tools")
        return usage_data

    def _parse_entries(self, cutoff_timestamp: int) -> Iterator[FishCommandEntry]:
        """
        Parse log entries after cutoff timestamp.

        Yields FishCommandEntry for each valid entry.
        """
        with open(self.log_path) as f:
            for line_num, line in enumerate(f, 1):
                entry = self._parse_line(line, line_num, cutoff_timestamp)
                if entry is not None:
                    yield entry

    def _parse_line(
        self, line: str, line_num: int, cutoff_timestamp: int
    ) -> FishCommandEntry | None:
        """Parse a single log line into a FishCommandEntry."""
        if not line.strip():
            return None

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON at line {line_num}: {e}")
            return None

        try:
            timestamp = data.get("ts", 0)
            cmd = data.get("cmd", "")
            source = data.get("src", "human")

            # Skip if outside analysis period
            if timestamp < cutoff_timestamp:
                return None

            # Extract tool name from command
            tool_name = self._extract_tool_name(cmd)
            if tool_name is None:
                return None

            return FishCommandEntry(
                timestamp=datetime.fromtimestamp(timestamp, tz=UTC),
                command=cmd,
                source=source,
                tool_name=tool_name,
            )
        except Exception as e:
            logger.debug(f"Error processing line {line_num}: {e}")
            return None

    def _extract_tool_name(self, cmd: str) -> str | None:
        """Extract canonical tool name from command string."""
        if not cmd:
            return None

        # Get first token (command name)
        parts = cmd.split()
        if not parts:
            return None

        first_token = parts[0]
        if not first_token:
            return None

        # Handle path prefixes (e.g., /usr/bin/git → git)
        command_name = Path(first_token).name

        # Get canonical tool name
        return get_canonical_tool_name(command_name)

    def _update_stats(self, stats: FishToolUsageData, entry: FishCommandEntry) -> None:
        """Update tool usage stats from a command entry."""
        stats.total += 1

        if entry.source == "human":
            stats.human += 1
        elif entry.source == "claude-code":
            stats.claude += 1
        elif entry.source in ("script", "bash-script", "python-script"):
            stats.script += 1

        # Update timestamps
        if stats.first_used is None or entry.timestamp < stats.first_used:
            stats.first_used = entry.timestamp
        if stats.last_used is None or entry.timestamp > stats.last_used:
            stats.last_used = entry.timestamp
