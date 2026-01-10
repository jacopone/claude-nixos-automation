#!/usr/bin/env python3
"""
Permission Auto-Learner Hook for Claude Code

This hook analyzes permission approval patterns and automatically generates
permission rules to reduce future prompts.

Workflow:
1. Runs on PreToolUse (every Nth invocation)
2. Analyzes recent approval history using PermissionPatternDetector
3. Generates suggested permission rules
4. Applies high-confidence rules automatically
5. Notifies user about changes

Learning Loop:
- User approves permissions → ApprovalTracker logs to JSONL
- This hook analyzes patterns periodically
- High-confidence patterns → Auto-add to settings.local.json
- Medium-confidence patterns → Suggest to user
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Debug log file
DEBUG_LOG_FILE = "/tmp/permission-auto-learner-log.txt"


def debug_log(message):
    """Append debug message to log file with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(DEBUG_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def get_invocation_counter(session_id):
    """Get and increment invocation counter for this session."""
    counter_file = Path.home() / ".claude" / f"learner_counter_{session_id}.txt"

    try:
        if counter_file.exists():
            count = int(counter_file.read_text().strip())
        else:
            count = 0

        count += 1
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        counter_file.write_text(str(count))

        return count
    except Exception as e:
        debug_log(f"Counter error: {e}")
        return 0


def should_analyze(session_id, check_interval=20):
    """
    Determine if we should run pattern analysis.

    Runs every Nth invocation to avoid performance overhead.

    Args:
        session_id: Current session ID
        check_interval: How often to analyze (default: every 20 tool uses)
                       Lowered from 50 for faster learning feedback

    Returns:
        bool: True if should analyze now
    """
    count = get_invocation_counter(session_id)

    # Run on first invocation and every Nth invocation
    return count == 1 or count % check_interval == 0


def analyze_and_suggest_permissions(project_path):
    """
    Analyze approval patterns and suggest permission rules.

    This is the core learning function that:
    1. Reads approval history from ~/.claude/learning/permission_approvals.jsonl
    2. Detects patterns using PermissionPatternDetector
    3. Generates suggested rules
    4. Returns high-confidence suggestions

    Args:
        project_path: Current project directory

    Returns:
        list: List of suggested permission rules
    """
    try:
        # Import the learning infrastructure
        sys.path.insert(0, str(Path.home() / "claude-nixos-automation"))
        from claude_automation.analyzers import (
            ApprovalTracker,
            PermissionPatternDetector,
        )

        # Initialize trackers with lower thresholds for faster learning
        tracker = ApprovalTracker()
        detector = PermissionPatternDetector(
            approval_tracker=tracker,
            min_occurrences=1,  # Lowered from 3 for faster learning
            confidence_threshold=0.5,  # Lowered from 0.75
        )

        # Detect patterns (last 30 days, project-specific)
        suggestions = detector.detect_patterns(days=30, project_path=project_path)

        debug_log(f"Found {len(suggestions)} pattern suggestions")

        # Filter suggestions with decent confidence (>= 0.6, lowered from 0.8)
        # This allows faster auto-approval of patterns you've approved multiple times
        high_confidence = [s for s in suggestions if s.pattern.confidence >= 0.6]

        return high_confidence

    except Exception as e:
        debug_log(f"Analysis failed: {e}")
        import traceback

        debug_log(traceback.format_exc())
        return []


def is_valid_permission_rule(rule):
    """
    Validate a permission rule follows Claude Code conventions.

    Checks:
    1. Not empty
    2. Not a bare pattern type (e.g., "file_write_operations")
    3. Tool names start with uppercase (e.g., "Bash", "Write", not "bash")
    4. No newlines (multi-line commands are invalid)
    5. No heredoc markers (EOF)
    6. :* wildcard must be at the very end

    Args:
        rule: Permission rule string to validate

    Returns:
        bool: True if valid
    """
    if not rule or not rule.strip():
        return False

    rule = rule.strip()

    # CRITICAL: Reject multi-line permissions (heredocs, complex commands)
    if '\n' in rule or '__NEW_LINE__' in rule:
        debug_log(f"Rejecting multi-line permission: {rule[:50]}...")
        return False

    # CRITICAL: Reject heredoc markers
    if 'EOF' in rule:
        debug_log(f"Rejecting heredoc permission: {rule[:50]}...")
        return False

    # CRITICAL: :* must be at the very end for prefix matching
    if ':*' in rule and not rule.endswith(':*)'):
        # For Bash(cmd:*) the rule ends with :*)
        if rule.startswith('Bash(') and ':*' in rule:
            inner = rule[5:-1] if rule.endswith(')') else rule[5:]
            if not inner.endswith(':*'):
                debug_log(f"Rejecting :* not at end: {rule[:50]}...")
                return False

    # CRITICAL: Reject shell fragments and constructs
    if rule.startswith('Bash('):
        inner = rule[5:-1] if rule.endswith(')') else rule[5:]
        # Shell fragments (standalone shell keywords)
        shell_fragments = ['done', 'fi', 'then', 'else', 'do', 'esac', 'in']
        if inner.strip() in shell_fragments:
            debug_log(f"Rejecting shell fragment: {rule}")
            return False
        # Shell constructs at start
        if re.match(r'^(do |for |while |if |export |then )', inner):
            debug_log(f"Rejecting shell construct: {rule[:50]}...")
            return False

    # Reject bare pattern types (internal category names)
    bare_pattern_types = {
        "file_write_operations",
        "file_operations",
        "git_workflow",
        "git_read_only",
        "git_destructive",
        "test_execution",
        "modern_cli",
        "project_full_access",
        "github_cli",
        "cloud_cli",
        "package_managers",
        "nix_tools",
        "database_cli",
        "network_tools",
        "runtime_tools",
        "posix_filesystem",
        "posix_search",
        "posix_read",
        "shell_utilities",
        "dangerous_operations",
        "pytest",
        "ruff",
    }
    if rule.lower() in bare_pattern_types:
        debug_log(f"Rejecting bare pattern type: {rule}")
        return False

    # MCP tools are valid (mcp__server__tool format)
    if rule.startswith("mcp__"):
        return True

    # WebFetch/WebSearch have special format
    if rule.startswith("WebFetch(") or rule.startswith("WebSearch"):
        return True

    # Standard tools must follow Tool(args) format with uppercase start
    tool_match = re.match(r"^([A-Za-z_]+)\(", rule)
    if tool_match:
        tool_name = tool_match.group(1)
        if not tool_name[0].isupper():
            debug_log(f"Rejecting lowercase tool name: {rule}")
            return False
        return True

    # Unrecognized format - likely invalid
    debug_log(f"Rejecting unrecognized format: {rule}")
    return False


def is_covered_by_existing_pattern(new_rule: str, existing_rules: list) -> bool:
    """
    Check if new_rule is already covered by a broader pattern in existing_rules.

    Boris Cherny style: Don't add specific patterns if a broad wildcard exists.

    Examples:
        - "Bash(git status:*)" is covered by "Bash(git:*)"
        - "Bash(nix flake check:*)" is covered by "Bash(nix:*)"
        - "Bash(git -C /path diff:*)" is covered by "Bash(git:*)"

    Args:
        new_rule: The rule being considered for addition
        existing_rules: List of existing permission rules

    Returns:
        bool: True if new_rule is redundant (already covered by existing pattern)
    """
    if not new_rule or not existing_rules:
        return False

    # Only applies to Bash commands
    if not new_rule.startswith('Bash('):
        return False

    # Extract the command from the new rule
    # Bash(git status:*) -> "git status"
    # Bash(git -C /path diff:*) -> "git -C /path diff"
    match = re.match(r'Bash\(([^:]+):?\*?\)', new_rule)
    if not match:
        return False

    new_cmd = match.group(1).strip()

    # Get the base command (first word)
    # "git status" -> "git"
    # "git -C /path diff" -> "git"
    # "nix flake check" -> "nix"
    base_cmd = new_cmd.split()[0]

    # Check if a broader pattern exists
    broad_pattern = f"Bash({base_cmd}:*)"

    if broad_pattern in existing_rules and broad_pattern != new_rule:
        debug_log(f"Rule '{new_rule}' is covered by broader '{broad_pattern}'")
        return True

    return False


def generate_permission_rules(suggestions):
    """
    Convert pattern suggestions into permission rule strings.

    Args:
        suggestions: List of PatternSuggestion objects

    Returns:
        list: Valid permission rule strings ready to add to settings.local.json
    """
    rules = []

    for suggestion in suggestions:
        rule = suggestion.proposed_rule
        # Split comma-separated rules
        if ", " in rule:
            individual_rules = rule.split(", ")
        else:
            individual_rules = [rule]

        # Validate each rule before adding
        for r in individual_rules:
            r = r.strip()
            if is_valid_permission_rule(r):
                rules.append(r)
            else:
                debug_log(f"Skipping invalid rule: {r}")

    return list(set(rules))  # Deduplicate


def update_settings_file(project_path, new_rules):
    """
    Update .claude/settings.local.json with new permission rules.

    Args:
        project_path: Project directory path
        new_rules: List of permission rule strings to add

    Returns:
        tuple: (success: bool, added_count: int)
    """
    try:
        project_dir = Path(
            project_path.replace("-", "/", 2)
        )  # Convert project_path format
        settings_file = project_dir / ".claude" / "settings.local.json"

        # Create if doesn't exist
        if not settings_file.exists():
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings = {
                "permissions": {"allow": []},
                "_auto_generated_permissions": {
                    "enabled": True,
                    "last_updated": datetime.now().isoformat(),
                    "rules_added": [],
                },
            }
        else:
            with open(settings_file) as f:
                settings = json.load(f)

        # Ensure structure exists
        if "permissions" not in settings:
            settings["permissions"] = {}
        if "allow" not in settings["permissions"]:
            settings["permissions"]["allow"] = []

        # Get existing permissions
        existing = set(settings["permissions"]["allow"])
        existing_list = list(existing)

        # Add new rules (with final validation check)
        added = []
        for rule in new_rules:
            if rule not in existing:
                # Final safety check - reject any rule with newlines/heredocs
                if '\n' in rule or 'EOF' in rule or '__NEW_LINE__' in rule:
                    debug_log(f"Final check rejected: {rule[:50]}...")
                    continue

                # Boris Cherny style: skip if covered by broader pattern
                if is_covered_by_existing_pattern(rule, existing_list):
                    debug_log(f"Skipping redundant rule (covered by broader pattern): {rule}")
                    continue

                settings["permissions"]["allow"].append(rule)
                added.append(rule)

        # Update metadata
        if added:
            if "_auto_generated_permissions" not in settings:
                settings["_auto_generated_permissions"] = {}

            settings["_auto_generated_permissions"]["last_updated"] = (
                datetime.now().isoformat()
            )
            if "rules_added" not in settings["_auto_generated_permissions"]:
                settings["_auto_generated_permissions"]["rules_added"] = []
            settings["_auto_generated_permissions"]["rules_added"].extend(added)

            # Write back to file
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)

            debug_log(f"Added {len(added)} new permission rules to {settings_file}")
            return True, len(added)

        return True, 0

    except Exception as e:
        debug_log(f"Failed to update settings: {e}")
        import traceback

        debug_log(traceback.format_exc())
        return False, 0


