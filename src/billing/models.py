"""SQLAlchemy models for the token billing system."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import Base


class UserToken(Base):
    """Token balance for a user on a specific bot."""

    __tablename__ = "user_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_purchased: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_user_tokens_telegram_bot", "telegram_id", "bot_id", unique=True),
        Index("ix_user_tokens_bot_id", "bot_id"),
    )

    def __repr__(self) -> str:
        return f"<UserToken(telegram_id={self.telegram_id!r}, bot={self.bot_id!r}, balance={self.balance!r})>"


class TokenTransaction(Base):
    """Transaction history for token operations."""

    __tablename__ = "token_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    transaction_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # purchase, consume, grant, refund
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Positive=credit, negative=debit
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # payment, action, welcome
    reference_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )  # Payment ID, action name
    stars_paid: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # For purchases
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_token_transactions_user_bot", "telegram_id", "bot_id"),
        Index("ix_token_transactions_created", "created_at"),
        Index("ix_token_transactions_type", "transaction_type"),
    )

    def __repr__(self) -> str:
        return f"<TokenTransaction(id={self.id!r}, type={self.transaction_type!r}, amount={self.amount!r})>"
