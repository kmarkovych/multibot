"""Billing plugin for token management and Telegram Stars purchases."""

from __future__ import annotations

import json
import logging
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
                label=p["label"],
                description=p.get("description", ""),
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
        logger.info(f"Billing plugin loaded for bot {self.bot_id}")

    def setup_handlers(self, router: Router) -> None:
        """Register billing-related handlers."""

        @router.message(Command("tokens"))
        async def cmd_tokens(message: Message) -> None:
            """Show token balance and purchase option."""
            user = message.from_user
            if not user:
                return

            stats = await self.token_manager.get_stats(user.id)
            balance = stats["balance"]
            total_purchased = stats["total_purchased"]
            total_consumed = stats["total_consumed"]

            # Build keyboard
            buttons = []
            packages = self.token_manager.get_all_packages()
            if packages:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="🛒 Buy Tokens",
                            callback_data="billing:buy_menu",
                        )
                    ]
                )

            buttons.append(
                [
                    InlineKeyboardButton(
                        text="📜 History",
                        callback_data="billing:history",
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            text = (
                f"💰 **Your Token Balance**\n\n"
                f"Balance: **{balance}** tokens\n"
                f"Total purchased: {total_purchased}\n"
                f"Total used: {total_consumed}\n"
            )

            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

        @router.message(Command("buy"))
        async def cmd_buy(message: Message) -> None:
            """Show available token packages."""
            await self._show_packages(message)

        @router.callback_query(F.data == "billing:buy_menu")
        async def callback_buy_menu(callback: CallbackQuery) -> None:
            """Show package selection menu."""
            if callback.message:
                await self._show_packages(callback.message, edit=True)
            await callback.answer()

        @router.callback_query(F.data == "billing:history")
        async def callback_history(callback: CallbackQuery) -> None:
            """Show transaction history."""
            user = callback.from_user
            if not user:
                await callback.answer()
                return

            history = await self.token_manager.get_history(user.id, limit=10)

            if not history:
                text = "📜 No transactions yet."
            else:
                lines = ["📜 **Recent Transactions**\n"]
                for tx in history:
                    amount_str = f"+{tx['amount']}" if tx["amount"] > 0 else str(tx["amount"])
                    emoji = "✅" if tx["amount"] > 0 else "📤"
                    ref = tx.get("reference_id", tx["type"])
                    lines.append(f"{emoji} {amount_str} tokens - {ref}")
                text = "\n".join(lines)

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Back",
                            callback_data="billing:back_to_balance",
                        )
                    ]
                ]
            )

            if callback.message:
                await callback.message.edit_text(
                    text, reply_markup=keyboard, parse_mode="Markdown"
                )
            await callback.answer()

        @router.callback_query(F.data == "billing:back_to_balance")
        async def callback_back_to_balance(callback: CallbackQuery) -> None:
            """Return to balance view."""
            user = callback.from_user
            if not user or not callback.message:
                await callback.answer()
                return

            stats = await self.token_manager.get_stats(user.id)
            balance = stats["balance"]
            total_purchased = stats["total_purchased"]
            total_consumed = stats["total_consumed"]

            buttons = []
            packages = self.token_manager.get_all_packages()
            if packages:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="🛒 Buy Tokens",
                            callback_data="billing:buy_menu",
                        )
                    ]
                )

            buttons.append(
                [
                    InlineKeyboardButton(
                        text="📜 History",
                        callback_data="billing:history",
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            text = (
                f"💰 **Your Token Balance**\n\n"
                f"Balance: **{balance}** tokens\n"
                f"Total purchased: {total_purchased}\n"
                f"Total used: {total_consumed}\n"
            )

            await callback.message.edit_text(
                text, reply_markup=keyboard, parse_mode="Markdown"
            )
            await callback.answer()

        @router.callback_query(F.data.startswith("billing:purchase:"))
        async def callback_purchase(callback: CallbackQuery, bot: Bot) -> None:
            """Initiate a token purchase."""
            user = callback.from_user
            if not user:
                await callback.answer("Error: User not found", show_alert=True)
                return

            package_id = callback.data.split(":", 2)[2] if callback.data else ""
            package = self.token_manager.get_package(package_id)

            if not package:
                await callback.answer("Package not found", show_alert=True)
                return

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
                title=package.label,
                description=package.description or f"Get {package.tokens} tokens",
                payload=payload,
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # XTR = Telegram Stars
                prices=[LabeledPrice(label=package.label, amount=package.stars)],
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

                await message.answer(
                    f"✅ **Payment Successful!**\n\n"
                    f"You received **{package.tokens}** tokens.\n"
                    f"New balance: **{new_balance}** tokens.\n\n"
                    f"Thank you for your purchase! 🎉",
                    parse_mode="Markdown",
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

    async def _show_packages(self, message: Message, edit: bool = False) -> None:
        """Display available token packages."""
        packages = self.token_manager.get_all_packages()

        if not packages:
            text = "No token packages available at this time."
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

        buttons = []
        lines = ["🛒 **Available Token Packages**\n"]

        for package in packages:
            lines.append(
                f"• **{package.label}** - {package.stars} ⭐\n"
                f"  {package.description or f'Get {package.tokens} tokens'}"
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{package.label} ({package.stars} ⭐)",
                        callback_data=f"billing:purchase:{package.id}",
                    )
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="billing:back_to_balance",
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        text = "\n".join(lines)

        if edit:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# Export for auto-discovery
plugin = BillingPlugin
