"""Error handling middleware."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware that catches and handles errors gracefully.

    This provides a safety net for unhandled exceptions.
    """

    def __init__(
        self,
        bot_id: str = "",
        notify_user: bool = True,
        user_message: str = "An error occurred. Please try again later.",
    ):
        self.bot_id = bot_id
        self.notify_user = notify_user
        self.user_message = user_message

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)

        except Exception as e:
            error_id = str(uuid.uuid4())[:8]

            # Log the error with full details
            logger.error(
                f"[{error_id}] Unhandled error in handler: {type(e).__name__}: {e}",
                extra={
                    "error_id": error_id,
                    "bot_id": self.bot_id,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Try to notify user
            if self.notify_user:
                try:
                    message = f"{self.user_message}\n\nError ID: {error_id}"

                    if isinstance(event, Message):
                        await event.answer(message)
                    elif isinstance(event, CallbackQuery):
                        await event.answer(message, show_alert=True)

                except Exception as notify_error:
                    logger.warning(f"Could not notify user of error: {notify_error}")

            # Re-raise so error handlers can also catch it
            raise
