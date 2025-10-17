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
    Parse a single session file to extract permission approvals.

    Claude Code session files are JSONL with this structure:
    {"type": "assistant", "message": {"role": "assistant", "content": [...]}, "timestamp": "..."}

    Tool use blocks contain permission requests.
    """
    approvals = []

    try:
        with open(session_file, 'r') as f:
            lines = f.readlines()

        session_id = session_file.stem
        project_path = session_file.parent.name.replace('-', '/', 1)  # Only first hyphen

        for line in lines:
            try:
                entry = json.loads(line.strip())

                # Look for assistant messages with tool use
                if entry.get('type') == 'assistant':
                    message = entry.get('message', {})
                    content = message.get('content', [])
                    timestamp = entry.get('timestamp', datetime.now().isoformat())

                    # Content is a list of blocks
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            tool_name = block.get('name', '')
                            tool_input = block.get('input', {})

                            # Extract permission pattern
                            permission = extract_permission(tool_name, tool_input)
                            if permission:
                                approvals.append({
                                    'timestamp': timestamp,
                                    'permission': permission,
                                    'session_id': session_id,
                                    'project_path': project_path,
                                    'context': {}
                                })

            except (json.JSONDecodeError, KeyError, TypeError):
                continue

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
    if tool_name == 'Bash':
        command = tool_input.get('command', '')
        if command:
            # Extract command, keeping git subcommands
            parts = command.split()
            if len(parts) >= 2 and parts[0] == 'git':
                # Keep git subcommand: git status → "Bash(git status:*)"
                cmd_name = f"{parts[0]} {parts[1]}"
            else:
                # Just first word: fd → "Bash(fd:*)"
                cmd_name = parts[0] if parts else 'unknown'
            return f"Bash({cmd_name}:*)"

    elif tool_name == 'Read':
        file_path = tool_input.get('file_path', '')
        if file_path:
            # Generalize path to directory level
            path_obj = Path(file_path)
            if path_obj.parent:
                return f"Read({path_obj.parent}/**)"
            return f"Read({file_path})"

    elif tool_name == 'Edit':
        file_path = tool_input.get('file_path', '')
        if file_path:
            path_obj = Path(file_path)
            if path_obj.parent:
                return f"Edit({path_obj.parent}/**)"
            return f"Edit({file_path})"

    elif tool_name == 'Write':
        file_path = tool_input.get('file_path', '')
        if file_path:
            path_obj = Path(file_path)
            if path_obj.parent:
                return f"Write({path_obj.parent}/**)"
            return f"Write({file_path})"

    elif tool_name == 'Glob':
        pattern = tool_input.get('pattern', '')
        if pattern:
            return f"Glob({pattern})"

    elif tool_name == 'Grep':
        pattern = tool_input.get('pattern', '')
        if pattern:
            return f"Grep(*)"

    return None


def main():
    """Parse all session files and extract permissions."""
    claude_projects = Path.home() / '.claude' / 'projects'

    if not claude_projects.exists():
        print(f"Error: {claude_projects} does not exist", file=sys.stderr)
        return 1

    print(f"📂 Scanning {claude_projects} for session logs...")

    all_approvals = []
    session_files = list(claude_projects.glob('*/*.jsonl'))

    print(f"   Found {len(session_files)} session files")

    for session_file in session_files:
        approvals = parse_session_file(session_file)
        all_approvals.extend(approvals)

    # Deduplicate and sort by timestamp
    unique_approvals = []
    seen = set()

    for approval in sorted(all_approvals, key=lambda x: x['timestamp']):
        key = (approval['permission'], approval['session_id'])
        if key not in seen:
            seen.add(key)
            unique_approvals.append(approval)

    print(f"   Extracted {len(unique_approvals)} unique permission approvals")

    # Write to learning file
    learning_dir = Path.home() / '.claude' / 'learning'
    learning_dir.mkdir(parents=True, exist_ok=True)

    output_file = learning_dir / 'permission_approvals.jsonl'

    # Backup existing file
    if output_file.exists():
        backup_file = output_file.with_suffix('.jsonl.backup')
        output_file.rename(backup_file)
        print(f"   Backed up existing file to {backup_file}")

    # Write new data
    with open(output_file, 'w') as f:
        for approval in unique_approvals:
            f.write(json.dumps(approval) + '\n')

    print(f"\n✅ Wrote {len(unique_approvals)} approvals to {output_file}")

    # Show top patterns
    from collections import Counter
    pattern_counts = Counter(a['permission'] for a in unique_approvals)

    print(f"\n📊 Top 10 most common permissions:")
    for permission, count in pattern_counts.most_common(10):
        print(f"   {count:3d}× {permission}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
