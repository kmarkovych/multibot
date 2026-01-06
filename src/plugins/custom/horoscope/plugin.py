"""Horoscope bot plugin with OpenAI integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from src.plugins.base import BasePlugin

from .cache import HoroscopeCache
from .keyboards import (
    get_confirm_keyboard,
    get_horoscope_keyboard,
    get_main_menu_keyboard,
    get_settings_keyboard,
    get_time_keyboard,
    get_zodiac_keyboard,
)
from .openai_client import HoroscopeGenerationError, OpenAIClient
from .scheduler import HoroscopeScheduler
from .subscription import SubscriptionManager
from .zodiac import ZodiacSign

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HoroscopePlugin(BasePlugin):
    """
    Horoscope bot plugin with daily delivery.

    Features:
    - Generate horoscopes using OpenAI gpt-4.1-nano
    - Cache horoscopes per zodiac sign per day
    - Subscribe to daily horoscope delivery
    """

    name = "horoscope"
    description = "Daily horoscope with AI generation"
    version = "1.0.0"
    author = "Multibot System"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._openai: OpenAIClient | None = None
        self._cache: HoroscopeCache | None = None
        self._subscriptions: SubscriptionManager | None = None
        self._scheduler: HoroscopeScheduler | None = None
        self._bot: Bot | None = None

    def setup_handlers(self, router: Router) -> None:
        """Register all command and callback handlers."""

        @router.message(CommandStart())
        async def cmd_start(message: Message) -> None:
            """Welcome message with main menu."""
            welcome = self.get_config("welcome_message", None) or """
<b>\u2b50 Welcome to Horoscope Bot!</b>

I can provide you with personalized daily horoscopes powered by AI.

<b>Features:</b>
\u2022 Get your daily horoscope
\u2022 Subscribe to receive it automatically
\u2022 Choose your preferred delivery time

