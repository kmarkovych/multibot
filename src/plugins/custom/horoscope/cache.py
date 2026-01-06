"""Horoscope caching using PluginState table."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.database.models import PluginState
from src.database.repositories.bot_repository import PluginStateRepository

from .i18n import get_lang
from .zodiac import ZodiacSign

if TYPE_CHECKING:
    from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

PLUGIN_NAME = "horoscope"


class HoroscopeCache:
    """Cache for horoscopes using PluginState table."""

    def __init__(self, db: DatabaseManager, bot_id: str):
        self.db = db
        self.bot_id = bot_id

    def _cache_key(self, sign: ZodiacSign, target_date: date, lang: str) -> str:
        """Generate cache key for a horoscope."""
        return f"cache_{sign.name.lower()}_{target_date.isoformat()}_{lang}"

    async def get(
        self, sign: ZodiacSign, target_date: date, lang: str | None = None
    ) -> str | None:
        """
        Get cached horoscope if available.

        Args:
            sign: Zodiac sign
            target_date: Date of the horoscope
            lang: Language code

        Returns:
            Cached horoscope text or None if not cached
        """
        lang = get_lang(lang)
        cache_key = self._cache_key(sign, target_date, lang)

        try:
            async with self.db.session() as session:
                repo = PluginStateRepository(session)
                state = await repo.get_state(self.bot_id, PLUGIN_NAME, cache_key)

                if state and "horoscope" in state:
                    logger.debug(f"Cache hit for {sign.value} on {target_date}")
                    return state["horoscope"]

                logger.debug(f"Cache miss for {sign.value} on {target_date}")
                return None

        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    async def set(
        self, sign: ZodiacSign, target_date: date, horoscope: str, lang: str | None = None
    ) -> None:
        """
        Cache a horoscope.

        Args:
            sign: Zodiac sign
            target_date: Date of the horoscope
            horoscope: Horoscope text to cache
            lang: Language code
        """
        lang = get_lang(lang)
        cache_key = self._cache_key(sign, target_date, lang)

        try:
            async with self.db.session() as session:
                repo = PluginStateRepository(session)
                await repo.set_state(
                    self.bot_id,
                    PLUGIN_NAME,
                    cache_key,
                    {
                        "horoscope": horoscope,
                        "sign": sign.name,
                        "date": target_date.isoformat(),
                        "cached_at": datetime.utcnow().isoformat(),
                    },
                )
                await session.commit()
                logger.debug(f"Cached horoscope for {sign.value} on {target_date}")

        except Exception as e:
            logger.error(f"Error writing cache: {e}")

    async def cleanup_old(self, days: int = 2) -> int:
        """
        Remove cache entries older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of entries removed
        """
        cutoff_date = date.today() - timedelta(days=days)
        removed = 0

        try:
            async with self.db.session() as session:
                # Find all cache entries for this plugin
                query = select(PluginState).where(
                    PluginState.bot_id == self.bot_id,
                    PluginState.plugin_name == PLUGIN_NAME,
                    PluginState.state_key.startswith("cache_"),
                )
                result = await session.execute(query)
                cache_entries = result.scalars().all()

                for entry in cache_entries:
                    # Parse date from cache key: cache_{sign}_{date}
                    parts = entry.state_key.split("_")
                    if len(parts) >= 3:
                        try:
                            entry_date = date.fromisoformat(parts[2])
                            if entry_date < cutoff_date:
                                await session.delete(entry)
                                removed += 1
                        except ValueError:
                            continue

                await session.commit()
                if removed > 0:
                    logger.info(f"Cleaned up {removed} old cache entries")

        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")

        return removed
