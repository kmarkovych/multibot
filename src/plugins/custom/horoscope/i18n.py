"""Internationalization support for horoscope bot."""

from __future__ import annotations

from typing import Any

# Supported languages
SUPPORTED_LANGUAGES = ["en", "uk", "pt", "kk"]
DEFAULT_LANGUAGE = "en"

# Translations dictionary
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Bot info
        "bot_name": "Horoscope Bot",
        "bot_description": """✨ Your Personal AI Horoscope Bot ✨

Get daily horoscopes powered by artificial intelligence!

• Personalized readings for all 12 zodiac signs
• Subscribe to receive your horoscope automatically
• Choose your preferred delivery time

Start now and discover what the stars have in store for you!""",
        "bot_short_description": "AI-powered daily horoscopes for all zodiac signs ✨",
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
        "btn_change_timezone": "🌍 Change Timezone",
        "btn_unsubscribe": "❌ Unsubscribe",
        "btn_subscribe_now": "✅ Subscribe",
        "btn_back": "« Back",
        "btn_confirm": "✅ Confirm",
        "btn_cancel": "❌ Cancel",
        # Messages
        "select_sign": "<b>♈ Select Your Zodiac Sign</b>\n\nChoose your sign to get today's horoscope:",
        "select_sign_change": "<b>♈ Change Your Zodiac Sign</b>\n\nSelect your new sign:",
        "subscribe_select_sign": "<b>📅 Subscribe to Daily Horoscope</b>\n\nFirst, select your zodiac sign:",
        "select_timezone": "<b>🌍 Select Your Timezone</b>\n\nSign: {sign}\n\nChoose your timezone:",
        "change_timezone": "<b>🌍 Change Timezone</b>\n\nCurrent: {timezone}\n\nSelect your new timezone:",
        "select_time": "<b>⏰ Select Delivery Time</b>\n\nSign: {sign}\nTimezone: {timezone}\n\nWhen would you like to receive your daily horoscope?",
        "change_time": "<b>⏰ Change Delivery Time</b>\n\nSign: {sign}\nTimezone: {timezone}\n\nSelect your preferred time:",
        "subscribed": """<b>✅ Subscribed Successfully!</b>

<b>Sign:</b> {sign}
<b>Delivery:</b> Daily at {time}

You'll receive your first horoscope at the scheduled time.
Use /horoscope to get today's horoscope now!""",
        "unsubscribe_confirm": "<b>❌ Unsubscribe?</b>\n\nYou're currently subscribed to receive {sign} horoscope daily at {time}.\n\nDo you want to unsubscribe?",
        "unsubscribed": """<b>✅ Unsubscribed</b>

You've been unsubscribed from daily horoscopes.
You can still use /horoscope to get your horoscope anytime!""",
        "settings_with_sub": """<b>⚙️ Your Settings</b>

<b>Sign:</b> {sign}
<b>Delivery:</b> Daily at {time}
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
        # Token welcome messages
        "welcome_free_tokens": "🎁 You received <b>{tokens} free tokens</b> to get started!",
        "welcome_token_balance": "💰 Your balance: <b>{balance}</b> tokens",
        # Subscription status in welcome
        "welcome_subscription_active": "📅 Subscription: <b>{sign}</b> daily at {time}",
        "welcome_no_subscription": "📅 No active subscription. Use /subscribe to get daily horoscopes!",
        # Billing
        "billing_balance_title": "Your Token Balance",
        "billing_balance": "Balance: <b>{balance}</b> tokens",
        "billing_total_purchased": "Total purchased: {total}",
        "billing_total_used": "Total used: {total}",
        "billing_buy_tokens": "Buy Tokens",
        "billing_history": "History",
        "billing_back": "Back",
        "billing_packages_title": "Available Token Packages",
        "billing_no_packages": "No token packages available at this time.",
        "billing_no_history": "No transactions yet.",
        "billing_history_title": "Recent Transactions",
        "billing_payment_success": "Payment Successful!",
        "billing_payment_received": "You received <b>{tokens}</b> tokens.",
        "billing_new_balance": "New balance: <b>{balance}</b> tokens.",
        "billing_thank_you": "Thank you for your purchase!",
        "billing_package_starter": "30 Tokens",
        "billing_package_starter_desc": "~1 month of daily horoscopes",
        "billing_package_standard": "100 Tokens",
        "billing_package_standard_desc": "Best value - 3+ months",
        "billing_package_premium": "250 Tokens",
        "billing_package_premium_desc": "Power user pack - save 20%",
        "insufficient_tokens": "You need {required} token(s) but have {available}.\n\nUse /tokens to check your balance or purchase more.",
    },
    "uk": {
        # Bot info
        "bot_name": "Бот Гороскопів",
        "bot_description": """✨ Ваш Особистий AI Бот Гороскопів ✨

