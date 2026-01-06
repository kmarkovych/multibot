"""Repository for statistics database operations."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from src.database.models import BotStatistics
from src.database.repositories.base import BaseRepository
from src.stats.models import AggregatedStats


class StatsRepository(BaseRepository[BotStatistics]):
    """Repository for BotStatistics operations."""

    model = BotStatistics

    async def upsert_hourly_stats(
        self,
        bot_id: str,
        hour_bucket: datetime,
        message_count: int = 0,
        command_count: int = 0,
        callback_count: int = 0,
        error_count: int = 0,
        unique_users: int = 0,
        new_users: int = 0,
        command_usage: dict[str, int] | None = None,
    ) -> None:
        """Upsert hourly statistics with atomic increment."""
        stmt = insert(BotStatistics).values(
            bot_id=bot_id,
            hour_bucket=hour_bucket,
            message_count=message_count,
            command_count=command_count,
            callback_count=callback_count,
            error_count=error_count,
            unique_users=unique_users,
            new_users=new_users,
            command_usage=command_usage or {},
        )

        # On conflict, increment counters
        stmt = stmt.on_conflict_do_update(
            index_elements=["bot_id", "hour_bucket"],
            set_={
                "message_count": BotStatistics.message_count + message_count,
                "command_count": BotStatistics.command_count + command_count,
                "callback_count": BotStatistics.callback_count + callback_count,
                "error_count": BotStatistics.error_count + error_count,
                "unique_users": func.greatest(BotStatistics.unique_users, unique_users),
                "new_users": BotStatistics.new_users + new_users,
                "command_usage": func.coalesce(
                    BotStatistics.command_usage, text("'{}'::jsonb")
                )
                + func.coalesce(text("'{}'::jsonb"), text("'{}'::jsonb")),
            },
        )

        await self.session.execute(stmt)
        await self.session.flush()

    async def merge_command_usage(
        self,
        bot_id: str,
        hour_bucket: datetime,
        command_usage: dict[str, int],
    ) -> None:
        """Merge command usage into existing stats using raw SQL for JSONB."""
        if not command_usage:
            return

        # Build the update for each command
        query = text("""
            UPDATE bot_statistics
            SET command_usage = COALESCE(command_usage, '{}'::jsonb) || :usage::jsonb
            WHERE bot_id = :bot_id AND hour_bucket = :hour_bucket
        """)

        await self.session.execute(
            query,
            {
                "bot_id": bot_id,
                "hour_bucket": hour_bucket,
                "usage": command_usage,
            },
        )

    async def get_daily_stats(self, bot_id: str, days: int = 1) -> AggregatedStats:
        """Get aggregated stats for the past N days."""
        since = datetime.utcnow() - timedelta(days=days)

        query = select(
            func.coalesce(func.sum(BotStatistics.message_count), 0).label(
                "message_count"
            ),
            func.coalesce(func.sum(BotStatistics.command_count), 0).label(
                "command_count"
            ),
            func.coalesce(func.sum(BotStatistics.callback_count), 0).label(
                "callback_count"
            ),
            func.coalesce(func.sum(BotStatistics.error_count), 0).label("error_count"),
            func.coalesce(func.sum(BotStatistics.new_users), 0).label("new_users"),
        ).where(
            BotStatistics.bot_id == bot_id,
            BotStatistics.hour_bucket >= since,
        )

        result = await self.session.execute(query)
        row = result.one()

        return AggregatedStats(
            message_count=int(row.message_count),
            command_count=int(row.command_count),
            callback_count=int(row.callback_count),
            error_count=int(row.error_count),
            new_users=int(row.new_users),
        )

    async def get_total_daily_stats(self, days: int = 1) -> AggregatedStats:
        """Get aggregated stats for all bots."""
        since = datetime.utcnow() - timedelta(days=days)

        query = select(
            func.coalesce(func.sum(BotStatistics.message_count), 0).label(
                "message_count"
            ),
            func.coalesce(func.sum(BotStatistics.command_count), 0).label(
                "command_count"
            ),
            func.coalesce(func.sum(BotStatistics.callback_count), 0).label(
                "callback_count"
            ),
            func.coalesce(func.sum(BotStatistics.error_count), 0).label("error_count"),
            func.coalesce(func.sum(BotStatistics.new_users), 0).label("new_users"),
        ).where(BotStatistics.hour_bucket >= since)

        result = await self.session.execute(query)
        row = result.one()

        return AggregatedStats(
            message_count=int(row.message_count),
            command_count=int(row.command_count),
            callback_count=int(row.callback_count),
            error_count=int(row.error_count),
            new_users=int(row.new_users),
        )

    async def get_hourly_pattern(self, bot_id: str, days: int = 7) -> list[int]:
        """Get message count by hour of day (0-23)."""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                func.extract("hour", BotStatistics.hour_bucket).label("hour"),
                func.sum(BotStatistics.message_count).label("count"),
            )
            .where(
                BotStatistics.bot_id == bot_id,
                BotStatistics.hour_bucket >= since,
            )
            .group_by(text("hour"))
            .order_by(text("hour"))
        )

        result = await self.session.execute(query)
        pattern = [0] * 24
        for row in result:
            hour_idx = int(row.hour) if row.hour is not None else 0
            pattern[hour_idx] = int(row.count) if row.count else 0
        return pattern

    async def get_top_commands(
        self,
        bot_id: str,
        days: int = 7,
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        """Get top commands by usage."""
        since = datetime.utcnow() - timedelta(days=days)

        # Use raw SQL for JSONB aggregation
        query = text("""
            SELECT
                key AS command,
                SUM((value)::int) AS count
            FROM bot_statistics,
                 jsonb_each_text(command_usage)
            WHERE bot_id = :bot_id AND hour_bucket >= :since
            GROUP BY key
            ORDER BY count DESC
            LIMIT :limit
        """)

        result = await self.session.execute(
            query,
            {"bot_id": bot_id, "since": since, "limit": limit},
        )
        return [(str(row.command), int(row.count)) for row in result]

    async def cleanup_old_stats(self, days: int = 90) -> int:
        """Delete statistics older than N days."""
        from sqlalchemy import delete

        cutoff = datetime.utcnow() - timedelta(days=days)

        query = delete(BotStatistics).where(BotStatistics.hour_bucket < cutoff)
        result = await self.session.execute(query)
        return result.rowcount
