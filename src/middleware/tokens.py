"""Token check middleware for billing system."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

if TYPE_CHECKING:
    from src.billing.token_manager import TokenManager

logger = logging.getLogger(__name__)


class TokenMiddleware(BaseMiddleware):
    """
    Middleware that initializes user tokens and injects token manager.

    Ensures new users receive their free tokens and provides
    token-related data to handlers.
    """

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        # Get user ID
        user = event.from_user
        user_id = user.id if user else 0

        # Initialize user and get balance
        is_new_user = False
        balance = 0

        if user_id:
            try:
                balance, is_new_user = await self.token_manager.ensure_initialized(
                    telegram_id=user_id,
                )
            except Exception as e:
                logger.error(f"Failed to initialize tokens for user {user_id}: {e}")
                # Continue anyway - don't block the request
                balance = 0

        # Inject token data into handler context
        data["token_manager"] = self.token_manager
        data["token_balance"] = balance
        data["is_new_token_user"] = is_new_user

        return await handler(event, data)
