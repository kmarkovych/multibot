"""Admin authorization middleware."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

logger = logging.getLogger(__name__)


class AdminAuthMiddleware(BaseMiddleware):
    """
    Middleware to restrict admin commands to authorized users.
    """

    def __init__(self, allowed_users: list[int]):
        self.allowed_users = set(allowed_users)

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        if not user:
            return None

        if user.id not in self.allowed_users:
            logger.warning(f"Unauthorized admin access attempt by user {user.id}")

            if isinstance(event, Message):
                await event.answer("⛔ Access denied. You are not authorized.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Access denied", show_alert=True)

            return None

        return await handler(event, data)

    def add_user(self, user_id: int) -> None:
        """Add a user to the allowed list."""
        self.allowed_users.add(user_id)

    def remove_user(self, user_id: int) -> None:
        """Remove a user from the allowed list."""
        self.allowed_users.discard(user_id)

    def is_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed."""
        return user_id in self.allowed_users
