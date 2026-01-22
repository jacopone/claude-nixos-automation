"""
Pattern categories for permission detection.

Defines regex patterns and rules for categorizing permission approvals.
Each category maps to a tier for tiered learning.

NOTE: Pattern category keys MUST start with uppercase to pass Claude Code validation
(Claude Code error: "Tool names must start with uppercase")
"""

from typing import TypedDict


class PatternRule(TypedDict):
    """Type definition for pattern detection rules."""

    patterns: list[str]
    description: str
    tier: str


# Pattern categories and their detection rules
PATTERN_CATEGORIES: dict[str, PatternRule] = {
    # === Git Operations ===
    "Git_read_only": {
        "patterns": [r"Bash\(git (status|log|diff|show|branch)"],
        "description": "Read-only git commands",
        "tier": "TIER_1_SAFE",
    },
    "Git_workflow": {
        "patterns": [
            r"Bash\(git (status|log|diff|show|branch|add|commit|push|pull|fetch|stash|checkout|merge|rebase|restore|reset(?! --hard))"
        ],
        "description": "Standard git workflow commands (excludes force/hard operations)",
        "tier": "TIER_2_MODERATE",
    },
    "Git_destructive": {
        "patterns": [
            r"Bash\(git.*(--force|--hard|push -f|push --force|reset --hard)",
        ],
        "description": "Destructive git operations (force push, hard reset)",
        "tier": "TIER_3_RISKY",
    },
    # === Development Tools ===
    "Pytest": {
        "patterns": [r"Bash\(pytest", r"Bash\(python -m pytest"],
        "description": "Pytest test execution",
        "tier": "TIER_1_SAFE",
    },
    "Ruff": {
        "patterns": [r"Bash\(ruff"],
        "description": "Ruff linter/formatter",
        "tier": "TIER_1_SAFE",
    },
    "Modern_cli": {
        "patterns": [
            r"Bash\((fd|eza|bat|rg|dust|procs|btm|tree)",
        ],
        "description": "Modern CLI tools (fd, eza, bat, rg, etc.)",
        "tier": "TIER_1_SAFE",
    },
    # === File Operations ===
    "File_operations": {
        "patterns": [
            r"Read\([^)]+\)",
            r"Glob\([^)]+\)",
        ],
        "description": "File read operations",
        "tier": "TIER_1_SAFE",
    },
    "File_write_operations": {
        "patterns": [
            r"Write\([^)]+\)",
            r"Edit\([^)]+\)",
        ],
        "description": "File write/edit operations",
        "tier": "TIER_2_MODERATE",
    },
    "Test_execution": {
        "patterns": [
            r"Bash\(.*test",
            r"Bash\(npm test",
            r"Bash\(cargo test",
        ],
        "description": "Test execution commands",
        "tier": "TIER_2_MODERATE",
    },
    "Project_full_access": {
        "patterns": [
            r"Read\(/home/[^/]+/[^/]+/\*\*\)",
        ],
        "description": "Full project directory access",
        "tier": "TIER_3_RISKY",
    },
    # === GitHub CLI (gh) ===
    "Github_cli": {
        "patterns": [r"Bash\(gh[\s:]"],
        "description": "GitHub CLI commands (gh pr, gh issue, gh api, etc.)",
        "tier": "TIER_2_MODERATE",
    },
    # === Cloud CLIs ===
    "Cloud_cli": {
        "patterns": [r"Bash\((gcloud|aws|az)[\s:]"],
        "description": "Cloud provider CLIs (GCP, AWS, Azure)",
        "tier": "TIER_3_RISKY",
    },
    # === Package Managers ===
    "Package_managers": {
        "patterns": [r"Bash\((npm|npx|yarn|pnpm|pip|uv|cargo|poetry)[\s:]"],
        "description": "Package manager commands",
        "tier": "TIER_2_MODERATE",
    },
    # === Nix Ecosystem ===
    "Nix_tools": {
        "patterns": [r"Bash\((nix|devenv|nix-shell|nix-build|nix-env)[\s:]"],
        "description": "Nix/NixOS ecosystem tools",
        "tier": "TIER_2_MODERATE",
    },
    # === Database CLIs ===
    "Database_cli": {
        "patterns": [r"Bash\((sqlite3|psql|mysql|mycli|pgcli|usql)[\s:]"],
        "description": "Database CLI tools",
        "tier": "TIER_2_MODERATE",
    },
    # === Network/HTTP Tools ===
    "Network_tools": {
        "patterns": [r"Bash\((curl|wget|xh|httpie)[\s:]"],
        "description": "Network/HTTP client tools",
        "tier": "TIER_2_MODERATE",
    },
    # === Runtime Interpreters ===
    "Runtime_tools": {
        "patterns": [r"Bash\((python3?|node|ruby|go run)[\s:]"],
        "description": "Language runtime interpreters",
        "tier": "TIER_2_MODERATE",
    },
    # === POSIX Filesystem ===
    "Posix_filesystem": {
        "patterns": [r"Bash\((find|ls|mkdir|rmdir|touch|mv|cp|rm(?! -rf))[\s:]"],
        "description": "POSIX filesystem commands (find, ls, mkdir, etc.)",
        "tier": "TIER_2_MODERATE",
    },
    # === POSIX Search/Transform ===
    "Posix_search": {
        "patterns": [r"Bash\((grep|awk|sed|cut|sort|uniq)[\s:]"],
        "description": "POSIX search/transform commands",
        "tier": "TIER_2_MODERATE",
    },
    # === POSIX Read ===
    "Posix_read": {
        "patterns": [r"Bash\((cat|head|tail|less|more|wc)[\s:]"],
        "description": "POSIX file reading/stats commands",
        "tier": "TIER_1_SAFE",
    },
    # === Shell Utilities ===
    "Shell_utilities": {
        "patterns": [
            r"Bash\((echo|printf|sleep|true|false|which|type|cd|pwd)[\s:]"
        ],
        "description": "Shell built-ins and utilities",
        "tier": "TIER_1_SAFE",
    },
    # === Dangerous Operations ===
    "Dangerous_operations": {
        "patterns": [r"Bash\((rm -rf|sudo|chmod 777)[\s:]"],
        "description": "Potentially dangerous operations",
        "tier": "TIER_3_RISKY",
    },
}


