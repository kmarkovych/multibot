"""Base plugin class for the multibot system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from aiogram import Bot, Router

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager


class BasePlugin(ABC):
    """
    Abstract base class for all plugins.

    Plugins are modular units of functionality that can be:
    - Loaded/unloaded at runtime
    - Shared across multiple bots
    - Bot-specific

    To create a plugin:
    1. Subclass BasePlugin
    2. Set class attributes (name, description, version)
    3. Implement setup_handlers() to register your handlers
    4. Optionally implement lifecycle hooks
    5. Export as `plugin = YourPluginClass` at module level
    """

    # Plugin metadata
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""

    # Dependencies on other plugins (loaded first)
    dependencies: set[str] = set()

    # Whether this plugin can be hot-reloaded
    supports_hot_reload: bool = True

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the plugin with optional configuration."""
        self.config = config or {}
        self._router: Router | None = None
        self._bot_id: str | None = None
        self._db: DatabaseManager | None = None

    @property
    def router(self) -> Router:
        """Get the plugin's router, creating it if needed."""
        if self._router is None:
            self._router = Router(name=self.name)
            self.setup_handlers(self._router)
        return self._router

    def set_context(
        self,
        bot_id: str,
        db: DatabaseManager | None = None,
    ) -> None:
        """Set runtime context for the plugin."""
        self._bot_id = bot_id
        self._db = db

    @property
    def bot_id(self) -> str:
        """Get the current bot ID."""
        if self._bot_id is None:
            raise RuntimeError("Plugin context not set. Call set_context() first.")
        return self._bot_id

    @property
    def db(self) -> DatabaseManager:
        """Get the database manager."""
        if self._db is None:
            raise RuntimeError("Database not available in plugin context.")
        return self._db

    @abstractmethod
    def setup_handlers(self, router: Router) -> None:
        """
        Register all handlers on the router.

        This method is called when the plugin is loaded.
        Override this to register your message handlers,
        command handlers, callback query handlers, etc.

        Example:
            @router.message(Command("mycommand"))
            async def handle_mycommand(message: Message):
                await message.answer("Hello!")
        """
        pass

    async def on_load(self, bot: Bot) -> None:
        """
        Called when the plugin is loaded for a bot.

        Override to perform initialization tasks like:
        - Loading data from database
        - Setting up external connections
        - Initializing caches
        """
        pass

    async def on_unload(self, bot: Bot) -> None:
        """
        Called when the plugin is unloaded from a bot.

        Override to perform cleanup tasks like:
        - Saving state to database
        - Closing connections
        - Releasing resources
        """
        pass

    async def on_bot_start(self, bot: Bot) -> None:
        """
        Called when the bot starts polling/webhook.

        Override to perform tasks that should happen when the bot
        becomes active, like sending startup notifications.
        """
        pass

    async def on_bot_stop(self, bot: Bot) -> None:
        """
        Called when the bot stops.

        Override to perform tasks that should happen when the bot
        becomes inactive, like sending shutdown notifications.
        """
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r}, version={self.version!r})>"
