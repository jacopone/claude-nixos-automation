"""
Session log parser for MCP usage analysis.

Extracted from mcp_usage_analyzer.py to reduce complexity.
The original _parse_session_log had CCN 35 - this module splits it into
focused functions with CCN < 10 each.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SessionTrackingData:
    """Tracks data for a single session during parsing."""

    project_path: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    servers_used: set[str] = field(default_factory=set)
    total_tokens: int = 0
    mcp_invocation_count: int = 0


@dataclass
class ToolUsageData:
    """Tracks usage data for a single MCP tool."""

    server_name: str = ""
    tool_name: str = ""
    invocation_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_used: datetime | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


class SessionParser:
    """
    Parse Claude session logs for MCP tool usage.

    Splits the monolithic parsing into focused, testable methods.
    """

    def parse_log_file(
        self,
        log_file: Path,
        cutoff_date: datetime,
        usage_data: dict[str, ToolUsageData],
        session_data: dict[str, SessionTrackingData],
    ) -> None:
        """
        Parse a single session log file for MCP invocations.

        Args:
            log_file: Path to the JSONL log file
            cutoff_date: Only include entries after this date
            usage_data: Dict to update with tool usage (mutated in place)
            session_data: Dict to update with session stats (mutated in place)
        """
        session_id = log_file.stem
        project_path = log_file.parent.name

        # Initialize session tracking
        if session_id not in session_data:
            session_data[session_id] = SessionTrackingData(project_path=project_path)

        with open(log_file) as f:
            for line_num, line in enumerate(f, 1):
                self._process_log_line(
                    line=line,
                    line_num=line_num,
                    log_file=log_file,
                    cutoff_date=cutoff_date,
                    session_id=session_id,
                    usage_data=usage_data,
                    session_data=session_data,
                )

    def _process_log_line(
        self,
        line: str,
        line_num: int,
        log_file: Path,
        cutoff_date: datetime,
        session_id: str,
        usage_data: dict[str, ToolUsageData],
        session_data: dict[str, SessionTrackingData],
    ) -> None:
        """Process a single line from the log file."""
        if not line.strip():
            return

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON in {log_file}:{line_num}: {e}")
            return

        try:
            timestamp = self._parse_timestamp(data)
            if timestamp is None or timestamp < cutoff_date:
                return

            self._update_session_timestamps(session_data[session_id], timestamp)

            message = data.get("message", {})
            content = message.get("content", [])

            if not isinstance(content, list):
                return

            self._update_session_tokens(session_data[session_id], message)
            self._process_mcp_tools(
                content, timestamp, session_id, usage_data, session_data
            )
            self._update_tool_tokens(content, message, usage_data)

        except Exception as e:
            logger.debug(f"Error processing line {line_num} in {log_file}: {e}")

    def _parse_timestamp(self, data: dict[str, Any]) -> datetime | None:
        """Parse timestamp from log entry."""
        timestamp_str = data.get("timestamp")
        if not timestamp_str:
            return None

        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    def _update_session_timestamps(
        self, session: SessionTrackingData, timestamp: datetime
    ) -> None:
        """Update session start/end times."""
        if session.start_time is None or timestamp < session.start_time:
            session.start_time = timestamp
        if session.end_time is None or timestamp > session.end_time:
            session.end_time = timestamp

    def _update_session_tokens(
        self, session: SessionTrackingData, message: dict[str, Any]
    ) -> None:
        """Update session token count from message usage."""
        usage = message.get("usage", {})
        if usage and isinstance(usage, dict):
            session.total_tokens += usage.get("input_tokens", 0)
            session.total_tokens += usage.get("output_tokens", 0)

    def _process_mcp_tools(
        self,
        content: list[Any],
        timestamp: datetime,
        session_id: str,
        usage_data: dict[str, ToolUsageData],
        session_data: dict[str, SessionTrackingData],
    ) -> None:
        """Process MCP tool invocations in message content."""
        for item in content:
            if not isinstance(item, dict):
                continue

            tool_name = item.get("name", "")
            if not tool_name.startswith("mcp__"):
                continue

            parsed = self._parse_mcp_tool_name(tool_name)
            if parsed is None:
                continue

            server_name, tool_only = parsed
            key = f"{server_name}__{tool_only}"

            # Track server usage in this session
            session_data[session_id].servers_used.add(server_name)
            session_data[session_id].mcp_invocation_count += 1

            # Initialize or update tool usage data
            if key not in usage_data:
                usage_data[key] = ToolUsageData(
                    server_name=server_name, tool_name=tool_only
                )

            usage_data[key].invocation_count += 1

            # Update last used
            if (
                usage_data[key].last_used is None
                or timestamp > usage_data[key].last_used
            ):
                usage_data[key].last_used = timestamp

            # Track success/failure
            self._update_tool_result(item, usage_data[key])

    def _parse_mcp_tool_name(self, tool_name: str) -> tuple[str, str] | None:
        """
        Parse MCP tool name into server and tool parts.

        Format: mcp__server__tool or mcp__server__subtool__name
        """
        parts = tool_name.split("__")
        if len(parts) < 3:
            return None

        server_name = parts[1]
        tool_only = "__".join(parts[2:])
        return server_name, tool_only

    def _update_tool_result(self, item: dict[str, Any], usage: ToolUsageData) -> None:
        """Update tool success/error counts from tool result."""
        item_type = item.get("type", "")
        if item_type == "tool_result":
            if item.get("isError", False):
                usage.error_count += 1
            else:
                usage.success_count += 1

    def _update_tool_tokens(
        self,
        content: list[Any],
        message: dict[str, Any],
        usage_data: dict[str, ToolUsageData],
    ) -> None:
        """Update token counts for MCP tools in this message."""
        usage = message.get("usage", {})
        if not usage or not isinstance(usage, dict):
            return

        # Find MCP tools in this message
        mcp_tools = [
            item.get("name", "")
            for item in content
            if isinstance(item, dict) and item.get("name", "").startswith("mcp__")
        ]

        if not mcp_tools:
            return

        # Attribute tokens to all MCP tools in this message
        for tool_name in mcp_tools:
            parsed = self._parse_mcp_tool_name(tool_name)
            if parsed is None:
                continue

            server_name, tool_only = parsed
            key = f"{server_name}__{tool_only}"

            if key not in usage_data:
                continue

            usage_data[key].input_tokens += usage.get("input_tokens", 0)
            usage_data[key].output_tokens += usage.get("output_tokens", 0)
            usage_data[key].cache_read_tokens += usage.get("cache_read_input_tokens", 0)
            usage_data[key].cache_creation_tokens += usage.get(
                "cache_creation_input_tokens", 0
            )