# Mapping from category to primary tool names (for wildcard coverage check)
# If git:* exists, skip Git_workflow detection entirely
CATEGORY_TO_TOOLS: dict[str, list[str]] = {
    "Git_read_only": ["git"],
    "Git_workflow": ["git"],
    "Git_destructive": ["git"],
    "Pytest": ["pytest", "python"],
    "Ruff": ["ruff"],
    "Modern_cli": ["fd", "eza", "bat", "rg", "dust", "procs", "btm", "tree"],
    "File_operations": [],  # These use Read/Glob, not Bash
    "File_write_operations": [],  # These use Write/Edit, not Bash
    "Test_execution": ["npm", "pytest", "cargo", "go"],
    "Project_full_access": [],
    "Github_cli": ["gh"],
    "Cloud_cli": ["gcloud", "aws", "az"],
    "Package_managers": ["npm", "pnpm", "pip", "uv", "cargo", "yarn"],
    "Nix_tools": ["nix", "devenv", "nix-shell", "nix-build"],
    "Database_cli": ["sqlite3", "psql", "mysql", "mycli", "pgcli"],
    "Network_tools": ["curl", "wget", "xh", "httpie"],
    "Runtime_tools": ["python", "python3", "node", "ruby", "go"],
    "Posix_filesystem": ["find", "ls", "mkdir", "rmdir", "touch", "mv", "cp"],
    "Posix_search": ["grep", "awk", "sed", "cut", "sort", "uniq"],
    "Posix_read": ["cat", "head", "tail", "less", "more", "wc"],
    "Shell_utilities": ["echo", "printf", "sleep", "which", "type", "cd", "pwd"],
    "Dangerous_operations": [],  # Never auto-skip dangerous ops
}


# Permission rule templates for each pattern category
RULE_TEMPLATES: dict[str, str] = {
    "Git_read_only": "Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git branch:*)",
    "Git_workflow": "Bash(git:*)",
    "Git_destructive": "Bash(git --force:*), Bash(git reset --hard:*)",
    "Pytest": "Bash(pytest:*), Bash(python -m pytest:*)",
    "Ruff": "Bash(ruff:*)",
    "Modern_cli": "Bash(fd:*), Bash(eza:*), Bash(bat:*), Bash(rg:*), Bash(dust:*), Bash(procs:*)",
    "File_operations": "Read(/**), Glob(**)",
    "File_write_operations": "Write(/**), Edit(/**)",
    "Test_execution": "Bash(npm test:*), Bash(pytest:*), Bash(cargo test:*), Bash(go test:*)",
    "Project_full_access": "Read(/home/*/project/**), Write(/home/*/project/**)",
    "Github_cli": "Bash(gh:*)",
    "Cloud_cli": "Bash(gcloud:*), Bash(aws:*), Bash(az:*)",
    "Package_managers": "Bash(npm:*), Bash(pnpm:*), Bash(pip:*), Bash(uv:*)",
    "Nix_tools": "Bash(nix:*), Bash(devenv:*)",
    "Database_cli": "Bash(sqlite3:*), Bash(psql:*), Bash(mycli:*)",
    "Network_tools": "Bash(curl:*), Bash(xh:*)",
    "Runtime_tools": "Bash(python:*), Bash(node:*)",
    "Posix_filesystem": "Bash(find:*), Bash(ls:*), Bash(mkdir:*)",
    "Posix_search": "Bash(grep:*), Bash(awk:*), Bash(sed:*)",
    "Posix_read": "Bash(cat:*), Bash(head:*), Bash(tail:*)",
    "Shell_utilities": "Bash(echo:*), Bash(which:*)",
    "Dangerous_operations": "Bash(rm -rf:*), Bash(sudo:*)",
}


# Edge cases that would still require approval even with category patterns
EDGE_CASES: dict[str, list[str]] = {
    "Git_workflow": ["Bash(git push --force)", "Bash(git reset --hard)"],
    "File_operations": ["Write(/etc/passwd)", "Read(/home/other_user/.ssh)"],
    "Project_full_access": ["Write(/home/user/.ssh/)", "Read(/etc/shadow)"],
}


def get_rule_template(pattern_type: str) -> str:
    """Get the permission rule template for a pattern type."""
    return RULE_TEMPLATES.get(pattern_type, "")


def get_edge_cases(pattern_type: str) -> list[str]:
    """Get edge cases for a pattern type."""
    return EDGE_CASES.get(pattern_type, [])
