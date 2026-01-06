"""Statistics command handlers for admin bot."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.bot_repository import UserRepository
from src.stats.models import BotStatsDTO, SystemStatsDTO
from src.stats.repository import StatsRepository

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager

router = Router(name="admin_stats")


def format_timedelta(td: timedelta | None) -> str:
    """Format a timedelta to a human-readable string."""
    if not td:
        return "N/A"

    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "< 1m"


def format_number(n: int) -> str:
    """Format a number with thousand separators."""
    return f"{n:,}"


def create_hourly_chart(hourly_pattern: list[int], width: int = 24) -> str:
    """Create an ASCII bar chart for hourly activity."""
    if not hourly_pattern or max(hourly_pattern) == 0:
        return "No activity data"

    max_val = max(hourly_pattern)
    bars = ["_", ".", ",", "-", "=", "+", "*", "#"]

    lines = []
    for i, count in enumerate(hourly_pattern):
        if max_val > 0:
            bar_idx = int((count / max_val) * (len(bars) - 1))
            bar_char = bars[bar_idx]
        else:
            bar_char = "_"

        # Only show every 4th hour label
        if i % 4 == 0:
            lines.append(f"{i:02d}|{bar_char}")
        else:
            lines.append(f"  |{bar_char}")

    # Join horizontally
    header = "".join(f"{i:02d}" if i % 4 == 0 else "  " for i in range(24))
    chart = "".join(
        bars[int((hourly_pattern[i] / max_val) * (len(bars) - 1))] if max_val > 0 else "_"
        for i in range(24)
    )

    return f"<code>Hour: {header}\n      {chart}</code>"


async def get_bot_stats(
    session: AsyncSession,
    bot_manager: BotManager,
    bot_id: str,
) -> BotStatsDTO:
    """Get comprehensive stats for a single bot."""
    stats_repo = StatsRepository(session)
    user_repo = UserRepository(session)

    # Get aggregated stats
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
    managed_bot = bot_manager.get_bot(bot_id)
    if managed_bot:
        bot_name = managed_bot.config.name
        if managed_bot.started_at:
            uptime = datetime.utcnow() - managed_bot.started_at

    # Calculate error rate
    total_interactions = today.message_count + today.command_count
    error_rate = today.error_count / total_interactions if total_interactions > 0 else 0.0

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


async def get_system_stats(
    session: AsyncSession,
    bot_manager: BotManager,
) -> SystemStatsDTO:
    """Get system-wide statistics."""
    bots = bot_manager.get_all_bots()
    running = sum(1 for b in bots.values() if b.state == "running")

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


def create_stats_keyboard(
    bot_ids: list[str] | None = None,
    current_bot_id: str | None = None,
) -> InlineKeyboardMarkup:
    """Create keyboard for stats navigation."""
    buttons = []

    if current_bot_id:
        # Bot detail view
        buttons.append([
            InlineKeyboardButton(text="Hourly Chart", callback_data=f"stats_hourly_{current_bot_id}"),
            InlineKeyboardButton(text="Top Commands", callback_data=f"stats_commands_{current_bot_id}"),
        ])
        buttons.append([
            InlineKeyboardButton(text="Refresh", callback_data=f"stats_bot_{current_bot_id}"),
            InlineKeyboardButton(text="Back", callback_data="stats_overview"),
        ])
    else:
        # Overview - list all bots
        if bot_ids:
            for bot_id in bot_ids[:6]:  # Limit to 6 buttons
                buttons.append([
                    InlineKeyboardButton(
                        text=bot_id,
                        callback_data=f"stats_bot_{bot_id}",
                    )
                ])

        buttons.append([
            InlineKeyboardButton(text="Refresh", callback_data="stats_overview"),
            InlineKeyboardButton(text="Back", callback_data="admin_menu"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("stats"))
async def cmd_stats(
    message: Message,
    bot_manager: BotManager,
    session: AsyncSession,
) -> None:
    """
    Show statistics.

    Usage: /stats [bot_id]
    """
    args = message.text.split()[1:] if message.text else []

    if args:
        # Show stats for specific bot
        bot_id = args[0]
        if not bot_manager.get_bot(bot_id):
            await message.answer(f"Bot not found: {bot_id}")
            return

        stats = await get_bot_stats(session, bot_manager, bot_id)
        await message.answer(
            _format_bot_stats(stats),
            reply_markup=create_stats_keyboard(current_bot_id=bot_id),
            parse_mode="HTML",
        )
    else:
        # Show system overview
        system_stats = await get_system_stats(session, bot_manager)
        bot_ids = list(bot_manager.get_all_bots().keys())

        await message.answer(
            _format_system_stats(system_stats),
            reply_markup=create_stats_keyboard(bot_ids=bot_ids),
            parse_mode="HTML",
        )


def _format_system_stats(stats: SystemStatsDTO) -> str:
    """Format system stats for display."""
    return f"""
<b>System Statistics</b>

<b>Bots:</b> {stats.running_bots}/{stats.total_bots} running
<b>Total Users:</b> {format_number(stats.total_users)}

<b>Today's Activity:</b>
  Messages: {format_number(stats.today_messages)}
  Commands: {format_number(stats.today_commands)}

