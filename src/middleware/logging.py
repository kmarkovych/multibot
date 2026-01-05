"""Logging middleware for request/response tracking."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware that logs all incoming updates with timing information."""

    def __init__(self, bot_id: str):
        self.bot_id = bot_id

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        data["request_id"] = request_id

        # Extract user info
        user = event.from_user
        user_id = user.id if user else "unknown"
        username = user.username if user else "unknown"

        # Log incoming request
        event_type = type(event).__name__
        content = ""
        if isinstance(event, Message):
            content = event.text[:50] if event.text else "[non-text]"
        elif isinstance(event, CallbackQuery):
            content = event.data or "[no data]"

        logger.info(
            f"[{request_id}] {event_type} from {username}({user_id}): {content}",
            extra={
                "request_id": request_id,
                "bot_id": self.bot_id,
                "user_id": user_id,
                "event_type": event_type,
            },
        )

        # Time the handler execution
        start_time = time.perf_counter()

        try:
            result = await handler(event, data)
            elapsed = (time.perf_counter() - start_time) * 1000

            logger.debug(
                f"[{request_id}] Completed in {elapsed:.2f}ms",
                extra={
                    "request_id": request_id,
                    "elapsed_ms": elapsed,
                },
            )

            return result

        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000

            logger.error(
                f"[{request_id}] Error after {elapsed:.2f}ms: {e}",
                extra={
                    "request_id": request_id,
                    "elapsed_ms": elapsed,
                    "error": str(e),
                },
                exc_info=True,
            )

            raise
