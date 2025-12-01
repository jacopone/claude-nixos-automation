"""
Cached Nix parser that avoids re-parsing unchanged files.
"""

import hashlib
import json
import logging
from pathlib import Path

from ..schemas import ParsingResult
from .nix_parser import NixConfigParser

logger = logging.getLogger(__name__)


class CachedNixParser:
    """Wrapper around NixConfigParser that caches parsing results."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize cached parser.

        Args:
            cache_dir: Directory to store cache files. Defaults to ~/.claude/cache/nix_parser/
        """
        self.parser = NixConfigParser()
        if cache_dir is None:
            cache_dir = Path.home() / ".claude" / "cache" / "nix_parser"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key from file path and mtime."""
        mtime = file_path.stat().st_mtime
        key_str = f"{file_path}:{mtime}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file."""
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, cache_path: Path) -> ParsingResult | None:
        """Load parsing result from cache."""
        try:
            if not cache_path.exists():
                return None

            with open(cache_path) as f:
                data = json.load(f)

            # Reconstruct ParsingResult from dict
            return ParsingResult(**data)
        except Exception as e:
            logger.warning(f"Failed to load cache from {cache_path}: {e}")
            return None

    def _save_to_cache(self, cache_path: Path, result: ParsingResult):
        """Save parsing result to cache."""
        try:
            # Convert to dict for JSON serialization
            data = result.dict()
            with open(cache_path, "w") as f:
                json.dump(data, f)
            logger.debug(f"Saved parsing result to cache: {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache to {cache_path}: {e}")

    def parse_packages(self, file_path: Path) -> ParsingResult:
        """Parse packages.nix with caching.

        Args:
            file_path: Path to packages.nix file

        Returns:
            ParsingResult with tools or errors
        """
        cache_key = self._get_cache_key(file_path)
        cache_path = self._get_cache_path(cache_key)

        # Try to load from cache
        cached_result = self._load_from_cache(cache_path)
        if cached_result is not None:
            logger.debug(f"Using cached parsing result for {file_path}")
            return cached_result

        # Parse fresh
        logger.debug(f"Parsing {file_path} (cache miss)")
        result = self.parser.parse_packages(file_path)

        # Save to cache if successful
        if result.success:
            self._save_to_cache(cache_path, result)

        return result

    def parse_fish_config(self, file_path: Path) -> ParsingResult:
        """Parse Fish config with caching."""
        cache_key = self._get_cache_key(file_path)
        cache_path = self._get_cache_path(cache_key)

        # Try to load from cache
        cached_result = self._load_from_cache(cache_path)
        if cached_result is not None:
            logger.debug(f"Using cached parsing result for {file_path}")
            return cached_result

        # Parse fresh
        logger.debug(f"Parsing {file_path} (cache miss)")
        result = self.parser.parse_fish_config(file_path)

        # Save to cache if successful
        if result.success:
            self._save_to_cache(cache_path, result)

        return result

    def clear_cache(self):
        """Clear all cached parsing results."""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Cleared Nix parser cache")
