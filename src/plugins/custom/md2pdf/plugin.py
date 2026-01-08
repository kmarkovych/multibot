"""Markdown to PDF converter plugin."""

from __future__ import annotations

import asyncio
import logging
import re
from io import BytesIO
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.plugins.base import BasePlugin

from .i18n import SUPPORTED_LANGUAGES, get_font_size_name, get_theme_name, t

logger = logging.getLogger(__name__)


class ConvertStates(StatesGroup):
    """States for markdown conversion."""

    waiting_for_markdown = State()
    waiting_for_filename = State()


class Md2PdfPlugin(BasePlugin):
    """
    Markdown to PDF converter bot.

    Features:
    - Convert markdown text to PDF
    - Convert .md files to PDF
    - Customizable styles
    - Multiple themes (light/dark)
    - Auto-combine split messages (handles Telegram's 4096 char limit)
    - Multilanguage support (en, uk, pt, kk)
    """

    name = "md2pdf"
    description = "Convert Markdown to PDF"
    version = "1.1.0"
    author = "Multibot System"

    # Buffer delay in seconds - wait for more messages before processing
    BUFFER_DELAY = 1.5

    # Font size configurations: (body_pt, code_pt, scale_factor)
    # scale_factor applies to margins, paddings, and spacing
    FONT_SIZES = {
        "small": (10, 8, 0.85),
        "medium": (12, 10, 1.0),
        "large": (14, 12, 1.2),
    }

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        # Buffer for combining split messages: {chat_id: [messages]}
        self._message_buffers: dict[int, list[str]] = {}
        # Pending buffer tasks: {chat_id: asyncio.Task}
        self._buffer_tasks: dict[int, asyncio.Task] = {}

    # Default CSS styles for PDF
    DEFAULT_CSS = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #333;
        max-width: 100%;
    }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }
    h3 { color: #7f8c8d; }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
    }
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        overflow-x: auto;
    }
    pre code {
        background: none;
        padding: 0;
    }
    blockquote {
        border-left: 4px solid #3498db;
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: #f9f9f9;
        color: #555;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
    }
    tr:nth-child(even) { background-color: #f9f9f9; }
    a { color: #3498db; text-decoration: none; }
    a:hover { text-decoration: underline; }
    img { max-width: 100%; height: auto; }
    hr { border: none; border-top: 1px solid #ddd; margin: 2em 0; }
    ul, ol { padding-left: 2em; }
    li { margin: 0.3em 0; }
    """

    DARK_CSS = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #e0e0e0;
        background-color: #1e1e1e;
        max-width: 100%;
    }
    h1 { color: #61afef; border-bottom: 2px solid #61afef; padding-bottom: 10px; }
    h2 { color: #98c379; border-bottom: 1px solid #4b5263; padding-bottom: 5px; }
    h3 { color: #e5c07b; }
    code {
        background-color: #2d2d2d;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
        color: #e06c75;
    }
    pre {
        background-color: #282c34;
        border: 1px solid #4b5263;
        border-radius: 5px;
        padding: 15px;
        overflow-x: auto;
    }
    pre code {
        background: none;
        padding: 0;
        color: #abb2bf;
    }
    blockquote {
        border-left: 4px solid #61afef;
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: #2d2d2d;
        color: #abb2bf;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    th, td {
        border: 1px solid #4b5263;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #3e4451;
        color: #61afef;
    }
    tr:nth-child(even) { background-color: #2d2d2d; }
    a { color: #61afef; text-decoration: none; }
    a:hover { text-decoration: underline; }
    img { max-width: 100%; height: auto; }
    hr { border: none; border-top: 1px solid #4b5263; margin: 2em 0; }
    ul, ol { padding-left: 2em; }
    li { margin: 0.3em 0; }
    """

    def setup_handlers(self, router: Router) -> None:
        """Register all handlers."""

        @router.message(CommandStart())
        async def cmd_start(message: Message) -> None:
            """Handle /start command."""
            lang = message.from_user.language_code if message.from_user else None
            welcome = self.get_config("welcome_message", None) or t("welcome", lang)
            await message.answer(welcome.strip(), parse_mode="HTML")

        @router.message(Command("help"))
        async def cmd_help(message: Message) -> None:
            """Show help message."""
            lang = message.from_user.language_code if message.from_user else None
            await message.answer(t("help", lang), parse_mode="HTML")

        @router.message(Command("themes"))
        async def cmd_themes(message: Message) -> None:
            """Show theme options."""
            lang = message.from_user.language_code if message.from_user else None
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"\u2600\ufe0f {t('btn_theme_light', lang)}",
                            callback_data="theme_light",
                        ),
                        InlineKeyboardButton(
                            text=f"\U0001f319 {t('btn_theme_dark', lang)}",
                            callback_data="theme_dark",
                        ),
                    ],
                ]
            )
            await message.answer(
                t("themes_title", lang),
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        @router.callback_query(F.data.startswith("theme_"))
        async def handle_theme(callback: CallbackQuery, state: FSMContext) -> None:
            """Handle theme selection."""
            lang = callback.from_user.language_code if callback.from_user else None
            theme = callback.data.split("_")[1]
            await state.update_data(theme=theme)
            theme_name = get_theme_name(theme, lang)
            await callback.answer(f"{theme_name}!")
            await callback.message.edit_text(
                t("theme_set", lang, theme=theme_name),
                parse_mode="HTML",
            )

        @router.message(Command("fontsize"))
        async def cmd_fontsize(message: Message) -> None:
            """Show font size options."""
            lang = message.from_user.language_code if message.from_user else None
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"\U0001f170 {t('btn_fontsize_small', lang)}",
                            callback_data="fontsize_small",
                        ),
                        InlineKeyboardButton(
                            text=f"\U0001f171 {t('btn_fontsize_medium', lang)}",
                            callback_data="fontsize_medium",
                        ),
                        InlineKeyboardButton(
                            text=f"\U0001f172 {t('btn_fontsize_large', lang)}",
                            callback_data="fontsize_large",
                        ),
                    ],
                ]
            )
            await message.answer(
                t("fontsize_title", lang),
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        @router.callback_query(F.data.startswith("fontsize_"))
        async def handle_fontsize(callback: CallbackQuery, state: FSMContext) -> None:
            """Handle font size selection."""
            lang = callback.from_user.language_code if callback.from_user else None
            size = callback.data.split("_")[1]
            await state.update_data(fontsize=size)
            size_name = get_font_size_name(size, lang)
            await callback.answer(f"{size_name}!")
            await callback.message.edit_text(
                t("fontsize_set", lang, size=size_name),
                parse_mode="HTML",
            )

        @router.message(Command("convert"))
        async def cmd_convert(message: Message, state: FSMContext) -> None:
            """Start interactive conversion."""
            lang = message.from_user.language_code if message.from_user else None
            await state.set_state(ConvertStates.waiting_for_markdown)

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"\u274c {t('btn_cancel', lang)}",
                            callback_data="cancel_convert",
                        )
                    ],
                ]
            )

            await message.answer(
                t("convert_prompt", lang),
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "cancel_convert")
        async def cancel_convert(callback: CallbackQuery, state: FSMContext) -> None:
            """Cancel conversion."""
            lang = callback.from_user.language_code if callback.from_user else None
            await state.clear()
            await callback.answer()
            await callback.message.edit_text(f"\u274c {t('cancelled', lang)}")

        @router.message(F.document)
        async def handle_document(message: Message, state: FSMContext, bot: Bot) -> None:
            """Handle uploaded .md files."""
            lang = message.from_user.language_code if message.from_user else None
            doc = message.document

            # Check file extension
            if not doc.file_name or not doc.file_name.endswith(
                (".md", ".markdown", ".txt")
            ):
                await message.answer(f"\u26a0\ufe0f {t('invalid_file_type', lang)}")
                return

            # Check file size (max 1MB)
            if doc.file_size > 1024 * 1024:
                await message.answer(f"\u26a0\ufe0f {t('file_too_large', lang)}")
                return

            # Download file
            file = await bot.get_file(doc.file_id)
            file_bytes = await bot.download_file(file.file_path)

            try:
                markdown_text = file_bytes.read().decode("utf-8")
            except UnicodeDecodeError:
                await message.answer(f"\u26a0\ufe0f {t('file_read_error', lang)}")
                return

            # Get filename without extension
            filename = Path(doc.file_name).stem

            # Convert to PDF
            await self._convert_and_send(message, state, markdown_text, filename, lang)

        @router.message(F.text & ~F.text.startswith("/"))
        async def handle_text(message: Message, state: FSMContext) -> None:
            """Handle markdown text input with buffering for split messages."""
            markdown_text = message.text
            chat_id = message.chat.id

            # Skip very short messages
            if len(markdown_text) < 10:
                return

            # Check if it looks like markdown (has some markdown syntax)
            markdown_indicators = ["#", "*", "_", "`", "[", "|", "-", ">"]
            if not any(indicator in markdown_text for indicator in markdown_indicators):
                # If in conversion state, convert anyway
                current_state = await state.get_state()
                if current_state != ConvertStates.waiting_for_markdown:
                    return

            # Add message to buffer
            if chat_id not in self._message_buffers:
                self._message_buffers[chat_id] = []
            self._message_buffers[chat_id].append(markdown_text)

            # Cancel existing buffer task if any
            if chat_id in self._buffer_tasks:
                self._buffer_tasks[chat_id].cancel()
                try:
                    await self._buffer_tasks[chat_id]
                except asyncio.CancelledError:
                    pass

            # Create new delayed task to process buffered messages
            async def process_after_delay():
                await asyncio.sleep(self.BUFFER_DELAY)
                await self._process_buffered_messages(chat_id, message, state)

            self._buffer_tasks[chat_id] = asyncio.create_task(process_after_delay())

    async def _process_buffered_messages(
        self,
        chat_id: int,
        message: Message,
        state: FSMContext,
    ) -> None:
        """Process all buffered messages for a chat as a single PDF."""
        lang = message.from_user.language_code if message.from_user else None

        # Get and clear the buffer
        messages = self._message_buffers.pop(chat_id, [])
        self._buffer_tasks.pop(chat_id, None)

        if not messages:
            return

        # Combine all messages
        markdown_text = "\n\n".join(messages)

        # Notify if multiple messages were combined
        if len(messages) > 1:
            await message.answer(
                f"\U0001f4ce {t('combined_messages', lang, count=len(messages))}",
                parse_mode="HTML",
            )

        # Generate filename from first line or use default
        first_line = markdown_text.split("\n")[0]
        filename = first_line.strip("#").strip()[:50] or "document"
        # Clean filename
        filename = "".join(
            c for c in filename if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        filename = filename or "document"

        await self._convert_and_send(message, state, markdown_text, filename, lang)

    async def _convert_and_send(
        self,
        message: Message,
        state: FSMContext,
        markdown_text: str,
        filename: str,
        lang: str | None = None,
    ) -> None:
        """Convert markdown to PDF and send it."""
        # Send processing message
        processing_msg = await message.answer(f"\u23f3 {t('converting', lang)}")

        try:
            # Get theme and font size preferences
            data = await state.get_data()
            theme = data.get("theme", "light")
            fontsize = data.get("fontsize", "medium")

            # Get base CSS for theme
            base_css = self.DARK_CSS if theme == "dark" else self.DEFAULT_CSS

            # Apply font size to CSS
            css = self._apply_font_size(base_css, fontsize)

            # Convert markdown to HTML
            html_content = await self._markdown_to_html(markdown_text, css)

            # Convert HTML to PDF
            pdf_bytes = await self._html_to_pdf(html_content)

            if pdf_bytes:
                # Send PDF file
                pdf_file = BufferedInputFile(
                    pdf_bytes,
                    filename=f"{filename}.pdf",
                )

                theme_name = get_theme_name(theme, lang)
                fontsize_name = get_font_size_name(fontsize, lang)
                await message.answer_document(
                    pdf_file,
                    caption=f"\u2705 {t('conversion_success', lang, filename=f'{filename}.pdf', size=len(pdf_bytes) / 1024, theme=theme_name)} | {fontsize_name}",
                    parse_mode="HTML",
                )

                # Delete processing message
                await processing_msg.delete()

                # Clear state if in conversion mode
                await state.clear()

            else:
                await processing_msg.edit_text(
                    f"\u274c {t('conversion_failed', lang)}"
                )

        except Exception as e:
            logger.error(f"Error converting markdown to PDF: {e}")
            await processing_msg.edit_text(
                f"\u274c {t('conversion_error', lang, error=str(e)[:100])}"
            )

    def _apply_font_size(self, css: str, fontsize: str) -> str:
        """Apply font size and scale margins/paddings accordingly."""
        body_pt, code_pt, scale = self.FONT_SIZES.get(fontsize, self.FONT_SIZES["medium"])

        # Replace body font-size
        css = re.sub(
            r"(body\s*\{[^}]*font-size:\s*)\d+pt",
            f"\\g<1>{body_pt}pt",
            css,
        )

        # Replace code font-size
        css = re.sub(
            r"(code\s*\{[^}]*font-size:\s*)\d+pt",
            f"\\g<1>{code_pt}pt",
            css,
        )

        # Scale numeric values in margins and paddings
        def scale_value(match: re.Match) -> str:
            prop = match.group(1)  # margin/padding property
            values = match.group(2)  # the values

            def scale_single(m: re.Match) -> str:
                num = float(m.group(1))
                unit = m.group(2)
                scaled = num * scale
                # Format nicely: no decimals for whole numbers
                if scaled == int(scaled):
                    return f"{int(scaled)}{unit}"
                return f"{scaled:.1f}{unit}"

            scaled_values = re.sub(r"(\d+\.?\d*)(px|pt|cm|mm|em)", scale_single, values)
            return f"{prop}{scaled_values}"

        # Scale margin and padding values
        css = re.sub(
            r"((?:margin|padding)(?:-(?:top|bottom|left|right))?:\s*)([^;]+)",
            scale_value,
            css,
        )

        # Scale line-height if numeric
        def scale_line_height(match: re.Match) -> str:
            value = float(match.group(1))
            # Scale line-height slightly (less aggressive than margins)
            scaled = 1.4 + (value - 1.4) * scale
            # Format nicely: remove trailing zeros
            formatted = f"{scaled:.2f}".rstrip("0").rstrip(".")
            return f"line-height: {formatted}"

        css = re.sub(r"line-height:\s*(\d+\.?\d*)", scale_line_height, css)

        return css

    async def _markdown_to_html(self, markdown_text: str, css: str) -> str:
        """Convert markdown to HTML with styling."""
        try:
            import markdown
        except ImportError:
            # Fallback to basic conversion
            import html

            escaped = html.escape(markdown_text)
            return f"""
            <!DOCTYPE html>
            <html>
            <head><style>{css}</style></head>
            <body><pre>{escaped}</pre></body>
            </html>
            """

        # Configure markdown extensions
        extensions = [
            "tables",
            "fenced_code",
            "codehilite",
            "toc",
            "nl2br",
            "sane_lists",
        ]

        extension_configs = {
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": True,
            },
        }

        # Convert markdown to HTML
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
        )
        html_content = md.convert(markdown_text)

        # Wrap in full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {css}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        return full_html

    async def _html_to_pdf(self, html_content: str) -> bytes | None:
        """Convert HTML to PDF bytes."""
        # Try different PDF libraries in order of preference

        # Option 1: WeasyPrint (best quality)
        try:
            from weasyprint import HTML

            pdf_bytes = await asyncio.to_thread(
                lambda: HTML(string=html_content).write_pdf()
            )
            return pdf_bytes
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"WeasyPrint failed: {e}")

        # Option 2: pdfkit (requires wkhtmltopdf)
        try:
            import pdfkit

            pdf_bytes = await asyncio.to_thread(
                lambda: pdfkit.from_string(
                    html_content,
                    False,
                    options={
                        "encoding": "UTF-8",
                        "page-size": "A4",
                        "margin-top": "20mm",
                        "margin-bottom": "20mm",
                        "margin-left": "20mm",
                        "margin-right": "20mm",
                    },
                )
            )
            return pdf_bytes
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfkit failed: {e}")

        # Option 3: xhtml2pdf (pure Python, basic)
        try:
            from xhtml2pdf import pisa

            output = BytesIO()
            await asyncio.to_thread(lambda: pisa.CreatePDF(html_content, dest=output))
            return output.getvalue()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"xhtml2pdf failed: {e}")

        # Option 4: reportlab with markdown2pdf-like approach
        try:
            return await self._fallback_pdf_generation(html_content)
        except Exception as e:
            logger.error(f"All PDF methods failed: {e}")

        return None

    async def _fallback_pdf_generation(self, html_content: str) -> bytes:
        """Fallback PDF generation using reportlab."""
        import re
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        output = BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # Simple HTML to text extraction
        text = re.sub(r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "\n", text)
        text = re.sub(r"\n+", "\n", text).strip()

        for line in text.split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 6))

        await asyncio.to_thread(doc.build, story)

        return output.getvalue()

    async def on_load(self, bot: Bot) -> None:
        """Initialize plugin when loaded."""
        # Set bot name, commands, description for each language
        for lang in SUPPORTED_LANGUAGES:
            commands = [
                BotCommand(command="start", description=t("cmd_start", lang)),
                BotCommand(command="convert", description=t("cmd_convert", lang)),
                BotCommand(command="themes", description=t("cmd_themes", lang)),
                BotCommand(command="fontsize", description=t("cmd_fontsize", lang)),
                BotCommand(command="help", description=t("cmd_help", lang)),
            ]
            await bot.set_my_name(t("bot_name", lang), language_code=lang)
            await bot.set_my_commands(commands, language_code=lang)
            await bot.set_my_description(t("bot_description", lang), language_code=lang)
            await bot.set_my_short_description(
                t("bot_short_description", lang), language_code=lang
            )

        # Set defaults (English) for users without language preference
        default_commands = [
            BotCommand(command="start", description=t("cmd_start", "en")),
            BotCommand(command="convert", description=t("cmd_convert", "en")),
            BotCommand(command="themes", description=t("cmd_themes", "en")),
            BotCommand(command="fontsize", description=t("cmd_fontsize", "en")),
            BotCommand(command="help", description=t("cmd_help", "en")),
        ]
        await bot.set_my_name(t("bot_name", "en"))
        await bot.set_my_commands(default_commands)
        await bot.set_my_description(t("bot_description", "en"))
        await bot.set_my_short_description(t("bot_short_description", "en"))

        logger.info("Md2Pdf plugin loaded with multilanguage support")

    async def on_unload(self, bot: Bot) -> None:
        """Cleanup when plugin is unloaded."""
        # Clear bot commands, description, and short description
        await bot.delete_my_commands()
        await bot.set_my_description("")
        await bot.set_my_short_description("")

        logger.info("Md2Pdf plugin unloaded")
