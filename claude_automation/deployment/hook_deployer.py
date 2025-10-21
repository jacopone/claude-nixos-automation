"""
Hook Deployment System for Claude Code.

Deploys hooks from claude_automation/hooks/ to ~/.claude-plugin/hooks/
with proper permissions and configuration.
"""

import json
import logging
import shutil
import stat
from pathlib import Path

logger = logging.getLogger(__name__)


class HookDeployer:
    """Deploys Claude Code hooks to the user's plugin directory."""

    def __init__(
        self,
        source_hooks_dir: Path | None = None,
        target_plugin_dir: Path | None = None,
    ):
        """
        Initialize hook deployer.

        Args:
            source_hooks_dir: Directory containing hooks to deploy
                             (defaults to claude_automation/hooks)
            target_plugin_dir: Target plugin directory
                              (defaults to ~/.claude-plugin)
        """
        if source_hooks_dir is None:
            # Default to claude_automation/hooks relative to this file
            package_root = Path(__file__).parent.parent
            source_hooks_dir = package_root / "hooks"

        if target_plugin_dir is None:
            target_plugin_dir = Path.home() / ".claude-plugin"

        self.source_hooks_dir = Path(source_hooks_dir)
        self.target_plugin_dir = Path(target_plugin_dir)
        self.target_hooks_dir = self.target_plugin_dir / "hooks"

    def deploy(self, dry_run: bool = False) -> dict[str, any]:
        """
        Deploy hooks to Claude Code plugin directory.

        Args:
            dry_run: If True, only show what would be deployed without actually deploying

        Returns:
            Dictionary with deployment results:
            {
                "success": bool,
                "hooks_deployed": list[str],
                "config_updated": bool,
                "errors": list[str]
            }
        """
        results = {
            "success": True,
            "hooks_deployed": [],
            "config_updated": False,
            "errors": [],
        }

        try:
            # Ensure source hooks directory exists
            if not self.source_hooks_dir.exists():
                results["success"] = False
                results["errors"].append(
                    f"Source hooks directory not found: {self.source_hooks_dir}"
                )
                return results

            # Create target directories if they don't exist
            if not dry_run:
                self.target_hooks_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created target hooks directory: {self.target_hooks_dir}")
            else:
                logger.info(
                    f"[DRY RUN] Would create directory: {self.target_hooks_dir}"
                )

            # Deploy Python hook files
            hook_files = list(self.source_hooks_dir.glob("*.py"))
            for hook_file in hook_files:
                try:
                    target_file = self.target_hooks_dir / hook_file.name

                    if not dry_run:
                        shutil.copy2(hook_file, target_file)
                        # Make executable
                        target_file.chmod(
                            target_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
                        )
                        logger.info(f"Deployed hook: {hook_file.name}")
                    else:
                        logger.info(f"[DRY RUN] Would deploy: {hook_file.name}")

                    results["hooks_deployed"].append(hook_file.name)
                except Exception as e:
                    error_msg = f"Failed to deploy {hook_file.name}: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Deploy hooks.json configuration
            hooks_config_source = self.source_hooks_dir / "hooks.json"
            if hooks_config_source.exists():
                try:
                    if not dry_run:
                        self._merge_hooks_config(hooks_config_source)
                        logger.info("Updated hooks.json configuration")
                    else:
                        logger.info("[DRY RUN] Would update hooks.json configuration")

                    results["config_updated"] = True
                except Exception as e:
                    error_msg = f"Failed to update hooks.json: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            else:
                logger.warning(
                    f"No hooks.json found at {hooks_config_source}, skipping config update"
                )

            if results["errors"]:
                results["success"] = False

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Deployment failed: {e}")
            logger.error(f"Deployment failed: {e}")

        return results

    def _merge_hooks_config(self, source_config: Path):
        """
        Merge hooks configuration into target hooks.json.

        If target hooks.json exists, merge new hooks with existing ones.
        If it doesn't exist, copy the source config.

        Args:
            source_config: Path to source hooks.json
        """
        target_config = self.target_plugin_dir / "hooks.json"

        # Load source configuration
        with open(source_config) as f:
            source_data = json.load(f)

        # If target doesn't exist, just copy source
        if not target_config.exists():
            with open(target_config, "w") as f:
                json.dump(source_data, f, indent=2)
            logger.info("Created new hooks.json")
            return

        # Load existing target configuration
        with open(target_config) as f:
            target_data = json.load(f)

        # Merge hooks (source hooks take precedence)
        if "hooks" not in target_data:
            target_data["hooks"] = {}

        for hook_type, hooks_list in source_data.get("hooks", {}).items():
            if hook_type not in target_data["hooks"]:
                target_data["hooks"][hook_type] = hooks_list
            else:
                # Merge hooks lists, avoiding duplicates based on command
                existing_commands = set()
                for existing_hook_group in target_data["hooks"][hook_type]:
                    for hook in existing_hook_group.get("hooks", []):
                        existing_commands.add(hook.get("command", ""))

                # Add new hooks that don't already exist
                for new_hook_group in hooks_list:
                    for new_hook in new_hook_group.get("hooks", []):
                        if new_hook.get("command", "") not in existing_commands:
                            target_data["hooks"][hook_type].append(new_hook_group)
                            break

        # Write merged configuration
        with open(target_config, "w") as f:
            json.dump(target_data, f, indent=2)

        logger.info("Merged hooks configuration")

    def status(self) -> dict[str, any]:
        """
        Check deployment status of hooks.

        Returns:
            Dictionary with status information:
            {
                "deployed": bool,
                "hooks_present": list[str],
                "hooks_missing": list[str],
                "config_present": bool
            }
        """
        status = {
            "deployed": False,
            "hooks_present": [],
            "hooks_missing": [],
            "config_present": False,
        }

        # Check if target directory exists
        if not self.target_hooks_dir.exists():
            # Get list of hook files that should be deployed
            if self.source_hooks_dir.exists():
                source_hooks = [f.name for f in self.source_hooks_dir.glob("*.py")]
                status["hooks_missing"] = source_hooks
            return status

        # Check which hooks are deployed
        if self.source_hooks_dir.exists():
            for hook_file in self.source_hooks_dir.glob("*.py"):
                target_file = self.target_hooks_dir / hook_file.name
                if target_file.exists():
                    status["hooks_present"].append(hook_file.name)
                else:
                    status["hooks_missing"].append(hook_file.name)

        # Check if hooks.json is present
        target_config = self.target_plugin_dir / "hooks.json"
        status["config_present"] = target_config.exists()

        # Consider deployed if at least one hook is present and config exists
        status["deployed"] = (
            len(status["hooks_present"]) > 0 and status["config_present"]
        )

        return status

    def undeploy(self, dry_run: bool = False) -> dict[str, any]:
        """
        Remove deployed hooks from Claude Code plugin directory.

        Args:
            dry_run: If True, only show what would be removed

        Returns:
            Dictionary with results
        """
        results = {"success": True, "hooks_removed": [], "errors": []}

        if not self.target_hooks_dir.exists():
            logger.info("No hooks directory found, nothing to undeploy")
            return results

        # Remove deployed hook files
        if self.source_hooks_dir.exists():
            for hook_file in self.source_hooks_dir.glob("*.py"):
                target_file = self.target_hooks_dir / hook_file.name
                if target_file.exists():
                    try:
                        if not dry_run:
                            target_file.unlink()
                            logger.info(f"Removed hook: {hook_file.name}")
                        else:
                            logger.info(f"[DRY RUN] Would remove: {hook_file.name}")

                        results["hooks_removed"].append(hook_file.name)
                    except Exception as e:
                        error_msg = f"Failed to remove {hook_file.name}: {e}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)

        if results["errors"]:
            results["success"] = False

        return results


