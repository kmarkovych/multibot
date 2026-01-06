"""Internationalization support for horoscope bot."""

from __future__ import annotations

from typing import Any

# Supported languages
SUPPORTED_LANGUAGES = ["en", "uk"]
DEFAULT_LANGUAGE = "en"

# Translations dictionary
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Commands
        "cmd_start": "Main menu",
        "cmd_horoscope": "Get today's horoscope",
        "cmd_subscribe": "Subscribe to daily delivery",
        "cmd_unsubscribe": "Cancel subscription",
        "cmd_settings": "View settings",
        "cmd_help": "Show help",
        # Welcome
        "welcome": """<b>⭐ Welcome to Horoscope Bot!</b>

I can provide you with personalized daily horoscopes powered by AI.

<b>Features:</b>
• Get your daily horoscope
• Subscribe to receive it automatically
• Choose your preferred delivery time

Select an option below to get started!""",
        # Menu buttons
        "btn_get_horoscope": "⭐ Get Horoscope",
        "btn_subscribe": "📅 Subscribe",
        "btn_settings": "⚙️ Settings",
        "btn_other_sign": "♈ Other Sign",
        "btn_menu": "« Menu",
        "btn_change_sign": "♈ Change Sign",
        "btn_change_time": "⏰ Change Time",
        "btn_unsubscribe": "❌ Unsubscribe",
        "btn_subscribe_now": "✅ Subscribe",
        "btn_back": "« Back",
        "btn_confirm": "✅ Confirm",
        "btn_cancel": "❌ Cancel",
        # Messages
        "select_sign": "<b>♈ Select Your Zodiac Sign</b>\n\nChoose your sign to get today's horoscope:",
        "select_sign_change": "<b>♈ Change Your Zodiac Sign</b>\n\nSelect your new sign:",
        "subscribe_select_sign": "<b>📅 Subscribe to Daily Horoscope</b>\n\nFirst, select your zodiac sign:",
        "select_time": "<b>⏰ Select Delivery Time</b>\n\nSign: {sign}\n\nWhen would you like to receive your daily horoscope? (UTC)",
        "change_time": "<b>⏰ Change Delivery Time</b>\n\nSelect your preferred time (UTC):",
        "subscribed": """<b>✅ Subscribed Successfully!</b>

<b>Sign:</b> {sign}
<b>Delivery:</b> Daily at {hour}:00 UTC

You'll receive your first horoscope at the scheduled time.
Use /horoscope to get today's horoscope now!""",
        "unsubscribe_confirm": "<b>❌ Unsubscribe?</b>\n\nYou're currently subscribed to receive {sign} horoscope daily at {hour}:00 UTC.\n\nDo you want to unsubscribe?",
        "unsubscribed": """<b>✅ Unsubscribed</b>

You've been unsubscribed from daily horoscopes.
You can still use /horoscope to get your horoscope anytime!""",
        "settings_with_sub": """<b>⚙️ Your Settings</b>

<b>Sign:</b> {sign}
<b>Delivery:</b> Daily at {hour}:00 UTC
<b>Status:</b> ✅ Active""",
        "settings_no_sub": """<b>⚙️ Settings</b>

You don't have an active subscription yet.
Subscribe to receive daily horoscopes!""",
        "settings_cancelled": "<b>⚙️ Settings</b>\n\nAction cancelled.",
        "main_menu": "<b>⭐ Horoscope Bot</b>\n\nSelect an option:",
        "generating": "⏳ Generating your horoscope...",
        "service_not_ready": "Service not ready. Please try again later.",
        "no_subscription": "You don't have an active subscription.",
        "cancelled": "Cancelled",
        "sub_cancelled": "Subscription cancelled.\n\nUse /start to return to the main menu.",
        "select_sign_first": "Please select your sign first",
        "invalid_sign": "Invalid sign",
        # Help
        "help": """<b>❓ Horoscope Bot Help</b>

<b>Commands:</b>
/start - Show main menu
/horoscope - Get today's horoscope
/subscribe - Subscribe to daily delivery
/unsubscribe - Cancel subscription
/settings - View and change settings
/help - Show this help

<b>How it works:</b>
1. Select your zodiac sign
2. Get your personalized horoscope
3. Subscribe to receive it daily!

<b>Tip:</b> Horoscopes are generated using AI and cached daily for each sign.""",
        # Horoscope footer
        "have_wonderful_day": "Have a wonderful day! ✨",
    },
    "uk": {
        # Commands
        "cmd_start": "Головне меню",
        "cmd_horoscope": "Отримати гороскоп на сьогодні",
        "cmd_subscribe": "Підписатися на щоденну розсилку",
        "cmd_unsubscribe": "Скасувати підписку",
        "cmd_settings": "Переглянути налаштування",
        "cmd_help": "Показати довідку",
        # Welcome
        "welcome": """<b>⭐ Ласкаво просимо до Бота Гороскопів!</b>

Я можу надати вам персоналізовані щоденні гороскопи на основі ШІ.

<b>Можливості:</b>
• Отримуйте щоденний гороскоп
• Підпишіться на автоматичну доставку
• Оберіть зручний час доставки

Оберіть опцію нижче, щоб почати!""",
        # Menu buttons
        "btn_get_horoscope": "⭐ Гороскоп",
        "btn_subscribe": "📅 Підписка",
        "btn_settings": "⚙️ Налаштування",
        "btn_other_sign": "♈ Інший знак",
        "btn_menu": "« Меню",
        "btn_change_sign": "♈ Змінити знак",
        "btn_change_time": "⏰ Змінити час",
        "btn_unsubscribe": "❌ Відписатися",
        "btn_subscribe_now": "✅ Підписатися",
        "btn_back": "« Назад",
        "btn_confirm": "✅ Підтвердити",
        "btn_cancel": "❌ Скасувати",
        # Messages
        "select_sign": "<b>♈ Оберіть ваш знак зодіаку</b>\n\nОберіть знак, щоб отримати гороскоп на сьогодні:",
        "select_sign_change": "<b>♈ Змінити знак зодіаку</b>\n\nОберіть новий знак:",
        "subscribe_select_sign": "<b>📅 Підписка на щоденний гороскоп</b>\n\nСпочатку оберіть ваш знак зодіаку:",
        "select_time": "<b>⏰ Оберіть час доставки</b>\n\nЗнак: {sign}\n\nКоли ви бажаєте отримувати щоденний гороскоп? (UTC)",
        "change_time": "<b>⏰ Змінити час доставки</b>\n\nОберіть бажаний час (UTC):",
        "subscribed": """<b>✅ Підписка оформлена!</b>

<b>Знак:</b> {sign}
<b>Доставка:</b> Щодня о {hour}:00 UTC

Ви отримаєте перший гороскоп у запланований час.
Використовуйте /horoscope, щоб отримати гороскоп зараз!""",
        "unsubscribe_confirm": "<b>❌ Відписатися?</b>\n\nВи підписані на гороскоп {sign} щодня о {hour}:00 UTC.\n\nБажаєте відписатися?",
        "unsubscribed": """<b>✅ Відписано</b>

Ви відписалися від щоденних гороскопів.
Ви все ще можете використовувати /horoscope для отримання гороскопу!""",
        "settings_with_sub": """<b>⚙️ Ваші налаштування</b>

<b>Знак:</b> {sign}
<b>Доставка:</b> Щодня о {hour}:00 UTC
<b>Статус:</b> ✅ Активна""",
        "settings_no_sub": """<b>⚙️ Налаштування</b>

У вас ще немає активної підписки.
Підпишіться, щоб отримувати щоденні гороскопи!""",
        "settings_cancelled": "<b>⚙️ Налаштування</b>\n\nДію скасовано.",
        "main_menu": "<b>⭐ Бот Гороскопів</b>\n\nОберіть опцію:",
        "generating": "⏳ Генерую ваш гороскоп...",
        "service_not_ready": "Сервіс не готовий. Спробуйте пізніше.",
        "no_subscription": "У вас немає активної підписки.",
        "cancelled": "Скасовано",
        "sub_cancelled": "Підписку скасовано.\n\nВикористовуйте /start, щоб повернутися до меню.",
        "select_sign_first": "Спочатку оберіть ваш знак",
        "invalid_sign": "Невірний знак",
        # Help
        "help": """<b>❓ Довідка бота гороскопів</b>

<b>Команди:</b>
/start - Головне меню
/horoscope - Отримати гороскоп на сьогодні
/subscribe - Підписатися на щоденну розсилку
/unsubscribe - Скасувати підписку
/settings - Переглянути налаштування
/help - Показати цю довідку

<b>Як це працює:</b>
1. Оберіть ваш знак зодіаку
2. Отримайте персоналізований гороскоп
3. Підпишіться на щоденну доставку!

<b>Порада:</b> Гороскопи генеруються за допомогою ШІ та кешуються щодня для кожного знаку.""",
        # Horoscope footer
        "have_wonderful_day": "Гарного дня! ✨",
    },
}


def get_lang(language_code: str | None) -> str:
    """Get supported language code or default."""
    if not language_code:
        return DEFAULT_LANGUAGE
    # Check for exact match or prefix match (e.g., "uk-UA" -> "uk")
    lang = language_code.lower().split("-")[0]
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, language_code: str | None = None, **kwargs: Any) -> str:
    """Get translated string."""
    lang = get_lang(language_code)
    text = TRANSLATIONS.get(lang, {}).get(key, "")
    if not text:
        # Fallback to English
        text = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
