"""
Policy version tracking for detecting new policies.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from .schemas_policies import PolicyVersionInfo

logger = logging.getLogger(__name__)


class PolicyVersionTracker:
    """Tracks policy versions to detect new additions."""

    def __init__(self, version_file: Path | None = None):
        """Initialize version tracker."""
        self.version_file = version_file or (
            Path.home() / ".claude" / ".policy-version.json"
        )

    def load_previous_version(self) -> PolicyVersionInfo | None:
        """Load previous version information."""
        if not self.version_file.exists():
            return None

        try:
            with open(self.version_file) as f:
                data = json.load(f)
                return PolicyVersionInfo(**data)
        except Exception as e:
            logger.warning(f"Failed to load version file: {e}")
            return None

    def save_current_version(
        self, policy_names: list[str], new_policies: list[str] | None = None
    ) -> None:
        """Save current version information."""
        version_info = PolicyVersionInfo(
            last_updated=datetime.now(),
            policies_count=len(policy_names),
            new_since_last=new_policies or [],
            version="2.0",
        )

        try:
            self.version_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.version_file, "w") as f:
                json.dump(version_info.model_dump(mode="json"), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save version file: {e}")

    def detect_new_policies(
        self, current_policies: dict[str, list[dict]]
    ) -> set[str]:
        """
        Detect which policies are new since last update.

        Returns set of policy names that are new.
        """
        # Get all current policy names
        current_names = set()
        for category_policies in current_policies.values():
            for policy in category_policies:
                current_names.add(policy["name"])

        # Load previous version
        prev_version = self.load_previous_version()
        if not prev_version:
            # First run - nothing is new
            self.save_current_version(list(current_names), [])
            return set()

        # Load previous policy names from version file
        # (We need to track this separately in the future)
        # For now, we'll detect based on the previous run
        new_policies = set()

        # Simple heuristic: policies marked as "scraped" are potentially new
        for category_policies in current_policies.values():
            for policy in category_policies:
                if policy.get("scraped", False):
                    # This was scraped, so it could be new
                    new_policies.add(policy["name"])

        # Save current state
        self.save_current_version(list(current_names), list(new_policies))

        return new_policies

    def mark_policy_as_new(
        self, policy: dict, new_policies: set[str]
    ) -> dict:
        """
        Add 'is_new' flag to policy if it's in the new set.

        Returns the policy dict with is_new flag added.
        """
        policy_copy = policy.copy()
        policy_copy["is_new"] = policy["name"] in new_policies
        return policy_copy
