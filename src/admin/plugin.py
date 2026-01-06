"""Admin plugin that provides bot management commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.admin.handlers.bot_control import router as bot_control_router
from src.admin.handlers.status import router as status_router
from src.plugins.base import BasePlugin

if TYPE_CHECKING:
    from src.core.bot_manager import BotManager


class AdminPlugin(BasePlugin):
    """
    Admin plugin for managing bots through Telegram.

    Provides commands for:
    - Viewing bot status
    - Starting/stopping bots
    - Reloading configurations
    - System health checks
    """

    name = "admin_core"
    description = "Admin commands for bot management"
    version = "1.0.0"
    author = "Multibot System"
    supports_hot_reload = False  # Admin bot shouldn't be reloaded

    def _create_main_keyboard(self) -> InlineKeyboardMarkup:
        """Create the main admin keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 Status", callback_data="admin_status"),
                    InlineKeyboardButton(text="📋 List Bots", callback_data="admin_list"),
                ],
                [
                    InlineKeyboardButton(text="💚 Health", callback_data="admin_health"),
                    InlineKeyboardButton(text="🔄 Reload All", callback_data="admin_reload_all"),
                ],
                [
                    InlineKeyboardButton(text="❓ Help", callback_data="admin_help"),
                ],
            ]
        )

    def _create_bot_actions_keyboard(self, bot_id: str, state: str) -> InlineKeyboardMarkup:
        """Create keyboard for bot-specific actions."""
        buttons = []

        if state == "running":
            buttons.append([
                InlineKeyboardButton(text="⏹️ Stop", callback_data=f"quick_stop_{bot_id}"),
                InlineKeyboardButton(text="🔄 Restart", callback_data=f"quick_restart_{bot_id}"),
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text="▶️ Start", callback_data=f"quick_start_{bot_id}"),
            ])

        buttons.append([
            InlineKeyboardButton(text="📄 Details", callback_data=f"bot_details_{bot_id}"),
            InlineKeyboardButton(text="🔃 Reload Config", callback_data=f"quick_reload_{bot_id}"),
        ])
        buttons.append([
            InlineKeyboardButton(text="« Back to Menu", callback_data="admin_menu"),
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def setup_handlers(self, router: Router) -> None:
        """Register admin command handlers."""
        # Include sub-routers
        router.include_router(status_router)
        router.include_router(bot_control_router)

        @router.message(CommandStart())
        async def cmd_start(message: Message, bot_manager: BotManager) -> None:
            """Handle /start command with main menu."""
            bots = bot_manager.get_all_bots()
            running = len([b for b in bots.values() if b.state == "running"])
            total = len(bots)

            welcome = f"""
<b>🤖 Multibot Admin Panel</b>

Welcome to the admin bot! From here you can monitor and control all your Telegram bots.

<b>Quick Stats:</b>
• Bots: {running}/{total} running
• System: Online

Select an option below or use /help to see all commands.
"""
            await message.answer(
                welcome.strip(),
                reply_markup=self._create_main_keyboard(),
                parse_mode="HTML",
            )

        @router.message(Command("menu"))
        async def cmd_menu(message: Message, bot_manager: BotManager) -> None:
            """Show the main menu."""
            bots = bot_manager.get_all_bots()
            running = len([b for b in bots.values() if b.state == "running"])
            total = len(bots)

            await message.answer(
                f"<b>🤖 Admin Menu</b>\n\nBots: {running}/{total} running",
                reply_markup=self._create_main_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "admin_menu")
        async def cb_admin_menu(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Return to main menu."""
            bots = bot_manager.get_all_bots()
            running = len([b for b in bots.values() if b.state == "running"])
            total = len(bots)

            await callback.answer()
            await callback.message.edit_text(
                f"<b>🤖 Admin Menu</b>\n\nBots: {running}/{total} running",
                reply_markup=self._create_main_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "admin_status")
        async def cb_status(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Show status via callback."""
            await callback.answer()
            bots = bot_manager.get_all_bots()

            if not bots:
                await callback.message.edit_text(
                    "No bots configured.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="« Back", callback_data="admin_menu")]
                    ]),
                )
                return

            status_emoji = {
                "running": "✅",
                "stopped": "⏹️",
                "starting": "🔄",
                "stopping": "⏳",
                "error": "❌",
            }

            lines = ["<b>📊 Bot Status</b>\n"]
            buttons = []

            for bot_id, managed_bot in bots.items():
                emoji = status_emoji.get(managed_bot.state, "❓")
                name = managed_bot.config.name
                lines.append(f"{emoji} <b>{name}</b> - {managed_bot.state}")
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{emoji} {name}",
                        callback_data=f"bot_select_{bot_id}",
                    )
                ])

            buttons.append([InlineKeyboardButton(text="« Back", callback_data="admin_menu")])

            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "admin_list")
        async def cb_list(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """List bots via callback."""
            await callback.answer()
            bots = bot_manager.get_all_bots()

            if not bots:
                await callback.message.edit_text(
                    "No bots configured.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="« Back", callback_data="admin_menu")]
                    ]),
                )
                return

            lines = ["<b>📋 Configured Bots</b>\n"]
            buttons = []

            for bot_id, managed_bot in bots.items():
                enabled = "✓" if managed_bot.config.enabled else "✗"
                lines.append(f"• <code>{bot_id}</code> - {managed_bot.config.name} [{enabled}]")
                buttons.append([
                    InlineKeyboardButton(
                        text=managed_bot.config.name,
                        callback_data=f"bot_select_{bot_id}",
                    )
                ])

            buttons.append([InlineKeyboardButton(text="« Back", callback_data="admin_menu")])

            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "admin_health")
        async def cb_health(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Show health via callback."""
            await callback.answer()

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

            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_health")],
                    [InlineKeyboardButton(text="« Back", callback_data="admin_menu")],
                ]),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "admin_reload_all")
        async def cb_reload_all(callback: CallbackQuery) -> None:
            """Confirm reload all."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>🔄 Reload All Configurations?</b>\n\n"
                "This will reload all bot configurations from disk.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_reload_all_all"),
                        InlineKeyboardButton(text="❌ Cancel", callback_data="admin_menu"),
                    ],
                ]),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "admin_help")
        async def cb_help(callback: CallbackQuery) -> None:
            """Show help via callback."""
            await callback.answer()
            help_text = """
<b>❓ Admin Bot Help</b>

<b>Commands:</b>
/start - Show main menu
/menu - Show main menu
/status - Bot status overview
/list - List all bots
/health - System health

<b>Bot Control:</b>
/start_bot &lt;id&gt; - Start a bot
/stop_bot &lt;id&gt; - Stop a bot
/restart_bot &lt;id&gt; - Restart
/reload &lt;id&gt; - Reload config

<b>Tips:</b>
• Use the buttons for quick actions
• Tap a bot name to manage it
"""
            await callback.message.edit_text(
                help_text.strip(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="« Back", callback_data="admin_menu")],
                ]),
                parse_mode="HTML",
            )

        @router.callback_query(F.data.startswith("bot_select_"))
        async def cb_bot_select(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Select a bot to manage."""
            bot_id = callback.data.replace("bot_select_", "")
            managed_bot = bot_manager.get_bot(bot_id)

            if not managed_bot:
                await callback.answer("Bot not found", show_alert=True)
                return

            await callback.answer()

            status_emoji = {
                "running": "✅",
                "stopped": "⏹️",
                "starting": "🔄",
                "stopping": "⏳",
                "error": "❌",
            }
            emoji = status_emoji.get(managed_bot.state, "❓")

            text = f"""
<b>🤖 {managed_bot.config.name}</b>

<b>ID:</b> <code>{bot_id}</code>
<b>Status:</b> {emoji} {managed_bot.state.title()}
<b>Mode:</b> {managed_bot.mode}

Select an action:
"""
            await callback.message.edit_text(
                text.strip(),
                reply_markup=self._create_bot_actions_keyboard(bot_id, managed_bot.state),
                parse_mode="HTML",
            )

        @router.callback_query(F.data.startswith("bot_details_"))
        async def cb_bot_details(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Show detailed bot info."""
            from datetime import datetime

            from src.admin.handlers.status import format_timedelta

            bot_id = callback.data.replace("bot_details_", "")
            managed_bot = bot_manager.get_bot(bot_id)

            if not managed_bot:
                await callback.answer("Bot not found", show_alert=True)
                return

            await callback.answer()

            status_emoji = {
                "running": "✅",
                "stopped": "⏹️",
                "starting": "🔄",
                "stopping": "⏳",
                "error": "❌",
            }
            emoji = status_emoji.get(managed_bot.state, "❓")

            lines = [
                f"<b>🤖 {managed_bot.config.name}</b>\n",
                f"<b>ID:</b> <code>{bot_id}</code>",
                f"<b>Description:</b> {managed_bot.config.description or 'N/A'}",
                f"<b>Status:</b> {emoji} {managed_bot.state.title()}",
                f"<b>Mode:</b> {managed_bot.mode}",
                f"<b>Enabled:</b> {'Yes' if managed_bot.config.enabled else 'No'}",
            ]

            if managed_bot.started_at:
                uptime = datetime.utcnow() - managed_bot.started_at
                lines.append(f"<b>Uptime:</b> {format_timedelta(uptime)}")

            if managed_bot.error_message:
                lines.append(f"<b>Error:</b> {managed_bot.error_message[:100]}")

            plugins = [p.name for p in managed_bot.config.plugins if p.enabled]
            if plugins:
                lines.append(f"<b>Plugins:</b> {', '.join(plugins)}")

            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="« Back", callback_data=f"bot_select_{bot_id}")],
                ]),
                parse_mode="HTML",
            )

        @router.callback_query(F.data.startswith("quick_start_"))
        async def cb_quick_start(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Quick start a bot."""
            bot_id = callback.data.replace("quick_start_", "")
            await callback.answer("Starting...")

            try:
                await bot_manager.start_bot(bot_id)
                await callback.answer("Bot started!", show_alert=True)
            except Exception as e:
                await callback.answer(f"Error: {e}", show_alert=True)
                return

            # Refresh the bot view
            managed_bot = bot_manager.get_bot(bot_id)
            if managed_bot:
                status_emoji = {"running": "✅", "stopped": "⏹️", "error": "❌"}
                emoji = status_emoji.get(managed_bot.state, "❓")
                await callback.message.edit_text(
                    f"<b>🤖 {managed_bot.config.name}</b>\n\n"
                    f"<b>Status:</b> {emoji} {managed_bot.state.title()}\n\n"
                    "Select an action:",
                    reply_markup=self._create_bot_actions_keyboard(bot_id, managed_bot.state),
                    parse_mode="HTML",
                )

        @router.callback_query(F.data.startswith("quick_stop_"))
        async def cb_quick_stop(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Quick stop a bot."""
            bot_id = callback.data.replace("quick_stop_", "")
            await callback.answer("Stopping...")

            try:
                await bot_manager.stop_bot(bot_id)
                await callback.answer("Bot stopped!", show_alert=True)
            except Exception as e:
                await callback.answer(f"Error: {e}", show_alert=True)
                return

            managed_bot = bot_manager.get_bot(bot_id)
            if managed_bot:
                status_emoji = {"running": "✅", "stopped": "⏹️", "error": "❌"}
                emoji = status_emoji.get(managed_bot.state, "❓")
                await callback.message.edit_text(
                    f"<b>🤖 {managed_bot.config.name}</b>\n\n"
                    f"<b>Status:</b> {emoji} {managed_bot.state.title()}\n\n"
                    "Select an action:",
                    reply_markup=self._create_bot_actions_keyboard(bot_id, managed_bot.state),
                    parse_mode="HTML",
                )

        @router.callback_query(F.data.startswith("quick_restart_"))
        async def cb_quick_restart(callback: CallbackQuery, bot_manager: BotManager) -> None:
            """Quick restart a bot."""
            bot_id = callback.data.replace("quick_restart_", "")
            await callback.answer("Restarting...")

            try:
                await bot_manager.restart_bot(bot_id)
                await callback.answer("Bot restarted!", show_alert=True)
            except Exception as e:
                await callback.answer(f"Error: {e}", show_alert=True)
                return

            managed_bot = bot_manager.get_bot(bot_id)
            if managed_bot:
                status_emoji = {"running": "✅", "stopped": "⏹️", "error": "❌"}
                emoji = status_emoji.get(managed_bot.state, "❓")
                await callback.message.edit_text(
                    f"<b>🤖 {managed_bot.config.name}</b>\n\n"
                    f"<b>Status:</b> {emoji} {managed_bot.state.title()}\n\n"
                    "Select an action:",
                    reply_markup=self._create_bot_actions_keyboard(bot_id, managed_bot.state),
                    parse_mode="HTML",
                )

        @router.callback_query(F.data.startswith("quick_reload_"))
        async def cb_quick_reload(
            callback: CallbackQuery,
            bot_manager: BotManager,
            config_manager,
        ) -> None:
            """Quick reload a bot's config."""
            bot_id = callback.data.replace("quick_reload_", "")
            await callback.answer("Reloading config...")

            try:
                new_config = config_manager.reload_bot_config(bot_id)
                if new_config:
                    await bot_manager.reload_bot(bot_id, new_config)
                    await callback.answer("Config reloaded!", show_alert=True)
                else:
                    await callback.answer("Config file not found", show_alert=True)
            except Exception as e:
                await callback.answer(f"Error: {e}", show_alert=True)

        @router.message(Command("help"))
        async def admin_help(message: Message) -> None:
            help_text = """
<b>Admin Bot Commands</b>

<b>Status & Monitoring:</b>
/status - Show all bots status
/status &lt;bot_id&gt; - Show detailed status
/list - List all configured bots
/health - Show system health

<b>Bot Control:</b>
/start_bot &lt;bot_id&gt; - Start a bot
/stop_bot &lt;bot_id&gt; - Stop a bot
/restart_bot &lt;bot_id&gt; - Restart a bot

<b>Configuration:</b>
/reload &lt;bot_id&gt; - Reload bot config
/reload_all - Reload all configs

<b>Navigation:</b>
/menu - Show main menu with buttons
"""
            await message.answer(help_text.strip(), parse_mode="HTML")


# Export for plugin discovery
plugin = AdminPlugin
