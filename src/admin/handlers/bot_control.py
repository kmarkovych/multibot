"""Bot control command handlers for admin bot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager
    from src.core.config import ConfigManager

logger = logging.getLogger(__name__)

router = Router(name="admin_bot_control")


def _create_confirmation_keyboard(action: str, bot_id: str) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for bot actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirm",
                    callback_data=f"confirm_{action}_{bot_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data="cancel_action",
                ),
            ]
        ]
    )


@router.message(Command("start_bot"))
async def cmd_start_bot(message: Message, bot_manager: BotManager) -> None:
    """
    Start a stopped bot.

    Usage: /start_bot <bot_id>
    """
    args = message.text.split()[1:] if message.text else []

    if not args:
        await message.answer(
            "Usage: /start_bot <bot_id>\n\n"
            "Use /list to see available bots."
        )
        return

    bot_id = args[0]
    managed_bot = bot_manager.get_bot(bot_id)

    if not managed_bot:
        await message.answer(f"Bot not found: {bot_id}")
        return

    if managed_bot.state == "running":
        await message.answer(f"Bot {bot_id} is already running.")
        return

    await message.answer(
        f"Start bot <b>{managed_bot.config.name}</b> ({bot_id})?",
        reply_markup=_create_confirmation_keyboard("start", bot_id),
        parse_mode="HTML",
    )


@router.message(Command("stop_bot"))
async def cmd_stop_bot(message: Message, bot_manager: BotManager) -> None:
    """
    Stop a running bot.

    Usage: /stop_bot <bot_id>
    """
    args = message.text.split()[1:] if message.text else []

    if not args:
        await message.answer(
            "Usage: /stop_bot <bot_id>\n\n"
            "Use /list to see available bots."
        )
        return

    bot_id = args[0]
    managed_bot = bot_manager.get_bot(bot_id)

    if not managed_bot:
        await message.answer(f"Bot not found: {bot_id}")
        return

    if managed_bot.state != "running":
        await message.answer(f"Bot {bot_id} is not running.")
        return

    await message.answer(
        f"Stop bot <b>{managed_bot.config.name}</b> ({bot_id})?",
        reply_markup=_create_confirmation_keyboard("stop", bot_id),
        parse_mode="HTML",
    )


@router.message(Command("restart_bot"))
async def cmd_restart_bot(message: Message, bot_manager: BotManager) -> None:
    """
    Restart a bot.

    Usage: /restart_bot <bot_id>
    """
    args = message.text.split()[1:] if message.text else []

    if not args:
        await message.answer(
            "Usage: /restart_bot <bot_id>\n\n"
            "Use /list to see available bots."
        )
        return

    bot_id = args[0]
    managed_bot = bot_manager.get_bot(bot_id)

    if not managed_bot:
        await message.answer(f"Bot not found: {bot_id}")
        return

    await message.answer(
        f"Restart bot <b>{managed_bot.config.name}</b> ({bot_id})?",
        reply_markup=_create_confirmation_keyboard("restart", bot_id),
        parse_mode="HTML",
    )


@router.message(Command("reload"))
async def cmd_reload(
    message: Message,
    bot_manager: BotManager,
    config_manager: ConfigManager,
) -> None:
    """
    Reload a bot's configuration.

    Usage: /reload <bot_id>
    """
    args = message.text.split()[1:] if message.text else []

    if not args:
        await message.answer(
            "Usage: /reload <bot_id>\n\n"
            "This reloads the bot's configuration from disk."
        )
        return

    bot_id = args[0]
    managed_bot = bot_manager.get_bot(bot_id)

    if not managed_bot:
        await message.answer(f"Bot not found: {bot_id}")
        return

    await message.answer(f"🔄 Reloading configuration for {bot_id}...")

    try:
        new_config = config_manager.reload_bot_config(bot_id)
        if not new_config:
            await message.answer(f"❌ Could not find config file for {bot_id}")
            return

        await bot_manager.reload_bot(bot_id, new_config)
        await message.answer(f"✅ Bot {bot_id} reloaded successfully")

    except Exception as e:
        logger.error(f"Error reloading bot {bot_id}: {e}")
        await message.answer(f"❌ Error reloading bot: {e}")


@router.message(Command("reload_all"))
async def cmd_reload_all(
    message: Message,
    bot_manager: BotManager,
    config_manager: ConfigManager,
) -> None:
    """
    Reload all bot configurations.

    Usage: /reload_all
    """
    await message.answer(
        "Reload all bot configurations?",
        reply_markup=_create_confirmation_keyboard("reload_all", "all"),
    )


# Callback query handlers for confirmations


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_"))
async def handle_confirmation(
    callback: CallbackQuery,
    bot_manager: BotManager,
    config_manager: ConfigManager,
) -> None:
    """Handle confirmation callbacks."""
    if not callback.data or not callback.message:
        return

    parts = callback.data.split("_", 2)
    if len(parts) < 3:
        return

    action = parts[1]
    bot_id = parts[2]

    await callback.answer()

    try:
        if action == "start":
            await callback.message.edit_text(f"🔄 Starting bot {bot_id}...")
            await bot_manager.start_bot(bot_id)
            await callback.message.edit_text(f"✅ Bot {bot_id} started successfully")

        elif action == "stop":
            await callback.message.edit_text(f"🔄 Stopping bot {bot_id}...")
            await bot_manager.stop_bot(bot_id)
            await callback.message.edit_text(f"✅ Bot {bot_id} stopped")

        elif action == "restart":
            await callback.message.edit_text(f"🔄 Restarting bot {bot_id}...")
            await bot_manager.restart_bot(bot_id)
            await callback.message.edit_text(f"✅ Bot {bot_id} restarted")

        elif action == "reload_all":
            await callback.message.edit_text("🔄 Reloading all configurations...")
            bot_configs = config_manager.load_bot_configs()

            results = []
            for bid, config in bot_configs.items():
                try:
                    if bot_manager.get_bot(bid):
                        await bot_manager.reload_bot(bid, config)
                    results.append(f"✅ {bid}")
                except Exception as e:
                    results.append(f"❌ {bid}: {e}")

            await callback.message.edit_text(
                "Reload complete:\n" + "\n".join(results)
            )

    except Exception as e:
        logger.error(f"Error executing {action} for {bot_id}: {e}")
        await callback.message.edit_text(f"❌ Error: {e}")


@router.callback_query(lambda c: c.data == "cancel_action")
async def handle_cancel(callback: CallbackQuery) -> None:
    """Handle cancel callbacks."""
    await callback.answer("Cancelled")
    if callback.message:
        await callback.message.edit_text("❌ Action cancelled")
