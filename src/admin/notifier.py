"""Admin notification service for critical alerts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

    from src.core.bot_manager import BotManager

logger = logging.getLogger(__name__)


class AdminNotifier:
    """
    Service for sending critical notifications to admin users.

    Uses the admin bot to send messages when important events occur,
    such as bot startup failures, configuration errors, etc.
    """

    def __init__(self, bot_manager: BotManager, admin_bot_id: str = "admin"):
        self.bot_manager = bot_manager
        self.admin_bot_id = admin_bot_id
        self._admin_users: list[int] = []

    def _get_admin_bot(self) -> Bot | None:
        """Get the admin bot instance if available."""
        managed_bot = self.bot_manager.get_bot(self.admin_bot_id)
        if managed_bot and managed_bot.state == "running" and managed_bot.bot:
            return managed_bot.bot
        return None

    def _get_admin_users(self) -> list[int]:
        """Get list of admin user IDs."""
        if self._admin_users:
            return self._admin_users

        # Try to get from admin bot config
        managed_bot = self.bot_manager.get_bot(self.admin_bot_id)
        if managed_bot and managed_bot.config.access:
            self._admin_users = managed_bot.config.access.admin_users or []

        return self._admin_users

    async def notify_bot_error(self, bot_id: str, error: str) -> None:
        """Notify admins about a bot startup/runtime error."""
        await self._send_notification(
            f"<b>Bot Error</b>\n\n"
            f"<b>Bot:</b> <code>{bot_id}</code>\n"
            f"<b>Error:</b> {self._escape_html(error)}"
        )

    async def notify_bot_started(self, bot_id: str, bot_name: str) -> None:
        """Notify admins when a bot starts successfully."""
        await self._send_notification(
            f"<b>Bot Started</b>\n\n"
            f"<b>Bot:</b> {bot_name}\n"
            f"<b>ID:</b> <code>{bot_id}</code>"
        )

    async def notify_bot_stopped(self, bot_id: str, bot_name: str) -> None:
        """Notify admins when a bot stops."""
        await self._send_notification(
            f"<b>Bot Stopped</b>\n\n"
            f"<b>Bot:</b> {bot_name}\n"
            f"<b>ID:</b> <code>{bot_id}</code>"
        )

    async def notify_critical(self, title: str, message: str) -> None:
        """Send a critical notification to admins."""
        await self._send_notification(
            f"<b>{self._escape_html(title)}</b>\n\n"
            f"{self._escape_html(message)}"
        )

    async def _send_notification(self, text: str) -> None:
        """Send notification to all admin users."""
        bot = self._get_admin_bot()
        if not bot:
            logger.debug("Admin bot not available for notifications")
            return

        admin_users = self._get_admin_users()
        if not admin_users:
            logger.debug("No admin users configured for notifications")
            return

        for user_id in admin_users:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Failed to send notification to admin {user_id}: {e}")

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
