"""
Base generator class with common functionality for CLAUDE.md generation.

Enforces source/artifact separation with explicit declarations.
"""

import logging
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateError

from ..schemas import GenerationHeader, GenerationResult, GitStatus

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """
    Base class for CLAUDE.md generators with source/artifact protection.

    Subclasses MUST override:
        MANUAL_SOURCES: List of filenames that are manually edited
        GENERATED_ARTIFACTS: List of filenames that are auto-generated

    The base class enforces:
        1. No overlap between sources and artifacts
        2. Cannot write to source files
        3. All artifacts include generation headers
    """

    # Subclasses MUST override these
    MANUAL_SOURCES: list[str] = []
    GENERATED_ARTIFACTS: list[str] = []

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize generator with template directory.

        Raises:
            ValueError: If source/artifact declarations overlap
        """
        if template_dir is None:
            # Default to templates directory relative to this file
            template_dir = Path(__file__).parent.parent / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,  # We're generating markdown, not HTML
        )

        # Add custom filters
        self.env.filters["strftime"] = self._strftime_filter

        # Validate source/artifact declarations
        self._validate_declarations()

    def _strftime_filter(self, date: datetime, fmt: str) -> str:
        """Jinja2 filter for datetime formatting."""
        return date.strftime(fmt)

    # =========================================================================
    # Source/Artifact Protection Methods
    # =========================================================================

    def _validate_declarations(self) -> None:
        """
        Validate that source and artifact declarations don't overlap.

        Raises:
            ValueError: If there's overlap or invalid declarations
        """
        # Check for overlap
        sources_set = set(self.MANUAL_SOURCES)
        artifacts_set = set(self.GENERATED_ARTIFACTS)
        overlap = sources_set & artifacts_set

        if overlap:
            raise ValueError(
                f"Source/artifact overlap detected in {self.__class__.__name__}: "
                f"{', '.join(overlap)}. A file cannot be both a source and an artifact."
            )

        # Check for duplicates within each list
        if len(self.MANUAL_SOURCES) != len(sources_set):
            raise ValueError(
                f"Duplicate entries in MANUAL_SOURCES: {self.MANUAL_SOURCES}"
            )

        if len(self.GENERATED_ARTIFACTS) != len(artifacts_set):
            raise ValueError(
                f"Duplicate entries in GENERATED_ARTIFACTS: {self.GENERATED_ARTIFACTS}"
            )

        logger.debug(
            f"{self.__class__.__name__}: "
            f"{len(self.MANUAL_SOURCES)} sources, "
            f"{len(self.GENERATED_ARTIFACTS)} artifacts"
        )

    def read_source(self, path: Path) -> str:
        """
        Read content from a manual source file.

        Logs a warning if the file is not declared in MANUAL_SOURCES.

        Args:
            path: Path to source file

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
        """
        filename = path.name

        # Warn if reading undeclared source
        if filename not in self.MANUAL_SOURCES:
            logger.warning(
                f"{self.__class__.__name__}: Reading undeclared source '{filename}'. "
                f"Consider adding to MANUAL_SOURCES."
            )

        try:
            content = path.read_text(encoding="utf-8")
            logger.debug(f"Read source: {path} ({len(content)} chars)")
            return content

        except FileNotFoundError:
            logger.error(f"Source file not found: {path}")
            raise

        except PermissionError:
            logger.error(f"Permission denied reading source: {path}")
            raise

    def write_artifact(
        self,
        path: Path,
        content: str,
        source_files: list[str] | None = None,
        create_backup: bool = True,
    ) -> GenerationResult:
        """
        Write generated artifact with protection and header.

        This method enforces:
        1. Cannot write to files declared as MANUAL_SOURCES
        2. Can only write to files declared as GENERATED_ARTIFACTS
        3. All artifacts get generation headers

        Args:
            path: Path to artifact file
            content: Content to write
            source_files: List of source files used (for header)
            create_backup: Whether to create backup before writing

        Returns:
            GenerationResult with success/error information

        Raises:
            ValueError: If trying to write to a source file or undeclared artifact
        """
        filename = path.name

        # Critical: Prevent writing to sources
        if filename in self.MANUAL_SOURCES:
            error_msg = (
                f"PROTECTION VIOLATION: Cannot write to source file '{filename}'. "
                f"This file is declared as a MANUAL_SOURCE in {self.__class__.__name__}."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Enforce declaration
        if filename not in self.GENERATED_ARTIFACTS:
            error_msg = (
                f"Undeclared artifact '{filename}'. "
                f"Add to GENERATED_ARTIFACTS in {self.__class__.__name__}."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Generate header
        header = self._generate_header(path, source_files or [])

        # Add header to content
        final_content = f"{header}\n\n{content}"

        # Use existing write_file method (with backup support)
        result = self.write_file(path, final_content, create_backup=create_backup)

        # Add metadata to result
        if result.success:
            result.stats["header_added"] = True
            result.stats["source_files"] = source_files or []

        return result

    def _generate_header(self, path: Path, source_files: list[str]) -> str:
        """
        Generate HTML comment header for artifacts.

        The header is invisible when markdown is rendered but visible
        in the source file, making it clear this is auto-generated.

        Args:
            path: Path to the artifact being generated
            source_files: List of source files used in generation

        Returns:
            HTML comment string
        """
        header_data = GenerationHeader(
            generator_name=self.__class__.__name__,
            generated_at=datetime.now(),
            source_files=source_files,
            warning_message="AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY",
        )

        return header_data.to_html_comment()

    @abstractmethod
    def generate(self) -> GenerationResult:
        """
        Generate the artifact.

        Subclasses must implement this method to perform the actual generation.

        Returns:
            GenerationResult indicating success/failure
        """
        pass

    # =========================================================================
    # Legacy Methods (maintained for backward compatibility)
    # =========================================================================

    def get_current_git_status(self) -> GitStatus:
        """Get current git repository status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self._get_repo_root(),
            )

            if result.returncode == 0:
                if not result.stdout.strip():
                    return GitStatus()  # Clean repository

                # Parse git status output
                lines = result.stdout.strip().split("\n")
                modified = sum(1 for line in lines if line.startswith(" M"))
                added = sum(1 for line in lines if line.startswith("A"))
                untracked = sum(1 for line in lines if line.startswith("??"))

                return GitStatus(modified=modified, added=added, untracked=untracked)

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as e:
            logger.warning(f"Failed to get git status: {e}")

        # Return unknown status on any error
        return GitStatus()

    def _get_repo_root(self) -> Path:
        """Get the root directory of the git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except Exception:
            pass

        # Fallback: assume we're in nixos-config
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists() and (current / "flake.nix").exists():
                return current
            current = current.parent

        return Path.cwd()

    def create_backup(self, file_path: Path) -> Path | None:
        """Create backup of existing file in .backups directory."""
        if not file_path.exists():
            return None

        # Create .backups directory next to the file
        backups_dir = file_path.parent / ".backups"
        backups_dir.mkdir(exist_ok=True)

        # Create backup filename with timestamp
        backup_filename = (
            f"{file_path.name}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        backup_path = backups_dir / backup_filename

        try:
            import shutil

            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

            # Cleanup old backups, keeping 5 most recent
            self.cleanup_old_backups(file_path, keep_count=5)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)

        except TemplateError as e:
            raise RuntimeError(f"Template rendering failed: {e}") from e

    def write_file(
        self, file_path: Path, content: str, create_backup: bool = True
    ) -> GenerationResult:
        """Write content to file with optional backup."""
        errors = []
        warnings = []
        backup_path = None

        try:
            # Create backup if requested and file exists
            if create_backup:
                backup_path = self.create_backup(file_path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Successfully wrote {file_path}")

            return GenerationResult(
                success=True,
                output_path=str(file_path),
                backup_path=str(backup_path) if backup_path else None,
                errors=errors,
                warnings=warnings,
                stats={
                    "file_size": len(content),
                    "line_count": content.count("\n") + 1,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            error_msg = f"Failed to write {file_path}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

            # Try to restore backup if write failed
            if backup_path and backup_path.exists():
                try:
                    import shutil

                    shutil.copy2(backup_path, file_path)
                    warnings.append("Restored from backup after write failure")
                except Exception as restore_e:
                    errors.append(f"Failed to restore backup: {restore_e}")

            return GenerationResult(
                success=False,
                output_path=str(file_path),
                backup_path=str(backup_path) if backup_path else None,
                errors=errors,
                warnings=warnings,
                stats={},
            )

    def validate_template_exists(self, template_name: str) -> bool:
        """Check if template file exists."""
        template_path = self.template_dir / template_name
        return template_path.exists()

    def get_template_info(self, template_name: str) -> dict[str, Any]:
        """Get information about a template."""
        template_path = self.template_dir / template_name

        if not template_path.exists():
            return {"exists": False}

        try:
            stat = template_path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "path": str(template_path),
            }
        except Exception as e:
            logger.warning(f"Failed to get template info: {e}")
            return {"exists": True, "error": str(e)}

    def cleanup_old_backups(self, file_path: Path, keep_count: int = 5):
        """Remove old backup files from .backups directory, keeping only the most recent."""
        try:
            backups_dir = file_path.parent / ".backups"
            if not backups_dir.exists():
                return

            backup_pattern = f"{file_path.name}.backup-*"
            backup_files = list(backups_dir.glob(backup_pattern))

            if len(backup_files) <= keep_count:
                return

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Remove excess backups
            for old_backup in backup_files[keep_count:]:
                try:
                    old_backup.unlink()
                    logger.info(f"Removed old backup: {old_backup}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {old_backup}: {e}")

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
