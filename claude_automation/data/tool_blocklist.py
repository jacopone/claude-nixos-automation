"""
Tool blocklist - Tools that should NEVER be auto-generalized to tool:*.

These are either shell constructs, generic invocations, or too broad to be safe.
The permission pattern detector uses this to skip false positives.
"""

TOOL_BLOCKLIST: frozenset[str] = frozenset({
    # Shell invocations (would match ANY command)
    "bash",
    "sh",
    "zsh",
    "fish",
    "dash",
    "ksh",
    "csh",
    "tcsh",
    # Shell control flow keywords (parsed as "tools" by regex)
    "if",
    "then",
    "else",
    "elif",
    "fi",
    "for",
    "while",
    "until",
    "do",
    "done",
    "case",
    "esac",
    "select",
    "in",
    # Other shell constructs
    "function",
    "time",
    "coproc",
    "local",
    "export",
    "source",
    "eval",
    "exec",
    # Single-letter "commands" (likely false positives from variable names)
    *list("abcdefghijklmnopqrstuvwxyz"),
    # Common variable prefixes that aren't tools
    "var",
    "tmp",
    "env",
    "set",
    "let",
    "new",
    "old",
    "the",
    "get",
    "put",
})
