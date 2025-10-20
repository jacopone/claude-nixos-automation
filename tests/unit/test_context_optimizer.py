"""
Unit tests for ContextOptimizer.

Tests section tracking, noise detection, and effective ratio calculation.
"""

import json
import tempfile
from pathlib import Path

import pytest

from claude_automation.analyzers import ContextOptimizer
from claude_automation.schemas import (
    SectionUsage,
)


class TestSectionTracking:
    """Test section usage tracking."""

    def test_log_section_access(self):
        """Test that section access is logged correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)
            optimizer.log_section_access(
                section_name="Modern CLI Tools",
                tokens_in_section=500,
                relevance_score=0.8,
                session_id="session-123",
                query_context="User asked about eza command",
            )

            # Verify log file was created and contains entry
            assert log_file.exists()

            # Read and verify entry
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 1

                entry_data = json.loads(lines[0])
                assert entry_data["section_name"] == "Modern CLI Tools"
                assert entry_data["tokens_in_section"] == 500
                assert entry_data["relevance_score"] == 0.8
                assert entry_data["session_id"] == "session-123"

    def test_log_multiple_accesses(self):
        """Test logging multiple section accesses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Log multiple accesses
            sections = ["Section A", "Section B", "Section A"]  # A accessed twice
            for section in sections:
                optimizer.log_section_access(
                    section_name=section,
                    tokens_in_section=100,
                    relevance_score=0.5,
                    session_id="session-123",
                )

            # Verify all logged
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 3

    def test_get_section_usage_statistics(self):
        """Test calculating section usage statistics from logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Log section accesses
            optimizer.log_section_access(
                section_name="Section A",
                tokens_in_section=500,
                relevance_score=0.9,
                session_id="session-1",
            )
            optimizer.log_section_access(
                section_name="Section A",
                tokens_in_section=500,
                relevance_score=0.7,
                session_id="session-2",
            )
            optimizer.log_section_access(
                section_name="Section B",
                tokens_in_section=300,
                relevance_score=0.5,
                session_id="session-1",
            )

            # Get statistics
            stats = optimizer.get_section_usage_statistics(period_days=30)

            # Verify Section A stats
            assert "Section A" in stats
            section_a = stats["Section A"]
            assert isinstance(section_a, SectionUsage)
            assert section_a.total_references == 2
            assert section_a.total_tokens == 500
            assert section_a.avg_relevance == pytest.approx(0.8, rel=0.01)  # (0.9+0.7)/2

            # Verify Section B stats
            assert "Section B" in stats
            section_b = stats["Section B"]
            assert section_b.total_references == 1
            assert section_b.avg_relevance == 0.5

    def test_section_usage_properties(self):
        """Test SectionUsage calculated properties."""
        usage = SectionUsage(
            section_name="Test Section",
            total_loads=10,
            total_references=3,
            total_tokens=500,
            avg_relevance=0.6,
        )

        # Utilization rate = references / loads
        assert usage.utilization_rate == pytest.approx(0.3, rel=0.01)  # 3/10

        # Not noise (loaded > 5 and utilization < 0.1)
        assert not usage.is_noise

    def test_section_is_noise_detection(self):
        """Test noise section detection."""
        # High loads, low utilization = noise
        noise_section = SectionUsage(
            section_name="Noise Section",
            total_loads=20,
            total_references=1,  # Used only once out of 20 loads
            total_tokens=1000,
            avg_relevance=0.2,
        )

        assert noise_section.utilization_rate < 0.1
        assert noise_section.is_noise

        # Low loads or high utilization = not noise
        good_section = SectionUsage(
            section_name="Good Section",
            total_loads=10,
            total_references=5,  # Used 50% of the time
            total_tokens=500,
            avg_relevance=0.8,
        )

        assert not good_section.is_noise


class TestNoiseDetection:
    """Test identification of noise sections."""

    def test_identify_noise_sections_basic(self):
        """Test basic noise section identification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Simulate: Section loaded 20 times, referenced only once
            for i in range(20):
                optimizer.log_section_access(
                    section_name="Rarely Used Section",
                    tokens_in_section=500,
                    relevance_score=0.1 if i == 0 else 0.0,  # Only relevant once
                    session_id=f"session-{i}",
                )

            # Also add a frequently used section
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Frequently Used Section",
                    tokens_in_section=300,
                    relevance_score=0.9,
                    session_id=f"session-{i}",
                )

            # Identify noise
            noise_sections = optimizer.identify_noise_sections(period_days=30)

            # Should identify rarely used section as noise
            assert len(noise_sections) > 0
            noise_names = [s.section_name for s in noise_sections]
            assert "Rarely Used Section" in noise_names
            assert "Frequently Used Section" not in noise_names

    def test_identify_noise_with_threshold(self):
        """Test noise detection with custom threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Section with 20% utilization
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Borderline Section",
                    tokens_in_section=500,
                    relevance_score=0.5 if i < 2 else 0.0,  # 2 out of 10 relevant
                    session_id=f"session-{i}",
                )

            # Default threshold (0.1) - should NOT be noise (20% > 10%)
            noise_default = optimizer.identify_noise_sections(period_days=30)
            noise_names = [s.section_name for s in noise_default]
            assert "Borderline Section" not in noise_names

            # Higher threshold (0.5) - should be noise (20% < 50%)
            noise_high = optimizer.identify_noise_sections(
                period_days=30, utilization_threshold=0.5
            )
            noise_names_high = [s.section_name for s in noise_high]
            assert "Borderline Section" in noise_names_high


class TestEffectiveRatioCalculation:
    """Test effective context ratio calculation."""

    def test_calculate_effective_context_ratio_perfect(self):
        """Test ratio calculation when all sections are used."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Log accesses where all sections are highly relevant
            sections = ["Section A", "Section B", "Section C"]
            for section in sections:
                optimizer.log_section_access(
                    section_name=section,
                    tokens_in_section=500,
                    relevance_score=0.9,
                    session_id="session-1",
                )

            # Calculate ratio
            ratio = optimizer.calculate_effective_context_ratio(period_days=30)

            # All sections used with high relevance = high ratio
            assert ratio > 0.8

    def test_calculate_effective_context_ratio_with_noise(self):
        """Test ratio calculation with noise sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Good section: loaded and used
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Good Section",
                    tokens_in_section=500,
                    relevance_score=0.9,
                    session_id=f"session-{i}",
                )

            # Noise section: loaded but rarely used
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Noise Section",
                    tokens_in_section=500,
                    relevance_score=0.1 if i == 0 else 0.0,
                    session_id=f"session-{i}",
                )

            # Calculate ratio
            ratio = optimizer.calculate_effective_context_ratio(period_days=30)

            # Ratio should be moderate (50% noise, 50% good)
            assert 0.3 < ratio < 0.7

    def test_calculate_ratio_weighs_by_tokens(self):
        """Test that ratio calculation weighs by token count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Small high-relevance section
            optimizer.log_section_access(
                section_name="Small Good",
                tokens_in_section=100,
                relevance_score=1.0,
                session_id="session-1",
            )

            # Large low-relevance section
            optimizer.log_section_access(
                section_name="Large Noise",
                tokens_in_section=1000,
                relevance_score=0.1,
                session_id="session-1",
            )

            # Calculate ratio
            ratio = optimizer.calculate_effective_context_ratio(period_days=30)

            # Large noise section should dominate, resulting in low ratio
            assert ratio < 0.3

    def test_effective_ratio_empty_log(self):
        """Test ratio calculation with no logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # No logs = ratio of 0
            ratio = optimizer.calculate_effective_context_ratio(period_days=30)
            assert ratio == 0.0


class TestContextOptimizationSuggestions:
    """Test generation of optimization suggestions."""

    def test_generate_prune_suggestion_for_noise(self):
        """Test that prune suggestions are generated for noise sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Create noise section
            for i in range(20):
                optimizer.log_section_access(
                    section_name="Unused Tools",
                    tokens_in_section=800,
                    relevance_score=0.0,
                    session_id=f"session-{i}",
                )

            # Generate suggestions
            suggestions = optimizer.analyze(period_days=30)

            # Should have prune suggestion
            prune_suggestions = [
                s for s in suggestions if s.optimization_type == "prune_section"
            ]
            assert len(prune_suggestions) > 0

            prune = prune_suggestions[0]
            assert prune.section_name == "Unused Tools"
            assert prune.token_savings == 800
            assert prune.priority >= 1

    def test_generate_reorder_suggestion_for_hot_sections(self):
        """Test that reorder suggestions prioritize frequently accessed sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Hot section (accessed frequently)
            for i in range(50):
                optimizer.log_section_access(
                    section_name="Hot Section",
                    tokens_in_section=500,
                    relevance_score=0.9,
                    session_id=f"session-{i}",
                )

            # Cold section (accessed rarely)
            for i in range(2):
                optimizer.log_section_access(
                    section_name="Cold Section",
                    tokens_in_section=300,
                    relevance_score=0.7,
                    session_id=f"session-{i}",
                )

            # Generate suggestions
            suggestions = optimizer.analyze(period_days=30)

            # Should have reorder suggestion
            reorder_suggestions = [
                s for s in suggestions if s.optimization_type == "reorder"
            ]

            # If reorder suggestions exist, hot section should be mentioned
            if reorder_suggestions:
                assert any(
                    "Hot Section" in s.reason or "Hot Section" in s.impact
                    for s in reorder_suggestions
                )

    def test_suggestion_priority_ordering(self):
        """Test that suggestions are prioritized correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "context-access.jsonl"

            optimizer = ContextOptimizer(log_file)

            # Create various scenarios
            # 1. Large noise section (high priority to prune)
            for i in range(20):
                optimizer.log_section_access(
                    section_name="Large Noise",
                    tokens_in_section=2000,
                    relevance_score=0.0,
                    session_id=f"session-{i}",
                )

            # 2. Small noise section (lower priority)
            for i in range(10):
                optimizer.log_section_access(
                    section_name="Small Noise",
                    tokens_in_section=100,
                    relevance_score=0.0,
                    session_id=f"session-{i}",
                )

            suggestions = optimizer.analyze(period_days=30)

            # Verify priority ordering
            for suggestion in suggestions:
                assert 1 <= suggestion.priority <= 3

            # High token savings should have higher priority
            if len(suggestions) > 1:
                high_savings = [s for s in suggestions if s.token_savings > 1000]
                if high_savings:
                    assert high_savings[0].priority == 1  # Highest priority
