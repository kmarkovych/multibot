"""Markdown to PDF converter plugin package."""

from .plugin import ConvertStates, Md2PdfPlugin

plugin = Md2PdfPlugin

__all__ = ["Md2PdfPlugin", "ConvertStates", "plugin"]
