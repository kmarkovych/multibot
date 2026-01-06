"""Inline keyboards for horoscope bot."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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


def get_time_keyboard() -> InlineKeyboardMarkup:
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
        InlineKeyboardButton(text="\u274c Cancel", callback_data="sub_cancel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_settings_keyboard(has_subscription: bool) -> InlineKeyboardMarkup:
    """Create settings menu keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="\u2648 Change Sign",
                callback_data="settings_sign",
            ),
        ],
    ]

    if has_subscription:
        buttons.append([
            InlineKeyboardButton(
                text="\u23f0 Change Time",
                callback_data="settings_time",
            ),
        ])
        buttons.append([
            InlineKeyboardButton(
                text="\u274c Unsubscribe",
                callback_data="settings_unsub",
            ),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="\u2705 Subscribe",
                callback_data="settings_sub",
            ),
        ])

    buttons.append([
        InlineKeyboardButton(text="\u00ab Back", callback_data="settings_back"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Create confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2705 Confirm",
                    callback_data=f"confirm_{action}",
                ),
                InlineKeyboardButton(
                    text="\u274c Cancel",
                    callback_data="confirm_cancel",
                ),
            ],
        ]
    )


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2b50 Get Horoscope",
                    callback_data="menu_horoscope",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\ud83d\udcc5 Subscribe",
                    callback_data="menu_subscribe",
                ),
                InlineKeyboardButton(
                    text="\u2699\ufe0f Settings",
                    callback_data="menu_settings",
                ),
            ],
        ]
    )
