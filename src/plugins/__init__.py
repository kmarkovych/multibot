"""Plugin system for the multibot."""

from src.plugins.base import BasePlugin
from src.plugins.loader import PluginLoader
from src.plugins.registry import PluginRegistry

__all__ = ["BasePlugin", "PluginRegistry", "PluginLoader"]
