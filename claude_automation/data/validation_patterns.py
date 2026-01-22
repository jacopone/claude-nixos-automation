"""
Permission validation patterns and constants.

Extracted from permission_auto_learner.is_valid_permission_rule (CCN 22)
to centralize validation data and reduce complexity.
"""

# Content that indicates invalid multi-line or heredoc permissions
INVALID_CONTENT_PATTERNS: tuple[str, ...] = (
    "\n",
    "__NEW_LINE__",
    "EOF",
)

# Shell fragments that should not be standalone permissions
SHELL_FRAGMENTS: frozenset[str] = frozenset({
    "done",
    "fi",
    "then",
    "else",
    "do",
    "esac",
    "in",
})

# Shell constructs that indicate multi-line commands
SHELL_CONSTRUCT_PATTERN = r"^(do |for |while |if |export |then )"

# Internal category names that should not be permission rules
BARE_PATTERN_TYPES: frozenset[str] = frozenset({
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
})

# Valid tool prefixes that bypass standard validation
SPECIAL_TOOL_PREFIXES: tuple[str, ...] = (
    "mcp__",
    "WebFetch(",
    "WebSearch",
)

# Standard tool pattern: Tool(args) with uppercase start
STANDARD_TOOL_PATTERN = r"^([A-Za-z_]+)\("
