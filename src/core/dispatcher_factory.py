"""Dispatcher factory for creating configured dispatchers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from src.core.config import BotConfig
from src.plugins.base import BasePlugin

if TYPE_CHECKING:
    from aiogram import Bot

    from src.database.connection import DatabaseManager
    from src.plugins.registry import PluginRegistry
    from src.stats.collector import StatsCollector

logger = logging.getLogger(__name__)


class DispatcherFactory:
    """
    Factory for creating Dispatcher instances with configured plugins and middleware.

    Responsibilities:
    - Create Dispatcher with appropriate FSM storage
    - Load and attach plugins as routers
    - Configure middleware
    - Set up error handling
    """

    def __init__(
        self,
        plugin_registry: PluginRegistry,
        db: DatabaseManager | None = None,
        stats_collector: StatsCollector | None = None,
    ):
        self.plugin_registry = plugin_registry
        self.db = db
        self.stats_collector = stats_collector

    async def create_dispatcher(
        self,
        config: BotConfig,
        bot_id: str,
        bot: Bot | None = None,
    ) -> tuple[Dispatcher, list[BasePlugin]]:
        """Create a fully configured Dispatcher for a bot."""
        # Create FSM storage
        # In production, you might want Redis storage
        storage = MemoryStorage()

        # Create dispatcher
        dispatcher = Dispatcher(storage=storage)

        # Create main router
        main_router = Router(name=f"main_{bot_id}")

        # Load and attach plugins
        plugins = await self._attach_plugins(main_router, config, bot_id, bot)

        # Include main router in dispatcher
        dispatcher.include_router(main_router)

        # Setup middleware
        self._setup_middleware(dispatcher, config, bot_id)

        logger.info(f"Created dispatcher for bot: {bot_id}")
        return dispatcher, plugins

    async def _attach_plugins(
        self,
        router: Router,
        config: BotConfig,
        bot_id: str,
        bot: Bot | None = None,
    ) -> list[BasePlugin]:
        """Load and attach plugins to the router."""
        if not config.plugins:
            # Use default plugins if none specified
            config.plugins = [
                {"name": "start", "enabled": True, "config": {}},
                {"name": "help", "enabled": True, "config": {}},
                {"name": "error_handler", "enabled": True, "config": {}},
            ]

        # Collect enabled plugin names
        enabled_plugins = [
            p.name for p in config.plugins if p.enabled
        ]

        # Resolve dependencies
        try:
            ordered_plugins = self.plugin_registry.resolve_dependencies(enabled_plugins)
        except ValueError as e:
            logger.error(f"Plugin dependency error for bot {bot_id}: {e}")
            ordered_plugins = enabled_plugins

        # Load each plugin
        loaded_plugins: list[BasePlugin] = []
        for plugin_name in ordered_plugins:
            try:
                # Find plugin config
                plugin_config = {}
                for p in config.plugins:
                    if p.name == plugin_name:
                        plugin_config = p.config
                        break

                # Create plugin instance
                plugin = self.plugin_registry.create_plugin(
                    name=plugin_name,
                    config=plugin_config,
                    bot_id=bot_id,
                    db=self.db,
                )

                # Attach plugin's router
                router.include_router(plugin.router)
                loaded_plugins.append(plugin)

                logger.debug(f"Attached plugin {plugin_name} to bot {bot_id}")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name} for bot {bot_id}: {e}")

        # Call on_load for each plugin if bot is provided
        if bot:
            for plugin in loaded_plugins:
                try:
                    await plugin.on_load(bot)
                    logger.debug(f"Called on_load for plugin {plugin.name}")
                except Exception as e:
                    logger.error(f"Error in on_load for plugin {plugin.name}: {e}")

        logger.info(f"Loaded {len(loaded_plugins)} plugins for bot {bot_id}")
        return loaded_plugins

    def _setup_middleware(
        self,
        dispatcher: Dispatcher,
        config: BotConfig,
        bot_id: str,
    ) -> None:
        """Setup middleware for the dispatcher."""
        from src.middleware.database import DatabaseMiddleware
        from src.middleware.logging import LoggingMiddleware

        # Add logging middleware
        dispatcher.message.middleware(LoggingMiddleware(bot_id=bot_id))
        dispatcher.callback_query.middleware(LoggingMiddleware(bot_id=bot_id))

        # Add stats middleware if collector is available
        if self.stats_collector:
            from src.middleware.stats import StatsMiddleware

            stats_mw = StatsMiddleware(bot_id=bot_id, collector=self.stats_collector)
            dispatcher.message.middleware(stats_mw)
            dispatcher.callback_query.middleware(stats_mw)

        # Add database middleware if available
        if self.db:
            dispatcher.message.middleware(DatabaseMiddleware(db=self.db))
            dispatcher.callback_query.middleware(DatabaseMiddleware(db=self.db))

        # Add rate limiting if enabled
        if config.rate_limiting and config.rate_limiting.enabled:
            from src.middleware.rate_limit import RateLimitMiddleware

            rate_limit_mw = RateLimitMiddleware(
                rate=config.rate_limiting.default_rate,
                burst=config.rate_limiting.burst_size,
            )
            dispatcher.message.middleware(rate_limit_mw)

        logger.debug(f"Setup middleware for bot {bot_id}")
