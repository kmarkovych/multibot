"""Repository for bot-related database operations."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from sqlalchemy import select

from src.database.models import BotEvent, BotRecord, BotUser, PluginState
from src.database.repositories.base import BaseRepository


class BotRepository(BaseRepository[BotRecord]):
    """Repository for BotRecord operations."""

    model = BotRecord

    async def get_by_id(self, bot_id: str) -> BotRecord | None:
        """Get a bot record by ID."""
        return await self.session.get(BotRecord, bot_id)

    async def get_enabled_bots(self) -> list[BotRecord]:
        """Get all enabled bot records."""
        query = select(BotRecord).where(BotRecord.is_enabled.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_bot(
        self,
        bot_id: str,
        name: str,
        token: str,
        mode: str = "polling",
        is_enabled: bool = True,
        config_json: dict[str, Any] | None = None,
    ) -> BotRecord:
        """Create or update a bot record."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]

        bot = await self.get_by_id(bot_id)
        if bot:
            bot.name = name
            bot.token_hash = token_hash
            bot.mode = mode
            bot.is_enabled = is_enabled
            if config_json:
                bot.config_json = config_json
        else:
            bot = BotRecord(
                id=bot_id,
                name=name,
                token_hash=token_hash,
                mode=mode,
                is_enabled=is_enabled,
                config_json=config_json,
            )
            self.session.add(bot)

        await self.session.flush()
        return bot

    async def mark_started(self, bot_id: str) -> None:
        """Mark a bot as started."""
        bot = await self.get_by_id(bot_id)
        if bot:
            bot.last_started_at = datetime.utcnow()
            await self.session.flush()

    async def log_event(
        self,
        bot_id: str,
        event_type: str,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BotEvent:
        """Log a bot event."""
        event = BotEvent(
            bot_id=bot_id,
            event_type=event_type,
            message=message,
            metadata_json=metadata,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_recent_events(
        self,
        bot_id: str,
        limit: int = 50,
    ) -> list[BotEvent]:
        """Get recent events for a bot."""
        query = (
            select(BotEvent)
            .where(BotEvent.bot_id == bot_id)
            .order_by(BotEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class UserRepository(BaseRepository[BotUser]):
    """Repository for BotUser operations."""

    model = BotUser

    async def get_or_create(
        self,
        telegram_id: int,
        bot_id: str,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> tuple[BotUser, bool]:
        """Get or create a user record. Returns (user, created)."""
        query = select(BotUser).where(
            BotUser.telegram_id == telegram_id,
            BotUser.bot_id == bot_id,
        )
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            # Update last seen and any changed info
            user.last_seen_at = datetime.utcnow()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if language_code:
                user.language_code = language_code
            await self.session.flush()
            return user, False

        # Create new user
        user = BotUser(
            telegram_id=telegram_id,
            bot_id=bot_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def get_user_count(self, bot_id: str) -> int:
        """Get the total number of users for a bot."""
        from sqlalchemy import func

        query = select(func.count()).select_from(BotUser).where(BotUser.bot_id == bot_id)
        result = await self.session.execute(query)
        return result.scalar() or 0


class PluginStateRepository(BaseRepository[PluginState]):
    """Repository for PluginState operations."""

    model = PluginState

    async def get_state(
        self,
        bot_id: str,
        plugin_name: str,
        state_key: str,
    ) -> dict[str, Any] | None:
        """Get a plugin state value."""
        query = select(PluginState).where(
            PluginState.bot_id == bot_id,
            PluginState.plugin_name == plugin_name,
            PluginState.state_key == state_key,
        )
        result = await self.session.execute(query)
        state = result.scalar_one_or_none()
        return state.state_value if state else None

    async def set_state(
        self,
        bot_id: str,
        plugin_name: str,
        state_key: str,
        state_value: dict[str, Any],
    ) -> PluginState:
        """Set a plugin state value."""
        query = select(PluginState).where(
            PluginState.bot_id == bot_id,
            PluginState.plugin_name == plugin_name,
            PluginState.state_key == state_key,
        )
        result = await self.session.execute(query)
        state = result.scalar_one_or_none()

        if state:
            state.state_value = state_value
        else:
            state = PluginState(
                bot_id=bot_id,
                plugin_name=plugin_name,
                state_key=state_key,
                state_value=state_value,
            )
            self.session.add(state)

        await self.session.flush()
        return state

    async def delete_state(
        self,
        bot_id: str,
        plugin_name: str,
        state_key: str | None = None,
    ) -> int:
        """Delete plugin state(s). If state_key is None, delete all states for the plugin."""
        from sqlalchemy import delete

        conditions = [
            PluginState.bot_id == bot_id,
            PluginState.plugin_name == plugin_name,
        ]
        if state_key:
            conditions.append(PluginState.state_key == state_key)

        query = delete(PluginState).where(*conditions)
        result = await self.session.execute(query)
        return result.rowcount
