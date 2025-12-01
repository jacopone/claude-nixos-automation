"""
Differential Package Reporter for NixOS.

Compares packages between NixOS generations to track what changed.
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PackageChange:
    """Represents a change to a package between generations."""

    package_name: str
    change_type: str  # "added", "removed", "updated"
    old_version: str | None = None
    new_version: str | None = None
    reason: str | None = None  # From git commit message


@dataclass
class GenerationDiff:
    """Represents differences between two NixOS generations."""

    current_generation: int
    previous_generation: int
    added_packages: list[PackageChange]
    removed_packages: list[PackageChange]
    updated_packages: list[PackageChange]
    timestamp: datetime
    git_commit: str | None = None


class PackageDiffer:
    """Analyzes package differences between NixOS generations."""

    def __init__(self, nixos_config_path: Path | None = None):
        """
        Initialize package differ.

        Args:
            nixos_config_path: Path to nixos-config directory (for git analysis)
        """
        self.nixos_config_path = (
            Path(nixos_config_path)
            if nixos_config_path
            else Path.home() / "nixos-config"
        )

    def get_current_generation(self) -> int:
        """Get the current NixOS generation number."""
        try:
            # Read the system profile symlink
            system_profile = Path("/nix/var/nix/profiles/system")
            if system_profile.exists():
                # Extract generation number from the link target
                # Format: system-123-link
                target = system_profile.resolve()
                match = re.search(r"system-(\d+)-link", str(target))
                if match:
                    return int(match.group(1))
        except Exception as e:
            logger.error(f"Failed to get current generation: {e}")

        return 0

    def get_generation_path(self, generation: int) -> Path | None:
        """
        Get the path to a specific generation.

        Args:
            generation: Generation number

        Returns:
            Path to generation or None if not found
        """
        gen_path = Path(f"/nix/var/nix/profiles/system-{generation}-link")
        if gen_path.exists():
            return gen_path
        return None

    def get_generation_packages(self, generation_path: Path) -> set[str]:
        """
        Get the set of package paths for a generation.

        Args:
            generation_path: Path to the generation

        Returns:
            Set of package store paths
        """
        try:
            result = subprocess.run(
                ["nix-store", "--query", "--references", str(generation_path)],
                capture_output=True,
                text=True,
                check=True,
            )

            # Extract package paths
            packages = set()
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and line.startswith("/nix/store/"):
                    packages.add(line)

            return packages

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to query generation packages: {e}")
            return set()

    def extract_package_info(self, store_path: str) -> tuple[str, str]:
        """
        Extract package name and version from Nix store path.

        Args:
            store_path: Full Nix store path

        Returns:
            Tuple of (package_name, version)
        """
        # Format: /nix/store/hash-name-version
        # Example: /nix/store/abc123-ripgrep-14.0.3
        match = re.search(r"/nix/store/[a-z0-9]+-(.+?)(?:-(\d+[^/]*))?$", store_path)
        if match:
            name = match.group(1)
            version = match.group(2) if match.group(2) else "unknown"
            return name, version
        return store_path, "unknown"

    def compare_generations(
        self,
        current_gen: int | None = None,
        previous_gen: int | None = None,
    ) -> GenerationDiff | None:
        """
        Compare two NixOS generations.

        Args:
            current_gen: Current generation number (default: auto-detect)
            previous_gen: Previous generation number (default: current - 1)

        Returns:
            GenerationDiff object or None if comparison failed
        """
        # Auto-detect current generation if not provided
        if current_gen is None:
            current_gen = self.get_current_generation()
            if current_gen == 0:
                logger.error("Could not determine current generation")
                return None

        # Default to previous generation
        if previous_gen is None:
            previous_gen = current_gen - 1

        logger.info(f"Comparing generation {previous_gen} -> {current_gen}")

        # Get generation paths
        current_path = self.get_generation_path(current_gen)
        previous_path = self.get_generation_path(previous_gen)

        if not current_path:
            logger.error(f"Generation {current_gen} not found")
            return None

        if not previous_path:
            logger.warning(
                f"Generation {previous_gen} not found, comparing against empty set"
            )
            previous_packages = set()
        else:
            previous_packages = self.get_generation_packages(previous_path)

        current_packages = self.get_generation_packages(current_path)

        # Find added, removed, and updated packages
        added = current_packages - previous_packages
        removed = previous_packages - current_packages

        # Detect updates (same package name, different version)
        updated = self._detect_updates(previous_packages, current_packages)

        # Convert to PackageChange objects
        added_changes = []
        for pkg in added:
            name, version = self.extract_package_info(pkg)
            # Skip if this is actually an update
            if not any(u.package_name == name for u in updated):
                added_changes.append(
                    PackageChange(
                        package_name=name,
                        change_type="added",
                        new_version=version,
                    )
                )

        removed_changes = []
        for pkg in removed:
            name, version = self.extract_package_info(pkg)
            # Skip if this is actually an update
            if not any(u.package_name == name for u in updated):
                removed_changes.append(
                    PackageChange(
                        package_name=name,
                        change_type="removed",
                        old_version=version,
                    )
                )

        # Try to extract git commit message for context
        git_commit = self._get_latest_commit()

        return GenerationDiff(
            current_generation=current_gen,
            previous_generation=previous_gen,
            added_packages=added_changes,
            removed_packages=removed_changes,
            updated_packages=updated,
            timestamp=datetime.now(),
            git_commit=git_commit,
        )

    def _detect_updates(
        self,
        previous_packages: set[str],
        current_packages: set[str],
    ) -> list[PackageChange]:
        """
        Detect package updates (same name, different version).

        Args:
            previous_packages: Package paths from previous generation
            current_packages: Package paths from current generation

        Returns:
            List of PackageChange objects for updated packages
        """
        # Build dictionaries of package_name -> (path, version)
        prev_dict = {}
        for pkg in previous_packages:
            name, version = self.extract_package_info(pkg)
            prev_dict[name] = (pkg, version)

        curr_dict = {}
        for pkg in current_packages:
            name, version = self.extract_package_info(pkg)
            curr_dict[name] = (pkg, version)

        # Find packages that exist in both but with different paths/versions
        updates = []
        for name in prev_dict:
            if name in curr_dict:
                prev_path, prev_version = prev_dict[name]
                curr_path, curr_version = curr_dict[name]
                if prev_path != curr_path and prev_version != curr_version:
                    updates.append(
                        PackageChange(
                            package_name=name,
                            change_type="updated",
                            old_version=prev_version,
                            new_version=curr_version,
                        )
                    )

        return updates

    def _get_latest_commit(self) -> str | None:
        """
        Get the latest git commit message from nixos-config.

        Returns:
            Commit message or None
        """
        if not self.nixos_config_path.exists():
            return None

        try:
            result = subprocess.run(
                ["git", "-C", str(self.nixos_config_path), "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def format_diff_markdown(self, diff: GenerationDiff) -> str:
        """
        Format GenerationDiff as markdown for CLAUDE.md.

        Args:
            diff: Generation differences

        Returns:
            Markdown formatted string
        """
        lines = []
        lines.append("## 📦 Recent Package Changes")
        lines.append("")
        lines.append(
            f"**Last rebuild**: Generation {diff.previous_generation} → {diff.current_generation} "
            f"({diff.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
        )
        lines.append("")

        if diff.git_commit:
            # Extract first line of commit message
            first_line = diff.git_commit.split("\n")[0]
            lines.append(f"**Commit**: {first_line}")
            lines.append("")

        total_changes = (
            len(diff.added_packages)
            + len(diff.removed_packages)
            + len(diff.updated_packages)
        )

        if total_changes == 0:
            lines.append("*No package changes since last generation*")
            lines.append("")
            return "\n".join(lines)

        # Added packages
        if diff.added_packages:
            lines.append(f"### ➕ Added ({len(diff.added_packages)})")
            lines.append("")
            for pkg in sorted(diff.added_packages, key=lambda x: x.package_name)[:10]:
                lines.append(f"- `{pkg.package_name}` ({pkg.new_version})")
            if len(diff.added_packages) > 10:
                lines.append(f"  ... and {len(diff.added_packages) - 10} more")
            lines.append("")

        # Removed packages
        if diff.removed_packages:
            lines.append(f"### ➖ Removed ({len(diff.removed_packages)})")
            lines.append("")
            for pkg in sorted(diff.removed_packages, key=lambda x: x.package_name)[:10]:
                lines.append(f"- `{pkg.package_name}` ({pkg.old_version})")
            if len(diff.removed_packages) > 10:
                lines.append(f"  ... and {len(diff.removed_packages) - 10} more")
            lines.append("")

        # Updated packages
        if diff.updated_packages:
            lines.append(f"### ⬆️  Updated ({len(diff.updated_packages)})")
            lines.append("")
            for pkg in sorted(diff.updated_packages, key=lambda x: x.package_name)[:10]:
                lines.append(
                    f"- `{pkg.package_name}`: {pkg.old_version} → {pkg.new_version}"
                )
            if len(diff.updated_packages) > 10:
                lines.append(f"  ... and {len(diff.updated_packages) - 10} more")
            lines.append("")

        lines.append("---")
        lines.append(
            "*This section shows changes from the most recent system rebuild.*"
        )
        lines.append("")

        return "\n".join(lines)


def main():
    """Command-line interface for package differ."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare packages between NixOS generations"
    )
    parser.add_argument(
        "--current",
        type=int,
        help="Current generation number (default: auto-detect)",
    )
    parser.add_argument(
        "--previous",
        type=int,
        help="Previous generation number (default: current - 1)",
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

    differ = PackageDiffer()
    diff = differ.compare_generations(args.current, args.previous)

    if diff:
        print(differ.format_diff_markdown(diff))
    else:
        print("Failed to compare generations")


if __name__ == "__main__":
    main()
