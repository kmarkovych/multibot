"""In-memory statistics collector with batched database writes."""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from datetime import datetime
from typing import TYPE_CHECKING

from src.stats.repository import StatsRepository

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class StatsCollector:
    """
    In-memory statistics collector with periodic database flush.

    Collects statistics in memory and writes to database in batches
    to minimize database load.
    """

    def __init__(self, db: DatabaseManager, flush_interval: int = 60):
        """
        Initialize the stats collector.

        Args:
            db: Database manager instance
            flush_interval: Seconds between database flushes
        """
        self.db = db
        self.flush_interval = flush_interval

        # In-memory counters (per bot_id)
        self._message_counts: Counter[str] = Counter()
        self._command_counts: Counter[str] = Counter()
        self._callback_counts: Counter[str] = Counter()
        self._error_counts: Counter[str] = Counter()
        self._new_user_counts: Counter[str] = Counter()

        # Command usage tracking (bot_id -> command -> count)
        self._command_usage: dict[str, Counter[str]] = {}

        # Unique users seen this flush period (bot_id -> set of user_ids)
        self._seen_users: dict[str, set[int]] = {}

        # Synchronization
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the periodic flush task."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info(
            f"Stats collector started (flush interval: {self.flush_interval}s)"
        )

    async def stop(self) -> None:
        """Stop the collector and perform final flush."""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_to_db()
        logger.info("Stats collector stopped")

    async def record_message(self, bot_id: str, user_id: int) -> None:
        """Record a non-command message."""
        async with self._lock:
            self._message_counts[bot_id] += 1
            self._seen_users.setdefault(bot_id, set()).add(user_id)

    async def record_command(self, bot_id: str, command: str, user_id: int) -> None:
        """Record a command usage."""
        async with self._lock:
            self._command_counts[bot_id] += 1
            self._command_usage.setdefault(bot_id, Counter())[command] += 1
            self._seen_users.setdefault(bot_id, set()).add(user_id)

    async def record_callback(self, bot_id: str, user_id: int) -> None:
        """Record a callback query."""
        async with self._lock:
            self._callback_counts[bot_id] += 1
            self._seen_users.setdefault(bot_id, set()).add(user_id)

    async def record_error(self, bot_id: str) -> None:
        """Record an error."""
        async with self._lock:
            self._error_counts[bot_id] += 1

    async def record_new_user(self, bot_id: str) -> None:
        """Record a new user registration."""
        async with self._lock:
            self._new_user_counts[bot_id] += 1

    def get_current_counters(self) -> dict[str, dict[str, int]]:
        """Get current in-memory counters (for metrics endpoint)."""
        result = {}
        all_bot_ids = set(self._message_counts.keys()) | set(
            self._command_counts.keys()
        )

        for bot_id in all_bot_ids:
            result[bot_id] = {
                "messages": self._message_counts.get(bot_id, 0),
                "commands": self._command_counts.get(bot_id, 0),
                "callbacks": self._callback_counts.get(bot_id, 0),
                "errors": self._error_counts.get(bot_id, 0),
            }

        return result

    async def _periodic_flush(self) -> None:
        """Periodically flush counters to database."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_to_db()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stats flush: {e}")

    async def _flush_to_db(self) -> None:
        """Flush current counters to database."""
        async with self._lock:
            # Check if there's anything to flush
            if not any(
                [
                    self._message_counts,
                    self._command_counts,
                    self._callback_counts,
                    self._error_counts,
                ]
            ):
                return

            # Get current hour bucket
            now = datetime.utcnow()
            hour_bucket = now.replace(minute=0, second=0, microsecond=0)

            # Collect all bot IDs
            all_bot_ids = (
                set(self._message_counts.keys())
                | set(self._command_counts.keys())
                | set(self._callback_counts.keys())
                | set(self._error_counts.keys())
            )

            try:
                async with self.db.session() as session:
                    repo = StatsRepository(session)

                    for bot_id in all_bot_ids:
                        await repo.upsert_hourly_stats(
                            bot_id=bot_id,
                            hour_bucket=hour_bucket,
                            message_count=self._message_counts.get(bot_id, 0),
                            command_count=self._command_counts.get(bot_id, 0),
                            callback_count=self._callback_counts.get(bot_id, 0),
                            error_count=self._error_counts.get(bot_id, 0),
                            unique_users=len(self._seen_users.get(bot_id, set())),
                            new_users=self._new_user_counts.get(bot_id, 0),
                            command_usage=dict(self._command_usage.get(bot_id, {})),
                        )

                    await session.commit()

                logger.debug(f"Flushed stats for {len(all_bot_ids)} bots")

            except Exception as e:
                logger.error(f"Failed to flush stats to database: {e}")
                # Don't clear counters on error - will retry next flush
                return

            # Clear counters after successful flush
            self._message_counts.clear()
            self._command_counts.clear()
            self._callback_counts.clear()
            self._error_counts.clear()
            self._new_user_counts.clear()
            self._command_usage.clear()
            self._seen_users.clear()
