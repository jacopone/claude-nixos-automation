#!/usr/bin/env python3
"""
Modern CLI Enforcer Hook for Claude Code
Enforces usage of modern CLI tools over legacy POSIX commands.
"""

import json
import os
import re
import sys
from datetime import datetime

# Debug log file
DEBUG_LOG_FILE = "/tmp/modern-cli-enforcer-log.txt"


def debug_log(message):
    """Append debug message to log file with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(DEBUG_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # Silently ignore logging errors


# Modern CLI tool mappings
# Format: legacy_command -> (modern_replacement, description)
TOOL_MAPPINGS = {
    "find": ("fd", "Fast file searching with better defaults"),
    "ls": ("eza", "Enhanced directory listing with git integration"),
    "grep": ("rg", "Ultra-fast text search (ripgrep)"),
    "cat": ("bat", "Syntax-highlighted file viewing"),
    "du": ("dust", "Interactive disk usage analyzer"),
    "ps": ("procs", "Modern process viewer with better formatting"),
}

# Patterns to detect legacy tool usage in bash commands
# More sophisticated detection to avoid false positives
LEGACY_TOOL_PATTERNS = {
    "find": r"\bfind\s+",  # find with arguments
    "ls": r"\bls\s+",  # ls with arguments or flags
    "grep": r"\bgrep\s+",  # grep with arguments
    "cat": r"\bcat\s+",  # cat with arguments
    "du": r"\bdu\s+",  # du with arguments
    "ps": r"\bps\s+",  # ps with arguments
}


def get_state_file(session_id):
    """Get session-specific state file path."""
    return os.path.expanduser(f"~/.claude/modern_cli_warnings_{session_id}.json")


def load_state(session_id):
    """Load the state of shown warnings from file."""
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return set(json.load(f))
        except (OSError, json.JSONDecodeError):
            return set()
    return set()


def save_state(session_id, shown_warnings):
    """Save the state of shown warnings to file."""
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown_warnings), f)
    except OSError as e:
        debug_log(f"Failed to save state file: {e}")
        pass  # Fail silently if we can't save state


def detect_legacy_tools(bash_command):
    """
    Detect legacy tools in bash command and suggest modern alternatives.

    Returns:
        tuple: (legacy_tool, modern_replacement, rewritten_command) or (None, None, None)
    """
    for legacy, pattern in LEGACY_TOOL_PATTERNS.items():
        if re.search(pattern, bash_command):
            modern, desc = TOOL_MAPPINGS[legacy]

            # Try to rewrite the command with modern equivalent
            rewritten = rewrite_command(bash_command, legacy, modern)

            return legacy, modern, rewritten, desc

    return None, None, None, None


def rewrite_command(command, legacy, modern):
    """
    Attempt to rewrite command from legacy to modern tool.

    This is a best-effort translation. Some commands may need manual adjustment.
    """
    rewrites = {
        "find": rewrite_find_to_fd,
        "ls": rewrite_ls_to_eza,
        "grep": rewrite_grep_to_rg,
        "cat": rewrite_cat_to_bat,
        "du": rewrite_du_to_dust,
        "ps": rewrite_ps_to_procs,
    }

    if legacy in rewrites:
        return rewrites[legacy](command)

    # Fallback: simple substitution
    return re.sub(r"\b" + legacy + r"\b", modern, command)


def rewrite_find_to_fd(command):
    """Rewrite find command to fd."""
    # Simple pattern: find . -name "*.py" -> fd "\.py$"
    # This is best-effort, complex find commands may need manual adjustment

    # Pattern: find [path] -name "pattern"
    match = re.search(r'find\s+(\S+)?\s+-name\s+["\']([^"\']+)["\']', command)
    if match:
        path = match.group(1) or "."
        pattern = match.group(2)
        # Convert shell glob to regex for fd
        fd_pattern = pattern.replace("*", ".*").replace("?", ".")
        if path == ".":
            return f'fd "{fd_pattern}"'
        else:
            return f'fd "{fd_pattern}" {path}'

    # Fallback: suggest fd with note
    return "fd  # Note: Complex find syntax may need manual adjustment"


def rewrite_ls_to_eza(command):
    """Rewrite ls command to eza."""
    # ls -la -> eza -la
    # ls -l -> eza -l
    return re.sub(r"\bls\b", "eza", command)


def rewrite_grep_to_rg(command):
    """Rewrite grep command to rg (ripgrep)."""
    # grep -r "pattern" -> rg "pattern"
    # grep "pattern" file -> rg "pattern" file
    return re.sub(r"\bgrep\s+(-r\s+)?", "rg ", command)


def rewrite_cat_to_bat(command):
    """Rewrite cat command to bat."""
    # cat file.py -> bat file.py
    # Exception: cat in pipes should stay as cat (bat adds formatting)
    if "|" in command and command.index("cat") < command.index("|"):
        # cat is being piped, likely for content not viewing
        return command  # Keep cat for piping

    return re.sub(r"\bcat\b", "bat", command)


def rewrite_du_to_dust(command):
    """Rewrite du command to dust."""
    # du -h -> dust
    # du -sh -> dust
    return re.sub(r"\bdu\s+(-[a-z]+\s+)?", "dust ", command)


def rewrite_ps_to_procs(command):
    """Rewrite ps command to procs."""
    # ps aux -> procs
    # ps aux | grep firefox -> procs firefox

    # Pattern: ps aux | grep <process>
    match = re.search(r"ps\s+aux\s*\|\s*grep\s+(\S+)", command)
    if match:
        process = match.group(1)
        return f"procs {process}"

    # Simple ps aux -> procs
    return re.sub(r"\bps\s+aux\b", "procs", command)


def format_warning(legacy, modern, rewritten, description):
    """Format the enforcement warning message."""
    return f"""⚠️  Modern CLI Tool Enforcement

