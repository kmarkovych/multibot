"""Status command handlers for admin bot."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager

router = Router(name="admin_status")


def format_timedelta(td) -> str:
    """Format a timedelta to a human-readable string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


@router.message(Command("status"))
async def cmd_status(message: Message, bot_manager: "BotManager") -> None:
    """
    Show status of all bots.

    Usage: /status [bot_id]
    """
    args = message.text.split()[1:] if message.text else []

    if args:
        # Show detailed status for specific bot
        bot_id = args[0]
        await _show_bot_details(message, bot_manager, bot_id)
    else:
        # Show overview of all bots
        await _show_all_status(message, bot_manager)


async def _show_all_status(message: Message, bot_manager: "BotManager") -> None:
    """Show status overview of all bots."""
    bots = bot_manager.get_all_bots()

    if not bots:
        await message.answer("No bots configured.")
        return

    lines = ["📊 <b>Bot Status Overview</b>\n"]

    status_emoji = {
        "running": "✅",
        "stopped": "⏹️",
        "starting": "🔄",
        "stopping": "⏳",
        "error": "❌",
    }

    for bot_id, managed_bot in bots.items():
        emoji = status_emoji.get(managed_bot.state, "❓")
        name = managed_bot.config.name

        line = f"{emoji} <b>{name}</b> ({bot_id})"

        if managed_bot.state == "running" and managed_bot.started_at:
            uptime = datetime.utcnow() - managed_bot.started_at
            line += f" - {format_timedelta(uptime)}"

        if managed_bot.error_message:
            line += f"\n   ⚠️ {managed_bot.error_message[:50]}"

        lines.append(line)

    # Summary
    total = len(bots)
    running = len([b for b in bots.values() if b.state == "running"])
    lines.append(f"\n<b>Summary:</b> {running}/{total} running")

    await message.answer("\n".join(lines), parse_mode="HTML")


async def _show_bot_details(
    message: Message,
    bot_manager: "BotManager",
    bot_id: str,
) -> None:
    """Show detailed status for a specific bot."""
    managed_bot = bot_manager.get_bot(bot_id)

    if not managed_bot:
        await message.answer(f"Bot not found: {bot_id}")
        return

    status_emoji = {
        "running": "✅",
        "stopped": "⏹️",
        "starting": "🔄",
        "stopping": "⏳",
        "error": "❌",
    }

    emoji = status_emoji.get(managed_bot.state, "❓")

    lines = [
        f"🤖 <b>{managed_bot.config.name}</b>",
        f"<b>ID:</b> {bot_id}",
        f"<b>Description:</b> {managed_bot.config.description or 'N/A'}",
        f"<b>Status:</b> {emoji} {managed_bot.state.title()}",
        f"<b>Mode:</b> {managed_bot.mode}",
        f"<b>Enabled:</b> {'Yes' if managed_bot.config.enabled else 'No'}",
    ]

    if managed_bot.started_at:
        uptime = datetime.utcnow() - managed_bot.started_at
        lines.append(f"<b>Uptime:</b> {format_timedelta(uptime)}")
        lines.append(f"<b>Started:</b> {managed_bot.started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    if managed_bot.error_message:
        lines.append(f"<b>Last Error:</b> {managed_bot.error_message}")

    # Plugin info
    plugins = [p.name for p in managed_bot.config.plugins if p.enabled]
    if plugins:
        lines.append(f"<b>Plugins:</b> {', '.join(plugins)}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("list"))
async def cmd_list(message: Message, bot_manager: "BotManager") -> None:
    """
    List all configured bots.

    Usage: /list
    """
    bots = bot_manager.get_all_bots()

    if not bots:
        await message.answer("No bots configured.")
        return

    lines = ["📋 <b>Configured Bots</b>\n"]

    for bot_id, managed_bot in bots.items():
        enabled = "✓" if managed_bot.config.enabled else "✗"
        lines.append(f"• <code>{bot_id}</code> - {managed_bot.config.name} [{enabled}]")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("health"))
async def cmd_health(message: Message, bot_manager: "BotManager") -> None:
    """
    Show system health status.

    Usage: /health
    """
    from src.health.checks import get_health_status

    health = await get_health_status(bot_manager)

    status_emoji = "✅" if health["status"] == "healthy" else "⚠️"

    lines = [f"{status_emoji} <b>System Health</b>\n"]

    for component, details in health.get("components", {}).items():
        if isinstance(details, dict):
            comp_status = details.get("status", "unknown")
            emoji = "✅" if comp_status == "healthy" else "❌"
            lines.append(f"{emoji} <b>{component}:</b> {comp_status}")
        else:
            lines.append(f"• <b>{component}:</b> {details}")

    await message.answer("\n".join(lines), parse_mode="HTML")
