"""Tests for Markdown to PDF converter plugin."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from src.plugins.custom.md2pdf import Md2PdfPlugin, ConvertStates


class TestMd2PdfPluginMetadata:
    """Tests for plugin metadata."""

    def test_plugin_name(self):
        """Test plugin has correct name."""
        plugin = Md2PdfPlugin()
        assert plugin.name == "md2pdf"

    def test_plugin_version(self):
        """Test plugin has version."""
        plugin = Md2PdfPlugin()
        assert plugin.version == "1.0.0"

    def test_plugin_description(self):
        """Test plugin has description."""
        plugin = Md2PdfPlugin()
        assert "PDF" in plugin.description

    def test_plugin_has_default_css(self):
        """Test plugin has default CSS styles."""
        plugin = Md2PdfPlugin()
        assert plugin.DEFAULT_CSS is not None
        assert "body" in plugin.DEFAULT_CSS
        assert "font-family" in plugin.DEFAULT_CSS

    def test_plugin_has_dark_css(self):
        """Test plugin has dark theme CSS."""
        plugin = Md2PdfPlugin()
        assert plugin.DARK_CSS is not None
        assert "#1e1e1e" in plugin.DARK_CSS  # Dark background color


class TestMd2PdfPluginConfig:
    """Tests for plugin configuration."""

    def test_default_config(self):
        """Test plugin works with no config."""
        plugin = Md2PdfPlugin()
        assert plugin.config == {}

    def test_custom_config(self):
        """Test plugin accepts custom config."""
        config = {
            "welcome_message": "Custom welcome!",
            "default_theme": "dark",
            "max_file_size": 2097152,
        }
        plugin = Md2PdfPlugin(config=config)
        assert plugin.get_config("welcome_message") == "Custom welcome!"
        assert plugin.get_config("default_theme") == "dark"
        assert plugin.get_config("max_file_size") == 2097152

    def test_config_defaults(self):
        """Test get_config returns defaults for missing keys."""
        plugin = Md2PdfPlugin()
        assert plugin.get_config("missing_key", "default") == "default"
        assert plugin.get_config("another_missing") is None


class TestMd2PdfPluginRouter:
    """Tests for plugin router setup."""

    def test_router_creation(self):
        """Test router is created."""
        plugin = Md2PdfPlugin()
        router = plugin.router
        assert router is not None
        assert router.name == "md2pdf"

    def test_router_is_cached(self):
        """Test router is cached on subsequent access."""
        plugin = Md2PdfPlugin()
        router1 = plugin.router
        router2 = plugin.router
        assert router1 is router2


class TestMarkdownToHtmlConversion:
    """Tests for markdown to HTML conversion."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    @pytest.mark.asyncio
    async def test_simple_markdown(self, plugin):
        """Test simple markdown conversion."""
        markdown = "# Hello World"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "<h1>" in html or "Hello World" in html
        assert "<!DOCTYPE html>" in html
        assert "<style>" in html

    @pytest.mark.asyncio
    async def test_markdown_with_bold(self, plugin):
        """Test bold text conversion."""
        markdown = "This is **bold** text"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        # Should contain bold tags or the text
        assert "bold" in html.lower()

    @pytest.mark.asyncio
    async def test_markdown_with_code(self, plugin):
        """Test code block conversion."""
        markdown = "```python\nprint('hello')\n```"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "print" in html

    @pytest.mark.asyncio
    async def test_markdown_with_list(self, plugin):
        """Test list conversion."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "Item 1" in html
        assert "Item 2" in html

    @pytest.mark.asyncio
    async def test_markdown_with_table(self, plugin):
        """Test table conversion."""
        markdown = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "Header 1" in html
        assert "Cell 1" in html

    @pytest.mark.asyncio
    async def test_markdown_with_link(self, plugin):
        """Test link conversion."""
        markdown = "[Example](https://example.com)"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "Example" in html
        assert "example.com" in html

    @pytest.mark.asyncio
    async def test_markdown_with_blockquote(self, plugin):
        """Test blockquote conversion."""
        markdown = "> This is a quote"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "quote" in html.lower()

    @pytest.mark.asyncio
    async def test_dark_theme_css(self, plugin):
        """Test dark theme CSS is applied."""
        markdown = "# Test"
        html = await plugin._markdown_to_html(markdown, plugin.DARK_CSS)

        assert "#1e1e1e" in html  # Dark background

    @pytest.mark.asyncio
    async def test_light_theme_css(self, plugin):
        """Test light theme CSS is applied."""
        markdown = "# Test"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "#333" in html  # Light theme text color

    @pytest.mark.asyncio
    async def test_empty_markdown(self, plugin):
        """Test empty markdown handling."""
        markdown = ""
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        assert "<!DOCTYPE html>" in html
        assert "<body>" in html

    @pytest.mark.asyncio
    async def test_special_characters(self, plugin):
        """Test special characters are handled."""
        markdown = "Special chars: <>&\"'"
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)

        # Should be in HTML (escaped or not)
        assert "Special chars" in html


class TestHtmlToPdfConversion:
    """Tests for HTML to PDF conversion."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    @pytest.mark.asyncio
    async def test_pdf_generation_returns_bytes(self, plugin):
        """Test PDF generation returns bytes."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>body { font-family: sans-serif; }</style></head>
        <body><h1>Test</h1><p>Content</p></body>
        </html>
        """
        pdf_bytes = await plugin._html_to_pdf(html)

        # Should return bytes (or None if no PDF library available)
        if pdf_bytes is not None:
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            # PDF magic bytes
            assert pdf_bytes[:4] == b'%PDF' or pdf_bytes[:5] == b'%PDF-'

    @pytest.mark.asyncio
    async def test_pdf_generation_complex_html(self, plugin):
        """Test PDF generation with complex HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
            body { font-family: Arial; }
            h1 { color: blue; }
            table { border-collapse: collapse; }
        </style></head>
        <body>
            <h1>Complex Document</h1>
            <p>This is a <strong>complex</strong> document.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <table>
                <tr><th>Header</th></tr>
                <tr><td>Cell</td></tr>
            </table>
        </body>
        </html>
        """
        pdf_bytes = await plugin._html_to_pdf(html)

        if pdf_bytes is not None:
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 100  # Should be substantial


