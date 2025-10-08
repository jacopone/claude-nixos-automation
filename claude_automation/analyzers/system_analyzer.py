"""
System analyzer for detecting hardware and running services.
Generates machine-specific local context.
"""

import logging
import socket
import subprocess
from pathlib import Path

from ..schemas import LocalContextConfig

logger = logging.getLogger(__name__)


class SystemAnalyzer:
    """Analyzes system for hardware info and running services."""

    def __init__(self, project_path: Path):
        """Initialize analyzer with project path."""
        self.project_path = project_path

    def analyze(self) -> LocalContextConfig:
        """
        Analyze system and build local context configuration.

        Returns:
            LocalContextConfig with system and project info
        """
        # Get hostname
        hostname = self._get_hostname()

        # Hardware info
        cpu_info = self._get_cpu_info()
        memory_total = self._get_memory_total()
        disk_usage = self._get_disk_usage()

        # Running services
        running_services = self._detect_running_services()

        # Git branches
        current_branches = self._get_current_branches()

        # Load existing WIP notes and experiments if file exists
        wip_notes, experiments = self._load_existing_notes()

        return LocalContextConfig(
            project_path=self.project_path,
            hostname=hostname,
            cpu_info=cpu_info,
            memory_total=memory_total,
            disk_usage=disk_usage,
            running_services=running_services,
            current_branches=current_branches,
            wip_notes=wip_notes,
            experiments=experiments,
        )

    def _get_hostname(self) -> str:
        """Get system hostname."""
        try:
            return socket.gethostname()
        except Exception as e:
            logger.warning(f"Failed to get hostname: {e}")
            return "unknown"

    def _get_cpu_info(self) -> str:
        """Get CPU information."""
        try:
            # Try lscpu first (Linux)
            result = subprocess.run(
                ["lscpu"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Extract model name
                for line in result.stdout.split("\n"):
                    if "Model name:" in line:
                        return line.split(":", 1)[1].strip()

            # Fallback: try /proc/cpuinfo
            if Path("/proc/cpuinfo").exists():
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if line.startswith("model name"):
                            return line.split(":", 1)[1].strip()

        except Exception as e:
            logger.warning(f"Failed to get CPU info: {e}")

        return "Unknown CPU"

    def _get_memory_total(self) -> str:
        """Get total system memory."""
        try:
            # Try /proc/meminfo (Linux)
            if Path("/proc/meminfo").exists():
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            # Convert KB to GB
                            kb = int(line.split()[1])
                            gb = kb / (1024 * 1024)
                            return f"{gb:.1f} GB"

            # Fallback: try free command
            result = subprocess.run(
                ["free", "-h"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                if len(lines) > 1:
                    mem_line = lines[1].split()
                    if len(mem_line) > 1:
                        return mem_line[1]

        except Exception as e:
            logger.warning(f"Failed to get memory info: {e}")

        return "Unknown"

    def _get_disk_usage(self) -> str:
        """Get disk usage for project directory."""
        try:
            result = subprocess.run(
                ["df", "-h", str(self.project_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    fields = lines[1].split()
                    if len(fields) >= 5:
                        # Format: Filesystem Size Used Avail Use% Mounted
                        return (
                            f"{fields[2]} used / {fields[1]} total ({fields[4]} full)"
                        )

        except Exception as e:
            logger.warning(f"Failed to get disk usage: {e}")

        return "Unknown"

    def _detect_running_services(self) -> list[str]:
        """Detect running services (Docker, PostgreSQL, etc.)."""
        services = []

        # Check Docker
        if self._is_service_running("docker"):
            services.append("Docker")
            # Get running containers
            try:
                result = subprocess.run(
                    ["docker", "ps", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    containers = result.stdout.strip().split("\n")
                    if containers:
                        services.append(f"  Containers: {', '.join(containers[:5])}")
            except Exception:
                pass

        # Check PostgreSQL
        if self._is_service_running("postgresql") or self._is_port_listening(5432):
            services.append("PostgreSQL (port 5432)")

        # Check MySQL/MariaDB
        if self._is_service_running("mysql") or self._is_port_listening(3306):
            services.append("MySQL/MariaDB (port 3306)")

        # Check Redis
        if self._is_service_running("redis") or self._is_port_listening(6379):
            services.append("Redis (port 6379)")

        # Check MongoDB
        if self._is_service_running("mongod") or self._is_port_listening(27017):
            services.append("MongoDB (port 27017)")

        # Check devenv processes
        if self._is_process_running("devenv"):
            services.append("DevEnv development environment")

        return services

    def _is_service_running(self, service_name: str) -> bool:
        """Check if a service is running via systemctl."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip() == "active"
        except Exception:
            return False

    def _is_port_listening(self, port: int) -> bool:
        """Check if a port is listening."""
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            return False

    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_current_branches(self) -> list[str]:
        """Get current git branches in the project."""
        branches = []

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                current = result.stdout.strip()
                if current and current != "HEAD":
                    branches.append(f"{current} (current)")

            # Get recent branches
            result = subprocess.run(
                [
                    "git",
                    "for-each-ref",
                    "--sort=-committerdate",
                    "refs/heads/",
                    "--format=%(refname:short)",
                    "--count=5",
                ],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                recent = [
                    b.strip() for b in result.stdout.strip().split("\n") if b.strip()
                ]
                for branch in recent:
                    if branch not in [b.split(" (")[0] for b in branches]:
                        branches.append(branch)

        except Exception as e:
            logger.warning(f"Failed to get git branches: {e}")

        return branches[:5]  # Limit to 5 branches

    def _load_existing_notes(self) -> tuple[list[str], list[str]]:
        """Load existing WIP notes and experiments from CLAUDE.local.md if it exists."""
        wip_notes = []
        experiments = []

        local_file = self.project_path / ".claude" / "CLAUDE.local.md"
        if not local_file.exists():
            return wip_notes, experiments

        try:
            content = local_file.read_text()
            lines = content.split("\n")

            # Parse WIP section
            in_wip = False
            in_experiments = False

            for line in lines:
                if line.startswith("## Work in Progress"):
                    in_wip = True
                    in_experiments = False
                    continue
                elif line.startswith("## Experiments"):
                    in_experiments = True
                    in_wip = False
                    continue
                elif line.startswith("##"):
                    in_wip = False
                    in_experiments = False
                    continue

                if in_wip and line.strip().startswith("-"):
                    wip_notes.append(line.strip()[2:])  # Remove "- "
                elif in_experiments and line.strip().startswith("-"):
                    experiments.append(line.strip()[2:])

        except Exception as e:
            logger.warning(f"Failed to load existing notes: {e}")

        return wip_notes, experiments
