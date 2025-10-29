"""
Tool categorization mappings for packages.nix.

This module provides hardcoded categorizations for the 122 system tools.
Categories are derived from the structure and comments in packages.nix.

Configuration Philosophy:
- Hardcoded for v1 speed (vs parsing Nix metadata)
- Easy to update when tools are added/removed
- Validated against packages.nix during analysis
"""

from claude_automation.schemas.tool_usage import ToolCategory

# Thresholds for tool usage analysis
DORMANCY_THRESHOLD_DAYS = 90  # Tools unused for 90+ days are dormant
MIN_USAGE_FOR_ADOPTION = 5  # Minimum uses to count as "adopted"

# Tool category mappings
TOOL_CATEGORIES: dict[str, set[str]] = {
    # AI Tools - All AI assistants and code generation tools
    ToolCategory.AI_TOOLS: {
        "claude-code",
        "opencode",
        "cursor",
        "claude-flow",
        "bmad-method",
        "gemini-cli",
        "jules",
        "serena",
        "specify",
        "bpkit",
        "brownfield",
        "whisper-dictation",
        "whisper-cpp",
        "mcp-nixos",
    },
    # Development Tools - Core development utilities
    ToolCategory.DEV_TOOLS: {
        "helix",
        "zed-editor",
        "vscode-fhs",
        "git",
        "gh",
        "nodejs_20",
        "python3",
        "python312",
        "gcc",
        "gnumake",
        "ninja",
        "pkg-config",
        "direnv",
        "devenv",
        "cachix",
        "docker-compose",
        "k9s",
        "podman",
        "httpie",
        "xh",
        "hurl",
        "lizard",
        "radon",
        "jscpd",
        "ruff",
        "shellcheck",
        "shfmt",
        "ast-grep",
        "semgrep",
        "hyperfine",
        "tokei",
        "entr",
        "watchman",
        "just",
        "gitui",
        "lazygit",
        "delta",
        "vhs",
    },
    # Modern CLI Tools - Replacements for traditional Unix tools
    ToolCategory.MODERN_CLI: {
        "eza",
        "bat",
        "ripgrep",
        "rg",
        "fd",
        "fdfind",
        "dust",
        "procs",
        "bottom",
        "btm",
        "duf",
        "dua",
        "zoxide",
        "choose",
        "skim",
        "atuin",
        "mcfly",
        "broot",
        "starship",
        "glow",
    },
    # System Tools - System administration and monitoring
    ToolCategory.SYSTEM_TOOLS: {
        "fastfetch",
        "pydf",
        "gparted",
        "gtop",
        "usbimager",
        "nmap",
        "wireshark",
        "tcpdump",
        "strace",
        "ltrace",
        "cmatrix",
        "tmux",
        "parallel",
    },
    # Productivity - End-user productivity applications
    ToolCategory.PRODUCTIVITY: {
        "google-chrome",
        "obsidian",
        "anki-bin",
        "gimp-with-plugins",
        "vlc",
        "libreoffice",
        "gedit",
        "warp-terminal",
    },
    # Network & Security - Network analysis and security tools
    ToolCategory.NETWORK_SECURITY: {
        "nmap",
        "wireshark",
        "tcpdump",
        "wget",
    },
    # File Management - File browsers, viewers, and processors
    ToolCategory.FILE_MANAGEMENT: {
        "yazi",
        "yaziPlugins.rich-preview",
        "rich-cli",
        "ueberzugpp",
        "file",
        "ffmpegthumbnailer",
        "poppler_utils",
        "imagemagick",
        "eog",
        "feh",
        "sxiv",
        "sioyek",
        "mupdf",
        "okular",
        "file-roller",
        "p7zip",
        "fzf",
        "peco",
        "gum",
    },
    # Database Tools - Database clients and utilities
    ToolCategory.DATABASE_TOOLS: {
        "pgcli",
        "mycli",
        "usql",
        "sqlite",
    },
    # Data Processing - CSV, JSON, YAML processors
    ToolCategory.DEV_TOOLS: {  # Adding to dev-tools
        "jq",
        "jless",
        "yq-go",
        "yq",
        "csvkit",
        "csvlook",
        "miller",
    },
    # Fonts - Font packages (typically not invoked directly)
    ToolCategory.FONTS: {
        "dejavu_fonts",
        "roboto",
        "jetbrains-mono",
        "nerd-fonts.jetbrains-mono",
        "pymupdf4llm",  # PDF processing library
        "python312Packages.pymupdf4llm",
        "python312Packages.lizard",
        "python312Packages.radon",
    },
    # Fish Shell - Shell and plugins
    ToolCategory.DEV_TOOLS: {  # Adding to dev-tools
        "fish",
        "fishPlugins.z",
    },
}

