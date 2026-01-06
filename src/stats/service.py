"""High-level statistics service."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.database.repositories.bot_repository import UserRepository
from src.stats.models import BotStatsDTO, SystemStatsDTO
from src.stats.repository import StatsRepository

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager
    from src.database.connection import DatabaseManager


class StatsService:
    """Service for querying statistics."""

    def __init__(self, db: DatabaseManager, bot_manager: BotManager):
        """
        Initialize the stats service.

        Args:
            db: Database manager instance
            bot_manager: Bot manager instance for uptime info
        """
        self.db = db
        self.bot_manager = bot_manager

    async def get_bot_stats(self, bot_id: str) -> BotStatsDTO:
        """Get comprehensive stats for a single bot."""
        async with self.db.session() as session:
            stats_repo = StatsRepository(session)
            user_repo = UserRepository(session)

            # Get aggregated stats for different time ranges
            today = await stats_repo.get_daily_stats(bot_id, days=1)
            week = await stats_repo.get_daily_stats(bot_id, days=7)

            # Get user counts
            total_users = await user_repo.get_user_count(bot_id)
            dau = await user_repo.get_active_users(bot_id, hours=24)
            wau = await user_repo.get_active_users(bot_id, hours=168)

            # Get hourly pattern
            hourly_pattern = await stats_repo.get_hourly_pattern(bot_id, days=7)

            # Get top commands
            top_commands = await stats_repo.get_top_commands(bot_id, days=7, limit=10)

        # Get uptime from bot manager
        uptime = None
        bot_name = bot_id
        managed_bot = self.bot_manager.get_bot(bot_id)
        if managed_bot:
            bot_name = managed_bot.config.name
            if managed_bot.started_at:
                uptime = datetime.utcnow() - managed_bot.started_at

        # Calculate error rate
        total_interactions = today.message_count + today.command_count
        error_rate = (
            today.error_count / total_interactions if total_interactions > 0 else 0.0
        )

        return BotStatsDTO(
            bot_id=bot_id,
            bot_name=bot_name,
            total_users=total_users,
            daily_active_users=dau,
            weekly_active_users=wau,
            uptime=uptime,
            today_messages=today.message_count,
            today_commands=today.command_count,
            today_callbacks=today.callback_count,
            week_messages=week.message_count,
            week_commands=week.command_count,
            error_rate=error_rate,
            hourly_pattern=hourly_pattern,
            top_commands=top_commands,
        )

    async def get_system_stats(self) -> SystemStatsDTO:
        """Get system-wide statistics."""
        bots = self.bot_manager.get_all_bots()
        running = sum(1 for b in bots.values() if b.state.value == "running")

        async with self.db.session() as session:
            stats_repo = StatsRepository(session)
            user_repo = UserRepository(session)

            total_users = await user_repo.get_total_user_count()
            today = await stats_repo.get_total_daily_stats(days=1)

        return SystemStatsDTO(
            total_bots=len(bots),
            running_bots=running,
            total_users=total_users,
            today_messages=today.message_count,
            today_commands=today.command_count,
        )
