"""Help command plugin."""

from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.plugins.base import BasePlugin


class HelpPlugin(BasePlugin):
    """Handles the /help command with a customizable command list."""

    name = "help"
    description = "Handles /help command with configurable command descriptions"
    version = "1.0.0"
    author = "Multibot System"

    def setup_handlers(self, router: Router) -> None:
        """Register the /help command handler."""

        @router.message(Command("help"))
        async def handle_help(message: Message) -> None:
            header = self.get_config("header", "Available Commands")
            commands: list[dict[str, str]] = self.get_config("commands", [])

            lines = [f"<b>{header}</b>\n"]

            if commands:
                for cmd in commands:
                    command = cmd.get("command", "")
                    description = cmd.get("description", "")
                    if command:
                        lines.append(f"{command} - {description}")
            else:
                lines.append("/start - Start the bot")
                lines.append("/help - Show this help message")

            footer = self.get_config("footer", "")
            if footer:
                lines.append(f"\n{footer}")

            await message.answer("\n".join(lines), parse_mode="HTML")


# Export for auto-discovery
plugin = HelpPlugin
