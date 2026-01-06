"""Horoscope bot plugin with OpenAI integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, CallbackQuery, Message

from src.plugins.base import BasePlugin

from .cache import HoroscopeCache
from .i18n import SUPPORTED_LANGUAGES, t
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
            lang = message.from_user.language_code if message.from_user else None
            welcome = self.get_config("welcome_message", None) or t("welcome", lang)
            await message.answer(
                welcome.strip(),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML",
            )

        @router.message(Command("horoscope"))
        async def cmd_horoscope(message: Message) -> None:
            """Get today's horoscope."""
            lang = message.from_user.language_code if message.from_user else None
            if not self._subscriptions or not self._scheduler:
                await message.answer(t("service_not_ready", lang))
                return

            # Check if user has a saved sign
            sub = await self._subscriptions.get_subscription(message.from_user.id)

            if sub:
                # User has subscription, use their sign
                await self._send_horoscope(message, sub.zodiac_sign, lang)
            else:
                # Ask user to select sign
                await message.answer(
                    t("select_sign", lang),
                    reply_markup=get_zodiac_keyboard(),
                    parse_mode="HTML",
                )

        @router.message(Command("subscribe"))
        async def cmd_subscribe(message: Message) -> None:
            """Subscribe to daily horoscope."""
            lang = message.from_user.language_code if message.from_user else None
            await message.answer(
                t("subscribe_select_sign", lang),
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.message(Command("unsubscribe"))
        async def cmd_unsubscribe(message: Message) -> None:
            """Unsubscribe from daily horoscope."""
            lang = message.from_user.language_code if message.from_user else None
            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(message.from_user.id)

            if not sub:
                await message.answer(t("no_subscription", lang), parse_mode="HTML")
                return

            await message.answer(
                t(
                    "unsubscribe_confirm",
                    lang,
                    sign=sub.zodiac_sign.format_display(),
                    hour=f"{sub.delivery_hour:02d}",
                ),
                reply_markup=get_confirm_keyboard("unsubscribe", lang),
                parse_mode="HTML",
            )

        @router.message(Command("settings"))
        async def cmd_settings(message: Message) -> None:
            """Show settings menu."""
            lang = message.from_user.language_code if message.from_user else None
            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(message.from_user.id)

            if sub:
                text = t(
                    "settings_with_sub",
                    lang,
                    sign=sub.zodiac_sign.format_display(),
                    hour=f"{sub.delivery_hour:02d}",
                )
            else:
                text = t("settings_no_sub", lang)

            await message.answer(
                text,
                reply_markup=get_settings_keyboard(sub is not None, lang),
                parse_mode="HTML",
            )

        @router.message(Command("help"))
        async def cmd_help(message: Message) -> None:
            """Show help message."""
            lang = message.from_user.language_code if message.from_user else None
            await message.answer(t("help", lang), parse_mode="HTML")

        # Callback handlers for main menu
        @router.callback_query(F.data == "menu_horoscope")
        async def cb_menu_horoscope(callback: CallbackQuery) -> None:
            """Handle horoscope menu button."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()

            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(callback.from_user.id)

            if sub:
                await callback.message.edit_text(t("generating", lang))
                await self._send_horoscope_edit(callback.message, sub.zodiac_sign, lang)
            else:
                await callback.message.edit_text(
                    t("select_sign", lang),
                    reply_markup=get_zodiac_keyboard(),
                    parse_mode="HTML",
                )

        @router.callback_query(F.data == "menu_subscribe")
        async def cb_menu_subscribe(callback: CallbackQuery) -> None:
            """Handle subscribe menu button."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("subscribe_select_sign", lang),
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "menu_settings")
        async def cb_menu_settings(callback: CallbackQuery) -> None:
            """Handle settings menu button."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()

            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(callback.from_user.id)

            if sub:
                text = t(
                    "settings_with_sub",
                    lang,
                    sign=sub.zodiac_sign.format_display(),
                    hour=f"{sub.delivery_hour:02d}",
                )
            else:
                text = t("settings_no_sub", lang)

            await callback.message.edit_text(
                text,
                reply_markup=get_settings_keyboard(sub is not None, lang),
                parse_mode="HTML",
            )

        # Zodiac sign selection callbacks
        @router.callback_query(F.data.startswith("zodiac_"))
        async def cb_zodiac_select(callback: CallbackQuery) -> None:
            """Handle zodiac sign selection."""
            lang = callback.from_user.language_code if callback.from_user else None
            sign_name = callback.data.replace("zodiac_", "")
            sign = ZodiacSign.from_name(sign_name)

            if not sign:
                await callback.answer(t("invalid_sign", lang), show_alert=True)
                return

            await callback.answer()

            # Check context - are we subscribing or just getting horoscope?
            msg_text = callback.message.text or ""

            if "Subscribe" in msg_text or "Підписка" in msg_text:
                # User is subscribing - ask for time
                await callback.message.edit_text(
                    t("select_time", lang, sign=sign.format_display()),
                    reply_markup=get_time_keyboard(lang),
                    parse_mode="HTML",
                )
                callback.message._sign_choice = sign.name  # noqa: SLF001
            else:
                # Just getting horoscope
                await callback.message.edit_text(t("generating", lang))
                await self._send_horoscope_edit(callback.message, sign, lang)

        # Time selection for subscription
        @router.callback_query(F.data.startswith("subtime_"))
        async def cb_time_select(callback: CallbackQuery) -> None:
            """Handle delivery time selection."""
            lang = callback.from_user.language_code if callback.from_user else None
            hour = int(callback.data.replace("subtime_", ""))

            if not self._subscriptions:
                await callback.answer(t("service_not_ready", lang), show_alert=True)
                return

            # Get sign from message context (look at the message text)
            msg_text = callback.message.text or ""
            sign = None

            for s in ZodiacSign:
                if s.value in msg_text:
                    sign = s
                    break

            if not sign:
                await callback.answer(t("select_sign_first", lang), show_alert=True)
                return

            await callback.answer()

            # Create subscription
            await self._subscriptions.subscribe(
                telegram_id=callback.from_user.id,
                sign=sign,
                delivery_hour=hour,
            )

            await callback.message.edit_text(
                t("subscribed", lang, sign=sign.format_display(), hour=f"{hour:02d}"),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "sub_cancel")
        async def cb_sub_cancel(callback: CallbackQuery) -> None:
            """Cancel subscription flow."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer(t("cancelled", lang))
            await callback.message.edit_text(t("sub_cancelled", lang))

        # Settings callbacks
        @router.callback_query(F.data == "settings_sign")
        async def cb_settings_sign(callback: CallbackQuery) -> None:
            """Change zodiac sign."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("select_sign_change", lang),
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_time")
        async def cb_settings_time(callback: CallbackQuery) -> None:
            """Change delivery time."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("change_time", lang),
                reply_markup=get_time_keyboard(lang),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_sub")
        async def cb_settings_sub(callback: CallbackQuery) -> None:
            """Start subscription from settings."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("subscribe_select_sign", lang),
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_unsub")
        async def cb_settings_unsub(callback: CallbackQuery) -> None:
            """Unsubscribe from settings."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("unsubscribe_confirm", lang, sign="", hour=""),
                reply_markup=get_confirm_keyboard("unsubscribe", lang),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "settings_back")
        async def cb_settings_back(callback: CallbackQuery) -> None:
            """Back to main menu from settings."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("main_menu", lang),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML",
            )

        # Confirmation callbacks
        @router.callback_query(F.data == "confirm_unsubscribe")
        async def cb_confirm_unsub(callback: CallbackQuery) -> None:
            """Confirm unsubscribe."""
            lang = callback.from_user.language_code if callback.from_user else None
            if not self._subscriptions:
                return

            await callback.answer()
            await self._subscriptions.unsubscribe(callback.from_user.id)

            await callback.message.edit_text(
                t("unsubscribed", lang),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "confirm_cancel")
        async def cb_confirm_cancel(callback: CallbackQuery) -> None:
            """Cancel confirmation."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer(t("cancelled", lang))

            if not self._subscriptions:
                return

            sub = await self._subscriptions.get_subscription(callback.from_user.id)
            await callback.message.edit_text(
                t("settings_cancelled", lang),
                reply_markup=get_settings_keyboard(sub is not None, lang),
                parse_mode="HTML",
            )

        # Horoscope result callbacks
        @router.callback_query(F.data == "horoscope_other")
        async def cb_horoscope_other(callback: CallbackQuery) -> None:
            """Select another zodiac sign."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("select_sign", lang),
                reply_markup=get_zodiac_keyboard(),
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "horoscope_menu")
        async def cb_horoscope_menu(callback: CallbackQuery) -> None:
            """Back to main menu."""
            lang = callback.from_user.language_code if callback.from_user else None
            await callback.answer()
            await callback.message.edit_text(
                t("main_menu", lang),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML",
            )

    async def _send_horoscope(
        self, message: Message, sign: ZodiacSign, lang: str | None = None
    ) -> None:
        """Send horoscope as a new message."""
        if not self._scheduler:
            await message.answer(t("service_not_ready", lang))
            return

        try:
            processing = await message.answer(t("generating", lang))

            horoscope_msg = await self._scheduler.deliver_now(
                message.from_user.id, sign, lang
            )

            await processing.delete()
            await message.answer(
                horoscope_msg,
                parse_mode="HTML",
                reply_markup=get_horoscope_keyboard(lang),
            )

        except HoroscopeGenerationError as e:
            await message.answer(f"\u274c {e}")

    async def _send_horoscope_edit(
        self, message: Message, sign: ZodiacSign, lang: str | None = None
    ) -> None:
        """Send horoscope by editing existing message."""
        if not self._scheduler:
            await message.edit_text(t("service_not_ready", lang))
            return

        try:
            horoscope_msg = await self._scheduler.deliver_now(0, sign, lang)
            await message.edit_text(
                horoscope_msg,
                parse_mode="HTML",
                reply_markup=get_horoscope_keyboard(lang),
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

        # Set bot commands for each supported language
        for lang in SUPPORTED_LANGUAGES:
            commands = [
                BotCommand(command="start", description=t("cmd_start", lang)),
                BotCommand(command="horoscope", description=t("cmd_horoscope", lang)),
                BotCommand(command="subscribe", description=t("cmd_subscribe", lang)),
                BotCommand(command="unsubscribe", description=t("cmd_unsubscribe", lang)),
                BotCommand(command="settings", description=t("cmd_settings", lang)),
                BotCommand(command="help", description=t("cmd_help", lang)),
            ]
            await bot.set_my_commands(commands, language_code=lang)

        # Set default commands (English) for users without language preference
        default_commands = [
            BotCommand(command="start", description=t("cmd_start", "en")),
            BotCommand(command="horoscope", description=t("cmd_horoscope", "en")),
            BotCommand(command="subscribe", description=t("cmd_subscribe", "en")),
            BotCommand(command="unsubscribe", description=t("cmd_unsubscribe", "en")),
            BotCommand(command="settings", description=t("cmd_settings", "en")),
            BotCommand(command="help", description=t("cmd_help", "en")),
        ]
        await bot.set_my_commands(default_commands)

        logger.info("Horoscope plugin loaded and scheduler started")

    async def on_unload(self, bot: Bot) -> None:
        """Cleanup when plugin is unloaded."""
        if self._scheduler:
            await self._scheduler.stop()

        if self._openai:
            await self._openai.close()

        # Clear bot commands menu
        await bot.delete_my_commands()

        logger.info("Horoscope plugin unloaded")
