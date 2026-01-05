"""Plugin system for the multibot."""

from src.plugins.base import BasePlugin
from src.plugins.registry import PluginRegistry
from src.plugins.loader import PluginLoader

__all__ = ["BasePlugin", "PluginRegistry", "PluginLoader"]