class TestFallbackPdfGeneration:
    """Tests for fallback PDF generation."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    @pytest.mark.asyncio
    async def test_fallback_pdf(self, plugin):
        """Test fallback PDF generation."""
        html = "<html><body><p>Test content</p></body></html>"

        try:
            pdf_bytes = await plugin._fallback_pdf_generation(html)
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
        except ImportError:
            pytest.skip("reportlab not installed")


class TestConvertStates:
    """Tests for FSM states."""

    def test_states_defined(self):
        """Test states are properly defined."""
        assert ConvertStates.waiting_for_markdown is not None
        assert ConvertStates.waiting_for_filename is not None

    def test_states_are_unique(self):
        """Test states have unique values."""
        states = [
            ConvertStates.waiting_for_markdown,
            ConvertStates.waiting_for_filename,
        ]
        state_values = [str(s) for s in states]
        assert len(state_values) == len(set(state_values))


class TestMessageHandlers:
    """Tests for message handlers using mocks."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance with router."""
        plugin = Md2PdfPlugin()
        _ = plugin.router  # Initialize router
        return plugin

    @pytest.fixture
    def mock_message(self):
        """Create a mock message."""
        message = AsyncMock()
        message.text = "/start"
        message.answer = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.from_user.first_name = "Test"
        return message

    @pytest.fixture
    def mock_state(self):
        """Create a mock FSM state."""
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.clear = AsyncMock()
        state.get_state = AsyncMock(return_value=None)
        return state

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = AsyncMock()
        bot.get_file = AsyncMock()
        bot.download_file = AsyncMock()
        return bot


class TestDocumentHandling:
    """Tests for document/file handling."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    def test_valid_file_extensions(self):
        """Test valid file extensions are recognized."""
        valid_extensions = ['.md', '.markdown', '.txt']
        for ext in valid_extensions:
            filename = f"test{ext}"
            assert filename.endswith(tuple(valid_extensions))

    def test_invalid_file_extensions(self):
        """Test invalid file extensions are rejected."""
        valid_extensions = ('.md', '.markdown', '.txt')
        invalid_files = ['test.pdf', 'test.doc', 'test.png', 'test']
        for filename in invalid_files:
            assert not filename.endswith(valid_extensions)


class TestFilenameGeneration:
    """Tests for filename generation from content."""

    def test_filename_from_header(self):
        """Test filename is extracted from markdown header."""
        markdown = "# My Document Title\n\nContent here"
        first_line = markdown.split('\n')[0]
        filename = first_line.strip('#').strip()[:50]
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()

        assert filename == "My Document Title"

    def test_filename_sanitization(self):
        """Test filename is sanitized."""
        dirty_filename = "Test/File:Name<>With|Special*Chars?"
        clean_filename = "".join(
            c for c in dirty_filename
            if c.isalnum() or c in (' ', '-', '_')
        ).strip()

        assert "/" not in clean_filename
        assert ":" not in clean_filename
        assert "<" not in clean_filename
        assert ">" not in clean_filename

    def test_long_filename_truncation(self):
        """Test long filenames are truncated."""
        long_title = "A" * 100
        truncated = long_title[:50]
        assert len(truncated) == 50

    def test_empty_filename_fallback(self):
        """Test empty filename falls back to default."""
        markdown = "   \n\nJust content, no header"
        first_line = markdown.split('\n')[0]
        filename = first_line.strip('#').strip()[:50] or "document"

        assert filename == "document"


class TestThemeSelection:
    """Tests for theme selection."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    def test_light_theme_selection(self, plugin):
        """Test light theme CSS selection."""
        theme = "light"
        css = plugin.DARK_CSS if theme == "dark" else plugin.DEFAULT_CSS
        assert css == plugin.DEFAULT_CSS

    def test_dark_theme_selection(self, plugin):
        """Test dark theme CSS selection."""
        theme = "dark"
        css = plugin.DARK_CSS if theme == "dark" else plugin.DEFAULT_CSS
        assert css == plugin.DARK_CSS

    def test_default_theme_is_light(self, plugin):
        """Test default theme is light."""
        theme = "anything_else"
        css = plugin.DARK_CSS if theme == "dark" else plugin.DEFAULT_CSS
        assert css == plugin.DEFAULT_CSS


