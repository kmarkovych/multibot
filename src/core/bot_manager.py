"""Bot lifecycle management."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.core.config import BotConfig
from src.core.exceptions import (
    BotAlreadyRunningError,
    BotNotFoundError,
    BotNotRunningError,
)

if TYPE_CHECKING:
    from src.core.dispatcher_factory import DispatcherFactory
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

BotState = Literal["starting", "running", "stopping", "stopped", "error"]


@dataclass
class ManagedBot:
    """Represents a managed bot instance with its state."""

    bot_id: str
    config: BotConfig
    bot: Bot
    dispatcher: Dispatcher
    mode: Literal["polling", "webhook"]
    state: BotState = "stopped"
    started_at: datetime | None = None
    error_message: str | None = None
    polling_task: asyncio.Task | None = field(default=None, repr=False)
    message_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "bot_id": self.bot_id,
            "name": self.config.name,
            "description": self.config.description,
            "mode": self.mode,
            "state": self.state,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "error_message": self.error_message,
            "message_count": self.message_count,
        }


class BotManager:
    """
    Manages multiple bot instances concurrently.

    Responsibilities:
    - Create/destroy Bot and Dispatcher instances
    - Start/stop individual bots (polling or webhook mode)
    - Track bot states (running, stopped, error)
    - Handle bot registration/deregistration
    - Provide bot status information
    """

    def __init__(
        self,
        db: DatabaseManager | None = None,
        dispatcher_factory: DispatcherFactory | None = None,
    ):
        self.bots: dict[str, ManagedBot] = {}
        self.db = db
        self.dispatcher_factory = dispatcher_factory
        self._shutdown_event = asyncio.Event()

    def set_dispatcher_factory(self, factory: DispatcherFactory) -> None:
        """Set the dispatcher factory."""
        self.dispatcher_factory = factory

    async def create_bot(self, config: BotConfig) -> ManagedBot:
        """Create a new managed bot from configuration."""
        if not self.dispatcher_factory:
            raise RuntimeError("DispatcherFactory not set")

        # Create Bot instance
        bot = Bot(
            token=config.token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
                if config.settings.get("parse_mode", "").upper() == "HTML"
                else None,
            ),
        )

        # Create Dispatcher with plugins
        dispatcher = await self.dispatcher_factory.create_dispatcher(
            config=config,
            bot_id=config.id,
        )

        managed_bot = ManagedBot(
            bot_id=config.id,
            config=config,
            bot=bot,
            dispatcher=dispatcher,
            mode=config.mode,
            state="stopped",
        )

        self.bots[config.id] = managed_bot
        logger.info(f"Created bot: {config.id} ({config.name})")

        return managed_bot

    async def start_bot(self, bot_id: str) -> None:
        """Start a bot with polling or webhook mode."""
        if bot_id not in self.bots:
            raise BotNotFoundError(bot_id)

        managed_bot = self.bots[bot_id]

        if managed_bot.state == "running":
            raise BotAlreadyRunningError(bot_id)

        managed_bot.state = "starting"
        managed_bot.error_message = None

        try:
            if managed_bot.mode == "polling":
                await self._start_polling(managed_bot)
            else:
                # Webhook mode - just mark as running
                # Actual webhook setup happens in webhook server
                managed_bot.state = "running"
                managed_bot.started_at = datetime.utcnow()

            logger.info(f"Started bot: {bot_id} in {managed_bot.mode} mode")

        except Exception as e:
            managed_bot.state = "error"
            managed_bot.error_message = str(e)
            logger.error(f"Failed to start bot {bot_id}: {e}")
            raise

    async def _start_polling(self, managed_bot: ManagedBot) -> None:
        """Start a bot in polling mode."""

        async def polling_loop():
            try:
                managed_bot.state = "running"
                managed_bot.started_at = datetime.utcnow()

                await managed_bot.dispatcher.start_polling(
                    managed_bot.bot,
                    allowed_updates=managed_bot.dispatcher.resolve_used_update_types(),
                )
            except asyncio.CancelledError:
                logger.info(f"Polling cancelled for bot: {managed_bot.bot_id}")
            except Exception as e:
                managed_bot.state = "error"
                managed_bot.error_message = str(e)
                logger.error(f"Polling error for bot {managed_bot.bot_id}: {e}")
            finally:
                if managed_bot.state == "running":
                    managed_bot.state = "stopped"

        managed_bot.polling_task = asyncio.create_task(polling_loop())

    async def stop_bot(self, bot_id: str) -> None:
        """Stop a running bot."""
        if bot_id not in self.bots:
            raise BotNotFoundError(bot_id)

        managed_bot = self.bots[bot_id]

        if managed_bot.state not in ("running", "starting"):
            raise BotNotRunningError(bot_id)

        managed_bot.state = "stopping"

        try:
            # Cancel polling task if running
            if managed_bot.polling_task and not managed_bot.polling_task.done():
                managed_bot.polling_task.cancel()
                try:
                    await managed_bot.polling_task
                except asyncio.CancelledError:
                    pass

            # Close bot session
            await managed_bot.bot.session.close()

            managed_bot.state = "stopped"
            managed_bot.polling_task = None
            logger.info(f"Stopped bot: {bot_id}")

        except Exception as e:
            managed_bot.state = "error"
            managed_bot.error_message = str(e)
            logger.error(f"Error stopping bot {bot_id}: {e}")
            raise

    async def restart_bot(self, bot_id: str) -> None:
        """Restart a bot."""
        managed_bot = self.bots.get(bot_id)
        if managed_bot and managed_bot.state in ("running", "starting"):
            await self.stop_bot(bot_id)

        # Wait a moment for cleanup
        await asyncio.sleep(0.5)

        await self.start_bot(bot_id)

    async def reload_bot(self, bot_id: str, new_config: BotConfig) -> None:
        """Reload a bot with new configuration."""
        if bot_id not in self.bots:
            raise BotNotFoundError(bot_id)

        managed_bot = self.bots[bot_id]
        was_running = managed_bot.state == "running"

        # Stop if running
        if was_running:
            await self.stop_bot(bot_id)

        # Remove old bot
        del self.bots[bot_id]

        # Create new bot with updated config
        await self.create_bot(new_config)

        # Start if was running
        if was_running and new_config.enabled:
            await self.start_bot(bot_id)

        logger.info(f"Reloaded bot: {bot_id}")

    async def remove_bot(self, bot_id: str) -> None:
        """Remove a bot completely."""
        if bot_id in self.bots:
            managed_bot = self.bots[bot_id]
            if managed_bot.state in ("running", "starting"):
                await self.stop_bot(bot_id)
            del self.bots[bot_id]
            logger.info(f"Removed bot: {bot_id}")

    def get_bot(self, bot_id: str) -> ManagedBot | None:
        """Get a managed bot by ID."""
        return self.bots.get(bot_id)

    def get_bot_status(self, bot_id: str) -> dict[str, Any]:
        """Get current status of a bot."""
        if bot_id not in self.bots:
            raise BotNotFoundError(bot_id)
        return self.bots[bot_id].to_dict()

    def get_all_bots(self) -> dict[str, ManagedBot]:
        """Get all managed bots."""
        return self.bots.copy()

    def get_running_bots(self) -> list[ManagedBot]:
        """Get all currently running bots."""
        return [bot for bot in self.bots.values() if bot.state == "running"]

    async def start_all(self) -> dict[str, str]:
        """Start all enabled bots. Returns status for each bot."""
        results = {}
        for bot_id, managed_bot in self.bots.items():
            if managed_bot.config.enabled:
                try:
                    await self.start_bot(bot_id)
                    results[bot_id] = "started"
                except Exception as e:
                    results[bot_id] = f"error: {e}"
            else:
                results[bot_id] = "disabled"
        return results

    async def stop_all(self) -> None:
        """Stop all running bots."""
        for bot_id, managed_bot in list(self.bots.items()):
            if managed_bot.state in ("running", "starting"):
                try:
                    await self.stop_bot(bot_id)
                except Exception as e:
                    logger.error(f"Error stopping bot {bot_id}: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown all bots."""
        logger.info("Shutting down bot manager...")
        self._shutdown_event.set()
        await self.stop_all()
        logger.info("Bot manager shutdown complete")
