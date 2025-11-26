#!/usr/bin/env python3
"""
Collect CI/CD metrics from GitHub Actions workflow runs.
Exports metrics for monitoring and trend analysis.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class CIMetricsCollector:
    """Collect metrics from GitHub Actions workflow runs."""

    def __init__(self, repo: str = None):
        """Initialize metrics collector."""
        self.repo = repo or self._get_repo()
        self.metrics: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "repository": self.repo,
            "metrics": {},
        }

    @staticmethod
    def _get_repo() -> str:
        """Get repository from git config."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
            # Extract owner/repo from URL
            if "github.com" in url:
                parts = url.split("/")
                return f"{parts[-2]}/{parts[-1].replace('.git', '')}"
        except (subprocess.CalledProcessError, IndexError):
            pass
        return "unknown/unknown"

    def collect_test_metrics(self) -> dict[str, Any]:
        """Collect test execution metrics from pytest."""
        metrics = {}

        # Try to read from pytest cache
        pytest_cache = Path(".pytest_cache")
        if pytest_cache.exists():
            # Could parse cache files, but for now use summary
            metrics["pytest_available"] = True
        else:
            metrics["pytest_available"] = False

        return metrics

    def collect_coverage_metrics(self) -> dict[str, Any]:
        """Collect code coverage metrics."""
        metrics = {}

        coverage_file = Path("coverage.xml")
        if coverage_file.exists():
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse(coverage_file)
                root = tree.getroot()

                # Extract line-rate (coverage percentage)
                line_rate = root.get("line-rate")
                if line_rate:
                    coverage_pct = float(line_rate) * 100
                    metrics["coverage_percentage"] = round(coverage_pct, 2)
                    metrics["coverage_threshold"] = 85
                    metrics["coverage_meets_threshold"] = coverage_pct >= 85

                # Count packages
                packages = root.findall("package")
                metrics["packages_count"] = len(packages)

            except Exception as e:
                metrics["coverage_error"] = str(e)
        else:
            metrics["coverage_available"] = False

        return metrics

    def collect_complexity_metrics(self) -> dict[str, Any]:
        """Collect code complexity metrics."""
        metrics = {}

        # Check if lizard analysis is available
        complexity_file = Path("/tmp/complexity.csv")
        if complexity_file.exists():
            try:
                import csv

                high_complexity = []
                with open(complexity_file) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            ccn = int(row.get("CCN", 0))
                            if ccn > 10:
                                high_complexity.append(
                                    {"file": row.get("Filename"), "ccn": ccn}
                                )
                        except (ValueError, TypeError):
                            pass

                metrics["high_complexity_count"] = len(high_complexity)
                metrics["high_complexity_functions"] = high_complexity[:5]

            except Exception as e:
                metrics["complexity_error"] = str(e)
        else:
            metrics["complexity_available"] = False

        return metrics

    def collect_test_execution_time(self) -> dict[str, Any]:
        """Collect test execution time metrics."""
        metrics = {}

        # Parse pytest output if available
        pytest_log = Path("/tmp/pytest.log")
        if pytest_log.exists():
            try:
                with open(pytest_log) as f:
                    content = f.read()

                # Extract timing info
                import re

                match = re.search(r"in ([\d.]+)s", content)
                if match:
                    execution_time = float(match.group(1))
                    metrics["test_execution_seconds"] = execution_time
                    metrics["test_execution_warning"] = execution_time > 30
                    metrics["test_execution_critical"] = execution_time > 60

            except Exception as e:
                metrics["timing_error"] = str(e)

        return metrics

    def collect_security_metrics(self) -> dict[str, Any]:
        """Collect security scanning metrics."""
        metrics = {}

        # Bandit results
        bandit_file = Path("/tmp/bandit.json")
        if bandit_file.exists():
            try:
                with open(bandit_file) as f:
                    data = json.load(f)

                issues = data.get("results", [])
                high_severity = [i for i in issues if i.get("severity") == "HIGH"]

                metrics["bandit_issues_total"] = len(issues)
                metrics["bandit_issues_high"] = len(high_severity)
                metrics["security_critical"] = len(high_severity) > 0

            except Exception as e:
                metrics["bandit_error"] = str(e)

        # pip-audit results
        pip_audit_file = Path("/tmp/pip-audit.json")
        if pip_audit_file.exists():
            try:
                with open(pip_audit_file) as f:
                    data = json.load(f)

                vulns = data.get("vulnerabilities", [])
                metrics["dependencies_vulnerable"] = len(vulns)
                metrics["dependencies_critical"] = len(vulns) > 0

            except Exception as e:
                metrics["pip_audit_error"] = str(e)

        return metrics

    def collect_all_metrics(self) -> dict[str, Any]:
        """Collect all available metrics."""
        self.metrics["metrics"] = {
            "test": self.collect_test_metrics(),
            "coverage": self.collect_coverage_metrics(),
            "complexity": self.collect_complexity_metrics(),
            "execution_time": self.collect_test_execution_time(),
            "security": self.collect_security_metrics(),
        }

        return self.metrics

    def export_json(self, output_file: str = None) -> str:
        """Export metrics as JSON."""
        if not output_file:
            output_file = (
                f"/tmp/ci-metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            )

        with open(output_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

        return output_file

    def export_prometheus(self, output_file: str = None) -> str:
        """Export metrics in Prometheus format."""
        if not output_file:
            output_file = (
                f"/tmp/ci-metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            )

        lines = [
            f"# Metrics for {self.metrics['repository']}",
            f"# Generated: {self.metrics['timestamp']}",
            "",
        ]

        # Add coverage metric
        coverage = self.metrics["metrics"].get("coverage", {})
        if "coverage_percentage" in coverage:
            lines.append(
                f"ci_coverage_percent{{{self._make_labels()}}} {coverage['coverage_percentage']}"
            )

        # Add test metrics
        exec_time = self.metrics["metrics"].get("execution_time", {})
        if "test_execution_seconds" in exec_time:
            lines.append(
                f"ci_test_duration_seconds{{{self._make_labels()}}} {exec_time['test_execution_seconds']}"
            )

        # Add security metrics
        security = self.metrics["metrics"].get("security", {})
        if "bandit_issues_total" in security:
            lines.append(
                f"ci_security_issues_total{{{self._make_labels()}}} {security['bandit_issues_total']}"
            )

        # Add complexity metrics
        complexity = self.metrics["metrics"].get("complexity", {})
        if "high_complexity_count" in complexity:
            lines.append(
                f"ci_high_complexity_count{{{self._make_labels()}}} {complexity['high_complexity_count']}"
            )

        with open(output_file, "w") as f:
            f.write("\n".join(lines))

        return output_file

    def _make_labels(self) -> str:
        """Create Prometheus labels."""
        return f'repo="{self.metrics["repository"]}"'

    def print_summary(self) -> None:
        """Print human-readable summary."""
        print("\n" + "=" * 60)
        print("CI/CD Metrics Summary")
        print("=" * 60)
        print(f"Repository: {self.metrics['repository']}")
        print(f"Timestamp: {self.metrics['timestamp']}")
        print("")

        # Coverage
        coverage = self.metrics["metrics"].get("coverage", {})
        if "coverage_percentage" in coverage:
            pct = coverage["coverage_percentage"]
            status = "✅" if coverage.get("coverage_meets_threshold") else "❌"
            print(f"Coverage: {status} {pct}% (threshold: {coverage.get('coverage_threshold', 'N/A')}%)")

        # Tests
        exec_time = self.metrics["metrics"].get("execution_time", {})
        if "test_execution_seconds" in exec_time:
            seconds = exec_time["test_execution_seconds"]
            status = "✅" if not exec_time.get("test_execution_warning") else "⚠️"
            print(f"Test Duration: {status} {seconds}s")

        # Security
        security = self.metrics["metrics"].get("security", {})
        if "bandit_issues_total" in security:
            total = security["bandit_issues_total"]
            high = security.get("bandit_issues_high", 0)
            status = "✅" if high == 0 else "❌"
            print(f"Security Issues: {status} {total} total, {high} high")

        if "dependencies_vulnerable" in security:
            vulns = security["dependencies_vulnerable"]
            status = "✅" if vulns == 0 else "⚠️"
            print(f"Vulnerable Dependencies: {status} {vulns}")

        # Complexity
        complexity = self.metrics["metrics"].get("complexity", {})
        if "high_complexity_count" in complexity:
            high = complexity["high_complexity_count"]
            status = "✅" if high == 0 else "⚠️"
            print(f"High Complexity Functions: {status} {high} functions (CCN > 10)")

        print("=" * 60 + "\n")


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect CI/CD metrics from workflow artifacts"
    )
    parser.add_argument(
        "--repo", help="Repository in owner/repo format (auto-detected if not provided)"
    )
    parser.add_argument(
        "--json", help="Export metrics as JSON to specified file"
    )
    parser.add_argument(
        "--prometheus",
        help="Export metrics in Prometheus format to specified file",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print summary to stdout"
    )

    args = parser.parse_args()

    # Create collector
    collector = CIMetricsCollector(repo=args.repo)

    # Collect all metrics
    collector.collect_all_metrics()

    # Export
    if args.json:
        json_file = collector.export_json(args.json)
        print(f"✅ Metrics exported to JSON: {json_file}")

    if args.prometheus:
        prom_file = collector.export_prometheus(args.prometheus)
        print(f"✅ Metrics exported to Prometheus: {prom_file}")

    if args.summary or (not args.json and not args.prometheus):
        collector.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
