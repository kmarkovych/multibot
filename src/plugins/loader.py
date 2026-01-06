"""Dynamic plugin loading and reloading."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from src.core.exceptions import PluginLoadError
from src.plugins.base import BasePlugin

if TYPE_CHECKING:
    from src.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Handles dynamic loading and reloading of plugins.

    Uses importlib for module management and supports
    hot reloading of plugins without restarting the application.
    """

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._loaded_modules: dict[str, ModuleType] = {}
        self._module_paths: dict[str, Path] = {}

    def load_plugin(self, plugin_path: Path) -> type[BasePlugin]:
        """
        Load a plugin from a file path.

        Returns the plugin class, not an instance.
        """
        plugin_path = Path(plugin_path).resolve()

        if not plugin_path.exists():
            raise PluginLoadError(str(plugin_path), "File not found")

        if not plugin_path.suffix == ".py":
            raise PluginLoadError(str(plugin_path), "Not a Python file")

        # Create a unique module name
        # For __init__.py files (packages), use parent directory name
        if plugin_path.stem == "__init__":
            module_name = f"multibot_plugin_{plugin_path.parent.name}"
        else:
            module_name = f"multibot_plugin_{plugin_path.stem}"

        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError(str(plugin_path), "Could not create module spec")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_class = self._extract_plugin_class(module, plugin_path)

            # Store for reloading
            self._loaded_modules[plugin_class.name] = module
            self._module_paths[plugin_class.name] = plugin_path

            logger.info(f"Loaded plugin: {plugin_class.name} from {plugin_path}")
            return plugin_class

        except PluginLoadError:
            raise
        except Exception as e:
            raise PluginLoadError(str(plugin_path), str(e)) from e

    def _extract_plugin_class(
        self, module: ModuleType, plugin_path: Path
    ) -> type[BasePlugin]:
        """Extract the plugin class from a loaded module."""
        # First, check for explicit 'plugin' attribute
        if hasattr(module, "plugin"):
            plugin_attr = module.plugin
            if isinstance(plugin_attr, type) and issubclass(plugin_attr, BasePlugin):
                return plugin_attr

        # Otherwise, find the first BasePlugin subclass
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
            ):
                return obj

        raise PluginLoadError(
            str(plugin_path),
            "No BasePlugin subclass found. Either set 'plugin = YourClass' "
            "or define a class inheriting from BasePlugin.",
        )

    def reload_plugin(self, plugin_name: str) -> type[BasePlugin]:
        """
        Reload a plugin module.

        This invalidates all existing instances of the plugin.
        Bots using this plugin will need to get new instances.
        """
        if plugin_name not in self._loaded_modules:
            raise PluginLoadError(plugin_name, "Plugin not loaded, cannot reload")

        plugin_path = self._module_paths[plugin_name]
        old_module = self._loaded_modules[plugin_name]

        # Remove old module from sys.modules
        module_name = old_module.__name__
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Remove from our tracking
        del self._loaded_modules[plugin_name]
        del self._module_paths[plugin_name]

        # Unregister from registry
        self.registry.unregister(plugin_name)

        # Load fresh
        new_class = self.load_plugin(plugin_path)

        logger.info(f"Reloaded plugin: {plugin_name}")
        return new_class

    def unload_plugin(self, plugin_name: str) -> None:
        """Unload a plugin module from memory."""
        if plugin_name not in self._loaded_modules:
            return

        module = self._loaded_modules[plugin_name]
        module_name = module.__name__

        # Remove from sys.modules
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Remove from our tracking
        del self._loaded_modules[plugin_name]
        if plugin_name in self._module_paths:
            del self._module_paths[plugin_name]

        # Unregister from registry
        self.registry.unregister(plugin_name)

        logger.info(f"Unloaded plugin: {plugin_name}")

    def get_plugin_path(self, plugin_name: str) -> Path | None:
        """Get the file path for a loaded plugin."""
        return self._module_paths.get(plugin_name)

    def is_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self._loaded_modules
