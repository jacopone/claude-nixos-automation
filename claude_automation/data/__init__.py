"""
Data module - Pure static configurations with no business logic.

This module contains:
- tool_categories: Tool categorization keywords and mappings
- pattern_categories: Permission pattern detection rules
- tier_config: Tiered learning configuration
- tool_blocklist: Tools that should never be auto-generalized
- validation_patterns: Permission rule validation patterns
"""

from .pattern_categories import CATEGORY_TO_TOOLS, PATTERN_CATEGORIES
from .tier_config import CROSS_FOLDER_CONFIG, TIER_CONFIG
from .tool_blocklist import TOOL_BLOCKLIST
from .tool_categories import (
    TOOL_CATEGORY_KEYWORDS,
    TOOL_NAME_MAPPING,
    categorize_tool_by_keywords,
)
from .validation_patterns import (
    BARE_PATTERN_TYPES,
    INVALID_CONTENT_PATTERNS,
    SHELL_CONSTRUCT_PATTERN,
    SHELL_FRAGMENTS,
    SPECIAL_TOOL_PREFIXES,
    STANDARD_TOOL_PATTERN,
)

__all__ = [
    "PATTERN_CATEGORIES",
    "CATEGORY_TO_TOOLS",
    "TIER_CONFIG",
    "CROSS_FOLDER_CONFIG",
    "TOOL_BLOCKLIST",
    "TOOL_CATEGORY_KEYWORDS",
    "TOOL_NAME_MAPPING",
    "categorize_tool_by_keywords",
    "BARE_PATTERN_TYPES",
    "INVALID_CONTENT_PATTERNS",
    "SHELL_CONSTRUCT_PATTERN",
    "SHELL_FRAGMENTS",
    "SPECIAL_TOOL_PREFIXES",
    "STANDARD_TOOL_PATTERN",
]
