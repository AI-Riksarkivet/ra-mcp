"""
Caching layer for RA-MCP server.
Provides persistent caching for API responses to improve performance.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional, Dict
import pickle

class SimpleCache:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache with optional directory."""
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "ra-mcp"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Different TTLs for different content types
        self.ttl_config = {
            'search': 3600,      # 1 hour for search results
            'alto': 86400,       # 24 hours for ALTO content
            'iiif': 86400,       # 24 hours for IIIF metadata
            'structure': 86400,  # 24 hours for document structure
        }

    def _get_cache_key(self, key_type: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from parameters."""
        # Create a stable string representation
        param_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.sha256(f"{key_type}:{param_str}".encode())
        return hash_obj.hexdigest()[:16]

    def _get_cache_path(self, cache_key: str, key_type: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key_type}_{cache_key}.cache"

    def get(self, key_type: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached value if it exists and is not expired."""
        cache_key = self._get_cache_key(key_type, params)
        cache_path = self._get_cache_path(cache_key, key_type)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)

            # Check if expired
            ttl = self.ttl_config.get(key_type, 3600)
            if time.time() - cached_data['timestamp'] > ttl:
                cache_path.unlink()  # Delete expired cache
                return None

            return cached_data['value']
        except Exception:
            # If cache is corrupted, delete it
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, key_type: str, params: Dict[str, Any], value: Any) -> None:
        """Store value in cache."""
        cache_key = self._get_cache_key(key_type, params)
        cache_path = self._get_cache_path(cache_key, key_type)

        cached_data = {
            'timestamp': time.time(),
            'params': params,
            'value': value
        }

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception:
            # Silently fail on cache write errors
            pass

    def clear(self, key_type: Optional[str] = None) -> int:
        """Clear cache files. Returns number of files deleted."""
        count = 0
        if key_type:
            pattern = f"{key_type}_*.cache"
        else:
            pattern = "*.cache"

        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass

        return count

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        stats = {}
        for key_type in self.ttl_config.keys():
            pattern = f"{key_type}_*.cache"
            stats[key_type] = len(list(self.cache_dir.glob(pattern)))
        stats['total'] = sum(stats.values())
        return stats


# Global cache instance
_cache_instance = None

def get_cache() -> SimpleCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache()
    return _cache_instance