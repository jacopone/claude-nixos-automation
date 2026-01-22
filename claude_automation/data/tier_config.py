"""
Tier configuration for permission pattern detection.

Defines the tiered learning approach:
- TIER_1_SAFE: Fast learning for read-only tools (low threshold)
- TIER_2_MODERATE: Normal learning for dev tools (medium threshold)
- TIER_3_RISKY: Conservative learning for write operations (higher threshold)

Also defines cross-folder generalization settings.
"""

from typing import TypedDict


class TierSettings(TypedDict):
    """Type definition for tier configuration."""

    min_occurrences: int
    time_window_days: int
    confidence_threshold: float
    description: str


class CrossFolderSettings(TypedDict):
    """Type definition for cross-folder configuration."""

    min_unique_folders: int
    min_total_approvals: int
    confidence_boost: float


# Tiered detection configuration
# Philosophy: If you approve a tool multiple times across different contexts,
# it means you trust that tool - generalize to tool:* pattern
TIER_CONFIG: dict[str, TierSettings] = {
    "TIER_1_SAFE": {
        "min_occurrences": 1,  # Single use proves utility
        "time_window_days": 14,  # Extended window
        "confidence_threshold": 0.3,  # Low bar for safe tools
        "description": "Safe read-only tools",
    },
    "TIER_2_MODERATE": {
        "min_occurrences": 2,  # Just 2 approvals needed
        "time_window_days": 21,  # 3 weeks
        "confidence_threshold": 0.4,  # Moderate threshold
        "description": "Development and testing tools",
    },
    "TIER_3_RISKY": {
        "min_occurrences": 3,  # 3 approvals for risky ops
        "time_window_days": 30,
        "confidence_threshold": 0.5,  # Higher threshold
        "description": "Write operations and risky commands",
    },
}


# Cross-folder generalization config
# If a tool is approved in N different folders, generalize to tool:*
CROSS_FOLDER_CONFIG: CrossFolderSettings = {
    "min_unique_folders": 2,  # 2+ folders triggers generalization
    "min_total_approvals": 3,  # At least 3 total approvals
    "confidence_boost": 0.3,  # Extra confidence for cross-folder patterns
}


def get_tier_for_category(category_tier: str) -> TierSettings:
    """Get tier settings for a category tier name."""
    return TIER_CONFIG.get(category_tier, TIER_CONFIG["TIER_2_MODERATE"])


def is_safe_tier(tier_name: str) -> bool:
    """Check if a tier is considered safe (TIER_1 or CROSS_FOLDER)."""
    return tier_name in ("TIER_1_SAFE", "CROSS_FOLDER")