def create_notification(project_path, added_count, suggestions):
    """
    Create a notification file for the user about auto-generated permissions.

    Args:
        project_path: Project directory
        added_count: Number of rules added
        suggestions: List of suggestions that were applied
    """
    try:
        project_dir = Path(project_path.replace("-", "/", 2))
        notification_file = project_dir / ".claude" / "permissions_auto_generated.md"

        content = f"""# Auto-Generated Permissions Update

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Rules Added**: {added_count}

## What Happened

The Permission Auto-Learner analyzed your recent approval patterns and detected
high-confidence permission patterns that will reduce future prompts.

## Added Permissions

"""

        for suggestion in suggestions:
            content += f"### {suggestion.description}\n\n"
            content += f"**Confidence**: {suggestion.pattern.confidence:.1%}  \n"
            content += f"**Occurrences**: {suggestion.pattern.occurrences}  \n"
            content += f"**Impact**: {suggestion.impact_estimate}  \n\n"
            content += "**Permissions added**:\n"
            for rule in suggestion.proposed_rule.split(", "):
                content += f"- `{rule}`\n"
            content += "\n"

        content += """---

These permissions have been automatically added to `.claude/settings.local.json`.
You can review and modify them at any time.

To disable auto-generation, set:
```json
{
  "_auto_generated_permissions": {
    "enabled": false
  }
}
```
"""

        notification_file.parent.mkdir(parents=True, exist_ok=True)
        notification_file.write_text(content)

        debug_log(f"Created notification: {notification_file}")

    except Exception as e:
        debug_log(f"Failed to create notification: {e}")