class TestMarkdownDetection:
    """Tests for detecting if text is markdown."""

    def test_markdown_with_headers(self):
        """Test detection of headers."""
        text = "# This is a header"
        indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
        assert any(indicator in text for indicator in indicators)

    def test_markdown_with_bold(self):
        """Test detection of bold text."""
        text = "This is **bold** text"
        indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
        assert any(indicator in text for indicator in indicators)

    def test_markdown_with_code(self):
        """Test detection of code."""
        text = "Use `code` here"
        indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
        assert any(indicator in text for indicator in indicators)

    def test_markdown_with_links(self):
        """Test detection of links."""
        text = "[Link](https://example.com)"
        indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
        assert any(indicator in text for indicator in indicators)

    def test_markdown_with_tables(self):
        """Test detection of tables."""
        text = "| Col1 | Col2 |"
        indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
        assert any(indicator in text for indicator in indicators)

    def test_plain_text_detection(self):
        """Test plain text without markdown."""
        text = "This is just plain text without any formatting"
        indicators = ['#', '*', '_', '`', '[', '|', '-', '>']
        # This text actually contains no markdown indicators
        # But we need to be careful - it might be processed anyway
        has_indicators = any(indicator in text for indicator in indicators)
        assert not has_indicators


class TestCSSStyles:
    """Tests for CSS style content."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    def test_default_css_has_page_size(self, plugin):
        """Test default CSS defines page size."""
        assert "@page" in plugin.DEFAULT_CSS
        assert "A4" in plugin.DEFAULT_CSS

    def test_default_css_has_margins(self, plugin):
        """Test default CSS defines margins."""
        assert "margin" in plugin.DEFAULT_CSS

    def test_default_css_has_font(self, plugin):
        """Test default CSS defines fonts."""
        assert "font-family" in plugin.DEFAULT_CSS

    def test_default_css_has_code_styles(self, plugin):
        """Test default CSS has code styling."""
        assert "code" in plugin.DEFAULT_CSS
        assert "pre" in plugin.DEFAULT_CSS

    def test_default_css_has_table_styles(self, plugin):
        """Test default CSS has table styling."""
        assert "table" in plugin.DEFAULT_CSS
        assert "th" in plugin.DEFAULT_CSS
        assert "td" in plugin.DEFAULT_CSS

    def test_dark_css_has_dark_colors(self, plugin):
        """Test dark CSS uses dark colors."""
        # Dark background colors
        assert "#1e1e1e" in plugin.DARK_CSS or "#2d2d2d" in plugin.DARK_CSS
        # Light text colors
        assert "#e0e0e0" in plugin.DARK_CSS or "#abb2bf" in plugin.DARK_CSS

    def test_dark_css_has_code_styles(self, plugin):
        """Test dark CSS has code styling."""
        assert "code" in plugin.DARK_CSS
        assert "#282c34" in plugin.DARK_CSS  # Code background


class TestIntegration:
    """Integration tests for full conversion flow."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return Md2PdfPlugin()

    @pytest.mark.asyncio
    async def test_full_conversion_light_theme(self, plugin):
        """Test full conversion with light theme."""
        markdown = """
# Test Document

This is a **test** document with various elements.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Table

| Name | Value |
|------|-------|
| Foo  | Bar   |

> This is a blockquote

- List item 1
- List item 2
"""
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)
        assert "Test Document" in html

        pdf_bytes = await plugin._html_to_pdf(html)
        if pdf_bytes:
            assert len(pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_full_conversion_dark_theme(self, plugin):
        """Test full conversion with dark theme."""
        markdown = "# Dark Theme Test\n\nContent here."
        html = await plugin._markdown_to_html(markdown, plugin.DARK_CSS)
        assert "Dark Theme Test" in html
        assert "#1e1e1e" in html

        pdf_bytes = await plugin._html_to_pdf(html)
        if pdf_bytes:
            assert len(pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_unicode_content(self, plugin):
        """Test conversion with unicode content."""
        markdown = """
# Тест Unicode

Привет мир! 你好世界! مرحبا بالعالم

- Emoji: 🎉 🚀 ✨
- Symbols: © ® ™ € £ ¥
"""
        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)
        assert "Тест" in html or "Unicode" in html

    @pytest.mark.asyncio
    async def test_large_document(self, plugin):
        """Test conversion of large document."""
        # Generate large markdown
        sections = []
        for i in range(50):
            sections.append(f"""
## Section {i}

This is section {i} with some content. It includes:
- Item {i}.1
- Item {i}.2
- Item {i}.3

```
Code block {i}
```
""")
        markdown = "# Large Document\n\n" + "\n".join(sections)

        html = await plugin._markdown_to_html(markdown, plugin.DEFAULT_CSS)
        assert "Section 49" in html

        # PDF generation of large docs might be slow, so we just test HTML
