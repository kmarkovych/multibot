"""Scheduler for daily horoscope delivery."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .cache import HoroscopeCache
from .openai_client import HoroscopeGenerationError, OpenAIClient
from .subscription import Subscription, SubscriptionManager
from .zodiac import ZodiacSign

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


def format_horoscope_message(sign: ZodiacSign, horoscope: str, target_date: date) -> str:
    """Format horoscope for Telegram message."""
    return (
        f"{sign.emoji} <b>{sign.value} - {target_date.strftime('%B %d, %Y')}</b>\n\n"
        f"{horoscope}\n\n"
        f"<i>Have a wonderful day!</i> \u2728"
    )


class HoroscopeScheduler:
    """Scheduler for automatic horoscope delivery."""

    def __init__(
        self,
        bot: Bot,
        subscription_manager: SubscriptionManager,
        cache: HoroscopeCache,
        openai_client: OpenAIClient,
    ):
        self.bot = bot
        self.subscription_manager = subscription_manager
        self.cache = cache
        self.openai_client = openai_client
        self._scheduler: AsyncIOScheduler | None = None

    async def start(self) -> None:
        """Start the scheduler."""
        self._scheduler = AsyncIOScheduler()

        # Run every hour at minute 0 to check for deliveries
        self._scheduler.add_job(
            self._deliver_horoscopes,
            CronTrigger(minute=0),
            id="horoscope_delivery",
            replace_existing=True,
        )

        # Cleanup old cache entries daily at 3 AM UTC
        self._scheduler.add_job(
            self._cleanup_cache,
            CronTrigger(hour=3, minute=0),
            id="cache_cleanup",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("Horoscope scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Horoscope scheduler stopped")

    async def _deliver_horoscopes(self) -> None:
        """Check and deliver horoscopes to subscribers for current hour."""
        current_hour = datetime.utcnow().hour
        logger.debug(f"Checking horoscope deliveries for hour {current_hour}")

        try:
            subscriptions = await self.subscription_manager.get_subscriptions_for_hour(
                current_hour
            )

            if not subscriptions:
                return

            logger.info(f"Delivering horoscopes to {len(subscriptions)} subscribers")

            for sub in subscriptions:
                try:
                    await self._deliver_to_user(sub)
                except Exception as e:
                    logger.error(
                        f"Failed to deliver horoscope to {sub.telegram_id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error in horoscope delivery job: {e}")

    async def _deliver_to_user(self, sub: Subscription) -> None:
        """Deliver horoscope to a single user."""
        today = date.today()

        try:
            horoscope = await self._get_or_generate_horoscope(sub.zodiac_sign, today)
            message = format_horoscope_message(sub.zodiac_sign, horoscope, today)

            await self.bot.send_message(
                chat_id=sub.telegram_id,
                text=message,
                parse_mode="HTML",
            )

            logger.debug(f"Delivered horoscope to {sub.telegram_id}")

        except TelegramForbiddenError:
            # User blocked the bot
            logger.warning(f"User {sub.telegram_id} blocked bot, deactivating")
            await self.subscription_manager.deactivate(sub.telegram_id)

        except TelegramRetryAfter as e:
            # Rate limited - log and skip (will retry next hour)
            logger.warning(f"Rate limited, retry after {e.retry_after}s")

        except HoroscopeGenerationError as e:
            # OpenAI error - skip this delivery
            logger.error(f"Could not generate horoscope: {e}")

    async def _get_or_generate_horoscope(
        self, sign: ZodiacSign, target_date: date
    ) -> str:
        """Get cached horoscope or generate a new one."""
        # Try cache first
        cached = await self.cache.get(sign, target_date)
        if cached:
            return cached

        # Generate new horoscope
        horoscope = await self.openai_client.generate_horoscope(sign, target_date)

        # Cache for future requests
        await self.cache.set(sign, target_date, horoscope)

        return horoscope

    async def _cleanup_cache(self) -> None:
        """Clean up old cache entries."""
        try:
            removed = await self.cache.cleanup_old(days=2)
            if removed > 0:
                logger.info(f"Cache cleanup removed {removed} old entries")
        except Exception as e:
            logger.error(f"Error in cache cleanup: {e}")

    async def deliver_now(self, telegram_id: int, sign: ZodiacSign) -> str:
        """
        Generate and deliver horoscope immediately (for /horoscope command).

        Args:
            telegram_id: User's Telegram ID
            sign: Zodiac sign

        Returns:
            Formatted horoscope message
        """
        today = date.today()
        horoscope = await self._get_or_generate_horoscope(sign, today)
        return format_horoscope_message(sign, horoscope, today)
