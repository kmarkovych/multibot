"""Plugin registry for discovering and managing plugins."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.exceptions import PluginNotFoundError
from src.plugins.base import BasePlugin

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all available plugins.

    Responsibilities:
    - Discover plugins from directories
    - Register/unregister plugin classes
    - Create plugin instances with configuration
    - Resolve plugin dependencies
    """

    def __init__(self):
        self._plugin_classes: dict[str, type[BasePlugin]] = {}
        self._builtin_loaded = False

    def register(self, plugin_class: type[BasePlugin]) -> None:
        """Register a plugin class."""
        name = plugin_class.name
        if not name:
            raise ValueError(f"Plugin class {plugin_class} must have a name")

        if name in self._plugin_classes:
            logger.warning(f"Replacing existing plugin: {name}")

        self._plugin_classes[name] = plugin_class
        logger.debug(f"Registered plugin: {name} v{plugin_class.version}")

    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        if plugin_name in self._plugin_classes:
            del self._plugin_classes[plugin_name]
            logger.debug(f"Unregistered plugin: {plugin_name}")

    def get_plugin_class(self, name: str) -> type[BasePlugin]:
        """Get a plugin class by name."""
        if name not in self._plugin_classes:
            raise PluginNotFoundError(name)
        return self._plugin_classes[name]

    def create_plugin(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        bot_id: str | None = None,
        db: DatabaseManager | None = None,
    ) -> BasePlugin:
        """Create a plugin instance with the given configuration."""
        plugin_class = self.get_plugin_class(name)
        plugin = plugin_class(config)
        if bot_id:
            plugin.set_context(bot_id, db)
        return plugin

    def has_plugin(self, name: str) -> bool:
        """Check if a plugin is registered."""
        return name in self._plugin_classes

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugin_classes.keys())

    def get_plugin_info(self, name: str) -> dict[str, Any]:
        """Get information about a registered plugin."""
        plugin_class = self.get_plugin_class(name)
        return {
            "name": plugin_class.name,
            "description": plugin_class.description,
            "version": plugin_class.version,
            "author": plugin_class.author,
            "dependencies": list(plugin_class.dependencies),
            "supports_hot_reload": plugin_class.supports_hot_reload,
        }

    def resolve_dependencies(self, plugin_names: list[str]) -> list[str]:
        """
        Resolve plugin dependencies and return ordered list.

        Plugins are returned in order such that dependencies come before
        dependents. Raises ValueError if circular dependency detected.
        """
        resolved: list[str] = []
        seen: set[str] = set()
        visiting: set[str] = set()

        def visit(name: str) -> None:
            if name in resolved:
                return
            if name in visiting:
                raise ValueError(f"Circular dependency detected: {name}")

            visiting.add(name)

            plugin_class = self.get_plugin_class(name)
            for dep in plugin_class.dependencies:
                if dep not in seen:
                    visit(dep)

            visiting.remove(name)
            seen.add(name)
            resolved.append(name)

        for name in plugin_names:
            if name not in seen:
                visit(name)

        return resolved

    def load_builtin_plugins(self) -> None:
        """Load built-in plugins from the builtin directory."""
        if self._builtin_loaded:
            return

        from src.admin.plugin import AdminPlugin
        from src.plugins.builtin.billing import BillingPlugin
        from src.plugins.builtin.error_handler import ErrorHandlerPlugin
        from src.plugins.builtin.help import HelpPlugin
        from src.plugins.builtin.start import StartPlugin

        self.register(StartPlugin)
        self.register(HelpPlugin)
        self.register(ErrorHandlerPlugin)
        self.register(AdminPlugin)
        self.register(BillingPlugin)

        self._builtin_loaded = True
        logger.info(f"Loaded {len(self._plugin_classes)} built-in plugins")

    def discover_plugins(self, *directories: Path | str) -> int:
        """
        Scan directories for plugin modules and packages.

        A valid plugin can be:
        1. A .py file (not starting with _) with a BasePlugin subclass
        2. A directory with __init__.py that exports 'plugin'

        Returns the number of plugins discovered.
        """
        from src.plugins.loader import PluginLoader

        loader = PluginLoader(self)
        count = 0

        for directory in directories:
            path = Path(directory)
            if not path.exists():
                logger.warning(f"Plugin directory not found: {path}")
                continue

            # Discover .py files
            for plugin_file in path.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue

                try:
                    plugin_class = loader.load_plugin(plugin_file)
                    self.register(plugin_class)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to load plugin from {plugin_file}: {e}")

            # Discover plugin packages (directories with __init__.py)
            for subdir in path.iterdir():
                if not subdir.is_dir():
                    continue
                if subdir.name.startswith("_"):
                    continue

                init_file = subdir / "__init__.py"
                if init_file.exists():
                    try:
                        plugin_class = loader.load_plugin(init_file)
                        self.register(plugin_class)
                        count += 1
                    except Exception as e:
                        logger.error(f"Failed to load plugin from {subdir}: {e}")

        logger.info(f"Discovered {count} plugins from {len(directories)} directories")
        return count
