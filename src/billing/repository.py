"""Repository for token billing database operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.billing.models import TokenTransaction, UserToken
from src.database.repositories.base import BaseRepository


class TokenRepository(BaseRepository[UserToken]):
    """Repository for UserToken operations."""

    model = UserToken

    async def get_or_create_balance(
        self,
        telegram_id: int,
        bot_id: str,
        free_tokens: int = 0,
    ) -> tuple[UserToken, bool]:
        """Get or create a user token balance. Returns (user_token, is_new)."""
        query = select(UserToken).where(
            UserToken.telegram_id == telegram_id,
            UserToken.bot_id == bot_id,
        )
        result = await self.session.execute(query)
        user_token = result.scalar_one_or_none()

        if user_token:
            return user_token, False

        # Create new user token record with free tokens
        user_token = UserToken(
            telegram_id=telegram_id,
            bot_id=bot_id,
            balance=free_tokens,
        )
        self.session.add(user_token)
        await self.session.flush()
        return user_token, True

    async def get_balance(self, telegram_id: int, bot_id: str) -> int | None:
        """Get current balance for a user. Returns None if user doesn't exist."""
        query = select(UserToken.balance).where(
            UserToken.telegram_id == telegram_id,
            UserToken.bot_id == bot_id,
        )
        result = await self.session.execute(query)
        row = result.scalar_one_or_none()
        return row if row is not None else None

    async def consume_tokens(
        self,
        telegram_id: int,
        bot_id: str,
        amount: int,
    ) -> int | None:
        """
        Atomically consume tokens from user balance.

        Returns the new balance if successful, or None if insufficient funds.
        Uses database-level check to prevent race conditions.
        """
        if amount <= 0:
            raise ValueError("Consume amount must be positive")

        # Atomic update: only succeeds if balance >= amount
        stmt = (
            update(UserToken)
            .where(
                UserToken.telegram_id == telegram_id,
                UserToken.bot_id == bot_id,
                UserToken.balance >= amount,
            )
            .values(
                balance=UserToken.balance - amount,
                total_consumed=UserToken.total_consumed + amount,
            )
            .returning(UserToken.balance)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            # Either user doesn't exist or insufficient balance
            return None

        await self.session.flush()
        return row

    async def credit_tokens(
        self,
        telegram_id: int,
        bot_id: str,
        amount: int,
        is_purchase: bool = False,
    ) -> int | None:
        """
        Credit tokens to user balance.

        Returns the new balance if successful, or None if user doesn't exist.
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        values: dict[str, Any] = {"balance": UserToken.balance + amount}
        if is_purchase:
            values["total_purchased"] = UserToken.total_purchased + amount

        stmt = (
            update(UserToken)
            .where(
                UserToken.telegram_id == telegram_id,
                UserToken.bot_id == bot_id,
            )
            .values(**values)
            .returning(UserToken.balance)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            return None

        await self.session.flush()
        return row

    async def get_user_stats(
        self,
        telegram_id: int,
        bot_id: str,
    ) -> dict[str, int] | None:
        """Get user token statistics."""
        query = select(
            UserToken.balance,
            UserToken.total_purchased,
            UserToken.total_consumed,
        ).where(
            UserToken.telegram_id == telegram_id,
            UserToken.bot_id == bot_id,
        )
        result = await self.session.execute(query)
        row = result.one_or_none()

        if row is None:
            return None

        return {
            "balance": row.balance,
            "total_purchased": row.total_purchased,
            "total_consumed": row.total_consumed,
        }


class TransactionRepository(BaseRepository[TokenTransaction]):
    """Repository for TokenTransaction operations."""

    model = TokenTransaction

    async def log_transaction(
        self,
        telegram_id: int,
        bot_id: str,
        transaction_type: str,
        amount: int,
        balance_after: int,
        reference_type: str | None = None,
        reference_id: str | None = None,
        stars_paid: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TokenTransaction:
        """Log a token transaction."""
        transaction = TokenTransaction(
            telegram_id=telegram_id,
            bot_id=bot_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            stars_paid=stars_paid,
            metadata_json=metadata,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def get_user_history(
        self,
        telegram_id: int,
        bot_id: str,
        limit: int = 50,
    ) -> list[TokenTransaction]:
        """Get recent transaction history for a user."""
        query = (
            select(TokenTransaction)
            .where(
                TokenTransaction.telegram_id == telegram_id,
                TokenTransaction.bot_id == bot_id,
            )
            .order_by(TokenTransaction.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_purchase_total(
        self,
        telegram_id: int,
        bot_id: str,
    ) -> int:
        """Get total stars spent by a user."""
        from sqlalchemy import func

        query = select(func.coalesce(func.sum(TokenTransaction.stars_paid), 0)).where(
            TokenTransaction.telegram_id == telegram_id,
            TokenTransaction.bot_id == bot_id,
            TokenTransaction.transaction_type == "purchase",
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def has_transaction_today(
        self,
        telegram_id: int,
        bot_id: str,
        reference_id: str,
    ) -> bool:
        """Check if user has a consume transaction with this reference_id today."""
        from datetime import date

        from sqlalchemy import func

        today = date.today()
        query = select(func.count()).where(
            TokenTransaction.telegram_id == telegram_id,
            TokenTransaction.bot_id == bot_id,
            TokenTransaction.transaction_type == "consume",
            TokenTransaction.reference_id == reference_id,
            func.date(TokenTransaction.created_at) == today,
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0


class TokenRepositoryFactory:
    """Factory to create token repositories from a session."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._token_repo: TokenRepository | None = None
        self._transaction_repo: TransactionRepository | None = None

    @property
    def tokens(self) -> TokenRepository:
        """Get TokenRepository instance."""
        if self._token_repo is None:
            self._token_repo = TokenRepository(self.session)
        return self._token_repo

    @property
    def transactions(self) -> TransactionRepository:
        """Get TransactionRepository instance."""
        if self._transaction_repo is None:
            self._transaction_repo = TransactionRepository(self.session)
        return self._transaction_repo
