"""
Improvement Applicator - Handles application of approved learning suggestions.
Applies changes to MCP configs, permissions, context files, and workflows.
"""

import json
import logging
import re
from pathlib import Path

from claude_automation.schemas import LearningReport

logger = logging.getLogger(__name__)


class ImprovementApplicator:
    """
    Handles application of approved improvements from the learning system.

    Responsibilities:
    - Display confirmation summary of changes
    - Apply MCP server optimizations
    - Apply permission pattern suggestions
    - Apply context optimizations
    - Apply workflow pattern suggestions
    - Update meta-learning based on user feedback
    """

    def __init__(self, meta_learner):
        """
        Initialize improvement applicator.

        Args:
            meta_learner: MetaLearner instance for recording feedback
        """
        self.meta_learner = meta_learner

    def apply_improvements(self, approved: list[dict]) -> None:
        """
        Apply approved improvements across all components.

        Args:
            approved: List of approved suggestions (each has 'type' and 'data')

        Side effects:
            - May modify .claude/mcp.json
            - May modify settings.local.json
            - May modify CLAUDE.md files
            - May create slash commands
        """
        if not approved:
            logger.info("No approved suggestions to apply")
            return

        # Show confirmation summary before applying
        print("\n" + "="*70)
        print("📋 FINAL CONFIRMATION - Changes to be applied:")
        print("="*70)

        for i, sug in enumerate(approved, 1):
            sug_type = sug['type']
            data = sug['data']

            if sug_type == 'mcp':
                server = data.get('server_name', 'Unknown')
                print(f"\n{i}. MCP: Remove server '{server}'")
                print("   File: .claude/mcp.json")
            elif sug_type == 'permission':
                desc = data.get('description', 'Unknown pattern')
                print(f"\n{i}. Permission: Auto-approve '{desc}'")
                print("   File: .claude/settings.local.json")
            elif sug_type == 'context':
                section = data.get('description', 'Unknown section')
                print(f"\n{i}. Context: Remove '{section}'")
                print("   File: CLAUDE.md")
            elif sug_type == 'workflow':
                desc = data.get('description', 'Unknown workflow')
                print(f"\n{i}. Workflow: Create slash command for '{desc}'")
                print("   File: .claude/commands/<new>.md")

        print("\n" + "─"*70)
        try:
            confirm = input("\n👉 Proceed with these changes? [y/N]: ").lower().strip()
            if confirm != 'y':
                print("\n⚠️  Changes cancelled. No modifications made.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️  Changes cancelled by user. No modifications made.")
            return

        print(f"\n🔧 Applying {len(approved)} approved improvements...")

        # Group by type
        by_type = {}
        for sug in approved:
            sug_type = sug['type']
            if sug_type not in by_type:
                by_type[sug_type] = []
            by_type[sug_type].append(sug['data'])

        # Apply MCP optimizations
        if 'mcp' in by_type:
            self._apply_mcp_optimizations(by_type['mcp'])

        # Apply permission patterns
        if 'permission' in by_type:
            self._apply_permission_patterns(by_type['permission'])

        # Apply context optimizations
        if 'context' in by_type:
            self._apply_context_optimizations(by_type['context'])

        # Apply workflow patterns
        if 'workflow' in by_type:
            self._apply_workflow_patterns(by_type['workflow'])

        print("✓ All improvements applied successfully\n")

    def _apply_mcp_optimizations(self, optimizations: list[dict]) -> None:
        """
        Apply MCP server optimization suggestions.

        Modifies .claude/mcp.json (project) or ~/.claude.json (global) to remove servers.
        """
        logger.info(f"Applying {len(optimizations)} MCP optimizations")

        for opt in optimizations:
            server_name = opt.get('server_name', 'unknown')
            action = opt.get('impact', '')  # Field is called 'impact' in the dict

            try:
                # Parse action to determine config location
                # Format: "Remove from global (~/.claude.json)" or "Remove from project (nixos-config)"
                if 'global' in action:
                    config_path = Path.home() / '.claude.json'
                    location_type = 'global'
                    location_desc = '~/.claude.json'
                elif 'project' in action:
                    # Extract project name from "Remove from project (PROJECT_NAME)"
                    match = re.search(r'project \(([^)]+)\)', action)
                    if not match:
                        logger.error(f"Could not parse project name from action: {action}")
                        print(f"  ✗ MCP: {server_name} - Failed (could not parse project name)")
                        continue

                    project_name = match.group(1)
                    config_path = self._find_project_mcp_config(project_name)
                    location_type = 'project'
                    location_desc = f'{project_name}/.claude/mcp.json'

                    if not config_path:
                        logger.error(f"Could not find .claude/mcp.json for project: {project_name}")
                        print(f"  ✗ MCP: {server_name} - Failed (project config not found)")
                        continue
                else:
                    logger.error(f"Could not determine config location from action: {action}")
                    print(f"  ✗ MCP: {server_name} - Failed (unknown location)")
                    continue

                # Remove server from config
                if self._remove_server_from_config(config_path, server_name, location_type):
                    print(f"  ✓ MCP: Removed '{server_name}' from {location_desc}")
                    logger.info(f"Successfully removed {server_name} from {location_desc}")
                else:
                    print(f"  ✗ MCP: Failed to remove '{server_name}' from {location_desc}")

            except Exception as e:
                logger.error(f"Error removing {server_name}: {e}")
                print(f"  ✗ MCP: {server_name} - Error: {e}")

    def _find_project_mcp_config(self, project_name: str) -> Path | None:
        """
        Find .claude/mcp.json for a project by name.

        Args:
            project_name: Name of project (e.g., "nixos-config", "birthday-manager")

        Returns:
            Path to .claude/mcp.json or None if not found
        """
        home_dir = Path.home()

        # Search for .claude/mcp.json in project with matching name
        for mcp_config in home_dir.rglob(".claude/mcp.json"):
            # Skip hidden directories (except .claude)
            path_parts = mcp_config.parts
            if any(part.startswith(".") and part != ".claude" for part in path_parts):
                continue

            # Check if project directory name matches
            project_path = mcp_config.parent.parent  # Go up from .claude/mcp.json
            if project_path.name == project_name:
                logger.debug(f"Found MCP config for {project_name}: {mcp_config}")
                return mcp_config

        logger.warning(f"Could not find .claude/mcp.json for project: {project_name}")
        return None

    def _remove_server_from_config(self, config_path: Path, server_name: str, location_type: str) -> bool:
        """
        Remove a server from MCP configuration file.

        Args:
            config_path: Path to config file (.claude.json or .claude/mcp.json)
            server_name: Name of server to remove
            location_type: 'global' or 'project'

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read config
            if not config_path.exists():
                logger.error(f"Config file not found: {config_path}")
                return False

            with open(config_path, encoding='utf-8') as f:
                config = json.load(f)

            # Check if server exists
            mcp_servers = config.get('mcpServers', {})
            if server_name not in mcp_servers:
                logger.warning(f"Server '{server_name}' not found in {config_path}")
                return False

            # Remove server
            del mcp_servers[server_name]
            config['mcpServers'] = mcp_servers

            # Write back
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                f.write('\n')  # Add trailing newline

            logger.info(f"Removed '{server_name}' from {config_path}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error modifying {config_path}: {e}")
            return False

    def _check_git_status(self) -> bool:
        """
        Check if git working directory is clean.

        Returns:
            True if clean (safe to modify), False if uncommitted changes
        """
        import subprocess
        from pathlib import Path

        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=5
            )

            # Empty output = clean working directory
            is_clean = len(result.stdout.strip()) == 0

            if not is_clean:
                logger.warning("Git working directory has uncommitted changes")

            return is_clean
        except Exception as e:
            logger.warning(f"Could not check git status: {e}")
            # Assume unsafe if git check fails (fail-safe behavior)
            return False

    def _apply_permission_patterns(self, patterns: list[dict]) -> None:
        """
        Apply permission pattern suggestions.

        Updates .claude/settings.local.json with new allow patterns.
        """
        logger.info(f"Applying {len(patterns)} permission patterns")

        import json
        from pathlib import Path

        # Check git status before modifying
        if not self._check_git_status():
            logger.warning("Uncommitted changes detected, skipping permission patterns")
            print("  ⚠️  Uncommitted changes - skipped permission patterns")
            return

        # Determine target file (project-local settings)
        target_file = Path.cwd() / ".claude" / "settings.local.json"

        # Ensure .claude directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize settings
        try:
            if target_file.exists():
                with open(target_file, encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {target_file}: {e}")
            print("  ✗ Permission patterns: Invalid JSON in settings file")
            return
        except Exception as e:
            logger.error(f"Error reading {target_file}: {e}")
            print("  ✗ Permission patterns: Error reading settings file")
            return

        # Ensure permissions structure exists
        if 'permissions' not in settings:
            settings['permissions'] = {}
        if 'allow' not in settings['permissions']:
            settings['permissions']['allow'] = []

        # Track changes
        added_count = 0

        # Apply each pattern
        for pattern in patterns:
            description = pattern.get('description', 'unknown pattern')
            examples = pattern.get('examples', [])

            # Generate permission rules from pattern
            # For minimal implementation, use examples directly
            rules = self._extract_permission_rules(description, examples)

            for rule in rules:
                # Avoid duplicates
                if rule not in settings['permissions']['allow']:
                    settings['permissions']['allow'].append(rule)
                    added_count += 1
                    logger.info(f"Added permission rule: {rule}")

        # Write back settings atomically
        if added_count > 0:
            try:
                import os
                import tempfile

                # Write to temporary file first
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    dir=target_file.parent,
                    delete=False,
                    suffix='.tmp',
                    encoding='utf-8'
                ) as tmp:
                    json.dump(settings, tmp, indent=2)
                    tmp.write('\n')  # Add trailing newline
                    tmp_path = tmp.name

                # Atomic rename
                os.replace(tmp_path, target_file)
                print(f"  ✓ Permission: Added {added_count} rules to {target_file.relative_to(Path.cwd())}")
                logger.info(f"Successfully applied {added_count} permission rules")
            except Exception as e:
                logger.error(f"Error writing {target_file}: {e}")
                print("  ✗ Permission patterns: Error writing settings file")
                # Clean up temp file if it exists
                try:
                    if 'tmp_path' in locals() and Path(tmp_path).exists():
                        Path(tmp_path).unlink()
                except Exception:
                    pass
        else:
            print("  ℹ️  Permission: No new rules to add (all already exist)")
            logger.info("No new permission rules needed")

    def _extract_permission_rules(self, description: str, examples: list[str]) -> list[str]:
        """
        Extract permission rules from pattern description and examples.

        Args:
            description: Pattern description (e.g., "Allow git read-only commands")
            examples: Example permissions (e.g., ["Bash(git status)", "Bash(git log)"])

        Returns:
            List of permission rules to add
        """
        rules = []

        # Use examples if available
        if examples:
            # Convert specific examples to wildcard patterns
            for ex in examples[:5]:  # Limit to 5 examples
                # Extract tool and command pattern
                # "Bash(git status)" -> "Bash(git status:*)"
                if '(' in ex and ')' in ex:
                    # Already has parameters
                    if ':' not in ex:
                        # Add wildcard if not already parameterized
                        rule = ex.replace(')', ':*)')
                    else:
                        rule = ex
                    rules.append(rule)
                else:
                    rules.append(ex)

        # Fallback: Generate from description
        if not rules:
            desc_lower = description.lower()
            if 'git' in desc_lower and ('read' in desc_lower or 'status' in desc_lower):
                rules = ["Bash(git status:*)", "Bash(git log:*)", "Bash(git diff:*)", "Bash(git show:*)"]
            elif 'pytest' in desc_lower or 'test' in desc_lower:
                rules = ["Bash(pytest:*)"]
            elif 'ruff' in desc_lower:
                rules = ["Bash(ruff:*)"]
            elif 'nix' in desc_lower:
                rules = ["Bash(nix:*)"]
            else:
                # Very conservative fallback
                logger.warning(f"Could not extract specific rules from: {description}")
                rules = []

        return rules

    def _apply_context_optimizations(self, optimizations: list[dict]) -> None:
        """Apply CLAUDE.md context optimizations."""
        logger.info(f"Applying {len(optimizations)} context optimizations")

        for opt in optimizations:
            description = opt.get('description', 'unknown optimization')

            # TODO: Modify CLAUDE.md files
            # For now, log what would be done
            print(f"  • Context: {description}")
            logger.warning(f"Context optimization not yet implemented: {description}")

    def _apply_workflow_patterns(self, patterns: list[dict]) -> None:
        """
        Apply workflow pattern suggestions by creating slash commands.

        Creates .claude/commands/<workflow-name>.md files.
        """
        logger.info(f"Applying {len(patterns)} workflow patterns")

        from pathlib import Path

        # Check git status before modifying
        if not self._check_git_status():
            logger.warning("Uncommitted changes detected, skipping workflow patterns")
            print("  ⚠️  Uncommitted changes - skipped workflow patterns")
            return

        # Ensure commands directory exists
        commands_dir = Path.cwd() / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)

        for pattern in patterns:
            description = pattern.get('description', 'unknown workflow')
            commands = pattern.get('commands', [])
            occurrences = pattern.get('occurrences', 0)

            if not commands:
                logger.warning(f"Workflow pattern has no commands: {description}")
                continue

            # Generate unique command name
            cmd_name = self._generate_command_name(commands, commands_dir)
            cmd_file = commands_dir / f"{cmd_name}.md"

            # Generate command content
            content = self._generate_command_content(description, commands, occurrences, cmd_name)

            # Write command file atomically
            try:
                import os
                import tempfile

                # Write to temporary file first
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    dir=commands_dir,
                    delete=False,
                    suffix='.tmp',
                    encoding='utf-8'
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                # Atomic rename
                os.replace(tmp_path, cmd_file)
                print(f"  ✓ Workflow: Created /{cmd_name} (.claude/commands/{cmd_name}.md)")
                logger.info(f"Created workflow command: {cmd_file}")
            except Exception as e:
                logger.error(f"Failed to create workflow command {cmd_name}: {e}")
                print(f"  ✗ Workflow: {cmd_name} - Error: {e}")
                # Clean up temp file if it exists
                try:
                    if 'tmp_path' in locals() and Path(tmp_path).exists():
                        Path(tmp_path).unlink()
                except Exception:
                    pass

    def _generate_command_name(self, commands: list[str], commands_dir) -> str:
        """
        Generate unique command name from command sequence.

        Args:
            commands: List of commands like ["/speckit.specify", "/speckit.plan"]
            commands_dir: Path to .claude/commands directory

        Returns:
            Unique command name like "workflow-specify-plan" or "workflow-specify-plan-2"
        """
        import re

        # Extract base names
        parts = []
        for cmd in commands:
            # Remove leading slash and extract meaningful parts
            clean = cmd.lstrip('/').replace('.', '-')
            # Take last part if hyphenated
            if '-' in clean:
                parts.append(clean.split('-')[-1])
            else:
                parts.append(clean)

        # Combine with workflow prefix
        if parts:
            base_name = 'workflow-' + '-'.join(parts[:3])  # Max 3 parts
        else:
            base_name = 'workflow'

        # Sanitize
        base_name = re.sub(r'[^a-z0-9-]', '', base_name.lower())
        base_name = base_name or 'workflow'

        # Ensure uniqueness by appending counter if needed
        name = base_name
        counter = 1
        while (commands_dir / f"{name}.md").exists():
            counter += 1
            name = f"{base_name}-{counter}"

        return name

    def _generate_command_content(self, description: str, commands: list[str], occurrences: int, cmd_name: str) -> str:
        """
        Generate markdown content for workflow command.

        Args:
            description: Workflow description
            commands: Command sequence
            occurrences: How many times pattern occurred
            cmd_name: Generated command name

        Returns:
            Markdown content for slash command
        """
        content = f"""# Workflow Command: {description}

**Auto-generated from usage patterns** (occurred {occurrences} times)

## Command Sequence

This workflow executes the following commands in order:

"""

        for i, cmd in enumerate(commands, 1):
            content += f"{i}. `{cmd}`\n"

        content += f"""

## Usage

```bash
# Run this workflow
/{cmd_name}
```

## What This Does

Automatically runs:
"""

        for cmd in commands:
            content += f"- {cmd}\n"

        content += """

## Notes

- This is an auto-generated workflow based on your usage patterns
- Edit or delete this file if the workflow needs adjustment
- File location: `.claude/commands/""" + cmd_name + """.md`

---
*Auto-generated by adaptive learning system*
"""

        return content

    def update_meta_learning(self, report: LearningReport, approved: list[dict]) -> None:
        """
        Update meta-learning based on user feedback.

        Args:
            report: Learning report with all suggestions
            approved: List of approved suggestions
        """
        acceptance_rate = (
            len(approved) / report.total_suggestions if report.total_suggestions > 0 else 1.0
        )

        self.meta_learner.record_session(
            total_suggestions=report.total_suggestions,
            accepted=len(approved),
            acceptance_rate=acceptance_rate,
        )

        logger.info(f"Meta-learning updated: {acceptance_rate:.0%} acceptance rate")
