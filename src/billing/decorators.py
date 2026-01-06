"""Decorators for token-gated handlers."""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar

from aiogram.types import CallbackQuery, Message

from src.billing.exceptions import InsufficientTokensError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def requires_tokens(
    cost: int,
    action: str,
    *,
    on_insufficient: Callable[
        [Message | CallbackQuery, int, int], Awaitable[Any]
    ]
    | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T | None]]]:
    """
    Decorator that requires tokens before executing a handler.

    Automatically consumes the specified tokens if the user has sufficient balance.
    If insufficient, either calls the on_insufficient callback or sends a default message.

    Args:
        cost: Number of tokens required for this action
        action: Name of the action (for logging and transactions)
        on_insufficient: Optional callback for custom insufficient tokens handling.
                        Receives (event, required, available) and should handle the response.

    Example:
        @router.message(Command("premium"))
        @requires_tokens(cost=10, action="premium_feature")
        async def cmd_premium(message: Message, token_manager: TokenManager):
            # Tokens already consumed if we get here
            await message.answer("Premium feature executed!")

        # With custom insufficient handler:
        async def show_buy_prompt(event, required, available):
            await event.answer(f"Need {required} tokens! You have {available}. /buy to get more!")

        @requires_tokens(cost=5, action="generate", on_insufficient=show_buy_prompt)
        async def cmd_generate(message: Message):
            ...
    """

    def decorator(
        func: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T | None]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            # Find the event (Message or CallbackQuery) from args
            event: Message | CallbackQuery | None = None
            for arg in args:
                if isinstance(arg, (Message, CallbackQuery)):
                    event = arg
                    break

            if event is None:
                # No event found - can't check tokens
                logger.warning(
                    f"requires_tokens: No event found for handler {func.__name__}"
                )
                return await func(*args, **kwargs)

            # Get token_manager from kwargs (injected by middleware)
            token_manager = kwargs.get("token_manager")
            if token_manager is None:
                logger.warning(
                    f"requires_tokens: No token_manager in context for {func.__name__}"
                )
                return await func(*args, **kwargs)

            # Get user ID
            user = event.from_user
            if not user:
                logger.warning(f"requires_tokens: No user for {func.__name__}")
                return await func(*args, **kwargs)

            # Try to consume tokens
            try:
                await token_manager.consume(
                    telegram_id=user.id,
                    cost=cost,
                    action=action,
                )
            except InsufficientTokensError as e:
                logger.info(
                    f"User {user.id} has insufficient tokens for {action}: "
                    f"need {e.required}, have {e.available}"
                )

                if on_insufficient:
                    await on_insufficient(event, e.required, e.available)
                else:
                    # Default insufficient tokens message
                    msg = (
                        f"⚠️ Insufficient tokens!\n\n"
                        f"This action requires {e.required} tokens.\n"
                        f"Your balance: {e.available} tokens.\n\n"
                        f"Use /tokens to check your balance or purchase more."
                    )
                    if isinstance(event, Message):
                        await event.answer(msg)
                    else:
                        await event.answer(msg, show_alert=True)

                return None

            # Tokens consumed successfully - execute the handler
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def check_tokens(
    cost: int,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T | None]]]:
    """
    Decorator that checks token balance without consuming.

    Useful for handlers that need to verify balance before showing options.

    Args:
        cost: Minimum token balance required

    Example:
        @router.message(Command("premium_menu"))
        @check_tokens(cost=1)
        async def cmd_premium_menu(message: Message, token_balance: int):
            # Only shown if user has at least 1 token
            await message.answer("Premium options: ...")
    """

    def decorator(
        func: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T | None]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            # Get token_balance from kwargs (injected by middleware)
            token_balance = kwargs.get("token_balance", 0)

            if token_balance < cost:
                # Find the event to send a message
                event: Message | CallbackQuery | None = None
                for arg in args:
                    if isinstance(arg, (Message, CallbackQuery)):
                        event = arg
                        break

                if event:
                    msg = (
                        f"⚠️ You need at least {cost} tokens to access this feature.\n"
                        f"Your balance: {token_balance} tokens.\n\n"
                        f"Use /tokens to purchase more."
                    )
                    if isinstance(event, Message):
                        await event.answer(msg)
                    else:
                        await event.answer(msg, show_alert=True)

                return None

            return await func(*args, **kwargs)

        return wrapper

    return decorator
