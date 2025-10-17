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

    def get_health_metrics(self) -> dict[str, float]:
        """
        Get health metrics for learning system.

        Returns:
            Dict with health metrics
        """
        if not self.metrics_file.exists():
            return {
                "overall_acceptance_rate": 1.0,
                "false_positive_rate": 0.0,
                "system_health": 1.0,
            }

        # Load recent metrics
        metrics = self._load_recent_metrics(days=30)

        if not metrics:
            return {
                "overall_acceptance_rate": 1.0,
                "false_positive_rate": 0.0,
                "system_health": 1.0,
            }

        # Calculate rates
        total = len(metrics)
        accepted = sum(1 for m in metrics if m.get("accepted"))
        false_positives = sum(
            1 for m in metrics if m.get("was_correct") is False
        )

        acceptance_rate = accepted / total if total > 0 else 1.0
        false_positive_rate = false_positives / total if total > 0 else 0.0

        # Calculate overall health (weighted)
        system_health = (
            (acceptance_rate * 0.7)  # 70% weight on acceptance
            + ((1.0 - false_positive_rate) * 0.3)  # 30% weight on low false positives
        )

        return {
            "overall_acceptance_rate": acceptance_rate,
            "false_positive_rate": false_positive_rate,
            "system_health": system_health,
            "total_suggestions": total,
        }

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
        adjustment = ThresholdAdjustment(
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