Select a bot for detailed statistics:
""".strip()


def _format_bot_stats(stats: BotStatsDTO) -> str:
    """Format bot stats for display."""
    error_pct = f"{stats.error_rate * 100:.2f}%" if stats.error_rate > 0 else "0%"

    return f"""
<b>Statistics: {stats.bot_name}</b>

<b>Users</b>
  Total: {format_number(stats.total_users)}
  Daily Active: {format_number(stats.daily_active_users)}
  Weekly Active: {format_number(stats.weekly_active_users)}

<b>Activity (Today)</b>
  Messages: {format_number(stats.today_messages)}
  Commands: {format_number(stats.today_commands)}
  Callbacks: {format_number(stats.today_callbacks)}

<b>Activity (Week)</b>
  Messages: {format_number(stats.week_messages)}
  Commands: {format_number(stats.week_commands)}

<b>Uptime:</b> {format_timedelta(stats.uptime)}
<b>Error Rate:</b> {error_pct}
""".strip()


@router.callback_query(F.data == "stats_overview")
async def cb_stats_overview(
    callback: CallbackQuery,
    bot_manager: BotManager,
    session: AsyncSession,
) -> None:
    """Show system stats overview."""
    await callback.answer()

    system_stats = await get_system_stats(session, bot_manager)
    bot_ids = list(bot_manager.get_all_bots().keys())

    await callback.message.edit_text(
        _format_system_stats(system_stats),
        reply_markup=create_stats_keyboard(bot_ids=bot_ids),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("stats_bot_"))
async def cb_stats_bot(
    callback: CallbackQuery,
    bot_manager: BotManager,
    session: AsyncSession,
) -> None:
    """Show stats for a specific bot."""
    bot_id = callback.data.replace("stats_bot_", "")

    if not bot_manager.get_bot(bot_id):
        await callback.answer("Bot not found", show_alert=True)
        return

    await callback.answer()

    stats = await get_bot_stats(session, bot_manager, bot_id)
    await callback.message.edit_text(
        _format_bot_stats(stats),
        reply_markup=create_stats_keyboard(current_bot_id=bot_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("stats_hourly_"))
async def cb_stats_hourly(
    callback: CallbackQuery,
    bot_manager: BotManager,
    session: AsyncSession,
) -> None:
    """Show hourly activity chart."""
    bot_id = callback.data.replace("stats_hourly_", "")

    managed_bot = bot_manager.get_bot(bot_id)
    if not managed_bot:
        await callback.answer("Bot not found", show_alert=True)
        return

    await callback.answer()

    stats_repo = StatsRepository(session)
    hourly_pattern = await stats_repo.get_hourly_pattern(bot_id, days=7)

    chart = create_hourly_chart(hourly_pattern)

    text = f"""
<b>Hourly Activity: {managed_bot.config.name}</b>

Activity distribution over the past 7 days (UTC):

{chart}

Peak hours: {_find_peak_hours(hourly_pattern)}
""".strip()

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Back", callback_data=f"stats_bot_{bot_id}")],
        ]),
        parse_mode="HTML",
    )


def _find_peak_hours(hourly_pattern: list[int]) -> str:
    """Find the top 3 peak hours."""
    if not hourly_pattern or max(hourly_pattern) == 0:
        return "No data"

    indexed = [(i, count) for i, count in enumerate(hourly_pattern)]
    sorted_hours = sorted(indexed, key=lambda x: x[1], reverse=True)[:3]

    return ", ".join(f"{h:02d}:00" for h, _ in sorted_hours if _ > 0)


@router.callback_query(F.data.startswith("stats_commands_"))
async def cb_stats_commands(
    callback: CallbackQuery,
    bot_manager: BotManager,
    session: AsyncSession,
) -> None:
    """Show top commands."""
    bot_id = callback.data.replace("stats_commands_", "")

    managed_bot = bot_manager.get_bot(bot_id)
    if not managed_bot:
        await callback.answer("Bot not found", show_alert=True)
        return

    await callback.answer()

    stats_repo = StatsRepository(session)
    top_commands = await stats_repo.get_top_commands(bot_id, days=7, limit=10)

    if not top_commands:
        commands_text = "No command usage data"
    else:
        commands_text = "\n".join(
            f"  /{cmd}: {format_number(count)}"
            for cmd, count in top_commands
        )

    text = f"""
<b>Top Commands: {managed_bot.config.name}</b>

Most used commands (past 7 days):

{commands_text}
""".strip()

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Back", callback_data=f"stats_bot_{bot_id}")],
        ]),
        parse_mode="HTML",
    )


# Also add callback for main menu statistics button
@router.callback_query(F.data == "admin_stats_menu")
async def cb_admin_stats_menu(
    callback: CallbackQuery,
    bot_manager: BotManager,
    session: AsyncSession,
) -> None:
    """Show stats menu from main admin menu."""
    await callback.answer()

    system_stats = await get_system_stats(session, bot_manager)
    bot_ids = list(bot_manager.get_all_bots().keys())

    await callback.message.edit_text(
        _format_system_stats(system_stats),
        reply_markup=create_stats_keyboard(bot_ids=bot_ids),
        parse_mode="HTML",
    )