# Flatten all categorized tools for validation
ALL_CATEGORIZED_TOOLS: set[str] = set()
for tools in TOOL_CATEGORIES.values():
    ALL_CATEGORIZED_TOOLS.update(tools)

# Command name aliases (for matching commands to tools)
# Maps: command_name → package_name
COMMAND_TO_TOOL_MAP = {
    # Python variants
    "python3": "python312",
    "python": "python312",
    "py": "python312",
    # Node.js variants
    "node": "nodejs_20",
    "npm": "nodejs_20",
    "npx": "nodejs_20",
    # Ripgrep variants
    "rg": "ripgrep",
    # Fd variants
    "fdfind": "fd",
    # YQ variants
    "yq": "yq-go",
    # KDE packages
    "okular": "kdePackages.okular",
    # Nerd fonts
    "jetbrains-mono-nerd": "nerd-fonts.jetbrains-mono",
    # Python packages
    "lizard": "python312Packages.lizard",
    "radon": "python312Packages.radon",
    "pymupdf4llm": "python312Packages.pymupdf4llm",
    # Yazi plugins
    "rich-preview": "yaziPlugins.rich-preview",
}

# Tools that compete with traditional Unix tools
# Format: modern_tool → traditional_tool
MODERN_VS_TRADITIONAL = {
    "eza": "ls",
    "bat": "cat",
    "ripgrep": "grep",
    "rg": "grep",
    "fd": "find",
    "dust": "du",
    "procs": "ps",
    "bottom": "top",
    "btm": "top",
    "duf": "df",
    "yq-go": "jq",  # For YAML
    "choose": "awk",
}

# Category descriptions for reports
CATEGORY_DESCRIPTIONS = {
    ToolCategory.AI_TOOLS: "AI assistants, code generation, and semantic analysis tools",
    ToolCategory.DEV_TOOLS: "Core development utilities, compilers, and build tools",
    ToolCategory.MODERN_CLI: "Modern replacements for traditional Unix commands",
    ToolCategory.SYSTEM_TOOLS: "System administration and monitoring tools",
    ToolCategory.PRODUCTIVITY: "End-user productivity applications (browsers, editors, media)",
    ToolCategory.NETWORK_SECURITY: "Network analysis and security auditing tools",
    ToolCategory.FILE_MANAGEMENT: "File browsers, viewers, and archive tools",
    ToolCategory.DATABASE_TOOLS: "Database clients with autocompletion",
    ToolCategory.FONTS: "Font packages and supporting libraries",
    ToolCategory.OTHER: "Uncategorized or utility tools",
}


def get_tool_category(tool_name: str) -> ToolCategory:
    """
    Get category for a tool name.

    Args:
        tool_name: Tool package name

    Returns:
        ToolCategory enum value
    """
    for category, tools in TOOL_CATEGORIES.items():
        if tool_name in tools:
            return category
    return ToolCategory.OTHER


def is_modern_alternative(tool_name: str) -> tuple[bool, str | None]:
    """
    Check if tool is a modern alternative to a traditional Unix tool.

    Args:
        tool_name: Tool name to check

    Returns:
        (is_modern, traditional_name) tuple
    """
    traditional = MODERN_VS_TRADITIONAL.get(tool_name)
    return (traditional is not None, traditional)


def get_canonical_tool_name(command: str) -> str:
    """
    Get canonical tool name from command.

    Handles aliases and variations.

    Args:
        command: Command name from shell history

    Returns:
        Canonical tool package name
    """
    # Direct match
    if command in ALL_CATEGORIZED_TOOLS:
        return command

    # Check alias map
    if command in COMMAND_TO_TOOL_MAP:
        return COMMAND_TO_TOOL_MAP[command]

    # Return as-is if no mapping found
    return command
