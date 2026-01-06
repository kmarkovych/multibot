"""Subscription management for horoscope delivery."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.database.models import PluginState
from src.database.repositories.bot_repository import PluginStateRepository

from .timezone import DEFAULT_TIMEZONE, local_to_utc
from .zodiac import ZodiacSign

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

PLUGIN_NAME = "horoscope"


@dataclass
class Subscription:
    """User subscription data."""

    telegram_id: int
    zodiac_sign: ZodiacSign
    delivery_hour: int  # Local hour (0-23)
    timezone: str  # Timezone ID (e.g., "Europe/Kyiv")
    is_active: bool
    created_at: datetime | None = None


class SubscriptionManager:
    """Manages user subscriptions for daily horoscope delivery."""

    def __init__(self, db: DatabaseManager, bot_id: str):
        self.db = db
        self.bot_id = bot_id

    def _sub_key(self, telegram_id: int) -> str:
        """Generate subscription key for a user."""
        return f"sub_{telegram_id}"

    async def subscribe(
        self,
        telegram_id: int,
        sign: ZodiacSign,
        delivery_hour: int = 8,
        timezone: str = DEFAULT_TIMEZONE,
    ) -> Subscription:
        """
        Create or update a subscription.

        Args:
            telegram_id: User's Telegram ID
            sign: User's zodiac sign
            delivery_hour: Hour to deliver horoscope (local time, 0-23)
            timezone: User's timezone ID

        Returns:
            The created/updated subscription
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            await repo.set_state(
                self.bot_id,
                PLUGIN_NAME,
                sub_key,
                {
                    "telegram_id": telegram_id,
                    "sign": sign.name,
                    "hour": delivery_hour,
                    "timezone": timezone,
                    "active": True,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            await session.commit()

        logger.info(
            f"User {telegram_id} subscribed: {sign.value} at {delivery_hour}:00 {timezone}"
        )

        return Subscription(
            telegram_id=telegram_id,
            zodiac_sign=sign,
            delivery_hour=delivery_hour,
            timezone=timezone,
            is_active=True,
            created_at=datetime.utcnow(),
        )

    async def unsubscribe(self, telegram_id: int) -> bool:
        """
        Remove a user's subscription.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            True if subscription was removed, False if not found
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            deleted = await repo.delete_state(self.bot_id, PLUGIN_NAME, sub_key)
            await session.commit()

        if deleted > 0:
            logger.info(f"User {telegram_id} unsubscribed")
            return True

        return False

    async def get_subscription(self, telegram_id: int) -> Subscription | None:
        """
        Get a user's subscription.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Subscription if found, None otherwise
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            state = await repo.get_state(self.bot_id, PLUGIN_NAME, sub_key)

            if not state:
                return None

            sign = ZodiacSign.from_name(state.get("sign", ""))
            if not sign:
                return None

            return Subscription(
                telegram_id=state.get("telegram_id", telegram_id),
                zodiac_sign=sign,
                delivery_hour=state.get("hour", 8),
                timezone=state.get("timezone", DEFAULT_TIMEZONE),
                is_active=state.get("active", True),
                created_at=datetime.fromisoformat(state["created_at"])
                if "created_at" in state
                else None,
            )

    async def update_sign(self, telegram_id: int, sign: ZodiacSign) -> bool:
        """
        Update a user's zodiac sign.

        Args:
            telegram_id: User's Telegram ID
            sign: New zodiac sign

        Returns:
            True if updated, False if subscription not found
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            state = await repo.get_state(self.bot_id, PLUGIN_NAME, sub_key)

            if not state:
                return False

            state["sign"] = sign.name
            await repo.set_state(self.bot_id, PLUGIN_NAME, sub_key, state)
            await session.commit()

        logger.info(f"User {telegram_id} updated sign to {sign.value}")
        return True

    async def update_time(self, telegram_id: int, hour: int) -> bool:
        """
        Update a user's delivery time.

        Args:
            telegram_id: User's Telegram ID
            hour: New delivery hour (UTC, 0-23)

        Returns:
            True if updated, False if subscription not found
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            state = await repo.get_state(self.bot_id, PLUGIN_NAME, sub_key)

            if not state:
                return False

            state["hour"] = hour
            await repo.set_state(self.bot_id, PLUGIN_NAME, sub_key, state)
            await session.commit()

        logger.info(f"User {telegram_id} updated delivery time to {hour}:00")
        return True

    async def update_timezone(self, telegram_id: int, timezone: str) -> bool:
        """
        Update a user's timezone.

        Args:
            telegram_id: User's Telegram ID
            timezone: New timezone ID

        Returns:
            True if updated, False if subscription not found
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            state = await repo.get_state(self.bot_id, PLUGIN_NAME, sub_key)

            if not state:
                return False

            state["timezone"] = timezone
            await repo.set_state(self.bot_id, PLUGIN_NAME, sub_key, state)
            await session.commit()

        logger.info(f"User {telegram_id} updated timezone to {timezone}")
        return True

    async def deactivate(self, telegram_id: int) -> None:
        """
        Deactivate a subscription (e.g., when user blocks bot).

        Args:
            telegram_id: User's Telegram ID
        """
        sub_key = self._sub_key(telegram_id)

        async with self.db.session() as session:
            repo = PluginStateRepository(session)
            state = await repo.get_state(self.bot_id, PLUGIN_NAME, sub_key)

            if state:
                state["active"] = False
                await repo.set_state(self.bot_id, PLUGIN_NAME, sub_key, state)
                await session.commit()
                logger.info(f"Deactivated subscription for user {telegram_id}")

    async def get_subscriptions_for_hour(self, utc_hour: int) -> list[Subscription]:
        """
        Get all active subscriptions scheduled for a specific UTC hour.

        This finds all subscriptions where the user's local delivery time
        corresponds to the given UTC hour.

        Args:
            utc_hour: Current UTC hour (0-23)

        Returns:
            List of active subscriptions to deliver at this UTC hour
        """
        subscriptions = []

        async with self.db.session() as session:
            # Query all subscription keys for this plugin
            query = select(PluginState).where(
                PluginState.bot_id == self.bot_id,
                PluginState.plugin_name == PLUGIN_NAME,
                PluginState.state_key.startswith("sub_"),
            )
            result = await session.execute(query)
            states = result.scalars().all()

            for state in states:
                data = state.state_value
                if not data:
                    continue

                # Check if active
                if not data.get("active", True):
                    continue

                # Get local hour and timezone
                local_hour = data.get("hour", 8)
                timezone = data.get("timezone", DEFAULT_TIMEZONE)

                # Check if this subscription's local time matches current UTC
                if local_to_utc(local_hour, timezone) != utc_hour:
                    continue

                sign = ZodiacSign.from_name(data.get("sign", ""))
                if not sign:
                    continue

                subscriptions.append(
                    Subscription(
                        telegram_id=data.get("telegram_id", 0),
                        zodiac_sign=sign,
                        delivery_hour=local_hour,
                        timezone=timezone,
                        is_active=True,
                        created_at=datetime.fromisoformat(data["created_at"])
                        if "created_at" in data
                        else None,
                    )
                )

        logger.debug(f"Found {len(subscriptions)} subscriptions for UTC hour {utc_hour}")
        return subscriptions

    async def get_all_subscriptions(self) -> list[Subscription]:
        """
        Get all active subscriptions.

        Returns:
            List of all active subscriptions
        """
        subscriptions = []

        async with self.db.session() as session:
            query = select(PluginState).where(
                PluginState.bot_id == self.bot_id,
                PluginState.plugin_name == PLUGIN_NAME,
                PluginState.state_key.startswith("sub_"),
            )
            result = await session.execute(query)
            states = result.scalars().all()

            for state in states:
                data = state.state_value
                if not data or not data.get("active", True):
                    continue

                sign = ZodiacSign.from_name(data.get("sign", ""))
                if not sign:
                    continue

                subscriptions.append(
                    Subscription(
                        telegram_id=data.get("telegram_id", 0),
                        zodiac_sign=sign,
                        delivery_hour=data.get("hour", 8),
                        timezone=data.get("timezone", DEFAULT_TIMEZONE),
                        is_active=True,
                        created_at=datetime.fromisoformat(data["created_at"])
                        if "created_at" in data
                        else None,
                    )
                )

        return subscriptions
