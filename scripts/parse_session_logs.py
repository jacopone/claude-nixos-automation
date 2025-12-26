#!/usr/bin/env python3
"""
Parse Claude Code session logs to extract permission approvals.
Initializes the learning system with historical data.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def parse_session_file(session_file: Path) -> list[dict]:
    """
    Parse a single session file to extract APPROVED permission requests.

    Claude Code session files are JSONL with this structure:
    {"type": "assistant", "message": {"role": "assistant", "content": [...]}, "timestamp": "..."}

    An approval is detected when:
    1. Claude issues a tool_use block (with an id)
    2. A corresponding tool_result block exists (user approved and tool executed)
    3. The tool_result has is_error=False (execution succeeded)

    This two-pass approach ensures we only learn from actually approved permissions,
    not just tools that Claude attempted to use.
    """
    approvals = []

    try:
        with open(session_file) as f:
            lines = f.readlines()

        session_id = session_file.stem
        project_path = session_file.parent.name.replace(
            "-", "/", 1
        )  # Only first hyphen

        # First pass: collect all tool_use and tool_result blocks
        tool_uses = {}  # tool_id -> (tool_name, tool_input, timestamp)
        tool_results = {}  # tool_id -> is_error

        for line in lines:
            try:
                entry = json.loads(line.strip())
                message = entry.get("message", {})
                content = message.get("content", [])
                timestamp = entry.get("timestamp", datetime.now().isoformat())

                if not isinstance(content, list):
                    continue

                for block in content:
                    if not isinstance(block, dict):
                        continue

                    block_type = block.get("type", "")

                    if block_type == "tool_use":
                        tool_id = block.get("id", "")
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        if tool_id:
                            tool_uses[tool_id] = (tool_name, tool_input, timestamp)

                    elif block_type == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        is_error = block.get("is_error", False)
                        if tool_id:
                            tool_results[tool_id] = is_error

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        # Second pass: only emit approvals for tool_uses that have successful results
        for tool_id, (tool_name, tool_input, timestamp) in tool_uses.items():
            # Check if this tool was approved (has a result) and succeeded
            if tool_id in tool_results:
                is_error = tool_results[tool_id]
                if not is_error:
                    # This tool was APPROVED by user AND executed successfully
                    permission = extract_permission(tool_name, tool_input)
                    if permission:
                        approvals.append(
                            {
                                "timestamp": timestamp,
                                "permission": permission,
                                "session_id": session_id,
                                "project_path": project_path,
                                "context": {"approved": True, "tool_id": tool_id},
                            }
                        )

    except Exception as e:
        print(f"Error parsing {session_file}: {e}", file=sys.stderr)

    return approvals


def extract_permission(tool_name: str, tool_input: dict) -> str | None:
    """
    Extract permission pattern from tool use.

    Examples:
    - Bash tool: "Bash(git status:*)"
    - Read tool: "Read(/path/to/file)"
    - Edit tool: "Edit(/path/to/file)"
    """
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if command:
            # Extract command, keeping git subcommands
            parts = command.split()
            if len(parts) >= 2 and parts[0] == "git":
                # Keep git subcommand: git status → "Bash(git status:*)"
                cmd_name = f"{parts[0]} {parts[1]}"
            else:
                # Just first word: fd → "Bash(fd:*)"
                cmd_name = parts[0] if parts else "unknown"
            return f"Bash({cmd_name}:*)"

    elif tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if file_path:
            # Generalize path to directory level
            path_obj = Path(file_path)
            if path_obj.parent:
                return f"Read({path_obj.parent}/**)"
            return f"Read({file_path})"

    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        if file_path:
            path_obj = Path(file_path)
            if path_obj.parent:
                return f"Edit({path_obj.parent}/**)"
            return f"Edit({file_path})"

    elif tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        if file_path:
            path_obj = Path(file_path)
            if path_obj.parent:
                return f"Write({path_obj.parent}/**)"
            return f"Write({file_path})"

    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        if pattern:
            return f"Glob({pattern})"

    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        if pattern:
            return "Grep(*)"

    return None


def main():
    """
    Parse session files and extract permissions incrementally.

    This function preserves existing approval data and only adds new approvals
    from sessions that haven't been processed yet. This is more efficient and
    preserves historical data with different parsing logic.
    """
    from collections import Counter

    claude_projects = Path.home() / ".claude" / "projects"

    if not claude_projects.exists():
        print(f"Error: {claude_projects} does not exist", file=sys.stderr)
        return 1

    # Setup paths
    learning_dir = Path.home() / ".claude" / "learning"
    learning_dir.mkdir(parents=True, exist_ok=True)
    output_file = learning_dir / "permission_approvals.jsonl"
    processed_file = learning_dir / "processed_sessions.txt"

    # Load existing approvals to get their keys for deduplication
    existing_keys = set()
    existing_count = 0
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    key = (entry.get("permission", ""), entry.get("session_id", ""))
                    existing_keys.add(key)
                    existing_count += 1
                except json.JSONDecodeError:
                    continue
        print(f"📂 Existing approvals: {existing_count}")

    # Load list of already-processed session files
    processed_sessions = set()
    if processed_file.exists():
        processed_sessions = set(processed_file.read_text().strip().split("\n"))
        print(f"   Already processed: {len(processed_sessions)} session files")

    # Find session files to process
    session_files = list(claude_projects.glob("*/*.jsonl"))
    new_session_files = [f for f in session_files if str(f) not in processed_sessions]

    print(f"   Found {len(session_files)} total session files")
    print(f"   New to process: {len(new_session_files)} session files")

    if not new_session_files:
        print("\n✅ No new sessions to process")
        return 0

    # Parse new session files
    new_approvals = []
    for session_file in new_session_files:
        approvals = parse_session_file(session_file)
        for approval in approvals:
            key = (approval["permission"], approval["session_id"])
            if key not in existing_keys:
                new_approvals.append(approval)
                existing_keys.add(key)

    print(f"   Extracted {len(new_approvals)} new unique permission approvals")

    # Append new approvals to output file
    if new_approvals:
        with open(output_file, "a") as f:
            for approval in new_approvals:
                f.write(json.dumps(approval) + "\n")

    # Update processed sessions list
    with open(processed_file, "w") as f:
        all_processed = processed_sessions | {str(sf) for sf in new_session_files}
        f.write("\n".join(sorted(all_processed)))

    total_approvals = existing_count + len(new_approvals)
    print(f"\n✅ Total approvals now: {total_approvals}")
    print(
        f"   Added {len(new_approvals)} new approvals from {len(new_session_files)} sessions"
    )

    # Show top patterns from new approvals
    if new_approvals:
        pattern_counts = Counter(a["permission"] for a in new_approvals)
        print("\n📊 Top 10 most common NEW permissions:")
        for permission, count in pattern_counts.most_common(10):
            print(f"   {count:3d}× {permission}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