Отримуйте щоденні гороскопи на основі штучного інтелекту!

• Персоналізовані передбачення для всіх 12 знаків зодіаку
• Підпишіться на автоматичну доставку гороскопу
• Оберіть зручний час доставки

Почніть зараз і дізнайтеся, що вам приготували зірки!""",
        "bot_short_description": "Щоденні AI-гороскопи для всіх знаків зодіаку ✨",
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
        "btn_change_timezone": "🌍 Змінити часовий пояс",
        "btn_unsubscribe": "❌ Відписатися",
        "btn_subscribe_now": "✅ Підписатися",
        "btn_back": "« Назад",
        "btn_confirm": "✅ Підтвердити",
        "btn_cancel": "❌ Скасувати",
        # Messages
        "select_sign": "<b>♈ Оберіть ваш знак зодіаку</b>\n\nОберіть знак, щоб отримати гороскоп на сьогодні:",
        "select_sign_change": "<b>♈ Змінити знак зодіаку</b>\n\nОберіть новий знак:",
        "subscribe_select_sign": "<b>📅 Підписка на щоденний гороскоп</b>\n\nСпочатку оберіть ваш знак зодіаку:",
        "select_timezone": "<b>🌍 Оберіть часовий пояс</b>\n\nЗнак: {sign}\n\nОберіть ваш часовий пояс:",
        "change_timezone": "<b>🌍 Змінити часовий пояс</b>\n\nПоточний: {timezone}\n\nОберіть новий часовий пояс:",
        "select_time": "<b>⏰ Оберіть час доставки</b>\n\nЗнак: {sign}\nЧасовий пояс: {timezone}\n\nКоли ви бажаєте отримувати щоденний гороскоп?",
        "change_time": "<b>⏰ Змінити час доставки</b>\n\nЗнак: {sign}\nЧасовий пояс: {timezone}\n\nОберіть бажаний час:",
        "subscribed": """<b>✅ Підписка оформлена!</b>

<b>Знак:</b> {sign}
<b>Доставка:</b> Щодня о {time}

Ви отримаєте перший гороскоп у запланований час.
Використовуйте /horoscope, щоб отримати гороскоп зараз!""",
        "unsubscribe_confirm": "<b>❌ Відписатися?</b>\n\nВи підписані на гороскоп {sign} щодня о {time}.\n\nБажаєте відписатися?",
        "unsubscribed": """<b>✅ Відписано</b>

Ви відписалися від щоденних гороскопів.
Ви все ще можете використовувати /horoscope для отримання гороскопу!""",
        "settings_with_sub": """<b>⚙️ Ваші налаштування</b>

