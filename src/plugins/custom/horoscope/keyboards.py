"""Inline keyboards for horoscope bot."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .i18n import t
from .timezone import get_timezone_list
from .zodiac import ZodiacSign


def get_zodiac_keyboard() -> InlineKeyboardMarkup:
    """Create a 4x3 grid of zodiac sign buttons."""
    signs = list(ZodiacSign)
    rows = []

    for i in range(0, 12, 3):
        row = [
            InlineKeyboardButton(
                text=sign.format_display(),
                callback_data=f"zodiac_{sign.name.lower()}",
            )
            for sign in signs[i : i + 3]
        ]
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_time_keyboard(lang: str | None = None) -> InlineKeyboardMarkup:
    """Create keyboard for selecting delivery time (UTC hours)."""
    times = [
        ("06:00", 6),
        ("08:00", 8),
        ("10:00", 10),
        ("12:00", 12),
        ("18:00", 18),
        ("20:00", 20),
    ]

    rows = []
    for i in range(0, 6, 3):
        row = [
            InlineKeyboardButton(
                text=f"\u23f0 {label}",
                callback_data=f"subtime_{hour}",
            )
            for label, hour in times[i : i + 3]
        ]
        rows.append(row)

    rows.append([
        InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="sub_cancel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_timezone_keyboard(lang: str | None = None) -> InlineKeyboardMarkup:
    """Create keyboard for selecting timezone."""
    timezones = get_timezone_list()
    rows = []

    # Group timezones in rows of 2
    for i in range(0, len(timezones), 2):
        row = []
        for tz in timezones[i : i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=tz.display_name,
                    callback_data=f"tz_{tz.timezone_id}",
                )
            )
        rows.append(row)

    rows.append([
        InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="sub_cancel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_settings_keyboard(has_subscription: bool, lang: str | None = None) -> InlineKeyboardMarkup:
    """Create settings menu keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text=t("btn_change_sign", lang),
                callback_data="settings_sign",
            ),
        ],
    ]

    if has_subscription:
        buttons.append([
            InlineKeyboardButton(
                text=t("btn_change_time", lang),
                callback_data="settings_time",
            ),
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("btn_change_timezone", lang),
                callback_data="settings_timezone",
            ),
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("btn_unsubscribe", lang),
                callback_data="settings_unsub",
            ),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text=t("btn_subscribe_now", lang),
                callback_data="settings_sub",
            ),
        ])

    buttons.append([
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="settings_back"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard(action: str, lang: str | None = None) -> InlineKeyboardMarkup:
    """Create confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_confirm", lang),
                    callback_data=f"confirm_{action}",
                ),
                InlineKeyboardButton(
                    text=t("btn_cancel", lang),
                    callback_data="confirm_cancel",
                ),
            ],
        ]
    )


def get_main_menu_keyboard(lang: str | None = None) -> InlineKeyboardMarkup:
    """Create main menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_get_horoscope", lang),
                    callback_data="menu_horoscope",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_subscribe", lang),
                    callback_data="menu_subscribe",
                ),
                InlineKeyboardButton(
                    text=t("btn_settings", lang),
                    callback_data="menu_settings",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn_my_balance", lang),
                    callback_data="billing:balance",
                ),
            ],
        ]
    )


def get_horoscope_keyboard(lang: str | None = None) -> InlineKeyboardMarkup:
    """Create keyboard shown after horoscope display."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_other_sign", lang),
                    callback_data="horoscope_other",
                ),
                InlineKeyboardButton(
                    text=t("btn_menu", lang),
                    callback_data="horoscope_menu",
                ),
            ],
        ]
    )
