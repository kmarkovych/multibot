"""Statistics collection middleware."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

if TYPE_CHECKING:
    from src.stats.collector import StatsCollector

logger = logging.getLogger(__name__)


class StatsMiddleware(BaseMiddleware):
    """Middleware that collects statistics for all bot interactions."""

    def __init__(self, bot_id: str, collector: StatsCollector):
        """
        Initialize the stats middleware.

        Args:
            bot_id: The bot identifier
            collector: Stats collector instance
        """
        self.bot_id = bot_id
        self.collector = collector

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        user_id = user.id if user else 0

        try:
            # Record the interaction type
            if isinstance(event, Message):
                await self._record_message(event, user_id)
            elif isinstance(event, CallbackQuery):
                await self.collector.record_callback(self.bot_id, user_id)

            # Execute the handler
            result = await handler(event, data)
            return result

        except Exception:
            # Record the error
            await self.collector.record_error(self.bot_id)
            raise

    async def _record_message(self, message: Message, user_id: int) -> None:
        """Record a message, distinguishing between commands and regular messages."""
        text = message.text or message.caption or ""

        # Check if it's a command
        if text.startswith("/"):
            # Extract command name (without the /)
            command = text.split()[0][1:]  # Remove leading /
            # Remove bot mention if present (e.g., /start@BotName)
            if "@" in command:
                command = command.split("@")[0]
            await self.collector.record_command(self.bot_id, command, user_id)
        else:
            await self.collector.record_message(self.bot_id, user_id)
