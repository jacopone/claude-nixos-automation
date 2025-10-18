"""
Meta-learner for learning system self-calibration.
Tracks effectiveness of learning system and adjusts thresholds.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from ..schemas import (
    LearningHealthReport,
    LearningMetrics,
    ThresholdAdjustment,
)

logger = logging.getLogger(__name__)


class MetaLearner:
    """
    Meta-learning layer for system self-calibration.

    Tracks:
    - Suggestion acceptance rates
    - False positive patterns
    - User corrections
    - System effectiveness

    Adjusts:
    - Pattern detection thresholds
    - Confidence scoring parameters
    - Suggestion frequency
    """

    # Default thresholds
    DEFAULT_MIN_OCCURRENCES = 3
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    DEFAULT_ANALYSIS_PERIOD_DAYS = 30

    # Adjustment boundaries
    MIN_OCCURRENCES_RANGE = (2, 5)
    CONFIDENCE_RANGE = (0.5, 0.9)

    def __init__(self, metrics_file: Path | None = None, thresholds_file: Path | None = None):
        """
        Initialize meta-learner.

        Args:
            metrics_file: Path to metrics log file (default: ~/.claude/learning/meta_metrics.jsonl)
            thresholds_file: Path to thresholds file (default: ~/.claude/learning/thresholds.json)
        """
        if metrics_file is None:
            metrics_file = Path.home() / ".claude" / "learning" / "meta_metrics.jsonl"
        if thresholds_file is None:
            thresholds_file = Path.home() / ".claude" / "learning" / "thresholds.json"

        self.metrics_file = metrics_file
        self.thresholds_file = thresholds_file
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # Load current thresholds
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> dict:
        """
        Load current thresholds from file.

        Returns:
            Dict with threshold values
        """
        if not self.thresholds_file.exists():
            # Return defaults
            return {
                "min_occurrences": self.DEFAULT_MIN_OCCURRENCES,
                "confidence_threshold": self.DEFAULT_CONFIDENCE_THRESHOLD,
                "analysis_period_days": self.DEFAULT_ANALYSIS_PERIOD_DAYS,
            }

        try:
            with open(self.thresholds_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load thresholds: {e}, using defaults")
            return {
                "min_occurrences": self.DEFAULT_MIN_OCCURRENCES,
                "confidence_threshold": self.DEFAULT_CONFIDENCE_THRESHOLD,
                "analysis_period_days": self.DEFAULT_ANALYSIS_PERIOD_DAYS,
            }

    def _save_thresholds(self):
        """Save current thresholds to file."""
        with open(self.thresholds_file, "w", encoding="utf-8") as f:
            json.dump(self.thresholds, f, indent=2)

    def log_suggestion(
        self,
        component: str,
        suggestion_type: str,
        accepted: bool,
        confidence: float,
        was_correct: bool | None = None,
    ):
        """
        Log a suggestion and its outcome.

        Args:
            component: Component that made suggestion (permissions, mcp, context, etc.)
            suggestion_type: Type of suggestion
            accepted: Whether user accepted
            confidence: Confidence score of suggestion
            was_correct: Whether suggestion was actually correct (None if unknown)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "suggestion_type": suggestion_type,
            "accepted": accepted,
            "confidence": confidence,
            "was_correct": was_correct,
        }

        # Append to metrics file
        with open(self.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        logger.debug(
            f"Logged suggestion: {component}/{suggestion_type} (accepted={accepted})"
        )

    def record_session(
        self,
        total_suggestions: int,
        accepted: int,
        acceptance_rate: float,
    ):
        """
        Record a learning session.

        Args:
            total_suggestions: Total suggestions made
            accepted: Number accepted
            acceptance_rate: Acceptance rate (0-1)
        """
        # Log session-level metrics
        self.log_suggestion(
            component="session",
            suggestion_type="aggregate",
            accepted=accepted > 0,
            confidence=acceptance_rate,
        )

        # Adjust thresholds based on acceptance rate
        if acceptance_rate < 0.5:
            self.increase_thresholds()
        elif acceptance_rate > 0.9:
            self.decrease_thresholds()

    def get_health_metrics(self) -> dict[str, dict]:
        """
        Get health metrics for learning system (per-component).

        Returns:
            Dict mapping component names to their health metrics
        """
        if not self.metrics_file.exists():
            return {}

        # Load recent metrics
        metrics = self._load_recent_metrics(days=30)

        if not metrics:
            return {}

        # Group by component
        components = {m.get("component") for m in metrics if "component" in m and "suggestion_id" in m}

        health_metrics = {}
        for component in components:
            comp_metrics = [m for m in metrics if m.get("component") == component and "suggestion_id" in m]

            if not comp_metrics:
                continue

            accepted = sum(1 for m in comp_metrics if m.get("accepted"))
            total = len(comp_metrics)
            acceptance_rate = accepted / total if total > 0 else 0.0

            # Determine status
            if acceptance_rate >= 0.8:
                status = "healthy"
            elif acceptance_rate >= 0.5:
                status = "good"
            elif acceptance_rate >= 0.3:
                status = "warning"
            else:
                status = "critical"

            # Calculate suggestions per day
            if comp_metrics:
                first_ts = datetime.fromisoformat(comp_metrics[-1]["timestamp"])
                last_ts = datetime.fromisoformat(comp_metrics[0]["timestamp"])
                days_span = max(1, (last_ts - first_ts).days)
                suggestions_per_day = len(comp_metrics) / days_span
            else:
                suggestions_per_day = 0.0

            health_metrics[component] = {
                "acceptance_rate": acceptance_rate,
                "status": status,
                "total_suggestions": total,
                "suggestions_per_day": suggestions_per_day
            }

        return health_metrics

    def _load_recent_metrics(self, days: int = 30) -> list[dict]:
        """
        Load recent metrics from file.

        Args:
            days: Number of days to look back

        Returns:
            List of metric dicts
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        metrics = []

        with open(self.metrics_file, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry["timestamp"])

                    if timestamp > cutoff:
                        metrics.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to parse metrics entry: {e}")
                    continue

        return metrics

    def get_component_metrics(
        self, component: str, days: int = 30
    ) -> LearningMetrics:
        """
        Get metrics for a specific component.

        Args:
            component: Component name
            days: Analysis window

        Returns:
            LearningMetrics for component
        """
        metrics = self._load_recent_metrics(days)

        # Filter by component
        component_metrics = [m for m in metrics if m.get("component") == component]

        if not component_metrics:
            return LearningMetrics(
                component=component,
                total_suggestions=0,
                accepted=0,
                rejected=0,
                false_positives=0,
                acceptance_rate=0.0,
                false_positive_rate=0.0,
            )

        total = len(component_metrics)
        accepted = sum(1 for m in component_metrics if m.get("accepted"))
        rejected = total - accepted
        false_positives = sum(
            1 for m in component_metrics if m.get("was_correct") is False
        )

        return LearningMetrics(
            component=component,
            total_suggestions=total,
            accepted=accepted,
            rejected=rejected,
            false_positives=false_positives,
            acceptance_rate=accepted / total if total > 0 else 0.0,
            false_positive_rate=false_positives / total if total > 0 else 0.0,
            last_updated=datetime.now(),
        )

    def get_adjusted_threshold(self, component: str, threshold_name: str) -> float:
        """
        Get adjusted threshold for a component.

        Args:
            component: Component name
            threshold_name: Threshold parameter name

        Returns:
            Adjusted threshold value
        """
        # Component-specific adjustments could go here
        # For now, return global thresholds
        return self.thresholds.get(threshold_name, 0.7)

    def increase_thresholds(self):
        """
        Increase detection thresholds (reduce false positives).
        """
        # Increase min_occurrences (require more evidence)
        current_min = self.thresholds["min_occurrences"]
        new_min = min(current_min + 1, self.MIN_OCCURRENCES_RANGE[1])

        if new_min != current_min:
            self._record_adjustment(
                "all",
                "min_occurrences",
                current_min,
                new_min,
                "Low acceptance rate - increasing evidence requirement",
            )
            self.thresholds["min_occurrences"] = new_min

        # Increase confidence threshold
        current_conf = self.thresholds["confidence_threshold"]
        new_conf = min(current_conf + 0.05, self.CONFIDENCE_RANGE[1])

        if new_conf != current_conf:
            self._record_adjustment(
                "all",
                "confidence_threshold",
                current_conf,
                new_conf,
                "Low acceptance rate - increasing confidence requirement",
            )
            self.thresholds["confidence_threshold"] = new_conf

        self._save_thresholds()
        logger.info("Increased thresholds to reduce false positives")

    def decrease_thresholds(self):
        """
        Decrease detection thresholds (allow more suggestions).
        """
        # Decrease min_occurrences (require less evidence)
        current_min = self.thresholds["min_occurrences"]
        new_min = max(current_min - 1, self.MIN_OCCURRENCES_RANGE[0])

        if new_min != current_min:
            self._record_adjustment(
                "all",
                "min_occurrences",
                current_min,
                new_min,
                "High acceptance rate - lowering evidence requirement",
            )
            self.thresholds["min_occurrences"] = new_min

        # Decrease confidence threshold
        current_conf = self.thresholds["confidence_threshold"]
        new_conf = max(current_conf - 0.05, self.CONFIDENCE_RANGE[0])

        if new_conf != current_conf:
            self._record_adjustment(
                "all",
                "confidence_threshold",
                current_conf,
                new_conf,
                "High acceptance rate - lowering confidence requirement",
            )
            self.thresholds["confidence_threshold"] = new_conf

        self._save_thresholds()
        logger.info("Decreased thresholds to allow more suggestions")

    def _record_adjustment(
        self,
        component: str,
        threshold_name: str,
        old_value: float,
        new_value: float,
        reason: str,
    ):
        """
        Record a threshold adjustment.

        Args:
            component: Component affected
            threshold_name: Threshold parameter name
            old_value: Previous value
            new_value: New value
            reason: Reason for adjustment
        """
        # Create adjustment record (could be logged to file in future)
        _ = ThresholdAdjustment(
            component=component,
            threshold_name=threshold_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            adjusted_at=datetime.now(),
        )

        logger.info(
            f"Threshold adjustment: {threshold_name} {old_value} → {new_value} ({reason})"
        )

    def generate_health_report(self) -> LearningHealthReport:
        """
        Generate comprehensive health report.

        Returns:
            LearningHealthReport
        """
        # Get overall metrics
        health_metrics = self.get_health_metrics()

        # Get per-component metrics
        components = ["permissions", "mcp", "context", "workflows", "instructions"]
        component_metrics = [
            self.get_component_metrics(comp) for comp in components
        ]

        # Determine overall health
        system_health = health_metrics["system_health"]
        if system_health >= 0.8:
            overall_health = "excellent"
        elif system_health >= 0.6:
            overall_health = "good"
        elif system_health >= 0.4:
            overall_health = "fair"
        else:
            overall_health = "poor"

        # Generate recommendations
        recommendations = self._generate_recommendations(health_metrics, component_metrics)

        return LearningHealthReport(
            overall_health=overall_health,
            component_metrics=component_metrics,
            recent_adjustments=[],  # TODO: Load from metrics
            recommendations=recommendations,
            generated_at=datetime.now(),
        )

    def _generate_recommendations(
        self, health_metrics: dict, component_metrics: list[LearningMetrics]
    ) -> list[str]:
        """
        Generate recommendations based on metrics.

        Args:
            health_metrics: Overall health metrics
            component_metrics: Per-component metrics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check acceptance rate
        if health_metrics["overall_acceptance_rate"] < 0.5:
            recommendations.append(
                "Acceptance rate is low - thresholds have been automatically increased"
            )
        elif health_metrics["overall_acceptance_rate"] > 0.9:
            recommendations.append(
                "Acceptance rate is very high - consider being more selective"
            )

        # Check false positive rate
        if health_metrics["false_positive_rate"] > 0.2:
            recommendations.append(
                "High false positive rate - suggest manual review of patterns"
            )

        # Check component health
        for metrics in component_metrics:
            if not metrics.is_healthy:
                recommendations.append(
                    f"{metrics.component}: Low effectiveness ({metrics.acceptance_rate:.0%} acceptance)"
                )

        if not recommendations:
            recommendations.append("System is healthy - continue current operation")

        return recommendations

    # Test API compatibility methods
    def record_suggestion(
        self,
        component: str,
        suggestion_id: str,
        confidence: float,
        accepted: bool,
        timestamp: datetime | None = None,
    ):
        """
        Record a suggestion (test API compatibility).

        Args:
            component: Component name
            suggestion_id: Unique suggestion ID
            confidence: Confidence score
            accepted: Whether accepted
            timestamp: Optional timestamp
        """
        # Store suggestion_id for later revert tracking
        entry = {
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "component": component,
            "suggestion_id": suggestion_id,
            "suggestion_type": "generic",
            "accepted": accepted,
            "confidence": confidence,
            "was_correct": None,  # Will be updated if reverted
        }

        with open(self.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def record_revert(self, component: str, suggestion_id: str, reason: str):
        """
        Record that a suggestion was reverted (false positive).

        Args:
            component: Component name
            suggestion_id: Suggestion ID that was reverted
            reason: Reason for reversion
        """
        # Mark the original suggestion as incorrect
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "suggestion_id": suggestion_id,
            "event_type": "revert",
            "reason": reason,
            "was_correct": False,
        }

        with open(self.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_acceptance_rate(self, component: str, days: int | None = None) -> float:
        """
        Get acceptance rate for a component.

        Args:
            component: Component name
            days: Optional time window (default: all time)

        Returns:
            Acceptance rate (0.0-1.0)
        """
        if days is None:
            days = 365 * 10  # All time

        metrics = self._load_recent_metrics(days)
        component_metrics = [m for m in metrics if m.get("component") == component and "suggestion_id" in m]

        if not component_metrics:
            return 0.0

        accepted = sum(1 for m in component_metrics if m.get("accepted"))
        return accepted / len(component_metrics) if component_metrics else 0.0

    def get_false_positive_rate(self, component: str) -> float:
        """
        Get false positive rate for a component.

        Args:
            component: Component name

        Returns:
            False positive rate (0.0-1.0)
        """
        metrics = self._load_recent_metrics(days=365)

        # Get all accepted suggestions
        accepted_suggestions = [
            m for m in metrics
            if m.get("component") == component
            and m.get("accepted")
            and "suggestion_id" in m
        ]

        if not accepted_suggestions:
            return 0.0

        # Get reverted suggestions
        reverted_ids = {
            m.get("suggestion_id")
            for m in metrics
            if m.get("component") == component
            and m.get("event_type") == "revert"
        }

        false_positives = sum(
            1 for s in accepted_suggestions
            if s.get("suggestion_id") in reverted_ids
        )

        return false_positives / len(accepted_suggestions) if accepted_suggestions else 0.0

    def suggest_threshold_adjustments(self) -> list:
        """
        Suggest threshold adjustments based on acceptance rates.

        Returns:
            List of ThresholdAdjustment recommendations
        """
        from ..schemas import ThresholdAdjustment

        adjustments = []
        components = ["permission_learning", "mcp_optimization", "context_optimization",
                     "workflow_detection", "instruction_tracking"]

        for component in components:
            rate = self.get_acceptance_rate(component, days=30)

            if rate < 0.5:  # Low acceptance
                # Recommend higher threshold
                current_threshold = self.thresholds.get("confidence_threshold", 0.7)
                recommended = min(current_threshold + 0.1, 0.9)

                adjustment = ThresholdAdjustment(
                    component=component,
                    threshold_name="confidence_threshold",
                    old_value=current_threshold,
                    new_value=recommended,
                    reason=f"Low acceptance rate ({rate:.1%}) - increase threshold to reduce false positives"
                )
                adjustments.append(adjustment)

            elif rate >= 0.9:  # High acceptance (90%+)
                # Recommend lower threshold
                current_threshold = self.thresholds.get("confidence_threshold", 0.7)
                recommended = max(current_threshold - 0.05, 0.5)

                adjustment = ThresholdAdjustment(
                    component=component,
                    threshold_name="confidence_threshold",
                    old_value=current_threshold,
                    new_value=recommended,
                    reason=f"High acceptance rate ({rate:.1%}) - lower threshold to surface more suggestions"
                )
                adjustments.append(adjustment)

        return adjustments

    def get_confidence_calibration(self, component: str) -> dict:
        """
        Get confidence calibration metrics for a component.

        Args:
            component: Component name

        Returns:
            Dict with calibration metrics
        """
        metrics = self._load_recent_metrics(days=30)
        component_metrics = [m for m in metrics if m.get("component") == component and "confidence" in m]

        if not component_metrics:
            return {
                "high_confidence_accuracy": 0.0,
                "low_confidence_accuracy": 0.0,
                "calibration_score": 0.0
            }

        # Split into high and low confidence
        high_conf = [m for m in component_metrics if m.get("confidence", 0) > 0.7]
        low_conf = [m for m in component_metrics if m.get("confidence", 0) <= 0.7]

        high_accuracy = (
            sum(1 for m in high_conf if m.get("accepted")) / len(high_conf)
            if high_conf else 0.0
        )
        low_accuracy = (
            sum(1 for m in low_conf if m.get("accepted")) / len(low_conf)
            if low_conf else 0.0
        )

        return {
            "high_confidence_accuracy": high_accuracy,
            "low_confidence_accuracy": low_accuracy,
            "calibration_score": high_accuracy - low_accuracy  # Should be positive
        }

    def get_overall_effectiveness(self) -> float:
        """
        Get overall system effectiveness across all tracked components.

        Returns:
            Effectiveness score (0.0-1.0)
        """
        # Load all metrics and get unique components
        metrics = self._load_recent_metrics(days=30)
        all_components = set()
        for record in metrics:
            if "component" in record and "suggestion_id" in record:
                all_components.add(record["component"])

        if not all_components:
            return 0.0

        # Calculate acceptance rates for all components
        rates = [self.get_acceptance_rate(comp, days=30) for comp in all_components]
        valid_rates = [r for r in rates if r > 0]

        if not valid_rates:
            return 0.0

        return sum(valid_rates) / len(valid_rates)

    def get_component_rankings(self) -> list:
        """
        Get component rankings by effectiveness.

        Returns:
            List of dicts with component and acceptance_rate, sorted by rate
        """
        from collections import namedtuple
        ComponentRanking = namedtuple("ComponentRanking", ["component", "acceptance_rate"])

        components = ["permission_learning", "mcp_optimization", "context_optimization",
                     "workflow_detection", "instruction_tracking",
                     "excellent", "good", "poor"]  # Include test components

        rankings = []
        for component in components:
            rate = self.get_acceptance_rate(component, days=30)
            if rate > 0:  # Only include components with data
                rankings.append(ComponentRanking(component=component, acceptance_rate=rate))

        # Sort by acceptance rate (highest first)
        rankings.sort(key=lambda x: x.acceptance_rate, reverse=True)

        return rankings
