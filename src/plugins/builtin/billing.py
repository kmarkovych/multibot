"""Billing plugin for token management and Telegram Stars purchases."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from src.billing.token_manager import TokenManager, TokenPackage
from src.plugins.base import BasePlugin

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type alias for translator function: (key, lang, **kwargs) -> str
TranslatorFunc = Callable[..., str]

# Global registry for translators per bot_id
# This allows other plugins to register their translators for billing to use
_translator_registry: dict[str, TranslatorFunc] = {}


def register_translator(bot_id: str, translator: TranslatorFunc) -> None:
    """Register a translator function for a bot."""
    _translator_registry[bot_id] = translator
    logger.debug(f"Registered translator for bot {bot_id}")


def get_registered_translator(bot_id: str) -> TranslatorFunc | None:
    """Get registered translator for a bot."""
    return _translator_registry.get(bot_id)


class BillingPlugin(BasePlugin):
    """
    Handles token balance display and Telegram Stars purchases.

    Configuration:
        free_tokens: int - Tokens granted to new users (default: 50)
        action_costs: dict - Cost per action (e.g., {"generate": 5})
        packages: list - Available token packages
            - id: str
            - stars: int
            - tokens: int
            - label: str
            - description: str (optional)

    Example config:
        plugins:
          - name: billing
            enabled: true
            config:
              free_tokens: 50
              action_costs:
                generate_horoscope: 1
              packages:
                - id: small
                  stars: 50
                  tokens: 100
                  label: "100 Tokens"
                - id: medium
                  stars: 200
                  tokens: 500
                  label: "500 Tokens (+100 bonus)"
    """

    name = "billing"
    description = "Token balance and Telegram Stars purchases"
    version = "1.0.0"
    author = "Multibot System"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._token_manager: TokenManager | None = None
        self._translator: TranslatorFunc | None = None

    def set_translator(self, translator: TranslatorFunc) -> None:
        """Set the translator function for i18n support."""
        self._translator = translator

    def _get_translator(self) -> TranslatorFunc | None:
        """Get translator, checking registry if not set (for late registration)."""
        if self._translator:
            return self._translator
        # Check registry in case it was registered after our on_load
        registered = get_registered_translator(self.bot_id)
        if registered:
            self._translator = registered
        return self._translator

    def _translate(
        self, key: str, lang: str | None = None, default: str | None = None, **kwargs: Any
    ) -> str:
        """Translate a key, falling back to default if no translator or key not found."""
        translator = self._get_translator()
        if translator:
            result = translator(key, lang, **kwargs)
            # If translator returns the key itself, it means key wasn't found
            if result != key:
                return result
        return default or key

    def _get_package_label(self, package: TokenPackage, lang: str | None = None) -> str:
        """Get translated package label."""
        translator = self._get_translator()
        if package.label_key and translator:
            translated = translator(package.label_key, lang)
            if translated != package.label_key:
                return translated
        # Fallback to label, or generate one from tokens
        return package.label or f"{package.tokens} Tokens"

    def _get_package_description(self, package: TokenPackage, lang: str | None = None) -> str:
        """Get translated package description."""
        translator = self._get_translator()
        if package.description_key and translator:
            translated = translator(package.description_key, lang)
            if translated != package.description_key:
                return translated
        return package.description or f"Get {package.tokens} tokens"

    def _build_token_manager(self) -> TokenManager:
        """Build TokenManager from config."""
        free_tokens = self.get_config("free_tokens", 50)
        action_costs = self.get_config("action_costs", {})

        # Parse packages from config
        packages_config = self.get_config("packages", [])
        packages = [
            TokenPackage(
                id=p["id"],
                stars=p["stars"],
                tokens=p["tokens"],
                label=p.get("label", ""),
                description=p.get("description", ""),
                label_key=p.get("label_key"),
                description_key=p.get("description_key"),
            )
            for p in packages_config
        ]

        return TokenManager(
            db=self.db,
            bot_id=self.bot_id,
            free_tokens=free_tokens,
            action_costs=action_costs,
            packages=packages,
        )

    @property
    def token_manager(self) -> TokenManager:
        """Get the token manager, creating it if needed."""
        if self._token_manager is None:
            self._token_manager = self._build_token_manager()
        return self._token_manager

    async def on_load(self, bot: Bot) -> None:
        """Initialize token manager on load."""
        self._token_manager = self._build_token_manager()

        # Check for registered translator
        registered = get_registered_translator(self.bot_id)
        if registered:
            self._translator = registered
            logger.debug(f"Using registered translator for bot {self.bot_id}")

        logger.info(f"Billing plugin loaded for bot {self.bot_id}")

    def _get_user_lang(self, user: Any) -> str | None:
        """Extract language code from user object."""
        if user and hasattr(user, "language_code"):
            return user.language_code
        return None

    def setup_handlers(self, router: Router) -> None:
        """Register billing-related handlers."""

        @router.message(Command("tokens"))
        async def cmd_tokens(message: Message) -> None:
            """Show token balance and purchase option."""
            user = message.from_user
            if not user:
                return

            lang = self._get_user_lang(user)
            stats = await self.token_manager.get_stats(user.id)
            balance = stats["balance"]
            total_purchased = stats["total_purchased"]
            total_consumed = stats["total_consumed"]

            # Build keyboard
            buttons = []
            packages = self.token_manager.get_all_packages()
            if packages:
                buy_text = self._translate(
                    "billing_buy_tokens", lang, default="Buy Tokens"
                )
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"🛒 {buy_text}",
                            callback_data="billing:buy_menu",
                        )
                    ]
                )

            history_text = self._translate("billing_history", lang, default="History")
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"📜 {history_text}",
                        callback_data="billing:history",
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            title = self._translate(
                "billing_balance_title", lang, default="Your Token Balance"
            )
            balance_line = self._translate(
                "billing_balance", lang, default=f"Balance: <b>{balance}</b> tokens", balance=balance
            )
            purchased_line = self._translate(
                "billing_total_purchased", lang, default=f"Total purchased: {total_purchased}", total=total_purchased
            )
            used_line = self._translate(
                "billing_total_used", lang, default=f"Total used: {total_consumed}", total=total_consumed
            )

            text = f"💰 <b>{title}</b>\n\n{balance_line}\n{purchased_line}\n{used_line}\n"

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

        @router.message(Command("buy"))
        async def cmd_buy(message: Message) -> None:
            """Show available token packages."""
            lang = self._get_user_lang(message.from_user)
            await self._show_packages(message, lang=lang)

        @router.callback_query(F.data == "billing:balance")
        async def callback_balance(callback: CallbackQuery) -> None:
            """Show token balance view."""
            user = callback.from_user
            if not user or not callback.message:
                await callback.answer()
                return

            lang = self._get_user_lang(user)
            stats = await self.token_manager.get_stats(user.id)
            balance = stats["balance"]
            total_purchased = stats["total_purchased"]
            total_consumed = stats["total_consumed"]

            # Build keyboard
            buttons = []
            packages = self.token_manager.get_all_packages()
            if packages:
                buy_text = self._translate(
                    "billing_buy_tokens", lang, default="Buy Tokens"
                )
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"🛒 {buy_text}",
                            callback_data="billing:buy_menu",
                        )
                    ]
                )

            history_text = self._translate("billing_history", lang, default="History")
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"📜 {history_text}",
                        callback_data="billing:history",
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            title = self._translate(
                "billing_balance_title", lang, default="Your Token Balance"
            )
            balance_line = self._translate(
                "billing_balance", lang, default=f"Balance: <b>{balance}</b> tokens", balance=balance
            )
            purchased_line = self._translate(
                "billing_total_purchased", lang, default=f"Total purchased: {total_purchased}", total=total_purchased
            )
            used_line = self._translate(
                "billing_total_used", lang, default=f"Total used: {total_consumed}", total=total_consumed
            )

            text = f"💰 <b>{title}</b>\n\n{balance_line}\n{purchased_line}\n{used_line}\n"

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()

        @router.callback_query(F.data == "billing:buy_menu")
        async def callback_buy_menu(callback: CallbackQuery) -> None:
            """Show package selection menu."""
            lang = self._get_user_lang(callback.from_user)
            if callback.message:
                await self._show_packages(callback.message, edit=True, lang=lang)
            await callback.answer()

        @router.callback_query(F.data == "billing:history")
        async def callback_history(callback: CallbackQuery) -> None:
            """Show transaction history."""
            user = callback.from_user
            if not user:
                await callback.answer()
                return

            lang = self._get_user_lang(user)
            history = await self.token_manager.get_history(user.id, limit=10)

            if not history:
                text = "📜 " + self._translate(
                    "billing_no_history", lang, default="No transactions yet."
                )
            else:
                title = self._translate(
                    "billing_history_title", lang, default="Recent Transactions"
                )
                lines = [f"📜 <b>{title}</b>\n"]
                for tx in history:
                    amount_str = f"+{tx['amount']}" if tx["amount"] > 0 else str(tx["amount"])
                    emoji = "✅" if tx["amount"] > 0 else "📤"
                    ref = tx.get("reference_id", tx["type"])
                    lines.append(f"{emoji} {amount_str} tokens - {ref}")
                text = "\n".join(lines)

            back_text = self._translate("billing_back", lang, default="Back")
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"⬅️ {back_text}",
                            callback_data="billing:back_to_balance",
                        )
                    ]
                ]
            )

            if callback.message:
                await callback.message.edit_text(
                    text, reply_markup=keyboard, parse_mode="HTML"
                )
            await callback.answer()

        @router.callback_query(F.data == "billing:back_to_balance")
        async def callback_back_to_balance(callback: CallbackQuery) -> None:
            """Return to balance view."""
            user = callback.from_user
            if not user or not callback.message:
                await callback.answer()
                return

            lang = self._get_user_lang(user)
            stats = await self.token_manager.get_stats(user.id)
            balance = stats["balance"]
            total_purchased = stats["total_purchased"]
            total_consumed = stats["total_consumed"]

            buttons = []
            packages = self.token_manager.get_all_packages()
            if packages:
                buy_text = self._translate(
                    "billing_buy_tokens", lang, default="Buy Tokens"
                )
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"🛒 {buy_text}",
                            callback_data="billing:buy_menu",
                        )
                    ]
                )

            history_text = self._translate("billing_history", lang, default="History")
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"📜 {history_text}",
                        callback_data="billing:history",
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            title = self._translate(
                "billing_balance_title", lang, default="Your Token Balance"
            )
            balance_line = self._translate(
                "billing_balance", lang, default=f"Balance: <b>{balance}</b> tokens", balance=balance
            )
            purchased_line = self._translate(
                "billing_total_purchased", lang, default=f"Total purchased: {total_purchased}", total=total_purchased
            )
            used_line = self._translate(
                "billing_total_used", lang, default=f"Total used: {total_consumed}", total=total_consumed
            )

            text = f"💰 <b>{title}</b>\n\n{balance_line}\n{purchased_line}\n{used_line}\n"

            await callback.message.edit_text(
                text, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer()

        @router.callback_query(F.data.startswith("billing:purchase:"))
        async def callback_purchase(callback: CallbackQuery, bot: Bot) -> None:
            """Initiate a token purchase."""
            user = callback.from_user
            if not user:
                await callback.answer("Error: User not found", show_alert=True)
                return

            lang = self._get_user_lang(user)
            package_id = callback.data.split(":", 2)[2] if callback.data else ""
            package = self.token_manager.get_package(package_id)

            if not package:
                await callback.answer("Package not found", show_alert=True)
                return

            # Get translated label and description
            label = self._get_package_label(package, lang)
            description = self._get_package_description(package, lang)

            # Create invoice payload
            payload = json.dumps(
                {
                    "package_id": package_id,
                    "user_id": user.id,
                    "bot_id": self.bot_id,
                }
            )

            # Send invoice using Telegram Stars
            await bot.send_invoice(
                chat_id=user.id,
                title=label,
                description=description,
                payload=payload,
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # XTR = Telegram Stars
                prices=[LabeledPrice(label=label, amount=package.stars)],
            )

            await callback.answer()

        @router.pre_checkout_query()
        async def handle_pre_checkout(pre_checkout: PreCheckoutQuery) -> None:
            """Validate purchase before processing."""
            try:
                payload = json.loads(pre_checkout.invoice_payload)
                package_id = payload.get("package_id")
                package = self.token_manager.get_package(package_id)

                if not package:
                    await pre_checkout.answer(
                        ok=False,
                        error_message="Invalid package. Please try again.",
                    )
                    return

                # Validate the price matches
                if pre_checkout.total_amount != package.stars:
                    await pre_checkout.answer(
                        ok=False,
                        error_message="Price mismatch. Please try again.",
                    )
                    return

                await pre_checkout.answer(ok=True)

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Invalid checkout payload: {e}")
                await pre_checkout.answer(
                    ok=False,
                    error_message="Invalid purchase data. Please try again.",
                )

        @router.message(F.successful_payment)
        async def handle_successful_payment(message: Message) -> None:
            """Process successful payment and credit tokens."""
            payment = message.successful_payment
            user = message.from_user

            if not payment or not user:
                return

            lang = self._get_user_lang(user)

            try:
                payload = json.loads(payment.invoice_payload)
                package_id = payload.get("package_id")
                package = self.token_manager.get_package(package_id)

                if not package:
                    logger.error(f"Unknown package in payment: {package_id}")
                    await message.answer(
                        "⚠️ Error processing payment. Please contact support."
                    )
                    return

                # Credit tokens
                new_balance = await self.token_manager.purchase(
                    telegram_id=user.id,
                    package_id=package_id,
                    stars_paid=payment.total_amount,
                    payment_id=payment.telegram_payment_charge_id,
                    metadata={"provider_charge_id": payment.provider_payment_charge_id},
                )

                success_title = self._translate(
                    "billing_payment_success", lang, default="Payment Successful!"
                )
                received_text = self._translate(
                    "billing_payment_received", lang,
                    default=f"You received <b>{package.tokens}</b> tokens.",
                    tokens=package.tokens
                )
                balance_text = self._translate(
                    "billing_new_balance", lang,
                    default=f"New balance: <b>{new_balance}</b> tokens.",
                    balance=new_balance
                )
                thank_you = self._translate(
                    "billing_thank_you", lang, default="Thank you for your purchase!"
                )

                await message.answer(
                    f"✅ <b>{success_title}</b>\n\n"
                    f"{received_text}\n"
                    f"{balance_text}\n\n"
                    f"{thank_you} 🎉",
                    parse_mode="HTML",
                )

                logger.info(
                    f"User {user.id} purchased {package.tokens} tokens "
                    f"for {payment.total_amount} stars"
                )

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing payment: {e}")
                await message.answer(
                    "⚠️ Error processing payment. Please contact support with your "
                    f"payment ID: {payment.telegram_payment_charge_id}"
                )

    async def _show_packages(
        self, message: Message, edit: bool = False, lang: str | None = None
    ) -> None:
        """Display available token packages."""
        packages = self.token_manager.get_all_packages()

        if not packages:
            text = self._translate(
                "billing_no_packages", lang,
                default="No token packages available at this time."
            )
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

        buttons = []
        title = self._translate(
            "billing_packages_title", lang, default="Available Token Packages"
        )
        lines = [f"🛒 <b>{title}</b>\n"]

        for package in packages:
            label = self._get_package_label(package, lang)
            description = self._get_package_description(package, lang)
            lines.append(
                f"• <b>{label}</b> - {package.stars} ⭐\n"
                f"  {description}"
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{label} ({package.stars} ⭐)",
                        callback_data=f"billing:purchase:{package.id}",
                    )
                ]
            )

        back_text = self._translate("billing_back", lang, default="Back")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"⬅️ {back_text}",
                    callback_data="billing:back_to_balance",
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        text = "\n".join(lines)

        if edit:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Export for auto-discovery
plugin = BillingPlugin
