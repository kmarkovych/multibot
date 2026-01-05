"""SQLAlchemy ORM models for the multibot system."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class BotRecord(Base):
    """Persistent record of bot configurations and state."""

    __tablename__ = "bots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="polling")
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
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
    last_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    users: Mapped[list["BotUser"]] = relationship(
        "BotUser",
        back_populates="bot",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["BotEvent"]] = relationship(
        "BotEvent",
        back_populates="bot",
        cascade="all, delete-orphan",
    )
    plugin_states: Mapped[list["PluginState"]] = relationship(
        "PluginState",
        back_populates="bot",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BotRecord(id={self.id!r}, name={self.name!r})>"


class BotUser(Base):
    """Users who have interacted with bots."""

    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bot_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_bot_users_telegram_bot", "telegram_id", "bot_id", unique=True),
        Index("ix_bot_users_bot_id", "bot_id"),
    )

    # Relationships
    bot: Mapped["BotRecord"] = relationship("BotRecord", back_populates="users")

    def __repr__(self) -> str:
        return f"<BotUser(id={self.id!r}, telegram_id={self.telegram_id!r})>"


class BotEvent(Base):
    """Audit log of bot events (start, stop, errors)."""

    __tablename__ = "bot_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_bot_events_bot_created", "bot_id", "created_at"),
        Index("ix_bot_events_type", "event_type"),
    )

    # Relationships
    bot: Mapped["BotRecord"] = relationship("BotRecord", back_populates="events")

    def __repr__(self) -> str:
        return f"<BotEvent(id={self.id!r}, type={self.event_type!r})>"


class PluginState(Base):
    """Persistent state for plugins."""

    __tablename__ = "plugin_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
    )
    plugin_name: Mapped[str] = mapped_column(String(128), nullable=False)
    state_key: Mapped[str] = mapped_column(String(255), nullable=False)
    state_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_plugin_states_unique",
            "bot_id",
            "plugin_name",
            "state_key",
            unique=True,
        ),
    )

    # Relationships
    bot: Mapped["BotRecord"] = relationship("BotRecord", back_populates="plugin_states")

    def __repr__(self) -> str:
        return f"<PluginState(plugin={self.plugin_name!r}, key={self.state_key!r})>"
