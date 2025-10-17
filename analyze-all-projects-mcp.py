#!/usr/bin/env python3
"""
Global Multi-Project MCP Analyzer

Scans all projects in home directory for MCP configurations and generates
a system-wide aggregated analysis with optimization recommendations.

This provides the global view of MCP servers across all projects,
addressing the limitation of project-scoped analysis.
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from claude_automation.analyzers.mcp_usage_analyzer import MCPUsageAnalyzer
from claude_automation.schemas import (
    MCPServerInfo,
    MCPServerStatus,
    MCPToolUsage,
    MCPUsageRecommendation,
    MCPServerSessionUtilization,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GlobalMCPAnalyzer:
    """Analyzes MCP usage across all projects system-wide."""

    def __init__(self, home_dir: Path, analysis_period_days: int = 30):
        self.home_dir = home_dir
        self.analysis_period_days = analysis_period_days
        self.projects = []
        self.global_servers = {}  # server_name -> MCPServerInfo
        self.global_tool_usage = []  # All MCPToolUsage entries
        self.global_recommendations = []  # All recommendations
        self.global_utilization = {}  # server_name -> MCPServerSessionUtilization

    def discover_projects(self) -> list[Path]:
        """Discover all projects with .claude/mcp.json configurations."""
        logger.info(f"Scanning {self.home_dir} for MCP-enabled projects...")

        projects = []
        for mcp_config in self.home_dir.rglob(".claude/mcp.json"):
            # Skip if in hidden directories (except .claude itself)
            path_parts = mcp_config.parts
            if any(part.startswith(".") and part != ".claude" for part in path_parts):
                continue

            project_path = mcp_config.parent.parent  # Go up from .claude/mcp.json
            projects.append(project_path)

        logger.info(f"Found {len(projects)} MCP-enabled projects")
        return projects

    def analyze_all_projects(self) -> dict:
        """Run MCP analysis for all discovered projects and aggregate results."""
        self.projects = self.discover_projects()

        if not self.projects:
            logger.warning("No MCP-enabled projects found")
            return self._build_report()

        # Analyze each project
        for project_path in self.projects:
            try:
                logger.info(f"Analyzing: {project_path.name}")
                self._analyze_project(project_path)
            except Exception as e:
                logger.error(f"Failed to analyze {project_path}: {e}")

        # Also analyze global config
        self._analyze_global_config()

        return self._build_report()

    def _analyze_project(self, project_path: Path):
        """Analyze a single project and add to global state."""
        analyzer = MCPUsageAnalyzer(project_path)
        config = analyzer.analyze(analysis_period_days=self.analysis_period_days)

        # Aggregate servers
        for server in config.configured_servers:
            if server.name not in self.global_servers:
                self.global_servers[server.name] = server
            else:
                # Merge info: if one shows connected, use that status
                existing = self.global_servers[server.name]
                if server.status == MCPServerStatus.CONNECTED:
                    existing.status = MCPServerStatus.CONNECTED

        # Aggregate tool usage
        self.global_tool_usage.extend(config.tool_usage)

        # Aggregate recommendations
        for rec in config.recommendations:
            # Add project context to recommendation
            rec.action = f"[{project_path.name}] {rec.action}"
            self.global_recommendations.append(rec)

        # Aggregate utilization
        for util in config.server_utilization:
            if util.server_name not in self.global_utilization:
                self.global_utilization[util.server_name] = util
            else:
                # Merge utilization metrics
                existing = self.global_utilization[util.server_name]
                existing.total_sessions += util.total_sessions
                existing.loaded_sessions += util.loaded_sessions
                existing.used_sessions += util.used_sessions

    def _analyze_global_config(self):
        """Check for servers in global ~/.claude.json."""
        global_config_path = self.home_dir / ".claude.json"
        if not global_config_path.exists():
            return

        try:
            with open(global_config_path) as f:
                global_config = json.load(f)
                mcp_servers = global_config.get("mcpServers", {})

                for name, config in mcp_servers.items():
                    if name not in self.global_servers:
                        # Create server info for global server
                        server = MCPServerInfo(
                            name=name,
                            type="unknown",
                            command=config.get("command", ""),
                            args=config.get("args", []),
                            status=MCPServerStatus.UNKNOWN,
                            description="",
                            is_configured=True,
                            config_location="global (~/.claude.json)",
                        )
                        self.global_servers[name] = server

        except Exception as e:
            logger.warning(f"Failed to parse global config: {e}")

    def _build_report(self) -> dict:
        """Build consolidated global report."""
        # Calculate aggregated metrics
        total_servers = len(self.global_servers)
        connected_servers = sum(
            1 for s in self.global_servers.values() if s.status == MCPServerStatus.CONNECTED
        )

        # Aggregate tool usage by server
        usage_by_server = defaultdict(lambda: {
            "invocation_count": 0,
            "total_tokens": 0,
            "success_count": 0,
            "error_count": 0,
        })

        for usage in self.global_tool_usage:
            usage_by_server[usage.server_name]["invocation_count"] += usage.invocation_count
            usage_by_server[usage.server_name]["total_tokens"] += usage.total_tokens
            usage_by_server[usage.server_name]["success_count"] += usage.success_count
            usage_by_server[usage.server_name]["error_count"] += usage.error_count

        # Find high-priority recommendations
        high_priority_recs = [
            r for r in self.global_recommendations if r.priority == 1
        ]

        # Calculate total sessions analyzed
        total_sessions = sum(
            util.total_sessions for util in self.global_utilization.values()
        ) // max(1, len(self.global_utilization))  # Avoid double-counting

        report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_period_days": self.analysis_period_days,
            "total_projects": len(self.projects),
            "total_servers": total_servers,
            "connected_servers": connected_servers,
            "total_sessions_analyzed": total_sessions,
            "servers": list(self.global_servers.values()),
            "usage_by_server": dict(usage_by_server),
            "utilization": list(self.global_utilization.values()),
            "recommendations": self.global_recommendations,
            "high_priority_recommendations": high_priority_recs,
            "projects_scanned": [str(p) for p in self.projects],
        }

        return report

    def generate_summary(self, report: dict) -> str:
        """Generate human-readable summary."""
        lines = []
        lines.append("=" * 70)
        lines.append("🌐 GLOBAL MCP SERVER ANALYSIS")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Analysis Period: Last {report['analysis_period_days']} days")
        lines.append(f"Projects Scanned: {report['total_projects']}")
        lines.append(f"Total Sessions: {report['total_sessions_analyzed']}")
        lines.append("")
        lines.append(f"📊 Servers: {report['connected_servers']}/{report['total_servers']} connected")
        lines.append("")

        # List servers by scope
        global_servers = [s for s in report['servers'] if 'global' in s.config_location.lower()]
        project_servers = [s for s in report['servers'] if 'project' in s.config_location.lower()]

        if global_servers:
            lines.append(f"Global Servers ({len(global_servers)}):")
            for server in global_servers:
                status_icon = "✓" if server.status == "connected" else "✗"
                lines.append(f"  {status_icon} {server.name}")

        if project_servers:
            lines.append(f"\nProject-Level Servers ({len(project_servers)}):")
            for server in project_servers:
                status_icon = "✓" if server.status == "connected" else "✗"
                lines.append(f"  {status_icon} {server.name} ({server.config_location})")

        # Show usage stats
        if report['usage_by_server']:
            lines.append("\n📈 Usage Statistics:")
            for server_name, stats in sorted(
                report['usage_by_server'].items(),
                key=lambda x: x[1]['invocation_count'],
                reverse=True
            ):
                invocations = stats['invocation_count']
                tokens = stats['total_tokens']
                lines.append(f"  • {server_name}: {invocations} calls, {tokens:,} tokens")

        # Show utilization
        if report['utilization']:
            lines.append("\n⚡ Utilization Rates:")
            for util in sorted(
                report['utilization'],
                key=lambda x: x.utilization_rate if hasattr(x, 'utilization_rate') else 0,
                reverse=True
            ):
                util_rate = util.utilization_rate if hasattr(util, 'utilization_rate') else 0
                lines.append(
                    f"  • {util.server_name}: {util_rate:.1f}% "
                    f"({util.used_sessions}/{util.loaded_sessions} sessions)"
                )

        # Show high-priority recommendations
        if report['high_priority_recommendations']:
            lines.append(f"\n⚠️  High-Priority Actions ({len(report['high_priority_recommendations'])}):")
            for rec in report['high_priority_recommendations'][:5]:
                lines.append(f"  • {rec.server_name}: {rec.reason}")
                lines.append(f"    → {rec.action}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def write_global_report(self, report: dict, output_path: Path):
        """Write detailed JSON report to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to dicts for JSON serialization
        json_report = {
            "timestamp": report["timestamp"],
            "analysis_period_days": report["analysis_period_days"],
            "total_projects": report["total_projects"],
            "total_servers": report["total_servers"],
            "connected_servers": report["connected_servers"],
            "total_sessions_analyzed": report["total_sessions_analyzed"],
            "servers": [
                {
                    "name": s.name,
                    "type": s.type,
                    "status": s.status.value if hasattr(s.status, 'value') else s.status,
                    "config_location": s.config_location,
                    "description": s.description,
                }
                for s in report["servers"]
            ],
            "usage_by_server": report["usage_by_server"],
            "utilization": [
                {
                    "server_name": u.server_name,
                    "scope": u.scope,
                    "total_sessions": u.total_sessions,
                    "loaded_sessions": u.loaded_sessions,
                    "used_sessions": u.used_sessions,
                    "utilization_rate": u.utilization_rate if hasattr(u, 'utilization_rate') else 0,
                    "estimated_overhead_tokens": u.estimated_overhead_tokens,
                }
                for u in report["utilization"]
            ],
            "recommendations": [
                {
                    "server_name": r.server_name,
                    "type": r.recommendation_type,
                    "reason": r.reason,
                    "action": r.action,
                    "priority": r.priority,
                }
                for r in report["recommendations"]
            ],
            "projects_scanned": report["projects_scanned"],
        }

        with open(output_path, "w") as f:
            json.dump(json_report, f, indent=2)

        logger.info(f"Wrote detailed report to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze MCP usage across all projects globally"
    )

    parser.add_argument(
        "--scan-home",
        action="store_true",
        help="Scan entire home directory for projects (default: True)",
    )

    parser.add_argument(
        "--analysis-period",
        type=int,
        default=30,
        help="Analysis period in days (default: 30)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".claude" / "global-mcp-analysis.json",
        help="Output path for detailed JSON report",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine scan directory
    scan_dir = Path.home() if args.scan_home else Path.cwd()

    logger.info(f"Starting global MCP analysis (scanning: {scan_dir})")

    try:
        # Run global analysis
        analyzer = GlobalMCPAnalyzer(scan_dir, args.analysis_period)
        report = analyzer.analyze_all_projects()

        # Generate and print summary
        summary = analyzer.generate_summary(report)
        print(summary)

        # Write detailed report
        analyzer.write_global_report(report, args.output)

        print(f"\n💾 Detailed report saved to: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Global MCP analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