Select an option below to get started!
"""
            await message.answer(
                welcome.strip(),
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

        @router.message(Command("horoscope"))
        async def cmd_horoscope(message: Message) -> None:
            """Get today's horoscope."""
            if not self._subscriptions or not self._scheduler:
                await message.answer("Service not ready. Please try again later.")
                return

            # Check if user has a saved sign
            sub = await self._subscriptions.get_subscription(message.from_user.id)

            if sub:
                # User has subscription, use their sign
                await self._send_horoscope(message, sub.zodiac_sign)
            else:
                # Ask user to select sign
                await message.answer(
                    "<b>\u2648 Select Your Zodiac Sign</b>\n\n"
                    "Choose your sign to get today's horoscope:",
                    reply_markup=get_zodiac_keyboard(),
                    parse_mode="HTML",
                )

        @router.message(Command("subscribe"))
        async def cmd_subscribe(message: Message) -> None:
            """Subscribe to daily horoscope."""
            await message.answer(
                "<b>\ud83d\udcc5 Subscribe to Daily Horoscope</b>\n\n"
                "First, select your zodiac sign:",
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.message(Command("unsubscribe"))
        async def cmd_unsubscribe(message: Message) -> None:
            """Unsubscribe from daily horoscope."""
            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(message.from_user.id)

            if not sub:
                await message.answer(
                    "You don't have an active subscription.",
                    parse_mode="HTML",
                )
                return

            await message.answer(
                f"<b>\u274c Unsubscribe?</b>\n\n"
                f"You're currently subscribed to receive {sub.zodiac_sign.format_display()} "
                f"horoscope daily at {sub.delivery_hour:02d}:00 UTC.\n\n"
                f"Do you want to unsubscribe?",
                reply_markup=get_confirm_keyboard("unsubscribe"),
                parse_mode="HTML",
            )

        @router.message(Command("settings"))
        async def cmd_settings(message: Message) -> None:
            """Show settings menu."""
            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(message.from_user.id)

            if sub:
                text = (
                    f"<b>\u2699\ufe0f Your Settings</b>\n\n"
                    f"<b>Sign:</b> {sub.zodiac_sign.format_display()}\n"
                    f"<b>Delivery:</b> Daily at {sub.delivery_hour:02d}:00 UTC\n"
                    f"<b>Status:</b> \u2705 Active"
                )
            else:
                text = (
                    "<b>\u2699\ufe0f Settings</b>\n\n"
                    "You don't have an active subscription yet.\n"
                    "Subscribe to receive daily horoscopes!"
                )

            await message.answer(
                text,
                reply_markup=get_settings_keyboard(sub is not None),
                parse_mode="HTML",
            )

        @router.message(Command("help"))
        async def cmd_help(message: Message) -> None:
            """Show help message."""
            help_text = """
<b>\u2753 Horoscope Bot Help</b>

<b>Commands:</b>
/start - Show main menu
/horoscope - Get today's horoscope
/subscribe - Subscribe to daily delivery
/unsubscribe - Cancel subscription
/settings - View and change settings
/help - Show this help

<b>How it works:</b>
1. Select your zodiac sign
2. Get your personalized horoscope
3. Subscribe to receive it daily!

<b>Tip:</b> Horoscopes are generated using AI and cached daily for each sign.
"""
            await message.answer(help_text.strip(), parse_mode="HTML")

        # Callback handlers for main menu
        @router.callback_query(F.data == "menu_horoscope")
        async def cb_menu_horoscope(callback: CallbackQuery) -> None:
            """Handle horoscope menu button."""
            await callback.answer()

            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(callback.from_user.id)

            if sub:
                await callback.message.edit_text(
                    "\u23f3 Generating your horoscope...",
                )
                await self._send_horoscope_edit(callback.message, sub.zodiac_sign)
            else:
                await callback.message.edit_text(
                    "<b>\u2648 Select Your Zodiac Sign</b>\n\n"
                    "Choose your sign to get today's horoscope:",
                    reply_markup=get_zodiac_keyboard(),
                    parse_mode="HTML",
                )

        @router.callback_query(F.data == "menu_subscribe")
        async def cb_menu_subscribe(callback: CallbackQuery) -> None:
            """Handle subscribe menu button."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\ud83d\udcc5 Subscribe to Daily Horoscope</b>\n\n"
                "First, select your zodiac sign:",
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "menu_settings")
        async def cb_menu_settings(callback: CallbackQuery) -> None:
            """Handle settings menu button."""
            await callback.answer()

            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(callback.from_user.id)

            if sub:
                text = (
                    f"<b>\u2699\ufe0f Your Settings</b>\n\n"
                    f"<b>Sign:</b> {sub.zodiac_sign.format_display()}\n"
                    f"<b>Delivery:</b> Daily at {sub.delivery_hour:02d}:00 UTC\n"
                    f"<b>Status:</b> \u2705 Active"
                )
            else:
                text = (
                    "<b>\u2699\ufe0f Settings</b>\n\n"
                    "You don't have an active subscription yet.\n"
                    "Subscribe to receive daily horoscopes!"
                )

            await callback.message.edit_text(
                text,
                reply_markup=get_settings_keyboard(sub is not None),
                parse_mode="HTML",
            )

        # Zodiac sign selection callbacks
        @router.callback_query(F.data.startswith("zodiac_"))
        async def cb_zodiac_select(callback: CallbackQuery) -> None:
            """Handle zodiac sign selection."""
            sign_name = callback.data.replace("zodiac_", "")
            sign = ZodiacSign.from_name(sign_name)

            if not sign:
                await callback.answer("Invalid sign", show_alert=True)
                return

            await callback.answer()

            # Check context - are we subscribing or just getting horoscope?
            msg_text = callback.message.text or ""

            if "Subscribe" in msg_text:
                # User is subscribing - ask for time
                # Store sign temporarily in callback state
                await callback.message.edit_text(
                    f"<b>\u23f0 Select Delivery Time</b>\n\n"
                    f"Sign: {sign.format_display()}\n\n"
                    f"When would you like to receive your daily horoscope? (UTC)",
                    reply_markup=get_time_keyboard(),
                    parse_mode="HTML",
                )
                # Store the sign choice for the time selection
                # We'll use the message as context
                callback.message._sign_choice = sign.name  # noqa: SLF001
            else:
                # Just getting horoscope
                await callback.message.edit_text("\u23f3 Generating your horoscope...")
                await self._send_horoscope_edit(callback.message, sign)

        # Time selection for subscription
        @router.callback_query(F.data.startswith("subtime_"))
        async def cb_time_select(callback: CallbackQuery) -> None:
            """Handle delivery time selection."""
            hour = int(callback.data.replace("subtime_", ""))

            if not self._subscriptions:
                await callback.answer("Service not ready", show_alert=True)
                return

            # Get sign from message context (look at the message text)
            msg_text = callback.message.text or ""
            sign = None

            for s in ZodiacSign:
                if s.value in msg_text:
                    sign = s
                    break

            if not sign:
                await callback.answer("Please select your sign first", show_alert=True)
                return

            await callback.answer()

            # Create subscription
            await self._subscriptions.subscribe(
                telegram_id=callback.from_user.id,
                sign=sign,
                delivery_hour=hour,
            )

            await callback.message.edit_text(
                f"<b>\u2705 Subscribed Successfully!</b>\n\n"
                f"<b>Sign:</b> {sign.format_display()}\n"
                f"<b>Delivery:</b> Daily at {hour:02d}:00 UTC\n\n"
                f"You'll receive your first horoscope at the scheduled time.\n"
                f"Use /horoscope to get today's horoscope now!",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "sub_cancel")
        async def cb_sub_cancel(callback: CallbackQuery) -> None:
            """Cancel subscription flow."""
            await callback.answer("Cancelled")
            await callback.message.edit_text(
                "Subscription cancelled.\n\nUse /start to return to the main menu.",
            )

        # Settings callbacks
        @router.callback_query(F.data == "settings_sign")
        async def cb_settings_sign(callback: CallbackQuery) -> None:
            """Change zodiac sign."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\u2648 Change Your Zodiac Sign</b>\n\n"
                "Select your new sign:",
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_time")
        async def cb_settings_time(callback: CallbackQuery) -> None:
            """Change delivery time."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\u23f0 Change Delivery Time</b>\n\n"
                "Select your preferred time (UTC):",
                reply_markup=get_time_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_sub")
        async def cb_settings_sub(callback: CallbackQuery) -> None:
            """Start subscription from settings."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\ud83d\udcc5 Subscribe to Daily Horoscope</b>\n\n"
                "First, select your zodiac sign:",
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_unsub")
        async def cb_settings_unsub(callback: CallbackQuery) -> None:
            """Unsubscribe from settings."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\u274c Unsubscribe?</b>\n\n"
                "Are you sure you want to cancel your daily horoscope?",
                reply_markup=get_confirm_keyboard("unsubscribe"),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_back")
        async def cb_settings_back(callback: CallbackQuery) -> None:
            """Back to main menu from settings."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\u2b50 Horoscope Bot</b>\n\n"
                "Select an option:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

        # Confirmation callbacks
        @router.callback_query(F.data == "confirm_unsubscribe")
        async def cb_confirm_unsub(callback: CallbackQuery) -> None:
            """Confirm unsubscribe."""
            if not self._subscriptions:
                return

            await callback.answer()
            await self._subscriptions.unsubscribe(callback.from_user.id)

            await callback.message.edit_text(
                "<b>\u2705 Unsubscribed</b>\n\n"
                "You've been unsubscribed from daily horoscopes.\n"
                "You can still use /horoscope to get your horoscope anytime!",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "confirm_cancel")
        async def cb_confirm_cancel(callback: CallbackQuery) -> None:
            """Cancel confirmation."""
            await callback.answer("Cancelled")

            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(callback.from_user.id)
            await callback.message.edit_text(
                "<b>\u2699\ufe0f Settings</b>\n\nAction cancelled.",
                reply_markup=get_settings_keyboard(sub is not None),
                parse_mode="HTML",
            )

        # Horoscope result callbacks
        @router.callback_query(F.data == "horoscope_other")
        async def cb_horoscope_other(callback: CallbackQuery) -> None:
            """Select another zodiac sign."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\u2648 Select Zodiac Sign</b>\n\n"
                "Choose a sign to get today's horoscope:",
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "horoscope_menu")
        async def cb_horoscope_menu(callback: CallbackQuery) -> None:
            """Back to main menu."""
            await callback.answer()
            await callback.message.edit_text(
                "<b>\u2b50 Horoscope Bot</b>\n\n"
                "Select an option:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

    async def _send_horoscope(self, message: Message, sign: ZodiacSign) -> None:
        """Send horoscope as a new message."""
        if not self._scheduler:
            await message.answer("Service not ready. Please try again later.")
            return

        try:
            processing = await message.answer("\u23f3 Generating your horoscope...")

            horoscope_msg = await self._scheduler.deliver_now(
                message.from_user.id, sign
            )

            await processing.delete()
            await message.answer(
                horoscope_msg,
                parse_mode="HTML",
                reply_markup=get_horoscope_keyboard(),
            )

        except HoroscopeGenerationError as e:
            await message.answer(f"\u274c {e}")

    async def _send_horoscope_edit(self, message: Message, sign: ZodiacSign) -> None:
        """Send horoscope by editing existing message."""
        if not self._scheduler:
            await message.edit_text("Service not ready. Please try again later.")
            return

        try:
            horoscope_msg = await self._scheduler.deliver_now(0, sign)
            await message.edit_text(
                horoscope_msg,
                parse_mode="HTML",
                reply_markup=get_horoscope_keyboard(),
            )

        except HoroscopeGenerationError as e:
            await message.edit_text(f"\u274c {e}")

    async def on_load(self, bot: Bot) -> None:
        """Initialize plugin components when loaded."""
        self._bot = bot

        # Get API key from config
        api_key = self.get_config("openai_api_key", "")
        if not api_key:
            logger.error("OpenAI API key not configured for horoscope plugin")
            return

        # Initialize components
        self._openai = OpenAIClient(api_key)
        self._cache = HoroscopeCache(self.db, self.bot_id)
        self._subscriptions = SubscriptionManager(self.db, self.bot_id)
        self._scheduler = HoroscopeScheduler(
            bot=bot,
            subscription_manager=self._subscriptions,
            cache=self._cache,
            openai_client=self._openai,
        )

        # Start scheduler
        await self._scheduler.start()
        logger.info("Horoscope plugin loaded and scheduler started")

    async def on_unload(self, bot: Bot) -> None:
        """Cleanup when plugin is unloaded."""
        if self._scheduler:
            await self._scheduler.stop()

        if self._openai:
            await self._openai.close()

        logger.info("Horoscope plugin unloaded")
