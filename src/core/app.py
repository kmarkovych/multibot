"""Main application orchestrator."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.bot_manager import BotManager
from src.core.config import AppConfig, ConfigManager
from src.core.dispatcher_factory import DispatcherFactory
from src.database.connection import DatabaseManager
from src.plugins.registry import PluginRegistry
from src.utils.signals import SignalHandler

if TYPE_CHECKING:
    from src.health.server import HealthServer
    from src.stats.collector import StatsCollector
    from src.utils.watcher import ConfigWatcher
    from src.webhook.server import WebhookServer

logger = logging.getLogger(__name__)


class MultibotApplication:
    """
    Main application class that orchestrates all components.

    Responsibilities:
    - Initialize database connection pool
    - Start health check HTTP server
    - Initialize bot manager
    - Start config file watcher for hot reload
    - Handle graceful shutdown
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.config_manager = ConfigManager(config)

        # Core components
        self.db: DatabaseManager | None = None
        self.bot_manager: BotManager | None = None
        self.plugin_registry: PluginRegistry | None = None
        self.dispatcher_factory: DispatcherFactory | None = None
        self.stats_collector: StatsCollector | None = None

        # Servers
        self.health_server: HealthServer | None = None
        self.webhook_server: WebhookServer | None = None

        # Hot reload
        self.config_watcher: ConfigWatcher | None = None

        # Signal handling
        self.signal_handler = SignalHandler()

    async def start(self) -> None:
        """Start all application components."""
        logger.info("Starting Multibot Application...")

        # Setup signal handlers
        self.signal_handler.setup()
        self.signal_handler.on_shutdown(self.shutdown)
        self.signal_handler.on_reload(self._reload_all_configs)

        # Initialize database
        await self._init_database()

        # Initialize stats collector
        await self._init_stats_collector()

        # Initialize plugin registry
        await self._init_plugins()

        # Initialize bot manager
        await self._init_bot_manager()

        # Load and start bots from config
        await self._load_and_start_bots()

        # Start health server
        if self.config.health.enabled:
            await self._start_health_server()

        # Start webhook server if enabled
        if self.config.webhook.enabled:
            await self._start_webhook_server()

        # Start config watcher for hot reload
        if self.config.hot_reload.enabled:
            await self._start_config_watcher()

        logger.info("Multibot Application started successfully")

        # Wait for shutdown signal
        await self.signal_handler.wait_for_shutdown()

    async def shutdown(self) -> None:
        """Graceful shutdown of all components."""
        logger.info("Shutting down Multibot Application...")

        # Stop config watcher
        if self.config_watcher:
            await self.config_watcher.stop()

        # Stop all bots
        if self.bot_manager:
            await self.bot_manager.shutdown()

        # Stop stats collector (flushes remaining data)
        if self.stats_collector:
            await self.stats_collector.stop()

        # Stop webhook server
        if self.webhook_server:
            await self.webhook_server.stop()

        # Stop health server
        if self.health_server:
            await self.health_server.stop()

        # Disconnect database
        if self.db:
            await self.db.disconnect()

        logger.info("Multibot Application shutdown complete")

    async def _init_database(self) -> None:
        """Initialize database connection."""
        self.db = DatabaseManager(self.config.database)
        await self.db.connect()
        logger.info("Database connection established")

    async def _init_stats_collector(self) -> None:
        """Initialize and start the stats collector."""
        from src.stats.collector import StatsCollector

        self.stats_collector = StatsCollector(self.db, flush_interval=60)
        await self.stats_collector.start()
        logger.info("Stats collector started")

    async def _init_plugins(self) -> None:
        """Initialize plugin registry and load plugins."""
        self.plugin_registry = PluginRegistry()

        # Load built-in plugins
        self.plugin_registry.load_builtin_plugins()

        # Discover custom plugins
        plugins_dir = Path(self.config.plugins_dir)
        if plugins_dir.exists():
            self.plugin_registry.discover_plugins(plugins_dir)

        logger.info(f"Loaded {len(self.plugin_registry.list_plugins())} plugins")

    async def _init_bot_manager(self) -> None:
        """Initialize bot manager."""
        self.dispatcher_factory = DispatcherFactory(
            plugin_registry=self.plugin_registry,
            db=self.db,
            stats_collector=self.stats_collector,
        )

        self.bot_manager = BotManager(
            db=self.db,
            dispatcher_factory=self.dispatcher_factory,
            config_manager=self.config_manager,
        )

        logger.info("Bot manager initialized")

    async def _load_and_start_bots(self) -> None:
        """Load bot configurations and start enabled bots."""
        config_dir = Path(self.config.config_dir)
        bot_configs = self.config_manager.load_bot_configs(config_dir)

        logger.info(f"Found {len(bot_configs)} bot configurations")

        for bot_id, bot_config in bot_configs.items():
            try:
                # Create bot
                await self.bot_manager.create_bot(bot_config)

                # Start if enabled
                if bot_config.enabled:
                    await self.bot_manager.start_bot(bot_id)

            except Exception as e:
                logger.error(f"Failed to start bot {bot_id}: {e}")

        running = len(self.bot_manager.get_running_bots())
        logger.info(f"Started {running} bots")

    async def _start_health_server(self) -> None:
        """Start the health check HTTP server."""
        from src.health.server import HealthServer

        self.health_server = HealthServer(
            host=self.config.health.host,
            port=self.config.health.port,
            bot_manager=self.bot_manager,
            db=self.db,
        )
        await self.health_server.start()
        logger.info(f"Health server started on port {self.config.health.port}")

    async def _start_webhook_server(self) -> None:
        """Start the webhook server."""
        from src.webhook.server import WebhookServer

        self.webhook_server = WebhookServer(
            host=self.config.webhook.host,
            port=self.config.webhook.port,
            bot_manager=self.bot_manager,
            base_url=self.config.webhook.base_url,
            secret=self.config.webhook.secret,
        )
        await self.webhook_server.start()
        logger.info(f"Webhook server started on port {self.config.webhook.port}")

    async def _start_config_watcher(self) -> None:
        """Start watching config files for hot reload."""
        from src.utils.watcher import ConfigWatcher

        watch_paths = [
            self.config.config_dir,
            self.config.plugins_dir,
        ]

        self.config_watcher = ConfigWatcher(
            watch_paths=watch_paths,
            on_config_change=self._on_config_change,
            on_plugin_change=self._on_plugin_change,
        )
        await self.config_watcher.start()
        logger.info(f"Config watcher started for: {watch_paths}")

    async def _on_config_change(self, bot_id: str, config_path: Path) -> None:
        """Handle bot configuration changes."""
        logger.info(f"Config changed for bot: {bot_id}")

        try:
            # Reload configuration
            new_config = self.config_manager.reload_bot_config(bot_id)
            if not new_config:
                logger.warning(f"Could not reload config for bot: {bot_id}")
                return

            # Reload the bot
            await self.bot_manager.reload_bot(bot_id, new_config)
            logger.info(f"Bot {bot_id} reloaded successfully")

        except Exception as e:
            logger.error(f"Failed to reload bot {bot_id}: {e}")

    async def _on_plugin_change(self, plugin_name: str, plugin_path: Path) -> None:
        """Handle plugin file changes."""
        logger.info(f"Plugin changed: {plugin_name}")

        try:
            from src.plugins.loader import PluginLoader

            loader = PluginLoader(self.plugin_registry)

            # Reload the plugin
            if loader.is_loaded(plugin_name):
                loader.reload_plugin(plugin_name)
            else:
                plugin_class = loader.load_plugin(plugin_path)
                self.plugin_registry.register(plugin_class)

            # Find and reload bots using this plugin
            for bot_id, managed_bot in self.bot_manager.get_all_bots().items():
                for plugin_config in managed_bot.config.plugins:
                    if plugin_config.name == plugin_name:
                        await self.bot_manager.reload_bot(bot_id, managed_bot.config)
                        break

            logger.info(f"Plugin {plugin_name} reloaded successfully")

        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_name}: {e}")

    async def _reload_all_configs(self) -> None:
        """Reload all bot configurations (called on SIGHUP)."""
        logger.info("Reloading all configurations...")

        config_dir = Path(self.config.config_dir)
        bot_configs = self.config_manager.load_bot_configs(config_dir)

        for bot_id, bot_config in bot_configs.items():
            try:
                if self.bot_manager.get_bot(bot_id):
                    await self.bot_manager.reload_bot(bot_id, bot_config)
                else:
                    await self.bot_manager.create_bot(bot_config)
                    if bot_config.enabled:
                        await self.bot_manager.start_bot(bot_id)
            except Exception as e:
                logger.error(f"Failed to reload bot {bot_id}: {e}")

        logger.info("All configurations reloaded")
