"""
Tool categorization data for Nix parser.

Maps tool names and description keywords to categories.
This replaces the large if/elif chain in nix_parser._categorize_tool.
"""

# Import ToolCategory from schemas to avoid duplication
from ..schemas import ToolCategory

# Keywords that indicate a tool belongs to a category
# Checked in order - first match wins
TOOL_CATEGORY_KEYWORDS: dict[ToolCategory, list[str]] = {
    # AI & MCP tools (check first - highest priority for showcase)
    ToolCategory.AI_MCP_TOOLS: [
        "mcp",
        "agent",
        "ai ",
        "claude",
        "gpt",
        "gemini",
        "anthropic",
        "serena",
        "aider",
        "plandex",
        "jules",
        "coding agent",
        "semantic",
        "model context",
    ],
    # System packages (fonts, python packages, build tools without CLI)
    ToolCategory.SYSTEM_PACKAGES: [
        "font",
        "typeface",
        "python312packages",
        "pythonpackages",
    ],
    # Modern CLI tools (replacements for POSIX commands)
    ToolCategory.CLI_TOOLS: [
        "modern",
        "replacement",
        "alternative",
        "instead of",
        "better than",
        "faster than",
    ],
    # Development tools
    ToolCategory.DEVELOPMENT: [
        "git",
        "code",
        "editor",
        "develop",
        "compile",
        "build",
        "debug",
        "lsp",
        "language",
        "programming",
        "ide",
        "vim",
        "emacs",
        "lint",
        "format",
        "test",
    ],
    # File management tools
    ToolCategory.FILE_MANAGEMENT: [
        "file",
        "find",
        "search",
        "grep",
        "ls",
        "cat",
        "tree",
        "manager",
        "archive",
        "compress",
        "extract",
        "preview",
        "thumbnail",
    ],
    # System monitoring tools
    ToolCategory.SYSTEM_MONITORING: [
        "system",
        "process",
        "monitor",
        "htop",
        "disk",
        "memory",
        "performance",
        "benchmark",
        "stats",
        "usage",
    ],
    # Network and security tools
    ToolCategory.NETWORK_SECURITY: [
        "network",
        "http",
        "wget",
        "curl",
        "nmap",
        "security",
        "firewall",
        "scan",
        "proxy",
        "ssl",
        "tls",
    ],
}


# Explicit tool name to category mapping (highest priority)
TOOL_NAME_MAPPING: dict[str, ToolCategory] = {
    # Modern CLI tools by name
    "fd": ToolCategory.CLI_TOOLS,
    "rg": ToolCategory.CLI_TOOLS,
    "ripgrep": ToolCategory.CLI_TOOLS,
    "bat": ToolCategory.CLI_TOOLS,
    "eza": ToolCategory.CLI_TOOLS,
    "dust": ToolCategory.CLI_TOOLS,
    "duf": ToolCategory.CLI_TOOLS,
    "procs": ToolCategory.CLI_TOOLS,
    "bottom": ToolCategory.CLI_TOOLS,
    "choose": ToolCategory.CLI_TOOLS,
    # AI tools by name
    "claude": ToolCategory.AI_MCP_TOOLS,
    "aider": ToolCategory.AI_MCP_TOOLS,
}


def categorize_tool_by_keywords(
    pkg_name: str, description: str = ""
) -> ToolCategory:
    """
    Categorize a tool based on its name and description.

    Uses a data-driven approach instead of large if/elif chains.
    Complexity reduced from CCN 18 to ~5.

    Args:
        pkg_name: Package name
        description: Package description

    Returns:
        ToolCategory for the package
    """
    # Check explicit name mapping first
    if pkg_name in TOOL_NAME_MAPPING:
        return TOOL_NAME_MAPPING[pkg_name]

    # Check for system packages by name patterns
    if pkg_name.endswith("_fonts") or "Packages." in pkg_name:
        return ToolCategory.SYSTEM_PACKAGES

    # Build search string from name and description
    search_text = f"{pkg_name} {description}".lower()

    # Check keywords in priority order
    for category, keywords in TOOL_CATEGORY_KEYWORDS.items():
        if any(keyword in search_text for keyword in keywords):
            return category

    return ToolCategory.OTHER
