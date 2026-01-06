"""Data transfer objects for statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class AggregatedStats:
    """Aggregated statistics for a time period."""

    message_count: int = 0
    command_count: int = 0
    callback_count: int = 0
    error_count: int = 0
    new_users: int = 0


@dataclass
class BotStatsDTO:
    """Comprehensive statistics for a single bot."""

    bot_id: str
    bot_name: str = ""
    total_users: int = 0
    daily_active_users: int = 0
    weekly_active_users: int = 0
    uptime: timedelta | None = None
    today_messages: int = 0
    today_commands: int = 0
    today_callbacks: int = 0
    week_messages: int = 0
    week_commands: int = 0
    error_rate: float = 0.0
    hourly_pattern: list[int] = field(default_factory=lambda: [0] * 24)
    top_commands: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class SystemStatsDTO:
    """System-wide statistics."""

    total_bots: int = 0
    running_bots: int = 0
    total_users: int = 0
    today_messages: int = 0
    today_commands: int = 0
