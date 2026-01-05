"""Database middleware for session injection."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager


class DatabaseMiddleware(BaseMiddleware):
    """Middleware that injects database session into handler data."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        # Inject database manager into data
        data["db"] = self.db

        # Create a session for this request
        async with self.db.session() as session:
            data["session"] = session
            return await handler(event, data)