<b>Знак:</b> {sign}
<b>Доставка:</b> Щодня о {time}
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
        # Token welcome messages
        "welcome_free_tokens": "🎁 Ви отримали <b>{tokens} безкоштовних токенів</b> для початку!",
        "welcome_token_balance": "💰 Ваш баланс: <b>{balance}</b> токенів",
        # Subscription status in welcome
        "welcome_subscription_active": "📅 Підписка: <b>{sign}</b> щодня о {time}",
        "welcome_no_subscription": "📅 Немає активної підписки. Використовуйте /subscribe для щоденних гороскопів!",
        # Billing
        "billing_balance_title": "Ваш баланс токенів",
        "billing_balance": "Баланс: <b>{balance}</b> токенів",
        "billing_total_purchased": "Всього придбано: {total}",
        "billing_total_used": "Всього використано: {total}",
        "billing_buy_tokens": "Купити токени",
        "billing_history": "Історія",
        "billing_back": "Назад",
        "billing_packages_title": "Доступні пакети токенів",
        "billing_no_packages": "Наразі немає доступних пакетів токенів.",
        "billing_no_history": "Транзакцій ще немає.",
        "billing_history_title": "Останні транзакції",
        "billing_payment_success": "Оплата успішна!",
        "billing_payment_received": "Ви отримали <b>{tokens}</b> токенів.",
        "billing_new_balance": "Новий баланс: <b>{balance}</b> токенів.",
        "billing_thank_you": "Дякуємо за покупку!",
        "billing_package_starter": "30 токенів",
        "billing_package_starter_desc": "~1 місяць щоденних гороскопів",
        "billing_package_standard": "100 токенів",
        "billing_package_standard_desc": "Найвигідніше - 3+ місяці",
        "billing_package_premium": "250 токенів",
        "billing_package_premium_desc": "Пакет для активних - економія 20%",
        "insufficient_tokens": "Вам потрібно {required} токен(ів), але у вас є {available}.\n\nВикористовуйте /tokens, щоб перевірити баланс або придбати більше.",
    },
    "pt": {
        # Bot info
        "bot_name": "Bot de Horoscopo",
        "bot_description": """✨ Seu Bot Pessoal de Horóscopo com IA ✨

Receba horóscopos diários gerados por inteligência artificial!

• Leituras personalizadas para todos os 12 signos do zodíaco
• Assine para receber seu horóscopo automaticamente
• Escolha seu horário preferido de entrega

Comece agora e descubra o que as estrelas reservam para você!""",
        "bot_short_description": "Horóscopos diários com IA para todos os signos ✨",
        # Commands
        "cmd_start": "Menu principal",
        "cmd_horoscope": "Ver horóscopo de hoje",
        "cmd_subscribe": "Assinar entrega diária",
        "cmd_unsubscribe": "Cancelar assinatura",
        "cmd_settings": "Ver configurações",
        "cmd_help": "Mostrar ajuda",
        # Welcome
        "welcome": """<b>⭐ Bem-vindo ao Bot de Horóscopo!</b>

Posso fornecer horóscopos diários personalizados com IA.

<b>Recursos:</b>
• Receba seu horóscopo diário
• Assine para receber automaticamente
• Escolha seu horário preferido de entrega

Selecione uma opção abaixo para começar!""",
        # Menu buttons
        "btn_get_horoscope": "⭐ Ver Horóscopo",
        "btn_subscribe": "📅 Assinar",
        "btn_settings": "⚙️ Configurações",
        "btn_other_sign": "♈ Outro Signo",
        "btn_menu": "« Menu",
        "btn_change_sign": "♈ Mudar Signo",
        "btn_change_time": "⏰ Mudar Horário",
        "btn_change_timezone": "🌍 Mudar Fuso Horário",
        "btn_unsubscribe": "❌ Cancelar",
        "btn_subscribe_now": "✅ Assinar",
        "btn_back": "« Voltar",
        "btn_confirm": "✅ Confirmar",
        "btn_cancel": "❌ Cancelar",
        # Messages
        "select_sign": "<b>♈ Selecione Seu Signo</b>\n\nEscolha seu signo para ver o horóscopo de hoje:",
        "select_sign_change": "<b>♈ Mudar Seu Signo</b>\n\nSelecione seu novo signo:",
        "subscribe_select_sign": "<b>📅 Assinar Horóscopo Diário</b>\n\nPrimeiro, selecione seu signo:",
        "select_timezone": "<b>🌍 Selecione Seu Fuso Horário</b>\n\nSigno: {sign}\n\nEscolha seu fuso horário:",
        "change_timezone": "<b>🌍 Mudar Fuso Horário</b>\n\nAtual: {timezone}\n\nSelecione seu novo fuso horário:",
        "select_time": "<b>⏰ Selecione o Horário de Entrega</b>\n\nSigno: {sign}\nFuso horário: {timezone}\n\nQuando você gostaria de receber seu horóscopo diário?",
        "change_time": "<b>⏰ Mudar Horário de Entrega</b>\n\nSigno: {sign}\nFuso horário: {timezone}\n\nSelecione seu horário preferido:",
        "subscribed": """<b>✅ Assinatura Confirmada!</b>

<b>Signo:</b> {sign}
<b>Entrega:</b> Diariamente às {time}

Você receberá seu primeiro horóscopo no horário agendado.
Use /horoscope para ver o horóscopo de hoje agora!""",
        "unsubscribe_confirm": "<b>❌ Cancelar Assinatura?</b>\n\nVocê está assinando o horóscopo de {sign} diariamente às {time}.\n\nDeseja cancelar?",
        "unsubscribed": """<b>✅ Assinatura Cancelada</b>

Você cancelou a assinatura de horóscopos diários.
Você ainda pode usar /horoscope para ver seu horóscopo a qualquer momento!""",
        "settings_with_sub": """<b>⚙️ Suas Configurações</b>

<b>Signo:</b> {sign}
<b>Entrega:</b> Diariamente às {time}
<b>Status:</b> ✅ Ativo""",
        "settings_no_sub": """<b>⚙️ Configurações</b>

Você ainda não tem uma assinatura ativa.
Assine para receber horóscopos diários!""",
        "settings_cancelled": "<b>⚙️ Configurações</b>\n\nAção cancelada.",
        "main_menu": "<b>⭐ Bot de Horóscopo</b>\n\nSelecione uma opção:",
        "generating": "⏳ Gerando seu horóscopo...",
        "service_not_ready": "Serviço não disponível. Tente novamente mais tarde.",
        "no_subscription": "Você não tem uma assinatura ativa.",
        "cancelled": "Cancelado",
        "sub_cancelled": "Assinatura cancelada.\n\nUse /start para voltar ao menu principal.",
        "select_sign_first": "Por favor, selecione seu signo primeiro",
        "invalid_sign": "Signo inválido",
        # Help
        "help": """<b>❓ Ajuda do Bot de Horóscopo</b>

<b>Comandos:</b>
/start - Mostrar menu principal
/horoscope - Ver horóscopo de hoje
/subscribe - Assinar entrega diária
/unsubscribe - Cancelar assinatura
/settings - Ver e alterar configurações
/help - Mostrar esta ajuda

<b>Como funciona:</b>
1. Selecione seu signo do zodíaco
2. Receba seu horóscopo personalizado
3. Assine para receber diariamente!

<b>Dica:</b> Os horóscopos são gerados por IA e armazenados diariamente para cada signo.""",
        # Horoscope footer
        "have_wonderful_day": "Tenha um dia maravilhoso! ✨",
        # Token welcome messages
        "welcome_free_tokens": "🎁 Você recebeu <b>{tokens} tokens grátis</b> para começar!",
        "welcome_token_balance": "💰 Seu saldo: <b>{balance}</b> tokens",
        # Subscription status in welcome
        "welcome_subscription_active": "📅 Assinatura: <b>{sign}</b> diariamente às {time}",
        "welcome_no_subscription": "📅 Sem assinatura ativa. Use /subscribe para receber horóscopos diários!",
        # Billing
        "billing_balance_title": "Seu Saldo de Tokens",
        "billing_balance": "Saldo: <b>{balance}</b> tokens",
        "billing_total_purchased": "Total comprado: {total}",
        "billing_total_used": "Total usado: {total}",
        "billing_buy_tokens": "Comprar Tokens",
        "billing_history": "Histórico",
        "billing_back": "Voltar",
        "billing_packages_title": "Pacotes de Tokens Disponíveis",
        "billing_no_packages": "Nenhum pacote de tokens disponível no momento.",
        "billing_no_history": "Nenhuma transação ainda.",
        "billing_history_title": "Transações Recentes",
        "billing_payment_success": "Pagamento Realizado!",
        "billing_payment_received": "Você recebeu <b>{tokens}</b> tokens.",
        "billing_new_balance": "Novo saldo: <b>{balance}</b> tokens.",
        "billing_thank_you": "Obrigado pela sua compra!",
        "billing_package_starter": "30 Tokens",
        "billing_package_starter_desc": "~1 mês de horóscopos diários",
        "billing_package_standard": "100 Tokens",
        "billing_package_standard_desc": "Melhor valor - 3+ meses",
        "billing_package_premium": "250 Tokens",
        "billing_package_premium_desc": "Pacote avançado - economize 20%",
        "insufficient_tokens": "Você precisa de {required} token(s) mas tem {available}.\n\nUse /tokens para verificar seu saldo ou comprar mais.",
    },
    "kk": {
        # Bot info
        "bot_name": "Жұлдызнама Боты",
        "bot_description": """✨ Сіздің Жеке AI Жұлдызнама Ботыңыз ✨

Жасанды интеллект негізінде күнделікті жұлдызнамалар алыңыз!

• Барлық 12 зодиак белгісі үшін жеке болжамдар
• Жұлдызнамаңызды автоматты түрде алу үшін жазылыңыз
• Қалаған жеткізу уақытын таңдаңыз

Қазір бастаңыз және жұлдыздар сізге не дайындағанын біліңіз!""",
        "bot_short_description": "Барлық зодиак белгілері үшін AI жұлдызнамалар ✨",
        # Commands
        "cmd_start": "Басты мәзір",
        "cmd_horoscope": "Бүгінгі жұлдызнама",
        "cmd_subscribe": "Күнделікті жіберуге жазылу",
        "cmd_unsubscribe": "Жазылымды болдырмау",
        "cmd_settings": "Параметрлерді көру",
        "cmd_help": "Анықтаманы көрсету",
        # Welcome
        "welcome": """<b>⭐ Жұлдызнама ботына қош келдіңіз!</b>

Мен сізге AI көмегімен жасалған жеке күнделікті жұлдызнамаларды ұсына аламын.

<b>Мүмкіндіктер:</b>
• Күнделікті жұлдызнамаңызды алыңыз
• Автоматты жіберуге жазылыңыз
• Қалаған жеткізу уақытын таңдаңыз

Бастау үшін төмендегі опцияны таңдаңыз!""",
        # Menu buttons
        "btn_get_horoscope": "⭐ Жұлдызнама",
        "btn_subscribe": "📅 Жазылу",
        "btn_settings": "⚙️ Параметрлер",
        "btn_other_sign": "♈ Басқа белгі",
        "btn_menu": "« Мәзір",
        "btn_change_sign": "♈ Белгіні өзгерту",
        "btn_change_time": "⏰ Уақытты өзгерту",
        "btn_change_timezone": "🌍 Уақыт белдеуін өзгерту",
        "btn_unsubscribe": "❌ Бас тарту",
        "btn_subscribe_now": "✅ Жазылу",
        "btn_back": "« Артқа",
        "btn_confirm": "✅ Растау",
        "btn_cancel": "❌ Болдырмау",
        # Messages
        "select_sign": "<b>♈ Зодиак белгіңізді таңдаңыз</b>\n\nБүгінгі жұлдызнаманы алу үшін белгіңізді таңдаңыз:",
        "select_sign_change": "<b>♈ Зодиак белгіңізді өзгертіңіз</b>\n\nЖаңа белгіңізді таңдаңыз:",
        "subscribe_select_sign": "<b>📅 Күнделікті жұлдызнамаға жазылу</b>\n\nАлдымен зодиак белгіңізді таңдаңыз:",
        "select_timezone": "<b>🌍 Уақыт белдеуін таңдаңыз</b>\n\nБелгі: {sign}\n\nУақыт белдеуіңізді таңдаңыз:",
        "change_timezone": "<b>🌍 Уақыт белдеуін өзгерту</b>\n\nҚазіргі: {timezone}\n\nЖаңа уақыт белдеуін таңдаңыз:",
        "select_time": "<b>⏰ Жеткізу уақытын таңдаңыз</b>\n\nБелгі: {sign}\nУақыт белдеуі: {timezone}\n\nКүнделікті жұлдызнамаңызды қашан алғыңыз келеді?",
        "change_time": "<b>⏰ Жеткізу уақытын өзгерту</b>\n\nБелгі: {sign}\nУақыт белдеуі: {timezone}\n\nҚалаған уақытты таңдаңыз:",
        "subscribed": """<b>✅ Сәтті жазылдыңыз!</b>

<b>Белгі:</b> {sign}
<b>Жеткізу:</b> Күн сайын {time}

Сіз бірінші жұлдызнаманы жоспарланған уақытта аласыз.
Бүгінгі жұлдызнаманы қазір алу үшін /horoscope пайдаланыңыз!""",
        "unsubscribe_confirm": "<b>❌ Жазылымнан бас тартасыз ба?</b>\n\nСіз қазір {sign} жұлдызнамасын күн сайын {time}-де алып жатырсыз.\n\nБас тартқыңыз келе ме?",
        "unsubscribed": """<b>✅ Жазылымнан бас тартылды</b>

Сіз күнделікті жұлдызнамалардан бас тарттыңыз.
Кез келген уақытта /horoscope пайдаланып жұлдызнамаңызды ала аласыз!""",
        "settings_with_sub": """<b>⚙️ Сіздің параметрлеріңіз</b>

<b>Белгі:</b> {sign}
<b>Жеткізу:</b> Күн сайын {time}
<b>Күй:</b> ✅ Белсенді""",
        "settings_no_sub": """<b>⚙️ Параметрлер</b>

Сізде әлі белсенді жазылым жоқ.
Күнделікті жұлдызнамалар алу үшін жазылыңыз!""",
        "settings_cancelled": "<b>⚙️ Параметрлер</b>\n\nӘрекет тоқтатылды.",
        "main_menu": "<b>⭐ Жұлдызнама боты</b>\n\nОпцияны таңдаңыз:",
        "generating": "⏳ Жұлдызнамаңыз жасалуда...",
        "service_not_ready": "Қызмет дайын емес. Кейінірек қайталап көріңіз.",
        "no_subscription": "Сізде белсенді жазылым жоқ.",
        "cancelled": "Тоқтатылды",
        "sub_cancelled": "Жазылым тоқтатылды.\n\nБасты мәзірге оралу үшін /start пайдаланыңыз.",
        "select_sign_first": "Алдымен белгіңізді таңдаңыз",
        "invalid_sign": "Жарамсыз белгі",
        # Help
        "help": """<b>❓ Жұлдызнама боты анықтамасы</b>

<b>Командалар:</b>
/start - Басты мәзірді көрсету
/horoscope - Бүгінгі жұлдызнаманы алу
/subscribe - Күнделікті жіберуге жазылу
/unsubscribe - Жазылымды болдырмау
/settings - Параметрлерді көру және өзгерту
/help - Осы анықтаманы көрсету

<b>Қалай жұмыс істейді:</b>
1. Зодиак белгіңізді таңдаңыз
2. Жеке жұлдызнамаңызды алыңыз
3. Күн сайын алу үшін жазылыңыз!

<b>Кеңес:</b> Жұлдызнамалар AI көмегімен жасалады және әр белгі үшін күн сайын сақталады.""",
        # Horoscope footer
        "have_wonderful_day": "Күніңіз жарқын болсын! ✨",
        # Token welcome messages
        "welcome_free_tokens": "🎁 Сіз бастау үшін <b>{tokens} тегін токен</b> алдыңыз!",
        "welcome_token_balance": "💰 Сіздің балансыңыз: <b>{balance}</b> токен",
        # Subscription status in welcome
        "welcome_subscription_active": "📅 Жазылым: <b>{sign}</b> күн сайын {time}",
        "welcome_no_subscription": "📅 Белсенді жазылым жоқ. Күнделікті жұлдызнамалар алу үшін /subscribe пайдаланыңыз!",
        # Billing
        "billing_balance_title": "Сіздің токен балансыңыз",
        "billing_balance": "Баланс: <b>{balance}</b> токен",
        "billing_total_purchased": "Барлығы сатып алынды: {total}",
        "billing_total_used": "Барлығы пайдаланылды: {total}",
        "billing_buy_tokens": "Токен сатып алу",
        "billing_history": "Тарих",
        "billing_back": "Артқа",
        "billing_packages_title": "Қолжетімді токен пакеттері",
        "billing_no_packages": "Қазіргі уақытта токен пакеттері жоқ.",
        "billing_no_history": "Әлі транзакциялар жоқ.",
        "billing_history_title": "Соңғы транзакциялар",
        "billing_payment_success": "Төлем сәтті!",
        "billing_payment_received": "Сіз <b>{tokens}</b> токен алдыңыз.",
        "billing_new_balance": "Жаңа баланс: <b>{balance}</b> токен.",
        "billing_thank_you": "Сатып алғаныңызға рахмет!",
        "billing_package_starter": "30 токен",
        "billing_package_starter_desc": "~1 ай күнделікті жұлдызнама",
        "billing_package_standard": "100 токен",
        "billing_package_standard_desc": "Ең тиімді - 3+ ай",
        "billing_package_premium": "250 токен",
        "billing_package_premium_desc": "Белсенді пакет - 20% үнемдеңіз",
        "insufficient_tokens": "Сізге {required} токен қажет, бірақ сізде {available} бар.\n\nБалансыңызды тексеру немесе көбірек сатып алу үшін /tokens пайдаланыңыз.",
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
