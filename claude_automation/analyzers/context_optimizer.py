"""
Context optimizer for CLAUDE.md effectiveness tracking.
Analyzes which sections Claude actually uses and optimizes accordingly.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from ..schemas import (
    ContextAccessLog,
    ContextOptimization,
    SectionUsage,
)

logger = logging.getLogger(__name__)


class ContextUsageTracker:
    """
    Tracks which CLAUDE.md sections Claude actually references.

    Logs section access, calculates utilization metrics, and
    identifies optimization opportunities.
    """

    def __init__(self, log_file: Path | None = None):
        """
        Initialize context usage tracker.

        Args:
            log_file: Path to JSONL log file (default: ~/.claude/learning/context_usage.jsonl)
        """
        if log_file is None:
            log_file = Path.home() / ".claude" / "learning" / "context_usage.jsonl"

        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_access(
        self,
        section_name: str,
        tokens_in_section: int,
        relevance_score: float,
        session_id: str,
        query_context: str = "",
    ):
        """
        Log a section access event.

        Args:
            section_name: Name of section accessed
            tokens_in_section: Estimated token count
            relevance_score: How relevant was this section (0-1)
            session_id: Claude Code session identifier
            query_context: What Claude was trying to do
        """
        entry = ContextAccessLog(
            timestamp=datetime.now(),
            section_name=section_name,
            tokens_in_section=tokens_in_section,
            relevance_score=relevance_score,
            session_id=session_id,
            query_context=query_context,
        )

        # Append to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

        logger.debug(f"Logged section access: {section_name} (relevance: {relevance_score:.2f})")

    def get_recent_accesses(self, days: int = 30) -> list[ContextAccessLog]:
        """
        Get recent section accesses within time window.

        Args:
            days: Number of days to look back

        Returns:
            List of ContextAccessLog entries
        """
        if not self.log_file.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        accesses = []

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    entry_dict = json.loads(line)
                    entry = ContextAccessLog(**entry_dict)

                    if entry.timestamp > cutoff:
                        accesses.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to parse access log entry: {e}")
                    continue

        return accesses

    def calculate_section_usage(
        self, accesses: list[ContextAccessLog]
    ) -> dict[str, SectionUsage]:
        """
        Calculate usage statistics per section.

        Args:
            accesses: List of access log entries

        Returns:
            Dict mapping section name to SectionUsage
        """
        usage_map: dict[str, SectionUsage] = {}

        for access in accesses:
            section = access.section_name

            if section not in usage_map:
                usage_map[section] = SectionUsage(
                    section_name=section,
                    total_loads=0,
                    total_references=0,
                    total_tokens=access.tokens_in_section,
                    avg_relevance=0.0,
                    last_used=None,
                )

            usage = usage_map[section]
            usage.total_loads += 1

            # Count as reference if relevance > 0.5
            if access.relevance_score > 0.5:
                usage.total_references += 1

            # Update average relevance
            usage.avg_relevance = (
                (usage.avg_relevance * (usage.total_loads - 1)) + access.relevance_score
            ) / usage.total_loads

            # Update last used
            if usage.last_used is None or access.timestamp > usage.last_used:
                usage.last_used = access.timestamp

        return usage_map

    def get_stats(self, days: int = 30) -> dict:
        """
        Get aggregated statistics.

        Args:
            days: Analysis window in days

        Returns:
            Dict with statistics
        """
        accesses = self.get_recent_accesses(days)

        if not accesses:
            return {
                "total_accesses": 0,
                "unique_sections": 0,
                "avg_relevance": 0.0,
            }

        usage_map = self.calculate_section_usage(accesses)

        return {
            "total_accesses": len(accesses),
            "unique_sections": len(usage_map),
            "avg_relevance": sum(u.avg_relevance for u in usage_map.values())
            / len(usage_map),
            "sections": usage_map,
        }


class ContextOptimizer:
    """
    Optimizes CLAUDE.md based on usage patterns.

    Identifies:
    - Noise sections (loaded but rarely used)
    - Context gaps (missing information)
    - Reordering opportunities
    - Pruning candidates
    """

    def __init__(self, log_file: Path | None = None, usage_tracker: ContextUsageTracker | None = None):
        """
        Initialize context optimizer.

        Args:
            log_file: Path to context access log (JSONL format)
            usage_tracker: ContextUsageTracker instance (optional, for compatibility)
        """
        # Support both interfaces for backwards compatibility
        if usage_tracker is not None:
            self.usage_tracker = usage_tracker
            self.log_file = usage_tracker.log_file
        else:
            if log_file is None:
                log_file = Path.home() / ".claude" / "context-access.jsonl"
            self.log_file = log_file
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.usage_tracker = ContextUsageTracker(log_file)

    def log_section_access(
        self,
        section_name: str,
        tokens_in_section: int,
        relevance_score: float,
        session_id: str,
        query_context: str = "",
    ):
        """
        Log a section access event.

        Args:
            section_name: Name of CLAUDE.md section accessed
            tokens_in_section: Estimated token count in section
            relevance_score: 0-1 score of how relevant section was
            session_id: Session identifier
            query_context: What user/Claude was trying to do
        """
        self.usage_tracker.log_access(
            section_name, tokens_in_section, relevance_score, session_id, query_context
        )

    def get_section_usage_statistics(
        self, period_days: int = 30
    ) -> dict[str, SectionUsage]:
        """
        Calculate usage statistics for all sections.

        Args:
            period_days: Analysis window in days

        Returns:
            Dict mapping section name -> SectionUsage
        """
        accesses = self.usage_tracker.get_recent_accesses(period_days)
        return self.usage_tracker.calculate_section_usage(accesses)

    def identify_noise_sections(
        self, period_days: int = 30, utilization_threshold: float = 0.1
    ) -> list[SectionUsage]:
        """
        Identify sections that are loaded but rarely used (noise).

        Args:
            period_days: Analysis window in days
            utilization_threshold: Minimum utilization rate (default 0.1 = 10%)

        Returns:
            List of SectionUsage objects for noise sections
        """
        usage_stats = self.get_section_usage_statistics(period_days)

        noise_sections = []
        for section_usage in usage_stats.values():
            # Noise criteria:
            # 1. Loaded more than 5 times (enough data)
            # 2. Utilization rate below threshold
            if (
                section_usage.total_loads > 5
                and section_usage.utilization_rate < utilization_threshold
            ):
                noise_sections.append(section_usage)

        # Sort by wasted tokens (loads * tokens per load * waste rate)
        noise_sections.sort(
            key=lambda s: s.total_loads
            * s.total_tokens
            * (1 - s.utilization_rate),
            reverse=True,
        )

        return noise_sections

    def calculate_effective_context_ratio(self, period_days: int = 30) -> float:
        """
        Calculate effective context ratio.

        Ratio = (sum of relevant_tokens) / (sum of total_tokens)
        Where relevant_tokens = tokens * avg_relevance

        Higher ratio = more efficient context usage

        Args:
            period_days: Analysis window in days

        Returns:
            Ratio between 0.0 and 1.0
        """
        usage_stats = self.get_section_usage_statistics(period_days)

        if not usage_stats:
            return 0.0

        total_tokens = 0
        relevant_tokens = 0.0

        for section_usage in usage_stats.values():
            # Weight by number of loads
            section_total = section_usage.total_tokens * section_usage.total_loads
            section_relevant = section_total * section_usage.avg_relevance

            total_tokens += section_total
            relevant_tokens += section_relevant

        if total_tokens == 0:
            return 0.0

        return relevant_tokens / total_tokens

    def generate_reordering_suggestions(
        self, period_days: int = 30
    ) -> list[tuple[str, int, float]]:
        """
        Generate section reordering based on access frequency.

        Frequently accessed sections should appear earlier in CLAUDE.md
        to reduce token consumption.

        Args:
            period_days: Analysis window in days

        Returns:
            List of (section_name, suggested_position, access_score) tuples
        """
        usage_stats = self.get_section_usage_statistics(period_days)

        # Calculate access score (loads * avg_relevance)
        section_scores = []
        for section_name, usage in usage_stats.items():
            score = usage.total_loads * usage.avg_relevance
            section_scores.append((section_name, score))

        # Sort by score (descending)
        section_scores.sort(key=lambda x: x[1], reverse=True)

        # Generate position suggestions
        suggestions = []
        for position, (section_name, score) in enumerate(section_scores, start=1):
            suggestions.append((section_name, position, score))

        return suggestions

    def generate_quick_reference(self, period_days: int = 30) -> dict[str, list[str]]:
        """
        Generate quick reference from hot paths.

        Identifies most frequently accessed content and suggests
        creating a "Quick Reference" section at the top.

        Args:
            period_days: Analysis window in days

        Returns:
            Dict with quick reference content suggestions
        """
        usage_stats = self.get_section_usage_statistics(period_days)

        # Find hot sections (top 20% by access frequency)
        section_access = [
            (name, usage.total_loads * usage.avg_relevance)
            for name, usage in usage_stats.items()
        ]
        section_access.sort(key=lambda x: x[1], reverse=True)

        # Top 20%
        top_count = max(1, len(section_access) // 5)
        hot_sections = section_access[:top_count]

        quick_ref = {
            "title": "Quick Reference",
            "description": "Most frequently accessed information",
            "sections": [name for name, _ in hot_sections],
        }

        return quick_ref

    def detect_context_gaps(self, period_days: int = 30) -> list[str]:
        """
        Detect frequently-queried information that's missing from context.

        This analyzes query_context fields to find patterns
        of questions that couldn't be answered from existing sections.

        Args:
            period_days: Analysis window in days

        Returns:
            List of gap descriptions
        """
        gaps = []
        usage_stats = self.get_section_usage_statistics(period_days)

        # Find sections with high load but low relevance
        for section_usage in usage_stats.values():
            if (
                section_usage.total_loads > 5
                and section_usage.avg_relevance < 0.3
            ):
                gaps.append(
                    f"Section '{section_usage.section_name}' loaded frequently "
                    f"but low relevance - may need better content"
                )

        return gaps[:5]  # Limit to top 5 gaps

    def analyze(
        self, period_days: int = 30, noise_threshold: float = 0.1
    ) -> list[ContextOptimization]:
        """
        Run full context analysis and generate optimization suggestions.

        Args:
            period_days: Analysis window in days
            noise_threshold: Utilization rate below which section is "noise"

        Returns:
            List of ContextOptimization suggestions, prioritized
        """
        suggestions = []

        # 1. Identify noise sections → prune suggestions
        noise_sections = self.identify_noise_sections(period_days, noise_threshold)
        for noise in noise_sections:
            # Priority based on token savings
            priority = 1 if noise.total_tokens > 1000 else 2

            suggestions.append(
                ContextOptimization(
                    optimization_type="prune_section",
                    section_name=noise.section_name,
                    reason=f"Loaded {noise.total_loads} times but only {noise.utilization_rate*100:.1f}% utilization",
                    impact=f"Save ~{noise.total_tokens} tokens per load",
                    token_savings=noise.total_tokens,
                    priority=priority,
                )
            )

        # 2. Reordering suggestions
        reorder_suggestions = self.generate_reordering_suggestions(period_days)
        if len(reorder_suggestions) > 3:
            # Only suggest reordering if we have enough data
            hot_sections = reorder_suggestions[:3]
            hot_names = ", ".join([name for name, _, _ in hot_sections])

            suggestions.append(
                ContextOptimization(
                    optimization_type="reorder",
                    section_name="Multiple sections",
                    reason=f"Hot sections accessed frequently: {hot_names}",
                    impact="Reduce token consumption by moving frequently used sections earlier",
                    token_savings=0,  # Indirect savings
                    priority=2,
                )
            )

        # 3. Quick reference generation
        quick_ref = self.generate_quick_reference(period_days)
        if len(quick_ref["sections"]) > 0:
            suggestions.append(
                ContextOptimization(
                    optimization_type="add_quick_ref",
                    section_name="Quick Reference",
                    reason=f"Create quick ref from hot sections: {', '.join(quick_ref['sections'][:3])}",
                    impact="Fast access to most frequently needed information",
                    token_savings=0,
                    priority=3,
                )
            )

        # 4. Context gaps → add_missing suggestions
        gaps = self.detect_context_gaps(period_days)
        for gap in gaps:
            suggestions.append(
                ContextOptimization(
                    optimization_type="add_missing",
                    section_name="Missing content",
                    reason=gap,
                    impact="Fill information gaps",
                    token_savings=0,
                    priority=3,
                )
            )

        # Sort by priority
        suggestions.sort(key=lambda s: s.priority)

        logger.info(f"Generated {len(suggestions)} context optimization suggestions")
        return suggestions

    def calculate_effective_ratio(self, days: int = 30) -> float:
        """
        Calculate effective context ratio.

        Ratio of referenced tokens to total loaded tokens.

        Args:
            days: Analysis window in days

        Returns:
            Effective context ratio (0-1)
        """
        accesses = self.usage_tracker.get_recent_accesses(days)

        if not accesses:
            return 0.0

        usage_map = self.usage_tracker.calculate_section_usage(accesses)

        total_tokens = sum(u.total_tokens for u in usage_map.values())
        referenced_tokens = sum(
            u.total_tokens for u in usage_map.values() if u.total_references > 0
        )

        if total_tokens == 0:
            return 0.0

        return referenced_tokens / total_tokens

    def identify_context_gaps(self, days: int = 30) -> list[str]:
        """
        Identify missing context (information Claude queries for but isn't in CLAUDE.md).

        Analyzes:
        - Sections with high load but low relevance (wrong content)
        - Query patterns from session logs
        - Tool usage not documented
        - Frequent error patterns

        Args:
            days: Analysis window in days

        Returns:
            List of context gap descriptions
        """
        gaps = []
        usage_stats = self.get_section_usage_statistics(days)

        # Gap Type 1: High load, low relevance
        # (Section exists but doesn't answer the actual query)
        for section_usage in usage_stats.values():
            if (
                section_usage.total_loads > 5
                and section_usage.avg_relevance < 0.3
            ):
                gaps.append(
                    f"Section '{section_usage.section_name}' loaded {section_usage.total_loads} times "
                    f"but only {section_usage.avg_relevance*100:.0f}% relevant - needs better/different content"
                )

        # Gap Type 2: Analyze query contexts for missing topics
        accesses = self.usage_tracker.get_recent_accesses(days)
        query_contexts = [
            access.query_context
            for access in accesses
            if access.query_context and access.relevance_score < 0.5
        ]

        # Look for patterns in low-relevance queries
        if query_contexts:
            # Simple keyword extraction (production would use NLP)
            common_keywords = self._extract_common_keywords(query_contexts)

            if common_keywords:
                gaps.append(
                    f"Frequent query topics not well-covered: {', '.join(common_keywords[:5])}"
                )

        # Gap Type 3: Session log analysis
        sessions_dir = Path.home() / ".claude" / "sessions"
        if sessions_dir.exists():
            tool_usage_gaps = self._analyze_undocumented_tools(sessions_dir, days)
            gaps.extend(tool_usage_gaps)

        # Limit to top 5 most important gaps
        return gaps[:5]

    def _extract_common_keywords(self, query_contexts: list[str]) -> list[str]:
        """
        Extract common keywords from query contexts.

        Simple implementation - production would use NLP.

        Args:
            query_contexts: List of query context strings

        Returns:
            List of common keywords
        """
        from collections import Counter

        # Combine all queries
        all_text = " ".join(query_contexts).lower()

        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
            "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
            "how", "what", "when", "where", "why", "which", "who", "that",
        }

        # Tokenize (simple split) and filter
        words = [
            word.strip(",.;:!?")
            for word in all_text.split()
            if len(word) > 3 and word not in stop_words
        ]

        # Count and return top keywords
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(10) if count >= 2]

    def _analyze_undocumented_tools(
        self, sessions_dir: Path, days: int
    ) -> list[str]:
        """
        Analyze session logs to find tools used but not documented.

        Args:
            sessions_dir: Path to sessions directory
            days: Analysis window in days

        Returns:
            List of gap descriptions for undocumented tools
        """
        gaps = []

        try:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=days)

            # Track tool invocations
            tool_invocations = {}  # tool_name -> count

            # Parse recent session logs
            for session_file in sessions_dir.glob("*.jsonl"):
                # Check if session is recent
                if datetime.fromtimestamp(session_file.stat().st_mtime) < cutoff:
                    continue

                try:
                    with open(session_file, encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue

                            try:
                                entry = json.loads(line)

                                # Track tool usage
                                if entry.get("type") == "tool_use":
                                    tool_name = entry.get("name", "unknown")
                                    tool_invocations[tool_name] = (
                                        tool_invocations.get(tool_name, 0) + 1
                                    )

                            except json.JSONDecodeError:
                                continue

                except Exception as e:
                    logger.debug(f"Failed to parse session {session_file}: {e}")
                    continue

            # Identify frequently-used but undocumented tools
            # (Tools used >10 times but not mentioned in CLAUDE.md context)
            for tool_name, count in tool_invocations.items():
                if count > 10:
                    # Check if this tool appears in any section with high relevance
                    # (Simplified: assume if it's not in a high-relevance section, it's missing)
                    is_documented = self._is_tool_documented(tool_name)

                    if not is_documented:
                        gaps.append(
                            f"Tool '{tool_name}' used {count} times but not well-documented in CLAUDE.md"
                        )

        except Exception as e:
            logger.warning(f"Failed to analyze undocumented tools: {e}")

        return gaps[:3]  # Limit to top 3

    def _is_tool_documented(self, tool_name: str) -> bool:
        """
        Check if tool is documented in high-relevance sections.

        Simplified heuristic: returns False if tool might be missing.

        Args:
            tool_name: Name of tool to check

        Returns:
            True if tool appears to be documented
        """
        # Get recent accesses
        accesses = self.usage_tracker.get_recent_accesses(30)

        # Check if any high-relevance accesses mention this tool
        for access in accesses:
            if access.relevance_score > 0.7 and tool_name.lower() in access.section_name.lower():
                return True

        # If we don't find it in recent high-relevance accesses, assume missing
        return False