def main():
    """Command-line interface for hook deployment."""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Claude Code hooks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deployed without actually deploying",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check deployment status",
    )
    parser.add_argument(
        "--undeploy",
        action="store_true",
        help="Remove deployed hooks",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    deployer = HookDeployer()

    if args.status:
        status = deployer.status()
        print("\n📊 Hook Deployment Status")
        print("=" * 50)
        print(f"Deployed: {'✓' if status['deployed'] else '✗'}")
        print(f"\nHooks present: {len(status['hooks_present'])}")
        for hook in status['hooks_present']:
            print(f"  ✓ {hook}")
        if status['hooks_missing']:
            print(f"\nHooks missing: {len(status['hooks_missing'])}")
            for hook in status['hooks_missing']:
                print(f"  ✗ {hook}")
        print(f"\nConfiguration: {'✓' if status['config_present'] else '✗'}")
        return

    if args.undeploy:
        print("\n🗑️  Undeploying hooks...")
        results = deployer.undeploy(dry_run=args.dry_run)
        if results["success"]:
            print(f"✓ Successfully removed {len(results['hooks_removed'])} hooks")
        else:
            print("✗ Undeployment completed with errors:")
            for error in results["errors"]:
                print(f"  - {error}")
        return

    # Deploy hooks
    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n🚀 {mode}Deploying Claude Code hooks...")

    results = deployer.deploy(dry_run=args.dry_run)

    if results["success"]:
        print(f"✓ Successfully deployed {len(results['hooks_deployed'])} hooks:")
        for hook in results["hooks_deployed"]:
            print(f"  - {hook}")
        if results["config_updated"]:
            print("✓ Updated hooks.json configuration")
        print(f"\nTarget directory: {deployer.target_hooks_dir}")
    else:
        print("✗ Deployment completed with errors:")
        for error in results["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
