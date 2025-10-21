#!/usr/bin/env python3
"""
NixOS Safety Guard Hook for Claude Code
Prevents accidental system damage and enforces NixOS best practices.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Debug log file
DEBUG_LOG_FILE = "/tmp/nixos-safety-guard-log.txt"


def debug_log(message):
    """Append debug message to log file with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(DEBUG_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # Silently ignore logging errors


def get_state_file(session_id):
    """Get session-specific state file path."""
    return os.path.expanduser(f"~/.claude/nixos_safety_warnings_{session_id}.json")


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


# Protected files that should never be edited
PROTECTED_FILES = [
    "hardware-configuration.nix",
    "configuration.nix",  # If not using flakes
]

# Dangerous Bash command patterns
DANGEROUS_COMMANDS = [
    {
        "pattern": r"\bnixos-rebuild\s+(switch|boot|test|build|dry-build|dry-activate)",
        "warning_type": "nixos-rebuild-direct",
        "message": """⚠️  NixOS Safety: Direct nixos-rebuild Usage

You're using 'nixos-rebuild' directly.

This system has a safer wrapper script: ./rebuild-nixos

Benefits of using ./rebuild-nixos:
- Pre-flight validation (nix flake check)
- Test build before activation
- User confirmation prompts
- Automatic CLAUDE.md updates
- Git integration
- Build time tracking
- Rollback capability

Suggested alternative:
  cd ~/nixos-config && ./rebuild-nixos

If you must use nixos-rebuild directly, you can proceed, but the wrapper
provides important safety checks and automation.

To bypass this warning: export NIXOS_SAFETY_GUARD=0
""",
    },
    {
        "pattern": r"\bnix-collect-garbage\s+(-d|--delete-old)",
        "warning_type": "garbage-collect-destructive",
        "message": """⚠️  NixOS Safety: Destructive Garbage Collection

You're running 'nix-collect-garbage' with destructive flags.

WARNING: This will delete old NixOS generations!
- You won't be able to rollback to previous configurations
- This frees disk space but removes safety net
- Cannot be undone

Safer alternatives:
- nix-collect-garbage (without -d)  # Keeps old generations
- nix-store --gc                    # Safe garbage collection
- nix-store --optimise              # Deduplicate without deleting

Are you sure you want to delete old generations?

To proceed anyway: Re-run this command
To bypass this warning: export NIXOS_SAFETY_GUARD=0
""",
    },
    {
        "pattern": r"\bnix\s+profile\s+wipe-history",
        "warning_type": "wipe-history",
        "message": """⚠️  NixOS Safety: Wipe History

You're running 'nix profile wipe-history'.

WARNING: This removes all profile history!
- Cannot be undone
- Loses ability to rollback profile changes
- May break system if current generation has issues

Consider if you really need to wipe history.

To proceed anyway: Re-run this command
To bypass this warning: export NIXOS_SAFETY_GUARD=0
""",
    },
    {
        "pattern": r"\bnixos-rebuild\s+.*--fast",
        "warning_type": "fast-rebuild",
        "message": """⚠️  NixOS Safety: Fast Rebuild

You're using 'nixos-rebuild --fast'.

WARNING: This skips important checks!
- No pre-flight validation
- May miss configuration errors
- Could break your system

Unless you're debugging, use normal rebuild process.

Recommended: ./rebuild-nixos (has all safety checks)

To proceed anyway: Re-run this command
To bypass this warning: export NIXOS_SAFETY_GUARD=0
""",
    },
    {
        "pattern": r"\brm\s+.*(/etc/nixos|/nix/var/nix)",
        "warning_type": "delete-nix-files",
        "message": """⚠️  NixOS Safety: Deleting Critical NixOS Files

You're trying to delete files in /etc/nixos or /nix/var/nix!

WARNING: This can break your NixOS system!
- /etc/nixos contains system configuration
- /nix/var/nix contains Nix store metadata
- Deleting these can make system unbootable

If you're trying to clean up:
- Use 'nix-collect-garbage' instead
- Use 'nix-store --optimise' to save space
- Don't manually delete Nix infrastructure

To proceed anyway: Re-run this command with extreme caution
To bypass this warning: export NIXOS_SAFETY_GUARD=0
""",
    },
]


def check_protected_file(file_path):
    """
    Check if file is protected and should not be edited.

    Returns:
        tuple: (is_protected, warning_message) or (False, None)
    """
    file_name = os.path.basename(file_path)

    # Check if it's hardware-configuration.nix
    if file_name == "hardware-configuration.nix":
        return True, f"""⚠️  NixOS Safety: Editing Auto-Generated File

You're trying to edit: {file_path}

WARNING: hardware-configuration.nix is AUTO-GENERATED!
- This file is created by nixos-generate-config
- Changes will be lost on next hardware detection
- Editing it manually is error-prone

Best practices:
1. Don't edit this file directly
2. If you need to override hardware settings, create a new module
3. Import your module in configuration.nix or flake.nix

Example:
  # Create: modules/hardware-overrides.nix
  # Import in flake.nix: ./modules/hardware-overrides.nix

To proceed with editing (not recommended): Re-run this operation
To bypass this warning: export NIXOS_SAFETY_GUARD=0
"""

    # Check if it's the old-style configuration.nix (when using flakes)
    if file_name == "configuration.nix":
        # Try to detect if system uses flakes
        if os.path.exists(os.path.join(os.path.dirname(file_path), "flake.nix")):
            return True, f"""⚠️  NixOS Safety: Editing Legacy Configuration

You're trying to edit: {file_path}

INFO: This system uses flakes (flake.nix detected).
- configuration.nix is typically not used with flakes
- Main configuration should be in flake.nix or imported modules
- Editing configuration.nix may have no effect

If you're using flakes, your configuration is likely in:
- flake.nix (main entry point)
- hosts/*/default.nix (host-specific config)
- modules/*/*.nix (modular configuration)

To proceed anyway: Re-run this operation
To bypass this warning: export NIXOS_SAFETY_GUARD=0
"""

    return False, None


def is_called_from_rebuild_script(tool_input):
    """
    Detect if the command is being executed from within the rebuild-nixos wrapper script.

    This allows nixos-rebuild to run from within the safe wrapper script
    while still blocking direct manual invocation.

    Returns:
        bool: True if called from rebuild-nixos wrapper
    """
    # Check if the command originates from rebuild-nixos by looking at context
    # The tool_input might contain file paths or descriptions that indicate source

    # Method 1: Check if we're in nixos-config directory
    cwd = os.getcwd()
    if "nixos-config" in cwd:
        # Check if rebuild-nixos script exists in this directory
        rebuild_script = Path(cwd) / "rebuild-nixos"
        if rebuild_script.exists():
            # Likely being called from within the rebuild workflow
            # Additional check: look for environment markers that rebuild-nixos sets
            if os.environ.get("NIXOS_REBUILD_WRAPPER"):
                return True

    return False


def check_dangerous_command(bash_command, tool_input=None):
    """
    Check if bash command matches dangerous patterns.

    Args:
        bash_command: The bash command to check
        tool_input: Full tool input dict for context detection

    Returns:
        tuple: (is_dangerous, warning_type, warning_message) or (False, None, None)
    """
    for danger in DANGEROUS_COMMANDS:
        if re.search(danger["pattern"], bash_command):
            # Special handling for nixos-rebuild
            if danger["warning_type"] == "nixos-rebuild-direct":
                # Allow if called from rebuild-nixos wrapper
                if tool_input and is_called_from_rebuild_script(tool_input):
                    # This is safe - called from within the wrapper
                    return False, None, None

            return True, danger["warning_type"], danger["message"]

    return False, None, None


def find_nixos_config_root(current_path):
    """
    Try to find the NixOS config root (directory containing flake.nix).

    Returns:
        Path or None
    """
    path = Path(current_path).resolve()

    # Check current directory and parents
    for parent in [path] + list(path.parents):
        if (parent / "flake.nix").exists():
            return parent

    # Check common locations
    common_locations = [
        Path.home() / "nixos-config",
        Path("/etc/nixos"),
    ]

    for location in common_locations:
        if location.exists() and (location / "flake.nix").exists():
            return location

    return None


def suggest_rebuild_script_location(file_path):
    """
    Try to find ./rebuild-nixos script location.

    Returns:
        str: Suggested command
    """
    config_root = find_nixos_config_root(file_path)

    if config_root:
        rebuild_script = config_root / "rebuild-nixos"
        if rebuild_script.exists():
            return f"cd {config_root} && ./rebuild-nixos"

    # Fallback suggestion
    return "cd ~/nixos-config && ./rebuild-nixos"


def main():
    """Main hook function."""
    # Check if safety guard is enabled
    safety_enabled = os.environ.get("NIXOS_SAFETY_GUARD", "1")

    if safety_enabled == "0":
        sys.exit(0)  # Safety guard disabled, allow all operations

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

    debug_log(f"Tool: {tool_name}, Input: {tool_input}")

    # Check based on tool type
    warning_key = None
    warning_message = None

    # Check file edit/write operations
    if tool_name in ["Edit", "Write", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")

        if file_path and file_path.endswith(".nix"):
            is_protected, message = check_protected_file(file_path)
            if is_protected:
                warning_key = f"protected-file-{file_path}"
                warning_message = message

    # Check Bash commands
    elif tool_name == "Bash":
        bash_command = tool_input.get("command", "")
        if bash_command:
            is_dangerous, danger_type, message = check_dangerous_command(
                bash_command, tool_input
            )
            if is_dangerous:
                # For nixos-rebuild, add contextual suggestion
                if danger_type == "nixos-rebuild-direct":
                    # Try to find the actual rebuild script location
                    cwd = os.getcwd()
                    suggested_cmd = suggest_rebuild_script_location(cwd)
                    message = message.replace(
                        "cd ~/nixos-config && ./rebuild-nixos",
                        suggested_cmd,
                    )

                warning_key = f"{danger_type}-{bash_command}"
                warning_message = message

    # If we have a warning to show
    if warning_key and warning_message:
        # Load existing warnings for this session
        shown_warnings = load_state(session_id)

        # Check if we've already shown this warning
        if warning_key not in shown_warnings:
            # Add to shown warnings and save
            shown_warnings.add(warning_key)
            save_state(session_id, shown_warnings)

            # Output the warning and block execution
            print(warning_message, file=sys.stderr)
            debug_log(f"Blocked operation: {warning_key}")
            sys.exit(2)  # Block tool execution
        else:
            # Already warned, allow to proceed
            # (user explicitly chose to ignore the warning)
            debug_log(f"Warning already shown, allowing: {warning_key}")
            sys.exit(0)

    # No safety issues detected, allow operation
    sys.exit(0)


if __name__ == "__main__":
    main()
