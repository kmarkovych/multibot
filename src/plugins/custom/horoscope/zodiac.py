"""Zodiac sign definitions and utilities."""

from __future__ import annotations

from datetime import date
from enum import Enum


class ZodiacSign(Enum):
    """Zodiac signs with their properties."""

    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"

    @property
    def emoji(self) -> str:
        """Get the zodiac emoji."""
        emojis = {
            "ARIES": "\u2648",
            "TAURUS": "\u2649",
            "GEMINI": "\u264a",
            "CANCER": "\u264b",
            "LEO": "\u264c",
            "VIRGO": "\u264d",
            "LIBRA": "\u264e",
            "SCORPIO": "\u264f",
            "SAGITTARIUS": "\u2650",
            "CAPRICORN": "\u2651",
            "AQUARIUS": "\u2652",
            "PISCES": "\u2653",
        }
        return emojis[self.name]

    @property
    def date_range(self) -> str:
        """Get the date range for this sign."""
        ranges = {
            "ARIES": "Mar 21 - Apr 19",
            "TAURUS": "Apr 20 - May 20",
            "GEMINI": "May 21 - Jun 20",
            "CANCER": "Jun 21 - Jul 22",
            "LEO": "Jul 23 - Aug 22",
            "VIRGO": "Aug 23 - Sep 22",
            "LIBRA": "Sep 23 - Oct 22",
            "SCORPIO": "Oct 23 - Nov 21",
            "SAGITTARIUS": "Nov 22 - Dec 21",
            "CAPRICORN": "Dec 22 - Jan 19",
            "AQUARIUS": "Jan 20 - Feb 18",
            "PISCES": "Feb 19 - Mar 20",
        }
        return ranges[self.name]

    @classmethod
    def from_name(cls, name: str) -> ZodiacSign | None:
        """Get zodiac sign from name (case-insensitive)."""
        name_upper = name.upper()
        for sign in cls:
            if sign.name == name_upper or sign.value.upper() == name_upper:
                return sign
        return None

    @classmethod
    def from_birthday(cls, birthday: date) -> ZodiacSign:
        """Determine zodiac sign from birthday."""
        month = birthday.month
        day = birthday.day

        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return cls.ARIES
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return cls.TAURUS
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return cls.GEMINI
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return cls.CANCER
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return cls.LEO
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return cls.VIRGO
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return cls.LIBRA
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return cls.SCORPIO
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return cls.SAGITTARIUS
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return cls.CAPRICORN
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return cls.AQUARIUS
        else:
            return cls.PISCES

    def format_display(self) -> str:
        """Format for display with emoji and name."""
        return f"{self.emoji} {self.value}"
