"""
Workflow detector for slash command pattern analysis.
Detects repeated command sequences and suggests bundled workflows.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from ..schemas import (
    SlashCommandLog,
    WorkflowSequence,
    WorkflowSuggestion,
)
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class WorkflowDetector(BaseAnalyzer):
    """
    Detects patterns in slash command sequences.

    Analyzes command invocation history to identify:
    - Repeated multi-command sequences
    - Workflow completion rates
    - Bundling opportunities
    """

    def __init__(self, log_file: Path | None = None):
        """
        Initialize workflow detector.

        Args:
            log_file: Path to JSONL log file (default: ~/.claude/learning/workflow_commands.jsonl)
        """
        if log_file is None:
            log_file = Path.home() / ".claude" / "learning" / "workflow_commands.jsonl"

        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


    def _get_analysis_method_name(self) -> str:
        """Return the name of the primary analysis method."""
        return "detect_patterns"

    def log_command(
        self,
        command: str,
        session_id: str,
        success: bool = True,
        duration_ms: int | None = None,
        project_path: str = "",
    ):
        """
        Log a slash command invocation.

        Args:
            command: Command invoked (e.g., '/speckit.specify')
            session_id: Session identifier
            success: Whether command succeeded
            duration_ms: Execution duration in milliseconds
            project_path: Project path if applicable
        """
        entry = SlashCommandLog(
            timestamp=datetime.now(),
            command=command,
            session_id=session_id,
            success=success,
            duration_ms=duration_ms,
            project_path=project_path,
        )

        # Append to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

        logger.debug(f"Logged slash command: {command}")

    def get_recent_commands(self, days: int = 30) -> list[SlashCommandLog]:
        """
        Get recent slash command invocations within time window.

        Args:
            days: Number of days to look back

        Returns:
            List of SlashCommandLog entries
        """
        if not self.log_file.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        commands = []

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    entry_dict = json.loads(line)
                    entry = SlashCommandLog(**entry_dict)

                    if entry.timestamp > cutoff:
                        commands.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to parse command log entry: {e}")
                    continue

        return commands

    def detect_patterns(
        self, min_occurrences: int = 3, days: int = 30, max_sequence_length: int = 5
    ) -> list[WorkflowSuggestion]:
        """
        Detect repeated command sequences and suggest workflows.

        Args:
            min_occurrences: Minimum times sequence must occur
            days: Analysis window in days
            max_sequence_length: Maximum commands in sequence

        Returns:
            List of WorkflowSuggestion for bundling
        """
        commands = self.get_recent_commands(days)

        if not commands:
            logger.info("No workflow command data available")
            return []

        # Group commands by session
        sessions = self._group_by_session(commands)

        # Extract sequences
        sequences = self._extract_sequences(sessions, max_sequence_length)

        # Count sequence occurrences
        sequence_counts = self._count_sequences(sequences)

        # Filter by minimum occurrences
        frequent_sequences = {
            seq: count
            for seq, count in sequence_counts.items()
            if count >= min_occurrences and len(seq) >= 2
        }

        if not frequent_sequences:
            logger.info("No frequent workflow patterns detected")
            return []

        # Generate suggestions
        suggestions = []
        for sequence_tuple, count in frequent_sequences.items():
            sequence_list = list(sequence_tuple)

            # Calculate completion rate (simplified - assumes all succeeded)
            completion_rate = 1.0  # TODO: Track actual completion

            # Create workflow sequence
            workflow_seq = WorkflowSequence(
                commands=sequence_list,
                occurrences=count,
                completion_rate=completion_rate,
                avg_duration_ms=None,  # TODO: Calculate from logs
                first_seen=datetime.now() - timedelta(days=days),
                last_seen=datetime.now(),
            )

            # Generate suggestion
            proposed_name = self._generate_workflow_name(sequence_list)
            description = self._generate_workflow_description(sequence_list)
            script_content = self._generate_workflow_script(sequence_list)
            impact = self._estimate_impact(count, len(sequence_list))

            suggestions.append(
                WorkflowSuggestion(
                    description=description,
                    sequence=workflow_seq,
                    proposed_command=proposed_name,
                    script_content=script_content,
                    impact_estimate=impact,
                )
            )

        # Sort by occurrences (most frequent first)
        suggestions.sort(key=lambda s: s.sequence.occurrences, reverse=True)

        logger.info(f"Detected {len(suggestions)} workflow patterns")
        return suggestions

    def _group_by_session(
        self, commands: list[SlashCommandLog]
    ) -> dict[str, list[SlashCommandLog]]:
        """
        Group commands by session ID.

        Args:
            commands: List of command logs

        Returns:
            Dict mapping session_id to commands
        """
        sessions: dict[str, list[SlashCommandLog]] = defaultdict(list)

        for cmd in commands:
            sessions[cmd.session_id].append(cmd)

        # Sort each session by timestamp
        for session_id in sessions:
            sessions[session_id].sort(key=lambda c: c.timestamp)

        return sessions

    def _extract_sequences(
        self,
        sessions: dict[str, list[SlashCommandLog]],
        max_length: int,
    ) -> list[tuple[str, ...]]:
        """
        Extract all possible sequences from sessions.

        Args:
            sessions: Commands grouped by session
            max_length: Maximum sequence length

        Returns:
            List of command sequences as tuples
        """
        sequences = []

        for session_commands in sessions.values():
            if len(session_commands) < 2:
                continue

            # Extract all subsequences of length 2 to max_length
            commands = [c.command for c in session_commands]

            for length in range(2, min(len(commands) + 1, max_length + 1)):
                for i in range(len(commands) - length + 1):
                    sequence = tuple(commands[i : i + length])
                    sequences.append(sequence)

        return sequences

    def _count_sequences(
        self, sequences: list[tuple[str, ...]]
    ) -> dict[tuple[str, ...], int]:
        """
        Count occurrences of each sequence.

        Args:
            sequences: List of sequences

        Returns:
            Dict mapping sequence to count
        """
        counts: dict[tuple[str, ...], int] = defaultdict(int)

        for sequence in sequences:
            counts[sequence] += 1

        return counts

    def _generate_workflow_name(self, commands: list[str]) -> str:
        """
        Generate suggested workflow command name.

        Args:
            commands: Command sequence

        Returns:
            Suggested command name (e.g., '/spec-full-plan')
        """
        # Extract common prefix
        if all(cmd.startswith("/speckit.") for cmd in commands):
            # Special case for speckit workflows
            parts = [cmd.replace("/speckit.", "") for cmd in commands]
            return f"/speckit.{'-'.join(parts)}"

        # Generic case
        first_cmd = commands[0].lstrip("/").replace(".", "-")
        return f"/{first_cmd}-workflow"

    def _generate_workflow_description(self, commands: list[str]) -> str:
        """
        Generate workflow description.

        Args:
            commands: Command sequence

        Returns:
            Human-readable description
        """
        cmd_names = [cmd.lstrip("/") for cmd in commands]
        return f"Bundles: {' → '.join(cmd_names)}"

    def _generate_workflow_script(self, commands: list[str]) -> str:
        """
        Generate script content for bundled workflow.

        Args:
            commands: Command sequence

        Returns:
            Script content
        """
        # Simple script that runs commands in sequence
        script_lines = ["#!/usr/bin/env bash", "set -e", ""]

        for cmd in commands:
            # Remove leading slash for execution
            script_lines.append(f"claude {cmd}")

        return "\n".join(script_lines)

    def _estimate_impact(self, occurrences: int, sequence_length: int) -> str:
        """
        Estimate time savings impact.

        Args:
            occurrences: Number of times sequence occurred
            sequence_length: Length of sequence

        Returns:
            Impact estimate string
        """
        # Estimate ~10 seconds saved per command in sequence
        seconds_per_command = 10
        total_saved = occurrences * sequence_length * seconds_per_command

        if total_saved < 60:
            return f"Save ~{total_saved}s total"
        elif total_saved < 3600:
            minutes = total_saved // 60
            return f"Save ~{minutes} minutes total"
        else:
            hours = total_saved // 3600
            return f"Save ~{hours} hours total"

    def get_stats(self, days: int = 30) -> dict:
        """
        Get aggregated statistics.

        Args:
            days: Analysis window in days

        Returns:
            Dict with statistics
        """
        commands = self.get_recent_commands(days)

        if not commands:
            return {
                "total_commands": 0,
                "unique_commands": 0,
                "total_sessions": 0,
            }

        unique_commands = set(c.command for c in commands)
        unique_sessions = set(c.session_id for c in commands)

        return {
            "total_commands": len(commands),
            "unique_commands": len(unique_commands),
            "total_sessions": len(unique_sessions),
            "most_used": self._get_most_used_commands(commands, top_n=5),
        }

    def _get_most_used_commands(
        self, commands: list[SlashCommandLog], top_n: int = 5
    ) -> list[tuple[str, int]]:
        """
        Get most frequently used commands.

        Args:
            commands: List of command logs
            top_n: Number of top commands to return

        Returns:
            List of (command, count) tuples
        """
        counts: dict[str, int] = defaultdict(int)

        for cmd in commands:
            counts[cmd.command] += 1

        # Sort by count descending
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        return sorted_counts[:top_n]
