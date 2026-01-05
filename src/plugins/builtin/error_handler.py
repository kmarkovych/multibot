"""Error handler plugin."""

import logging
import traceback
import uuid
from typing import Any

from aiogram import Router
from aiogram.types import ErrorEvent

from src.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class ErrorHandlerPlugin(BasePlugin):
    """Global error handler for the bot."""

    name = "error_handler"
    description = "Handles errors and optionally notifies users/admins"
    version = "1.0.0"
    author = "Multibot System"

    def setup_handlers(self, router: Router) -> None:
        """Register the error handler."""

        @router.error()
        async def handle_error(event: ErrorEvent) -> bool:
            """Handle all unhandled exceptions."""
            error_id = str(uuid.uuid4())[:8]
            exception = event.exception
            update = event.update

            # Log the error
            logger.error(
                f"Error {error_id}: {type(exception).__name__}: {exception}",
                extra={
                    "error_id": error_id,
                    "bot_id": self._bot_id,
                    "update": update.model_dump_json() if update else None,
                },
                exc_info=exception,
            )

            # Try to notify the user
            show_error_id = self.get_config("show_error_id", True)
            user_message = self.get_config(
                "user_message",
                "An error occurred while processing your request.",
            )

            if show_error_id:
                user_message += f"\n\nError ID: {error_id}"

            try:
                # Try to get a message context to reply to
                message = None
                if update.message:
                    message = update.message
                elif update.callback_query and update.callback_query.message:
                    message = update.callback_query.message

                if message:
                    await message.answer(user_message)
            except Exception as notify_error:
                logger.warning(f"Could not notify user of error: {notify_error}")

            # Notify admins if configured
            await self._notify_admins(event.exception, error_id, update)

            # Return True to indicate the error was handled
            return True

    async def _notify_admins(
        self,
        exception: Exception,
        error_id: str,
        update: Any,
    ) -> None:
        """Notify admin users about the error."""
        if not self.get_config("notify_admins", False):
            return

        admin_chat_ids = self.get_config("admin_chat_ids", [])
        if not admin_chat_ids:
            return

        # Format error message for admins
        error_text = (
            f"<b>Error Report</b>\n\n"
            f"<b>ID:</b> {error_id}\n"
            f"<b>Bot:</b> {self._bot_id}\n"
            f"<b>Type:</b> {type(exception).__name__}\n"
            f"<b>Message:</b> {str(exception)[:500]}\n"
        )

        # Add truncated traceback
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        if len(tb) > 1000:
            tb = tb[:1000] + "\n..."
        error_text += f"\n<pre>{tb}</pre>"

        # Note: This requires the Bot instance to be available
        # In practice, this would be done through the bot manager
        logger.debug(f"Admin notification would be sent: {error_text[:200]}...")


# Export for auto-discovery
plugin = ErrorHandlerPlugin
