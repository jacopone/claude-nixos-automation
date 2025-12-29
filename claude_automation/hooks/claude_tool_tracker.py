#!/usr/bin/env python3
"""
Claude Tool Tracker Hook - PostToolUse Hook

Logs Claude Code's Bash commands to the Fish command tracking system.
This enables the tool usage analytics to track both human and Claude usage.

Output: ~/.local/share/fish/command-source.jsonl
"""

import fcntl
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
LOG_FILE = Path.home() / ".local" / "share" / "fish" / "command-source.jsonl"
LOCK_FILE = Path.home() / ".local" / "share" / "fish" / "command-source.lock"
DEBUG_LOG_FILE = Path("/tmp/claude-tool-tracker-log.txt")

# Tools to track (Bash commands)
TRACKED_TOOLS = {"Bash", "BashOutput"}


def debug_log(message: str) -> None:
    """Append debug message to log file with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(DEBUG_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # Silently ignore logging errors


def extract_command_name(command: str) -> str | None:
    """Extract the first token (command name) from a bash command."""
    if not command:
        return None

    # Get first token
    tokens = command.split()
    if not tokens:
        return None

    first_token = tokens[0]

    # Handle path prefixes (e.g., /usr/bin/git → git)
    return Path(first_token).name


def sanitize_command(command: str) -> str:
    """Redact sensitive information from command."""
    import re

    # Sanitize passwords, tokens, API keys from logs
    cmd = re.sub(r"(-p\s+)\S+", r"\1***", command)
    cmd = re.sub(r"(--password[=\s]+)\S+", r"\1***", cmd)
    cmd = re.sub(
        r"(token|key|apikey|api_key|api-key)[=:]\s*\S+",
        r"\1=***",
        cmd,
        flags=re.IGNORECASE,
    )
    cmd = re.sub(
        r"(password|passwd|pwd)[=:]\s*\S+", r"\1=***", cmd, flags=re.IGNORECASE
    )
    cmd = re.sub(r"(Bearer\s+)\S+", r"\1***", cmd, flags=re.IGNORECASE)
    cmd = re.sub(r"(Authorization:\s+)\S+", r"\1***", cmd, flags=re.IGNORECASE)

    return cmd


def log_command(command: str, session_id: str, tool_result: dict | None = None) -> bool:
    """
    Log a command to the JSONL file.

    Args:
        command: The bash command that was executed
        session_id: Claude Code session ID
        tool_result: Optional tool result to determine success/failure

    Returns:
        True if logged successfully, False otherwise
    """
    try:
        # Ensure log directory exists
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Build log entry
        timestamp = int(time.time())
        sanitized_cmd = sanitize_command(command)
        command_name = extract_command_name(command)

        # Determine detection method and confidence
        detection_method = "claude-code-hook"
        confidence = 100  # Hooks have 100% confidence

        # Check if command succeeded (if tool_result available)
        success = True
        if tool_result:
            # Check for error indicators in result
            result_text = str(tool_result.get("content", ""))
            if "error" in result_text.lower() or "failed" in result_text.lower():
                success = False

        log_entry = {
            "ts": timestamp,
            "cmd": sanitized_cmd,
            "src": "claude-code",
            "confidence": confidence,
            "method": detection_method,
            "session": session_id[:8] if session_id else "unknown",
            "tool": command_name or "bash",
            "success": success,
        }

        # Convert to JSON
        json_line = json.dumps(log_entry, separators=(",", ":"))

        # Atomic write with file locking
        with open(LOCK_FILE, "w") as lock_fd:
            try:
                # Try to acquire lock with timeout
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                # Lock busy, skip this entry rather than block
                debug_log(f"Lock busy, skipping: {command_name}")
                return False

            try:
                with open(LOG_FILE, "a") as f:
                    f.write(json_line + "\n")
                debug_log(f"Logged: {command_name} (src=claude-code)")
                return True
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

    except Exception as e:
        debug_log(f"Error logging command: {e}")
        return False


def main():
    """Main hook function - runs after tool execution."""
    # Check if tracking is disabled
    if os.environ.get("CLAUDE_TOOL_TRACKER", "1") == "0":
        sys.exit(0)

    # Read input from stdin
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        sys.exit(0)  # Don't block on parse errors

    # Extract tool information
    session_id = input_data.get("session_id", "")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_result = input_data.get("tool_result", {})

    debug_log(
        f"PostToolUse: tool={tool_name}, session={session_id[:8] if session_id else 'none'}"
    )

    # Only track Bash commands
    if tool_name not in TRACKED_TOOLS:
        sys.exit(0)

    # Extract the bash command
    command = tool_input.get("command", "")
    if not command:
        debug_log("No command found in tool_input")
        sys.exit(0)

    # Log the command
    success = log_command(command, session_id, tool_result)

    if success:
        debug_log(f"Successfully logged: {extract_command_name(command)}")
    else:
        debug_log(f"Failed to log: {extract_command_name(command)}")

    # PostToolUse hooks should always exit 0 (don't block after execution)
    sys.exit(0)


if __name__ == "__main__":
    main()
