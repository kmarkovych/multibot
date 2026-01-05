"""Rate limiting middleware."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

logger = logging.getLogger(__name__)


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""

    tokens: float
    last_update: float
    rate: float  # tokens per second
    burst: int

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.time()

        # Refill tokens based on time elapsed
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware that implements per-user rate limiting.

    Uses a token bucket algorithm for smooth rate limiting.
    """

    def __init__(
        self,
        rate: int = 30,  # requests per minute
        burst: int = 10,
    ):
        self.rate = rate / 60.0  # Convert to per-second
        self.burst = burst
        self._buckets: dict[int, RateLimitBucket] = {}
        self._cleanup_interval = 300  # Cleanup old buckets every 5 minutes
        self._last_cleanup = time.time()

    def _get_bucket(self, user_id: int) -> RateLimitBucket:
        """Get or create a rate limit bucket for a user."""
        if user_id not in self._buckets:
            self._buckets[user_id] = RateLimitBucket(
                tokens=self.burst,
                last_update=time.time(),
                rate=self.rate,
                burst=self.burst,
            )
        return self._buckets[user_id]

    def _cleanup_old_buckets(self) -> None:
        """Remove buckets that haven't been used recently."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        cutoff = now - self._cleanup_interval
        to_remove = [
            user_id
            for user_id, bucket in self._buckets.items()
            if bucket.last_update < cutoff
        ]

        for user_id in to_remove:
            del self._buckets[user_id]

        self._last_cleanup = now
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} rate limit buckets")

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        # Cleanup old buckets periodically
        self._cleanup_old_buckets()

        # Get user ID
        user = event.from_user
        if not user:
            return await handler(event, data)

        # Check rate limit
        bucket = self._get_bucket(user.id)

        if not bucket.consume():
            logger.warning(f"Rate limited user {user.id}")

            # Optionally notify the user
            if isinstance(event, Message):
                await event.answer(
                    "You're sending messages too fast. Please wait a moment.",
                )

            return None  # Drop the request

        return await handler(event, data)
