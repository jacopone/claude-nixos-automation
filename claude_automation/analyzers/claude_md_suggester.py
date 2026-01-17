"""
CLAUDE.md Suggestion Engine (Two-Stage Pipeline).

Stage 1: Regex extraction of candidate instruction patterns from session logs
Stage 2: Claude API analysis to filter, understand context, and format suggestions

Detects patterns like:
- "always do X"
- "never do Y"
- "remember to Z"
- Corrections: "no, use X instead"
"""

import json
import logging
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from ..schemas.suggestions import (
    ClaudeMdSuggestion,
    SuggestionConfig,
    SuggestionReport,
    SuggestionScope,
)
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class ClaudeMdSuggester(BaseAnalyzer):
    """
    Two-stage suggestion engine for CLAUDE.md additions.

    Stage 1: Regex-based candidate extraction (loose matching)
    Stage 2: Claude API analysis for filtering and formatting
    """

    # Loose regex patterns to capture candidates (Stage 1)
    # These intentionally match broadly - Claude will filter in Stage 2
    CANDIDATE_PATTERNS = [
        # Direct instructions
        r"(?:always|never|remember|don't forget)\s+(.{15,200}?)(?:\.|$|!|\?)",
        # Corrections
        r"(?:no,?\s+)?(?:use|do|run|try)\s+(.{10,150}?)\s+instead",
        r"actually,?\s+(.{15,200}?)(?:\.|$|!|\?)",
        # Preferences
        r"i (?:always )?prefer\s+(.{10,150}?)(?:\.|$|!|\?)",
        r"please (?:always )?(?:use|do|make sure)\s+(.{10,150}?)(?:\.|$|!|\?)",
        # Reminders
        r"make sure (?:to )?(.{15,200}?)(?:\.|$|!|\?)",
        r"keep in mind (?:that )?(.{15,200}?)(?:\.|$|!|\?)",
        # Strong preferences
        r"you should (?:always |never )?(.{15,200}?)(?:\.|$|!|\?)",
    ]

    # Claude model to use for Stage 2 analysis
    CLAUDE_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        claude_dir: Path | None = None,
        config: SuggestionConfig | None = None,
        **kwargs,
    ):
        """
        Initialize suggester.

        Args:
            claude_dir: Path to ~/.claude directory
            config: Suggestion configuration
        """
        super().__init__(**kwargs)
        self.claude_dir = claude_dir or Path.home() / ".claude"
        self.config = config or SuggestionConfig()
        self._client: Anthropic | None = None

    def _get_client(self) -> Anthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable required for Stage 2 analysis"
                )
            self._client = Anthropic(api_key=api_key)
        return self._client

    def _get_analysis_method_name(self) -> str:
        return "analyze_sessions"

    def analyze_sessions(self, days: int | None = None) -> SuggestionReport:
        """
        Analyze recent sessions for instruction patterns using two-stage pipeline.

        Args:
            days: Number of days to analyze (default from config)

        Returns:
            SuggestionReport with Claude-analyzed suggestions
        """
        days = days or self.config.analysis_period_days
        cutoff = datetime.now() - timedelta(days=days)

        # Stage 1: Find session files and extract candidates
        sessions = self._find_session_files(cutoff)
        logger.info(f"Found {len(sessions)} sessions to analyze from last {days} days")

        # Extract candidate patterns from all sessions
        all_candidates: list[dict[str, Any]] = []
        for session_file in sessions:
            candidates = self._extract_candidates_from_session(session_file)
            all_candidates.extend(candidates)

        logger.info(f"Stage 1: Extracted {len(all_candidates)} candidate patterns")

        if not all_candidates:
            return SuggestionReport(
                analysis_period_days=days,
                sessions_analyzed=len(sessions),
                global_suggestions=[],
                project_suggestions={},
                total_suggestions=0,
            )

        # Stage 2: Send candidates to Claude for analysis
        suggestions = self._analyze_with_claude(all_candidates)
        logger.info(f"Stage 2: Claude identified {len(suggestions)} valid suggestions")

        # Separate into global and project-specific
        global_suggestions = [s for s in suggestions if s.scope == SuggestionScope.GLOBAL]
        project_suggestions: dict[str, list[ClaudeMdSuggestion]] = defaultdict(list)
        for s in suggestions:
            if s.scope == SuggestionScope.PROJECT and s.projects:
                for project in s.projects:
                    project_suggestions[project].append(s)

        return SuggestionReport(
            analysis_period_days=days,
            sessions_analyzed=len(sessions),
            global_suggestions=global_suggestions,
            project_suggestions=dict(project_suggestions),
            total_suggestions=len(suggestions),
        )

    def _find_session_files(self, cutoff: datetime) -> list[Path]:
        """Find session JSONL files modified after cutoff."""
        sessions = []
        projects_dir = self.claude_dir / "projects"

        if not projects_dir.exists():
            logger.warning(f"Projects directory not found: {projects_dir}")
            return sessions

        # Find all .jsonl files (not .lifecycle.json)
        for jsonl_file in projects_dir.rglob("*.jsonl"):
            if ".lifecycle" in jsonl_file.name:
                continue

            try:
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
                if mtime >= cutoff:
                    sessions.append(jsonl_file)
            except OSError:
                continue

        return sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)

    def _extract_candidates_from_session(
        self, session_file: Path
    ) -> list[dict[str, Any]]:
        """
        Stage 1: Extract candidate instruction patterns from a session.

        Returns raw candidates with full context for Claude to analyze.
        """
        candidates = []
        project_path = self._get_project_from_session_path(session_file)
        session_id = session_file.stem

        try:
            with open(session_file, encoding="utf-8") as f:
                messages = []
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if self._is_user_message(entry):
                            text = self._extract_message_text(entry)
                            if text and len(text) > 20:  # Skip very short messages
                                messages.append(text)
                    except json.JSONDecodeError:
                        continue

                # Look for instruction patterns in user messages
                for msg_idx, text in enumerate(messages):
                    text_lower = text.lower()

                    # Apply candidate patterns
                    for pattern in self.CANDIDATE_PATTERNS:
                        matches = re.findall(pattern, text_lower, re.IGNORECASE)
                        for match in matches:
                            if len(match.strip()) >= 15:  # Minimum viable instruction
                                candidates.append({
                                    "raw_text": match.strip(),
                                    "full_message": text[:500],  # Context (truncated)
                                    "project_path": project_path,
                                    "session_id": session_id,
                                    "message_index": msg_idx,
                                })

        except (OSError, UnicodeDecodeError):
            logger.warning(f"Failed to read session {session_file}: e")

        return candidates

    def _is_user_message(self, entry: dict[str, Any]) -> bool:
        """Check if JSONL entry is a user message."""
        if entry.get("type") == "user":
            return True
        if entry.get("role") == "user":
            return True
        return False

    def _extract_message_text(self, entry: dict[str, Any]) -> str:
        """Extract text content from a message entry."""
        if "message" in entry:
            msg = entry["message"]
            if isinstance(msg, str):
                return msg
            if isinstance(msg, dict) and "content" in msg:
                content = msg["content"]
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    texts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            texts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            texts.append(block)
                    return " ".join(texts)

        if "content" in entry:
            content = entry["content"]
            if isinstance(content, str):
                return content

        return ""

    def _get_project_from_session_path(self, session_file: Path) -> str:
        """Extract project path from session file location."""
        parent_name = session_file.parent.name
        if parent_name.startswith("-"):
            return parent_name.replace("-", "/")
        return parent_name

    def _analyze_with_claude(
        self, candidates: list[dict[str, Any]]
    ) -> list[ClaudeMdSuggestion]:
        """
        Stage 2: Use Claude to analyze candidates and generate formatted suggestions.
        """
        if not candidates:
            return []

        # Group candidates by similarity and project
        grouped = self._group_candidates(candidates)

        # Prepare context for Claude
        candidate_summary = self._format_candidates_for_claude(grouped)

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(candidate_summary)

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse Claude's response
            response_text = response.content[0].text
            return self._parse_claude_response(response_text, grouped)

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            # Fallback: return empty list rather than crash
            return []

    def _group_candidates(
        self, candidates: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group similar candidates together."""
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for candidate in candidates:
            # Simple normalization for grouping
            normalized = " ".join(candidate["raw_text"].lower().split())
            # Use first 50 chars as key to group similar instructions
            key = normalized[:50] if len(normalized) > 50 else normalized
            grouped[key].append(candidate)

        return grouped

    def _format_candidates_for_claude(
        self, grouped: dict[str, list[dict[str, Any]]]
    ) -> str:
        """Format candidate groups for Claude analysis."""
        lines = []
        for i, (key, items) in enumerate(grouped.items(), 1):
            projects = list({c["project_path"] for c in items})
            example_context = items[0]["full_message"][:200]

            lines.append(f"""
### Candidate {i}
- **Pattern**: "{key}"
- **Occurrences**: {len(items)}
- **Projects**: {', '.join(projects)}
- **Example context**: "{example_context}..."
""")

        return "\n".join(lines)

    def _build_analysis_prompt(self, candidate_summary: str) -> str:
        """Build the prompt for Claude to analyze candidates."""
        return f"""You are analyzing user instruction patterns from Claude Code sessions to suggest additions to CLAUDE.md configuration files.

## Your Task
Review these candidate patterns extracted from user messages and:
1. **Filter out noise**: Reject patterns that are just code snippets, log output, single words, or contextual remarks
2. **Identify real instructions**: Keep only patterns that represent actual user preferences or policies
3. **Format as actionable CLAUDE.md entries**: Write clear, imperative instructions

## Candidate Patterns
{candidate_summary}

## Output Format
Respond with a JSON array of suggestions. Each suggestion must have:
- `instruction`: Clear, actionable text for CLAUDE.md (imperative mood, e.g., "Always use X", "Never do Y")
- `scope`: "global" if it applies across projects, "project" if specific to one
- `suggested_section`: Where it fits (e.g., "## Code Style", "## Testing", "## Git Workflow")
- `confidence`: 0.0-1.0 based on clarity and frequency
- `projects`: List of project paths where this was seen
- `reason`: Brief explanation of why this is a valid suggestion

## Rules
- Only include suggestions with confidence >= 0.6
- Merge similar patterns into single, well-written instructions
- Reject: single words, code fragments, tool output, questions, greetings
- Accept: explicit preferences ("always use X"), corrections ("no, use Y instead"), policies ("never commit without tests")

## Example Output
```json
[
  {{
    "instruction": "Always run tests before committing code",
    "scope": "global",
    "suggested_section": "## Testing Conventions",
    "confidence": 0.85,
    "projects": ["/home/user/project1", "/home/user/project2"],
    "reason": "User explicitly stated this preference 5 times across multiple projects"
  }}
]
```

If no valid suggestions remain after filtering, return an empty array: `[]`

Respond ONLY with the JSON array, no other text."""

    def _parse_claude_response(
        self,
        response_text: str,
        grouped: dict[str, list[dict[str, Any]]],
    ) -> list[ClaudeMdSuggestion]:
        """Parse Claude's JSON response into suggestion objects."""
        suggestions = []

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Remove markdown code fences
                lines = json_text.split("\n")
                json_lines = []
                in_code = False
                for line in lines:
                    if line.startswith("```"):
                        in_code = not in_code
                        continue
                    if in_code:
                        json_lines.append(line)
                json_text = "\n".join(json_lines)

            parsed = json.loads(json_text)

            for item in parsed:
                if not isinstance(item, dict):
                    continue

                confidence = float(item.get("confidence", 0))
                if confidence < self.config.confidence_threshold:
                    continue

                scope = (
                    SuggestionScope.GLOBAL
                    if item.get("scope") == "global"
                    else SuggestionScope.PROJECT
                )

                projects = item.get("projects", [])
                target_file = (
                    "~/.claude/CLAUDE-USER-POLICIES.md"
                    if scope == SuggestionScope.GLOBAL
                    else f"{projects[0]}/CLAUDE.md" if projects else "./CLAUDE.md"
                )

                suggestions.append(
                    ClaudeMdSuggestion(
                        instruction=item.get("instruction", ""),
                        scope=scope,
                        target_file=target_file,
                        suggested_section=item.get("suggested_section", "## Development Conventions"),
                        occurrences=len(grouped.get(item.get("instruction", "")[:50], [])),
                        projects=projects,
                        confidence=confidence,
                        source_sessions=[],  # Not tracked through Claude analysis
                        pattern_type="claude_analyzed",
                    )
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}")

        return suggestions