def main():
    """Main hook function."""
    # Check if auto-learning is enabled
    auto_learn_enabled = os.environ.get("ENABLE_PERMISSION_AUTO_LEARN", "1")

    if auto_learn_enabled == "0":
        sys.exit(0)  # Auto-learning disabled

    try:
        # Read input from stdin
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)

        session_id = input_data.get("session_id", "default")
        project_path = input_data.get("project_path", "")

        debug_log(f"Hook triggered: session={session_id}, project={project_path}")

        # Check if we should analyze now (every 50 invocations)
        if not should_analyze(session_id, check_interval=50):
            sys.exit(0)  # Not time to analyze yet

        debug_log("Running pattern analysis...")

        # Analyze approval patterns
        suggestions = analyze_and_suggest_permissions(project_path)

        if not suggestions:
            debug_log("No high-confidence suggestions found")
            sys.exit(0)

        debug_log(f"Found {len(suggestions)} high-confidence suggestions")

        # Generate permission rules
        new_rules = generate_permission_rules(suggestions)

        if not new_rules:
            debug_log("No new rules to add")
            sys.exit(0)

        debug_log(f"Generated {len(new_rules)} permission rules")

        # Update settings.local.json
        success, added_count = update_settings_file(project_path, new_rules)

        if success and added_count > 0:
            debug_log(f"Successfully added {added_count} permission rules")

            # Create notification for user
            create_notification(project_path, added_count, suggestions)

            # Output notification to stderr (visible to Claude)
            notification = f"""
🤖 Permission Auto-Learner

Analyzed recent approval patterns and added {added_count} high-confidence
permission rules to reduce future prompts.

See .claude/permissions_auto_generated.md for details.
"""
            print(notification, file=sys.stderr)

        sys.exit(0)  # Always allow tool to proceed

    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        sys.exit(0)
    except Exception as e:
        debug_log(f"Unexpected error: {e}")
        import traceback

        debug_log(traceback.format_exc())
        sys.exit(0)


if __name__ == "__main__":
    main()
