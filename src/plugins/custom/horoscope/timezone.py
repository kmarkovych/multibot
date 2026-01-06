"""Timezone utilities for horoscope scheduling."""

from __future__ import annotations

from dataclasses import dataclass

# Common timezones with their UTC offsets (simplified, no DST handling)
# Format: (display_name, timezone_id, utc_offset_hours)
TIMEZONES: list[tuple[str, str, int]] = [
    # UTC
    ("UTC (GMT+0)", "UTC", 0),
    # Europe
    ("London (GMT+0)", "Europe/London", 0),
    ("Paris (GMT+1)", "Europe/Paris", 1),
    ("Berlin (GMT+1)", "Europe/Berlin", 1),
    ("Kyiv (GMT+2)", "Europe/Kyiv", 2),
    ("Istanbul (GMT+3)", "Europe/Istanbul", 3),
    ("Moscow (GMT+3)", "Europe/Moscow", 3),
    # Asia
    ("Dubai (GMT+4)", "Asia/Dubai", 4),
    ("Almaty (GMT+6)", "Asia/Almaty", 6),
    ("Bangkok (GMT+7)", "Asia/Bangkok", 7),
    ("Singapore (GMT+8)", "Asia/Singapore", 8),
    ("Tokyo (GMT+9)", "Asia/Tokyo", 9),
    # Americas
    ("Sao Paulo (GMT-3)", "America/Sao_Paulo", -3),
    ("New York (GMT-5)", "America/New_York", -5),
    ("Chicago (GMT-6)", "America/Chicago", -6),
    ("Denver (GMT-7)", "America/Denver", -7),
    ("Los Angeles (GMT-8)", "America/Los_Angeles", -8),
]

# Default timezone
DEFAULT_TIMEZONE = "UTC"


@dataclass
class TimezoneInfo:
    """Timezone information."""

    display_name: str
    timezone_id: str
    utc_offset: int


def get_timezone_list() -> list[TimezoneInfo]:
    """Get list of available timezones."""
    return [
        TimezoneInfo(display_name=name, timezone_id=tz_id, utc_offset=offset)
        for name, tz_id, offset in TIMEZONES
    ]


def get_timezone_offset(timezone_id: str) -> int:
    """Get UTC offset for a timezone ID."""
    for _, tz_id, offset in TIMEZONES:
        if tz_id == timezone_id:
            return offset
    return 0  # Default to UTC


def get_timezone_display(timezone_id: str) -> str:
    """Get display name for a timezone ID."""
    for name, tz_id, _ in TIMEZONES:
        if tz_id == timezone_id:
            return name
    return timezone_id


def local_to_utc(local_hour: int, timezone_id: str) -> int:
    """
    Convert local hour to UTC hour.

    Args:
        local_hour: Hour in local time (0-23)
        timezone_id: Timezone identifier

    Returns:
        UTC hour (0-23)
    """
    offset = get_timezone_offset(timezone_id)
    utc_hour = (local_hour - offset) % 24
    return utc_hour


def utc_to_local(utc_hour: int, timezone_id: str) -> int:
    """
    Convert UTC hour to local hour.

    Args:
        utc_hour: Hour in UTC (0-23)
        timezone_id: Timezone identifier

    Returns:
        Local hour (0-23)
    """
    offset = get_timezone_offset(timezone_id)
    local_hour = (utc_hour + offset) % 24
    return local_hour


def format_local_time(hour: int, timezone_id: str) -> str:
    """
    Format time for display with timezone.

    Args:
        hour: Local hour (0-23)
        timezone_id: Timezone identifier

    Returns:
        Formatted string like "08:00 (Kyiv)"
    """
    # Extract city name from timezone_id (e.g., "Europe/Kyiv" -> "Kyiv")
    city = timezone_id.split("/")[-1].replace("_", " ")
    return f"{hour:02d}:00 ({city})"
