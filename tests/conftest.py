"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import Generator

import pytest

from src.core.config import AppConfig, BotConfig
from src.plugins.registry import PluginRegistry


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app_config() -> AppConfig:
    """Create a test application config."""
    return AppConfig(
        database_url="postgresql://test:test@localhost:5432/test",
        admin_bot_token="test:token",
        admin_allowed_users="123456789",
        health_check_enabled=True,
        health_check_port=8080,
        log_level="DEBUG",
        log_format="text",
    )


@pytest.fixture
def bot_config() -> BotConfig:
    """Create a test bot config."""
    return BotConfig(
        id="test_bot",
        name="Test Bot",
        description="A test bot",
        token="123456:ABCdefGHIjklMNOpqrsTUVwxyz",
        enabled=True,
        mode="polling",
        plugins=[],
    )


@pytest.fixture
def plugin_registry() -> PluginRegistry:
    """Create a plugin registry with built-in plugins."""
    registry = PluginRegistry()
    registry.load_builtin_plugins()
    return registry
