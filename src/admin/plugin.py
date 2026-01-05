"""Admin plugin that provides bot management commands."""

from __future__ import annotations

from aiogram import Router

from src.admin.handlers.bot_control import router as bot_control_router
from src.admin.handlers.status import router as status_router
from src.plugins.base import BasePlugin


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

    def setup_handlers(self, router: Router) -> None:
        """Register admin command handlers."""
        # Include sub-routers
        router.include_router(status_router)
        router.include_router(bot_control_router)

        # Register help command specific to admin
        from aiogram.filters import Command
        from aiogram.types import Message

        @router.message(Command("help"))
        async def admin_help(message: Message) -> None:
            help_text = """
<b>Admin Bot Commands</b>

<b>Status & Monitoring:</b>
/status - Show all bots status
/status <bot_id> - Show detailed status
/list - List all configured bots
/health - Show system health

<b>Bot Control:</b>
/start_bot <bot_id> - Start a bot
/stop_bot <bot_id> - Stop a bot
/restart_bot <bot_id> - Restart a bot

<b>Configuration:</b>
/reload <bot_id> - Reload bot config
/reload_all - Reload all configs
"""
            await message.answer(help_text.strip(), parse_mode="HTML")


# Export for plugin discovery
plugin = AdminPlugin
