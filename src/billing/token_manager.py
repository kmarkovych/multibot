"""Token management service for billing operations."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.billing.exceptions import InsufficientTokensError
from src.billing.repository import TokenRepository, TransactionRepository

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class TokenPackage:
    """Token package configuration."""

    id: str
    stars: int
    tokens: int
    label: str
    description: str = ""
    # Optional translation keys (used instead of label/description when translator provided)
    label_key: str | None = None
    description_key: str | None = None


class TokenManager:
    """
    High-level service for token operations.

    Handles token initialization, consumption, purchases, and balance queries.
    """

    def __init__(
        self,
        db: DatabaseManager,
        bot_id: str,
        free_tokens: int = 50,
        action_costs: dict[str, int] | None = None,
        packages: list[TokenPackage] | None = None,
    ):
        self.db = db
        self.bot_id = bot_id
        self.free_tokens = free_tokens
        self.action_costs = action_costs or {}
        self.packages = {p.id: p for p in (packages or [])}

    async def ensure_initialized(
        self,
        telegram_id: int,
    ) -> tuple[int, bool]:
        """
        Ensure user has a token balance initialized.

        Returns:
            Tuple of (current_balance, is_new_user)
        """
        async with self.db.session() as session:
            token_repo = TokenRepository(session)
            tx_repo = TransactionRepository(session)

            user_token, is_new = await token_repo.get_or_create_balance(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                free_tokens=self.free_tokens,
            )

            if is_new and self.free_tokens > 0:
                # Log the welcome bonus transaction
                await tx_repo.log_transaction(
                    telegram_id=telegram_id,
                    bot_id=self.bot_id,
                    transaction_type="grant",
                    amount=self.free_tokens,
                    balance_after=self.free_tokens,
                    reference_type="welcome",
                    reference_id="initial_bonus",
                )
                logger.info(
                    f"Initialized user {telegram_id} with {self.free_tokens} free tokens"
                )

            return user_token.balance, is_new

    async def get_balance(self, telegram_id: int) -> int:
        """Get current token balance for a user."""
        async with self.db.session() as session:
            repo = TokenRepository(session)
            balance = await repo.get_balance(telegram_id, self.bot_id)
            return balance if balance is not None else 0

    async def can_afford(self, telegram_id: int, cost: int) -> bool:
        """Check if user can afford a specific cost."""
        balance = await self.get_balance(telegram_id)
        return balance >= cost

    async def get_action_cost(self, action: str) -> int:
        """Get the cost for a specific action."""
        return self.action_costs.get(action, 0)

    async def consume(
        self,
        telegram_id: int,
        cost: int,
        action: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Consume tokens for an action.

        Args:
            telegram_id: User's Telegram ID
            cost: Number of tokens to consume
            action: Name of the action consuming tokens
            metadata: Optional additional data to log

        Returns:
            New balance after consumption

        Raises:
            InsufficientTokensError: If user doesn't have enough tokens
        """
        async with self.db.session() as session:
            token_repo = TokenRepository(session)
            tx_repo = TransactionRepository(session)

            # Try to consume atomically
            new_balance = await token_repo.consume_tokens(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                amount=cost,
            )

            if new_balance is None:
                # Get current balance for error message
                current_balance = await token_repo.get_balance(telegram_id, self.bot_id)
                raise InsufficientTokensError(
                    required=cost,
                    available=current_balance or 0,
                    action=action,
                )

            # Log the transaction
            await tx_repo.log_transaction(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                transaction_type="consume",
                amount=-cost,
                balance_after=new_balance,
                reference_type="action",
                reference_id=action,
                metadata=metadata,
            )

            logger.info(
                f"User {telegram_id} consumed {cost} tokens for '{action}', "
                f"balance: {new_balance}"
            )
            return new_balance

    async def purchase(
        self,
        telegram_id: int,
        package_id: str,
        stars_paid: int,
        payment_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Credit tokens from a purchase.

        Args:
            telegram_id: User's Telegram ID
            package_id: ID of the purchased package
            stars_paid: Number of Telegram Stars paid
            payment_id: Telegram payment ID
            metadata: Optional additional data

        Returns:
            New balance after purchase

        Raises:
            ValueError: If package not found or tokens amount invalid
        """
        package = self.packages.get(package_id)
        if not package:
            raise ValueError(f"Unknown package: {package_id}")

        tokens = package.tokens

        async with self.db.session() as session:
            token_repo = TokenRepository(session)
            tx_repo = TransactionRepository(session)

            # Ensure user exists (shouldn't happen but be safe)
            await token_repo.get_or_create_balance(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                free_tokens=0,
            )

            # Credit the tokens
            new_balance = await token_repo.credit_tokens(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                amount=tokens,
                is_purchase=True,
            )

            if new_balance is None:
                raise ValueError("Failed to credit tokens")

            # Log the transaction
            tx_metadata = {
                "package_id": package_id,
                "package_label": package.label,
                **(metadata or {}),
            }
            await tx_repo.log_transaction(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                transaction_type="purchase",
                amount=tokens,
                balance_after=new_balance,
                reference_type="payment",
                reference_id=payment_id,
                stars_paid=stars_paid,
                metadata=tx_metadata,
            )

            logger.info(
                f"User {telegram_id} purchased {tokens} tokens for {stars_paid} stars, "
                f"balance: {new_balance}"
            )
            return new_balance

    async def grant(
        self,
        telegram_id: int,
        amount: int,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Grant tokens to a user (admin/promotional).

        Args:
            telegram_id: User's Telegram ID
            amount: Number of tokens to grant
            reason: Reason for the grant
            metadata: Optional additional data

        Returns:
            New balance after grant
        """
        async with self.db.session() as session:
            token_repo = TokenRepository(session)
            tx_repo = TransactionRepository(session)

            # Ensure user exists
            await token_repo.get_or_create_balance(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                free_tokens=0,
            )

            # Credit the tokens (not marked as purchase)
            new_balance = await token_repo.credit_tokens(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                amount=amount,
                is_purchase=False,
            )

            if new_balance is None:
                raise ValueError("Failed to grant tokens")

            # Log the transaction
            await tx_repo.log_transaction(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                transaction_type="grant",
                amount=amount,
                balance_after=new_balance,
                reference_type="admin",
                reference_id=reason,
                metadata=metadata,
            )

            logger.info(
                f"Granted {amount} tokens to user {telegram_id}: {reason}, "
                f"balance: {new_balance}"
            )
            return new_balance

    async def get_stats(self, telegram_id: int) -> dict[str, int]:
        """Get user token statistics."""
        async with self.db.session() as session:
            repo = TokenRepository(session)
            stats = await repo.get_user_stats(telegram_id, self.bot_id)
            return stats or {"balance": 0, "total_purchased": 0, "total_consumed": 0}

    async def get_history(
        self,
        telegram_id: int,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get user transaction history."""
        async with self.db.session() as session:
            repo = TransactionRepository(session)
            transactions = await repo.get_user_history(
                telegram_id=telegram_id,
                bot_id=self.bot_id,
                limit=limit,
            )
            return [
                {
                    "id": tx.id,
                    "type": tx.transaction_type,
                    "amount": tx.amount,
                    "balance_after": tx.balance_after,
                    "reference_type": tx.reference_type,
                    "reference_id": tx.reference_id,
                    "stars_paid": tx.stars_paid,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                }
                for tx in transactions
            ]

    def get_package(self, package_id: str) -> TokenPackage | None:
        """Get a package by ID."""
        return self.packages.get(package_id)

    def get_all_packages(self) -> list[TokenPackage]:
        """Get all available packages."""
        return list(self.packages.values())
