"""Start command plugin."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.plugins.base import BasePlugin


class StartPlugin(BasePlugin):
    """Handles the /start command with a customizable welcome message."""

    name = "start"
    description = "Handles /start command with customizable welcome message"
    version = "1.0.0"
    author = "Multibot System"

    def setup_handlers(self, router: Router) -> None:
        """Register the /start command handler."""

        @router.message(CommandStart())
        async def handle_start(message: Message) -> None:
            welcome_message = self.get_config(
                "welcome_message",
                "Welcome! Use /help to see available commands.",
            )
            await message.answer(welcome_message)


# Export for auto-discovery
plugin = StartPlugin
