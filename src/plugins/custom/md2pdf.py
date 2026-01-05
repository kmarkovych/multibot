"""Markdown to PDF converter plugin."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Document,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.plugins.base import BasePlugin

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
    """

    name = "md2pdf"
    description = "Convert Markdown to PDF"
    version = "1.0.0"
    author = "Multibot System"

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
            welcome = self.get_config("welcome_message", None) or """
<b>📄 Markdown to PDF Converter</b>

Welcome! I can convert your Markdown text or files to beautifully formatted PDF documents.

<b>How to use:</b>
• Send me any Markdown text
• Send me a <code>.md</code> file
• Use /convert to start a conversion

<b>Commands:</b>
/convert - Start markdown conversion
/help - Show detailed help
/themes - View available themes

<b>Quick tip:</b> Just paste your Markdown text and I'll convert it!
"""
            await message.answer(welcome.strip(), parse_mode="HTML")

        @router.message(Command("help"))
        async def cmd_help(message: Message) -> None:
            """Show help message."""
            help_text = """
<b>📖 Markdown to PDF Help</b>

<b>Supported Markdown features:</b>
• Headers (# H1, ## H2, ### H3)
• Bold, italic, strikethrough
• Code blocks and inline code
• Lists (ordered and unordered)
• Links and images
• Tables
• Blockquotes
• Horizontal rules

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
</code>
"""
            await message.answer(help_text.strip(), parse_mode="HTML")

        @router.message(Command("themes"))
        async def cmd_themes(message: Message) -> None:
            """Show theme options."""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="☀️ Light Theme", callback_data="theme_light"),
                    InlineKeyboardButton(text="🌙 Dark Theme", callback_data="theme_dark"),
                ],
            ])
            await message.answer(
                "<b>🎨 Choose PDF Theme</b>\n\n"
                "Select a theme for your PDF documents:",
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        @router.callback_query(F.data.startswith("theme_"))
        async def handle_theme(callback: CallbackQuery, state: FSMContext) -> None:
            """Handle theme selection."""
            theme = callback.data.split("_")[1]
            await state.update_data(theme=theme)
            await callback.answer(f"Theme set to {theme}!")
            await callback.message.edit_text(
                f"✅ Theme set to <b>{theme}</b>\n\n"
                "Now send me your Markdown text or file!",
                parse_mode="HTML",
            )

        @router.message(Command("convert"))
        async def cmd_convert(message: Message, state: FSMContext) -> None:
            """Start interactive conversion."""
            await state.set_state(ConvertStates.waiting_for_markdown)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_convert")],
            ])

            await message.answer(
                "<b>📝 Markdown Conversion</b>\n\n"
                "Send me your Markdown content:\n"
                "• Paste text directly\n"
                "• Send a <code>.md</code> file\n\n"
                "<i>Tip: You can also just send markdown anytime without using /convert</i>",
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        @router.callback_query(F.data == "cancel_convert")
        async def cancel_convert(callback: CallbackQuery, state: FSMContext) -> None:
            """Cancel conversion."""
            await state.clear()
            await callback.answer("Cancelled")
            await callback.message.edit_text("❌ Conversion cancelled.")

        @router.message(F.document)
        async def handle_document(message: Message, state: FSMContext, bot: Bot) -> None:
            """Handle uploaded .md files."""
            doc = message.document

            # Check file extension
            if not doc.file_name or not doc.file_name.endswith(('.md', '.markdown', '.txt')):
                await message.answer(
                    "⚠️ Please send a Markdown file (.md, .markdown, or .txt)"
                )
                return

            # Check file size (max 1MB)
            if doc.file_size > 1024 * 1024:
                await message.answer("⚠️ File too large. Maximum size is 1MB.")
                return

            # Download file
            file = await bot.get_file(doc.file_id)
            file_bytes = await bot.download_file(file.file_path)

            try:
                markdown_text = file_bytes.read().decode('utf-8')
            except UnicodeDecodeError:
                await message.answer("⚠️ Could not read file. Please ensure it's UTF-8 encoded.")
                return

            # Get filename without extension
            filename = Path(doc.file_name).stem

            # Convert to PDF
            await self._convert_and_send(message, state, markdown_text, filename)

        @router.message(F.text & ~F.text.startswith("/"))
        async def handle_text(message: Message, state: FSMContext) -> None:
            """Handle markdown text input."""
            markdown_text = message.text

            # Skip very short messages
            if len(markdown_text) < 10:
                return

            # Check if it looks like markdown (has some markdown syntax)
            markdown_indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
            if not any(indicator in markdown_text for indicator in markdown_indicators):
                # If in conversion state, convert anyway
                current_state = await state.get_state()
                if current_state != ConvertStates.waiting_for_markdown:
                    return

            # Generate filename from first line or use default
            first_line = markdown_text.split('\n')[0]
            filename = first_line.strip('#').strip()[:50] or "document"
            # Clean filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = filename or "document"

            await self._convert_and_send(message, state, markdown_text, filename)

    async def _convert_and_send(
        self,
        message: Message,
        state: FSMContext,
        markdown_text: str,
        filename: str,
    ) -> None:
        """Convert markdown to PDF and send it."""
        # Send processing message
        processing_msg = await message.answer("⏳ Converting to PDF...")

        try:
            # Get theme preference
            data = await state.get_data()
            theme = data.get("theme", "light")
            css = self.DARK_CSS if theme == "dark" else self.DEFAULT_CSS

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

                await message.answer_document(
                    pdf_file,
                    caption=f"✅ <b>{filename}.pdf</b>\n\n"
                            f"📊 Size: {len(pdf_bytes) / 1024:.1f} KB\n"
                            f"🎨 Theme: {theme.title()}",
                    parse_mode="HTML",
                )

                # Delete processing message
                await processing_msg.delete()

                # Clear state if in conversion mode
                await state.clear()

            else:
                await processing_msg.edit_text(
                    "❌ Failed to generate PDF. Please try again."
                )

        except Exception as e:
            logger.error(f"Error converting markdown to PDF: {e}")
            await processing_msg.edit_text(
                f"❌ Error during conversion: {str(e)[:100]}"
            )

    async def _markdown_to_html(self, markdown_text: str, css: str) -> str:
        """Convert markdown to HTML with styling."""
        try:
            import markdown
            from markdown.extensions.codehilite import CodeHiliteExtension
            from markdown.extensions.tables import TableExtension
            from markdown.extensions.fenced_code import FencedCodeExtension
            from markdown.extensions.toc import TocExtension
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
            'tables',
            'fenced_code',
            'codehilite',
            'toc',
            'nl2br',
            'sane_lists',
        ]

        extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': True,
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
                lambda: pdfkit.from_string(html_content, False, options={
                    'encoding': 'UTF-8',
                    'page-size': 'A4',
                    'margin-top': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '20mm',
                    'margin-right': '20mm',
                })
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
            await asyncio.to_thread(
                lambda: pisa.CreatePDF(html_content, dest=output)
            )
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
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from io import BytesIO
        import re

        output = BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # Simple HTML to text extraction
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'\n+', '\n', text).strip()

        for line in text.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 6))

        await asyncio.to_thread(doc.build, story)

        return output.getvalue()


# Export for auto-discovery
plugin = Md2PdfPlugin
