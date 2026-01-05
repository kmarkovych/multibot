"""Tests for plugin system."""

import pytest

from src.core.exceptions import PluginNotFoundError
from src.plugins.base import BasePlugin
from src.plugins.registry import PluginRegistry


class DummyPlugin(BasePlugin):
    """A dummy plugin for testing."""

    name = "dummy"
    description = "A dummy plugin"
    version = "1.0.0"

    def setup_handlers(self, router):
        pass


class DependentPlugin(BasePlugin):
    """A plugin that depends on dummy."""

    name = "dependent"
    description = "Depends on dummy"
    version = "1.0.0"
    dependencies = {"dummy"}

    def setup_handlers(self, router):
        pass


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)

        assert registry.has_plugin("dummy")
        assert "dummy" in registry.list_plugins()

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)
        registry.unregister("dummy")

        assert not registry.has_plugin("dummy")

    def test_get_plugin_class(self):
        """Test getting a plugin class."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)

        plugin_class = registry.get_plugin_class("dummy")
        assert plugin_class is DummyPlugin

    def test_get_missing_plugin_raises(self):
        """Test that getting a missing plugin raises an error."""
        registry = PluginRegistry()

        with pytest.raises(PluginNotFoundError):
            registry.get_plugin_class("nonexistent")

    def test_create_plugin_instance(self):
        """Test creating a plugin instance."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)

        plugin = registry.create_plugin("dummy", config={"key": "value"})

        assert isinstance(plugin, DummyPlugin)
        assert plugin.config == {"key": "value"}

    def test_resolve_dependencies(self):
        """Test resolving plugin dependencies."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)
        registry.register(DependentPlugin)

        order = registry.resolve_dependencies(["dependent"])

        assert order == ["dummy", "dependent"]

    def test_resolve_dependencies_no_deps(self):
        """Test resolving plugins with no dependencies."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)

        order = registry.resolve_dependencies(["dummy"])

        assert order == ["dummy"]

    def test_load_builtin_plugins(self):
        """Test loading built-in plugins."""
        registry = PluginRegistry()
        registry.load_builtin_plugins()

        assert registry.has_plugin("start")
        assert registry.has_plugin("help")
        assert registry.has_plugin("error_handler")

    def test_get_plugin_info(self):
        """Test getting plugin information."""
        registry = PluginRegistry()
        registry.register(DummyPlugin)

        info = registry.get_plugin_info("dummy")

        assert info["name"] == "dummy"
        assert info["description"] == "A dummy plugin"
        assert info["version"] == "1.0.0"


class TestBasePlugin:
    """Tests for BasePlugin."""

    def test_plugin_config(self):
        """Test plugin configuration."""
        plugin = DummyPlugin(config={"welcome": "Hello"})

        assert plugin.get_config("welcome") == "Hello"
        assert plugin.get_config("missing", "default") == "default"

    def test_plugin_router_creation(self):
        """Test that router is created on access."""
        plugin = DummyPlugin()

        router = plugin.router

        assert router is not None
        assert router.name == "dummy"

    def test_plugin_context(self):
        """Test setting plugin context."""
        plugin = DummyPlugin()
        plugin.set_context(bot_id="test_bot")

        assert plugin.bot_id == "test_bot"

    def test_plugin_context_not_set_raises(self):
        """Test that accessing context before setting raises error."""
        plugin = DummyPlugin()

        with pytest.raises(RuntimeError):
            _ = plugin.bot_id
