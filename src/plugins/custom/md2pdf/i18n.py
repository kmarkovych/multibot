"""Internationalization support for md2pdf bot."""

from __future__ import annotations

from typing import Any

# Supported languages
SUPPORTED_LANGUAGES = ["en", "uk", "pt", "kk"]
DEFAULT_LANGUAGE = "en"

# Translations dictionary
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Bot info
        "bot_name": "Markdown to PDF",
        "bot_description": """Convert Markdown to beautifully formatted PDF documents!

Features:
- Paste markdown text directly
- Upload .md files
- Light and dark themes
- Auto-combine split messages

Just send your markdown and get a PDF back!""",
        "bot_short_description": "Convert Markdown to PDF documents",
        # Commands
        "cmd_start": "Main menu",
        "cmd_convert": "Start conversion",
        "cmd_themes": "Choose PDF theme",
        "cmd_help": "Show help",
        # Welcome
        "welcome": """<b>Markdown to PDF Converter</b>

Welcome! I can convert your Markdown text or files to beautifully formatted PDF documents.

<b>How to use:</b>
- Send me any Markdown text
- Send me a <code>.md</code> file
- Use /convert to start a conversion

<b>Commands:</b>
/convert - Start markdown conversion
/help - Show detailed help
/themes - View available themes

<b>Quick tip:</b> Just paste your Markdown text and I'll convert it!""",
        # Help
        "help": """<b>Markdown to PDF Help</b>

<b>Supported Markdown features:</b>
- Headers (# H1, ## H2, ### H3)
- Bold, italic, strikethrough
- Code blocks and inline code
- Lists (ordered and unordered)
- Links and images
- Tables
- Blockquotes
- Horizontal rules

<b>Commands:</b>
/convert - Interactive conversion mode
/themes - Choose PDF theme
/help - This help message

<b>Examples:</b>
<code># My Document
This is **bold** and *italic*.

## Code Example
```python
print("Hello, World!")
```

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
</code>""",
        # Themes
        "themes_title": "<b>Choose PDF Theme</b>\n\nSelect a theme for your PDF documents:",
        "btn_theme_light": "Light Theme",
        "btn_theme_dark": "Dark Theme",
        "theme_set": "Theme set to <b>{theme}</b>\n\nNow send me your Markdown text or file!",
        # Convert
        "convert_prompt": """<b>Markdown Conversion</b>

Send me your Markdown content:
- Paste text directly
- Send a <code>.md</code> file

<i>Tip: You can also just send markdown anytime without using /convert</i>""",
        "btn_cancel": "Cancel",
        "cancelled": "Conversion cancelled.",
        # Processing
        "converting": "Converting to PDF...",
        "combined_messages": "<b>Combined {count} messages</b> into a single document.",
        "conversion_success": "<b>{filename}</b>\n\n Size: {size:.1f} KB\n Theme: {theme}",
        "conversion_failed": "Failed to generate PDF. Please try again.",
        "conversion_error": "Error during conversion: {error}",
        # File handling
        "invalid_file_type": "Please send a Markdown file (.md, .markdown, or .txt)",
        "file_too_large": "File too large. Maximum size is 1MB.",
        "file_read_error": "Could not read file. Please ensure it's UTF-8 encoded.",
    },
    "uk": {
        # Bot info
        "bot_name": "Markdown у PDF",
        "bot_description": """Конвертуйте Markdown у гарно оформлені PDF документи!

Можливості:
- Вставте текст markdown напряму
- Завантажте .md файли
- Світла та темна теми
- Автооб'єднання розділених повідомлень

Просто надішліть markdown і отримайте PDF!""",
        "bot_short_description": "Конвертація Markdown у PDF документи",
        # Commands
        "cmd_start": "Головне меню",
        "cmd_convert": "Почати конвертацію",
        "cmd_themes": "Обрати тему PDF",
        "cmd_help": "Показати довідку",
        # Welcome
        "welcome": """<b>Конвертер Markdown у PDF</b>

Вітаю! Я можу конвертувати ваш Markdown текст або файли у гарно оформлені PDF документи.

<b>Як користуватися:</b>
- Надішліть мені будь-який Markdown текст
- Надішліть мені <code>.md</code> файл
- Використовуйте /convert для початку конвертації

<b>Команди:</b>
/convert - Почати конвертацію
/help - Детальна довідка
/themes - Переглянути доступні теми

<b>Порада:</b> Просто вставте ваш Markdown текст і я конвертую його!""",
        # Help
        "help": """<b>Довідка Markdown у PDF</b>

<b>Підтримувані функції Markdown:</b>
- Заголовки (# H1, ## H2, ### H3)
- Жирний, курсив, закреслений
- Блоки коду та інлайн код
- Списки (нумеровані та марковані)
- Посилання та зображення
- Таблиці
- Цитати
- Горизонтальні лінії

<b>Команди:</b>
/convert - Інтерактивний режим конвертації
/themes - Обрати тему PDF
/help - Ця довідка

<b>Приклади:</b>
<code># Мій документ
Це **жирний** та *курсив*.

## Приклад коду
```python
print("Привіт, Світе!")
```

| Колонка 1 | Колонка 2 |
|-----------|-----------|
| Дані 1    | Дані 2    |
</code>""",
        # Themes
        "themes_title": "<b>Оберіть тему PDF</b>\n\nОберіть тему для ваших PDF документів:",
        "btn_theme_light": "Світла тема",
        "btn_theme_dark": "Темна тема",
        "theme_set": "Тему встановлено: <b>{theme}</b>\n\nТепер надішліть мені ваш Markdown текст або файл!",
        # Convert
        "convert_prompt": """<b>Конвертація Markdown</b>

Надішліть мені ваш Markdown контент:
- Вставте текст напряму
- Надішліть <code>.md</code> файл

<i>Порада: Ви також можете просто надіслати markdown без /convert</i>""",
        "btn_cancel": "Скасувати",
        "cancelled": "Конвертацію скасовано.",
        # Processing
        "converting": "Конвертую у PDF...",
        "combined_messages": "<b>Об'єднано {count} повідомлень</b> в один документ.",
        "conversion_success": "<b>{filename}</b>\n\n Розмір: {size:.1f} КБ\n Тема: {theme}",
        "conversion_failed": "Не вдалося створити PDF. Спробуйте ще раз.",
        "conversion_error": "Помилка конвертації: {error}",
        # File handling
        "invalid_file_type": "Будь ласка, надішліть Markdown файл (.md, .markdown, або .txt)",
        "file_too_large": "Файл занадто великий. Максимальний розмір 1МБ.",
        "file_read_error": "Не вдалося прочитати файл. Переконайтеся, що він у кодуванні UTF-8.",
    },
    "pt": {
        # Bot info
        "bot_name": "Markdown para PDF",
        "bot_description": """Converta Markdown em documentos PDF lindamente formatados!

Recursos:
- Cole texto markdown diretamente
- Envie arquivos .md
- Temas claro e escuro
- Combina mensagens divididas automaticamente

Basta enviar seu markdown e receber um PDF!""",
        "bot_short_description": "Converta Markdown em documentos PDF",
        # Commands
        "cmd_start": "Menu principal",
        "cmd_convert": "Iniciar conversao",
        "cmd_themes": "Escolher tema do PDF",
        "cmd_help": "Mostrar ajuda",
        # Welcome
        "welcome": """<b>Conversor de Markdown para PDF</b>

Bem-vindo! Posso converter seu texto ou arquivos Markdown em documentos PDF lindamente formatados.

<b>Como usar:</b>
- Envie-me qualquer texto Markdown
- Envie-me um arquivo <code>.md</code>
- Use /convert para iniciar uma conversao

<b>Comandos:</b>
/convert - Iniciar conversao de markdown
/help - Mostrar ajuda detalhada
/themes - Ver temas disponiveis

<b>Dica rapida:</b> Basta colar seu texto Markdown e eu o converterei!""",
        # Help
        "help": """<b>Ajuda Markdown para PDF</b>

<b>Recursos Markdown suportados:</b>
- Cabecalhos (# H1, ## H2, ### H3)
- Negrito, italico, tachado
- Blocos de codigo e codigo inline
- Listas (ordenadas e nao ordenadas)
- Links e imagens
- Tabelas
- Citacoes
- Linhas horizontais

<b>Comandos:</b>
/convert - Modo de conversao interativo
/themes - Escolher tema do PDF
/help - Esta mensagem de ajuda

<b>Exemplos:</b>
<code># Meu Documento
Isto e **negrito** e *italico*.

## Exemplo de Codigo
```python
print("Ola, Mundo!")
```

| Coluna 1 | Coluna 2 |
|----------|----------|
| Dado 1   | Dado 2   |
</code>""",
        # Themes
        "themes_title": "<b>Escolha o Tema do PDF</b>\n\nSelecione um tema para seus documentos PDF:",
        "btn_theme_light": "Tema Claro",
        "btn_theme_dark": "Tema Escuro",
        "theme_set": "Tema definido para <b>{theme}</b>\n\nAgora envie-me seu texto ou arquivo Markdown!",
        # Convert
        "convert_prompt": """<b>Conversao de Markdown</b>

Envie-me seu conteudo Markdown:
- Cole o texto diretamente
- Envie um arquivo <code>.md</code>

<i>Dica: Voce tambem pode enviar markdown a qualquer momento sem usar /convert</i>""",
        "btn_cancel": "Cancelar",
        "cancelled": "Conversao cancelada.",
        # Processing
        "converting": "Convertendo para PDF...",
        "combined_messages": "<b>Combinadas {count} mensagens</b> em um unico documento.",
        "conversion_success": "<b>{filename}</b>\n\n Tamanho: {size:.1f} KB\n Tema: {theme}",
        "conversion_failed": "Falha ao gerar PDF. Por favor, tente novamente.",
        "conversion_error": "Erro durante a conversao: {error}",
        # File handling
        "invalid_file_type": "Por favor, envie um arquivo Markdown (.md, .markdown ou .txt)",
        "file_too_large": "Arquivo muito grande. O tamanho maximo e 1MB.",
        "file_read_error": "Nao foi possivel ler o arquivo. Certifique-se de que esta codificado em UTF-8.",
    },
    "kk": {
        # Bot info
        "bot_name": "Markdown-тан PDF",
        "bot_description": """Markdown-ты әдемі форматталған PDF құжаттарына айналдырыңыз!

Мүмкіндіктер:
- Markdown мәтінін тікелей қойыңыз
- .md файлдарын жүктеңіз
- Ашық және қараңғы темалар
- Бөлінген хабарламаларды автоматты біріктіру

Markdown жіберіңіз және PDF алыңыз!""",
        "bot_short_description": "Markdown-ты PDF құжаттарына айналдыру",
        # Commands
        "cmd_start": "Басты мәзір",
        "cmd_convert": "Түрлендіруді бастау",
        "cmd_themes": "PDF тақырыбын таңдау",
        "cmd_help": "Анықтаманы көрсету",
        # Welcome
        "welcome": """<b>Markdown-тан PDF-ке түрлендіргіш</b>

Қош келдіңіз! Мен сіздің Markdown мәтініңізді немесе файлдарыңызды әдемі форматталған PDF құжаттарына айналдыра аламын.

<b>Қалай пайдалану:</b>
- Маған кез келген Markdown мәтінін жіберіңіз
- Маған <code>.md</code> файлын жіберіңіз
- Түрлендіруді бастау үшін /convert пайдаланыңыз

<b>Командалар:</b>
/convert - Markdown түрлендіруін бастау
/help - Толық анықтаманы көрсету
/themes - Қолжетімді тақырыптарды көру

<b>Кеңес:</b> Markdown мәтінін қойыңыз, мен оны түрлендіремін!""",
        # Help
        "help": """<b>Markdown-тан PDF-ке анықтама</b>

<b>Қолдау көрсетілетін Markdown мүмкіндіктері:</b>
- Тақырыптар (# H1, ## H2, ### H3)
- Қалың, көлбеу, сызылған
- Код блоктары және инлайн код
- Тізімдер (нөмірленген және таңбаланған)
- Сілтемелер мен суреттер
- Кестелер
- Дәйексөздер
- Көлденең сызықтар

<b>Командалар:</b>
/convert - Интерактивті түрлендіру режимі
/themes - PDF тақырыбын таңдау
/help - Осы анықтама

<b>Мысалдар:</b>
<code># Менің құжатым
Бұл **қалың** және *көлбеу*.

## Код мысалы
```python
print("Сәлем, Әлем!")
```

| Баған 1 | Баған 2 |
|---------|---------|
| Дерек 1 | Дерек 2 |
</code>""",
        # Themes
        "themes_title": "<b>PDF тақырыбын таңдаңыз</b>\n\nPDF құжаттарыңыз үшін тақырып таңдаңыз:",
        "btn_theme_light": "Ашық тақырып",
        "btn_theme_dark": "Қараңғы тақырып",
        "theme_set": "Тақырып орнатылды: <b>{theme}</b>\n\nЕнді маған Markdown мәтінін немесе файлды жіберіңіз!",
        # Convert
        "convert_prompt": """<b>Markdown түрлендіру</b>

Маған Markdown мазмұнын жіберіңіз:
- Мәтінді тікелей қойыңыз
- <code>.md</code> файлын жіберіңіз

<i>Кеңес: /convert пайдаланбай-ақ кез келген уақытта markdown жібере аласыз</i>""",
        "btn_cancel": "Болдырмау",
        "cancelled": "Түрлендіру болдырылмады.",
        # Processing
        "converting": "PDF-ке түрлендіруде...",
        "combined_messages": "<b>{count} хабарлама біріктірілді</b> бір құжатқа.",
        "conversion_success": "<b>{filename}</b>\n\n Өлшемі: {size:.1f} КБ\n Тақырып: {theme}",
        "conversion_failed": "PDF жасау сәтсіз аяқталды. Қайталап көріңіз.",
        "conversion_error": "Түрлендіру қатесі: {error}",
        # File handling
        "invalid_file_type": "Markdown файлын жіберіңіз (.md, .markdown немесе .txt)",
        "file_too_large": "Файл тым үлкен. Максималды өлшем 1МБ.",
        "file_read_error": "Файлды оқу мүмкін болмады. UTF-8 кодтауында екенін тексеріңіз.",
    },
}

# Theme name translations
THEME_NAMES: dict[str, dict[str, str]] = {
    "en": {"light": "Light", "dark": "Dark"},
    "uk": {"light": "Світла", "dark": "Темна"},
    "pt": {"light": "Claro", "dark": "Escuro"},
    "kk": {"light": "Ашық", "dark": "Қараңғы"},
}


def get_lang(language_code: str | None) -> str:
    """Get supported language code or default."""
    if not language_code:
        return DEFAULT_LANGUAGE
    lang = language_code.lower().split("-")[0]
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, language_code: str | None = None, **kwargs: Any) -> str:
    """Get translated string."""
    lang = get_lang(language_code)
    text = TRANSLATIONS.get(lang, {}).get(key, "")
    if not text:
        text = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_theme_name(theme: str, language_code: str | None = None) -> str:
    """Get translated theme name."""
    lang = get_lang(language_code)
    return THEME_NAMES.get(lang, THEME_NAMES["en"]).get(theme, theme.title())
