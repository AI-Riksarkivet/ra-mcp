"""
CLI command for browsing Riksarkivet document pages.
"""

from .app import browse_app
from .browse_cmd import browse

__all__ = ["browse_app", "browse"]