Your command uses the legacy tool '{legacy}'.
This system enforces modern CLI tools with better defaults and performance.

Legacy:  {legacy}
Modern:  {modern} - {description}

Suggested rewrite:
  {rewritten}

To learn more about modern CLI tools, see:
  ~/.claude/CLAUDE.md (section: Modern CLI Tools)

Note: This enforcement can be disabled by setting:
  export ENFORCE_MODERN_CLI=0
"""


def main():
    """Main hook function."""
    # Check if enforcement is enabled
    enforce_enabled = os.environ.get("ENFORCE_MODERN_CLI", "1")

    if enforce_enabled == "0":
        sys.exit(0)  # Enforcement disabled, allow all commands

    # Read input from stdin
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        sys.exit(0)  # Allow tool to proceed if we can't parse input

    # Extract session ID and tool information
    session_id = input_data.get("session_id", "default")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Bash commands
    if tool_name != "Bash":
        sys.exit(0)  # Allow non-Bash tools to proceed

    # Extract the bash command
    bash_command = tool_input.get("command", "")
    if not bash_command:
        sys.exit(0)  # No command to check

    debug_log(f"Checking command: {bash_command}")

    # Detect legacy tools and get modern alternatives
    legacy, modern, rewritten, description = detect_legacy_tools(bash_command)

    if legacy:
        # Create unique warning key for this specific command
        warning_key = f"{legacy}-{bash_command}"

        # Load existing warnings for this session
        shown_warnings = load_state(session_id)

        # Check if we've already warned about this exact command
        if warning_key not in shown_warnings:
            # Add to shown warnings and save
            shown_warnings.add(warning_key)
            save_state(session_id, shown_warnings)

            # Format and output the warning
            warning = format_warning(legacy, modern, rewritten, description)
            print(warning, file=sys.stderr)

            # Block execution (exit code 2)
            debug_log(f"Blocked command using {legacy}, suggested {modern}")
            sys.exit(2)
        else:
            # Already warned about this command in this session
            # Allow it to proceed (user chose to ignore the suggestion)
            debug_log(f"Command already warned, allowing: {bash_command}")
            sys.exit(0)

    # No legacy tools detected, allow command to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
